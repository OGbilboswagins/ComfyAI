export class ComfyAISettings {
    static async fetch() {
        const res = await fetch("/api/comfyai/settings");
        if (!res.ok) throw new Error("Failed to fetch settings");
        return res.json();
    }

    static async save(data) {
        const res = await fetch("/api/comfyai/settings", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error("Failed to save settings");
        return res.json();
    }
}
