# ADR 0002: ChromaDB for Vector Storage

**Status:** Accepted  
**Date:** 2026-04-04

## Context

The RAG pipeline needs to store and search document chunk embeddings (high-dimensional vectors). Two main options were considered: **ChromaDB** and **pgvector** (a PostgreSQL extension).

## Decision

Use **ChromaDB** as a separate, local vector store.

## Reasons

- **pgvector** would store vectors inside PostgreSQL, meaning one tool does both jobs. Simpler to operate, but ties vector search performance to the relational DB.
- **ChromaDB** keeps the vector index physically separate. This means better search performance at scale and the ability to swap it out for Qdrant or Pinecone in the future without touching the relational schema.
- ChromaDB runs locally with zero configuration — no cloud account, no cost. This matters for a portfolio project that needs to be easy to demo.
- The hybrid query strategy (SQL metadata filter → vector similarity search) works at the **application layer**, so the two stores don't need to be co-located anyway.

## Trade-offs

- Two datastores to manage instead of one
- ChromaDB's persistence format is less battle-tested than PostgreSQL at large scale
- If this project moves to a managed cloud service, pgvector is simpler (one connection, one backup target)
