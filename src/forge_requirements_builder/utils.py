"""Utility functions for Forge Requirements Builder

Provides shared utilities for content detection, conversation management, 
logging, and error handling.
"""

import logging
import time
from typing import List, Dict, Callable, Any, Optional
from functools import wraps
import re


# ============================================================================
# Content Type Detection
# ============================================================================

def detect_content_type(content: str) -> str:
    """Detect the type of content provided by user for smart phase detection.
    
    Args:
        content: User-provided text content
        
    Returns:
        Content type: "user_stories" | "requirements" | "prioritized" | "raw_ideas"
    """
    content_lower = content.lower()
    
    # Check for user story patterns
    user_story_patterns = [
        r"as\s+a\s+\w+.*i\s+want.*so\s+that",
        r"acceptance\s+criteria",
        r"given.*when.*then",
        r"definition\s+of\s+done",
        r"story[-\s]?\d+"
    ]
    
    user_story_matches = sum(
        1 for pattern in user_story_patterns 
        if re.search(pattern, content_lower, re.IGNORECASE)
    )
    
    if user_story_matches >= 2:
        return "user_stories"
    
    # Check for requirements patterns
    requirements_patterns = [
        r"req[-\s]?\d+",
        r"requirement[s]?:",
        r"the\s+system\s+(shall|must|should)",
        r"functional\s+requirement",
        r"non[-\s]?functional\s+requirement"
    ]
    
    requirements_matches = sum(
        1 for pattern in requirements_patterns 
        if re.search(pattern, content_lower, re.IGNORECASE)
    )
    
    if requirements_matches >= 2:
        return "requirements"
    
    # Check for prioritized content
    prioritized_patterns = [
        r"priority\s*[:=]\s*(high|medium|low|must|should|could)",
        r"phase\s+\d+",
        r"must\s+have.*should\s+have",
        r"rice\s+score",
        r"moscow",
        r"rank\s*[:=]?\s*\d+"
    ]
    
    prioritized_matches = sum(
        1 for pattern in prioritized_patterns 
        if re.search(pattern, content_lower, re.IGNORECASE)
    )
    
    if prioritized_matches >= 1:
        return "prioritized"
    
    # Default to raw ideas
    return "raw_ideas"


# ============================================================================
# Conversation History Management
# ============================================================================

class ConversationHistoryManager:
    """Manages conversation history for state management."""
    
    @staticmethod
    def add_message(
        history: List[dict],
        role: str,
        content: str,
        agent: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> List[dict]:
        """Add a message to conversation history.
        
        Args:
            history: Current conversation history
            role: Message role ("user" | "assistant" | "system")
            content: Message content
            agent: Optional agent name if from specialized agent
            metadata: Optional additional metadata
            
        Returns:
            Updated conversation history
        """
        import time
        
        message = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
        }
        
        if agent:
            message["agent"] = agent
        
        if metadata:
            message["metadata"] = metadata
        
        history.append(message)
        return history
    
    @staticmethod
    def get_context(
        history: List[dict],
        last_n: Optional[int] = None,
        role_filter: Optional[str] = None
    ) -> List[dict]:
        """Retrieve conversation context with optional filters.
        
        Args:
            history: Current conversation history
            last_n: Optional limit to last N messages
            role_filter: Optional filter by role
            
        Returns:
            Filtered conversation messages
        """
        messages = history
        
        if role_filter:
            messages = [msg for msg in messages if msg.get("role") == role_filter]
        
        if last_n:
            messages = messages[-last_n:]
        
        return messages
    
    @staticmethod
    def format_for_prompt(
        history: List[dict],
        last_n: int = 10
    ) -> str:
        """Format conversation history for inclusion in prompts.
        
        Args:
            history: Current conversation history
            last_n: Number of recent messages to include
            
        Returns:
            Formatted conversation string
        """
        recent = history[-last_n:] if len(history) > last_n else history
        
        formatted = []
        for msg in recent:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            agent = msg.get("agent", "")
            
            if agent:
                formatted.append(f"[{role.upper()} - {agent}]: {content}")
            else:
                formatted.append(f"[{role.upper()}]: {content}")
        
        return "\n".join(formatted)


