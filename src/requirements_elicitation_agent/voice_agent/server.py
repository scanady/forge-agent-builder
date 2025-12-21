"""
Voice Agent WebSocket Server

FastAPI server that handles WebSocket connections for real-time
voice interaction with the requirements elicitation agent.
"""

import asyncio
import json
from pathlib import Path
from typing import AsyncIterator
from uuid import uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.websockets import WebSocketState

from .events import event_to_dict, VoiceAgentEvent, TTSChunkEvent, AgentEndEvent, STTOutputEvent
from .stt import OpenAISTT
from .tts import OpenAITTS
from .agent_stream import agent_stream


def create_voice_app(graph, static_dir: Path | None = None) -> FastAPI:
    """
    Create a FastAPI application for the voice agent.
    
    Args:
        graph: The LangGraph agent instance
        static_dir: Optional path to static files directory for web frontend
    
    Returns:
        FastAPI application configured for voice agent
    """
    app = FastAPI(
        title="Forge Requirements Assistant - Voice Interface",
        description="Voice-enabled requirements elicitation agent",
        version="1.0.0",
    )

    # CORS middleware for browser access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "voice-agent"}

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """
        WebSocket endpoint for voice communication.
        
        Protocol:
        - Client sends: Binary audio data (16kHz, 16-bit, mono PCM) OR JSON messages
        - Server sends: JSON events (stt_chunk, stt_output, agent_chunk, agent_end, tts_chunk, tts_end)
        
        Client JSON messages:
        - {"type": "playback_complete"} - Signals that TTS audio playback has finished
        """
        await websocket.accept()
        
        # Generate unique thread ID for this session
        thread_id = str(uuid4())
        print(f"[WS] New connection (thread_id={thread_id})")
        
        # Shared state
        stt = OpenAISTT()
        tts = OpenAITTS()
        
        # State machine: LISTENING -> PROCESSING -> SPEAKING -> wait for playback_complete -> LISTENING
        state = "LISTENING"
        playback_complete_event = asyncio.Event()
        
        async def process_messages():
            """Main loop: handle incoming messages (audio or control)."""
            nonlocal state
            
            try:
                while True:
                    # Receive message (could be binary audio or text JSON)
                    try:
                        message = await websocket.receive()
                    except WebSocketDisconnect:
                        print(f"[WS] Client disconnected")
                        break
                    
                    if message["type"] == "websocket.disconnect":
                        print(f"[WS] Client disconnected")
                        break
                    
                    # Handle text messages (control messages from client)
                    if message["type"] == "websocket.receive" and "text" in message:
                        try:
                            data = json.loads(message["text"])
                            if data.get("type") == "playback_complete":
                                print(f"[WS] Client finished playback")
                                playback_complete_event.set()
                        except json.JSONDecodeError:
                            print(f"[WS] Invalid JSON from client")
                        continue
                    
                    # Handle binary messages (audio data)
                    if message["type"] == "websocket.receive" and "bytes" in message:
                        audio_data = message["bytes"]
                        
                        # Only process audio when LISTENING
                        if state != "LISTENING":
                            continue
                        
                        # Process audio through STT
                        transcript = await stt.process_audio(audio_data)
                        
                        if transcript and transcript.strip():
                            # Filter out empty/noise transcriptions
                            if transcript in [".", "..", "...", " ", ""]:
                                print(f"[WS] Ignoring noise transcript: '{transcript}'")
                                continue
                                
                            print(f"[WS] Got transcript: '{transcript}'")
                            
                            # Transition to PROCESSING state
                            state = "PROCESSING"
                            stt.pause()  # Clear audio buffer
                            
                            # Send transcript event
                            await websocket.send_json(event_to_dict(STTOutputEvent.create(transcript)))
                            
                            # Process through agent and send TTS (non-blocking)
                            asyncio.create_task(process_and_respond(transcript))
                            
            except Exception as e:
                print(f"[WS] Message handling error: {e}")
            finally:
                await stt.close()
                await tts.close()
        
        async def process_and_respond(transcript: str):
            """Process transcript through agent and send TTS response."""
            nonlocal state
            
            try:
                from langchain_core.messages import HumanMessage, AIMessage
                
                config = {"configurable": {"thread_id": thread_id}}
                input_state = {"messages": [HumanMessage(content=transcript)]}
                
                full_response = ""
                try:
                    async for graph_event in graph.astream(input_state, config, stream_mode="values"):
                        if "messages" in graph_event and graph_event["messages"]:
                            last_msg = graph_event["messages"][-1]
                            if isinstance(last_msg, AIMessage) and last_msg.content:
                                content = last_msg.content
                                if isinstance(content, str) and content != full_response:
                                    from .events import AgentChunkEvent
                                    new_content = content[len(full_response):]
                                    if new_content:
                                        await websocket.send_json(event_to_dict(AgentChunkEvent.create(new_content)))
                                    full_response = content
                    
                    # Send agent end event
                    await websocket.send_json(event_to_dict(AgentEndEvent.create()))
                    
                    # Transition to SPEAKING state
                    state = "SPEAKING"
                    
                    # Synthesize and send TTS
                    if full_response:
                        print(f"[WS] Synthesizing: '{full_response[:50]}...'")
                        async for audio_chunk in tts.synthesize_streaming(full_response):
                            await websocket.send_json(event_to_dict(TTSChunkEvent.create(audio_chunk)))
                    
                    # Send TTS end marker so client knows all audio has been sent
                    await websocket.send_json({"type": "tts_end"})
                    print(f"[WS] TTS complete, waiting for client playback...")
                    
                    # Wait for client to signal playback is complete
                    playback_complete_event.clear()
                    try:
                        await asyncio.wait_for(playback_complete_event.wait(), timeout=60.0)
                        print(f"[WS] Playback confirmed complete")
                    except asyncio.TimeoutError:
                        print(f"[WS] Playback timeout, resuming anyway")
                    
                except Exception as e:
                    print(f"[WS] Agent/TTS error: {e}")
                
                # Transition back to LISTENING
                await asyncio.sleep(0.3)  # Small buffer after playback
                stt.resume()
                state = "LISTENING"
                print(f"[WS] Ready for next input (state=LISTENING)")
                
            except Exception as e:
                print(f"[WS] Process error: {e}")
                state = "LISTENING"
                stt.resume()
        
        await process_messages()

    # Serve static files if directory provided
    if static_dir and static_dir.exists():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    return app


def run_voice_server(graph, host: str = "0.0.0.0", port: int = 8000):
    """
    Run the voice agent server.
    
    Args:
        graph: The LangGraph agent instance
        host: Host to bind to
        port: Port to listen on
    """
    import uvicorn
    
    app = create_voice_app(graph)
    uvicorn.run(app, host=host, port=port)
