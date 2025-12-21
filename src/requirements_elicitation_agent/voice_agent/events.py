"""
Voice Agent Event Types

Defines typed dataclasses for all events that flow through
the voice agent pipeline, from user audio input through STT,
agent processing, and TTS output.
"""

import base64
import time
from dataclasses import dataclass, field
from typing import Literal, Union


def _now_ms() -> int:
    """Return current Unix timestamp in milliseconds."""
    return int(time.time() * 1000)


@dataclass
class STTChunkEvent:
    """Partial transcription result (real-time feedback)."""
    type: Literal["stt_chunk"] = field(default="stt_chunk", init=False)
    transcript: str = ""
    ts: int = field(default_factory=_now_ms)

    @classmethod
    def create(cls, transcript: str) -> "STTChunkEvent":
        return cls(transcript=transcript)


@dataclass
class STTOutputEvent:
    """Final, formatted transcription that triggers agent processing."""
    type: Literal["stt_output"] = field(default="stt_output", init=False)
    transcript: str = ""
    ts: int = field(default_factory=_now_ms)

    @classmethod
    def create(cls, transcript: str) -> "STTOutputEvent":
        return cls(transcript=transcript)


STTEvent = Union[STTChunkEvent, STTOutputEvent]


@dataclass
class AgentChunkEvent:
    """Text chunk from agent response (streaming)."""
    type: Literal["agent_chunk"] = field(default="agent_chunk", init=False)
    text: str = ""
    ts: int = field(default_factory=_now_ms)

    @classmethod
    def create(cls, text: str) -> "AgentChunkEvent":
        return cls(text=text)


@dataclass
class AgentEndEvent:
    """Signals end of agent turn."""
    type: Literal["agent_end"] = field(default="agent_end", init=False)
    ts: int = field(default_factory=_now_ms)

    @classmethod
    def create(cls) -> "AgentEndEvent":
        return cls()


@dataclass
class TTSChunkEvent:
    """Audio chunk for playback (base64-encoded)."""
    type: Literal["tts_chunk"] = field(default="tts_chunk", init=False)
    audio: str = ""  # Base64 encoded audio
    ts: int = field(default_factory=_now_ms)

    @classmethod
    def create(cls, audio_bytes: bytes) -> "TTSChunkEvent":
        return cls(audio=base64.b64encode(audio_bytes).decode())


# Union type for all voice agent events
VoiceAgentEvent = Union[STTChunkEvent, STTOutputEvent, AgentChunkEvent, AgentEndEvent, TTSChunkEvent]


def event_to_dict(event: VoiceAgentEvent) -> dict:
    """Convert a voice agent event to a dictionary for JSON serialization."""
    if isinstance(event, STTChunkEvent):
        return {"type": "stt_chunk", "transcript": event.transcript, "ts": event.ts}
    elif isinstance(event, STTOutputEvent):
        return {"type": "stt_output", "transcript": event.transcript, "ts": event.ts}
    elif isinstance(event, AgentChunkEvent):
        return {"type": "agent_chunk", "text": event.text, "ts": event.ts}
    elif isinstance(event, AgentEndEvent):
        return {"type": "agent_end", "ts": event.ts}
    elif isinstance(event, TTSChunkEvent):
        return {"type": "tts_chunk", "audio": event.audio, "ts": event.ts}
    else:
        raise ValueError(f"Unknown event type: {type(event)}")
