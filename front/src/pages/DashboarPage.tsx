import DashboardAdmin from "@/components/dashboards/DashboardAdmin";
import { useAuth } from "@/contexts/useAuth";
import { Navigate } from "react-router-dom";

export const DashboardPage = () => {
    const { role, isAuthenticated } = useAuth();

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }

    if (role === "ADMIN" || role === "DEVELOPER") {
        return <DashboardAdmin />;
    }

    return <Navigate to="/login" replace />;
};
