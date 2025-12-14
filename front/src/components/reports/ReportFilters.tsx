import React, { useState, useRef, useEffect } from 'react';
import { Search, X, ChevronDown } from 'lucide-react';
import { UI_MESSAGES } from '@/constants/reports';

interface ReportFiltersProps {
    filters: {
        merchant: string;
        providers: string[];
    };
    onFilterChange: (key: string, value: string | string[]) => void;
    onClearFilters: () => void;
    merchants: string[];
    providers: string[];
    // TODO: Add these props when API is ready
    // onMerchantChange?: (merchantId: string) => void; // To fetch providers for selected merchant
    // loadingProviders?: boolean;
}

export const ReportFilters: React.FC<ReportFiltersProps> = ({
    filters,
    onFilterChange,
    onClearFilters,
    merchants,
    providers
}) => {
    const [isProviderDropdownOpen, setIsProviderDropdownOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    const hasActiveFilters = filters.merchant || filters.providers.length > 0;

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsProviderDropdownOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleProviderToggle = (provider: string) => {
        const newProviders = filters.providers.includes(provider)
            ? filters.providers.filter(p => p !== provider)
            : [...filters.providers, provider];
        onFilterChange('providers', newProviders);
    };

    const getProviderButtonText = () => {
        if (filters.providers.length === 0) return UI_MESSAGES.FILTERS.ALL_PROVIDERS;
        if (filters.providers.length === 1) return filters.providers[0];
        return UI_MESSAGES.FILTERS.PROVIDERS_SELECTED(filters.providers.length);
    };

    return (
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 mb-6">
            <div className="flex items-center gap-4 flex-wrap">
                <div className="flex items-center gap-2">
                    <Search size={20} className="text-slate-400" />
                    <span className="text-sm font-medium text-slate-300">Filters:</span>
                </div>

                <div className="flex-1 flex gap-4 flex-wrap">
                    {/* Merchant Filter */}
                    <div className="flex-1 min-w-[200px]">
                        <select
                            value={filters.merchant}
                            onChange={(e) => {
                                onFilterChange('merchant', e.target.value);
                                // TODO: When merchant changes, fetch its providers
                                // if (onMerchantChange) onMerchantChange(e.target.value);
                            }}
                            className="w-full px-3 py-2 border border-slate-800 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm bg-slate-900 text-slate-300"
                        >
                            <option value="">{UI_MESSAGES.FILTERS.ALL_MERCHANTS}</option>
                            {merchants.map((merchant) => (
                                <option key={merchant} value={merchant}>
                                    {merchant}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Multi-Select Provider Filter */}
                    <div className="flex-1 min-w-[200px] relative" ref={dropdownRef}>
                        <button
                            type="button"
                            onClick={() => setIsProviderDropdownOpen(!isProviderDropdownOpen)}
                            className="w-full px-3 py-2 border border-slate-800 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm bg-slate-900 text-left flex items-center justify-between"
                        >
                            <span className={filters.providers.length === 0 ? 'text-slate-400' : 'text-white'}>
                                {getProviderButtonText()}
                            </span>
                            <ChevronDown size={16} className={`transition-transform ${isProviderDropdownOpen ? 'rotate-180' : ''}`} />
                        </button>

                        {isProviderDropdownOpen && (
                            <div className="absolute z-10 mt-1 w-full bg-slate-800 border border-slate-800 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                                {providers.map((provider) => (
                                    <label
                                        key={provider}
                                        className="flex items-center px-3 py-2 hover:bg-slate-800/30 cursor-pointer"
                                    >
                                        <input
                                            type="checkbox"
                                            checked={filters.providers.includes(provider)}
                                            onChange={() => handleProviderToggle(provider)}
                                            className="mr-2 rounded border-slate-700 text-blue-600 focus:ring-blue-500"
                                        />
                                        <span className="text-sm text-slate-300">{provider}</span>
                                    </label>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Clear Filters Button */}
                {hasActiveFilters && (
                    <button
                        onClick={onClearFilters}
                        className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
                    >
                        <X size={16} />
                        {UI_MESSAGES.FILTERS.CLEAR_FILTERS}
                    </button>
                )}
            </div>
        </div>
    );
};
