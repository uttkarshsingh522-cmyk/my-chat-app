import streamlit as st
import google.generativeai as genai
import os

# Page configuration
st.set_page_config(page_title="UTTKARSH AI", page_icon="🤖", layout="wide")

# Custom CSS to hide Streamlit branding & display custom top banner
st.markdown("""
    <style>
    /* Hide Streamlit Header, Main Menu, Toolbar, and Footer */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}
    div[data-testid="stToolbar"] {visibility: hidden;}
    div[data-testid="stDecoration"] {display: none;}
    div[data-testid="stStatusWidget"] {display: none;}
    button[title="View app in Streamlit Community Cloud"] {display: none;}
    
    /* Custom Top Banner Styling */
    .top-banner {
        background-color: #1E1E1E;
        color: #00FFCC;
        text-align: center;
        padding: 12px;
        font-weight: bold;
        font-size: 18px;
        letter-spacing: 2px;
        border-radius: 8px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    </style>
    
    <div class="top-banner">
        ALWAYS READY WHEN YOU ARE
    </div>
""", unsafe_allow_html=True)

# Initialize Gemini API Key
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    st.error("GEMINI_API_KEY environment variable not set.")
    st.stop()

genai.configure(api_key=api_key)

# Model initialization targeting Gemini 3.6 Flash
model = genai.GenerativeModel('gemini-3.6-flash')

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input Prompt
if prompt := st.chat_input("Ask UTTKARSH AI..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            response = model.generate_content(prompt)
            message_placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                message_placeholder.error("Service is busy right now. Please try again in a few seconds.")
            else:
                message_placeholder.error(f"Error: {e}")
