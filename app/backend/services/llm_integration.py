import os

import ollama
from google import genai
from dotenv import load_dotenv


load_dotenv()

# configuration

OLLAMA_MODEL = "llama3.1"

GEMINI_MODEL = "gemini-3.6-flash"

DEFAULT_PROVIDER = "ollama"

# google gemini client

gemini_api_key = os.getenv("GEMINI_API_KEY")

gemini_client = None

if gemini_api_key:
    gemini_client = genai.Client(
        api_key=gemini_api_key
    )
# ollama

def generate_with_ollama(
    prompt: str,
    system_prompt: str = "",
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
                "temperature": 0.5,
            },
        )

        return response["message"]["content"]

    except Exception as exc:
        raise RuntimeError(
            f"Ollama generation failed: {exc}"
        ) from exc

# goole gemini

def generate_with_gemini(
    prompt: str,
    system_prompt: str = "",
) -> str:

    if gemini_client is None:
        raise RuntimeError(
            "GEMINI_API_KEY was not found."
        )

    try:

        full_prompt = prompt

        if system_prompt:
            full_prompt = (
                f"{system_prompt}\n\n"
                f"{prompt}"
            )

        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=full_prompt,
        )

        return response.text

    except Exception as exc:
        raise RuntimeError(
            f"Gemini generation failed: {exc}"
        ) from exc

# llm function

def generate_text(
    prompt: str,
    provider: str = DEFAULT_PROVIDER,
    system_prompt: str = "",
) -> str:

    provider = provider.lower().strip()

    if provider == "ollama":

        return generate_with_ollama(
            prompt=prompt,
            system_prompt=system_prompt,
        )

    elif provider in {"google", "gemini"}:

        return generate_with_gemini(
            prompt=prompt,
            system_prompt=system_prompt,
        )

    else:

        raise ValueError(
            f"Unsupported LLM provider: {provider}"
        )