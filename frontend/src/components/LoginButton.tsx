const API_URL = import.meta.env.VITE_API_URL;

function GoogleSignInButton() {
    const handleGoogleSignIn = () => {
        window.location.assign(`${API_URL}/auth/google/login`);
    };

    return (
        <button type="button" onClick={handleGoogleSignIn}>
            Sign in with Google
        </button>
    )
}

export default GoogleSignInButton;