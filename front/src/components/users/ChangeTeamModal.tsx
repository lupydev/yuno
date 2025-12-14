import React from 'react';
import { X, ArrowLeftRight } from 'lucide-react';

interface ChangeTeamModalProps {
    userName: string;
    currentTeam: string;
    teams: string[];
    onConfirm: (newTeam: string) => void;
    onCancel: () => void;
}

export const ChangeTeamModal: React.FC<ChangeTeamModalProps> = ({
    userName,
    currentTeam,
    teams,
    onConfirm,
    onCancel
}) => {
    const [selectedTeam, setSelectedTeam] = React.useState(currentTeam);

    const handleConfirm = () => {
        if (selectedTeam !== currentTeam) {
            onConfirm(selectedTeam);
        } else {
            onCancel();
        }
    };

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-md shadow-2xl">
                <div className="flex items-center justify-between p-6 border-b border-slate-800">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-indigo-500/10 rounded-lg">
                            <ArrowLeftRight className="w-5 h-5 text-indigo-400" />
                        </div>
                        <h2 className="text-xl font-bold text-white">Change Team</h2>
                    </div>
                    <button
                        onClick={onCancel}
                        className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                <div className="p-6">
                    <p className="text-slate-300 mb-2">
                        User: <span className="font-semibold text-white">{userName}</span>
                    </p>
                    <p className="text-slate-400 text-sm mb-4">
                        Current team: <span className="text-indigo-400 font-medium">{currentTeam}</span>
                    </p>

                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            Select new team
                        </label>
                        <select
                            value={selectedTeam}
                            onChange={(e) => setSelectedTeam(e.target.value)}
                            className="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:border-indigo-600"
                        >
                            {teams.map(team => (
                                <option key={team} value={team}>{team}</option>
                            ))}
                        </select>
                    </div>

                    <div className="flex gap-3 mt-6">
                        <button
                            onClick={onCancel}
                            className="flex-1 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg font-medium transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handleConfirm}
                            disabled={selectedTeam === currentTeam}
                            className="flex-1 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Change Team
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
