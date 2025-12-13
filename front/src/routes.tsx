import { Routes, Route, Navigate } from "react-router-dom";
import { ProtectedRoute } from "./components/ProtectedRoute.tsx";
import { Login } from "./pages/LoginPage.tsx";
import { DashboardPage } from "./pages/DashboarPage.tsx";
import { ReportsPage } from "./pages/ReportsPage.tsx";
import { DashboardLayout } from "./components/dashboards/DashboardsLayout.tsx";

export const AppRoutes = () => {
    return (
        <Routes>
            <Route path="*" element={<Navigate to="/login" />} />
            <Route path="/" element={<Navigate to="/login" />} />
            <Route path="/login" element={<Login />} />

            <Route element={<DashboardLayout />}>
                <Route
                    element={
                        <ProtectedRoute allowedRoles={["ADMIN", "CLIENT"]} />
                    }
                >
                    <Route path="/dashboard" element={<DashboardPage />} />
                    <Route path="/reports" element={<ReportsPage />} />
                </Route>
            </Route>

        </Routes>
    );
};
