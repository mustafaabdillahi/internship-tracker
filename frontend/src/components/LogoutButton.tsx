import { useState } from "react";

const API_URL = import.meta.env.VITE_API_URL;

function LogoutButton() {
    const [message, setMessage] = useState("");
    const [loading, setLoading] = useState(false);

    async function logOut() {
        setLoading(true);
        setMessage("");

        try {
            const response = await fetch(`${API_URL}/auth/logout`, {
                method: "POST",
                credentials: "include"
            });
            window.location.href = "/dashboard";

        } catch(error) {
            setMessage("Failed to connect to the server.");
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            <button type="button" onClick={logOut} disabled={loading}>
                Log out
            </button>

            {message && <p>{message}</p>}
        </>
    )
}

export default LogoutButton;