import { ComfyAISettings } from "/extensions/ComfyAI/frontend/settings.js";

console.log("[ComfyAI] comfyai.js loaded");

// ------------------------------------------------------------
// Ensure comfyai.css is loaded globally
// ------------------------------------------------------------
(function injectComfyAICSS() {
    const href = "/extensions/ComfyAI/frontend/comfyai.css";

    // Prevent duplicate injection
    if (document.querySelector(`link[href="${href}"]`)) return;

    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);

    console.log("[ComfyAI] Injected comfyai.css");
})();

async function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

// --------------------------------------------------------
// Global state
// --------------------------------------------------------
let comfyAIProviders = {};
let comfyAIDefaultProvider = null;
let comfyAISettings = null;
let lastMetaExpanded = false;
let currentMode = "chat";
let modelOverride = false;

let sidebarButton = null;
let chatPanel = null;
let modelDropdown = null;

// ========================================================
// Chat helpers (Markdown + bubbles + history)
// ========================================================

/**
 * Append a user/assistant message bubble.
 * role: "user" | "assistant"
 * markdown: content in markdown/plain text
 */
function appendMessage(role, markdown, modelName = null, mode = null) {
    const msgArea = document.getElementById("comfyai-messages");
    if (!msgArea) return null;

    // --- TYPING INDICATOR BUBBLE ---
    if (role === "typing") {
        const typing = document.createElement("div");
        typing.className = "comfyai-typing";
        typing.innerHTML = `
            <span class="comfyai-dot"></span>
            <span class="comfyai-dot"></span>
            <span class="comfyai-dot"></span>
        `;
        msgArea.appendChild(typing);
        msgArea.scrollTop = msgArea.scrollHeight;
        return typing;
    }

    // --- NORMAL MESSAGE BUBBLES ---
    if (role === "user") {
        const div = document.createElement("div");
        div.className = `comfyai-msg comfyai-user`;
        div.textContent = markdown;
        msgArea.appendChild(div);
        msgArea.scrollTop = msgArea.scrollHeight;
        saveHistory();
        return div;
    }

    // --- ASSISTANT MESSAGE WITH METADATA ---
    const wrapper = document.createElement("div");
    wrapper.className = "comfyai-msg-wrapper assistant";

    const bubble = document.createElement("div");
    bubble.className = "comfyai-msg comfyai-assistant";

    const content = document.createElement("div");
    content.className = "comfyai-msg-content";

    const meta = document.createElement("div");
    const isHidden = comfyAISettings?.show_metadata === false ? "hidden" : "";
    const isCollapsed = lastMetaExpanded ? "" : "collapsed";
    meta.className = `comfyai-msg-meta ${isCollapsed} ${isHidden}`;

    const modeIcon = document.createElement("span");
    modeIcon.className = `mode-icon ${mode || "chat"}`;

    const MODE_LABELS = {
        chat: "Chat mode",
        plan: "Plan mode",
        edit: "Edit mode",
    };
    modeIcon.title = MODE_LABELS[mode || "chat"] || (mode || "chat");

    const modelSpan = document.createElement("span");
    modelSpan.className = "model-name";
    modelSpan.title = modelName || "Unknown Model";
    modelSpan.textContent = modelName || "Unknown Model";

    const expanded = document.createElement("div");
    expanded.className = `meta-expanded ${lastMetaExpanded ? "" : "hidden"}`;
    // future MCP/tool UI will go here

    meta.appendChild(modeIcon);
    meta.appendChild(modelSpan);
    meta.appendChild(expanded);

    bubble.appendChild(content);
    bubble.appendChild(meta);

    const controls = document.createElement("div");
    controls.className = "comfyai-msg-controls";

    const copyBtn = document.createElement("button");
    copyBtn.className = "meta-copy";
    copyBtn.innerHTML = `<img src="/extensions/ComfyAI/frontend/icons/copy.svg">`;
    copyBtn.title = "Copy raw message";
    copyBtn.onclick = (e) => {
        e.stopPropagation();
        const textToCopy = bubble.dataset.rawText;
        if (textToCopy) {
            navigator.clipboard.writeText(textToCopy).then(() => {
                copyBtn.classList.add("copied");
                setTimeout(() => copyBtn.classList.remove("copied"), 1500);
            });
        }
    };

    const toggleBtn = document.createElement("button");
    toggleBtn.className = "meta-toggle";
    toggleBtn.innerHTML = `<img src="/extensions/ComfyAI/frontend/icons/metadata.svg">`;
    toggleBtn.title = "Toggle Metadata";
    toggleBtn.onclick = (e) => {
        e.stopPropagation();
        lastMetaExpanded = !lastMetaExpanded;
        
        // Update all existing bubbles? No, just this one for now, 
        // but new ones will inherit. Actually, the requirement says 
        // "The next assistant message inherits the previous expand/collapse state."
        // So we only update this one and the global state.
        
        meta.classList.toggle("collapsed", !lastMetaExpanded);
        expanded.classList.toggle("hidden", !lastMetaExpanded);
    };

    controls.appendChild(copyBtn);
    controls.appendChild(toggleBtn);

    wrapper.appendChild(bubble);
    wrapper.appendChild(controls);

    if (markdown) {
        if (window.marked) {
            content.innerHTML = marked.parse(markdown);
        } else {
            content.textContent = markdown;
        }
        bubble.dataset.rawText = markdown;
    }

    msgArea.appendChild(wrapper);
    msgArea.scrollTop = msgArea.scrollHeight;

    saveHistory();
    return content; // Return content div so streaming can update it
}

