"""
Speech-to-Text using OpenAI Whisper API.

Processes audio chunks and converts them to text transcripts.
Uses OpenAI's Whisper model for high-quality transcription.
"""

import asyncio
import io
import os
import struct
import tempfile
from typing import AsyncIterator, Optional

from openai import AsyncOpenAI

from .events import STTChunkEvent, STTOutputEvent, VoiceAgentEvent


class OpenAISTT:
    """
    OpenAI Whisper Speech-to-Text processor.
    
    Accumulates audio chunks and transcribes them when silence is detected
    or when the buffer reaches a certain size.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "whisper-1",
        language: str = "en",
        min_audio_length: float = 1.0,  # Minimum seconds of audio before transcribing
        max_audio_length: float = 30.0,  # Maximum seconds before forcing transcription
        sample_rate: int = 16000,  # Expected input sample rate
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = model
        self.language = language
        self.min_audio_length = min_audio_length
        self.max_audio_length = max_audio_length
        
        # Audio buffer
        self._audio_chunks: list[bytes] = []
        self._total_bytes = 0
        self._sample_rate = sample_rate
        self._bytes_per_sample = 2  # 16-bit
        self._min_bytes = int(min_audio_length * self._sample_rate * self._bytes_per_sample)
        self._max_bytes = int(max_audio_length * self._sample_rate * self._bytes_per_sample)
        
        # Silence detection - more lenient thresholds
        self._silence_threshold = 200  # Higher threshold to ignore background noise
        self._silence_duration = 1.5  # Seconds of silence to trigger transcription
        self._silence_bytes = int(self._silence_duration * self._sample_rate * self._bytes_per_sample)
        self._consecutive_silence = 0
        
        # Minimum speech amplitude to trigger transcription
        self._min_speech_amplitude = 300  # Must see speech above this level
        self._has_detected_speech = False
        
        self._closed = False
        self._paused = False  # Pause processing during TTS playback
        self._debug = True  # Enable debug logging
        
        self._log(f"Initialized with sample_rate={sample_rate}, min_bytes={self._min_bytes}, silence_bytes={self._silence_bytes}")

    def _log(self, msg: str):
        if getattr(self, '_debug', True):
            print(f"[STT] {msg}")

    def pause(self):
        """Pause audio processing and clear buffer (used during TTS playback)."""
        self._paused = True
        self._audio_chunks = []
        self._total_bytes = 0
        self._consecutive_silence = 0
        self._has_detected_speech = False
        self._log("Paused and buffer cleared")

    def resume(self):
        """Resume audio processing."""
        self._paused = False
        self._has_detected_speech = False
        self._log("Resumed")

    async def process_audio(self, audio_chunk: bytes) -> Optional[str]:
        """
        Process an audio chunk and return transcript if ready.
        
        Returns None if more audio is needed, or the transcript string
        when enough audio has been collected and silence is detected.
        """
        if self._closed or self._paused:
            return None
        
        self._audio_chunks.append(audio_chunk)
        self._total_bytes += len(audio_chunk)
        
        # Check for silence in this chunk (simple amplitude check)
        is_silence, avg_amp = self._is_silence_with_amp(audio_chunk)
        
        # Track if we've seen real speech (not just noise)
        if avg_amp >= self._min_speech_amplitude:
            self._has_detected_speech = True
        
        if is_silence:
            self._consecutive_silence += len(audio_chunk)
        else:
            self._consecutive_silence = 0
        
        # Log periodically
        if self._total_bytes % 32000 < len(audio_chunk):  # Every ~1 second
            self._log(f"Buffer: {self._total_bytes} bytes, silence: {self._consecutive_silence} bytes, avg_amp: {avg_amp:.0f}, speech: {self._has_detected_speech}")
        
        # Force transcription if max length reached (only if speech was detected)
        if self._total_bytes >= self._max_bytes:
            if self._has_detected_speech:
                self._log(f"Max buffer reached ({self._total_bytes} bytes), transcribing...")
                return await self._transcribe()
            else:
                # Discard silent audio to prevent buffer from growing
                self._log(f"Max buffer reached but no speech detected, discarding...")
                self._audio_chunks = []
                self._total_bytes = 0
                self._consecutive_silence = 0
                return None
        
        # Check if we should transcribe (enough audio + silence detected + speech was present)
        if self._total_bytes >= self._min_bytes and self._consecutive_silence >= self._silence_bytes:
            if self._has_detected_speech:
                self._log(f"Silence detected after speech ({self._total_bytes} bytes), transcribing...")
                return await self._transcribe()
            else:
                # Silent period without speech, discard and reset
                self._log(f"Silence detected but no speech, discarding {self._total_bytes} bytes")
                self._audio_chunks = []
                self._total_bytes = 0
                self._consecutive_silence = 0
                return None
        
        return None

    def _is_silence_with_amp(self, audio_chunk: bytes) -> tuple[bool, float]:
        """Check if audio chunk is mostly silence. Returns (is_silence, avg_amplitude)."""
        if len(audio_chunk) < 2:
            return True, 0.0
        
        # Calculate average amplitude
        total = 0
        count = 0
        for i in range(0, len(audio_chunk) - 1, 2):
            sample = struct.unpack('<h', audio_chunk[i:i+2])[0]
            total += abs(sample)
            count += 1
        
        if count == 0:
            return True, 0.0
        
        avg_amplitude = total / count
        return avg_amplitude < self._silence_threshold, avg_amplitude

    async def _transcribe(self) -> Optional[str]:
        """Transcribe the buffered audio using Whisper API."""
        if not self._audio_chunks:
            return None
        
        # Combine all audio chunks
        audio_data = b''.join(self._audio_chunks)
        
        if len(audio_data) < self._min_bytes // 2:
            self._log(f"Audio too short ({len(audio_data)} bytes), skipping")
            return None
        
        # Reset buffer and state
        self._audio_chunks = []
        self._total_bytes = 0
        self._consecutive_silence = 0
        self._has_detected_speech = False
        
        self._log(f"Transcribing {len(audio_data)} bytes of audio...")
        
        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        self._write_wav(wav_buffer, audio_data)
        wav_buffer.seek(0)
        
        # Write to temporary file (Whisper API requires a file)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(wav_buffer.getvalue())
        
        try:
            with open(temp_path, "rb") as audio_file:
                transcript = await self.client.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file,
                    language=self.language,
                    response_format="text"
                )
            result = transcript.strip() if transcript else None
            self._log(f"Transcription result: '{result}'")
            return result
        except Exception as e:
            self._log(f"Transcription error: {e}")
            return None
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

    def _write_wav(self, buffer: io.BytesIO, audio_data: bytes):
        """Write a complete WAV file to the buffer."""
        num_channels = 1
        sample_rate = self._sample_rate
        bits_per_sample = 16
        byte_rate = sample_rate * num_channels * bits_per_sample // 8
        block_align = num_channels * bits_per_sample // 8
        data_size = len(audio_data)
        
        # RIFF header
        buffer.write(b'RIFF')
        buffer.write(struct.pack('<I', 36 + data_size))
        buffer.write(b'WAVE')
        
        # fmt chunk
        buffer.write(b'fmt ')
        buffer.write(struct.pack('<I', 16))  # Chunk size
        buffer.write(struct.pack('<H', 1))   # Audio format (PCM)
        buffer.write(struct.pack('<H', num_channels))
        buffer.write(struct.pack('<I', sample_rate))
        buffer.write(struct.pack('<I', byte_rate))
        buffer.write(struct.pack('<H', block_align))
        buffer.write(struct.pack('<H', bits_per_sample))
        
        # data chunk
        buffer.write(b'data')
        buffer.write(struct.pack('<I', data_size))
        buffer.write(audio_data)

    async def flush(self) -> Optional[str]:
        """Force transcription of any remaining audio in the buffer."""
        if self._total_bytes >= self._min_bytes // 4:  # Very low threshold for flush
            self._log(f"Flushing {self._total_bytes} bytes...")
            return await self._transcribe()
        return None

    async def close(self):
        """Close the STT processor."""
        self._closed = True
        self._audio_chunks = []
        self._total_bytes = 0


async def stt_stream(
    audio_stream: AsyncIterator[bytes],
) -> AsyncIterator[VoiceAgentEvent]:
    """
    Transform stream: Audio (Bytes) → Voice Events (VoiceAgentEvent)
    
    Processes incoming audio and yields transcription events.
    """
    stt = OpenAISTT()
    
    try:
        async for audio_chunk in audio_stream:
            transcript = await stt.process_audio(audio_chunk)
            if transcript:
                yield STTOutputEvent.create(transcript)
        
        # Flush any remaining audio
        final_transcript = await stt.flush()
        if final_transcript:
            yield STTOutputEvent.create(final_transcript)
    finally:
        await stt.close()
