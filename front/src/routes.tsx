import { Routes, Route } from 'react-router-dom';
import { DashboardLayout } from './components/dashboards/DashboardsLayout';
import DashboardAdmin from './components/dashboards/DashboardAdmin';
import UsersView from './components/UsersView';
import TransactionReport from "@/components/ReportData";
import { Login } from './pages/LoginPage';

export const AppRoutes = () => {
    return (
        <Routes>
            <Route path="/login" element={<Login />} />

            <Route
                path="/dashboard"
                element={
                    <DashboardLayout>
                        <DashboardAdmin />
                    </DashboardLayout>
                }
            />

            <Route
                path="/reports"
                element={
                    <DashboardLayout>
                        <TransactionReport />
                    </DashboardLayout>
                }
            />

            <Route
                path="/users"
                element={
                    <DashboardLayout>
                        <UsersView />
                    </DashboardLayout>
                }
            />

            {/* Redirect unknown routes */}
            <Route path="*" element={<DashboardLayout><DashboardAdmin /></DashboardLayout>} />
        </Routes>
    );
};