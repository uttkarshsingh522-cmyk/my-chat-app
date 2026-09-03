import streamlit as st
import requests

# ==========================================
# CONFIGURATION - SET YOUR KEY & PASSWORD HERE
# ==========================================
GEMINI_API_KEY = "AQ.Ab8RN6LanO_T2kujuH20sB0ZNEDqxtrcXX631Rkc04IXGQeKTQ"  # Paste your Gemini API key inside quotes
APP_PASSWORD = "UTTKARSH6234"                        # Set your desired login password

# Page Setup
st.set_page_config(page_title="My Custom ChatGPT", page_icon="🤖", layout="centered")

# Initialize authentication state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# ==========================================
# 1. LOGIN SCREEN
# ==========================================
if not st.session_state.authenticated:
    st.title("🔒 Password Protected AI")
    user_password = st.text_input("Enter Password:", type="password")
    
    if st.button("Login"):
        if user_password == APP_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect Password!")
    st.stop()

# ==========================================
# 2. MAIN CHAT APPLICATION
# ==========================================
st.title("🤖 My Custom ChatGPT")

# Sidebar
with st.sidebar:
    st.header("Settings")
    system_prompt = st.text_area(
        "System Instructions (Optional):", 
        value="You are a helpful, knowledgeable, and polite AI assistant."
    )
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()
        
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

# Initialize message history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Chat Input
if prompt := st.chat_input("Ask me anything..."):
    # Save user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response from Gemini
    with st.chat_message("assistant"):
        try:
            # Format history for Gemini REST API
            contents = []
            for msg in st.session_state.messages:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({"role": role, "parts": [{"text": msg["content"]}]})

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": contents,
                "systemInstruction": {"parts": [{"text": system_prompt}]}
            }
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(url, json=payload, headers=headers)
            data = response.json()

            if response.status_code == 200:
                ai_reply = data["candidates"][0]["content"]["parts"][0]["text"]
                st.markdown(ai_reply)
                st.session_state.messages.append({"role": "assistant", "content": ai_reply})
            else:
                error_msg = data.get("error", {}).get("message", "Unknown API error")
                st.error(f"API Error ({response.status_code}): {error_msg}")

        except Exception as e:
            st.error(f"Connection Error: {str(e)}")
