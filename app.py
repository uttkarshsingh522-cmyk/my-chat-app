import streamlit as st
import os

# Set page configuration with initial sidebar state open
st.set_page_config(
    page_title="UTTKARSH AI", 
    page_icon="🤖", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for UI cleanup and custom header styling
st.markdown("""
    <style>
    /* Hide Streamlit Footer and Deploy Elements */
    footer {visibility: hidden !important;}
    .stAppDeployButton {display: none !important;}
    button[title="View app in Streamlit Community Cloud"] {display: none !important;}
    .viewerBadge_container__163Vn {display: none !important;}

    /* Top Banner Styling */
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

    /* Sidebar Title Banner */
    .sidebar-banner {
        background-color: #0E1117;
        color: #00FFCC;
        text-align: center;
        padding: 10px;
        font-weight: bold;
        font-size: 16px;
        letter-spacing: 1.5px;
        border-bottom: 2px solid #00FFCC;
        margin-bottom: 15px;
        border-radius: 6px;
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
    st.error("Missing required packages. Ensure 'streamlit', 'google-generativeai', and 'Pillow' are in requirements.txt.")
    st.stop()

# Initialize Gemini API Key
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    st.error("GEMINI_API_KEY environment variable is not set.")
    st.stop()

genai.configure(api_key=api_key)

# Fast Gemini Flash model initialization
model_name = "gemini-1.5-flash"
try:
    model = genai.GenerativeModel(model_name)
except Exception:
    model = genai.GenerativeModel("gemini-1.5-flash")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Dialog for Search Chat
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
    st.markdown('<div class="sidebar-banner">WELCOME TO UTTKARSH AI</div>', unsafe_allow_html=True)
    st.title("⚙️ Controls")
    
    # 1. Search Button
    if st.button("🔍 Search Chat", use_container_width=True):
        if not st.session_state.messages:
            st.toast("No past chats available yet!")
        else:
            search_dialog()

    # 2. Delete Chat Button
    if st.button("🗑️ Delete Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
        
    st.divider()
    
    # 3. File & Image Upload Widget
    st.subheader("📎 Attach Files / Images")
    uploaded_file = st.file_uploader("Upload Image or Document", type=["png", "jpg", "jpeg", "webp", "pdf", "txt"])

# Display Existing Chat Messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "image" in message and message["image"] is not None:
            st.image(message["image"], use_column_width=True)

# Streaming Response Generator Function
def stream_response(prompt_content):
    response_stream = model.generate_content(prompt_content, stream=True)
    for chunk in response_stream:
        if chunk.text:
            yield chunk.text

# User Input Box
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

    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt, "image": img})
    
    with st.chat_message("user"):
        st.markdown(prompt)
        if img:
            st.image(img, use_column_width=True)

    # Stream Response in Real Time
    with st.chat_message("assistant"):
        try:
            full_response = st.write_stream(stream_response(prompt_content))
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                st.error("Service is temporarily busy. Please send your message again.")
            else:
                st.error(f"Error: {e}")
