"""Forge Requirements Builder - Multi-Agent Requirements System

A 5-agent orchestrated network that guides users through the complete requirements 
lifecycle: Discovery → Authoring → Quality → Prioritization → Synthesis.
"""

__version__ = "1.0.0"
__author__ = "Forge Agent Builder"

from .state import (
    ForgeRequirementsState,
    RequirementRaw,
    UserStory,
    QualityIssue,
    AcknowledgedRisk,
    PrioritizedRequirement,
    create_project_state,
)

__all__ = [
    "ForgeRequirementsState",
    "RequirementRaw",
    "UserStory",
    "QualityIssue",
    "AcknowledgedRisk",
    "PrioritizedRequirement",
    "create_project_state",
]
