from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class LLMProvider(ABC):
    @abstractmethod
    def extract_json(self, prompt: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extract structured JSON data from a prompt."""
        pass

    @abstractmethod
    def generate_text(self, prompt: str) -> str:
        """Generate plain text from a prompt."""
        pass

    @abstractmethod
    def summarize(self, text: str) -> str:
        """Generate a summary of the provided text."""
        pass