/**
 * Create typing indicator (3 animated dots).
 * Returns the wrapper element so we can remove it later.
 */
function showTypingIndicator() {
    const msgArea = document.getElementById("comfyai-messages");
    if (!msgArea) return null;

    const wrap = document.createElement("div");
    wrap.className = "comfyai-typing";

    for (let i = 0; i < 3; i++) {
        const dot = document.createElement("div");
        dot.className = "comfyai-dot";
        wrap.appendChild(dot);
    }

    msgArea.appendChild(wrap);
    msgArea.scrollTo({
        top: msgArea.scrollHeight,
        behavior: "smooth",
    });

    return wrap;
}

function buildChatMessage() {
    const txt = document.getElementById("comfyai-input");
    return txt ? txt.value.trim() : "";
}

// ========================================================
// Local history storage and persistence
// (stores rendered HTML so markdown survives reload)
// ========================================================
function saveHistory() {
    const container = document.getElementById("comfyai-messages");
    if (!container) return;

    const history = [];
    // We need to find all messages, including wrapped ones
    container.querySelectorAll(".comfyai-msg").forEach((msg) => {
        let role = "assistant";
        if (msg.classList.contains("comfyai-user")) {
            role = "user";
            history.push({
                role,
                raw: msg.textContent,
            });
        } else if (msg.classList.contains("comfyai-assistant")) {
            role = "assistant";
            // For assistant messages, we want the model and mode too
            const meta = msg.querySelector(".comfyai-msg-meta");
            const modelName = msg.querySelector(".model-name")?.textContent || "";
            const mode = msg.querySelector(".mode-icon")?.classList[1] || "chat";
            
            history.push({
                role,
                raw: msg.dataset.rawText || "",
                modelName,
                mode
            });
        }
    });

    localStorage.setItem("comfyai-chat-history", JSON.stringify(history));
}

function loadHistory() {
    const container = document.getElementById("comfyai-messages");
    if (!container) return;

    const raw = localStorage.getItem("comfyai-chat-history");
    if (!raw) return;

    let history = [];
    try {
        history = JSON.parse(raw);
    } catch {
        history = [];
    }

    history.forEach((m) => {
        appendMessage(m.role, m.raw || "", m.modelName, m.mode);
    });
}

