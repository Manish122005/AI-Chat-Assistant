import os
from dotenv import load_dotenv
import streamlit as st
from google import genai
from google.genai import types

# Load API key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Initialize client
client = genai.Client(api_key=api_key)

st.set_page_config(page_title="Chatbot with Streamlit and Gemini", page_icon="🤖")

st.title("My Personal Chat-Assistant 🤖")
st.write("Ask me anything!")

# Chat history (keeps the raw list for the Streamlit UI)
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history on rerun
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
user_input = st.chat_input("Type your message here...")

if user_input:
    # 1. Immediately show user message on UI
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking... 💭"):
            try:
                # 2. Convert st.session_state history into the format Google expects natively
                api_history = []
                for msg in st.session_state.messages:
                    # Map 'assistant' back to the API's expected 'model' role
                    api_role = "model" if msg["role"] == "assistant" else "user"
                    api_history.append(
                        types.Content(
                            role=api_role,
                            parts=[types.Part.from_text(text=msg["content"])]
                        )
                    )

                # 3. Initialize Google's native multi-turn chat helper with our existing history
                chat = client.chats.create(
                    model="gemini-2.5-flash",
                    history=api_history
                )

                # 4. Send the new message through the native manager
                response = chat.send_message(user_input)
                ai_message = response.text

                # 5. Output response and commit BOTH messages to session state on success
                st.markdown(ai_message)
                st.session_state.messages.append({"role": "user", "content": user_input})
                st.session_state.messages.append({"role": "assistant", "content": ai_message})

            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    st.error("⚠️ Woohoo, slow down! You've hit the Gemini API free-tier rate limit. Please wait a few seconds and try again.")
                elif "503" in str(e) or "UNAVAILABLE" in str(e):
                    st.error("🔄 The server is temporarily busy handling high demand. Let's give it a moment and try that complex prompt again!")
                else:
                    st.error(f"Error generating response: {e}")