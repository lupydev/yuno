import React, { useState, useEffect } from "react";
import apiBackClient from "../services/apiBackClient";
import { UserActionButtons } from "../components/users/UserActionButtons";
import { UserFilters } from "../components/users/UserFilters";
import { UsersTable } from "../components/users/UsersTable";
import { EditUserModal } from "../components/users/EditUserModal";
import { DeleteConfirmModal } from "../components/users/DeleteConfirmModal";
import { ChangeTeamModal } from "../components/users/ChangeTeamModal";
import { CreateTeamModal } from "../components/users/CreateTeamModal";
import { CreateUserModal } from "../components/users/CreateUserModal";
import { TeamsManagement } from "../components/users/TeamsManagement";

interface User {
    id: string;
    email: string;
    role: string;
    name?: string;
    team?: string;
    status?: string;
    createdAt?: string;
}

export const UsersPage: React.FC = () => {
    const [users, setUsers] = useState<User[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string>("");
    const [searchTerm, setSearchTerm] = useState("");
    const [selectedTeam, setSelectedTeam] = useState<string | null>(null);
    const [teams, setTeams] = useState<string[]>([]);
    const [editingUser, setEditingUser] = useState<User | null>(null);
    const [deletingUserId, setDeletingUserId] = useState<string | null>(null);
    const [changingTeamUser, setChangingTeamUser] = useState<User | null>(null);
    const [showCreateTeam, setShowCreateTeam] = useState(false);
    const [showCreateUser, setShowCreateUser] = useState(false);

    useEffect(() => {
        fetchUsers();
        fetchTeams();
    }, []);

    const fetchUsers = async () => {
        try {
            setIsLoading(true);
            const response = await apiBackClient.get("/users/");
            // Mapear datos del backend al formato esperado
            const mappedUsers = response.data.map((user: any) => ({
                id: user.id,
                name: user.name || 'No name',
                email: user.email,
                team: user.team_id || 'No team',
                role: user.role,
                // Map is_active (boolean) from backend to status (string) in frontend
                status: user.is_active ? 'active' : 'inactive',
                createdAt: user.created_at
            }));
            setUsers(mappedUsers);
            setError("");
        } catch (err) {
            console.error("Error loading users:", err);
            setError("Error loading users");
        } finally {
            setIsLoading(false);
        }
    };

    const fetchTeams = async () => {
        try {
            const response = await apiBackClient.get("/teams/names/all");
            // El endpoint devuelve directamente un array de strings
            setTeams(response.data);
        } catch (err) {
            console.error("Error al cargar equipos:", err);
            // Fallback a equipos por defecto en caso de error
            setTeams([]);
        }
    };

    // Filtrar usuarios
    const filteredUsers = users.filter(user => {
        const matchesSearch = !searchTerm || 
            user.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
            user.email.toLowerCase().includes(searchTerm.toLowerCase());
        
        const matchesTeam = !selectedTeam || user.team === selectedTeam;
        
        return matchesSearch && matchesTeam;
    });

    const handleCreateGroup = () => {
        setShowCreateTeam(true);
    };

    const handleCreateDeveloper = () => {
        setShowCreateUser(true);
    };

    const handleSaveTeam = async (name: string) => {
        try {
            await apiBackClient.post("/teams/", { name });
            await fetchTeams();
            setShowCreateTeam(false);
            // Trigger para refrescar la tabla de equipos
            window.dispatchEvent(new Event('teamsUpdated'));
        } catch (err: any) {
            console.error('Error creating team:', err);
            alert(err.response?.data?.detail || 'Error creating team');
            throw err;
        }
    };

    const handleCreateUser = async (userData: any) => {
        try {
            await apiBackClient.post("/users/", userData);
            await fetchUsers();
            setShowCreateUser(false);
        } catch (err: any) {
            console.error('Error creating user:', err);
            alert(err.response?.data?.detail || 'Error creating user');
            throw err;
        }
    };

    const handleEditUser = (user: User) => {
        setEditingUser(user);
    };

    const handleSaveUser = async (updatedUser: User) => {
        try {
            // Construir objeto solo con campos que cambiaron
            const updateData: any = {};
            
            const originalUser = users.find(u => u.id === updatedUser.id);
            if (!originalUser) return;

            if (updatedUser.name !== originalUser.name) {
                updateData.name = updatedUser.name;
            }
            if (updatedUser.email !== originalUser.email) {
                updateData.email = updatedUser.email;
            }
            // El rol siempre es DEVELOPER para developers
            updateData.role = 'DEVELOPER';
            
            if (updatedUser.team !== originalUser.team) {
                if (updatedUser.team && updatedUser.team !== 'Sin equipo') {
                    updateData.team_id = updatedUser.team;
                } else {
                    updateData.team_id = null;
                }
            }
            if (updatedUser.status !== originalUser.status) {
                updateData.is_active = updatedUser.status === 'active';
            }

            await apiBackClient.patch(`/users/${updatedUser.id}`, updateData);
            await fetchUsers();
            setEditingUser(null);
        } catch (err: any) {
            console.error('Error updating user:', err);
            alert(err.response?.data?.detail || 'Error updating user');
        }
    };

    const handleDeleteUser = (userId: string) => {
        setDeletingUserId(userId);
    };

    const confirmDelete = async () => {
        if (!deletingUserId) return;
        try {
            await apiBackClient.delete(`/users/${deletingUserId}`);
            await fetchUsers();
            setDeletingUserId(null);
        } catch (err: any) {
            console.error('Error deleting user:', err);
            alert(err.response?.data?.detail || 'Error deleting user');
        }
    };

    const handleChangeTeam = (user: User) => {
        setChangingTeamUser(user);
    };

    const confirmChangeTeam = async (newTeam: string) => {
        if (!changingTeamUser) return;
        try {
            await apiBackClient.patch(`/users/${changingTeamUser.id}`, { team_id: newTeam });
            await fetchUsers();
            setChangingTeamUser(null);
        } catch (err: any) {
            console.error('Error changing team:', err);
            alert(err.response?.data?.detail || 'Error changing team');
        }
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-full">
                <p className="text-lg text-white">Loading users...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center h-full">
                <p className="text-lg text-red-400">{error}</p>
            </div>
        );
    }

    return (
        <div className="p-8 max-w-[1800px] mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-white">User Management</h1>
                    <p className="text-slate-400 mt-1">Manage users, teams and assignments</p>
                </div>
                <UserActionButtons 
                    onCreateGroup={handleCreateGroup}
                    onCreateDeveloper={handleCreateDeveloper}
                />
            </div>

            {/* Filtros */}
            <div className="mb-6">
                <UserFilters
                    searchTerm={searchTerm}
                    onSearchChange={setSearchTerm}
                    selectedTeam={selectedTeam}
                    onTeamChange={setSelectedTeam}
                    teams={teams}
                />
            </div>

            {/* Tabla de usuarios */}
            <UsersTable
                users={filteredUsers}
                onEdit={handleEditUser}
                onDelete={handleDeleteUser}
                onChangeTeam={handleChangeTeam}
            />

            {/* Gestión de Equipos */}
            <div className="mt-8">
                <TeamsManagement />
            </div>

            {/* Estadísticas */}
            <div className="grid grid-cols-3 gap-4 mt-6">
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                    <div className="text-slate-400 text-sm font-medium mb-1">Total Users</div>
                    <div className="text-2xl font-bold text-white">{users.length}</div>
                </div>
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                    <div className="text-slate-400 text-sm font-medium mb-1">Active Users</div>
                    <div className="text-2xl font-bold text-emerald-400">
                        {users.filter(u => u.status === 'active').length}
                    </div>
                </div>
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                    <div className="text-slate-400 text-sm font-medium mb-1">Teams</div>
                    <div className="text-2xl font-bold text-indigo-400">
                        {new Set(users.map(u => u.team).filter(Boolean)).size}
                    </div>
                </div>
            </div>

            {/* Modales */}
            {editingUser && (
                <EditUserModal
                    user={editingUser}
                    teams={teams}
                    onClose={() => setEditingUser(null)}
                    onSave={handleSaveUser}
                />
            )}

            {deletingUserId && (
                <DeleteConfirmModal
                    userName={users.find(u => u.id === deletingUserId)?.name || 'this user'}
                    onConfirm={confirmDelete}
                    onCancel={() => setDeletingUserId(null)}
                />
            )}

            {changingTeamUser && (
                <ChangeTeamModal
                    userName={changingTeamUser.name || changingTeamUser.email}
                    currentTeam={changingTeamUser.team || 'No team'}
                    teams={teams}
                    onConfirm={confirmChangeTeam}
                    onCancel={() => setChangingTeamUser(null)}
                />
            )}

            {showCreateTeam && (
                <CreateTeamModal
                    onClose={() => setShowCreateTeam(false)}
                    onSave={handleSaveTeam}
                />
            )}

            {showCreateUser && (
                <CreateUserModal
                    teams={teams}
                    fixedRole="DEVELOPER"
                    onClose={() => setShowCreateUser(false)}
                    onSave={handleCreateUser}
                />
            )}
        </div>
    );
};