// ========================================================
// Send message + streaming + typing indicator
// ========================================================
async function sendMessage() {
    const text = buildChatMessage();
    if (!text) return;

    const inputEl = document.getElementById("comfyai-input");
    if (inputEl) inputEl.value = "";

    // Show user's message
    appendMessage("user", text);

    const dropdown = document.getElementById("comfyai-model-dropdown");
    if (!dropdown || !dropdown.value) {
        appendMessage("assistant", "[ERROR] No model selected.");
        return;
    }

    const value = dropdown.value; // "provider::model"
    const [provider_id, model_name] = value.split("::");
    
    const modeSelect = document.getElementById("comfyai-mode-select");
    const currentMode = modeSelect ? modeSelect.value : "chat";

    const payload = {
        provider: provider_id,
        model: model_name,
        messages: [{ role: "user", content: text }],
    };

    // Typing indicator (three dots, no text)
    const typingDiv = showTypingIndicator();

    try {
        const res = await fetch("/api/comfyai/chat/stream", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        // If streaming is not available, fallback to non-streaming
        if (!res.ok) {
            if (typingDiv) typingDiv.remove();
            const errText = await res.text();
            appendMessage("assistant", `[ERROR] HTTP ${res.status}: ${errText}`, model_name, currentMode);
            return;
        }

        if (!res.body || !res.body.getReader) {
            // No streaming → fallback
            if (typingDiv) typingDiv.remove();

            const res2 = await fetch("/api/comfyai/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });

            const data = await res2.json();

            appendMessage(
                "assistant",
                data.error ? `[ERROR] ${data.error}` : data.reply,
                model_name,
                currentMode
            );

            return;
        }

        // --- Streaming mode ---
        const reader = res.body.getReader();
        const decoder = new TextDecoder();

        // Remove typing indicator and create real assistant bubble
        // assistantContentDiv is the .comfyai-msg-content element
        let assistantContentDiv = null;
        if (typingDiv) typingDiv.remove();
        assistantContentDiv = appendMessage("assistant", "", model_name, currentMode); 
        if (!assistantContentDiv) return;

        // Get the bubble element (parent of content)
        const assistantBubble = assistantContentDiv.parentElement;

        let accumulated = "";

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            accumulated += chunk;

            if (window.marked) {
                assistantContentDiv.innerHTML = marked.parse(accumulated);
            } else {
                assistantContentDiv.textContent = accumulated;
            }

            assistantBubble.dataset.rawText = accumulated;

            const msgArea = document.getElementById("comfyai-messages");
            if (msgArea) {
                msgArea.scrollTo({
                    top: msgArea.scrollHeight,
                    behavior: "smooth",
                });
            }
        }

        saveHistory();

    } catch (err) {
        if (typingDiv) typingDiv.remove();
        appendMessage("assistant", "[NETWORK ERROR] " + err);
    }
}

// --------------------------------------------------------
// Centralized model selection for mode switching
// --------------------------------------------------------
function applyModelForMode(mode, { force = false } = {}) {
    if (!comfyAISettings) return;

    if (!force && modelOverride) return;

    const targetModel = comfyAISettings.default_models?.[mode];

    if (!targetModel) {
        console.warn(`[ComfyAI] No default model for mode: ${mode}`);
        return;
    }

    const dropdown = document.getElementById("comfyai-model-dropdown");
    if (!dropdown) return;

    const exists = [...dropdown.options].some((o) => o.value === targetModel);
    if (!exists) {
        console.warn(
            `[ComfyAI] Default model not found in dropdown: ${targetModel}`
        );
        return;
    }

    dropdown.value = targetModel;
}

// --------------------------------------------------------
// Add mode icon
// --------------------------------------------------------
const COMFYAI_MODE_ICON_MAP = {
    chat: "/extensions/ComfyAI/frontend/icons/mode-chat.svg",
    plan: "/extensions/ComfyAI/frontend/icons/mode-plan.svg",
    edit: "/extensions/ComfyAI/frontend/icons/mode-edit.svg",
};

function applyComfyAIModeIcon(mode) {
    const select = document.getElementById("comfyai-mode-select");
    if (!select) return;

    const icon = COMFYAI_MODE_ICON_MAP[mode];
    if (icon) {
        select.style.backgroundImage = `url("${icon}")`;
    } else {
        select.style.backgroundImage = "none";
    }
}

// --------------------------------------------------------
// Load and apply mode
// --------------------------------------------------------
async function loadAndApplyComfyAIMode() {
    try {
        const settings = await ComfyAISettings.fetch();
        comfyAISettings = settings; // Update global state

        const select = document.getElementById("comfyai-mode-select");
        if (!select) return;

        const newMode = settings.mode || "chat";
        currentMode = newMode;
        select.value = newMode;
        applyComfyAIModeIcon(newMode);
    } catch (err) {
        console.error("[ComfyAI] Failed to load mode:", err);
    }
}

// --------------------------------------------------------
// Save mode on change
// --------------------------------------------------------
async function bindComfyAIModeSelector() {
    const select = document.getElementById("comfyai-mode-select");
    if (!select) return;

    select.addEventListener("change", async (e) => {
        const newMode = e.target.value;

        if (newMode === currentMode) {
            modelOverride = false;
            applyModelForMode(newMode, { force: true });
        } else {
            currentMode = newMode;
            applyModelForMode(newMode);
        }

        try {
            await ComfyAISettings.save({ mode: newMode });
            applyComfyAIModeIcon(newMode);
        } catch (err) {
            console.error("[ComfyAI] Failed to save mode:", err);
        }
    });
}

// --------------------------------------------------------
// Load chat.html into the floating panel
// --------------------------------------------------------
async function loadChatPanel() {
    try {
        const res = await fetch("/extensions/ComfyAI/frontend/chat.html");
        if (!res.ok) throw new Error("HTTP " + res.status);

        const html = await res.text();
        chatPanel.innerHTML = html;

        console.log("[ComfyAI] Chat panel loaded");

        await loadAndApplyComfyAIMode();
        bindComfyAIModeSelector();

        // ------------------------------------------------------
        // SETTINGS PANEL EVENT BINDINGS (HTML only, no logic)
        // ------------------------------------------------------
        const settingsPanel = document.getElementById("comfyai-settings-panel");
        if (settingsPanel) {
            const closeBtn = settingsPanel.querySelector("#comfyai-settings-close");

            if (closeBtn) {
                console.log("[ComfyAI] Close button found — binding handler");
                closeBtn.addEventListener("click", () => {
                    console.log("[ComfyAI] Close button clicked");
                    if (typeof window.__comfyaiCloseSettings === "function") {
                        window.__comfyaiCloseSettings();
                    }
                });
            } else {
                console.warn("[ComfyAI] Close button NOT found in settings panel markup");
            }
        }

        modelDropdown = document.getElementById("comfyai-model-dropdown");
        if (modelDropdown) {
            modelDropdown.addEventListener("change", () => {
                modelOverride = true;
            });
        }
        await populateModelDropdown();
        applyModelForMode(currentMode);
        loadHistory();

        const sendBtn = document.getElementById("comfyai-send-button");
        if (sendBtn) sendBtn.addEventListener("click", sendMessage);

        const input = document.getElementById("comfyai-input");
        if (input) {
            input.addEventListener("keydown", (e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });
        }

    } catch (err) {
        console.error("[ComfyAI] ERROR loading chat panel:", err);
    }
}

// --------------------------------------------------------
// Setup floating chat panel container WITH SAFE DELAY
// --------------------------------------------------------
async function createChatPanel() {
    chatPanel = document.createElement("div");
    chatPanel.id = "comfyai-chat-panel";
    chatPanel.classList.remove("open");
    document.body.appendChild(chatPanel);

    // 🔥 FIX: Wait for Vue/PrimeVue layout to fully settle before loading HTML
    // This removes the "2-piece panel" bug.
    await sleep(250); // <-- This is the key line!

    await loadChatPanel();

    // 🔧 FORCE reflow after HTML + CSS are applied
    chatPanel.getBoundingClientRect();
}

// --------------------------------------------------------
// Fetch providers from backend
// --------------------------------------------------------
async function fetchProviders() {
    try {
        const res = await fetch("/api/comfyai/providers");
        if (!res.ok) throw new Error("HTTP " + res.status);

        const data = await res.json();
        comfyAIProviders = data.providers || {};

        console.log("[ComfyAI] Providers loaded:", comfyAIProviders);
    } catch (err) {
        console.error("[ComfyAI] Error loading providers:", err);
    }
}

// --------------------------------------------------------
// Populate model dropdown
// --------------------------------------------------------
async function populateModelDropdown() {
    if (!modelDropdown) return;

    modelDropdown.innerHTML = "";

    for (const [provider_id, prov] of Object.entries(comfyAIProviders)) {
        const optgroup = document.createElement("optgroup");
        optgroup.label = prov.name || provider_id;

        try {
            const res = await fetch(`/api/comfyai/models?provider=${provider_id}`);
            if (!res.ok) throw new Error("HTTP " + res.status);

            const models = await res.json();

            for (const m of models) {
                const opt = document.createElement("option");

                // Use provider::model so we know which provider was chosen
                opt.value = `${provider_id}::${m.name}`;
                opt.textContent = m.display_name || m.name;

                optgroup.appendChild(opt);
            }
        } catch (err) {
            console.error(
                `[ComfyAI] Failed to load models for ${provider_id}:`,
                err
            );
        }

        modelDropdown.appendChild(optgroup);
    }

    console.log("[ComfyAI] Model dropdown updated (grouped by provider).");
}

// --------------------------------------------------------
// Sidebar button → slide panel toggle
// --------------------------------------------------------
function togglePanel() {
    if (!chatPanel) return;
    chatPanel.classList.toggle("open");
}

// --------------------------------------------------------
// Inject sidebar button ABOVE Queue
// --------------------------------------------------------
async function insertSidebarButton() {
    console.log("[ComfyAI][DEBUG] insertSidebarButton() called");

    for (let i = 0; i < 50; i++) {
        const groups = document.querySelectorAll(".sidebar-item-group");
        console.log(
            `[ComfyAI][DEBUG] Loop ${i}, found ${groups.length} sidebar groups`
        );

        if (groups.length === 0) {
            await sleep(150);
            continue;
        }

        // Dump each group to see what’s inside
        groups.forEach((g, idx) => {
            console.log(
                `[ComfyAI][DEBUG] group[${idx}] innerHTML:\n`,
                g.innerHTML.substring(0, 200)
            );
        });

        let targetGroup = null;
        for (const g of groups) {
            if (g.querySelector(".queue-tab-button")) {
                targetGroup = g;
                break;
            }
        }

        if (!targetGroup) {
            console.log(
                "[ComfyAI][DEBUG] No group contains queue-tab-button yet, retrying..."
            );
            await sleep(150);
            continue;
        }

        console.log(
            "[ComfyAI][DEBUG] Found group containing queue-tab-button:",
            targetGroup
        );

        const queueBtn = targetGroup.querySelector(".queue-tab-button");
        if (!queueBtn) {
            console.log(
                "[ComfyAI][DEBUG] queue-tab-button vanished? retrying..."
            );
            await sleep(150);
            continue;
        }

        console.log("[ComfyAI][DEBUG] queueBtn = ", queueBtn);

        // Button already inserted?
        if (document.getElementById("comfyai-sidebar-button")) {
            console.log(
                "[ComfyAI][DEBUG] Button already exists, skipping injection."
            );
            return;
        }

        if (!document.getElementById("comfyai-sidebar-button")) {
            console.log("[ComfyAI][DEBUG] Creating button…");
            sidebarButton = document.createElement("button");
            sidebarButton.id = "comfyai-sidebar-button";
            sidebarButton.type = "button";
        }


        window.addEventListener("DOMContentLoaded", () => {
            if (
                sidebarButton &&
                !document.getElementById("comfyai-sidebar-button")
            ) {
                sidebarContainer.appendChild(sidebarButton);
            }
        });



        /* REQUIRED PrimeVue + Vue hydration metadata */
        sidebarButton.setAttribute("data-v-c90a38ba", "");
        sidebarButton.setAttribute("data-v-d92ba606", "");
        sidebarButton.setAttribute("data-pc-section", "root");
        sidebarButton.setAttribute("data-pc-name", "button");
        sidebarButton.setAttribute("data-p-disabled", "false");
        sidebarButton.setAttribute("data-pd-tooltip", "true");
        sidebarButton.setAttribute("aria-label", "ComfyAI");

        sidebarButton.className =
            "p-button p-component p-button-icon-only p-button-text side-bar-button p-button-secondary comfyai-tab-button";
        sidebarButton.innerHTML = `
            <div class="side-bar-button-content">
                <img src="/extensions/ComfyAI/frontend/icons/sidebar-icon.svg"
                class="side-bar-button-icon comfyai-sidebar-icon"
                style="width:18px;height:18px;">
                <span class="side-bar-button-label">ComfyAI</span>
            </div>
            <span class="p-button-label">&nbsp;</span>
        `;

        sidebarButton.addEventListener("click", () => {
            console.log("[ComfyAI][DEBUG] ComfyAI button clicked");
            togglePanel();
        });

        console.log("[ComfyAI][DEBUG] Inserting button ABOVE queueBtn…");

        try {
            targetGroup.insertBefore(sidebarButton, queueBtn);
            console.log("[ComfyAI] Button injection SUCCESS");
        } catch (err) {
            console.error("[ComfyAI][DEBUG] insertBefore failed:", err);
        }

        return;
    }

    console.error(
        "[ComfyAI][DEBUG] FAILED: insertSidebarButton() exhausted all retries"
    );
}

// --------------------------------------------------------
// Initialize ComfyAI
// --------------------------------------------------------
async function initComfyAI() {
    console.log("[ComfyAI] Initializing...");

    // 🔥 FIX — Remove old/duplicate chat panels if they exist
    const existing = document.getElementById("comfyai-chat-panel");
    if (existing) {
        console.warn("[ComfyAI] Removing duplicate chat panel…");
        existing.remove();
    }

    // 1. Load providers
    await fetchProviders();

    // 2. Insert the sidebar button
    await insertSidebarButton();

    // 3. Create the floating chat panel (creates EXACTLY ONE)
    await createChatPanel();
}

if (document.readyState === "loading") {
    window.addEventListener("DOMContentLoaded", () => {
        console.log("[ComfyAI] DOMContentLoaded fired");
        initComfyAI();
    });
} else {
    console.log("[ComfyAI] DOM already loaded → init immediately");
    initComfyAI();
}

// -------------------------------
// SETTINGS HELPERS
// -------------------------------
async function loadComfyAISettings() {
    const res = await fetch("/api/comfyai/settings");
    const data = await res.json();
    comfyAISettings = data || {};
    return comfyAISettings;
}

async function saveComfyAISettings(data) {
    return fetch("/api/comfyai/settings", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(data)
    });
}

