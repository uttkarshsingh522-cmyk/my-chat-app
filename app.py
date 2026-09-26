import base64
import json
import os
import requests
import streamlit as st

# 1. Page Configuration & Native App Styling
st.set_page_config(
    page_title="UTTKARSH AI", page_icon="✨", layout="wide"
)

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

HISTORY_FILE = "chat_history.json"


# 2. JSON History Storage Functions
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_history(messages):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)


# 3. Initialize Chat History State
if "messages" not in st.session_state:
    st.session_state.messages = load_history()

# 4. Sidebar Controls (Displaying AI 3.6)
with st.sidebar:
    st.title("✨ UTTKARSH AI")

    # Display option shows "AI 3.6" directly in the dropdown menu
    model_display = st.selectbox(
        "Select Model",
        [
            "AI 3.6 (Gemini 3.6 Flash)",
            "AI 3.5 (Gemini 3.5 Flash-Lite)",
            "AI 3.1 Pro (Gemini 3.1 Pro)",
        ],
    )

    # Map display names to Gemini API endpoints
    model_mapping = {
        "AI 3.6 (Gemini 3.6 Flash)": "gemini-3.6-flash",
        "AI 3.5 (Gemini 3.5 Flash-Lite)": "gemini-3.5-flash-lite",
        "AI 3.1 Pro (Gemini 3.1 Pro)": "gemini-3.1-pro-preview",
    }
    selected_api_model = model_mapping[model_display]

    enable_search = st.checkbox("🌐 Enable Web Search Grounding", value=False)
    system_instruction = st.text_area(
        "System Instructions",
        value="You are UTTKARSH AI, a helpful, intelligent assistant.",
    )

    if st.button("➕ New Chat"):
        st.session_state.messages = []
        save_history([])
        st.rerun()

    if st.button("🗑️ Clear History"):
        st.session_state.messages = []
        save_history([])
        st.rerun()

# 5. Render Saved Chat Messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 6. Multimodal Attachment Input
uploaded_file = st.file_uploader(
    "Attach image or document (optional)", type=["png", "jpg", "jpeg", "pdf"]
)

# 7. User Input & Gemini API Streaming Call
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")

if user_prompt := st.chat_input("Ask UTTKARSH AI..."):
    # Append user prompt and save locally
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    save_history(st.session_state.messages)

    with st.chat_message("user"):
        st.markdown(user_prompt)

    # Send last 6 messages to keep context active while preventing rate limits
    recent_messages = st.session_state.messages[-6:]
    contents = []
    for msg in recent_messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})

    # Add file attachment if uploaded
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

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{selected_api_model}:streamGenerateContent?alt=sse&key={GEMINI_API_KEY}"
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

            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )
            save_history(st.session_state.messages)
        else:
            st.error(f"Error {response.status_code}: {response.text}")
