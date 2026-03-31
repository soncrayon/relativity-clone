# Relativity Clone MVP Plan

Relativity is primarily an e-discovery platform. This MVP focuses on core document management, processing, and review, with an AI chatbot for document Q&A.

---

## Current Architecture (Implemented)

```
Frontend Stack:
├── Vite 7 (upgrading to Vite+ / Vite 8 + Rolldown)
├── React 19 + TypeScript 5.8
├── Chakra UI v3 (Emotion runtime, compound component API)
├── React Router v7 — data mode (createBrowserRouter + RouterProvider)
├── Zustand 5 (client state)
└── Pure client-side SPA (no SSR)

Patterns:
├── Lazy-loaded routes via React Router `lazy` property
├── Parallel loading of components + loaders via Promise.all
├── Route loaders return data before components render (useLoaderData)
├── Suspense boundary with Chakra Spinner fallback
├── @ path alias (vite.config.ts + tsconfig.app.json)
└── Code-split chunks per route (automatic via dynamic imports)
```

### Project Structure

```
src/
├── main.tsx                    # Router + Provider + Suspense setup
├── Layout.tsx                  # Shell (sidebar nav + Outlet)
├── index.css                   # Global styles
├── components/
│   ├── Home.tsx                # Landing page
│   ├── Workspaces.tsx          # Workspaces table (useLoaderData)
│   ├── Users.tsx               # Users table (useLoaderData)
│   ├── Groups.tsx              # Groups table (useLoaderData)
│   └── ui/
│       └── provider.tsx        # Chakra v3 Provider wrapper
├── loaders/
│   ├── workspaces.ts           # Workspace data loader
│   ├── users.ts                # User data loader
│   └── groups.ts               # Group data loader
├── data/
│   ├── workspaces.ts           # Mock workspace data
│   ├── users.ts                # Mock user data
│   └── groups.ts               # Mock group data
└── store/
    └── index.ts                # Zustand store
```

---

## Phase 1: Core Document Management System (DMS) — MVP

### 1. Technology Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| **Toolchain** | **Vite+** (Vite 8 + Rolldown + Oxlint + Oxfmt + Vitest) | Unified CLI (`vp`). Currently on Vite 7; migrate via `vp migrate`. |
| **Frontend** | React 19 (TypeScript 5.8) + Chakra UI v3 | Pure client-side SPA. Compound component API (`Table.Root`, `List.Root`, etc.). |
| **Routing** | React Router v7 — data mode | `createBrowserRouter` + `RouterProvider`. Route `loader` functions + `useLoaderData()`. Lazy-loaded routes via `lazy` property. |
| **Client State** | Zustand 5 | Lightweight store for UI state (selections, filters, etc.). |
| **Backend** | Python 3.10 (FastAPI) | REST API for documents, users, auth. |
| **Database** | PostgreSQL 14.7 (Homebrew) | Metadata store + full-text search via `tsvector`. |
| **Object Storage** | Local Filesystem (`./storage/documents`) | Upgrade to S3/MinIO for production. |
| **Doc Processing** | `pdfminer.six`, `python-docx`, `python-magic` | Text extraction from PDF, DOCX, TXT, EML. |

### 2. Vite+ Toolchain Migration

Vite+ is a unified toolchain wrapper (not a framework). It bundles Vite 8 (Rolldown-based), Oxlint, Oxfmt, and Vitest under a single `vp` CLI and `vite.config.ts`.

**Migration steps:**
1.  Install `vp` CLI globally: `curl -fsSL https://vite.plus | bash`
2.  Run `vp migrate` in project root (auto-upgrades Vite 7 → 8, merges ESLint into `lint` block)
3.  Remove stale ESLint devDependencies (already done)
4.  Upgrade `@vitejs/plugin-react` to v6 (Oxc-based, drops Babel)
5.  Add `lint`, `fmt`, and `test` blocks to `vite.config.ts`

**New CLI commands:**

| Command | Purpose |
|---------|---------|
| `vp dev` | Start dev server |
| `vp build` | Production build (Vite 8 + Rolldown) |
| `vp check` | Format + lint + type-check in one pass |
| `vp test` | Run Vitest |

### 3. User Management
*   Implement JWT-based authentication using FastAPI + PostgreSQL.
*   Roles: **Admin** (system/workspace management), **Reviewer** (tagging/search).
*   Frontend: Login page route with loader-based auth guard on protected routes.

### 4. Document Ingestion
*   Chakra UI v3 drag-and-drop upload interface.
*   Secure storage in local filesystem (`./storage/documents`).
*   Metadata extraction (filename, size, MIME type, upload date) stored in PostgreSQL.
*   Upload progress via Chakra `Progress` component.

### 5. Basic Document Processing
*   Extract plain text from PDF, DOCX, TXT, EML.
*   Index text for search using PostgreSQL's `tsvector` (full-text search).
*   Processing status tracked per document (pending → processing → complete → error).

### 6. Document Review Interface
*   **Viewer:** Display extracted text content with scroll sync.
*   **Coding:** "Responsive", "Non-Responsive", "Privileged" tags via Chakra `Tag` components.
*   **Search:** Keyword and boolean search across indexed documents.
*   **Route structure:**
    ```
    /workspaces/:workspaceId/documents          → Document list (table + filters)
    /workspaces/:workspaceId/documents/:docId   → Document viewer + coding panel
    ```

---

## Phase 2: AI Chatbot Integration

### 1. Knowledge Base Preparation
*   **Document Chunking:** `langchain` or `llama-index` for context-aware chunking.
*   **Vector Embeddings:** Local models (`sentence-transformers`) or Gemini API.
*   **Vector Database:** **ChromaDB** (local Python library, `pip install chromadb`).

### 2. Chatbot Backend API
*   FastAPI endpoint for user queries.
*   RAG (Retrieval-Augmented Generation) pipeline:
    1.  Embed query.
    2.  Retrieve top-N chunks from ChromaDB.
    3.  Generate prompt for LLM (Gemini/OpenAI).
    4.  Return streamable response via SSE.

### 3. Chatbot Frontend Integration
*   Integrated chat panel in the Review interface (Chakra `Drawer` component).
*   Citations/links back to source documents and specific text chunks.
*   Lazy-loaded chat route/panel for zero cost when not in use.

---

## Phase 3: Deployment & Iteration

### 1. Local Dev Workflow

| Service | Command |
|---------|---------|
| Frontend | `vp dev` (Vite+ dev server, port 9000) |
| Backend | `uvicorn main:app --reload` (FastAPI) |
| Database | PostgreSQL service (Homebrew) |

### 2. Packaging
*   `poetry` for Python dependency management.
*   Containerize with Docker when ready (frontend + backend + PostgreSQL).

### 3. Testing
*   Frontend: `vp test` (Vitest, built into Vite+).
*   Backend: `pytest` + `httpx` for FastAPI endpoint tests.

### 4. Monitoring & Feedback
*   Python `logging` module for backend.
*   Simple feedback loop for tagging accuracy.

---

## Technical Notes

1.  **Database:** PostgreSQL 14.7 via Homebrew. Can also serve as vector store via `pgvector` extension.
2.  **Object Storage:** Local filesystem for now. Zero-config, no Docker required.
3.  **Vite+ status:** Currently on Vite 7.3.1. Vite+ (`vp` CLI) is in alpha — run `vp migrate` when ready.
4.  **Chakra UI v3:** Uses Emotion at runtime today. Long-term direction is zero-runtime (Panda CSS) but migration will be transparent.
5.  **AI Models:** Gemini API for low local footprint, or Ollama for fully local inference.
