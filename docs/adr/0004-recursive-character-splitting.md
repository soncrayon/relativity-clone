# ADR 0004: Recursive Character Splitting for Document Chunking

**Status:** Accepted  
**Date:** 2026-04-04

## Context

Documents must be split into smaller pieces ("chunks") before being embedded and stored in ChromaDB. The LLM can only handle a limited amount of text at once, so rather than passing an entire 200-page deposition, we retrieve only the most relevant chunks for each query.

Two main approaches were considered:

- **Recursive character splitting:** Split text by paragraph → sentence → character, in order of preference, until chunks are within a target size. Predictable and deterministic.
- **Semantic chunking:** Use an embedding model to split at topic boundaries. More intelligent, but slower and non-deterministic.

## Decision

Use **recursive character splitting** with configurable chunk size and overlap.

## Reasons

- **Deterministic:** The same document always produces the same chunks. This is important for reproducibility — if a citation points to chunk 42, it will always be the same text.
- **No extra model dependency:** Semantic chunking requires running embeddings twice (once to chunk, once to index). Recursive splitting has no additional dependencies.
- **Overlap handles boundary cases:** A configurable overlap (e.g. 10% of chunk size) ensures that sentences split across chunk boundaries still appear in at least one chunk fully intact.
- **Explainability:** In legal tech, being able to explain exactly how a document was processed matters. "We split on paragraph breaks, then sentence breaks, targeting 512 tokens" is easy to explain to a client or court.

## Trade-offs

- Semantic chunking would better preserve topic coherence in long, dense documents
- Fixed-size chunks can cut mid-argument in legal briefs; overlap mitigates but doesn't fully solve this
- Chunk size is a tuneable parameter — too small loses context, too large wastes the LLM's context window
