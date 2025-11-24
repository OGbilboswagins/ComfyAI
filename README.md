# ComfyAI (Under Construction)

**ComfyAI** is an experimental custom plugin for **ComfyUI**, currently under active development. Its goal is to provide:

- 🔧 **LLM‑powered workflow rewriting**
- 🧠 **Provider system** (local & cloud models)
- 🚀 **MCP‑ready architecture** (not fully enabled yet)
- 🎛️ **Future UI panel** for interactive workflow edits

This repository is not yet ready for general use. Expect frequent changes, incomplete features, and breaking updates.

## Status
- Backend loads successfully inside ComfyUI
- Rewrite engine operational and responding to API requests
- Provider system partially implemented
- Frontend UI not yet integrated
- Documentation in progress

## Temporary Instructions
Until full documentation is written:

1. Place this plugin inside:
   ```
   ComfyUI/custom_nodes/ComfyUI-ComfyAI
   ```

2. Ensure you have a `providers.json` file inside:
   ```
   ComfyUI/user/default/ComfyAI/providers.json
   ```

3. Test the rewrite endpoint:
   ```bash
   python scripts/test_workflow_rewrite.py
   ```

## Roadmap
- Full README with install steps
- Provider configuration docs
- UI component build & integration
- MCP agent integration
- Workflow validation tools
- Release packaging

---
**NOTE:** This README is temporary and will be replaced soon.

---

