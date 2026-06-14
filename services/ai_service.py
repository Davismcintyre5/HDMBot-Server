"""
server/services/ai_service.py — AI provider integrations (DeepSeek, Gemini, ChatGPT)
"""
import logging
import requests
from typing import Optional
from config.settings import settings

logger = logging.getLogger(__name__)


class AIService:
    """Service for querying AI models."""

    @staticmethod
    def query_deepseek(prompt: str) -> str:
        """Query DeepSeek AI."""
        if not settings.DEEPSEEK_API_KEY:
            return "❌ DeepSeek API key not configured."

        try:
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000,
                },
                timeout=30,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except requests.RequestException as e:
            logger.error(f"DeepSeek error: {e}")
            return f"❌ DeepSeek error: {e}"
        except (KeyError, IndexError) as e:
            logger.error(f"DeepSeek parse error: {e}")
            return "❌ Failed to parse DeepSeek response."

    @staticmethod
    def query_gemini(prompt: str) -> str:
        """Query Google Gemini AI."""
        if not settings.GEMINI_API_KEY:
            return "❌ Gemini API key not configured."

        try:
            response = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={settings.GEMINI_API_KEY}",
                headers={"Content-Type": "application/json"},
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=30,
            )
            response.raise_for_status()
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        except requests.RequestException as e:
            logger.error(f"Gemini error: {e}")
            return f"❌ Gemini error: {e}"
        except (KeyError, IndexError) as e:
            logger.error(f"Gemini parse error: {e}")
            return "❌ Failed to parse Gemini response."

    @staticmethod
    def query_chatgpt(prompt: str) -> str:
        """Query OpenAI ChatGPT."""
        if not settings.OPENAI_API_KEY:
            return "❌ ChatGPT API key not configured."

        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000,
                },
                timeout=30,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except requests.RequestException as e:
            logger.error(f"ChatGPT error: {e}")
            return f"❌ ChatGPT error: {e}"
        except (KeyError, IndexError) as e:
            logger.error(f"ChatGPT parse error: {e}")
            return "❌ Failed to parse ChatGPT response."

    @staticmethod
    def query(prompt: str, model: Optional[str] = None) -> str:
        """Query the default or specified AI model."""
        model = model or settings.DEFAULT_AI_MODEL

        if model == "gemini":
            return AIService.query_gemini(prompt)
        elif model == "chatgpt":
            return AIService.query_chatgpt(prompt)
        else:
            return AIService.query_deepseek(prompt)


# Singleton
ai_service = AIService()