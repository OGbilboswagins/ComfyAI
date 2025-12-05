<div align="center">
  <img src="https://raw.githubusercontent.com/OGbilboswagins/ComfyAI/main/assets/comfyai_logo.png" alt="ComfyAI Logo" width="260"/>

  <h1>ComfyAI</h1>
  <p><b>The intelligent AI assistant for ComfyUI.</b></p>

  <!-- Badges -->
  <p>
    <a href="https://github.com/OGbilboswagins/ComfyAI/stargazers">
      <img src="https://img.shields.io/github/stars/OGbilboswagins/ComfyAI?style=for-the-badge" alt="GitHub stars"/>
    </a>
    <a href="https://github.com/OGbilboswagins/ComfyAI/releases">
      <img src="https://img.shields.io/github/v/release/OGbilboswagins/ComfyAI?style=for-the-badge" alt="Latest release"/>
    </a>
    <a href="https://registry.comfy.org/node/ComfyUI-ComfyAI">
      <img src="https://registry.comfy.org/badge/ComfyUI-ComfyAI" alt="Available via ComfyUI Manager" style="height:28px;"/>
    </a>
    <a href="https://github.com/sponsors/OGbilboswagins">
      <img src="https://img.shields.io/badge/Sponsor-❤️%20Support%20Development-red?style=for-the-badge" alt="GitHub Sponsors"/>
    </a>
    <a href="https://paypal.me/ogbilboswaggins">
      <img src="https://img.shields.io/badge/PayPal-Donate-0070ba?style=for-the-badge&logo=paypal" alt="Donate via PayPal"/>
    </a>
  </p>

  <p>
    <img src="https://raw.githubusercontent.com/OGbilboswagins/ComfyAI/main/assets/ComfyAI.gif" alt="ComfyAI Demo" width="640"/>
  </p>
</div>

---

## ✨ What is ComfyAI?

**ComfyAI** is an intelligent assistant that lives <b>inside ComfyUI</b>.

It adds a slide-out chat panel with a clean, focused UI where you can:

- Chat with local or cloud LLMs directly inside ComfyUI
- Use a beautiful ChatGPT-style interface with bubbles and markdown
- Stream responses with a smooth typing indicator
- Pick providers and models from a dropdown
- Configure behavior via an integrated settings panel

ComfyAI is designed to become a **full workflow copilot** for ComfyUI:
chat, plan, and eventually edit workflows — not just talk.

---

## 🧠 Key Features

- 🗨️ **Embedded Chat Panel** — slides in from the left sidebar, like a native ComfyUI tool.
- 💬 **ChatGPT-Style Bubbles** — markdown support, code blocks, and clean message layout.
- ⚡ **Streaming Responses** — token-by-token streaming with 3-dot typing indicator.
- 🧩 **Multiple Providers** — Ollama (local), OpenAI, Google Gemini, and more via configuration.
- 🎛 **Settings Panel** — full-screen overlay with tabs:
  - General
  - Appearance (future)
  - Chat Behavior (future)
  - Providers & Models
  - Advanced
- 💾 **Persistent Settings** — stored under `user/default/ComfyUI-ComfyAI/settings.json`.
- 🧱 **Registry-Ready** — published via the ComfyUI Registry and installable via ComfyUI Manager.
- 🛠 **Extensible Design** — built to support plan/edit modes and workflow automation.

---

## 🚀 Roadmap (High-Level)

ComfyAI is just getting started.

- **v0.3.x** — Core chat experience, settings UI, provider management (current).
- **v0.4.x** — Optional web search, improved context, safety controls.
- **v0.5.x** — Chat / Plan / Edit modes and per-mode default models.
- **v0.6.x** — Workflow automation (read/modify workflows via AI).
- **v0.7.x+** — Tooling, MCP-style integrations, advanced automation.

See the full [Roadmap](docs/roadmap.md) for details.

---

## 📦 Installation

### 1. Via ComfyUI Manager (Recommended)

1. Open **ComfyUI Manager** inside ComfyUI.
2. Search for **"ComfyAI"**.
3. Click **Install** or **Update**.
4. Restart ComfyUI.

> ComfyAI is published to the official **ComfyUI Registry**, so Manager can detect and manage it automatically.

### 2. Manual Install (Git)

From your ComfyUI root directory:

```bash
cd custom_nodes
git clone https://github.com/OGbilboswagins/ComfyAI.git ComfyUI-ComfyAI
```

Then restart ComfyUI.

---

## 🧩 Usage

1. Start ComfyUI as usual.
2. Look for the **ComfyAI** button in the left sidebar.
3. Click it — the ComfyAI panel will slide in.
4. Select a provider + model from the dropdown.
5. Type your message and press **Enter** or click **Send**.
6. Open the settings panel via the ⚙️ button near the Send button to configure:
   - Theme
   - Auto-scroll
   - Streaming
   - Default provider
   - Default models per mode (chat/plan/edit, as they roll out)

---

## ⚙️ Configuration

ComfyAI stores settings in:

```text
COMFYUI_ROOT/user/default/ComfyUI-ComfyAI/settings.json
```

You can:

- Edit them via the **Settings** UI.
- Read/write via the HTTP API:
  - `GET /api/comfyai/settings`
  - `POST /api/comfyai/settings`
- Manually edit the JSON while ComfyUI is stopped.

See [docs/settings.md](docs/settings.md) for the detailed schema.

---

## 🤝 Contributing

Contributions of all kinds are welcome:

- Bug fixes
- New features (web search, tools, workflow automation)
- UI/UX improvements
- Docs and examples
- Provider integrations

Please see:

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- [SECURITY.md](SECURITY.md)

And feel free to start a conversation in:

- **Discussions** → https://github.com/OGbilboswagins/ComfyAI/discussions

---

## 🛡 Security & Privacy

- ComfyAI does not send data anywhere you haven’t configured.
- Local providers like **Ollama** keep data on your machine.
- Cloud providers (OpenAI, Gemini, etc.) depend on their privacy policies.
- API keys are stored in your local configuration and never hard-coded in the repo.

If you discover a security issue, please follow the process described in [SECURITY.md](SECURITY.md).

---

## ❤️ Support & Sponsorship

If ComfyAI saves you time, helps your workflow, or becomes part of your daily stack, please consider supporting its development:

- ⭐ Star the repo on GitHub  
- 💖 Sponsor via GitHub: https://github.com/sponsors/OGbilboswagins  
- ☕ Donate via PayPal: https://paypal.me/ogbilboswaggins  

Your support directly helps keep this project alive and evolving.

---

## 📜 License

ComfyAI is released under the **MIT License**.  
See [LICENSE](LICENSE) for details.
