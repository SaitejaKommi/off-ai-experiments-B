"""LLM Configuration and Setup."""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class LLMConfig:
    """Configuration for LLM providers."""
    
    # Gemini API
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-2.0-flash")
    
    # Groq API (future support)
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    # Provider selection
    PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
    
    # Feature flags
    USE_LLM_PAIRINGS = os.getenv("USE_LLM_PAIRINGS", "true").lower() == "true"
    LLM_FALLBACK_TO_RULES = os.getenv("LLM_FALLBACK_TO_RULES", "false").lower() == "true"
    
    # Request timeouts
    REQUEST_TIMEOUT = 30  # seconds
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that required API keys are configured.
        
        Returns
        -------
        bool
            True if configuration is valid, False otherwise.
        """
        if cls.PROVIDER == "gemini":
            if not cls.GEMINI_API_KEY:
                print("Error: GEMINI_API_KEY not set in .env file")
                print("Please set your API key: https://aistudio.google.com/app/apikey")
                return False
        elif cls.PROVIDER == "groq":
            if not cls.GROQ_API_KEY:
                print("Error: GROQ_API_KEY not set in .env file")
                print("Please set your API key: https://console.groq.com/keys")
                return False
        else:
            print(f"Error: Unknown LLM_PROVIDER: {cls.PROVIDER}")
            return False
        
        return True
    
    @classmethod
    def get_status(cls) -> str:
        """Get a status string about LLM configuration.
        
        Returns
        -------
        str
            Status message.
        """
        if not cls.USE_LLM_PAIRINGS:
            return "LLM pairings disabled (USE_LLM_PAIRINGS=false)"
        
        if cls.PROVIDER == "gemini":
            status = f"✓ Gemini API configured ({cls.GEMINI_MODEL})"
        elif cls.PROVIDER == "groq":
            status = f"✓ Groq API configured ({cls.GROQ_MODEL})"
        else:
            status = f"✗ Unknown provider: {cls.PROVIDER}"
        
        fallback = " + rule-based fallback" if cls.LLM_FALLBACK_TO_RULES else ""
        return status + fallback
