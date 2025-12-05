# Embeddings & Tooling (Future Plans)

> **Note:** This document describes planned functionality for future versions of ComfyAI.

ComfyAI is designed to eventually support:

- Vector-based memory and retrieval
- Per-workflow semantic search
- Tool calling and MCP-style extensions
- External knowledge integration (docs, notes, tutorials)

This will likely involve:

- A local or remote vector database (Chroma, Qdrant, SQLite-based, etc.)
- Embedding models (local or cloud)
- Structured tools exposed by ComfyAI for the LLM to call

## Planned Directions

- Let the model "read" workflows, names, and descriptions.
- Allow quick search: "find my anime upscaling workflow".
- Store user hints and preferences as embeddings.
- Offer pluggable embedding backends for power users.

These designs will be refined once chat, plan, and edit modes are fully stable.
