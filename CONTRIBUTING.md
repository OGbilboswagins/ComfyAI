# Contributing to ComfyAI

Thanks for your interest in contributing! 🎉

We welcome:

- Bug fixes and stability improvements
- UI/UX tweaks
- Provider integrations
- Feature implementations for the roadmap
- Documentation updates and examples

## Getting Started

1. Make sure you have a working ComfyUI installation.
2. Clone this repo into your `custom_nodes` directory:

```bash
cd /path/to/ComfyUI/custom_nodes
git clone https://github.com/OGbilboswagins/ComfyAI.git
```

3. Restart ComfyUI.
4. Open the browser devtools console to debug the frontend (`F12`).

## Development Guidelines

- Keep pull requests small and focused when possible.
- Write clear commit messages (e.g., `fix:`, `feat:`, `refactor:`, `docs:`).
- Make sure the basic chat flow + settings panel still work.
- Add or update documentation when introducing user-facing changes.

## Issue Reporting

When opening an issue, please include:

- OS, browser, and ComfyUI version
- Console logs (frontend) and relevant backend logs
- Steps to reproduce
- Screenshots or GIFs if applicable

## Code Style

Try to keep changes consistent with the existing style:

- Python: follow PEP8 where practical.
- JS: keep it simple and readable (no unnecessary framework baggage).
- CSS: keep ComfyUI’s dark theme and spacing philosophy.

---

Thank you again for helping build ComfyAI 💙
