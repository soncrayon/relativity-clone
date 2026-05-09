"""
Base types and protocol for the provider-agnostic LLM abstraction.

Every LLM provider (Ollama, Gemini, Claude, OpenAI) must implement the
BaseLLMProvider protocol — specifically the `generate` method. This means
the RAG pipeline can call `provider.generate(...)` without knowing or caring
which model is actually running underneath.

This is the Strategy design pattern: the algorithm (which model to call) is
swapped at runtime via the LLM_PROVIDER environment variable, while the
interface stays constant.

Response shape
--------------
Every provider returns an LLMResponse:

  answer     — the model's response text
  citations  — list of citation markers the model emitted, each linked back
               to a chunk_id from ChromaDB (validated in the RAG pipeline)
  confidence — a 0.0–1.0 score; providers that don't natively expose
               confidence should estimate it from response length / hedging
               language, or return a fixed 0.8 as a placeholder
"""

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class Citation:
    """
    A single citation emitted by the LLM, linking a marker in the answer
    text (e.g. "[1]") to a specific DocumentChunk in ChromaDB.

    The RAG pipeline validates that chunk_id actually exists before returning
    the response to the caller — this is the anti-hallucination guard.
    """
    marker: str       # The citation label in the answer, e.g. "[1]" or "[Smith2024]"
    chunk_id: str     # ChromaDB entry ID, e.g. "doc_3_chunk_12"


@dataclass
class LLMResponse:
    """
    Structured response returned by every provider.

    Using a dataclass (rather than a plain dict) means the RAG pipeline can
    access fields by name and get a TypeError at dev time if a provider
    forgets to return a required field — instead of a KeyError at runtime.
    """
    answer: str
    citations: list[Citation] = field(default_factory=list)
    confidence: float = 0.8


@runtime_checkable
class BaseLLMProvider(Protocol):
    """
    Protocol that all LLM providers must satisfy.

    `runtime_checkable` means you can use `isinstance(provider, BaseLLMProvider)`
    to verify a provider is correctly wired at startup — useful in tests and
    the provider factory.

    Parameters
    ----------
    prompt : str
        The user's question or instruction.
    context : list[str]
        The retrieved document chunks passed as context. The provider is
        responsible for formatting these into the final prompt it sends to
        the model — each provider may do this differently (system message,
        user turn, XML tags, etc.).

    Returns
    -------
    LLMResponse
        Structured response with answer, citations, and confidence.
    """

    def generate(self, prompt: str, context: list[str]) -> LLMResponse:
        ...
