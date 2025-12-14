import React from 'react';
import { Users, Plus } from 'lucide-react';

interface UserActionButtonsProps {
    onCreateGroup: () => void;
    onCreateDeveloper: () => void;
}

export const UserActionButtons: React.FC<UserActionButtonsProps> = ({ 
    onCreateGroup, 
    onCreateDeveloper 
}) => {
    return (
        <div className="flex items-center gap-3">
            <button
                onClick={onCreateGroup}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium flex items-center gap-2 transition-colors"
            >
                <Users className="w-4 h-4" />
                New Team
            </button>
            <button
                onClick={onCreateDeveloper}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium flex items-center gap-2 transition-colors"
            >
                <Plus className="w-4 h-4" />
                New Developer
            </button>
        </div>
    );
};
