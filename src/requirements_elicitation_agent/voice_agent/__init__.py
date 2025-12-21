"""
Voice Agent Interface for Forge Requirements Assistant.

Implements the LangChain "Sandwich" voice agent architecture:
STT (Speech-to-Text) → LangChain Agent → TTS (Text-to-Speech)
"""

from .events import (
    VoiceAgentEvent,
    STTChunkEvent,
    STTOutputEvent,
    AgentChunkEvent,
    AgentEndEvent,
    TTSChunkEvent,
)
from .server import create_voice_app

__all__ = [
    "VoiceAgentEvent",
    "STTChunkEvent",
    "STTOutputEvent",
    "AgentChunkEvent",
    "AgentEndEvent",
    "TTSChunkEvent",
    "create_voice_app",
]
