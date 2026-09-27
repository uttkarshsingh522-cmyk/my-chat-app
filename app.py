import streamlit as st
import os

# Page configuration
st.set_page_config(page_title="UTTKARSH AI", page_icon="🤖", layout="wide")

# Custom CSS to hide default Streamlit UI elements and style top banner
st.markdown("""
    <style>
    /* Hide Streamlit Header, Main Menu, Toolbar, and Footer */
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

# Import google.generativeai and PIL safely
try:
    import google.generativeai as genai
    from PIL import Image
except ModuleNotFoundError:
    st.error("Missing required packages. Make sure 'streamlit', 'google-generativeai', and 'Pillow' are in requirements.txt.")
    st.stop()

# Initialize Gemini API Key
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    st.error("GEMINI_API_KEY environment variable is not set.")
    st.stop()

genai.configure(api_key=api_key)

# Initialize Gemini 3.6 Flash model with standard fallback
model_name = "gemini-3.6-flash"
try:
    model = genai.GenerativeModel(model_name)
except Exception:
    model = genai.GenerativeModel("gemini-1.5-flash")

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# Modal dialog for Search Chat feature
@st.dialog("🔍 Search Previous Chats")
def search_dialog():
    query = st.text_input("Type a keyword or phrase to search:", placeholder="e.g., Python, AI, project...")
    st.divider()
    
    if query.strip():
        results = [
            msg for msg in st.session_state.messages 
            if query.lower() in msg["content"].lower()
        ]
        if results:
            st.write(f"Found **{len(results)}** matching message(s):")
            for msg in results:
                role_label = "👤 User" if msg["role"] == "user" else "🤖 UTTKARSH AI"
                with st.expander(f"{role_label}: {msg['content'][:40]}..."):
                    st.write(msg["content"])
        else:
            st.info("No matching conversations found.")
    else:
        st.write("All Past Messages:")
        for msg in st.session_state.messages:
            role_label = "👤 User" if msg["role"] == "user" else "🤖 UTTKARSH AI"
            with st.expander(f"{role_label}: {msg['content'][:50]}..."):
                st.write(msg["content"])

# Sidebar Controls
with st.sidebar:
    st.title("⚙️ Controls")
    
    # 1. Clickable Search Button opens full chat search overlay
    if st.button("🔍 Search Chat", use_container_width=True):
        if not st.session_state.messages:
            st.toast("No past chats available yet!")
        else:
            search_dialog()

    # 2. Clear / Delete Chat Option
    if st.button("🗑️ Delete Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
        
    st.divider()
    
    # 3. File & Image Upload Option
    st.subheader("📎 Attach Files / Images")
    uploaded_file = st.file_uploader("Upload Image or Document", type=["png", "jpg", "jpeg", "webp", "pdf", "txt"])

# Display Main Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "image" in message and message["image"] is not None:
            st.image(message["image"], use_column_width=True)

# Main Input Box
if prompt := st.chat_input("Ask UTTKARSH AI..."):
    img = None
    prompt_content = [prompt]
    
    if uploaded_file is not None:
        file_type = uploaded_file.name.split(".")[-1].lower()
        if file_type in ["png", "jpg", "jpeg", "webp"]:
            img = Image.open(uploaded_file)
            prompt_content.append(img)
        elif file_type in ["txt", "pdf"]:
            text_content = uploaded_file.read().decode("utf-8", errors="ignore")
            prompt_content[0] += f"\n\n[Attached File Content]:\n{text_content}"

    # Save user message
    st.session_state.messages.append({"role": "user", "content": prompt, "image": img})
    
    with st.chat_message("user"):
        st.markdown(prompt)
        if img:
            st.image(img, use_column_width=True)

    # Generate Response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            response = model.generate_content(prompt_content)
            message_placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                message_placeholder.error("Service is temporarily busy. Please send your message again.")
            else:
                message_placeholder.error(f"Error: {e}")
