import streamlit as st
import pandas as pd
import numpy as np
from fetch_data import fetch_data

@st.cache_data(ttl=86400)
def finalize_data():
    df = fetch_data()
    return df