# ADR 0001: Python + FastAPI for the Backend

**Status:** Accepted  
**Date:** 2026-04-04

## Context

We needed to choose a backend language and framework. Go was considered as an alternative, given its growing popularity and performance reputation.

## Decision

Use **Python 3.10** with **FastAPI**.

## Reasons

The core differentiator of this project is the AI/RAG pipeline. The Python ecosystem owns this space:

- `sentence-transformers`, `chromadb`, and LLM SDKs (`openai`, `google-generativeai`) are Python-native with no Go equivalents
- Document parsing libraries (`pdfminer.six`, `python-docx`) are mature in Python; Go alternatives are thin
- `presidio-analyzer` (PII detection, Phase 5) is Microsoft's Python library with no Go port

Using Go would mean calling out to Python microservices for all AI work anyway — more complexity with no payoff.

FastAPI was chosen over Flask/Django because:

- Native async support for non-blocking LLM API calls
- Automatic Swagger/OpenAPI docs generation at `/docs`
- Tight Pydantic integration for request/response validation

## Trade-offs

- Python is slower than Go for CPU-bound work, but **the bottleneck here is LLM API latency**, not server throughput
- Go would be the right choice for a pure CRUD API or real-time system with no AI features
