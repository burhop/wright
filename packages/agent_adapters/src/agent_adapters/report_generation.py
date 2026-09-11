"""Generate workflow responses through the configured Hermes model."""
from __future__ import annotations

import uuid
import httpx
from .hermes_config import resolve_hermes_api_settings

# Wright's conservative workflow text policy, not a provider context guarantee.
# Native engineering observations can exceed 120 KB well below model capacity.
# The bridge still enforces complete evidence, per-part limits and retry reserves.
WORKFLOW_TRANSLATION_PROMPT_BYTES = 200_000

FORMAT_INSTRUCTIONS = {
    "text": "Return plain text answering the prompt.",
    "markdown": "Return a Markdown document answering the prompt. Do not wrap the document in a code fence.",
    "html": "Return only a complete standalone HTML document starting with <!doctype html>, with a title and readable headings. Use inline CSS, no scripts, external assets or forms. Do not wrap it in a code fence.",
    "json": "Return only valid JSON answering the prompt. Do not add prose or code fences.",
}

def response_instructions(output_format: str) -> str:
    return FORMAT_INSTRUCTIONS[output_format] + " Do not write files or call tools; Wright handles saving the response. Clearly label assumptions and do not claim unperformed tool execution."

async def generate_workflow_response(prompt: str, output_format: str, *, images: list[str] | None = None) -> str:
    settings = resolve_hermes_api_settings()
    headers = {"X-Hermes-Session-Id": f"wright-workflow-{uuid.uuid4()}"}
    if settings.api_key:
        headers["Authorization"] = f"Bearer {settings.api_key}"
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(180, connect=10)) as client:
            response = await client.post(
                f"{settings.base_url}/v1/chat/completions", headers=headers,
                json={"model": "hermes", "stream": False, "tools": [], "tool_choice": "none",
                      "messages": [{"role": "system", "content": response_instructions(output_format)},
                                   {"role": "user", "content": ([{"type": "text", "text": prompt}, *[{"type": "image_url", "image_url": {"url": url}} for url in images]] if images else prompt)}]},
            )
            response.raise_for_status()
            value = response.json()["choices"][0]["message"]["content"]
    except httpx.ReadTimeout as error:
        raise TimeoutError("The model did not finish responding within 180 seconds.") from error
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as error:
        raise ValueError("The model did not return a response. Check Model Setup and run again.") from error
    if not isinstance(value, str):
        raise ValueError("The model returned no text response. Run again with a clearer prompt.")
    return value

async def generate_html_report(prompt: str) -> str:
    """Compatibility entry point; workflow execution validates the response."""
    return await generate_workflow_response(prompt, "html")


async def decide_workflow_tool_action(messages: list[dict], tools: list[dict], *, required: bool = False) -> dict:
    """Reuse Hermes' validated single-action protocol adapter for native tasks."""
    from .hermes_openai_bridge import HermesOpenAICompatibilityBridge, HermesOpenAIBridgeSettings, HermesBridgeError
    settings = resolve_hermes_api_settings()
    bridge = HermesOpenAICompatibilityBridge(HermesOpenAIBridgeSettings(
        base_url=settings.base_url, api_key=settings.api_key, workflow_task=True,
        timeout_seconds=180, maximum_tools=64,
        maximum_translation_prompt_bytes=WORKFLOW_TRANSLATION_PROMPT_BYTES,
        # Includes base64 workspace image attachments, which remain separate
        # from the bounded 200,000-byte textual decision transcript.
        maximum_text_bytes=16 * 1024 * 1024,
    ))
    try:
        result = await bridge.complete({"model": "wright-hermes", "messages": messages,
            "tools": tools, "tool_choice": "required" if required else "auto", "stream": False})
        return result["choices"][0]["message"]
    except HermesBridgeError as error:
        # Bridge errors are deliberately browser-safe. Preserve the actionable
        # contract failure rather than misreporting every error as Model Setup.
        raise ValueError(f"The model task could not continue ({error.code}): {error}") from error
    except (KeyError, IndexError, TypeError) as error:
        raise ValueError("The model could not choose a valid task action. Check Model Setup or clarify the task.") from error
