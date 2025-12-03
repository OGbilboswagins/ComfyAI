<p align="center">
  <img src="assets/comfyai_logo.png" alt="ComfyAI Logo" width="260">
</p>

<h1 align="center">ComfyAI — Your AI Copilot Inside ComfyUI</h1>

<p align="center">
  <strong>Chat • Plan • Edit • Automate</strong><br>
  AI assistant panel fully integrated into the ComfyUI interface.
</p>

<p align="center">
  <img src="assets/ComfyAI.gif" width="720" alt="ComfyAI Demo">
</p>

---

<p align="center">

  <!-- Core repo stats -->
  <a href="https://github.com/OGbilboswagins/ComfyAI/stargazers">
    <img src="https://img.shields.io/github/stars/OGbilboswagins/ComfyAI?style=for-the-badge&logo=github&color=yellow" alt="GitHub Stars">
  </a>

  <a href="https://github.com/OGbilboswagins/ComfyAI/issues">
    <img src="https://img.shields.io/github/issues/OGbilboswagins/ComfyAI?style=for-the-badge&logo=github" alt="GitHub Issues">
  </a>

  <a href="https://github.com/OGbilboswagins/ComfyAI">
    <img src="https://img.shields.io/github/last-commit/OGbilboswagins/ComfyAI?style=for-the-badge&logo=git" alt="Last Commit">
  </a>

  <!-- Size / license -->
  <a href="https://github.com/OGbilboswagins/ComfyAI">
    <img src="https://img.shields.io/github/repo-size/OGbilboswagins/ComfyAI?style=for-the-badge&logo=github" alt="Repo Size">
  </a>

  <a href="https://github.com/OGbilboswagins/ComfyAI/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge" alt="License: MIT">
  </a>

  <!-- ComfyUI Manager availability (link can be updated once registry page exists) -->
  <a href="https://github.com/comfyanonymous/ComfyUI">
    <img src="https://img.shields.io/badge/Available%20via-ComfyUI%20Manager-0f766e?style=for-the-badge&logo=data:image/svg+xml;base64," alt="Available via ComfyUI Manager">
  </a>

  <!-- Funding -->
  <a href="https://github.com/sponsors/OGbilboswagins">
    <img src="https://img.shields.io/badge/Sponsor-❤-ff69b4?style=for-the-badge&logo=githubsponsors" alt="GitHub Sponsors">
  </a>

  <a href="https://paypal.me/ogbilboswaggins">
    <img src="https://img.shields.io/badge/Donate-PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="Donate via PayPal">
  </a>

</p>

---

## 🚀 What Is ComfyAI?

**ComfyAI** is a fully embedded AI assistant panel for **ComfyUI**, inspired by tools like Continue.dev but purpose-built for AI image generation and node-based workflows.

It lets you:

- 💬 Chat with LLMs directly inside ComfyUI  
- 🧠 Plan and debug workflows in natural language  
- 🎛 Switch between local and cloud models via providers  
- ⚙️ Configure everything through a fullscreen settings panel  
- 🔮 (Roadmap) Use AI-powered modes like **Chat / Plan / Edit** to control how the assistant behaves

All without leaving the ComfyUI interface.

---

## ✨ Key Features

### 🧩 Integrated Chat Panel

- Side-panel button in the ComfyUI sidebar  
- Sliding chat panel that matches ComfyUI’s dark theme  
- ChatGPT-style bubbles with markdown & code blocks  
- Animated 3-dot typing indicator  
- Auto-scroll that doesn’t fight with you  
- Local history persistence

### ⚙️ Fullscreen Settings Panel

- Opens from the chat footer via a settings icon  
- Covers the chat UI with a dedicated settings layout  
- Left-hand sidebar with icons for:
  - General  
  - Appearance  
  - Chat Behavior  
  - Providers & Models  
  - Advanced  
- All settings persisted under the ComfyUI `user/default/ComfyUI-ComfyAI` directory  
- Backed by `/api/comfyai/settings` in the Python backend

### 🔌 Provider & Model Management

- Backend provider manager detects configured providers  
- Designed for:
  - **Ollama** (local models)
  - **OpenAI-compatible APIs**
  - **Google Gemini**
  - More providers as the project evolves  
- UI model dropdown groups models by provider  
- Settings panel supports:
  - Default provider
  - Default model per mode (Chat / Plan / Edit) — roadmap

---

## 📦 Installation

### 1. ComfyUI Manager (Recommended)

Once published to the registry:

1. Open **ComfyUI Manager**
2. Go to the **Custom Nodes** tab  
3. Search for **“ComfyAI”**  
4. Click **Install** and restart ComfyUI

### 2. Manual Git Clone

From your ComfyUI root:

```bash
cd custom_nodes
git clone https://github.com/OGbilboswagins/ComfyAI.git
```

Restart ComfyUI.

### 3. ZIP Download

Download the latest release ZIP from:

👉 https://github.com/OGbilboswagins/ComfyAI/releases

Extract into `ComfyUI/custom_nodes/ComfyAI` and restart.

---

## 🧭 Basic Usage

1. Start ComfyUI
2. Click the **ComfyAI** button in the left sidebar (above the Queue tab)
3. The chat panel will slide in from the left
4. Use the input at the bottom to chat with the selected model
5. Click the ⚙️ **settings icon** in the footer to open the fullscreen settings panel
6. Configure your theme, auto-scroll, streaming, default provider and (eventually) per-mode defaults

---

## 🗺 Roadmap

See [ROADMAP.md](ROADMAP.md) for a living roadmap. Highlights:

- [x] Floating chat panel with streaming  
- [x] Backend provider + settings APIs  
- [x] Fullscreen settings UI with tabs  
- [ ] Mode selector (Chat / Plan / Edit)  
- [ ] Per-mode model defaults and behavior knobs  
- [ ] MCP tools integration  
- [ ] Workflow rewrite and automation helpers  
- [ ] Deeper integration with ComfyUI’s queue and workflow graph  

---

## 🤝 Contributing

Pull requests, issues, and ideas are very welcome.

- Read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines  
- Check [ROADMAP.md](ROADMAP.md) and [ISSUES](https://github.com/OGbilboswagins/ComfyAI/issues) for ideas  
- If you build something cool on top of ComfyAI, please share it!

---

## ❤️ Support & Sponsorship

If ComfyAI makes your workflow better, consider supporting its development:

- **GitHub Sponsors:** https://github.com/sponsors/OGbilboswagins  
- **PayPal Tips:** https://paypal.me/ogbilboswaggins  

Even small recurring sponsorships help justify time spent building new features, testing changes with ComfyUI updates, and keeping docs up to date.

---

## 🔐 Security

Please do **not** disclose security issues publicly.  
See [SECURITY.md](SECURITY.md) for how to report vulnerabilities responsibly.

---

## 📜 License

ComfyAI is released under the **MIT License**.  
See [LICENSE](LICENSE) for full details.

---

<!--
SEO Keywords for search engines:

ComfyAI, Comfy UI AI Assistant, ComfyUI chat panel, ComfyUI plugin, AI copilot for ComfyUI,
Ollama ComfyUI, OpenAI ComfyUI integration, Gemini ComfyUI, MCP ComfyUI, ComfyUI LLM,
AI workflow assistant, ComfyUI custom node, ComfyUI Manager plugin, Continue.dev alternative
-->
