"""
LLM Client for Google Gemini API
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LLMClient:
    """Simple LLM client for Gemini."""
    
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        # Get API key from .env
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in .env file")
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Create the model
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": 0.1,
                "max_output_tokens": 8192,
            }
        )
        
        print(f"LLM Client ready: {model_name}")
    
    def call(self, prompt: str) -> str:
        """Make a simple call to Gemini."""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"LLM Error: {e}")
            return f"Error: {str(e)}"