"""
Node implementations for the Forge Requirements Assistant.

Implements all nodes defined in plan.md Section 4, with persona behaviors
from persona.md integrated throughout.
"""

import re
import os
from typing import Literal, Optional
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from .state import AgentState, Requirement, TodoItem
from .tools import read_file, RecordRequirement, DocumentSummary, RequirementExtraction, MultipleRequirements
from .persona_loader import load_greeting, load_interviewer_prompt, load_recorder_prompt, load_gap_analyzer_prompt, load_doc_extractor_prompt


def get_llm():
    """Get or create LLM instance lazily."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found. Please set it in your .env file or environment variables."
        )
    model = os.getenv("OPENAI_MODEL", "gpt-4o")  # Default to gpt-4o if not specified
    temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    return ChatOpenAI(model=model, temperature=temperature)


def initializer(state: AgentState) -> dict:
    """Initialize the requirements discovery session.
    
    Ref: Plan Section 4.2
    Task: 3.1
    
    Greets user and determines session mode (interactive vs document analysis).
    """
    messages = state.get("messages", [])
    current_phase = state.get("current_phase")
    
    # If this is the first interaction (no phase set or only 1 user message), provide greeting
    if not current_phase or (len(messages) == 1 and isinstance(messages[0], HumanMessage)):
        greeting = load_greeting()
        
        return {
            "messages": [AIMessage(content=greeting)],
            "current_phase": "init",
            "requirements": [],
            "todo_list": [],
            "clarification_counts": {},
            "pending_file_path": None,
            "pending_risk_warning": None,
            "pending_paraphrase": None,
            "user_expertise": None
        }
    
    # Session already initialized
    return {}


def interviewer(state: AgentState) -> dict:
    """Generate contextual questions to elicit requirements.
    
    Ref: Plan Section 4.3, Persona Directives #2, #5, #15, #16
    Tasks: 3.2, 3.12
    
    Uses layered questioning approach with progress transparency.
    """
    todo_list = state.get("todo_list", [])
    requirements = state.get("requirements", [])
    messages = state.get("messages", [])
    user_expertise = state.get("user_expertise", None)
    
    # Seed todo list if empty - FOCUS on functional requirements from user perspective first
    if not todo_list:
        todo_list = [
            # Primary focus: WHO uses the system and HOW
            {"topic": "User Roles & Personas", "status": "pending"},
            {"topic": "Core User Goals", "status": "pending"},
            {"topic": "Key User Workflows", "status": "pending"},
            {"topic": "User Interactions & Features", "status": "pending"},
            {"topic": "Data & Information Needs", "status": "pending"},
            # Secondary: Explore after core functional requirements
            {"topic": "Edge Cases & Exceptions", "status": "pending"}
        ]
    
    # Find next pending topic
    pending_topics = [t for t in todo_list if t["status"] == "pending"]
    covered_topics = [t["topic"] for t in todo_list if t["status"] == "covered"]
    
    # Directive #15: Suggest completion check if all covered
    if not pending_topics:
        completion_message = f"""That's great progress! We've covered: {', '.join(covered_topics)}.

I think we've explored the main areas. Would you like to:
- **Review** what we've captured (say "show me the requirements")
- **Explore** any other aspects you'd like to discuss
- **Move forward** with what we have

