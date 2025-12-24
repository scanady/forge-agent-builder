"""Node Implementations for Forge Requirements Builder

Contains the logic for all 6 nodes in the LangGraph workflow:
1. Orchestrator Node
2. Discovery Agent Node
3. Authoring Agent Node
4. Quality Agent Node
5. Prioritization Agent Node
6. Synthesis Node
"""

import json
import logging
import os
import tempfile
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser

from .state import (
    ForgeRequirementsState, 
    RequirementRaw, 
    UserStory, 
    QualityIssue, 
    PrioritizedRequirement,
    AcknowledgedRisk
)
from .utils import (
    detect_content_type, 
    ConversationHistoryManager, 
    ProjectLogger,
    extract_requirements_count
)
from .tools import (
    extract_from_document, 
    validate_requirement_capture,
    validate_user_story, 
    format_user_story_template,
    validate_requirements_quality,
    apply_prioritization_framework,
    validate_acceptance_criteria
)
from .prompts import (
    ORCHESTRATOR_SYSTEM_PROMPT,
    DISCOVERY_SYSTEM_PROMPT,
    AUTHORING_SYSTEM_PROMPT,
    QUALITY_SYSTEM_PROMPT,
    PRIORITIZATION_SYSTEM_PROMPT,
    SYNTHESIS_SYSTEM_PROMPT
)

# Initialize Logger
logger = logging.getLogger("forge_requirements_builder")

# Initialize LLM
# Note: In a real app, model name and temp would come from config
llm = ChatOpenAI(model="gpt-4o", temperature=0)


# ============================================================================
# 1. Orchestrator Node
# ============================================================================

