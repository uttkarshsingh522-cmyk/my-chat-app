import streamlit as st
import requests

st.set_page_config(page_title="UTTKARSH AI Chatbot", page_icon="🤖")

# --- PASSWORD PROTECTION ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.title("🔒 Security Login")
        user_password = st.text_input("Enter Password to Access Chatbot:", type="password")
        if st.button("Login"):
            if "PASSWORD" in st.secrets and user_password == st.secrets["PASSWORD"]:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Incorrect Password. Please try again.")
        return False
    return True

if check_password():
    # --- APP INTERFACE & STYLING ---
    st.title("🤖 UTTKARSH AI Chatbot")

    # Retrieve secrets
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # --- SIDEBAR CONTROLS ---
    with st.sidebar:
        st.header("⚙️ Chat Options")

        # Option 1: New Chat / Clear Chat
        if st.button("➕ New Chat"):
            st.session_state.messages = []
            st.rerun()

        # Option 2: Search Chat
        search_query = st.text_input("🔍 Search Chat History:")

        # Option 3: Delete Chat
        if st.button("🗑️ Delete All Chat"):
            st.session_state.messages = []
            st.success("Chat history deleted!")
            st.rerun()

        st.markdown("---")
        if st.button("🚪 Logout"):
            st.session_state["authenticated"] = False
            st.rerun()

    # --- CHAT DISPLAY & FILTERING ---
    # Display search results if search bar has text
    if search_query:
        st.subheader(f"Search Results for: '{search_query}'")
        found = False
        for msg in st.session_state.messages:
            if search_query.lower() in msg["content"].lower():
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
                found = True
        if not found:
            st.info("No matching messages found.")
    else:
        # Regular chat history display
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

    # --- USER INPUT & API CALL ---
    if user_prompt := st.chat_input("Ask something..."):
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.write(user_prompt)

        # Working REST Endpoint
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": user_prompt}]}]}

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = requests.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    bot_reply = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                    st.write(bot_reply)
                    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                else:
                    st.error(f"Error {response.status_code}: {response.text}")
