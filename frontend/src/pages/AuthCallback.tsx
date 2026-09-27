import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import apiClient from "../api/client";

function AuthCallback() {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const exchanged = useRef(false);

    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if(exchanged.current) {
            return;
        }
        
        exchanged.current = true;
        
        async function exchangeCode() {

            const code = searchParams.get("code");

            if(!code) {
                setError("Missing OAuth code");
                return;
            }

            try {
                const response = await apiClient.post(
                    "/auth/exchange",
                    { code }
                );

                localStorage.setItem("access_token", response.data.access_token);
                navigate("/dashboard", { replace: true });

            } catch(error) {
                console.error(error);
                setError("Login failed");
            }
        }

        exchangeCode();
    }, [searchParams, navigate]);

    if(error) {
        return <div>{error}</div>
    }

    return <div>Completing login...</div>;

}

export default AuthCallback;