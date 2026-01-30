"""
LLM Client for Google Gemini
Provides a simple interface for calling the Gemini API.
"""

import os
import google.generativeai as genai
from typing import Optional


class LLMClient:
    """
    Wrapper for Google Gemini API.
    Handles API key configuration and model interactions.
    """
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the LLM client.
        
        Args:
            model_name: Model to use (defaults to environment variable or gemini-2.5-flash-exp)
        """
        # Get API key
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Set model (use gemini-2.5-flash - confirmed working)
        self.model_name = model_name or "gemini-2.5-flash"
        self.model = genai.GenerativeModel(self.model_name)
        
        print(f"[LLM] LLM Client initialized: {self.model_name}")
    
    def call(self, prompt: str, temperature: float = 0.1) -> str:
        """
        Call the LLM with a prompt.
        
        Args:
            prompt: The prompt to send
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
        
        Returns:
            The LLM's response as a string
        
        Raises:
            Exception: If the API call fails
        """
        try:
            # Configure generation
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=8000,
            )
            
            # Generate response
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            # Extract text
            if not response.text:
                raise ValueError("Empty response from LLM")
            
            return response.text
        
        except Exception as e:
            print(f"[LLM] LLM API Error: {e}")
            raise
    
    def call_with_json(self, prompt: str) -> str:
        """
        Call the LLM with a prompt that expects JSON output.
        Uses lower temperature for more consistent JSON.
        
        Args:
            prompt: The prompt (should specify JSON output format)
        
        Returns:
            The LLM's response
        """
        # Add JSON instruction if not present
        if "json" not in prompt.lower():
            prompt += "\n\nIMPORTANT: Return ONLY valid JSON. No explanations or markdown."
        
        return self.call(prompt, temperature=0.0)