What would you like to do?"""
        return {"messages": [AIMessage(content=completion_message)]}
    
    current_topic = pending_topics[0]["topic"]
    
    # Directive #16: Progress breadcrumb
    breadcrumb = ""
    if covered_topics:
        breadcrumb = f"We've covered {', '.join(covered_topics)}. "
    
    # Build system prompt with persona identity (Task 3.13)
    prompt_template = load_interviewer_prompt()
    
    # Build adaptive section based on user expertise
    if user_expertise == 'experienced':
        adaptive_section = "- User is EXPERIENCED: Use faster pace, fewer examples, assume domain vocabulary"
    elif user_expertise == 'exploratory':
        adaptive_section = "- User is EXPLORATORY: Provide more structure, suggest requirement formats, model good statements"
    else:
        adaptive_section = "- Expertise unknown: Use moderate scaffolding, assess from responses"
    
    # Format the template with current context
    system_prompt = prompt_template.format(
        current_topic=current_topic,
        covered_topics=', '.join(covered_topics) if covered_topics else 'None yet',
        requirements_count=len(requirements),
        user_expertise=user_expertise or 'unknown',
        adaptive_section=adaptive_section,
        breadcrumb=breadcrumb
    )
    
    # Get previous context for adaptive questioning
    recent_messages = messages[-4:] if len(messages) >= 4 else messages
    context_str = "\n".join([
        f"{'AI' if isinstance(m, AIMessage) else 'Human'}: {m.content[:200]}"
        for m in recent_messages
    ])
    
    user_prompt = f"""Recent conversation:
{context_str}

