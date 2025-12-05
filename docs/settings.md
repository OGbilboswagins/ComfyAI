# Settings & Configuration

ComfyAI stores its persistent user settings in a JSON file located at:

```text
COMFYUI_ROOT/user/default/ComfyUI-ComfyAI/settings.json
```

These settings are managed by the backend `SettingsManager` and surfaced via:

- `GET /api/comfyai/settings`
- `POST /api/comfyai/settings`

## Current Settings

As of `v0.3.0`, the settings JSON may look like:

```json
{
  "theme": "dark",
  "auto_scroll": true,
  "streaming": true,
  "default_provider": "ollama",
  "default_models": {
    "chat": "ollama::qwen2.5:7b-instruct-fp16",
    "plan": "google::gemini-2.5-flash",
    "edit": "openai::gpt-4.1"
  }
}
```

### Fields

- `theme`  
  `"dark"` or `"light"`. Controls the UI theme inside the chat panel.

- `auto_scroll`  
  If `true`, the chat view will auto-scroll to the latest message.

- `streaming`  
  If `true`, the chat uses streaming responses (chunked tokens).  
  If `false`, it falls back to non-streaming `/chat` endpoint.

- `default_provider`  
  Which provider is selected by default when the panel opens.

- `default_models.chat / plan / edit`  
  Per-mode model selection for the upcoming mode system.

## Editing Settings

You can change settings in three ways:

1. **Via the Settings Panel (recommended)**  
   - Click the settings icon in the bottom-right of the chat panel.
   - Use the sidebar icons to switch tabs.
   - Adjust theme, behavior, provider, and models.
   - Click **Save Settings**.

2. **Via the HTTP API**  
   - `GET /api/comfyai/settings` to inspect the current JSON.
   - `POST /api/comfyai/settings` with a JSON body to override parts of it.

3. **Via direct file edit**  
   - Manually edit `user/default/ComfyUI-ComfyAI/settings.json` while ComfyUI is shut down.
   - Restart ComfyUI to reload.

## Resetting Settings

To reset settings:

1. Stop ComfyUI.
2. Delete `settings.json` from `user/default/ComfyUI-ComfyAI/`.
3. Restart ComfyUI.
4. The backend will recreate settings with defaults when the UI or API loads them.
