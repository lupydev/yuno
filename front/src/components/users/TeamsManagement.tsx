import React, { useState, useEffect } from 'react';
import { Users, Edit2, Trash2 } from 'lucide-react';
import apiBackClient from '../../services/apiBackClient';
import { EditTeamModal } from './EditTeamModal';
import { DeleteConfirmModal } from './DeleteConfirmModal';

interface Team {
    name: string;
    created: string;
}

export const TeamsManagement: React.FC = () => {
    const [teams, setTeams] = useState<Team[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [editingTeam, setEditingTeam] = useState<Team | null>(null);
    const [deletingTeam, setDeletingTeam] = useState<string | null>(null);

    useEffect(() => {
        fetchTeams();
        
        // Escuchar evento de actualización de equipos
        const handleTeamsUpdated = () => {
            fetchTeams();
        };
        
        window.addEventListener('teamsUpdated', handleTeamsUpdated);
        return () => window.removeEventListener('teamsUpdated', handleTeamsUpdated);
    }, []);

    const fetchTeams = async () => {
        try {
            setIsLoading(true);
            const response = await apiBackClient.get('/teams/');
            setTeams(response.data);
        } catch (err) {
            console.error('Error al cargar equipos:', err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleEditTeam = async (oldName: string, newName: string) => {
        try {
            await apiBackClient.patch(`/teams/${oldName}`, { name: newName });
            await fetchTeams();
            setEditingTeam(null);
            window.dispatchEvent(new Event('teamsUpdated'));
        } catch (err: any) {
            console.error('Error al actualizar equipo:', err);
            alert(err.response?.data?.detail || 'Error al actualizar el equipo');
            throw err;
        }
    };

    const handleDeleteTeam = async () => {
        if (!deletingTeam) return;
        try {
            await apiBackClient.delete(`/teams/${deletingTeam}`);
            await fetchTeams();
            setDeletingTeam(null);
            window.dispatchEvent(new Event('teamsUpdated'));
        } catch (err: any) {
            console.error('Error al eliminar equipo:', err);
            alert(err.response?.data?.detail || 'Error al eliminar el equipo. Asegúrate de que no tenga developers asignados.');
        }
    };

    if (isLoading) {
        return (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-8">
                <p className="text-slate-400 text-center">Cargando equipos...</p>
            </div>
        );
    }

    return (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
            <div className="p-4 border-b border-slate-800">
                <h3 className="text-base font-semibold text-white flex items-center gap-2">
                    <Users className="w-4 h-4" />
                    Equipos Existentes
                </h3>
                <p className="text-slate-400 text-xs mt-1">
                    {teams.length} equipo{teams.length !== 1 ? 's' : ''} registrado{teams.length !== 1 ? 's' : ''}
                </p>
            </div>

            <div className="overflow-x-auto max-h-80 overflow-y-auto">
                <table className="w-full">
                    <thead className="bg-slate-800/50 sticky top-0">
                        <tr>
                            <th className="px-4 py-2 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                                Nombre del Equipo
                            </th>
                            <th className="px-4 py-2 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                                Fecha de Creación
                            </th>
                            <th className="px-4 py-2 text-right text-xs font-semibold text-slate-300 uppercase tracking-wider">
                                Acciones
                            </th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                        {teams.map((team) => (
                            <tr key={team.name} className="hover:bg-slate-800/30 transition-colors">
                                <td className="px-4 py-2 whitespace-nowrap">
                                    <span className="text-sm font-medium text-white">{team.name}</span>
                                </td>
                                <td className="px-4 py-2 whitespace-nowrap">
                                    <span className="text-sm text-slate-300">
                                        {new Date(team.created).toLocaleDateString()}
                                    </span>
                                </td>
                                <td className="px-4 py-2 whitespace-nowrap text-right">
                                    <div className="flex items-center justify-end gap-2">
                                        <button
                                            onClick={() => setEditingTeam(team)}
                                            className="p-1.5 text-slate-400 hover:text-blue-400 hover:bg-slate-800 rounded-lg transition-colors"
                                            title="Editar equipo"
                                        >
                                            <Edit2 className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={() => setDeletingTeam(team.name)}
                                            className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded-lg transition-colors"
                                            title="Eliminar equipo"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {teams.length === 0 && (
                <div className="text-center py-8">
                    <Users className="w-10 h-10 text-slate-600 mx-auto mb-2" />
                    <p className="text-slate-400 text-sm">No hay equipos registrados</p>
                </div>
            )}

            {editingTeam && (
                <EditTeamModal
                    team={editingTeam}
                    onClose={() => setEditingTeam(null)}
                    onSave={handleEditTeam}
                />
            )}

            {deletingTeam && (
                <DeleteConfirmModal
                    userName={`el equipo "${deletingTeam}"`}
                    onConfirm={handleDeleteTeam}
                    onCancel={() => setDeletingTeam(null)}
                />
            )}
        </div>
    );
};
