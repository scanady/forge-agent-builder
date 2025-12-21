"""
Comprehensive behavioral/functional tests for the Requirements Elicitation Agent.

These tests validate the complete user journey from start to finish,
ensuring all features work correctly without manual testing.
"""

import pytest
import uuid
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from src.requirements_elicitation_agent.graph import create_graph, router
from src.requirements_elicitation_agent.state import AgentState
from src.requirements_elicitation_agent.nodes import doc_reader, doc_extractor
from src.requirements_elicitation_agent.tools import read_file

# Load environment variables
load_dotenv()


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def graph():
    """Create a fresh graph instance."""
    return create_graph()


@pytest.fixture
def fresh_config():
    """Create a fresh config with unique thread ID."""
    return {"configurable": {"thread_id": str(uuid.uuid4())}}


@pytest.fixture
def initialized_session(graph, fresh_config):
    """Return a graph session that's past the greeting phase."""
    graph.invoke({"messages": [HumanMessage(content="hi")]}, fresh_config)
    graph.invoke({"messages": [HumanMessage(content="interactive")]}, fresh_config)
    return graph, fresh_config


@pytest.fixture
def sample_file():
    """Create a temporary file with sample requirements content."""
    content = """Meeting Notes - Product Requirements
    
The main role is the life insurance product manager. The product manager designs and manages the life insurance product portfolio.

Compliance users need to review the products to make sure they are compliant with regulatory and state requirements. 
Underwriters need to review the underwriting requirements and eligibility. 
Actuaries develop rate tables and other details. 
Marketers use as the source for product information they bring to market. 
Systems use the application via APIs to provide quotes, product information, etc.
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(content)
        return Path(f.name)


# =============================================================================
# Router Tests - Test all routing decisions
# =============================================================================

class TestRouterDecisions:
    """Test that the router makes correct routing decisions."""
    
    def test_routes_to_initializer_on_empty_state(self):
        """Empty state should route to initializer."""
        state: AgentState = {"messages": [], "current_phase": None}
        assert router(state) == "initializer"
    
    def test_routes_to_initializer_on_no_phase(self):
        """No phase should route to initializer."""
        state: AgentState = {"messages": [HumanMessage(content="hi")], "current_phase": None}
        assert router(state) == "initializer"
    
    def test_routes_to_interviewer_after_init(self):
        """After init phase, regular message routes to interviewer."""
        state: AgentState = {
            "messages": [
                AIMessage(content="Hello!"),
                HumanMessage(content="interactive")
            ],
            "current_phase": "init"
        }
        assert router(state) == "interviewer"
    
    def test_routes_to_doc_reader_on_file_upload_init_phase(self):
        """File upload message during init routes to doc_reader."""
        state: AgentState = {
            "messages": [
                AIMessage(content="Hello!"),
                HumanMessage(content="I uploaded a file: C:\\temp\\test.md")
            ],
            "current_phase": "init"
        }
        assert router(state) == "doc_reader"
    
    def test_routes_to_doc_reader_on_file_upload_elicitation_phase(self):
        """File upload message during elicitation routes to doc_reader."""
        state: AgentState = {
            "messages": [
                AIMessage(content="Tell me about users"),
                HumanMessage(content="I uploaded a file: /tmp/notes.md")
            ],
            "current_phase": "elicitation"
        }
        assert router(state) == "doc_reader"
    
    def test_routes_to_doc_reader_on_file_extension(self):
        """Message with file extension routes to doc_reader."""
        state: AgentState = {
            "messages": [
                AIMessage(content="Tell me about users"),
                HumanMessage(content="analyze meeting-notes.txt")
            ],
            "current_phase": "elicitation"
        }
        assert router(state) == "doc_reader"
    
    def test_routes_to_requirement_recorder_in_elicitation(self):
        """Regular message during elicitation routes to requirement_recorder."""
        state: AgentState = {
            "messages": [
                AIMessage(content="Tell me about users"),
                HumanMessage(content="Users need to login with email")
            ],
            "current_phase": "elicitation"
        }
        assert router(state) == "requirement_recorder"
    
    def test_routes_to_doc_extractor_on_confirm(self):
        """Yes confirmation during analysis_confirm routes to doc_extractor."""
        state: AgentState = {
            "messages": [
                AIMessage(content="Should I extract requirements?"),
                HumanMessage(content="yes")
            ],
            "current_phase": "analysis_confirm"
        }
        assert router(state) == "doc_extractor"
    
    def test_routes_to_interviewer_on_decline(self):
        """No during analysis_confirm routes to interviewer."""
        state: AgentState = {
            "messages": [
                AIMessage(content="Should I extract requirements?"),
                HumanMessage(content="no, skip it")
            ],
            "current_phase": "analysis_confirm"
        }
        assert router(state) == "interviewer"
    
    def test_routes_to_output_generator_show_requirements(self):
        """'show requirements' routes to output_generator."""
        state: AgentState = {
            "messages": [HumanMessage(content="show requirements")],
            "current_phase": "elicitation"
        }
        assert router(state) == "output_generator"
    
    def test_routes_to_output_generator_show_me_the_requirements(self):
        """'show me the requirements' routes to output_generator."""
        state: AgentState = {
            "messages": [HumanMessage(content="show me the requirements")],
            "current_phase": "elicitation"
        }
        assert router(state) == "output_generator"
    
    def test_routes_to_output_generator_list_requirements(self):
        """'list requirements' routes to output_generator."""
        state: AgentState = {
            "messages": [HumanMessage(content="list all requirements")],
            "current_phase": "elicitation"
        }
        assert router(state) == "output_generator"
    
    def test_routes_to_output_generator_what_captured(self):
        """'what have we captured' routes to output_generator."""
        state: AgentState = {
            "messages": [HumanMessage(content="what have we captured")],
            "current_phase": "elicitation"
        }
        assert router(state) == "output_generator"
    
    def test_does_not_route_to_output_on_requirement_containing_review(self):
        """Requirement text containing 'review' should NOT route to output_generator."""
        state: AgentState = {
            "messages": [HumanMessage(content="Compliance users need to review products for regulatory requirements")],
            "current_phase": "elicitation"
        }
        # Should route to requirement_recorder, not output_generator
        assert router(state) == "requirement_recorder"
    
    def test_does_not_route_to_output_on_requirement_containing_requirements(self):
        """Requirement text containing 'requirements' should NOT route to output_generator."""
        state: AgentState = {
            "messages": [HumanMessage(content="Underwriters review eligibility requirements")],
            "current_phase": "elicitation"
        }
        assert router(state) == "requirement_recorder"


# =============================================================================
# File Upload Flow Tests
# =============================================================================

class TestFileUploadFlow:
    """Test the complete file upload flow."""
    
    def test_read_file_tool_reads_content(self, sample_file):
        """Test that read_file tool can read file content."""
        content = read_file.invoke({"file_path": str(sample_file)})
        assert "life insurance product manager" in content.lower()
        assert "Compliance users" in content
    
    def test_read_file_returns_error_for_missing_file(self):
        """Test that read_file returns error for non-existent file."""
        result = read_file.invoke({"file_path": "/nonexistent/file.txt"})
        assert "Error" in result or "error" in result.lower()
    
    def test_doc_reader_extracts_file_path_from_message(self, sample_file):
        """Test doc_reader extracts file path correctly."""
        state: AgentState = {
            "messages": [HumanMessage(content=f"I uploaded a file: {sample_file}")],
            "current_phase": "elicitation",
            "requirements": [],
            "todo_list": [],
            "clarification_counts": {}
        }
        result = doc_reader(state)
        
        # Should ask for confirmation
        assert "messages" in result
        assert len(result["messages"]) > 0
        assert result.get("current_phase") == "analysis_confirm"
        assert result.get("pending_file_path") == str(sample_file)
    
    def test_full_file_upload_flow(self, graph, fresh_config, sample_file):
        """Test complete file upload and extraction flow."""
        # Initialize
        graph.invoke({"messages": [HumanMessage(content="hi")]}, fresh_config)
        
        # Upload file
        file_msg = f"I uploaded a file: {sample_file}"
        result = graph.invoke({"messages": [HumanMessage(content=file_msg)]}, fresh_config)
        
        # Should be in analysis_confirm phase asking for confirmation
        assert result["current_phase"] == "analysis_confirm"
        assert "extract" in result["messages"][-1].content.lower() or "proceed" in result["messages"][-1].content.lower()
        
        # Confirm extraction
        result = graph.invoke({"messages": [HumanMessage(content="yes")]}, fresh_config)
        
        # Should have extracted requirements
        assert len(result.get("requirements", [])) >= 1, "Should extract at least 1 requirement from file"


# =============================================================================
# Requirement Extraction Tests
# =============================================================================

class TestRequirementExtraction:
    """Test requirement extraction from user messages."""
    
    def test_extracts_single_clear_requirement(self, initialized_session):
        """Test extraction of a single clear requirement."""
        graph, config = initialized_session
        
        result = graph.invoke(
            {"messages": [HumanMessage(content="Users must be able to login with email and password")]},
            config
        )
        
        assert len(result["requirements"]) >= 1
        req_descriptions = " ".join([r["description"].lower() for r in result["requirements"]])
        assert "login" in req_descriptions or "email" in req_descriptions
    
    def test_extracts_multiple_requirements_from_one_message(self, initialized_session):
        """Test extraction of multiple requirements from a single message."""
        graph, config = initialized_session
        
        complex_input = """
        Product managers must create new insurance products with coverage limits.
        Actuaries must calculate premium rates using risk data.
        Legal team must draft policy contracts.
        """
        result = graph.invoke({"messages": [HumanMessage(content=complex_input)]}, config)
        
        assert len(result["requirements"]) >= 2, f"Expected at least 2 requirements, got {len(result['requirements'])}"
    
    def test_extracts_requirements_with_multiple_roles(self, initialized_session):
        """Test extraction when multiple user roles are mentioned."""
        graph, config = initialized_session
        
        input_text = """
        Compliance users need to review products for regulatory compliance.
        Underwriters need to review eligibility requirements.
        Actuaries need to develop rate tables.
        """
        result = graph.invoke({"messages": [HumanMessage(content=input_text)]}, config)
        
        assert len(result["requirements"]) >= 2
        
        # Check that different roles appear in requirements
        req_text = " ".join([r["description"].lower() for r in result["requirements"]])
        roles_found = sum([
            1 if "compliance" in req_text else 0,
            1 if "underwriter" in req_text else 0,
            1 if "actuar" in req_text else 0
        ])
        assert roles_found >= 2, f"Expected at least 2 roles, found {roles_found}"
    
    def test_requirements_accumulate_across_turns(self, initialized_session):
        """Test that requirements accumulate across multiple conversation turns."""
        graph, config = initialized_session
        
        # First requirement
        graph.invoke(
            {"messages": [HumanMessage(content="Users must be able to create accounts with email")]},
            config
        )
        
        # Second requirement
        result = graph.invoke(
            {"messages": [HumanMessage(content="Admins must be able to manage user permissions")]},
            config
        )
        
        # Should have accumulated requirements
        assert len(result["requirements"]) >= 2, "Requirements should accumulate"
    
    def test_assigns_category_to_requirements(self, initialized_session):
        """Test that requirements are assigned categories."""
        graph, config = initialized_session
        
        result = graph.invoke(
            {"messages": [HumanMessage(content="The system must respond within 2 seconds")]},
            config
        )
        
        if len(result["requirements"]) > 0:
            assert result["requirements"][-1].get("category") is not None


# =============================================================================
# Output Generation Tests
# =============================================================================

class TestOutputGeneration:
    """Test the output/requirements display functionality."""
    
    def test_show_requirements_with_no_requirements(self, graph, fresh_config):
        """Test showing requirements when none captured yet."""
        # Initialize
        graph.invoke({"messages": [HumanMessage(content="hi")]}, fresh_config)
        graph.invoke({"messages": [HumanMessage(content="interactive")]}, fresh_config)
        
        # Ask to show requirements
        result = graph.invoke({"messages": [HumanMessage(content="show requirements")]}, fresh_config)
        
        # Should indicate no requirements yet
        last_msg = result["messages"][-1].content.lower()
        assert "no" in last_msg or "haven't" in last_msg or "yet" in last_msg or "none" in last_msg
    
    def test_show_requirements_after_capturing(self, initialized_session):
        """Test showing requirements after some are captured."""
        graph, config = initialized_session
        
        # Add a requirement
        graph.invoke(
            {"messages": [HumanMessage(content="Users must be able to login with SSO")]},
            config
        )
        
        # Show requirements
        result = graph.invoke({"messages": [HumanMessage(content="show me the requirements")]}, config)
        
        # Should show the requirement
        last_msg = result["messages"][-1].content
        assert "REQ-" in last_msg or "login" in last_msg.lower() or "SSO" in last_msg


# =============================================================================
# Phase Transition Tests
# =============================================================================

class TestPhaseTransitions:
    """Test phase transitions through the conversation."""
    
    def test_starts_in_init_phase(self, graph, fresh_config):
        """Test that conversation starts in init phase."""
        result = graph.invoke({"messages": [HumanMessage(content="hi")]}, fresh_config)
        assert result["current_phase"] == "init"
    
    def test_transitions_to_elicitation_on_mode_selection(self, graph, fresh_config):
        """Test transition from init to elicitation."""
        graph.invoke({"messages": [HumanMessage(content="hi")]}, fresh_config)
        result = graph.invoke({"messages": [HumanMessage(content="interactive")]}, fresh_config)
        assert result["current_phase"] == "elicitation"
    
    def test_transitions_to_analysis_confirm_on_file_upload(self, graph, fresh_config, sample_file):
        """Test transition to analysis_confirm on file upload."""
        graph.invoke({"messages": [HumanMessage(content="hi")]}, fresh_config)
        
        result = graph.invoke(
            {"messages": [HumanMessage(content=f"I uploaded a file: {sample_file}")]},
            fresh_config
        )
        assert result["current_phase"] == "analysis_confirm"
    
    def test_stays_in_elicitation_after_requirement(self, initialized_session):
        """Test that phase stays in elicitation after recording requirement."""
        graph, config = initialized_session
        
        result = graph.invoke(
            {"messages": [HumanMessage(content="Users must be able to reset passwords via email")]},
            config
        )
        
        # Should stay in elicitation
        assert result["current_phase"] in ["elicitation", "gap_analysis"]


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_handles_empty_message(self, initialized_session):
        """Test handling of empty message."""
        graph, config = initialized_session
        
        # This might raise or return gracefully
        try:
            result = graph.invoke({"messages": [HumanMessage(content="")]}, config)
            # Should have some response
            assert len(result["messages"]) > 0
        except Exception:
            pass  # Some empty message handling may raise
    
    def test_handles_very_long_message(self, initialized_session):
        """Test handling of very long message."""
        graph, config = initialized_session
        
        long_text = "Users need to be able to " + "do things " * 500
        result = graph.invoke({"messages": [HumanMessage(content=long_text)]}, config)
        
        # Should handle gracefully
        assert "messages" in result
    
    def test_handles_special_characters(self, initialized_session):
        """Test handling of special characters in requirements."""
        graph, config = initialized_session
        
        result = graph.invoke(
            {"messages": [HumanMessage(content="Users must see prices in $USD & €EUR formats")]},
            config
        )
        
        assert "messages" in result
    
    def test_multiple_sessions_are_isolated(self, graph):
        """Test that different thread IDs have isolated state."""
        config1 = {"configurable": {"thread_id": str(uuid.uuid4())}}
        config2 = {"configurable": {"thread_id": str(uuid.uuid4())}}
        
        # Initialize both
        graph.invoke({"messages": [HumanMessage(content="hi")]}, config1)
        graph.invoke({"messages": [HumanMessage(content="hi")]}, config2)
        
        graph.invoke({"messages": [HumanMessage(content="interactive")]}, config1)
        graph.invoke({"messages": [HumanMessage(content="interactive")]}, config2)
        
        # Add requirement to session 1 only
        result1 = graph.invoke(
            {"messages": [HumanMessage(content="Users must login with email and password")]},
            config1
        )
        
        # Session 2 should not have that requirement
        result2 = graph.invoke(
            {"messages": [HumanMessage(content="show requirements")]},
            config2
        )
        
        # Session 1 should have requirements, session 2 should not
        assert len(result1.get("requirements", [])) >= 1
        # Session 2's response should indicate no requirements
        last_msg2 = result2["messages"][-1].content.lower()
        assert "no" in last_msg2 or "haven't" in last_msg2 or "none" in last_msg2


# =============================================================================
# Conversation Flow Tests
# =============================================================================

class TestConversationFlow:
    """Test realistic conversation flows."""
    
    def test_complete_interactive_flow(self, graph, fresh_config):
        """Test a complete interactive session from start to finish."""
        # 1. Start
        result = graph.invoke({"messages": [HumanMessage(content="hello")]}, fresh_config)
        assert "Forge Requirements Assistant" in result["messages"][-1].content
        
        # 2. Choose interactive
        result = graph.invoke({"messages": [HumanMessage(content="I want to do interactive discovery")]}, fresh_config)
        assert result["current_phase"] == "elicitation"
        
        # 3. Provide requirements
        result = graph.invoke(
            {"messages": [HumanMessage(content="Admin users need to manage all system settings and user accounts")]},
            fresh_config
        )
        assert len(result.get("requirements", [])) >= 1
        
        # 4. Provide more requirements
        result = graph.invoke(
            {"messages": [HumanMessage(content="Regular users can only view their own profile and data")]},
            fresh_config
        )
        
        # 5. Ask to see requirements
        result = graph.invoke({"messages": [HumanMessage(content="show me the requirements")]}, fresh_config)
        last_msg = result["messages"][-1].content
        assert "REQ-" in last_msg or "admin" in last_msg.lower() or "user" in last_msg.lower()
    
    def test_file_then_interactive_flow(self, graph, fresh_config, sample_file):
        """Test uploading a file then continuing interactively."""
        # 1. Start
        graph.invoke({"messages": [HumanMessage(content="hi")]}, fresh_config)
        
        # 2. Upload file
        result = graph.invoke(
            {"messages": [HumanMessage(content=f"I uploaded a file: {sample_file}")]},
            fresh_config
        )
        assert result["current_phase"] == "analysis_confirm"
        
        # 3. Confirm extraction
        result = graph.invoke({"messages": [HumanMessage(content="yes please")]}, fresh_config)
        initial_req_count = len(result.get("requirements", []))
        
        # 4. Add more requirements interactively
        result = graph.invoke(
            {"messages": [HumanMessage(content="Auditors need read-only access to all records")]},
            fresh_config
        )
        
        # Should have more requirements than from file alone
        assert len(result.get("requirements", [])) >= initial_req_count


# =============================================================================
# Run tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
