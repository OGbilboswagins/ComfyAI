console.log("[ComfyAI] comfyai.js loaded");

async function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

// --------------------------------------------------------
// Global state
// --------------------------------------------------------
let comfyAIProviders = {};
let comfyAIDefaultProvider = null;
let comfyAISettings = null;

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
function appendMessage(role, markdown) {
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
    const div = document.createElement("div");
    const roleClass = role === "user" ? "comfyai-user" : "comfyai-assistant";
    div.className = `comfyai-msg ${roleClass}`;

    // Render markdown → HTML
    if (window.marked && markdown) {
        div.innerHTML = marked.parse(markdown);
    } else if (markdown) {
        div.textContent = markdown;
    }

    msgArea.appendChild(div);
    msgArea.scrollTop = msgArea.scrollHeight;

    saveHistory();
    return div;
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
    container.querySelectorAll(".comfyai-msg").forEach((msg) => {
        let role = "assistant";
        if (msg.classList.contains("comfyai-user")) role = "user";
        if (msg.classList.contains("comfyai-assistant")) role = "assistant";

        history.push({
            role,
            html: msg.innerHTML,
        });
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
        appendMessage(m.role, m.content || m.html || "");
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
            appendMessage("assistant", `[ERROR] HTTP ${res.status}: ${errText}`);
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
                data.error ? `[ERROR] ${data.error}` : data.reply
            );

            return;
        }

        // --- Streaming mode ---
        const reader = res.body.getReader();
        const decoder = new TextDecoder();

        // Remove typing indicator and create real assistant bubble
        if (typingDiv) typingDiv.remove();
        const assistantDiv = appendMessage("assistant", "");
        if (!assistantDiv) return;

        let accumulated = "";

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            accumulated += chunk;

            if (window.marked) {
                assistantDiv.innerHTML = marked.parse(accumulated);
            } else {
                assistantDiv.textContent = accumulated;
            }

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
// Load chat.html into the floating panel
// --------------------------------------------------------
async function loadChatPanel() {
    try {
        const res = await fetch("/extensions/ComfyAI/frontend/chat.html");
        if (!res.ok) throw new Error("HTTP " + res.status);

        const html = await res.text();
        chatPanel.innerHTML = html;

        console.log("[ComfyAI] Chat panel loaded");

        modelDropdown = document.getElementById("comfyai-model-dropdown");
        await populateModelDropdown();
        loadHistory();

        // Hook send button
        const sendBtn = document.getElementById("comfyai-send-button");
        if (sendBtn) {
            sendBtn.addEventListener("click", sendMessage);
        }

        const input = document.getElementById("comfyai-input");
        if (input) {
            input.addEventListener("keydown", (e) => {
                if (e.key === "Enter") {
                    if (e.shiftKey) {
                        // Insert newline instead of sending
                        return;
                    }
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

        console.log("[ComfyAI][DEBUG] Creating button…");

        sidebarButton = document.createElement("button");
        sidebarButton.id = "comfyai-sidebar-button";
        sidebarButton.type = "button";

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
                <img src="/extensions/ComfyAI/frontend/icon.svg"
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