def orchestrator_node(state: ForgeRequirementsState) -> ForgeRequirementsState:
    """
    Supervisor agent that routes tasks and manages workflow state.
    
    Responsibilities:
    - Analyze user intent
    - Detect content type for smart routing
    - Manage phase transitions
    - Handle interruptions
    """
    project_id = state["project_id"]
    logger.info(f"[{project_id}] Orchestrator active. Phase: {state['workflow_phase']}")
    
    # Get recent conversation history
    messages = state["conversation_history"]
    last_message = messages[-1] if messages else None
    
    # 1. Handle User Interruptions / Explicit Commands
    if last_message and last_message["role"] == "user":
        user_text = last_message["content"].lower()
        
        # Check for file upload
        if "i have uploaded a file:" in user_text:
            try:
                # Extract path
                file_path = last_message["content"].split("I have uploaded a file:")[1].strip()
                
                # Call extraction tool
                result = extract_from_document(file_path)
                
                if result.requirements:
                    # Add to state
                    current_count = len(state["requirements_raw"])
                    new_reqs = []
                    
                    # Create a set of existing signatures (title + description) to prevent duplicates
                    existing_signatures = {
                        (r.title.strip().lower(), r.description.strip().lower()) 
                        for r in state["requirements_raw"]
                    }
                    
                    added_count = 0
                    skipped_count = 0

                    for i, extracted in enumerate(result.requirements):
                        # Check for duplicates
                        signature = (extracted.title.strip().lower(), extracted.description.strip().lower())
                        if signature in existing_signatures:
                            skipped_count += 1
                            continue

                        req_id = f"REQ-{current_count + added_count + 1:03d}"
                        new_reqs.append(RequirementRaw(
                            id=req_id,
                            title=extracted.title,
                            description=extracted.description,
                            type=extracted.type,
                            source=f"File: {file_path}"
                        ))
                        existing_signatures.add(signature)
                        added_count += 1

                    state["requirements_raw"].extend(new_reqs)
                    
                    # Add confirmation message
                    msg = f"Successfully processed file. Extracted {len(new_reqs)} new requirements."
                    if skipped_count > 0:
                        msg += f" (Skipped {skipped_count} duplicates)."

                    ConversationHistoryManager.add_message(
                        state["conversation_history"],
                        "assistant",
                        msg,
                        agent="Orchestrator"
                    )
                    
                    # Mark discovery as potentially complete or just continue
                    # For now, let's stay in discovery to allow refinement
                    state["workflow_phase"] = "discovery"
                    state["current_agent"] = "discovery_agent"
                    return state
            except Exception as e:
                logger.error(f"File processing failed: {e}")
                ConversationHistoryManager.add_message(
                    state["conversation_history"],
                    "assistant",
                    f"Error processing file: {str(e)}",
                    agent="Orchestrator"
                )
                return state

        # Check for explicit phase transitions
        if "skip to" in user_text:
            if "authoring" in user_text:
                state["workflow_phase"] = "authoring"
                state["current_agent"] = "authoring_agent"
                return state
            elif "quality" in user_text:
                state["workflow_phase"] = "quality"
                state["current_agent"] = "quality_agent"
                return state
            elif "prioritization" in user_text:
                state["workflow_phase"] = "prioritization"
                state["current_agent"] = "prioritization_agent"
                return state
        
        # Detect user requesting to create/generate stories
        if any(phrase in user_text for phrase in ["create stories", "generate stories", "create the stories", "make stories", "let's see the stories", "write stories"]):
            if state["workflow_phase"] == "discovery" and state["requirements_raw"]:
                state["discovery_complete"] = True
                logger.info(f"[{project_id}] User requested stories - marking discovery complete")
                ConversationHistoryManager.add_message(
                    state["conversation_history"],
                    "assistant",
                    "Understood! Discovery phase is complete. Now I'll generate user stories from the requirements.",
                    agent="Orchestrator"
                )
                # Don't return yet - let the phase transition logic below handle routing
        
        # Detect user acknowledging quality issues and wanting to proceed
        if state["workflow_phase"] == "quality" and state["quality_complete"] and not state["quality_issues_resolved"]:
            if any(phrase in user_text for phrase in ["let's proceed", "proceed", "acknowledge", "move on", "continue", "let's move", "what's next", "next phase", "next step"]):
                state["quality_issues_resolved"] = True
                logger.info(f"[{project_id}] User acknowledged quality issues - marking resolved")
                ConversationHistoryManager.add_message(
                    state["conversation_history"],
                    "assistant",
                    "Understood. Acknowledged the quality issues. Moving forward to prioritization.",
                    agent="Orchestrator"
                )
                # Don't return yet - let the phase transition logic below handle routing
        
        # Detect user wants to continue editing after synthesis
        if state["workflow_phase"] == "synthesis" and state["synthesis_complete"]:
            if any(phrase in user_text for phrase in ["add requirement", "add more", "more requirements", "back to discovery", "refine stories", "back to authoring", "review issues", "back to quality", "adjust priorities", "back to prioritization", "regenerate document", "regenerate", "update document"]):
                ConversationHistoryManager.add_message(
                    state["conversation_history"],
                    "assistant",
                    "Great! Let's continue refining the requirements. Where would you like to go?",
                    agent="Orchestrator"
                )
                
                if any(phrase in user_text for phrase in ["add requirement", "add more", "more requirements", "back to discovery"]):
                    state["workflow_phase"] = "discovery"
                    state["discovery_complete"] = False  # Re-open discovery
                    logger.info(f"[{project_id}] User returning to discovery phase")
                elif any(phrase in user_text for phrase in ["refine stories", "back to authoring"]):
                    state["workflow_phase"] = "authoring"
                    state["authoring_complete"] = False  # Re-open authoring
                    logger.info(f"[{project_id}] User returning to authoring phase")
                elif any(phrase in user_text for phrase in ["review issues", "back to quality"]):
                    state["workflow_phase"] = "quality"
                    state["quality_complete"] = False  # Re-open quality
                    state["quality_issues_resolved"] = False
                    logger.info(f"[{project_id}] User returning to quality phase")
                elif any(phrase in user_text for phrase in ["adjust priorities", "back to prioritization"]):
                    state["workflow_phase"] = "prioritization"
                    state["prioritization_complete"] = False  # Re-open prioritization
                    logger.info(f"[{project_id}] User returning to prioritization phase")
                elif any(phrase in user_text for phrase in ["regenerate document", "regenerate", "update document"]):
                    state["workflow_phase"] = "synthesis"
                    state["synthesis_complete"] = False  # Re-run synthesis
                    logger.info(f"[{project_id}] User regenerating synthesis document")
            
            # User wants to finish/end workflow
            elif any(phrase in user_text for phrase in ["done", "finish", "complete", "that's all", "no more", "end workflow"]):
                state["workflow_phase"] = "complete"
                logger.info(f"[{project_id}] User marking workflow as complete")
                ConversationHistoryManager.add_message(
                    state["conversation_history"],
                    "assistant",
                    "Perfect! Your requirements document is ready. You can download it and use it for development. Thank you for working with the Forge Requirements Assistant!",
                    agent="Orchestrator"
                )

    
    # 2. Smart Phase Detection (if in discovery or initial state)
    if state["workflow_phase"] == "discovery" and last_message and last_message["role"] == "user":
        content_type = detect_content_type(last_message["content"])
        
        if content_type == "user_stories" and not state["user_stories"]:
            # User provided stories, suggest moving to Quality
            # In a real implementation, we'd ask confirmation. For now, we'll note it.
            pass
        elif content_type == "requirements" and not state["requirements_raw"]:
            # User provided requirements, suggest moving to Authoring
            pass

    # 3. Determine Next Step based on State
    # This logic is primarily handled by the conditional edges in the graph,
    # but the orchestrator prepares the state for those edges.
    
    # If we are just starting or returning to orchestrator, decide who acts next
    if state["workflow_phase"] == "discovery":
        if state["discovery_complete"]:
            state["workflow_phase"] = "authoring"
            state["current_agent"] = "authoring_agent"
        else:
            state["current_agent"] = "discovery_agent"
            
    elif state["workflow_phase"] == "authoring":
        if state["authoring_complete"]:
            state["workflow_phase"] = "quality"
            state["current_agent"] = "quality_agent"
        else:
            state["current_agent"] = "authoring_agent"
            
    elif state["workflow_phase"] == "quality":
        if state["quality_issues_resolved"]:
            state["workflow_phase"] = "prioritization"
            state["current_agent"] = "prioritization_agent"
        else:
            state["current_agent"] = "quality_agent"
            
    elif state["workflow_phase"] == "prioritization":
        if state["prioritization_complete"]:
            state["workflow_phase"] = "synthesis"
            state["current_agent"] = "synthesis_node"
        else:
            state["current_agent"] = "prioritization_agent"
    
    elif state["workflow_phase"] == "synthesis":
        # After synthesis, stay in review phase and let user decide next action
        # Don't mark as complete - user controls when to finish
        state["current_agent"] = "orchestrator"
    
    return state


