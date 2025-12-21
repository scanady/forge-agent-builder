"""
Streamlit frontend for the Forge Requirements Assistant.

Implements the UI specification from plan.md Section 7.3.
Phase 5 tasks: 5.1-5.5
"""

import streamlit as st
import uuid
import sys
import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from audio_recorder_streamlit import audio_recorder
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.requirements_elicitation_agent.graph import create_graph


def transcribe_audio(audio_bytes: bytes) -> str:
    """Transcribe audio bytes to text using OpenAI Whisper API."""
    client = OpenAI()
    
    # Save audio to a temporary file (Whisper API requires a file)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
        temp_audio.write(audio_bytes)
        temp_audio_path = temp_audio.name
    
    try:
        with open(temp_audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
        return transcript.strip()
    finally:
        # Clean up temp file
        os.unlink(temp_audio_path)


# Page configuration (Task 5.1)
st.set_page_config(
    page_title="Forge Requirements Assistant",
    page_icon="🔥",
    layout="centered"
)

# Initialize session state (Task 5.1)
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "processed_files" not in st.session_state:
    st.session_state.processed_files = set()
if "graph" not in st.session_state:
    st.session_state.graph = create_graph()
if "audio_processed" not in st.session_state:
    st.session_state.audio_processed = None

# Title and description
st.title("🔥 Forge Requirements Assistant")
st.markdown("""
*Your partner in discovering software requirements through structured discovery*

I help you bridge the gap between vague ideas and executable software requirements 
through interactive interviews and document analysis.
""")

# Voice interface link
st.info("🎤 **Voice Interface Available!** Run the voice server with:\n```\npython src/requirements_elicitation_agent/voice_agent/run.py\n```\nThen open http://localhost:8000")

# Sidebar (Task 5.2)
with st.sidebar:
    st.header("Options")
    
    # Voice Input Section
    st.subheader("🎤 Voice Input")
    audio_bytes = audio_recorder(
        text="Click to record",
        recording_color="#e74c3c",
        neutral_color="#3498db",
        icon_size="2x",
        pause_threshold=2.0,
    )
    
    st.divider()
    
    # File uploader (Task 5.2)
    uploaded_file = st.file_uploader(
        "Upload Document",
        type=["txt", "md"],
        help="Upload meeting notes, specs, or other requirement documents"
    )
    
    # Clear chat button (Task 5.2)
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.processed_files = set()
        st.rerun()
    
    st.divider()
    
    # Requirements counter (Task 5.2)
    if st.session_state.messages:
        # Count requirements from state
        try:
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            state = st.session_state.graph.get_state(config)
            req_count = len(state.values.get("requirements", []))
            st.metric("Requirements Captured", req_count)
        except:
            pass
    
    st.divider()
    
    # Help section
    with st.expander("ℹ️ How to Use"):
        st.markdown("""
**Getting Started:**
1. Choose interactive discovery or upload a document
2. Answer my questions or review extracted requirements
3. When ready, ask me to "show requirements"

**Voice Input:**
- Click the microphone to start recording
- Speak clearly and pause when done
- Your speech will be transcribed automatically

**Tips:**
- Be as specific as possible
- I'll ask follow-up questions to clarify
- You can upload documents anytime
- I track conflicts and risks automatically
        """)

# Handle file upload (Task 5.4)
if uploaded_file and uploaded_file.name not in st.session_state.processed_files:
    # Save file temporarily using cross-platform temp directory
    import tempfile
    temp_dir = Path(tempfile.gettempdir())
    temp_path = temp_dir / uploaded_file.name
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Add file message
    file_message = f"I uploaded a file: {temp_path}"
    st.session_state.messages.append({"role": "human", "content": file_message})
    st.session_state.processed_files.add(uploaded_file.name)
    
    # Process through agent
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    state = {"messages": [HumanMessage(content=file_message)]}
    
    for event in st.session_state.graph.stream(state, config, stream_mode="values"):
        if "messages" in event and event["messages"]:
            last_msg = event["messages"][-1]
            if isinstance(last_msg, AIMessage):
                st.session_state.messages.append({"role": "assistant", "content": last_msg.content})
    
    st.rerun()

# Handle voice input
if audio_bytes and audio_bytes != st.session_state.audio_processed:
    st.session_state.audio_processed = audio_bytes
    
    with st.spinner("🎤 Transcribing your voice..."):
        try:
            transcribed_text = transcribe_audio(audio_bytes)
            
            if transcribed_text:
                # Add user message
                st.session_state.messages.append({"role": "human", "content": transcribed_text})
                
                # Process through agent
                config = {"configurable": {"thread_id": st.session_state.thread_id}}
                state = {"messages": [HumanMessage(content=transcribed_text)]}
                
                for event in st.session_state.graph.stream(state, config, stream_mode="values"):
                    if "messages" in event and event["messages"]:
                        last_msg = event["messages"][-1]
                        if isinstance(last_msg, AIMessage):
                            st.session_state.messages.append({"role": "assistant", "content": last_msg.content})
                
                st.rerun()
            else:
                st.warning("Could not transcribe audio. Please try again.")
        except Exception as e:
            st.error(f"Error transcribing audio: {str(e)}")

# Display chat history (Task 5.3)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input (Task 5.3)
if prompt := st.chat_input("Type your message..."):
    # Add user message
    st.session_state.messages.append({"role": "human", "content": prompt})
    
    with st.chat_message("human"):
        st.markdown(prompt)
    
    # Process through agent
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    state = {"messages": [HumanMessage(content=prompt)]}
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            for event in st.session_state.graph.stream(state, config, stream_mode="values"):
                if "messages" in event and event["messages"]:
                    last_msg = event["messages"][-1]
                    if isinstance(last_msg, AIMessage):
                        full_response = last_msg.content
                        message_placeholder.markdown(full_response)
            
            if full_response:
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            else:
                error_msg = "I encountered an issue processing that. Could you try rephrasing?"
                message_placeholder.markdown(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                # Debug: Log the state
                import traceback
                st.error(f"Debug: No response generated. Last state: {st.session_state.graph.get_state(config).values}")
        
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            error_msg = f"I encountered an error: {str(e)}\n\n```\n{error_details}\n```"
            message_placeholder.markdown(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": f"Error: {str(e)}"})

# Requirements preview (Task 5.5 - optional enhancement)
try:
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    state = st.session_state.graph.get_state(config)
    requirements = state.values.get("requirements", [])
    
    if requirements:
        with st.expander(f"📋 Current Requirements ({len(requirements)})", expanded=False):
            for req in requirements:
                st.markdown(f"**{req['id']}** ({req['category']}): {req['description']}")
                if req['tags']:
                    st.caption(f"Tags: {', '.join(req['tags'])}")
                st.caption(f"Source: {req['source']}")
                st.divider()
except:
    pass
