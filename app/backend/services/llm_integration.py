# services/llm_service.py

import os
import time

import ollama
from dotenv import load_dotenv
from google import genai
from huggingface_hub import InferenceClient


load_dotenv()


# ============================================================
# Configuration
# ============================================================

OLLAMA_MODEL = "llama3.1"

GEMINI_MODEL = "gemini-3.6-flash"

HUGGINGFACE_MODEL = "deepseek-ai/DeepSeek-V3-0324"

DEFAULT_PROVIDER = "ollama"

QUESTION_TEMPERATURE = 0.5
EVALUATION_TEMPERATURE = 0.0


# ============================================================
# API Keys
# ============================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")


# ============================================================
# Clients
# ============================================================

gemini_client = None

if GEMINI_API_KEY:
    gemini_client = genai.Client(
        api_key=GEMINI_API_KEY
    )


huggingface_client = None

if HF_TOKEN:
    huggingface_client = InferenceClient(
        api_key=HF_TOKEN,
        provider="auto",
    )


# ============================================================
# Ollama
# ============================================================

def generate_with_ollama(
    prompt: str,
    system_prompt: str = "",
    temperature: float = QUESTION_TEMPERATURE,
) -> str:

    messages = []

    if system_prompt:
        messages.append(
            {
                "role": "system",
                "content": system_prompt,
            }
        )

    messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=messages,
            options={
                "temperature": temperature,
            },
        )

        content = response["message"]["content"]

        if not content or not content.strip():
            raise RuntimeError(
                "Ollama returned an empty response."
            )

        return content.strip()

    except Exception as exc:
        raise RuntimeError(
            f"Ollama generation failed: {exc}"
        ) from exc


# ============================================================
# Gemini
# ============================================================

def generate_with_gemini(
    prompt: str,
    system_prompt: str = "",
    temperature: float = QUESTION_TEMPERATURE,
    max_retries: int = 3,
) -> str:

    if gemini_client is None:
        raise RuntimeError(
            "GEMINI_API_KEY was not found."
        )

    full_prompt = prompt

    if system_prompt:
        full_prompt = (
            f"{system_prompt}\n\n"
            f"{prompt}"
        )

    for attempt in range(max_retries):

        try:
            response = gemini_client.models.generate_content(
                model=GEMINI_MODEL,
                contents=full_prompt,
                config={
                    "temperature": temperature,
                },
            )

            if not response.text:
                raise RuntimeError(
                    "Gemini returned an empty response."
                )

            return response.text.strip()

        except Exception as exc:

            error_text = str(exc)

            temporary_error = (
                "503" in error_text
                or "UNAVAILABLE" in error_text
                or "high demand" in error_text.lower()
            )

            if temporary_error and attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue

            raise RuntimeError(
                f"Gemini generation failed: {exc}"
            ) from exc

    raise RuntimeError(
        "Gemini generation failed after multiple retries."
    )


# ============================================================
# Hugging Face
# ============================================================

def generate_with_huggingface(
    prompt: str,
    system_prompt: str = "",
    temperature: float = QUESTION_TEMPERATURE,
) -> str:

    if huggingface_client is None:
        raise RuntimeError(
            "HF_TOKEN was not found."
        )

    messages = []

    if system_prompt:
        messages.append(
            {
                "role": "system",
                "content": system_prompt,
            }
        )

    messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    try:
        response = huggingface_client.chat.completions.create(
            model=HUGGINGFACE_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=500,
        )

        content = response.choices[0].message.content

        if not content or not content.strip():
            raise RuntimeError(
                "Hugging Face returned an empty response."
            )

        return content.strip()

    except Exception as exc:
        raise RuntimeError(
            f"Hugging Face generation failed: {exc}"
        ) from exc


# ============================================================
# Unified Provider Function
# ============================================================

def generate_text(
    prompt: str,
    provider: str = DEFAULT_PROVIDER,
    system_prompt: str = "",
    temperature: float = QUESTION_TEMPERATURE,
) -> str:

    if not prompt or not prompt.strip():
        raise ValueError(
            "Prompt cannot be empty."
        )

    provider = provider.lower().strip()

    if provider == "ollama":

        return generate_with_ollama(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
        )

    elif provider in {"google", "gemini"}:

        return generate_with_gemini(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
        )

    elif provider in {
        "huggingface",
        "hugging_face",
        "hf",
    }:

        return generate_with_huggingface(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
        )

    else:

        raise ValueError(
            f"Unsupported LLM provider: {provider}"
        )