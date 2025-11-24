(() => {
    console.log("[ComfyAI] comfyai.js loaded");

    const BASE = "/extensions/ComfyAI/frontend";

    async function loadChatPanel() {
        if (document.getElementById("comfyai-chat-panel")) return;

        try {
            const resp = await fetch(`${BASE}/chat.html`);
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const html = await resp.text();
            const t = document.createElement("template");
            t.innerHTML = html.trim();
            document.body.appendChild(t.content);

            setupChatBehavior();
            console.log("[ComfyAI] Chat panel loaded");
        } catch (err) {
            console.error("[ComfyAI] Failed to load chat.html:", err);
        }
    }

    function setupChatBehavior() {
        const closeBtn = document.getElementById("comfyai-close-button");
        const panel = document.getElementById("comfyai-chat-panel");
        const dropdown = document.getElementById("comfyai-model-dropdown");

        closeBtn?.addEventListener("click", () => {
            panel.classList.remove("open");
        });

        fetchProviders(dropdown);
    }

    window.toggleChatPanel = function () {
        const panel = document.getElementById("comfyai-chat-panel");
        if (!panel) {
            loadChatPanel().then(() => {
                document.getElementById("comfyai-chat-panel").classList.add("open");
            });
            return;
        }
        panel.classList.toggle("open");
    };

    async function fetchProviders(select) {
        try {
            const resp = await fetch("/comfyai/providers");
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const providers = await resp.json();
            select.innerHTML = "";

            for (const key in providers) {
                if (!providers[key]?.model) continue;
                const opt = document.createElement("option");
                opt.value = providers[key].model;
                opt.textContent = `${key}: ${providers[key].model}`;
                select.appendChild(opt);
            }

        } catch (err) {
            console.error("[ComfyAI] Error loading providers:", err);
            select.innerHTML = `<option>Error loading models</option>`;
        }
    }

    function injectSidebarButton() {
        const group = document.querySelector("div.sidebar-item-group");
        if (!group) return setTimeout(injectSidebarButton, 300);

        const queue = group.querySelector(".queue-tab-button");
        if (!queue) return setTimeout(injectSidebarButton, 300);

        if (document.getElementById("comfyai-sidebar-button")) return;

        const btn = document.createElement("button");
        btn.id = "comfyai-sidebar-button";
        btn.type = "button";

        /* REQUIRED PrimeVue + Vue hydration metadata */
        btn.setAttribute("data-v-c90a38ba", "");
        btn.setAttribute("data-v-d92ba606", "");
        btn.setAttribute("data-pc-section", "root");
        btn.setAttribute("data-pc-name", "button");
        btn.setAttribute("data-p-disabled", "false");
        btn.setAttribute("data-pd-tooltip", "true");
        btn.setAttribute("aria-label", "ComfyAI");

        /* EXACT same classes */
        btn.className =
            "p-button p-component p-button-icon-only p-button-text side-bar-button p-button-secondary comfyai-tab-button";

        /* Internal structure */
        btn.innerHTML = `
            <div data-v-c90a38ba="" class="side-bar-button-content">
                <img src="${BASE}/icon.svg"
                    class="side-bar-button-icon comfyai-sidebar-icon"
                    style="width:18px;height:18px;" />
                <span data-v-c90a38ba="" class="side-bar-button-label">ComfyAI</span>
            </div>
            <span class="p-button-label" data-pc-section="label">&nbsp;</span>
        `;




        btn.addEventListener("click", () => {
            console.log("[ComfyAI] Sidebar button clicked → toggle panel");
            window.toggleChatPanel();
        });

        group.insertBefore(btn, queue);
        console.log("[ComfyAI] ComfyAI button injected above Queue");
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", injectSidebarButton);
    } else {
        injectSidebarButton();
    }
})();
