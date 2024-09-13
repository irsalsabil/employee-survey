import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from data_processing import finalize_data

credentials = st.secrets["credentials"]

authenticator = stauth.Authenticate(
    credentials, 
    st.secrets["cookie"]["name"],
    st.secrets["cookie"]["key"], 
    st.secrets["cookie"]["expiry_days"]
)

name, authentication_status, username = authenticator.login('main')

if authentication_status:
    # Welcome message and HR unit
    user_unit = credentials["usernames"][username]["unit"]
    st.write(f"Welcome {name} from {user_unit}")
    
    # Fetch and filter data for the logged-in user's HR unit
    df = finalize_data()
    
    # Assuming 'unit' is a column in your dataframe
    filtered_data = df[df['unit'] == user_unit]
    
    # Display the filtered data
    st.write(filtered_data.head())

    # Logout button
    authenticator.logout('Logout', 'sidebar')

elif authentication_status == False:
    st.error("Username/password is incorrect")
elif authentication_status == None:
    st.warning("Please enter your username and password")