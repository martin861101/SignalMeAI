import os
import requests
import json
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class LLMManager:
    """
    LLM Manager with fallback to Ollama local instance.
    Uses Ollama primarily, with API key support for future expansion.
    """

    def __init__(self):
        self.ollama_available = self._check_ollama()
        self.api_keys = {
            "gemini": os.getenv("GEMINI_API_KEY"),
            "mistral": os.getenv("MISTRAL_API_KEY"),
            "moonshot": os.getenv("MOONSHOT_API_KEY"),
        }

    def _check_ollama(self) -> bool:
        """Check if Ollama is running locally."""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    def generate_response(self, prompt: str, model_name: str = "mistral:latest") -> str:
        """
        Generate response using Ollama.
        """
        if not self.ollama_available:
            raise RuntimeError("Ollama is not available. Please start Ollama locally.")

        try:
            return self._ollama_generate(prompt, model_name)
        except Exception as e:
            raise RuntimeError(f"LLM generation failed: {e}")

    def _ollama_generate(self, prompt: str, model_name: str = "llama3.2") -> str:
        """Generate response using Ollama API."""
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": model_name, "prompt": prompt, "stream": False},
                timeout=60,
            )
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                raise Exception(f"Ollama API returned {response.status_code}")
        except Exception as e:
            raise Exception(f"Ollama generation failed: {e}")


# Global instance
llm_manager = LLMManager()


def get_llm_manager() -> LLMManager:
    """Get the global LLM manager instance."""
    return llm_manager


def generate_llm_response(prompt: str, model_name: str = "llama3.2") -> str:
    """Convenience function to generate LLM response."""
    return llm_manager.generate_response(prompt, model_name)
