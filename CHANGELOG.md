# Changelog

All notable changes to this project will be documented in this file.

The format loosely follows [Keep a Changelog](https://keepachangelog.com/),  
and this project adheres to **Semantic Versioning**.

---

## [Unreleased]

<!-- Future changes go here -->

---

## [1.0.0] – 2025-12-27

### Added
- Major documentation overhaul: README, LICENSE, CONTRIBUTING, FUNDING, SECURITY.
- Complete chat panel + settings panel UI integration.
- ComfyUI-style modal settings panel with icons and tabs.
- Full provider management backend (OpenAI, Gemini, Ollama, Groq-ready).
- Unified persistent settings backend using JSON in `user/default/ComfyUI-ComfyAI/`.
- UI model selector with per-mode default model support.
- Mode-aware chat system (Chat / Plan / Edit).
- Automatic model switching per mode with manual override protection.
- Collapsible assistant message metadata (mode + model).
- Markdown rendering for assistant messages.
- One-click copy of raw Markdown responses.
- Typing indicator (3-dot animation).
- Workflow rewrite infrastructure & agent stubs.

### Improved
- Significant UI polish: scrolling, streaming, bubbles layout.
- Sidebar button injection and event handlers.
- CSS architecture for chat + settings layout.
- Error handling for provider load and settings failures.
- Streaming stability and message rendering pipeline.
- Hover-based icon-only controls with no layout shift.

### Fixed
- System prompts being dropped during streaming.
- Model auto-switch race conditions.
- Hover flicker and unclickable message controls.
- Settings JSON being written to the wrong path.
- Chat panel slide-in transform not applying.
- Settings button click not registering.
- Large icon and label scaling in sidebar.
- Missing styles due to extension path prefix mismatch.
- Duplicate backend routing (“split-brain” issue).

---

## [0.3.0] – 2025-12-02

### Added
- Initial public release of the repository.
- First working version of ComfyAI chat panel inside ComfyUI.
- Logo, branding, and animated GIF added to assets.
- GitHub Sponsors tiers, PayPal link, repo automation.
- Comfy Registry integration and auto-publish workflow.

### Improved
- Repository structure standardized.
- Compatible with ComfyUI Manager auto-discovery.
- pyproject.toml updated with correct PublisherId and node metadata.

---

## [0.1.0] – 2025-11-22

### Added
- First internal prototype for chat interface.
- Basic LLM request/response support.
- Local provider handling & configuration system.
