"""
Text-to-Speech using OpenAI TTS API.

Converts agent text responses to audio for playback.
"""

import asyncio
import os
from typing import AsyncIterator, Optional

from openai import AsyncOpenAI

from .events import AgentChunkEvent, AgentEndEvent, TTSChunkEvent, VoiceAgentEvent


class OpenAITTS:
    """
    OpenAI Text-to-Speech processor.
    
    Converts text to speech using OpenAI's TTS API.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "tts-1",
        voice: str = "alloy",
        response_format: str = "pcm",
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = model
        self.voice = voice
        self.response_format = response_format
        
        self._text_buffer: list[str] = []
        self._closed = False

    async def synthesize(self, text: str) -> Optional[bytes]:
        """
        Synthesize text to audio.
        
        Returns audio bytes or None if synthesis fails.
        """
        if self._closed or not text.strip():
            return None
        
        try:
            response = await self.client.audio.speech.create(
                model=self.model,
                voice=self.voice,
                input=text,
                response_format=self.response_format,
            )
            return response.content
        except Exception as e:
            print(f"[TTS] Synthesis error: {e}")
            return None

    async def synthesize_streaming(self, text: str) -> AsyncIterator[bytes]:
        """
        Synthesize text to audio with streaming output.
        
        Yields audio chunks as they become available.
        """
        if self._closed or not text.strip():
            return
        
        try:
            async with self.client.audio.speech.with_streaming_response.create(
                model=self.model,
                voice=self.voice,
                input=text,
                response_format=self.response_format,
            ) as response:
                async for chunk in response.iter_bytes(chunk_size=4096):
                    yield chunk
        except Exception as e:
            print(f"[TTS] Streaming synthesis error: {e}")

    def add_text(self, text: str):
        """Add text to the buffer for batch synthesis."""
        self._text_buffer.append(text)

    async def flush(self) -> Optional[bytes]:
        """Synthesize all buffered text."""
        if not self._text_buffer:
            return None
        
        full_text = "".join(self._text_buffer)
        self._text_buffer.clear()
        
        return await self.synthesize(full_text)

    async def close(self):
        """Close the TTS processor."""
        self._closed = True
        self._text_buffer.clear()


async def tts_stream(
    event_stream: AsyncIterator[VoiceAgentEvent],
) -> AsyncIterator[VoiceAgentEvent]:
    """
    Transform stream: Voice Events → Voice Events (with Audio)
    
    Passes through all upstream events and adds TTS audio events
    when processing agent text chunks.
    """
    tts = OpenAITTS()
    text_buffer: list[str] = []
    
    try:
        async for event in event_stream:
            # Pass through all events
            yield event
            
            # Collect agent text chunks
            if isinstance(event, AgentChunkEvent):
                text_buffer.append(event.text)
            
            # Synthesize on agent end
            elif isinstance(event, AgentEndEvent):
                if text_buffer:
                    full_text = "".join(text_buffer)
                    text_buffer.clear()
                    
                    # Stream audio chunks
                    async for audio_chunk in tts.synthesize_streaming(full_text):
                        yield TTSChunkEvent.create(audio_chunk)
    finally:
        await tts.close()