Generate your question about {current_topic}. Remember to:
- {breadcrumb}
- Use layered questioning (broad → specific)
- Match the user's expertise level
- Be encouraging and patient"""
    
    response = get_llm().invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])
    
    return {
        "messages": [AIMessage(content=response.content)],
        "current_phase": "elicitation",
        "todo_list": todo_list
    }


def requirement_recorder(state: AgentState) -> dict:
    """Parse user input and record requirements with persona behaviors.
    
    Ref: Plan Section 4.4, Persona Directives #3-8, #11-14
    Tasks: 3.3-3.6, 3.11
    
    Handles: recording, conflicts, risks, vagueness, scope boundaries, paraphrasing.
    """
    messages = state.get("messages", [])
    requirements = state.get("requirements", [])
    clarification_counts = state.get("clarification_counts", {})
    user_expertise = state.get("user_expertise", None)
    pending_paraphrase = state.get("pending_paraphrase")
    
    if not messages:
        return {}
    
    last_message = messages[-1]
    if not isinstance(last_message, HumanMessage):
        return {}
    
    user_input = last_message.content
    
    # Check if user is confirming a paraphrase
    if pending_paraphrase and user_input.lower().strip() in ['yes', 'correct', 'right', 'yep', 'yeah', 'that\'s right', 'that is right', 'exactly']:
        # User confirmed - record the pending requirement(s)
        new_reqs = []
        confirmations = []
        
        # Handle multiple requirements
        if "requirements" in pending_paraphrase:
            for pending_req in pending_paraphrase["requirements"]:
                req_id = f"REQ-{len(requirements) + len(new_reqs) + 1:03d}"
                new_req: Requirement = {
                    "id": req_id,
                    "description": pending_req["description"],
                    "category": pending_req["category"],
                    "tags": pending_req.get("tags", []),
                    "source": "User Interview"
                }
                new_reqs.append(new_req)
                confirmation = f"{req_id}: {new_req['description']} ({new_req['category']})"
                if new_req['tags']:
                    confirmation += f" [{', '.join(new_req['tags'])}]"
                confirmations.append(confirmation)
        else:
            # Single requirement (legacy support)
            req_id = f"REQ-{len(requirements) + 1:03d}"
            new_req: Requirement = {
                "id": req_id,
                "description": pending_paraphrase["description"],
                "category": pending_paraphrase["category"],
                "tags": pending_paraphrase.get("tags", []),
                "source": "User Interview"
            }
            new_reqs.append(new_req)
            confirmation = f"{req_id}: {new_req['description']} ({new_req['category']})"
            if new_req['tags']:
                confirmation += f" [{', '.join(new_req['tags'])}]"
            confirmations.append(confirmation)
        
        # Update requirements silently - user can view them in Current Requirements
        return {
            "requirements": requirements + new_reqs,
            "pending_paraphrase": None
        }
    
    # Check if user is rejecting a paraphrase
    if pending_paraphrase and user_input.lower().strip() in ['no', 'not quite', 'not exactly', 'incorrect', 'nope', 'wrong']:
        # User rejected - ask for clarification
        clarification = "I see. Could you clarify what I misunderstood? Please rephrase the requirement."
        return {
            "messages": [AIMessage(content=clarification)],
            "pending_paraphrase": None
        }
    
    # Build system prompt with persona behaviors (Task 3.13)
    prompt_template = load_recorder_prompt()
    
    # Format with context variables
    formatted_prompt = prompt_template.format(
        requirements_count=len(requirements),
        user_expertise=user_expertise or 'unknown',
        clarification_count=clarification_counts.get('total', 0)
    )
    
    # Use structured output for multiple requirements
    structured_llm = get_llm().with_structured_output(MultipleRequirements)
    
    try:
        result: MultipleRequirements = structured_llm.invoke([
            SystemMessage(content=formatted_prompt),
            HumanMessage(content=f"User message to analyze:\n{user_input}")
        ])
        
        # If no requirements extracted, skip
        if not result.requirements:
            return {}
        
        # Handle paraphrasing for multiple requirements (Directive #3)
        if result.needs_paraphrase and result.paraphrase_text:
            # Store ALL requirements for later confirmation
            pending_reqs = []
            for req in result.requirements:
                pending_req = {
                    "description": req.description,
                    "category": req.category,
                    "tags": [],
                    "conflicts_with": req.conflicts_with or []
                }
                if req.is_risk:
                    pending_req["tags"].append("RISK_ACCEPTED")
                if req.conflicts_with:
                    pending_req["tags"].extend([f"CONFLICT with {cid}" for cid in req.conflicts_with])
                pending_reqs.append(pending_req)
            
            return {
                "messages": [AIMessage(content=result.paraphrase_text)],
                "pending_paraphrase": {"requirements": pending_reqs}  # Store multiple
            }
        
        # Process each requirement
        new_requirements = []
        confirmations = []
        
        for req in result.requirements:
            # Handle out-of-scope (Task 3.11, Directives #12-14)
            if req.out_of_scope:
                return {"messages": [AIMessage(content=req.out_of_scope)]}
            
            # Handle risk warnings (Directive #8)
            if req.is_risk and req.risk_warning:
                pending_req = {
                    "description": req.description,
                    "category": req.category,
                    "risk_warning": req.risk_warning
                }
                return {
                    "messages": [AIMessage(content=req.risk_warning)],
                    "pending_risk_warning": str(pending_req)
                }
            
            # Handle vagueness - Three-Strike Rule (Directive #6)
            description = req.description
            tags = []
            
            if req.is_vague:
                topic_key = req.description[:50]  # Use first 50 chars as key
                count = clarification_counts.get(topic_key, 0) + 1
                clarification_counts[topic_key] = count
                
                if count <= 3:
                    # Progressive clarification
                    if count == 1:
                        clarification = f"I'd like to understand '{req.description}' better. Could you be more specific? For example, what does that mean in concrete terms?"
                    elif count == 2:
                        clarification = f"Can you give me a specific target or metric? For instance, a number, time limit, or measurable criterion?"
                    else:  # count == 3
                        clarification = f"Let me try once more: can you describe the most important aspect or provide any concrete detail?"
                    
                    if count < 3:
                        return {
                            "messages": [AIMessage(content=clarification)],
                            "clarification_counts": clarification_counts
                        }
                    else:
                        # Strike 3: Record with tag
                        description = description + " [NEEDS_REFINEMENT]"
                        tags.append("NEEDS_REFINEMENT")
            
            # Build tags
            if req.is_risk:
                tags.append("RISK_ACCEPTED")
            if req.conflicts_with:
                tags.extend([f"CONFLICT with {cid}" for cid in req.conflicts_with])
            
            # Generate new requirement ID
            req_id = f"REQ-{len(requirements) + len(new_requirements) + 1:03d}"
            
            # Create requirement (Directive #4: Append-only, #11: Source attribution)
            new_req: Requirement = {
                "id": req_id,
                "description": description,
                "category": req.category,
                "tags": tags,
                "source": "User Interview"  # Directive #11
            }
            new_requirements.append(new_req)
            
            # Build confirmation message
            confirmation = f"{req_id}: {description} ({req.category})"
            if tags:
                confirmation += f" [{', '.join(tags)}]"
            confirmations.append(confirmation)
            
            # Add conflict notification if applicable (Directive #7)
            if req.conflicts_with:
                conflict_ids = ', '.join(req.conflicts_with)
                confirmations.append(f"  ⚠️  Conflicts with {conflict_ids}")
        
        # Update requirements silently - user can view them in Current Requirements
        updated_reqs = requirements + new_requirements
        
        # Detect user expertise for adaptive communication (Task 3.12)
        new_expertise = detect_user_expertise(user_input, user_expertise)
        
        return {
            "requirements": updated_reqs,
            "clarification_counts": clarification_counts,
            "user_expertise": new_expertise
        }
        
    except Exception as e:
        error_msg = f"I had trouble processing that. Could you rephrase or provide more detail? (Error: {str(e)})"
        return {"messages": [AIMessage(content=error_msg)]}


def detect_user_expertise(user_input: str, current_expertise: Optional[str]) -> Optional[Literal["experienced", "exploratory"]]:
    """Detect user expertise level for adaptive communication.
    
    Ref: Plan Section 2.2, Persona - Adaptive Depth
    Task: 3.12
    
    Heuristics:
    - Experienced: Technical jargon, detailed responses (>100 words), specific metrics
    - Exploratory: Brief responses (<50 words), vague terms, questions back to agent
    """
    if current_expertise:
        return current_expertise  # Don't change once determined
    
    word_count = len(user_input.split())
    has_technical_terms = any(term in user_input.lower() for term in [
        'api', 'database', 'authentication', 'scalability', 'latency', 
        'microservice', 'backend', 'frontend', 'deployment', 'architecture'
    ])
    has_metrics = bool(re.search(r'\d+\s*(seconds?|users?|requests?|ms|gb|mb)', user_input.lower()))
    
    if word_count > 100 and (has_technical_terms or has_metrics):
        return "experienced"
    elif word_count < 50 and not has_technical_terms:
        return "exploratory"
    
    return None  # Keep as unknown


def gap_analyzer(state: AgentState) -> dict:
    """Identify unexplored requirement domains and update todo list.
    
    Ref: Plan Section 4.5, Persona Directives #1, #5
    Task: 3.7
    
    IMPORTANT: Focus on functional requirements first. Only suggest non-functional
    domains (Security, Performance, etc.) AFTER the user has captured sufficient
    functional requirements (at least 5+ requirements covering core user workflows).
    """
    requirements = state.get("requirements", [])
    todo_list = state.get("todo_list", [])
    
    # Count functional requirements (non-constraint, non-technical)
    functional_req_count = sum(
        1 for r in requirements 
        if r.get('category', '').lower() not in ['constraint', 'technical constraint', 'non-functional']
    )
    
    # Primary domains - always check these (user-centric, functional)
    primary_domains = [
        "User Roles & Personas", "Core User Goals", "Key User Workflows",
        "User Interactions & Features", "Data & Information Needs",
        "Edge Cases & Exceptions"
    ]
    
    # Secondary domains - only suggest AFTER sufficient functional requirements (5+)
    secondary_domains = [
        "Security", "Performance", "Usability",
        "Admin Capabilities", "Error Handling"
    ]
    
    # Build domain list based on progress
    standard_domains = primary_domains.copy()
    if functional_req_count >= 5:
        standard_domains.extend(secondary_domains)
    
    # Check which domains are already covered
    existing_topics = {item["topic"] for item in todo_list}
    
    # Use LLM to determine which domains are covered by existing requirements
    if requirements:
        req_summary = "\n".join([f"- {r['description']}" for r in requirements])
        
        prompt_template = load_gap_analyzer_prompt()
        system_prompt = prompt_template.format(
            standard_domains=', '.join(standard_domains),
            requirements=req_summary
        )
        
        try:
            response = get_llm().invoke([SystemMessage(content=system_prompt)])
            covered_domains = []
            for line in response.content.split('\n'):
                if ':' in line:
                    domain, status = line.split(':', 1)
                    if 'YES' in status.upper():
                        covered_domains.append(domain.strip())
        except:
            covered_domains = []
    else:
        covered_domains = []
    
    # Add missing domains to todo list
    for domain in standard_domains:
        if domain not in existing_topics and domain not in covered_domains:
            todo_list.append({"topic": domain, "status": "pending"})
    
    # Mark current topic as covered (Directive #5)
    if todo_list:
        # Find the topic being discussed
        pending_topics = [t for t in todo_list if t["status"] == "pending"]
        if pending_topics:
            # Mark first pending as covered
            for item in todo_list:
                if item["topic"] == pending_topics[0]["topic"]:
                    item["status"] = "covered"
                    break
    
    return {"todo_list": todo_list}


def doc_reader(state: AgentState) -> dict:
    """Read uploaded file and validate relevance.
    
    Ref: Plan Section 4.6, Persona Directive #9
    Task: 3.8
    
    Validates document relevance before extraction.
    """
    messages = state.get("messages", [])
    
    if not messages:
        return {}
    
    last_message = messages[-1]
    if not isinstance(last_message, HumanMessage):
        return {}
    
    # Extract file path from message
    file_path_match = re.search(r'file:///(.+?)(?:\s|$)', last_message.content)
    if not file_path_match:
        # Try "I uploaded a file: <path>" pattern
        file_path_match = re.search(r'(?:uploaded\s+a\s+file|file):\s*(.+?\.(?:txt|md|pdf|docx))(?:\s|$)', 
                                   last_message.content, re.IGNORECASE)
    if not file_path_match:
        # Try other patterns
        file_path_match = re.search(r'(?:uploaded?|file|analyze|read)\s+(.+?\.(?:txt|md|pdf|docx))(?:\s|$)', 
                                   last_message.content, re.IGNORECASE)
    
    if not file_path_match:
        return {}
    
    file_path = file_path_match.group(1).strip()
    
    # Read file
    content = read_file.invoke({"file_path": file_path})
    
    if content.startswith("Error"):
        return {"messages": [AIMessage(content=content)]}
    
    # Generate summary and validate relevance (Directive #9)
    structured_llm = get_llm().with_structured_output(DocumentSummary)
    
    try:
        summary: DocumentSummary = structured_llm.invoke([
            SystemMessage(content="""Analyze this document and provide:
