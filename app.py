import streamlit as st
import os

# Set page configuration first
st.set_page_config(page_title="UTTKARSH AI", page_icon="🤖", layout="wide")

# Custom CSS to hide all Streamlit interface elements and add top banner
st.markdown("""
    <style>
    /* Hide Streamlit Header, Main Menu, Footer, and Toolbar */
    #MainMenu {visibility: hidden !important;}
    header {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    .stAppDeployButton {display: none !important;}
    div[data-testid="stToolbar"] {visibility: hidden !important;}
    div[data-testid="stDecoration"] {display: none !important;}
    div[data-testid="stStatusWidget"] {display: none !important;}
    button[title="View app in Streamlit Community Cloud"] {display: none !important;}
    .viewerBadge_container__163Vn {display: none !important;}
    
    /* Top Persistent Banner */
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

# Import google.generativeai with error handling
try:
    import google.generativeai as genai
except ModuleNotFoundError:
    st.error("The package 'google-generativeai' is missing. Make sure 'requirements.txt' is added to your GitHub repository.")
    st.stop()

# Initialize Gemini API Key
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    st.error("GEMINI_API_KEY is not set in Secrets/Environment Variables.")
    st.stop()

genai.configure(api_key=api_key)

# Initialize Model with fallback handling for custom version strings
model_name = "gemini-3.6-flash"
try:
    model = genai.GenerativeModel(model_name)
except Exception:
    # Fallback to standard supported Flash tier if specific model string fails
    model = genai.GenerativeModel("gemini-1.5-flash")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Existing Chat Messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input Box
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
                message_placeholder.error("Service is experiencing high demand. Please try sending your request again.")
            else:
                message_placeholder.error(f"Error generating response: {e}")
