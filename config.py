
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

class Config:
    """ Application Configuration"""

    # API KEY
    GROQ_API_KEY:str = os.getenv("GROQ_API_KEY", "")

    # Text LLM Model Settings
    LLM_MODEL: str = "llama-3.1-8b-instant"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: Optional[int] = None

    #Vision LLM Settings
    VISION_MODEL:str = "meta-llama/llama-4-scout-17b-16e-instruct"
    VISION_TEMPERATURE: float= 0.2
    VISION_MAX_TOKENS: int = 1024

    # App Settings
    MAX_PLAN_STEPS: int = 5
    MEMORY_SUMMARY_THRESHOLD: int = 10
    MAX_PLAN_REVISIONS: int = 3

    # Streamlit Settings
    STREAMLIT_THEME: dict = {
        "primaryColor": "#FF4B4B",
        "backgroundColor": "#0E1117",
        "secondaryBackgroundColor": "#262730",
        "textColor": "#FAFAFA",
        "font": "sans serif"
    }

    # --- ADD INDENTATION TO THE METHODS BELOW ---
    @classmethod
    def validate(cls):
        """ Validate Configuration"""
        if not cls.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not found in env variables")
        
    @classmethod
    def get_llm_kwargs(cls):
        """Get LLM initialization arguments"""
        return {
            "model": cls.LLM_MODEL,
            "temperature": cls.LLM_TEMPERATURE,
            "api_key": cls.GROQ_API_KEY,
            "max_tokens": cls.LLM_MAX_TOKENS
        }
    
    @classmethod
    def get_vision_kwargs(cls):
        """Get Vision LLM initializable arguments"""
        return {
            "model": cls.VISION_MODEL,
            "temperature": cls.VISION_TEMPERATURE,
            "max_completion_tokens": cls.VISION_MAX_TOKENS
        }
    
# validate on import
Config.validate()

