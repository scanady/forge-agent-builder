"""
Tool definitions for the Forge Requirements Assistant.

Implements tools defined in plan.md Section 5.
"""

from typing import Optional, Annotated
from pydantic import BaseModel, Field
from langchain_core.tools import tool


@tool
def read_file(file_path: Annotated[str, "The absolute path to the file to read"]) -> str:
    """Read the contents of a file to extract requirements.
    
    Supports .txt, .md files. PDF and DOCX support are stretch goals.
    
    Args:
        file_path: The absolute path to the file to read
        
    Returns:
        The file contents as a string
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        IOError: If the file cannot be read
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        return f"Error: File not found at {file_path}"
    except Exception as e:
        return f"Error reading file: {str(e)}"


class RecordRequirement(BaseModel):
    """Structured output schema for requirement recording.
    
    Used by requirement_recorder node to parse user input.
    Implements the schema defined in plan.md Section 5.2.
    """
    description: str = Field(description="The clear, atomic requirement text. Should be a single, testable statement.")
    category: str = Field(description="The classification: Functional, Non-Functional, Constraint, or Technical Constraint")
    is_vague: bool = Field(description="True if the requirement lacks specificity (e.g., 'make it fast' without metrics)")
    is_risk: bool = Field(description="True if the requirement poses a security or viability risk")
    risk_warning: Optional[str] = Field(default=None, description="Warning message if is_risk is true")
    conflicts_with: list[str] = Field(default_factory=list, description="List of requirement IDs this conflicts with")
    needs_paraphrase: bool = Field(default=False, description="True if statement is complex and needs confirmation")
    paraphrase_text: Optional[str] = Field(default=None, description="Paraphrased version for user confirmation")
    out_of_scope: Optional[str] = Field(default=None, description="If out-of-scope (architecture/code/priority), the redirect message")


class DocumentSummary(BaseModel):
    """Structured output for document analysis.
    
    Used by doc_reader node to summarize uploaded documents.
    """
    topic: str = Field(description="Brief 1-sentence summary of the document's main topic")
    appears_relevant: bool = Field(description="Whether this document likely contains requirements")
    document_type: str = Field(description="Type of document: meeting notes, technical spec, email, etc.")


class RequirementExtraction(BaseModel):
    """Structured output for extracting requirements from documents.
    
    Used by doc_extractor node.
    """
    requirements: list[RecordRequirement] = Field(description="List of atomic requirements extracted from document")


class MultipleRequirements(BaseModel):
    """Schema for extracting multiple requirements from a single user message.
    
    Used when user provides complex answers containing multiple distinct requirements.
    """
    requirements: list[RecordRequirement] = Field(description="List of all distinct requirements mentioned in the user's message. Extract ALL requirements mentioned, not just one.")
    needs_paraphrase: bool = Field(default=False, description="True if the entire set of requirements is complex and needs confirmation")
    paraphrase_text: Optional[str] = Field(default=None, description="Paraphrased version summarizing all requirements for user confirmation")
