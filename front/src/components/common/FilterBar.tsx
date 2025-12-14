import React, { useState } from 'react';
import { ChevronDown, X } from 'lucide-react';

const FilterBar = () => {
    const [activeFilter, setActiveFilter] = useState<string | null>(null);
    const [selectedFilters, setSelectedFilters] = useState({
        merchant: null,
        country: null,
        provider: null,
        method: null
    });

    const filterOptions = {
        merchant: ['Shopito', 'StoreX', 'MegaShop', 'TechStore', 'FashionHub'],
        country: ['United States', 'United Kingdom', 'Germany', 'France', 'Spain', 'Mexico', 'Colombia'],
        provider: ['Stripe', 'PayPal', 'Adyen', 'BAC', 'Square'],
        method: ['Tarjeta', 'PSE', 'Wallet', 'Bank Transfer', 'Cash']
    };

    const filterLabels = {
        merchant: 'Merchant',
        country: 'Country',
        provider: 'Provider',
        method: 'Payment Method'
    };

    const toggleFilter = (filterType: string) => {
        setActiveFilter(activeFilter === filterType ? null : filterType);
    };

    const selectOption = (filterType: string, option: string) => {
        setSelectedFilters(prev => ({
            ...prev,
            [filterType]: prev[filterType] === option ? null : option
        }));
        setActiveFilter(null);
    };

    const clearFilter = (filterType: string) => {
        setSelectedFilters(prev => ({
            ...prev,
            [filterType]: null
        }));
    };

    return (
        <div className="mb-6 flex items-center gap-3">
            {Object.keys(filterOptions).map(filterType => (
                <div key={filterType} className="relative">
                    <button
                        onClick={() => toggleFilter(filterType)}
                        className={`px-4 py-2 rounded-lg border text-sm font-medium transition-all flex items-center gap-2 ${
                            selectedFilters[filterType]
                                ? 'bg-blue-600 border-blue-600 text-white'
                                : 'bg-slate-900 border-slate-700 text-slate-300 hover:border-slate-600'
                        }`}
                    >
                        {selectedFilters[filterType] || filterLabels[filterType]}
                        {selectedFilters[filterType] ? (
                            <X
                                className="w-4 h-4"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    clearFilter(filterType);
                                }}
                            />
                        ) : (
                            <ChevronDown className={`w-4 h-4 transition-transform ${activeFilter === filterType ? 'rotate-180' : ''}`} />
                        )}
                    </button>

                    {activeFilter === filterType && (
                        <div className="absolute top-full mt-2 left-0 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-50 min-w-[200px] py-1">
                            {filterOptions[filterType].map(option => (
                                <button
                                    key={option}
                                    onClick={() => selectOption(filterType, option)}
                                    className={`w-full px-4 py-2 text-left text-sm transition-colors ${
                                        selectedFilters[filterType] === option
                                            ? 'bg-blue-600 text-white'
                                            : 'text-slate-300 hover:bg-slate-700'
                                    }`}
                                >
                                    {option}
                                </button>
                            ))}
                        </div>
                    )}
                </div>
            ))}

            {Object.values(selectedFilters).some(v => v !== null) && (
                <button
                    onClick={() => setSelectedFilters({ merchant: null, country: null, provider: null, method: null })}
                    className="px-4 py-2 text-sm text-slate-400 hover:text-white transition-colors"
                >
                    Clear all
                </button>
            )}
        </div>
    );
};

export default FilterBar;