# ============================================================================
# 2. Discovery Agent Node
# ============================================================================

def discovery_node(state: ForgeRequirementsState) -> ForgeRequirementsState:
    """
    Conducts interactive discovery to elicit requirements.
    """
    project_id = state["project_id"]
    logger.info(f"[{project_id}] Discovery Agent active.")
    
    # Prepare context
    req_summary = "\n".join([f"- {r.title}: {r.description}" for r in state["requirements_raw"]])
    
    logger.info(f"Discovery Node: Found {len(state['requirements_raw'])} requirements in state.")
    logger.info(f"Discovery Node: Summary length: {len(req_summary)} chars.")
    
    system_msg = DISCOVERY_SYSTEM_PROMPT.format(
        project_name=state["project_name"],
        requirements_summary=req_summary if req_summary else "None yet."
    )
    
    # Get conversation history
    history = ConversationHistoryManager.get_context(state["conversation_history"], last_n=10)
    lc_messages = [SystemMessage(content=system_msg)]
    
    for msg in history:
        if msg["role"] == "user":
            lc_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            lc_messages.append(AIMessage(content=msg["content"]))
            
    # Call LLM
    # In a full implementation, we would bind tools here (extract_from_document)
    # For this MVP node, we'll simulate the extraction logic via prompt or direct tool usage if triggered
    
    response = llm.invoke(lc_messages)
    
    # Check if we should mark discovery as complete
    if "discovery complete" in response.content.lower() or "move to authoring" in response.content.lower():
        state["discovery_complete"] = True
    
    # Parse the response to extract any new requirements the agent captured
    # Look for phrases like "I've captured this as a new requirement:" or requirement lists
    response_content = response.content
    new_requirements_captured = []
    
    # Try to extract requirements that the LLM is reporting it captured
    # This is a simple heuristic - in production we'd use structured output
    if any(phrase in response_content.lower() for phrase in [
        "captured this as", "captured as a", "new requirement",
        "here are the requirements", "requirements captured so far",
        "summary of the requirements"
    ]):
        # The LLM is reporting requirements - try to extract them from its response
        try:
            # Use the same extraction tool on the LLM's response
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as tmp:
                tmp.write(response_content)
                tmp_path = tmp.name
            
            try:
                extraction_result = extract_from_document(tmp_path, file_type="txt")
                
                if extraction_result.requirements:
                    current_count = len(state["requirements_raw"])
                    
                    # Create a set of existing signatures to prevent duplicates
                    existing_signatures = {
                        (r.title.strip().lower(), r.description.strip().lower()) 
                        for r in state["requirements_raw"]
                    }
                    
                    added_count = 0
                    for extracted in extraction_result.requirements:
                        signature = (extracted.title.strip().lower(), extracted.description.strip().lower())
                        if signature in existing_signatures:
                            continue
                            
                        req_id = f"REQ-{current_count + added_count + 1:03d}"
                        new_req = RequirementRaw(
                            id=req_id,
                            title=extracted.title,
                            description=extracted.description,
                            type=extracted.type,
                            source="Discovery Conversation"
                        )
                        new_requirements_captured.append(new_req)
                        existing_signatures.add(signature)
                        added_count += 1
                    
                    if new_requirements_captured:
                        state["requirements_raw"].extend(new_requirements_captured)
                        logger.info(f"Extracted {len(new_requirements_captured)} requirements from agent response.")
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        except Exception as e:
            logger.warning(f"Failed to extract requirements from agent response: {e}")
        
    # Update conversation history
    ConversationHistoryManager.add_message(
        state["conversation_history"], 
        "assistant", 
        response.content, 
        agent="Discovery Agent"
    )
    
    return state


