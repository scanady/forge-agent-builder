"""
Agent Stream Processor

Processes transcripts through the LangChain requirements elicitation agent
and streams response tokens.
"""

import asyncio
from typing import AsyncIterator
from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage

from .events import AgentChunkEvent, AgentEndEvent, STTOutputEvent, VoiceAgentEvent


async def agent_stream(
    event_stream: AsyncIterator[VoiceAgentEvent],
    graph,
    thread_id: str | None = None,
) -> AsyncIterator[VoiceAgentEvent]:
    """
    Transform stream: Voice Events → Voice Events (with Agent Responses)
    
    Passes through all upstream events and adds agent_chunk events
    when processing STT transcripts.
    
    Args:
        event_stream: Async iterator of voice agent events
        graph: The LangGraph agent instance
        thread_id: Optional thread ID for conversation memory (generates one if not provided)
    
    Yields:
        All upstream events plus agent response events
    """
    # Generate unique thread ID for conversation memory
    if thread_id is None:
        thread_id = str(uuid4())
    
    async for event in event_stream:
        # Pass through all upstream events
        yield event
        
        # Process final transcripts through the agent
        if isinstance(event, STTOutputEvent):
            transcript = event.transcript
            
            if not transcript.strip():
                continue
            
            config = {"configurable": {"thread_id": thread_id}}
            state = {"messages": [HumanMessage(content=transcript)]}
            
            try:
                # Stream agent response
                async for graph_event in graph.astream(state, config, stream_mode="messages"):
                    # graph_event is a tuple of (message, metadata) when using stream_mode="messages"
                    if isinstance(graph_event, tuple) and len(graph_event) >= 1:
                        message = graph_event[0]
                        if isinstance(message, AIMessage) and message.content:
                            # Stream each content chunk
                            content = message.content
                            if isinstance(content, str):
                                yield AgentChunkEvent.create(content)
                            elif isinstance(content, list):
                                for block in content:
                                    if isinstance(block, str):
                                        yield AgentChunkEvent.create(block)
                                    elif hasattr(block, 'text'):
                                        yield AgentChunkEvent.create(block.text)
                
                # Signal end of agent turn
                yield AgentEndEvent.create()
                
            except Exception as e:
                print(f"[Agent] Error processing transcript: {e}")
                # Send error message as agent response
                yield AgentChunkEvent.create(f"I encountered an error: {str(e)}")
                yield AgentEndEvent.create()


def create_agent_stream_factory(graph):
    """
    Create an agent stream function bound to a specific graph.
    
    This is useful for creating a pipeline where the graph is pre-configured.
    """
    async def bound_agent_stream(
        event_stream: AsyncIterator[VoiceAgentEvent],
        thread_id: str | None = None,
    ) -> AsyncIterator[VoiceAgentEvent]:
        async for event in agent_stream(event_stream, graph, thread_id):
            yield event
    
    return bound_agent_stream
