"""
Persona loader for externalizing agent configuration.

Loads persona configuration, prompts, and other persona-related content
from external files for easier management and updates.
"""

import os
from pathlib import Path
from typing import Dict, Optional
import yaml


class PersonaLoader:
    """Loads persona configuration and prompts from external files."""
    
    def __init__(self, persona_dir: Optional[str] = None):
        """Initialize the loader with a persona directory path.
        
        Args:
            persona_dir: Path to persona directory. Defaults to ./persona in the same directory as this module.
        """
        if persona_dir is None:
            persona_dir = Path(__file__).parent / "persona"
        self.persona_dir = Path(persona_dir)
        self._config = None
        self._cache = {}
    
    @property
    def config(self) -> dict:
        """Load and cache the persona configuration."""
        if self._config is None:
            config_path = self.persona_dir / "config.yaml"
            with open(config_path, 'r') as f:
                self._config = yaml.safe_load(f)
        return self._config
    
    def load_greeting(self) -> str:
        """Load the greeting message."""
        return self._load_text_file("greeting.md")
    
    def load_interviewer_prompt(self) -> str:
        """Load the interviewer system prompt template."""
        return self._load_text_file("interviewer_prompt.md")
    
    def load_recorder_prompt(self) -> str:
        """Load the requirement recorder system prompt template."""
        return self._load_text_file("recorder_prompt.md")
    
    def load_gap_analyzer_prompt(self) -> str:
        """Load the gap analyzer system prompt template."""
        return self._load_text_file("gap_analyzer_prompt.md")
    
    def load_doc_extractor_prompt(self) -> str:
        """Load the document extractor system prompt template."""
        return self._load_text_file("doc_extractor_prompt.md")
    
    def _load_text_file(self, filename: str) -> str:
        """Load a text file from the persona directory.
        
        Args:
            filename: Name of the file to load (relative to persona directory)
            
        Returns:
            File contents as string
        """
        if filename in self._cache:
            return self._cache[filename]
        
        file_path = self.persona_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Persona file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self._cache[filename] = content
        return content
    
    def get_persona_name(self) -> str:
        """Get the persona name."""
        return self.config.get('persona', {}).get('name', 'Unknown')
    
    def get_persona_full_name(self) -> str:
        """Get the persona's full name."""
        return self.config.get('persona', {}).get('full_name', 'Unknown')
    
    def get_persona_title(self) -> str:
        """Get the persona's title."""
        return self.config.get('persona', {}).get('title', 'Unknown')


# Global loader instance
_loader: Optional[PersonaLoader] = None


def get_persona_loader() -> PersonaLoader:
    """Get the global PersonaLoader instance, creating it if necessary."""
    global _loader
    if _loader is None:
        _loader = PersonaLoader()
    return _loader


def load_greeting() -> str:
    """Load the greeting message."""
    return get_persona_loader().load_greeting()


def load_interviewer_prompt() -> str:
    """Load the interviewer system prompt template."""
    return get_persona_loader().load_interviewer_prompt()


def load_recorder_prompt() -> str:
    """Load the requirement recorder system prompt template."""
    return get_persona_loader().load_recorder_prompt()


def load_gap_analyzer_prompt() -> str:
    """Load the gap analyzer system prompt template."""
    return get_persona_loader().load_gap_analyzer_prompt()


def load_doc_extractor_prompt() -> str:
    """Load the document extractor system prompt template."""
    return get_persona_loader().load_doc_extractor_prompt()
