import streamlit as st
import pandas as pd
import numpy as np
from fetch_data import fetch_data_survey, fetch_data_creds

@st.cache_data(ttl=86400)
def finalize_data():
    df_survey = fetch_data_survey()
    df_creds = fetch_data_creds()
    return df_survey, df_creds