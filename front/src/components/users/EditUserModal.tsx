import React from 'react';
import { X } from 'lucide-react';

interface User {
    id: string;
    name?: string;
    email: string;
    team?: string;
    role: string;
    status?: string;
}

interface EditUserModalProps {
    user: User;
    teams: string[];
    onClose: () => void;
    onSave: (user: User) => void;
}

export const EditUserModal: React.FC<EditUserModalProps> = ({
    user,
    teams,
    onClose,
    onSave
}) => {
    const [formData, setFormData] = React.useState({
        name: user.name || '',
        email: user.email,
        team: user.team || '',
        status: user.status || 'active'
    });

    const handleSubmit = () => {
        if (!formData.name || !formData.email || !formData.team) {
            alert('Por favor completa todos los campos');
            return;
        }
        onSave({
            ...user,
            ...formData
        });
    };

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-md shadow-2xl">
                <div className="flex items-center justify-between p-6 border-b border-slate-800">
                    <h2 className="text-xl font-bold text-white">Editar Usuario</h2>
                    <button
                        onClick={onClose}
                        className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                <div className="p-6 space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            Nombre <span className="text-red-400">*</span>
                        </label>
                        <input
                            type="text"
                            value={formData.name}
                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:border-blue-600"
                            placeholder="Nombre del usuario"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            Email <span className="text-red-400">*</span>
                        </label>
                        <input
                            type="email"
                            value={formData.email}
                            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                            className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:border-blue-600"
                            placeholder="email@ejemplo.com"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            Equipo <span className="text-red-400">*</span>
                        </label>
                        <select
                            value={formData.team}
                            onChange={(e) => setFormData({ ...formData, team: e.target.value })}
                            className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:border-blue-600"
                        >
                            <option value="">Selecciona un equipo</option>
                            {teams.map(team => (
                                <option key={team} value={team}>{team}</option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            Estado <span className="text-red-400">*</span>
                        </label>
                        <div className="flex items-center gap-4 p-3 bg-slate-800 border border-slate-700 rounded-lg">
                            <button
                                type="button"
                                onClick={() => setFormData({ ...formData, status: 'active' })}
                                className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
                                    formData.status === 'active'
                                        ? 'bg-emerald-600 text-white'
                                        : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
                                }`}
                            >
                                Activo
                            </button>
                            <button
                                type="button"
                                onClick={() => setFormData({ ...formData, status: 'inactive' })}
                                className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
                                    formData.status === 'inactive'
                                        ? 'bg-red-600 text-white'
                                        : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
                                }`}
                            >
                                Inactivo
                            </button>
                        </div>
                        <p className="text-slate-500 text-xs mt-2">
                            Los usuarios inactivos no pueden acceder al sistema
                        </p>
                    </div>

                    <div className="flex gap-3 pt-4">
                        <button
                            onClick={onClose}
                            className="flex-1 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg font-medium transition-colors"
                        >
                            Cancelar
                        </button>
                        <button
                            onClick={handleSubmit}
                            className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
                        >
                            Guardar Cambios
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
