# Changelog

All notable changes to this project will be documented in this file.

The format loosely follows [Keep a Changelog](https://keepachangelog.com/),  
and this project adheres to **Semantic Versioning**.

---

## [Unreleased]

### Added
- Major documentation overhaul: README, LICENSE, CONTRIBUTING, FUNDING, SECURITY.
- Added complete chat panel + settings panel UI integration.
- Added ComfyUI-style modal settings panel with icons and tabs.
- Added full provider management backend (OpenAI, Gemini, Ollama, Groq-ready).
- Added unified persistent settings backend using JSON in `user/default/ComfyUI-ComfyAI/`.
- Added UI model selector and settings-driven default model loader.
- Added workflow rewrite infrastructure & agent stubs.
- Added typing indicator (3-dot animation).

### Improved
- Significant UI polish: fixed scrolling, streaming, bubbles layout.
- Improved sidebar button injection and event handlers.
- Cleaner CSS architecture for chat + settings layout.
- Better error handling for provider load and settings load failures.

### Fixed
- Fixed settings JSON being written to the wrong path.
- Fixed chat panel not sliding open due to transform not being applied.
- Fixed settings button click not registering.
- Fixed large icons and label scaling in sidebar.
- Fixed missing styles due to extension path prefix mismatch.

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