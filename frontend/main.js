export class Extension {
    getName() {
        return "ComfyAI";
    }

    getDisplayName() {
        return "ComfyAI";
    }

    async setup(app) {
        console.log("[ComfyAI] Registering UI extension…");

        app.registerExtensionTab({
            id: "comfyai",
            name: "ComfyAI",
            icon: "/extensions/ComfyAI/frontend/icon.svg",

            render: (root) => {
                root.innerHTML = `
                    <div style="width:100%;height:100%;display:flex;flex-direction:column;">
                        <iframe 
                            src="/extensions/ComfyAI/frontend/chat.html"
                            style="width:100%;height:100%;border:none;background:#222;">
                        </iframe>
                    </div>
                `;
            }
        });

        console.log("[ComfyAI] Extension tab registered.");
    }
}
