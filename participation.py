import requests
import hashlib
import hmac
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import toml
import altair as alt
import streamlit_authenticator as stauth

# AUTHENTICATION SECTION

#Fetch credential
def fetch_data_creds():
    secret_info = st.secrets["sheets"]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(secret_info, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open('Dashboard Credentials')
    sheet = spreadsheet.sheet1
    data = sheet.get_all_records()
    df_creds = pd.DataFrame(data)
    return df_creds

df_creds = fetch_data_creds()

st.write(df_creds.columns)

# Process `df_creds` to extract credentials in the required format
def extract_credentials(df_creds):
    credentials = {
        "credentials": {
            "usernames": {}
        },
        "cookie": {
            "name": "growth_center",
            "key": "growth_2024",
            "expiry_days": 30
        }
    }
    for index, row in df_creds.iterrows():
        credentials['credentials']['usernames'][row['username']] = {
            'name': row['name'],  # Add the 'name' field
            'password': row['password'],  # Password should already be hashed
            'unit': row['unit'],  # Store the user's unit for later filtering
        }
    return credentials

# Extract credentials from df_creds
credentials = extract_credentials(df_creds)

# Authentication Setup
authenticator = stauth.Authenticate(
    credentials['credentials'],
    credentials['cookie']['name'],
    credentials['cookie']['key'],
    credentials['cookie']['expiry_days']
)

# Display the login form
#name, authentication_status, username = authenticator.login()
name, authentication_status, username = authenticator.login('main', fields = {'Form name': 'Welcome to Employee Survey Participation Dashboard'})


# Handle authentication status
if st.session_state['authentication_status']:


    # FETCHING DATA FROM API SECTION 

    # Load secrets from secrets.toml
    secret_key = st.secrets["api"]["secret_key"]
    surresp_url = st.secrets["api"]["surresp_url"]  # Survey Respondent Data
    suransw_url = st.secrets["api"]["suransw_url"]  # Survey Answer Data

    # Function to generate HMAC-SHA256 using MD5 hash of date params
    def generate_code(start_date, end_date, secret_key):

        # Step 1: Create the MD5 hash from start and end dates
        date_string = f"{start_date.strftime('%Y-%m-%d %H:%M')}{end_date.strftime('%Y-%m-%d %H:%M')}"
        md5_hash = hashlib.md5(date_string.encode('utf-8')).hexdigest()

        # Step 2: Create HMAC-SHA256 using the MD5 hash and secret key
        secret = secret_key.encode('utf-8')
        code = hmac.new(secret, md5_hash.encode(), hashlib.sha256).hexdigest()

        return code

    # Function to fetch data from the API
    def fetch_data(start_date, end_date, api_url):
        # Generate code for the date range
        code = generate_code(start_date, end_date, secret_key)
        
        # Format the start and end dates for the API request
        start_date_str = start_date.strftime("%Y-%m-%d %H:%M")
        end_date_str = end_date.strftime("%Y-%m-%d %H:%M")

        # Build the API URL
        url = api_url.format(start_date=start_date_str, end_date=end_date_str, code=code)

        # Fetch the data
        response = requests.get(url)

        # Check the response status
        if response.status_code == 200:
            print("Data fetched successfully!")
            return pd.DataFrame(response.json()["data"])  # Convert JSON to a DataFrame
        else:
            print(f"Failed to fetch data for {start_date_str} to {end_date_str}.")
            print(f"Status code: {response.status_code}")
            print(f"Response content: {response.content}")
            return None

    # Function to handle fetching Survey Respondent Data (24-hour intervals)
    @st.cache_resource(ttl=86400)
    def fetch_survey_respondent_data(start_date, end_date):
        all_data = []
        current_date = start_date

        while current_date < end_date:
            next_date = (current_date + timedelta(days=1)).replace(hour=0, minute=0)
            print(f"Fetching Survey Respondent Data for range: {current_date} to {next_date}")
            daily_data = fetch_data(current_date, next_date, surresp_url)

            if daily_data is not None:
                all_data.append(daily_data)

            current_date = next_date

        if all_data:
            combined_data = pd.concat(all_data, ignore_index=True)
            return combined_data
        else:
            return pd.DataFrame()

    # Function to handle fetching Survey Answer Data (12-hour intervals)
    #def fetch_survey_answer_data(start_date, end_date):
    #    all_data = []
    #    current_date = start_date

    #    while current_date < end_date:
    #        next_date = current_date + timedelta(hours=12)
    #        print(f"Fetching Survey Answer Data for range: {current_date} to {next_date}")
    #        daily_data = fetch_data(current_date, next_date, suransw_url)

    #        if daily_data is not None:
    #            all_data.append(daily_data)

    #        current_date = next_date

    #    if all_data:
    #        combined_data = pd.concat(all_data, ignore_index=True)
    #        return combined_data
    #    else:
    #        return pd.DataFrame()

    # Define the start and end date range
    start_date = datetime.strptime("2014-07-07 00:00", "%Y-%m-%d %H:%M")
    end_date = datetime.strptime("2014-07-09 00:00", "%Y-%m-%d %H:%M")

    # Fetch the Survey Respondent Data (24-hour interval)
    survey_respondent_data = fetch_survey_respondent_data(start_date, end_date)

    # Fetch the Survey Answer Data (12-hour interval)
    #survey_answer_data = fetch_survey_answer_data(start_date, end_date)

    # Display the result in Streamlit
    if not survey_respondent_data.empty:
        st.write("Survey Respondent Data fetched successfully:")
        st.dataframe(survey_respondent_data)
    else:
        st.write("No Survey Respondent Data available for the specified range.")

    #if not survey_answer_data.empty:
    #    st.write("Survey Answer Data fetched successfully:")
    #    st.dataframe(survey_answer_data)
    #else:
    #    st.write("No Survey Answer Data available for the specified range.")

    # CONNECT SHEET SAP SECTION

    # Fetch data
    @st.cache_resource(ttl=86400)
    def fetch_data_sap():
        secret_info = st.secrets["sheets"]
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(secret_info, scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open('0. Active Employee - Monthly Updated')
        sheet = spreadsheet.sheet1
        data = sheet.get_all_records()
        df_sap = pd.DataFrame(data)
        return df_sap

    # Finalize data
    df_sap = fetch_data_sap()

    # Display data from sap
    st.write('Df_sap')
    st.dataframe(df_sap)

    # JOIN SURVER RESPONDENT AND SHEET SAP SECTION

    # Convert 'nik' column to string and ensure it is 6 digits starting with "00"
    survey_respondent_data['nik'] = survey_respondent_data['nik'].astype(str).str.zfill(6)
    df_sap['nik_short'] = df_sap['nik_short'].astype(str).str.zfill(6)

    # Now perform the merge
    df_merged = pd.merge(survey_respondent_data, df_sap, left_on='nik', right_on='nik_short', how='outer', indicator=True)

    # Display df_merged
    st.write('Df_merged')
    st.dataframe(df_merged)

    # CONCISE DATAFRAME SECTION

    # Create the new concise DataFrame
    df_concise = pd.DataFrame({
        'nik': df_merged['nik_short'].combine_first(df_merged['nik_x']),
        'unit': df_merged.apply(lambda row: row['subunit'] if row['unit_long'] == 'GROUP OF MEDIA' else row['unit_long'] if pd.notna(row['unit_long']) else row['unit_name'], axis=1),
        'division': df_merged['division'].combine_first(df_merged['div_name']),
        'department': df_merged['department'].combine_first(df_merged['dept_name']),
        'status_survey': df_merged['_merge'].apply(lambda x: 'done' if x in ['left_only', 'both'] else 'not done'),
        'admin_goman': df_merged.apply(lambda row: row['admin_goman'] if pd.notna(row['admin_goman']) else '-', axis=1)
    })

    # Replace 'Group of' with 'G.' and 'Corporate' with 'C.' in the 'unit' column
    df_concise['unit'] = df_concise['unit'].replace({'GROUP OF ': 'G. ', 'CORPORATE': 'C.'}, regex=True)

    # Display the resulting DataFrame
    st.write('Df_concise')
    st.dataframe(df_concise)

    # FILTER SECTION

    # Sidebar: Add a selectbox for unit filter
    st.sidebar.markdown('### Unit Filter')

    # Multiselect widget to select multiple units
    unit_list = list(df_concise['unit'].unique())  # Remove 'All' for multiselect
    selected_unit = st.sidebar.multiselect('Select Unit:', unit_list, default=[])  # Pre-select all by default

    # Filter the DataFrame based on the selected units
    if selected_unit:
        df_concise = df_concise[df_concise['unit'].isin(selected_unit)]

    # If 'G. MANUFACTURE' is in the selected units, show additional filter for 'Admin GOMAN'
    if 'G. MANUFACTURE' in selected_unit:
        admin_goman_list = ['All'] + list(df_concise['admin_goman'].unique())
        selected_admin_goman = st.sidebar.multiselect('Select Admin GOMAN:', admin_goman_list)

        # Filter the DataFrame based on the selected 'Admin GOMAN'
        if selected_admin_goman:
            df_concise = df_concise[df_concise['admin_goman'].isin(selected_admin_goman)]

    division_list = list(df_concise['division'].unique())
    selected_division = st.sidebar.multiselect('Select Division:', division_list, default=[])

    if selected_division:
        df_concise = df_concise[df_concise['division'].isin(selected_division)]

    department_list = list(df_concise['department'].unique())
    selected_department = st.sidebar.multiselect('Select Department:', department_list, default=[])

    if selected_department:
        df_concise = df_concise[df_concise['department'].isin(selected_department)] 

    # Sidebar: Add a selectbox for breakdown variable
    st.sidebar.markdown ('### Breakdown Variable')
    breakdown_variable = st.sidebar.selectbox('Select Breakdown Variable:', ['unit', 'division', 'department'])

    # BAR CHART SECTION 

    # Create pivot table
    final_counts = df_concise.pivot_table(index=breakdown_variable, columns='status_survey', values='nik', aggfunc='nunique', fill_value=0).reset_index()

    # Ensure both 'Active Learners' and 'Passive Learners' columns exist
    if 'done' not in final_counts:
        final_counts['done'] = 0
    if 'not done' not in final_counts:
        final_counts['not done'] = 0

    final_counts.columns = [breakdown_variable, 'Done', 'Not Done']

    # Calculate Done (%) and Not Done (%)
    final_counts['Done (%)'] = final_counts['Done'] / (final_counts['Done'] + final_counts['Not Done']) * 100
    final_counts['Not Done (%)'] = final_counts['Not Done'] / (final_counts['Done'] + final_counts['Not Done']) * 100

    # final_counts
    st.write('final_counts')
    st.write(final_counts)

    # Calculate overall status survey
    total_done = final_counts['Done'].sum()
    total_employee = final_counts['Done'].sum() + final_counts['Not Done'].sum()
    overall_status = (total_done / total_employee) * 100

    # Display the calculated percentage as a bar chart
    st.header(f'Overall Participation', divider='rainbow')

    # Display metrics column
    col1, col2, col3 = st.columns(3)
    col1.metric("Done", int(total_done))
    col2.metric("Total Employees", int(total_employee))
    col3.metric("Overall Participation", f"{overall_status:.2f}%")

    # Display the calculated percentage as a bar chart
    st.header(f'Survey Participation by {breakdown_variable.capitalize()}', divider='rainbow')

    # Transform data for Altair
    melted_counts = final_counts.melt(
        id_vars=breakdown_variable,
        value_vars=['Done', 'Not Done'],
        var_name='Survey Status',
        value_name='Count'
    )

    melted_percentage = final_counts.melt(
        id_vars=breakdown_variable,
        value_vars=['Done (%)', 'Not Done (%)'],
        var_name='Survey Status',
        value_name='Percent'
    )

    # Combine counts and percentage into a single DataFrame
    melted_counts['Percent'] = melted_percentage['Percent']

    # Create the chart
    participation_chart = alt.Chart(melted_counts).mark_bar().encode(
        y=alt.Y(f'{breakdown_variable}:N', sort='-x', axis=alt.Axis(title=breakdown_variable.capitalize())),
        x=alt.X('Percent:Q', axis=alt.Axis(title='Survey Participation (%)'), scale=alt.Scale(domain=[0, 100])),
        color=alt.Color('Survey Status:N', scale=alt.Scale(domain=['Done', 'Not Done'], range=['#1f77b4', '#ff7f0e'])),
        order=alt.Order('Survey Status:N', sort='ascending'),    # Ensure done is plotted first
        tooltip=[
            alt.Tooltip(f'{breakdown_variable}:N', title=breakdown_variable.capitalize()),
            alt.Tooltip('Survey Status:N', title='Survey Status'),
            alt.Tooltip('Count:Q', title='Count'),
            alt.Tooltip('Percent:Q', title='Percentage', format='.1f')
        ]
    ).properties(
        width=alt.Step(40)   # Adjust width as needed
    )

    # Display the chart using Streamlit
    st.altair_chart(participation_chart, use_container_width=True)

     # Logout button
    st.sidebar.markdown('### Options')
    authenticator.logout('Logout', 'sidebar')

elif st.session_state['authentication_status'] is False:
    st.error('Username/password is incorrect')
    
elif st.session_state['authentication_status'] is None:
    st.warning('Please enter your username and password')