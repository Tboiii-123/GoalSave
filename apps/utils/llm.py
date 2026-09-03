import json

from django.conf import settings
from groq import Groq

client = Groq(api_key=settings.GROQ_API_KEY)


def generate_llm_response(
    *,
    system_prompt: str,
    user_prompt: str | None = None,
    temperature: float = 0,
    json_mode: bool = False,
):
    """
    Reusable LLM service.

    Handles communication with the LLM provider while
    keeping business logic outside this layer.
    """

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]

    if user_prompt:
        messages.append(
            {
                "role": "user",
                "content": user_prompt,
            }
        )

    kwargs = {
        "model": "openai/gpt-oss-120b",
        "messages": messages,
        "temperature": temperature,
    }

    if json_mode:
        kwargs["response_format"] = {
            "type": "json_object"
        }

    response = client.chat.completions.create(**kwargs)

    content = response.choices[0].message.content

    if json_mode:
        return json.loads(content)

    return content