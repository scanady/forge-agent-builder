"""
Streamlit frontend for Riley - Requirements Analyst.

Implements the UI specification from plan.md Section 7.3.
Phase 5 tasks: 5.1-5.5
"""

import streamlit as st
import uuid
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage

# Load environment variables from .env file
load_dotenv()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.requirements_elicitation_agent.graph import create_graph


# Page configuration (Task 5.1)
st.set_page_config(
    page_title="Riley - Requirements Analyst",
    page_icon="📋",
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
if "initialized" not in st.session_state:
    st.session_state.initialized = False

# Show initial greeting automatically when the app first loads
if not st.session_state.initialized and len(st.session_state.messages) == 0:
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    state = {"messages": [HumanMessage(content="__init__")]}
    
    try:
        for event in st.session_state.graph.stream(state, config, stream_mode="values"):
            if "messages" in event and event["messages"]:
                last_msg = event["messages"][-1]
                if isinstance(last_msg, AIMessage):
                    st.session_state.messages.append({"role": "assistant", "content": last_msg.content})
        st.session_state.initialized = True
    except:
        pass

# Title and description
st.title("📋 Riley - Requirements Analyst")
st.markdown("""
*Your expert partner in discovering and documenting software requirements*

I help you bridge the gap between business concepts and executable software requirements
through collaborative interviews and structured analysis.
""")

# Custom CSS for sidebar panels
st.markdown("""
<style>
    [data-testid="stSidebar"] .stButton > button {
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        background-color: #f8f9fa;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: #e9ecef;
        border-color: #dee2e6;
    }
    .sidebar-panel {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        border: 1px solid #e9ecef;
    }
    .panel-header {
        font-size: 1.1em;
        font-weight: 600;
        color: #374151;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar (Task 5.2)
with st.sidebar:
    # Start over button at the top
    if st.button("🔄 Start Over", use_container_width=True):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.processed_files = set()
        st.session_state.initialized = False
        st.rerun()
    
    st.markdown("")  # Spacer
    
    # Requirements counter panel
    try:
        config = {"configurable": {"thread_id": st.session_state.thread_id}}
        state = st.session_state.graph.get_state(config)
        req_count = len(state.values.get("requirements", []))
    except:
        req_count = 0
    
    st.markdown(f"""
<div class="sidebar-panel">
    <div class="panel-header">📊 Requirements Captured</div>
    <div style="font-size: 2.5em; font-weight: bold; color: #1f77b4; text-align: center;">{req_count}</div>
</div>
    """, unsafe_allow_html=True)    
    
    # Help section panel
    st.markdown("""
<div class="sidebar-panel">
    <div class="panel-header">💡 How to Use</div>
    <div style="font-size: 0.9em; color: #4b5563;">
    <b>Getting Started:</b><br>
    1. Tell me about your project<br>
    2. Upload a document to extract requirements<br>
    3. Ask me to "show requirements" to review or export the requirements.<br><br>
    <b>Tips:</b><br>Be specific • Ask for clarifications • Upload information anytime
    </div>
</div>
    """, unsafe_allow_html=True)
       
    # File uploader panel - using container for proper grouping
    with st.container():
        st.markdown('<div class="panel-header">📄 Upload Document</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Upload Document",
            type=["txt", "md"],
            help="Upload meeting notes, specs, or other requirement documents",
            label_visibility="collapsed"
    )

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
                st.rerun()  # Refresh to update sidebar metrics
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
