import { Routes, Route, Navigate } from "react-router-dom";
import { ProtectedRoute } from "./components/ProtectedRoute.tsx";
import { Login } from "./pages/LoginPage.tsx";
import { DashboardPage } from "./pages/DashboarPage.tsx";
import { ReportsPage } from "./pages/ReportsPage.tsx";
import { UsersPage } from "./pages/UsersPage.tsx";
import { DashboardLayout } from "./components/dashboards/DashboardsLayout.tsx";

export const AppRoutes = () => {
    return (
        <Routes>
            <Route path="/login" element={<Login />} />

            <Route element={<DashboardLayout />}>
                {/* Routes to ADMIN & DEVELOPER */}
                <Route
                    element={
                        <ProtectedRoute allowedRoles={["ADMIN", "DEVELOPER"]} />
                    }
                >
                    <Route path="/dashboard" element={<DashboardPage />} />
                    <Route path="/reports" element={<ReportsPage />} />
                </Route>

                {/* Routes only to ADMIN */}
                <Route
                    element={
                        <ProtectedRoute allowedRoles={["ADMIN"]} />
                    }
                >
                    <Route path="/users" element={<UsersPage />} />
                </Route>
            </Route>
            
            <Route path="/" element={<Navigate to="/login" replace />} />
            <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
    );
};
