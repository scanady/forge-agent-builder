import streamlit as st
import os
import json
import uuid
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables immediately
load_dotenv()

from forge_requirements_builder.state import create_project_state, ForgeRequirementsState, serialize_state, deserialize_state
from forge_requirements_builder.graph import create_graph
from forge_requirements_builder.utils import ProjectLogger

# Page Configuration
st.set_page_config(
    page_title="Forge Requirements Assistant",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
PROJECTS_DIR = Path("projects")
PROJECTS_DIR.mkdir(exist_ok=True)

def list_projects():
    """List all available projects."""
    projects = []
    if PROJECTS_DIR.exists():
        for item in PROJECTS_DIR.iterdir():
            if item.is_dir():
                # Check if state.json exists to confirm it's a valid project
                if (item / "state.json").exists():
                    projects.append(item.name)
    return sorted(projects)

def load_project_state(project_id: str) -> dict:
    """Load project state from JSON."""
    state_path = PROJECTS_DIR / project_id / "state.json"
    if state_path.exists():
        with open(state_path, "r") as f:
            data = json.load(f)
            state = deserialize_state(data)
            
            # Sanity check for corrupted state (strings instead of objects)
            # This handles legacy state files saved before serialization fix
            if state.get("requirements_raw") and isinstance(state["requirements_raw"][0], str):
                st.warning("Detected corrupted requirements data (legacy format). Resetting requirements list.")
                state["requirements_raw"] = []
                
            if state.get("user_stories") and isinstance(state["user_stories"][0], str):
                state["user_stories"] = []
                
            return state
    return None

def save_project_state(project_id: str, state: dict):
    """Save project state to JSON."""
    # Update last_updated timestamp before saving
    state["last_updated"] = datetime.now()
    project_path = PROJECTS_DIR / project_id
    project_path.mkdir(exist_ok=True)
    with open(project_path / "state.json", "w") as f:
        json.dump(serialize_state(state), f, indent=2, default=str)

def create_new_project(name: str, context: str) -> str:
    """Create a new project and return its ID."""
    project_id = str(uuid.uuid4())[:8]  # Short ID for readability
    # Sanitize name for folder usage if we wanted to use name in path, but ID is safer
    # We'll store name in the state
    
    initial_state = create_project_state(name, context)
    initial_state["project_id"] = project_id
    
    save_project_state(project_id, initial_state)
    return project_id

# Sidebar - Project Management
with st.sidebar:
    st.title("Projects")
    
    # Project Selection
    existing_projects = list_projects()
    
    # Add "New Project" option
    options = ["Create New Project"] + existing_projects
    
    selected_option = st.selectbox("Select Project", options)
    
    if selected_option == "Create New Project":
        st.subheader("New Project")
        new_project_name = st.text_input("Project Name")
        new_project_context = st.text_area("Project Context/Description")
        
        if st.button("Create Project"):
            if new_project_name:
                new_id = create_new_project(new_project_name, new_project_context)
                st.success(f"Project '{new_project_name}' created!")
                st.rerun()  # Rerun to update list and select the new project
            else:
                st.error("Please enter a project name.")
    else:
        # Load selected project
        project_id = selected_option
        # Always load fresh state from disk to ensure sidebar reflects latest updates
        state = load_project_state(project_id)
        
        if state:
            st.session_state["current_project_id"] = project_id
            st.session_state["project_state"] = state
            
            st.divider()
            st.info(f"**Project:** {state.get('project_name')}")
            st.caption(f"ID: {project_id}")
            st.caption(f"Phase: {state.get('workflow_phase')}")
            
            # Progress Indicators - These are now dynamic and reflect the current state
            st.divider()
            st.subheader("Progress")
            req_count = len(state.get("requirements_raw", []))
            story_count = len(state.get("user_stories", []))
            issue_count = len(state.get("quality_issues", []))
            prioritized_count = len(state.get("prioritized_backlog", []))
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Reqs", req_count)
            with col2:
                st.metric("Stories", story_count)
            col3, col4 = st.columns(2)
            with col3:
                st.metric("Quality Issues", issue_count)
            with col4:
                st.metric("Prioritized", prioritized_count)
            
            # Status display
            if state.get("discovery_complete"):
                st.caption("✅ Discovery Complete")
            if state.get("authoring_complete"):
                st.caption("✅ Authoring Complete")
            if state.get("quality_complete"):
                st.caption("✅ Quality Review Complete")
            if state.get("prioritization_complete"):
                st.caption("✅ Prioritization Complete")
            
            # Debug info
            with st.expander("Debug Info"):
                last_update = state.get('last_updated')
                if last_update:
                    if isinstance(last_update, str):
                        st.write(f"Last Update: {last_update}")
                    else:
                        st.write(f"Last Update: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    st.write("Last Update: N/A")
                st.write(f"Total Messages: {len(state.get('conversation_history', []))}")
                st.write(f"Actual Reqs in State: {len(state.get('requirements_raw', []))}")
            # File Upload
            st.divider()
            st.subheader("Upload Document")
            uploaded_file = st.file_uploader("Upload requirements doc", type=["txt", "md", "pdf", "docx"])
            if uploaded_file:
                # Save file temporarily
                temp_dir = Path("temp_uploads")
                temp_dir.mkdir(exist_ok=True)
                file_path = temp_dir / uploaded_file.name
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                st.success(f"Uploaded {uploaded_file.name}")
                
                if st.button("Process File"):
                    # Add file path to user message to trigger doc_reader (if implemented) or just extract
                    # For now, we'll send a message saying "I uploaded a file..."
                    # The graph should handle it.
                    # Or we can call the tool directly?
                    # The plan says "Route to doc_reader: user message contains file path"
                    
                    user_msg_content = f"I have uploaded a file: {file_path.absolute()}"
                    
                    # Add to state and run
                    current_state = st.session_state["project_state"]
                    new_msg = {"role": "user", "content": user_msg_content, "timestamp": datetime.now().isoformat()}
                    current_state["conversation_history"].append(new_msg)
                    
                    with st.spinner("Analyzing document..."):
                        # Initialize graph
                        graph = create_graph()
                        final_state = graph.invoke(current_state, config={"configurable": {"thread_id": project_id}})
                        
                        st.session_state["project_state"] = final_state
                        save_project_state(project_id, final_state)
                        st.rerun()

            # Phase Controls (Task 6.1.5)
            st.divider()
            st.subheader("Phase Controls")
            col_p1, col_p2 = st.columns(2)
            if col_p1.button("Skip to Authoring"):
                current_state = st.session_state["project_state"]
                new_msg = {"role": "user", "content": "skip to authoring", "timestamp": datetime.now().isoformat()}
                current_state["conversation_history"].append(new_msg)
                graph = create_graph()
                final_state = graph.invoke(current_state, config={"configurable": {"thread_id": project_id}})
                st.session_state["project_state"] = final_state
                save_project_state(project_id, final_state)
                st.rerun()
                
            if col_p2.button("Skip to Quality"):
                current_state = st.session_state["project_state"]
                new_msg = {"role": "user", "content": "skip to quality", "timestamp": datetime.now().isoformat()}
                current_state["conversation_history"].append(new_msg)
                graph = create_graph()
                final_state = graph.invoke(current_state, config={"configurable": {"thread_id": project_id}})
                st.session_state["project_state"] = final_state
                save_project_state(project_id, final_state)
                st.rerun()

            if st.button("Clear Chat History"):
                # Reset messages but keep project data
                state["messages"] = [] # Wait, state uses "conversation_history"
                state["conversation_history"] = []
                save_project_state(project_id, state)
                st.session_state["project_state"] = state
                st.rerun()

# Main Content
st.title("Forge Requirements Assistant")

if "current_project_id" in st.session_state:
    # Always reload the latest project state from disk to ensure consistency
    project_id = st.session_state["current_project_id"]
    project_state = load_project_state(project_id)
    
    if project_state:
        st.session_state["project_state"] = project_state
        
        st.write(f"Working on: **{project_state.get('project_name')}**")
        
        # Phase and Progress Info
        phase_emoji = {
            "discovery": "🔍",
            "authoring": "✍️",
            "quality": "🔎",
            "prioritization": "📊",
            "synthesis": "📝",
            "complete": "✅"
        }
        current_phase = project_state.get('workflow_phase', 'unknown')
        st.info(f"{phase_emoji.get(current_phase, '⚙️')} Current Phase: **{current_phase.title()}**")
        
        # Final Deliverable Download (Task 6.1.6)
        if project_state.get("final_deliverable"):
            st.success("🎉 Requirements Document Ready!")
            st.download_button(
                label="Download Requirements (Markdown)",
                data=project_state["final_deliverable"],
                file_name=f"{project_state.get('project_name', 'requirements')}.md",
                mime="text/markdown"
            )
        
        # Display Chat History
        for msg in project_state.get("conversation_history", []):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
        # Chat Input
        if prompt := st.chat_input("Type your requirement or instruction..."):
            # Add user message
            with st.chat_message("user"):
                st.markdown(prompt)
                
            current_state = project_state
            new_msg = {"role": "user", "content": prompt, "timestamp": datetime.now().isoformat()}
            current_state["conversation_history"].append(new_msg)
            
            # Run Graph
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        graph = create_graph()
                        final_state = graph.invoke(current_state, config={"configurable": {"thread_id": project_id}})
                        
                        # Debug: Check if state was updated
                        req_count_before = len(project_state.get("requirements_raw", []))
                        req_count_after = len(final_state.get("requirements_raw", []))
                        logger = ProjectLogger(project_id)
                        logger.info(f"State Update Check - Reqs Before: {req_count_before}, After: {req_count_after}")
                        
                        # Get the last message from assistant
                        if final_state.get("conversation_history"):
                            last_msg = final_state["conversation_history"][-1]
                            if last_msg["role"] == "assistant":
                                st.markdown(last_msg["content"])
                        else:
                            st.warning("No assistant response generated")
                        
                        # Update state
                        st.session_state["project_state"] = final_state
                        save_project_state(project_id, final_state)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error processing request: {str(e)}")
                        logger = ProjectLogger(project_id)
                        logger.error(f"Error: {str(e)}")
                        import traceback
                        logger.error(traceback.format_exc())
    
else:
    st.info("👈 Please select or create a project from the sidebar to get started.")

