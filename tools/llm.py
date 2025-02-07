from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import streamlit as st

OPENAI_API_KEY = st.secrets["openai"]["OPENAI_API_KEY"]

llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4o-mini")
