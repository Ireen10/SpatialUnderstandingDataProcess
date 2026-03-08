"""
AI service for LLM-powered features
"""

import json
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.core.config import settings


class AIService:
    """Service for AI-powered features using OpenRouter/GLM-5."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        self.base_url = base_url or settings.OPENROUTER_BASE_URL
        self.model = model or settings.OPENROUTER_MODEL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/SUDP",  # Optional for rankings
        }
    
    async def _call_api(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> Optional[str]:
        """Make API call to OpenRouter."""
        if not self.api_key:
            raise ValueError("API key not configured")
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        # Add proxy if configured
        proxy = None
        if settings.HTTPS_PROXY:
            proxy = settings.HTTPS_PROXY
        elif settings.HTTP_PROXY:
            proxy = settings.HTTP_PROXY
        
        async with httpx.AsyncClient(proxy=proxy, timeout=120.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as e:
                print(f"API error: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                print(f"API call failed: {e}")
                raise
    
    async def generate_visualization_code(
        self,
        data_type: str,
        sample_data: Dict[str, Any],
        description: Optional[str] = None,
    ) -> str:
        """
        Generate HTML visualization code for data.
        
        Args:
            data_type: Type of data (image, video, text, image_text, video_text)
            sample_data: Sample data info (fields, structure, etc.)
            description: User's description of desired visualization
        
        Returns:
            HTML code for visualization
        """
        system_prompt = """You are an expert frontend developer specializing in data visualization. 
Generate clean, modern HTML/CSS/JavaScript code for visualizing data.

Rules:
1. Output ONLY valid HTML code (including embedded CSS and JavaScript)
2. Use modern CSS (flexbox, grid) and vanilla JavaScript
3. Make it responsive and visually appealing
4. Use a clean, professional color scheme
5. Include hover effects and smooth transitions
6. No external dependencies except CDN libraries if absolutely needed
7. The code will be embedded in an existing page, so don't include <html>, <head>, <body> tags
8. Wrap everything in a single <div class="visualization-container">

The visualization should display:
- For image-text pairs: show images with their associated text labels
- For video-text pairs: show video thumbnails with text
- For text data: show formatted text with statistics
- Support grid layouts for multiple items"""

        user_message = f"""Generate visualization HTML code for:
Data type: {data_type}
Sample data structure: {json.dumps(sample_data, indent=2, ensure_ascii=False)}
{"User description: " + description if description else ""}

Generate the complete HTML/CSS/JavaScript code."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        
        return await self._call_api(messages, temperature=0.7, max_tokens=8192)
    
    async def generate_conversion_script(
        self,
        source_format: str,
        target_format: str,
        sample_data: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
    ) -> str:
        """
        Generate Python script for data format conversion.
        
        Args:
            source_format: Current format description
            target_format: Desired format description
            sample_data: Sample of source data
            description: Additional instructions
        
        Returns:
            Python script code
        """
        system_prompt = """You are an expert Python developer specializing in data processing and format conversion.
Generate clean, efficient Python code for converting data between formats.

Rules:
1. Output ONLY valid Python code
2. Use standard libraries when possible (json, csv, os, pathlib, etc.)
3. Add proper error handling with try-except
4. Include type hints
5. Add docstrings for functions
6. Make the code production-ready
7. Handle edge cases gracefully
8. The script should be executable as a standalone module
9. Include a main() function with argument parsing if needed"""

        user_message = f"""Generate Python conversion script:

Source format: {source_format}
Target format: {target_format}
{f"Sample data: {json.dumps(sample_data, indent=2, ensure_ascii=False)}" if sample_data else ""}
{f"Additional instructions: {description}" if description else ""}

Generate the complete Python script."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        
        return await self._call_api(messages, temperature=0.3, max_tokens=4096)
    
    async def analyze_data_quality(
        self,
        data_info: Dict[str, Any],
        issues: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze data quality and suggest fixes.
        
        Args:
            data_info: Information about the data
            issues: Known issues to address
        
        Returns:
            Analysis results with suggestions
        """
        system_prompt = """You are a data quality expert for machine learning datasets.
Analyze data and provide actionable suggestions for quality improvement.

Respond in JSON format with:
{
    "quality_score": <0-100>,
    "issues": ["issue1", "issue2", ...],
    "suggestions": ["suggestion1", "suggestion2", ...],
    "priority_fixes": [{"issue": "...", "fix": "..."}]
}"""

        user_message = f"""Analyze this dataset:
{json.dumps(data_info, indent=2, ensure_ascii=False)}

{f"Known issues: {json.dumps(issues)}" if issues else ""}

Provide quality analysis and recommendations."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        
        response = await self._call_api(messages, temperature=0.5, max_tokens=2048)
        
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                return json.loads(response[json_start:json_end])
        except json.JSONDecodeError:
            pass
        
        return {
            "quality_score": None,
            "analysis": response,
            "error": "Failed to parse structured response"
        }
    
    async def chat(
        self,
        message: str,
        context: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        General chat completion.
        
        Args:
            message: User message
            context: Additional context
            system_prompt: Custom system prompt
        
        Returns:
            AI response
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        else:
            messages.append({"role": "system", "content": "You are a helpful AI assistant."})
        
        if context:
            messages.append({"role": "user", "content": f"Context:\n{context}\n\nQuestion: {message}"})
        else:
            messages.append({"role": "user", "content": message})
        
        return await self._call_api(messages)


def get_ai_service(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
) -> AIService:
    """Factory function to create AI service with custom config."""
    return AIService(api_key=api_key, base_url=base_url, model=model)


# Default instance
ai_service = AIService()
