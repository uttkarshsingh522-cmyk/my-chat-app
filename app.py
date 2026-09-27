import streamlit as st
import os
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="UTTKARSH AI", 
    page_icon="🤖", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for UI styling
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

    /* History List Items */
    .history-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 14px;
        margin-bottom: 8px;
        border-radius: 8px;
        background-color: #1a1c23;
        border: 1px solid #2d313e;
    }
    </style>
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

# Initialize Gemini 3.6 Flash model
MODEL_ID = "gemini-3.6-flash"
model = genai.GenerativeModel(MODEL_ID)

# Initialize Session States
if "messages" not in st.session_state:
    st.session_state.messages = []

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "chat"  # Options: "chat" or "search"

# Sample default search history list (Matches screenshot structure)
if "chat_history_list" not in st.session_state:
    st.session_state.chat_history_list = [
        {"title": "Building a Python ChatGPT Clone", "date": "Today"},
        {"title": "How to Close Running Programs", "date": "Yesterday"},
        {"title": "How to Install Android APK", "date": "Yesterday"},
        {"title": "Offline Music Player Apps Guide", "date": "Sep 25"},
        {"title": "NCERT Class 11 Math Activity", "date": "Sep 25"},
        {"title": "Class 11 IP Data Handling Notes", "date": "Sep 23"},
        {"title": "Windows 11 System Requirements", "date": "Sep 23"},
        {"title": "Pandas Data Handling Exam Cheat Sheet", "date": "Sep 23"},
        {"title": "Fix Missing .NET Framework Error", "date": "Sep 12"},
    ]

# Sidebar Controls
with st.sidebar:
    st.markdown('<div class="sidebar-banner">WELCOME TO UTTKARSH AI</div>', unsafe_allow_html=True)
    st.title("⚙️ Controls")
    
    # Navigation Buttons
    if st.session_state.view_mode == "search":
        if st.button("💬 Back to Chat", use_container_width=True):
            st.session_state.view_mode = "chat"
            st.rerun()
    else:
        if st.button("🔍 Search Chat", use_container_width=True):
            st.session_state.view_mode = "search"
            st.rerun()

    # 2. Delete Chat Button
    if st.button("🗑️ Delete Chat History", use_container_width=True):
        st.session_state.messages = []
        st.toast("Chat history cleared!")
        st.rerun()
        
    st.divider()
    
    # 3. File & Image Upload Widget
    st.subheader("📎 Attach Files / Images")
    uploaded_file = st.file_uploader("Upload Image or Document", type=["png", "jpg", "jpeg", "webp", "pdf", "txt"])

# ==========================================
# PAGE VIEW 1: SEARCH CHAT HISTORY INTERFACE
# ==========================================
if st.session_state.view_mode == "search":
    st.markdown('<div class="top-banner">SEARCH CHATS</div>', unsafe_allow_html=True)
    
    # Centered Search Bar
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        search_query = st.text_input("🔍 Search chats", placeholder="Search chats...", label_visibility="collapsed")
        st.write("")
        st.subheader("Recent")
        
        # Filter Chat History
        filtered_history = st.session_state.chat_history_list
        if search_query.strip():
            filtered_history = [
                item for item in st.session_state.chat_history_list 
                if search_query.lower() in item["title"].lower()
            ]

        # Display History List
        if filtered_history:
            for item in filtered_history:
                col_title, col_date = st.columns([4, 1])
                with col_title:
                    if st.button(f"💬 {item['title']}", key=f"hist_{item['title']}", use_container_width=True):
                        st.session_state.view_mode = "chat"
                        st.rerun()
                with col_date:
                    st.caption(f"**{item['date']}**")
        else:
            st.info("No matching chat history found.")

# ==========================================
# PAGE VIEW 2: REGULAR CHAT INTERFACE
# ==========================================
else:
    st.markdown('<div class="top-banner">ALWAYS READY WHEN YOU ARE</div>', unsafe_allow_html=True)

    # Display Existing Chat Messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "image" in message and message["image"] is not None:
                st.image(message["image"], use_column_width=True)

    # Streaming Generator for response
    def stream_response(prompt_content):
        response_stream = model.generate_content(prompt_content, stream=True)
        for chunk in response_stream:
            if chunk.text:
                yield chunk.text

    # User Input Box
    if prompt := st.chat_input("Ask UTTKARSH AI..."):
        img = None
        prompt_content = [prompt]
        
        # Add new chat entry to search history list dynamically if first prompt
        if len(st.session_state.messages) == 0:
            title_text = prompt[:35] + "..." if len(prompt) > 35 else prompt
            st.session_state.chat_history_list.insert(0, {
                "title": title_text,
                "date": "Today"
            })

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

        # Stream Response Live
        with st.chat_message("assistant"):
            try:
                full_response = st.write_stream(stream_response(prompt_content))
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            except Exception as e:
                if "503" in str(e) or "UNAVAILABLE" in str(e):
                    st.error("Service is temporarily busy. Please send your message again.")
                else:
                    st.error(f"Error: {e}")