// =====================================================
// WAIT FOR THE COMFYAI CHAT PANEL TO APPEAR
// =====================================================
const comfyAIObserver = new MutationObserver(() => {
    const panel = document.getElementById("comfyai-chat-panel");
    if (!panel) return;

    const chatWindow = panel.querySelector("#comfyai-chat-window");
    const settingsPanel = panel.querySelector("#comfyai-settings-panel");
    const settingsButton = panel.querySelector("#comfyai-settings-button");

    if (!chatWindow || !settingsPanel || !settingsButton) return;

    console.log("[ComfyAI] Chat panel detected — installing settings handlers");
    comfyAIObserver.disconnect();

    // Sidebar + tabs
    const sidebarItems = settingsPanel.querySelectorAll(".sidebar-item");
    const tabs = settingsPanel.querySelectorAll(".settings-tab");

    function activateTab(tabName) {
        sidebarItems.forEach(i =>
            i.classList.toggle("active", i.dataset.tab === tabName)
        );
        tabs.forEach(t =>
            t.classList.toggle("hidden", t.id !== `tab-${tabName}`)
        );
    }

    sidebarItems.forEach(item => {
        item.onclick = () => activateTab(item.dataset.tab);
    });

    let settingsOpen = false;

    async function openSettings() {
        settingsOpen = true;
        chatWindow.style.display = "none";
        settingsPanel.classList.remove("hidden");

        const settings = await loadComfyAISettings();

        panel.querySelector("#cai-theme").value = settings.theme ?? "dark";
        panel.querySelector("#cai-autoscroll").checked = settings.auto_scroll ?? true;
        panel.querySelector("#cai-streaming").checked = settings.streaming ?? true;
        panel.querySelector("#cai-system-prompt").value = settings.system_prompt ?? "";
        panel.querySelector("#cai-temperature").value = settings.defaults?.temperature ?? 0.7; // Access temperature from defaults
        panel.querySelector("#cai-markdown").checked = settings.markdown ?? true;
        panel.querySelector("#cai-show-metadata").checked = settings.show_metadata ?? true;
        panel.querySelector("#cai-dev-mode").checked = settings.dev_mode ?? false;

        await populateProviderAndModelsUI(panel, settings);
        activateTab("general");
    }

    function closeSettings() {
        settingsOpen = false;
        settingsPanel.classList.add("hidden");
        chatWindow.style.display = "flex";
    }

    function toggleSettings() {
        settingsOpen ? closeSettings() : openSettings();
    }

    // 🔑 expose canonical controls
    window.__comfyaiCloseSettings = closeSettings;
    window.__comfyaiToggleSettings = toggleSettings;

    settingsButton.onclick = toggleSettings;

    const resetBtn = panel.querySelector("#cai-reset-settings");
    if (resetBtn) {
        resetBtn.onclick = async () => {
            comfyAISettings = {
                theme: "dark",
                auto_scroll: true,
                streaming: true,
                default_provider: Object.keys(comfyAIProviders)[0] || null,
                default_models: { chat: "", plan: "", edit: "" }
            };
            await saveComfyAISettings(comfyAISettings);
            openSettings();
        };
    }

    const saveBtn = panel.querySelector("#cai-save-settings");
    if (saveBtn) {
        saveBtn.onclick = async () => {
            if (!comfyAISettings) comfyAISettings = {};

            comfyAISettings.theme = panel.querySelector("#cai-theme").value;
            comfyAISettings.auto_scroll = panel.querySelector("#cai-autoscroll").checked;
            comfyAISettings.streaming = panel.querySelector("#cai-streaming").checked;
            comfyAISettings.system_prompt = panel.querySelector("#cai-system-prompt").value;
            comfyAISettings.markdown = panel.querySelector("#cai-markdown").checked;
            comfyAISettings.show_metadata = panel.querySelector("#cai-show-metadata").checked;
            comfyAISettings.dev_mode = panel.querySelector("#cai-dev-mode").checked;

            comfyAISettings.default_provider =
                panel.querySelector("#cai-default-provider").value || null;

            // Ensure defaults object exists
            if (!comfyAISettings.defaults) comfyAISettings.defaults = {};
            comfyAISettings.defaults.temperature =
                parseFloat(panel.querySelector("#cai-temperature").value) || 0.7;

            comfyAISettings.default_models = {
                chat: panel.querySelector("#cai-model-chat").value || "",
                plan: panel.querySelector("#cai-model-plan").value || "",
                edit: panel.querySelector("#cai-model-edit").value || ""
            };

            await saveComfyAISettings(comfyAISettings);
            modelOverride = false;
            applyModelForMode(currentMode, { force: true });
            closeSettings();
        };
    }
});

