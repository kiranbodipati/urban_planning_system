import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

st.title('Welcome to U.P.S.E.T.!')
st.markdown('UPSET stands for **Urban Planning System for Enhancement of Transport**.')
st.markdown('Our goal is to provide insights into lacking public transport infrastructure in Singapore, so that \
those concerned know what to focus on improving first.')
st.markdown("""
### Instructions for use:
 - Check out the Bus Analysis and MRT Analysis tabs for stats and visualizations on the current state of public transport
 - Use the Suggested Improvements tab to browse our insights and recommendations
""")