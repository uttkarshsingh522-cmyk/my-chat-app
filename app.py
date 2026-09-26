import base64
import json
import os
import requests
import streamlit as st

# 1. Page Configuration & Native App Styling
st.set_page_config(page_title="UTTKARSH AI", page_icon="✨", layout="wide")

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            .stAppHeader {display: none;}
            .stChatMessage {border-radius: 12px; padding: 10px; margin-bottom: 8px;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

SESSIONS_FILE = "chat_sessions.json"


# 2. Session Management Functions
def load_all_sessions():
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_all_sessions(sessions):
    with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)


# 3. Initialize Session State
if "all_sessions" not in st.session_state:
    st.session_state.all_sessions = load_all_sessions()

if "current_session_id" not in st.session_state:
    if st.session_state.all_sessions:
        st.session_state.current_session_id = list(
            st.session_state.all_sessions.keys()
        )[0]
    else:
        st.session_state.current_session_id = "Chat 1"
        st.session_state.all_sessions["Chat 1"] = []

# 4. Sidebar Controls & Clickable Chat History
with st.sidebar:
    st.title("✨ UTTKARSH AI")

    if st.button("➕ New Chat", use_container_width=True):
        new_id = f"Chat {len(st.session_state.all_sessions) + 1}"
        st.session_state.all_sessions[new_id] = []
        st.session_state.current_session_id = new_id
        save_all_sessions(st.session_state.all_sessions)
        st.rerun()

    st.subheader("📜 Recent Chats")

    # Render a clickable button for each past conversation thread
    for session_id in list(st.session_state.all_sessions.keys()):
        messages = st.session_state.all_sessions[session_id]
        # Use first message as title if available
        title = messages[0]["content"][:20] + "..." if messages else session_id

        # Highlight current active chat
        button_label = (
            f"💬 {title}"
            if session_id != st.session_state.current_session_id
            else f"👉 {title}"
        )
        if st.button(button_label, key=f"btn_{session_id}"):
            st.session_state.current_session_id = session_id
            st.rerun()

    st.divider()
    enable_search = st.checkbox("🌐 Enable Web Search Grounding", value=False)
    system_instruction = st.text_area(
        "System Instructions",
        value="You are UTTKARSH AI, a helpful, intelligent assistant.",
    )

    if st.button("🗑️ Clear All Chats"):
        st.session_state.all_sessions = {"Chat 1": []}
        st.session_state.current_session_id = "Chat 1"
        save_all_sessions(st.session_state.all_sessions)
        st.rerun()

# 5. Get current active chat messages
current_messages = st.session_state.all_sessions.get(
    st.session_state.current_session_id, []
)

# Render active chat thread
for msg in current_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 6. Multimodal Attachment Input
uploaded_file = st.file_uploader(
    "Attach image or document (optional)", type=["png", "jpg", "jpeg", "pdf"]
)

# 7. User Input & Gemini API Streaming Call
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")

if user_prompt := st.chat_input("Ask UTTKARSH AI..."):
    # Append user prompt to current active thread
    current_messages.append({"role": "user", "content": user_prompt})

    # Rename session label dynamically from first question
    if (
        len(current_messages) == 1
        and st.session_state.current_session_id.startswith("Chat ")
    ):
        new_title = (
            user_prompt[:25] + "..." if len(user_prompt) > 25 else user_prompt
        )
        st.session_state.all_sessions[new_title] = st.session_state.all_sessions.pop(
            st.session_state.current_session_id
        )
        st.session_state.current_session_id = new_title

    st.session_state.all_sessions[
        st.session_state.current_session_id
    ] = current_messages
    save_all_sessions(st.session_state.all_sessions)

    with st.chat_message("user"):
        st.markdown(user_prompt)

    # Send last 6 messages of current session to stay within quota
    recent_messages = current_messages[-6:]
    contents = []
    for msg in recent_messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})

    if uploaded_file:
        bytes_data = uploaded_file.read()
        b64_data = base64.b64encode(bytes_data).decode("utf-8")
        contents[-1]["parts"].append({
            "inline_data": {
                "mime_type": uploaded_file.type,
                "data": b64_data,
            }
        })

    payload = {
        "contents": contents,
        "systemInstruction": {"parts": [{"text": system_instruction}]},
    }

    if enable_search:
        payload["tools"] = [{"googleSearch": {}}]

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:streamGenerateContent?alt=sse&key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""

        response = requests.post(
            url, headers=headers, json=payload, stream=True
        )
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    line_text = line.decode("utf-8")
                    if line_text.startswith("data: "):
                        try:
                            data = json.loads(line_text[6:])
                            chunk = data["candidates"][0]["content"]["parts"][
                                0
                            ]["text"]
                            full_response += chunk
                            response_placeholder.markdown(full_response + "▌")
                        except (KeyError, IndexError, json.JSONDecodeError):
                            pass
            response_placeholder.markdown(full_response)

            current_messages.append(
                {"role": "assistant", "content": full_response}
            )
            st.session_state.all_sessions[
                st.session_state.current_session_id
            ] = current_messages
            save_all_sessions(st.session_state.all_sessions)
        else:
            st.error(f"Error {response.status_code}: {response.text}")
