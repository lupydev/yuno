import { Routes, Route, Navigate } from "react-router-dom";
import { Login } from "./pages/LoginPage.tsx";
import DashboardAdmin from "./components/dashboards/DashboardAdmin.tsx";
import { ReportsPage } from "./pages/ReportsPage.tsx";

export const AppRoutes = () => {
    return (
        <Routes>
            <Route path="*" element={<Navigate to="/dashboard" />} />
            <Route path="/" element={<Navigate to="/dashboard" />} />
            <Route path="/login" element={<Login />} />
            <Route path="/dashboard" element={<DashboardAdmin />} />
            <Route path="/reports" element={<ReportsPage />} />


        </Routes>
    );
};
