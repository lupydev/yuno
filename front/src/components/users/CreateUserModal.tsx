import React from 'react';
import { X, UserPlus } from 'lucide-react';

interface CreateUserModalProps {
    teams: string[];
    onClose: () => void;
    onSave: (userData: {
        email: string;
        name: string;
        password: string;
        role: string;
        team_id?: string;
    }) => void;
    fixedRole?: string; // Si se provee, el rol es fijo y no editable
}

export const CreateUserModal: React.FC<CreateUserModalProps> = ({
    teams,
    onClose,
    onSave,
    fixedRole = 'DEVELOPER' // Por defecto DEVELOPER
}) => {
    const [formData, setFormData] = React.useState({
        email: '',
        name: '',
        password: '',
        confirmPassword: '',
        role: fixedRole,
        team_id: ''
    });
    const [isSubmitting, setIsSubmitting] = React.useState(false);

    const handleSubmit = async () => {
        // Validaciones
        if (!formData.email || !formData.name || !formData.password) {
            alert('Please complete all required fields');
            return;
        }

        if (formData.password !== formData.confirmPassword) {
            alert('Passwords do not match');
            return;
        }

        if (formData.password.length < 8) {
            alert('Password must be at least 8 characters');
            return;
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(formData.email)) {
            alert('Por favor ingresa un email válido');
            return;
        }

        setIsSubmitting(true);
        try {
            const userData: any = {
                email: formData.email,
                name: formData.name,
                password: formData.password,
                role: formData.role
            };

            // Solo agregar team_id si se seleccionó uno
            if (formData.team_id) {
                userData.team_id = formData.team_id;
            }

            await onSave(userData);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-md shadow-2xl max-h-[90vh] overflow-y-auto">
                <div className="flex items-center justify-between p-6 border-b border-slate-800 sticky top-0 bg-slate-900 z-10">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-500/10 rounded-lg">
                            <UserPlus className="w-6 h-6 text-blue-400" />
                        </div>
                        <h2 className="text-xl font-bold text-white">Create User</h2>
                    </div>
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
                            Full Name <span className="text-red-400">*</span>
                        </label>
                        <input
                            type="text"
                            value={formData.name}
                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            placeholder="e.g. John Doe"
                            className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-600"
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
                            placeholder="email@example.com"
                            className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-600"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            Password <span className="text-red-400">*</span>
                        </label>
                        <input
                            type="password"
                            value={formData.password}
                            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                            placeholder="Minimum 8 characters"
                            className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-600"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            Confirm Password <span className="text-red-400">*</span>
                        </label>
                        <input
                            type="password"
                            value={formData.confirmPassword}
                            onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                            placeholder="Repeat the password"
                            className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-600"
                        />
                    </div>

                    {/* Solo mostrar selector de rol si no está fijo */}
                    {!fixedRole && (
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                Role <span className="text-red-400">*</span>
                            </label>
                            <select
                                value={formData.role}
                                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                                className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:border-indigo-600"
                            >
                                <option value="CLIENT">Client</option>
                                <option value="DEVELOPER">Developer</option>
                                <option value="TEAM_LEADER">Team Leader</option>
                            </select>
                            <p className="text-slate-500 text-xs mt-1">
                                Select the user's role in the system
                            </p>
                        </div>
                    )}

                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            Team (optional)
                        </label>
                        <select
                            value={formData.team_id}
                            onChange={(e) => setFormData({ ...formData, team_id: e.target.value })}
                            className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:border-indigo-600"
                        >
                            <option value="">No team assigned</option>
                            {teams.map(team => (
                                <option key={team} value={team}>{team}</option>
                            ))}
                        </select>
                        <p className="text-slate-500 text-xs mt-1">
                            You can assign a team later
                        </p>
                    </div>

                    <div className="flex gap-3 pt-4">
                        <button
                            onClick={onClose}
                            disabled={isSubmitting}
                            className="flex-1 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg font-medium transition-colors disabled:opacity-50"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handleSubmit}
                            disabled={isSubmitting}
                            className="flex-1 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isSubmitting ? 'Creating...' : 'Create User' }
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
