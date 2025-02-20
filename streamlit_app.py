import streamlit as st
import json
from openai import OpenAI

# App title
st.title("💬 Chatbot with Memory")
st.write("This chatbot uses OpenAI's GPT-3.5 and remembers context across chats.")

# OpenAI API Key input
openai_api_key = st.text_input("OpenAI API Key", type="password")
if not openai_api_key:
    st.info("Please enter your OpenAI API key.", icon="🔑")
    st.stop()

# Create OpenAI client
client = OpenAI(api_key=openai_api_key)

# Files for saving chat history and context
HISTORY_FILE = "chat_history.json"
CONTEXT_FILE = "chat_context.json"

# Load chat history from file
def load_chat_history():
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Save chat history to file
def save_chat_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

# Load context from file
def load_context():
    try:
        with open(CONTEXT_FILE, "r") as f:
            return json.load(f).get("context", "")
    except FileNotFoundError:
        return "You are a helpful assistant."

# Save context to file
def save_context(context):
    with open(CONTEXT_FILE, "w") as f:
        json.dump({"context": context}, f, indent=4)

# Extract important context automatically
def extract_relevant_context(response_text):
    """
    Extracts key details from responses and stores them in context.
    """
    # Example: Identify sentences containing key phrases (modify as needed)
    important_info = []
    for line in response_text.split(". "):
        if any(keyword in line.lower() for keyword in ["you are", "remember that", "your name is", "your task is"]):
            important_info.append(line)
    
    if important_info:
        new_context = "\n".join(important_info)
        st.session_state.context += f"\n{new_context}"
        save_context(st.session_state.context)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "full_chat_history" not in st.session_state:
    st.session_state.full_chat_history = load_chat_history()

if "context" not in st.session_state:
    st.session_state.context = load_context()

# Display stored context
st.write("### Stored Context:")
st.write(st.session_state.context)

# Button to load previous chat history
if st.button("Load Previous Chats"):
    st.session_state.messages = st.session_state.full_chat_history

# Display previous chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Type your message..."):
    
    # Store user input
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Prepare full prompt with context
    full_prompt = f"Context: {st.session_state.context}\nUser: {prompt}"
    
    # Generate AI response
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": st.session_state.context}] + st.session_state.messages,
        stream=True,
    )
    
    # Collect response
    response_text = ""
    with st.chat_message("assistant"):
        response_container = st.empty()
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                response_text += chunk.choices[0].delta.content
                response_container.markdown(response_text)
    
    # Store response
    st.session_state.messages.append({"role": "assistant", "content": response_text})
    
    # Extract and update context automatically
    extract_relevant_context(response_text)
    
    # Update full chat history and save
    st.session_state.full_chat_history.extend([
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": response_text},
    ])
    save_chat_history(st.session_state.full_chat_history)

# Reset chat (only clears session, keeps saved history and context)
if st.button("Reset Chat"):
    st.session_state.messages = []  # Clears session chat only
    st.rerun()