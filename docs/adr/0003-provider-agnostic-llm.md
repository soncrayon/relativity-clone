# ADR 0003: Provider-Agnostic LLM Abstraction

**Status:** Accepted  
**Date:** 2026-04-04

## Context

The RAG pipeline needs to call a Large Language Model (LLM). Different LLMs have different trade-offs: cost, quality, privacy, and whether an internet connection is required.

## Decision

Build a **`BaseLLMProvider` protocol** in `backend/app/services/llm/` with separate implementations for OpenAI, Gemini, and Ollama. The active provider is selected via the `LLM_PROVIDER` environment variable.

## Reasons

- **Demo flexibility:** Ollama runs a local model (no API key, no cost) — ideal for running the demo anywhere. OpenAI/Gemini can be swapped in for higher quality responses.
- **Portfolio signal:** The abstraction layer demonstrates knowledge of the Strategy design pattern and shows the system isn't tightly coupled to one vendor.
- **Privacy argument:** In legal tech, the ability to run a fully local model (no data leaves the machine) is a real selling point. The abstraction makes this easy to demonstrate.

## Interface contract

Every provider must return the same `LLMResponse` shape:

```python
{
  "answer": str,
  "citations": [{"marker": str, "chunk_id": int}],
  "confidence": float  # 0.0–1.0
}
```

## Trade-offs

- Adds a layer of indirection that makes the code slightly more complex to follow
- Each provider needs to handle its own prompt formatting differences
- Confidence scoring is not natively provided by all LLMs; it must be estimated from retrieval scores or self-consistency checks
