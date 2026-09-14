import streamlit as st
import requests
import json

# Replace your previous USER INPUT & API CALL section with this:
if user_prompt := st.chat_input("Ask something..."):
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.write(user_prompt)

    # Gemini REST API streaming endpoint
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:streamGenerateContent?alt=sse&key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": user_prompt}]}]}

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        # Stream response chunks live
        response = requests.post(url, headers=headers, json=payload, stream=True)
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    if line_text.startswith("data: "):
                        data = json.loads(line_text[6:])
                        try:
                            chunk = data["candidates"][0]["content"]["parts"][0]["text"]
                            full_response += chunk
                            response_placeholder.markdown(full_response + "▌")
                        except (KeyError, IndexError):
                            pass
            response_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        else:
            st.error(f"Error {response.status_code}: {response.text}")
