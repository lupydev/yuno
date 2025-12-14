import React, { useState, useRef, useEffect } from 'react';
import { Search, X, ChevronDown } from 'lucide-react';

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
        if (filters.providers.length === 0) return 'All Providers';
        if (filters.providers.length === 1) return filters.providers[0];
        return `${filters.providers.length} Providers Selected`;
    };

    return (
        <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
            <div className="flex items-center gap-4 flex-wrap">
                <div className="flex items-center gap-2">
                    <Search size={20} className="text-gray-400" />
                    <span className="text-sm font-medium text-gray-700">Filters:</span>
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
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                        >
                            <option value="">All Merchants</option>
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
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm bg-white text-left flex items-center justify-between"
                        >
                            <span className={filters.providers.length === 0 ? 'text-gray-500' : 'text-gray-900'}>
                                {getProviderButtonText()}
                            </span>
                            <ChevronDown size={16} className={`transition-transform ${isProviderDropdownOpen ? 'rotate-180' : ''}`} />
                        </button>

                        {isProviderDropdownOpen && (
                            <div className="absolute z-10 mt-1 w-full bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                                {providers.map((provider) => (
                                    <label
                                        key={provider}
                                        className="flex items-center px-3 py-2 hover:bg-gray-50 cursor-pointer"
                                    >
                                        <input
                                            type="checkbox"
                                            checked={filters.providers.includes(provider)}
                                            onChange={() => handleProviderToggle(provider)}
                                            className="mr-2 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                        />
                                        <span className="text-sm text-gray-700">{provider}</span>
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
                        className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                    >
                        <X size={16} />
                        Clear Filters
                    </button>
                )}
            </div>
        </div>
    );
};
