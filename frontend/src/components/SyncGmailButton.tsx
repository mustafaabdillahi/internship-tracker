import { useState } from "react";

const API_URL = import.meta.env.VITE_API_URL;

function SyncGmailButton() {
    const [message, setMessage] = useState("");
    const [loading, setLoading] = useState(false);

    async function syncGmail() {
        setLoading(true);
        setMessage("");

        try {
            const response = await fetch(`${API_URL}/gmail/sync`, {
                method: "POST",
                credentials: "include"
            });

            const data = await response.json();
            if(!response.ok) {
                setMessage(data.detail ?? "Something went wrong.");
                return;
            }

            setMessage(data.DEBUG);

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
                Sync emails
            </button>

            {message && <p>{message}</p>}
        </>
    )
}

export default SyncGmailButton;