import { useState } from "react";
import apiClient from "../api/client";

function LogoutButton() {
    const [message, setMessage] = useState("");
    const [loading, setLoading] = useState(false);

    async function logOut() {
        setLoading(true);
        setMessage("");

        try {
            await apiClient.post("/auth/logout");
            window.location.href = "/login";

        } catch(error) {
            setMessage("Failed to connect to the server.");
            console.error("Logout error: " + error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            <button type="button" onClick={logOut} disabled={loading}>
                {loading ? "Logging out..." : "Log out"}
            </button>

            {message && <p>{message}</p>}
        </>
    )
}

export default LogoutButton;