# ============================================================================
# 3. Authoring Agent Node
# ============================================================================

def authoring_node(state: ForgeRequirementsState) -> ForgeRequirementsState:
    """
    Transforms raw requirements into user stories.
    """
    project_id = state["project_id"]
    logger.info(f"[{project_id}] Authoring Agent active.")
    
    # If we have raw requirements but no stories, generate them
    if state["requirements_raw"] and not state["user_stories"]:
        new_stories = []
        
        for req in state["requirements_raw"]:
            # Use LLM to generate story for each requirement
            prompt = f"""
            Transform this requirement into a User Story with Acceptance Criteria:
            Title: {req.title}
            Description: {req.description}
            Type: {req.type}
            
            Output JSON format:
            {{
                "title": "Story Title",
                "story_statement": "As a... I want... So that...",
                "acceptance_criteria": ["AC1", "AC2"],
                "effort": "M"
            }}
            """
            
            try:
                response = llm.invoke([
                    SystemMessage(content=AUTHORING_SYSTEM_PROMPT.format(requirements_count=1)),
                    HumanMessage(content=prompt)
                ])
                
                # Parse JSON (simplified)
                content = str(response.content).strip()
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                    
                data = json.loads(content)
                
                story = UserStory(
                    id=f"STORY-{len(new_stories)+1:03d}",
                    requirement_id=req.id,
                    title=data.get("title", req.title),
                    story_statement=data.get("story_statement", ""),
                    acceptance_criteria=data.get("acceptance_criteria", []),
                    edge_cases=[], # Could ask LLM for these too
                    definition_of_done=["Unit tests passed", "Code reviewed"],
                    effort_estimate=data.get("effort", "M")
                )
                new_stories.append(story)
                
            except Exception as e:
                logger.error(f"Failed to generate story for {req.id}: {e}")
        
        state["user_stories"] = new_stories
        state["authoring_complete"] = True
        
        ConversationHistoryManager.add_message(
            state["conversation_history"],
            "assistant",
            f"I've drafted {len(new_stories)} user stories based on your requirements. Please review them.",
            agent="Authoring Agent"
        )
        
    return state


# ============================================================================
# 4. Quality Agent Node
# ============================================================================