// Helper to populate provider + model dropdowns in Providers tab (READ-ONLY)
async function populateProviderAndModelsUI(panel, settings) {
    // Always resolve from the actual settings panel
    const settingsPanel =
        panel?.querySelector?.("#comfyai-settings-panel") ||
        document.getElementById("comfyai-settings-panel");

    if (!settingsPanel) {
        console.warn("[ComfyAI][Settings] settings panel not found");
        return;
    }

    const providerSelect = settingsPanel.querySelector("#cai-default-provider");
    const modelChatSelect = settingsPanel.querySelector("#cai-model-chat");
    const modelPlanSelect = settingsPanel.querySelector("#cai-model-plan");
    const modelEditSelect = settingsPanel.querySelector("#cai-model-edit");

    if (!providerSelect || !modelChatSelect || !modelPlanSelect || !modelEditSelect) {
        console.warn("[ComfyAI][Settings] One or more selects not found", {
            providerSelect,
            modelChatSelect,
            modelPlanSelect,
            modelEditSelect
        });
        return;
    }

    // Fetch providers
    const provRes = await fetch("/api/comfyai/providers");
    if (!provRes.ok) {
        console.error("[ComfyAI][Settings] Failed to fetch providers");
        return;
    }

    const provData = await provRes.json();
    const providers = provData.providers || {};
    const providerIds = Object.keys(providers);

    // Clear selects
    providerSelect.innerHTML = "";
    modelChatSelect.innerHTML = "";
    modelPlanSelect.innerHTML = "";
    modelEditSelect.innerHTML = "";

    // Populate provider dropdown
    for (const pid of providerIds) {
        const opt = document.createElement("option");
        opt.value = pid;
        opt.textContent = providers[pid].name || pid;
        providerSelect.appendChild(opt);
    }

    // Select default provider
    if (settings?.default_provider && providerIds.includes(settings.default_provider)) {
        providerSelect.value = settings.default_provider;
    } else if (providerIds.length > 0) {
        providerSelect.value = providerIds[0];
    }

    // Load models for selected provider
    async function loadModelsForProvider(pid) {
        modelChatSelect.innerHTML = "";
        modelPlanSelect.innerHTML = "";
        modelEditSelect.innerHTML = "";

        try {
            const res = await fetch(`/api/comfyai/models?provider=${pid}`);
            if (!res.ok) return;

            const models = await res.json();

            for (const m of models) {
                const value = `${pid}::${m.name}`;
                const label = `${pid}: ${m.display_name || m.name}`;

                [modelChatSelect, modelPlanSelect, modelEditSelect].forEach(sel => {
                    const opt = document.createElement("option");
                    opt.value = value;
                    opt.textContent = label;
                    sel.appendChild(opt);
                });
            }
        } catch (err) {
            console.error("[ComfyAI][Settings] Failed to load models", err);
        }
    }

    // Initial load
    if (providerSelect.value) {
        await loadModelsForProvider(providerSelect.value);
    }

    // Reload when provider changes
    providerSelect.addEventListener("change", () => {
        loadModelsForProvider(providerSelect.value);
    });

    // Apply default models
    const dm = settings?.default_models || {};
    if (dm.chat) modelChatSelect.value = dm.chat;
    if (dm.plan) modelPlanSelect.value = dm.plan;
    if (dm.edit) modelEditSelect.value = dm.edit;
}

comfyAIObserver.observe(document.body, { childList: true, subtree: true });
