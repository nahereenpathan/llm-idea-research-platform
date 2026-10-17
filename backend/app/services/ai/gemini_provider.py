import json
import re
import httpx
from typing import Dict, Any, Optional
from app.services.ai.provider_base import LLMProvider


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        url = f"{self.base_url}?key={self.api_key}"
        full_text = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        payload = {
            "contents": [{"parts": [{"text": full_text}]}],
            "generationConfig": {"temperature": 0.3}
        }
        with httpx.Client(timeout=45.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    def generate_structured(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.base_url}?key={self.api_key}"
        full_text = (
            f"{system_prompt or ''}\n\n{prompt}\n\n"
            "Respond ONLY with a valid raw JSON object. Do not include markdown codeblocks or any additional commentary."
        )
        payload = {
            "contents": [{"parts": [{"text": full_text}]}],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json"
            }
        }
        with httpx.Client(timeout=45.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            # Clean possible markdown ticks if any
            clean_text = re.sub(r"^```json\s*", "", text.strip())
            clean_text = re.sub(r"```$", "", clean_text).strip()
            return json.loads(clean_text)
