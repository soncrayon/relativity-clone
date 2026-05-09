"""
Ollama LLM provider — runs models locally, no API key required.

Ollama exposes a local HTTP server (default: http://localhost:11434) that
serves open-source models like Llama 3, Mistral, and Gemma. This provider
calls Ollama's `/api/chat` endpoint using Python's built-in `urllib` so
there's no extra dependency.

Setup (one-time):
  1. Install Ollama: https://ollama.com
  2. Pull a model: `ollama pull llama3.2`
  3. Ollama starts automatically in the background on macOS.

The model and base URL are configured via settings (LLM_PROVIDER=ollama,
OLLAMA_MODEL, OLLAMA_BASE_URL).

Citation parsing
----------------
The system prompt instructs the model to cite sources using [1], [2], ...
notation. This provider parses those markers from the response text and
maps them back to the ChromaDB chunk IDs passed in via context metadata.

If the model doesn't emit any citations (common with smaller models), the
response still returns successfully — citation validation happens upstream
in the RAG pipeline.
"""

import json
import re
import urllib.error
import urllib.request
from typing import Any

from app.services.llm.base import Citation, LLMResponse

# System prompt injected before every request.
# The instructions are explicit about citation format so the parser below
# can reliably extract them. The legal framing is intentional — it primes
# the model to be precise and conservative rather than fluent and creative.
_SYSTEM_PROMPT = """\
You are a precise legal document assistant. Answer questions using ONLY the
provided source documents. Do not speculate or add information not present
in the sources.

When you use information from a source, cite it inline using the format [1],
[2], etc., where the number corresponds to the source number in the context.
If a statement draws on multiple sources, list all relevant citations: [1][3].

If the provided sources do not contain enough information to answer the
question, say so explicitly rather than guessing.
"""


class OllamaProvider:
    """
    Sends requests to a locally-running Ollama server.

    Raises RuntimeError on connection failure (server not running) or if
    the model has not been pulled. The error message includes actionable
    instructions so developers know exactly what to run.
    """

    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._chat_url = f"{self.base_url}/api/chat"

    def generate(self, prompt: str, context: list[str]) -> LLMResponse:
        """
        Build a chat request, send to Ollama, parse the response.

        context is a list of chunk texts. They are numbered starting from 1
        so the model can cite them as [1], [2], etc. and so the parser can
        map citation numbers back to the chunk IDs passed by the RAG pipeline.
        """
        user_message = _build_user_message(prompt, context)

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            # Keep responses deterministic for reproducible evals.
            "options": {"temperature": 0.1},
        }

        raw_response = _post_json(self._chat_url, payload)
        answer = raw_response["message"]["content"]
        citations = _parse_citations(answer, context)

        return LLMResponse(answer=answer, citations=citations)

    def check_connection(self) -> bool:
        """
        Ping Ollama's /api/tags endpoint to verify the server is running.
        Returns True if reachable, False otherwise. Used at startup to give
        a clear warning if Ollama isn't running rather than failing silently
        on the first chat request.
        """
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=3):
                return True
        except Exception:
            return False


# ── helpers ────────────────────────────────────────────────────────────────────

def _build_user_message(prompt: str, context: list[str]) -> str:
    """
    Format retrieved chunks as numbered sources above the user's question.
    The numbering matches the citation markers ([1], [2]) the model is
    instructed to use.
    """
    if not context:
        return prompt

    sources = "\n\n".join(
        f"[{i + 1}] {chunk}" for i, chunk in enumerate(context)
    )
    return f"SOURCES:\n{sources}\n\nQUESTION: {prompt}"


def _post_json(url: str, payload: dict) -> dict:
    """
    POST a JSON payload and return the parsed JSON response.
    Raises RuntimeError with actionable messages on connection/model errors.
    """
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Cannot connect to Ollama at {url}. "
            "Is Ollama running? Start it with: ollama serve"
        ) from exc
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        if "model" in body.lower() and "not found" in body.lower():
            model = payload.get("model", "unknown")
            raise RuntimeError(
                f"Ollama model '{model}' is not pulled. "
                f"Run: ollama pull {model}"
            ) from exc
        raise RuntimeError(f"Ollama returned HTTP {exc.code}: {body}") from exc


_CITATION_RE = re.compile(r"\[(\d+)\]")


def _parse_citations(answer: str, context: list[str]) -> list[Citation]:
    """
    Extract [1], [2], ... markers from the answer and build Citation objects.

    The chunk_id field is left as the raw number string here because the
    RAG pipeline has the actual ChromaDB IDs — it will map [1] → chunk IDs
    using the same ordered list of context chunks it passed in.

    Only includes citation numbers that are within range of the context list
    so we don't create citations pointing to non-existent sources.
    """
    seen: set[str] = set()
    citations: list[Citation] = []

    for match in _CITATION_RE.finditer(answer):
        number_str = match.group(1)
        number = int(number_str)

        if number_str in seen:
            continue
        seen.add(number_str)

        # 1-indexed citation number, 0-indexed context list
        if 1 <= number <= len(context):
            citations.append(Citation(marker=f"[{number_str}]", chunk_id=number_str))

    return citations
