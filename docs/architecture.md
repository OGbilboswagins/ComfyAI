# ComfyAI Architecture

This document gives a high-level overview of how ComfyAI is structured internally.

## High-Level Overview

ComfyAI is split into three main pieces:

1. **Backend (Python / aiohttp)**
2. **Frontend (JavaScript + CSS injected into ComfyUI)**
3. **ComfyUI Integration (extension mounting, user config paths, registry metadata)**

### Backend

The backend lives under `backend/` and integrates with ComfyUI's `server.PromptServer` via a custom extension.

Key modules:

- `backend/router.py`  
  Registers all `/api/comfyai/*` routes and initializes core services.

- `backend/provider_manager.py`  
  Loads provider definitions from `config/providers.json` and exposes the active provider registry.

- `backend/llm/`  
  Provider-specific implementations:
    - `ollama_provider.py`
    - `openai_provider.py`
    - `gemini_provider.py`
    - `base.py` (interfaces)
    - `registry.py` (LLM provider registry)

- `backend/routes/`  
  HTTP route handlers:
    - `chat.py` — `/api/comfyai/chat` and `/api/comfyai/chat/stream`
    - `providers.py` — `/api/comfyai/providers`, `/api/comfyai/models`
    - `settings.py` — `/api/comfyai/settings`

- `backend/utils/settings_manager.py`  
  Reads/writes the user-facing `settings.json` under:
  `COMFYUI_ROOT/user/default/ComfyUI-ComfyAI/settings.json`

- `backend/utils/paths.py`  
  Centralized path resolution (plugin root, ComfyUI root, user config path).

### Frontend

The frontend lives in `frontend/`:

- `comfyai.js`  
  - Injects a sidebar button into the ComfyUI left sidebar.  
  - Creates a floating sliding chat panel.  
  - Loads `chat.html` into the panel.  
  - Sends chat requests to `/api/comfyai/chat` or `/api/comfyai/chat/stream`.  
  - Wires up the settings button and full-screen settings panel.

- `comfyai.css`  
  - Implements the ChatGPT-style UI:
    - Sliding panel
    - Header with logo
    - Scrollable message area
    - Input + send button
    - Typing indicator animation
  - Styles for the settings panel and sidebar icons.

- `chat.html`  
  - The HTML shell loaded into the panel.
  - Contains the chat window, settings button, settings panel DOM.

### ComfyUI Integration

ComfyAI is mounted by ComfyUI as an extension under:

- `/extensions/ComfyUI-ComfyAI/` (repo root)
- `/extensions/ComfyAI/frontend/` (static assets)

The user config directory lives in:

- `COMFYUI_ROOT/user/default/ComfyUI-ComfyAI/`

Registry metadata is defined in:

- `pyproject.toml` → `[tool.comfy]` section
  - `PublisherId`
  - `DisplayName`
  - `Icon`

This allows ComfyUI Manager and the Comfy Registry to discover, list, and update the node.
