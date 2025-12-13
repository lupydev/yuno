import { DashboardAdmin } from "@/components/dashboards/DashboardAdmin";
import { DashboardClient } from "@/components/dashboards/DashboardClient";
import { useAuth } from "@/contexts/useAuth";
import { Navigate } from "react-router-dom";

export const DashboardPage = () => {
    const { role, isAuthenticated } = useAuth();

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }

    if (role === "ADMIN") {
        return <DashboardAdmin />;
    }

    if (role === "CLIENT") {
        return <DashboardClient />;
    }

    return <Navigate to="/login" replace />;
};