1. A 1-2 sentence summary of what the document is about (topic/subject matter)
2. Whether it likely contains software or system requirements
3. The document type (meeting notes, technical spec, email, user story, etc.)

Keep the summary natural and concise."""),
            HumanMessage(content=f"Document content:\n{content[:2000]}")  # First 2000 chars
        ])
        
        # Ask for confirmation (Directive #9)
        confirmation_msg = f"""I found a {summary.document_type} about {summary.topic}.

Should I extract requirements from this document?
(Reply 'yes' to proceed, or 'no' to skip)"""
        
        return {
            "messages": [AIMessage(content=confirmation_msg)],
            "pending_file_path": file_path,
            "current_phase": "analysis_confirm"
        }
        
    except Exception as e:
        error_msg = f"I had trouble analyzing that document. Could you confirm it's a text file? (Error: {str(e)})"
        return {"messages": [AIMessage(content=error_msg)]}


def doc_extractor(state: AgentState) -> dict:
    """Extract requirements atomically from confirmed document.
    
    Ref: Plan Section 4.7, Persona Directives #10, #11
    Task: 3.9
    
    Extracts atomic requirements with source attribution.
    """
    pending_file_path = state.get("pending_file_path")
    requirements = state.get("requirements", [])
    
    if not pending_file_path:
        return {}
    
    # Read file content
    content = read_file.invoke({"file_path": pending_file_path})
    
    if content.startswith("Error"):
        return {
            "messages": [AIMessage(content=content)],
            "pending_file_path": None
        }
    
    # Extract requirements atomically (Directive #10)
    structured_llm = get_llm().with_structured_output(RequirementExtraction)
    
    prompt_template = load_doc_extractor_prompt()
    system_prompt = prompt_template
    
    try:
        extraction: RequirementExtraction = structured_llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Document content:\n{content}")
        ])
        
        # Create requirement objects with source attribution (Directive #11)
        filename = pending_file_path.split('/')[-1].split('\\')[-1]
        new_reqs = []
        
        for idx, req in enumerate(extraction.requirements):
            req_id = f"REQ-{len(requirements) + idx + 1:03d}"
            new_req: Requirement = {
                "id": req_id,
                "description": req.description,
                "category": req.category,
                "tags": [],
                "source": f"File: {filename}"  # Directive #11
            }
            new_reqs.append(new_req)
        
        updated_reqs = requirements + new_reqs
        
        summary_msg = f"I extracted {len(new_reqs)} requirements from {filename}."
        
        return {
            "messages": [AIMessage(content=summary_msg)],
            "requirements": updated_reqs,
            "pending_file_path": None,
            "current_phase": "elicitation"
        }
        
    except Exception as e:
        error_msg = f"I had trouble extracting requirements from that document. (Error: {str(e)})"
        return {
            "messages": [AIMessage(content=error_msg)],
            "pending_file_path": None
        }


def output_generator(state: AgentState) -> dict:
    """Generate the Raw Requirements Dump in Markdown format.
    
    Ref: Plan Section 4.8, Spec Step 6, Persona Directive #17
    Task: 3.10
    
    Formats requirements as specified in the spec.
    """
    requirements = state.get("requirements", [])
    
    if not requirements:
        no_reqs_msg = """I haven't captured any requirements yet.