def quality_node(state: ForgeRequirementsState) -> ForgeRequirementsState:
    """
    Validates requirements and identifies issues.
    """
    project_id = state["project_id"]
    logger.info(f"[{project_id}] Quality Agent active.")
    
    # Run validation tools only once
    if state["requirements_raw"] and not state["quality_complete"]:
        validation_result = validate_requirements_quality(
            state["requirements_raw"],
            state["user_stories"]
        )
        
        state["quality_issues"] = validation_result.issues_found
        
        # Generate summary message
        issue_summary = (
            f"Found {validation_result.total_issues} issues: "
            f"{validation_result.critical_count} Critical, "
            f"{validation_result.high_count} High, "
            f"{validation_result.medium_count} Medium."
        )
        
        if validation_result.total_issues == 0:
            state["quality_issues_resolved"] = True
            msg = "Quality check passed! No issues found."
        else:
            msg = f"Quality check complete. {issue_summary}\n\nYou can acknowledge these issues and move forward by saying something like 'let's proceed' or 'acknowledge issues and continue'."
            
        state["quality_complete"] = True  # Mark complete whether or not issues found
        
        ConversationHistoryManager.add_message(
            state["conversation_history"],
            "assistant",
            msg,
            agent="Quality Agent"
        )
        
        # In a real interactive loop, we'd wait for user to fix or acknowledge
        # For MVP automation, if only Low/Medium issues, we might auto-acknowledge
        # But let's stick to the plan: User must resolve.
        # Since this is a node run, we just report. The Orchestrator/UI handles the loop.
        
    return state


# ============================================================================
# 5. Prioritization Agent Node
# ============================================================================

def prioritization_node(state: ForgeRequirementsState) -> ForgeRequirementsState:
    """
    Ranks requirements using a framework.
    """
    project_id = state["project_id"]
    logger.info(f"[{project_id}] Prioritization Agent active.")
    
    if not state["prioritization_complete"]:
        # Default to MoSCoW if not selected
        framework = state.get("prioritization_framework") or "MoSCoW"
        
        # In a real app, we'd ask the user for inputs here.
        # For MVP, we'll simulate applying the framework with default/random inputs
        # or inputs extracted from conversation.
        
        result = apply_prioritization_framework(
            framework,
            state["requirements_raw"],
            scoring_inputs={} # Empty inputs will use defaults in tool
        )
        
        state["prioritized_backlog"] = result.ranked_requirements
        state["prioritization_complete"] = True
        
        ConversationHistoryManager.add_message(
            state["conversation_history"],
            "assistant",
            f"Prioritization complete using {framework}. Top priority items: " + 
            ", ".join([r.title for r in result.ranked_requirements[:3]]),
            agent="Prioritization Agent"
        )
        
    return state


# ============================================================================
# 6. Synthesis Node
# ============================================================================

def synthesis_node(state: ForgeRequirementsState) -> ForgeRequirementsState:
    """
    Generates the final requirements document.
    """
    project_id = state["project_id"]
    logger.info(f"[{project_id}] Synthesis Node active.")
    
    if not state["synthesis_complete"]:
        # Prepare data for the prompt
        data_context = {
            "project_name": state["project_name"],
            "context": state["user_context"],
            "requirements": [r.model_dump() for r in state["requirements_raw"]],
            "stories": [s.model_dump() for s in state["user_stories"]],
            "priorities": [p.model_dump() for p in state["prioritized_backlog"]],
            "risks": [r.model_dump() for r in state["acknowledged_risks"]]
        }
        
        prompt = f"""
        Generate the final Requirements Specification Document based on this data:
        {json.dumps(data_context, default=str)}
        
        Follow the 10-section structure defined in your system prompt.
        Output valid Markdown.
        """
        
        response = llm.invoke([
            SystemMessage(content=SYNTHESIS_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ])
        
        state["final_deliverable"] = str(response.content)
        state["synthesis_complete"] = True
        # Don't set workflow_phase to "complete" - let user decide when done
        
        ConversationHistoryManager.add_message(
            state["conversation_history"],
            "assistant",
            "✅ Requirements Document Generated!\n\nYour final Requirements Specification Document is ready. You can download it from the sidebar.\n\nYou can also continue refining the requirements:\n- **Add requirements** - Return to discovery to add more requirements\n- **Refine stories** - Go back to authoring to adjust user stories\n- **Review issues** - Return to quality review\n- **Adjust priorities** - Go back to prioritization\n- **Regenerate document** - Create an updated version with current changes\n- **Done** - When you're satisfied, just say 'done' to finish",
            agent="Synthesis Agent"
        )
        
    return state
