import { useQuery } from "@tanstack/react-query";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { getCurrentUser } from "../api/auth";

function ProtectedRoute() {
    const location = useLocation();

    const {
        data: user,
        isLoading,
        isError
    } = useQuery({
        queryKey: ["currentUser"],
        queryFn: getCurrentUser,
        retry: false
    });

    if(isLoading) {
        return <div>Checking authentication...</div>;
    }

    if(isError || !user) {
        return (
            <Navigate to="/login" replace state={{ from: location}} />
        );
    }

    return <Outlet />;
}

export default ProtectedRoute;