Would you like to:
- Start an interactive discovery session
- Upload a document to analyze
- Ask me questions about the process"""
        return {"messages": [AIMessage(content=no_reqs_msg)]}
    
    # Group by category
    by_category = {
        "Functional": [],
        "Non-Functional": [],
        "Constraint": [],
        "Technical Constraint": []
    }
    
    conflicts = []
    warnings = []
    refinements = []
    
    for req in requirements:
        by_category[req["category"]].append(req)
        
        # Collect flagged items
        for tag in req["tags"]:
            if "CONFLICT" in tag:
                conflicts.append(req)
            elif "RISK_ACCEPTED" in tag:
                warnings.append(req)
            elif "NEEDS_REFINEMENT" in tag:
                refinements.append(req)
    
    # Build Markdown output
    output = "# Raw Captured Requirements\n\n"
    output += f"**Total Requirements:** {len(requirements)}\n\n"
    output += "---\n\n"
    
    # Requirements by category
    for category, reqs in by_category.items():
        if reqs:
            output += f"## {category}\n\n"
            for req in reqs:
                tags_str = f" [{', '.join(req['tags'])}]" if req['tags'] else ""
                source_str = f" *(Source: {req['source']})*"
                output += f"- **{req['id']}:** {req['description']}{tags_str}{source_str}\n"
            output += "\n"
    
    # Flags & Warnings section
    if conflicts or warnings or refinements:
        output += "---\n\n## Flags & Warnings\n\n"
        
        if conflicts:
            output += "### Conflicts\n"
            output += "The following requirements have contradictions that need resolution:\n\n"
            for req in conflicts:
                output += f"- **{req['id']}:** {req['description']}\n"
                for tag in req['tags']:
                    if "CONFLICT" in tag:
                        output += f"  - {tag}\n"
            output += "\n"
        
        if warnings:
            output += "### Risk Accepted\n"
            output += "These requirements were flagged as risks but accepted by user:\n\n"
            for req in warnings:
                output += f"- **{req['id']}:** {req['description']}\n"
            output += "\n"
        
        if refinements:
            output += "### Needs Refinement\n"
            output += "These requirements need more specific detail:\n\n"
            for req in refinements:
                output += f"- **{req['id']}:** {req['description']}\n"
            output += "\n"
    
    output += "---\n\n"
    output += "*This is a raw requirements dump ready for formal PRD structuring.*"
    
    return {"messages": [AIMessage(content=output)]}
