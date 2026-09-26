import base64
import json
import os
import requests
import streamlit as st

# 1. Page Configuration
st.set_page_config(page_title="UTTKARSH AI", page_icon="✨", layout="wide")

# Styling to keep UI clean and fix sidebar toggle visibility
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            .stAppHeader {background-color: transparent;}
            [data-testid="stSidebarCollapseButton"] {
                visibility: visible !important;
                display: block !important;
                z-index: 999999;
            }
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
        st.session_state.current_session_id = "New Chat"
        st.session_state.all_sessions["New Chat"] = []

# 4. Sidebar Controls & Compressed History Dropdown
with st.sidebar:
    st.title("✨ UTTKARSH AI")

    if st.button("➕ New Chat", use_container_width=True):
        count = len(st.session_state.all_sessions) + 1
        new_id = f"Chat {count}"
        st.session_state.all_sessions[new_id] = []
        st.session_state.current_session_id = new_id
        save_all_sessions(st.session_state.all_sessions)
        st.rerun()

    # Compressed Chat History Expander (Closed by default until clicked)
    with st.expander("📜 Recent Chats & Search", expanded=False):
        search_query = st.text_input(
            "🔍 Search history", value="", placeholder="Search chats..."
        )

        st.markdown("---")

        # Filter sessions by search query
        all_keys = list(st.session_state.all_sessions.keys())
        for session_id in all_keys:
            messages = st.session_state.all_sessions[session_id]

            # Determine title
            display_title = (
                messages[0]["content"][:22] + "..." if messages else session_id
            )

            # Check if search keyword matches title or any message content
            matches_search = True
            if search_query.strip():
                content_text = " ".join([m["content"] for m in messages]).lower()
                if (
                    search_query.lower() not in display_title.lower()
                    and search_query.lower() not in content_text
                ):
                    matches_search = False

            if matches_search:
                is_active = session_id == st.session_state.current_session_id
                icon = "🔹" if is_active else "💬"

                if st.button(
                    f"{icon} {display_title}",
                    key=f"hist_{session_id}",
                    use_container_width=True,
                ):
                    st.session_state.current_session_id = session_id
                    st.rerun()

    st.divider()
    enable_search = st.checkbox("🌐 Enable Web Search Grounding", value=False)
    system_instruction = st.text_area(
        "System Instructions",
        value="You are UTTKARSH AI, a helpful, intelligent assistant.",
    )

    if st.button("🗑️ Clear All Chats", use_container_width=True):
        st.session_state.all_sessions = {"New Chat": []}
        st.session_state.current_session_id = "New Chat"
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
    current_messages.append({"role": "user", "content": user_prompt})

    # Dynamically update thread name based on initial user query
    if (
        len(current_messages) == 1
        and st.session_state.current_session_id.startswith(("Chat ", "New Chat"))
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
