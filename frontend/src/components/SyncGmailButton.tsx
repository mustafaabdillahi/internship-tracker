import { useState } from "react";
import apiClient from "../api/client";

function SyncGmailButton() {
    const [message, setMessage] = useState("");
    const [loading, setLoading] = useState(false);

    async function syncGmail() {
        setLoading(true);
        setMessage("");

        try {
            const response = await apiClient.post("/gmail/sync");
            setMessage(response.data.DEBUG);

        } catch(error) {
            setMessage("Failed to connect to the server.");
            console.error("Server connection error: " + error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            <button type="button" onClick={syncGmail} disabled={loading}>
                {loading ? "Syncing emails..." : "Sync emails"}
            </button>

            {message && <p>{message}</p>}
        </>
    )
}

export default SyncGmailButton;