import streamlit as st
import pandas as pd
from data_processing import finalize_data
import streamlit_authenticator as stauth

# Fetch the credentials and survey data
df_survey, df_creds = finalize_data()

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
            'unit': row['unit']  # Store the user's unit for later filtering
        }
    return credentials

# Extract credentials from df_creds
credentials = extract_credentials(df_creds)

# Verify credentials structure (for debugging, can be removed later)
st.write("Credentials passed to authenticator:", credentials['credentials'])

# Authentication Setup
authenticator = stauth.Authenticate(
    credentials['credentials'],
    credentials['cookie']['name'],
    credentials['cookie']['key'],
    credentials['cookie']['expiry_days']
)

# Display the login form
name, authentication_status, username = authenticator.login('main')

st.write("Name:", name)
st.write("Authentication Status:", authentication_status)
st.write("Username:", username)

# Handle authentication status
if authentication_status:
    # Get the unit for the logged-in user from the credentials
    user_unit = credentials['credentials']['usernames'][username]['unit']
    
    # Welcome message and user's unit
    st.sidebar.write(f"Welcome {name} from {user_unit}!")
    
    # Filter survey data based on the logged-in user's unit
    filtered_survey = df_survey[df_survey['unit'] == user_unit]
    
    # Display filtered survey data
    st.title(f'Survey Data for {user_unit}')
    st.write(filtered_survey.head())
    
    # Logout button
    authenticator.logout('Logout', 'sidebar')

elif authentication_status == False:
    st.error("Username/password is incorrect")

elif authentication_status == None:
    st.warning("Please enter your username and password")
