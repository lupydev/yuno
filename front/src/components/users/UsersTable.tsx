import React from 'react';
import { Edit2, Trash2, Users as UsersIcon, ArrowLeftRight } from 'lucide-react';

interface User {
    id: string;
    name?: string;
    email: string;
    team?: string;
    role: string;
    status?: string;
}

interface UsersTableProps {
    users: User[];
    onEdit: (user: User) => void;
    onDelete: (userId: string) => void;
    onChangeTeam: (user: User) => void;
}

export const UsersTable: React.FC<UsersTableProps> = ({
    users,
    onEdit,
    onDelete,
    onChangeTeam
}) => {

    return (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
            <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
                <table className="w-full">
                    <thead className="bg-slate-800/50">
                        <tr>
                            <th className="px-6 py-4 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">ID</th>
                            <th className="px-6 py-4 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">Name</th>
                            <th className="px-6 py-4 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">Email</th>
                            <th className="px-6 py-4 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">Team</th>
                            <th className="px-6 py-4 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">Role</th>
                            <th className="px-6 py-4 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">Status</th>
                            <th className="px-6 py-4 text-right text-xs font-semibold text-slate-300 uppercase tracking-wider">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                        {users.map((user) => (
                            <tr key={user.id} className="hover:bg-slate-800/30 transition-colors">
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className="text-sm font-mono text-slate-400">{user.id}</span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className="text-sm font-medium text-white">{user.name || 'No name'}</span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className="text-sm text-slate-300">{user.email}</span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className="inline-flex px-3 py-1 text-xs font-semibold rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
                                        {user.team || 'No team'}
                                    </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className="text-sm text-slate-300">{user.role}</span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className={`inline-flex px-3 py-1 text-xs font-semibold rounded-full ${
                                        user.status === 'active'
                                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                            : 'bg-slate-500/10 text-slate-400 border border-slate-500/20'
                                    }`}>
                                        {user.status || 'inactive'}
                                    </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-right">
                                    <div className="flex items-center justify-end gap-2">
                                        {/* Cambio rápido de equipo */}
                                        <button
                                            onClick={() => onChangeTeam(user)}
                                            className="p-2 text-slate-400 hover:text-indigo-400 hover:bg-slate-800 rounded-lg transition-colors"
                                            title="Change team"
                                        >
                                            <ArrowLeftRight className="w-4 h-4" />
                                        </button>

                                        {/* Editar */}
                                        <button
                                            onClick={() => onEdit(user)}
                                            className="p-2 text-slate-400 hover:text-blue-400 hover:bg-slate-800 rounded-lg transition-colors"
                                            title="Edit user"
                                        >
                                            <Edit2 className="w-4 h-4" />
                                        </button>

                                        {/* Eliminar */}
                                        <button
                                            onClick={() => onDelete(user.id)}
                                            className="p-2 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded-lg transition-colors"
                                            title="Delete user"
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

            {users.length === 0 && (
                <div className="text-center py-12">
                    <UsersIcon className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                    <p className="text-slate-400">No users found</p>
                </div>
            )}
        </div>
    );
};