# ============================================================================
# Logging Configuration
# ============================================================================

def setup_logging(
    log_level: str = "INFO",
    project_id: Optional[str] = None
) -> logging.Logger:
    """Configure structured logging with project context.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        project_id: Optional project ID for context
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("forge_requirements_builder")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Create console handler with formatting
    handler = logging.StreamHandler()
    handler.setLevel(getattr(logging, log_level.upper()))
    
    # Format: timestamp [LEVEL] [project_id] message
    if project_id:
        formatter = logging.Formatter(
            f'%(asctime)s [%(levelname)s] [{project_id}] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


class ProjectLogger:
    """Context-aware logger that includes project_id in all messages."""
    
    def __init__(self, project_id: str, log_level: str = "INFO"):
        self.project_id = project_id
        self.logger = setup_logging(log_level, project_id)
    
    def debug(self, message: str, **kwargs):
        self.logger.debug(message, extra={"project_id": self.project_id, **kwargs})
    
    def info(self, message: str, **kwargs):
        self.logger.info(message, extra={"project_id": self.project_id, **kwargs})
    
    def warning(self, message: str, **kwargs):
        self.logger.warning(message, extra={"project_id": self.project_id, **kwargs})
    
    def error(self, message: str, **kwargs):
        self.logger.error(message, extra={"project_id": self.project_id, **kwargs})


# ============================================================================
# Error Handling Utilities
# ============================================================================

def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger = logging.getLogger("forge_requirements_builder")
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            f"All {max_retries} retries failed for {func.__name__}: {e}"
                        )
            
            # If we get here, all retries failed
            raise last_exception
        
        return wrapper
    return decorator


class FallbackHandler:
    """Provides fallback strategies when operations fail."""
    
    @staticmethod
    def with_fallback(
        primary_func: Callable,
        fallback_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute primary function with fallback on failure.
        
        Args:
            primary_func: Primary function to attempt
            fallback_func: Fallback function if primary fails
            *args: Positional arguments for functions
            **kwargs: Keyword arguments for functions
            
        Returns:
            Result from primary or fallback function
        """
        logger = logging.getLogger("forge_requirements_builder")
        
        try:
            return primary_func(*args, **kwargs)
        except Exception as e:
            logger.warning(
                f"Primary function {primary_func.__name__} failed: {e}. "
                f"Attempting fallback {fallback_func.__name__}..."
            )
            try:
                return fallback_func(*args, **kwargs)
            except Exception as fallback_error:
                logger.error(
                    f"Fallback function {fallback_func.__name__} also failed: {fallback_error}"
                )
                raise


# ============================================================================
# Text Processing Utilities
# ============================================================================

def truncate_for_context(
    text: str,
    max_tokens: int = 4000,
    chars_per_token: float = 4.0
) -> str:
    """Truncate text to fit within token limit for LLM context.
    
    Args:
        text: Text to truncate
        max_tokens: Maximum number of tokens
        chars_per_token: Approximate characters per token
        
    Returns:
        Truncated text with indicator if truncated
    """
    max_chars = int(max_tokens * chars_per_token)
    
    if len(text) <= max_chars:
        return text
    
    truncated = text[:max_chars]
    return truncated + "\n\n[... content truncated for length ...]"


def extract_requirements_count(text: str) -> int:
    """Extract count of requirements from text for metrics.
    
    Args:
        text: Text potentially containing requirements
        
    Returns:
        Number of requirements detected
    """
    # Look for REQ-XXX pattern
    req_pattern = r'REQ[-\s]?\d+'
    matches = re.findall(req_pattern, text, re.IGNORECASE)
    return len(set(matches))  # Unique requirement IDs
