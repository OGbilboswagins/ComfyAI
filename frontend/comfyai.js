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
    await sleep(250);  // <-- This is the key line!

    await loadChatPanel();

    // 🔧 FORCE reflow after HTML + CSS are applied
    chatPanel.getBoundingClientRect();
}

// --------------------------------------------------------
// Fetch providers from backend
// --------------------------------------------------------
async function fetchProviders() {
    try {
        const res = await fetch("/comfyai/providers");
        if (!res.ok) throw new Error("HTTP " + res.status);

        const data = await res.json();
        comfyAIProviders = data.providers || {};
        // Fallback default from provider config (single default flag)
        comfyAIDefaultProvider = data.default_provider || null;

        console.log("[ComfyAI] Providers loaded:", data);
    } catch (err) {
        console.error("[ComfyAI] Error loading providers:", err);
    }
}

// --------------------------------------------------------
// Fetch settings (Option-3 schema) and override defaults
// --------------------------------------------------------
async function fetchSettings() {
    try {
        const res = await fetch("/comfyai/settings");
        if (!res.ok) throw new Error("HTTP " + res.status);

        const data = await res.json();
        comfyAISettings = data;

        if (data.defaults && data.defaults.chat_model) {
            comfyAIDefaultProvider = data.defaults.chat_model;
        }

        console.log("[ComfyAI] Settings loaded:", data);
    } catch (err) {
        console.error("[ComfyAI] Error loading settings:", err);
    }
}

// --------------------------------------------------------
// Populate model dropdown
// --------------------------------------------------------
async function populateModelDropdown() {
    if (!modelDropdown) return;

    modelDropdown.innerHTML = "";

    for (const [name, prov] of Object.entries(comfyAIProviders)) {
        const opt = document.createElement("option");
        opt.value = name;
        opt.textContent = `${prov.model} (${name})`;

        if (name === comfyAIDefaultProvider) {
            opt.selected = true;
        }

        modelDropdown.appendChild(opt);
    }

    console.log("[ComfyAI] Model dropdown updated.");
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
        console.log(`[ComfyAI][DEBUG] Loop ${i}, found ${groups.length} sidebar groups`);

        if (groups.length === 0) {
            await sleep(150);
            continue;
        }

        // Dump each group to see what’s inside
        groups.forEach((g, idx) => {
            console.log(`[ComfyAI][DEBUG] group[${idx}] innerHTML:\n`, g.innerHTML.substring(0, 200));
        });

        let targetGroup = null;
        for (const g of groups) {
            if (g.querySelector(".queue-tab-button")) {
                targetGroup = g;
                break;
            }
        }

        if (!targetGroup) {
            console.log("[ComfyAI][DEBUG] No group contains queue-tab-button yet, retrying...");
            await sleep(150);
            continue;
        }

        console.log("[ComfyAI][DEBUG] Found group containing queue-tab-button:", targetGroup);

        const queueBtn = targetGroup.querySelector(".queue-tab-button");
        if (!queueBtn) {
            console.log("[ComfyAI][DEBUG] queue-tab-button vanished? retrying...");
            await sleep(150);
            continue;
        }

        console.log("[ComfyAI][DEBUG] queueBtn = ", queueBtn);

        // Button already inserted?
        if (document.getElementById("comfyai-sidebar-button")) {
            console.log("[ComfyAI][DEBUG] Button already exists, skipping injection.");
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

    console.error("[ComfyAI][DEBUG] FAILED: insertSidebarButton() exhausted all retries");
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

    // 1. Load providers + settings (order matters)
    await fetchProviders();
    await fetchSettings();

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
