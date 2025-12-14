import React from 'react';
import { Search, ChevronDown, X } from 'lucide-react';

interface UserFiltersProps {
    searchTerm: string;
    onSearchChange: (value: string) => void;
    selectedTeam: string | null;
    onTeamChange: (team: string | null) => void;
    teams: string[];
}

export const UserFilters: React.FC<UserFiltersProps> = ({
    searchTerm,
    onSearchChange,
    selectedTeam,
    onTeamChange,
    teams
}) => {
    const [showTeamDropdown, setShowTeamDropdown] = React.useState(false);

    const handleTeamSelect = (team: string) => {
        onTeamChange(selectedTeam === team ? null : team);
        setShowTeamDropdown(false);
    };

    const clearTeamFilter = (e: React.MouseEvent) => {
        e.stopPropagation();
        onTeamChange(null);
    };

    return (
        <div className="flex items-center gap-4">
            {/* Filtro por nombre */}
            <div className="flex-1 relative">
                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                    type="text"
                    placeholder="Search by name or email..."
                    value={searchTerm}
                    onChange={(e) => onSearchChange(e.target.value)}
                    className="w-full pl-12 pr-4 py-2.5 bg-slate-900 border border-slate-800 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-600"
                />
            </div>

            {/* Filtro por equipo */}
            <div className="relative min-w-[200px]">
                <button
                    onClick={() => setShowTeamDropdown(!showTeamDropdown)}
                    className={`w-full px-4 py-2.5 rounded-lg border text-sm font-medium transition-all flex items-center justify-between gap-2 ${
                        selectedTeam
                            ? 'bg-indigo-600 border-indigo-600 text-white'
                            : 'bg-slate-900 border-slate-800 text-slate-300 hover:border-slate-700'
                    }`}
                >
                    <span>{selectedTeam || 'Filter by team'}</span>
                    {selectedTeam ? (
                        <X
                            className="w-4 h-4"
                            onClick={clearTeamFilter}
                        />
                    ) : (
                        <ChevronDown className={`w-4 h-4 transition-transform ${showTeamDropdown ? 'rotate-180' : ''}`} />
                    )}
                </button>

                {showTeamDropdown && (
                    <div className="absolute top-full mt-2 left-0 right-0 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-50 py-1 max-h-64 overflow-y-auto">
                        {teams.map(team => (
                            <button
                                key={team}
                                onClick={() => handleTeamSelect(team)}
                                className={`w-full px-4 py-2 text-left text-sm transition-colors ${
                                    selectedTeam === team
                                        ? 'bg-indigo-600 text-white'
                                        : 'text-slate-300 hover:bg-slate-700'
                                }`}
                            >
                                {team}
                            </button>
                        ))}
                    </div>
                )}
            </div>

            {/* Clear filters */}
            {(searchTerm || selectedTeam) && (
                <button
                    onClick={() => {
                        onSearchChange('');
                        onTeamChange(null);
                    }}
                    className="px-4 py-2.5 text-sm text-slate-400 hover:text-white transition-colors whitespace-nowrap"
                >
                    Clear filters
                </button>
            )}
        </div>
    );
};
