import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from "lucide-react";

interface PaginationProps {
currentPage: number;
totalPages: number;
onPageChange: (page: number) => void;
maxVisible?: number;
}

export const Pagination = ({
currentPage,
totalPages,
onPageChange,
maxVisible = 7,
}: PaginationProps) => {
if (totalPages <= 1) return null;

const getVisiblePages = (current: number, total: number, max: number) => {
    const half = Math.floor(max / 2);
    let start = Math.max(current + 1 - half, 1);
    const end = Math.min(start + max - 1, total);

    if (end - start < max - 1) {
        start = Math.max(end - max + 1, 1);
    }

    return Array.from({ length: end - start + 1 }, (_, i) => start + i);
};

const visiblePages = getVisiblePages(currentPage, totalPages, maxVisible);

const goToPage = (page: number) => {
    if (page >= 0 && page < totalPages) onPageChange(page);
};

return (
    <div className="flex items-center justify-center gap-1 mt-6 select-none">
    <button
        onClick={() => goToPage(0)}
        disabled={currentPage === 0}
        className="p-2 rounded hover:bg-gray-100 disabled:opacity-40"
    >
        <ChevronsLeft size={18} />
    </button>

    <button
        onClick={() => goToPage(currentPage - 1)}
        disabled={currentPage === 0}
        className="p-2 rounded hover:bg-gray-100 disabled:opacity-40"
    >
        <ChevronLeft size={18} />
    </button>

    {visiblePages[0] > 1 && (
        <span className="px-2 text-gray-500">...</span>
    )}

    {visiblePages.map((page) => (
        <button
        key={page}
        onClick={() => goToPage(page - 1)}
        className={`px-3 py-1 rounded font-medium ${
            page - 1 === currentPage
            ? "bg-blue-600 text-white"
            : "hover:bg-gray-100 text-gray-700"
        }`}
        >
        {page}
        </button>
    ))}

    {visiblePages[visiblePages.length - 1] < totalPages && (
        <span className="px-2 text-gray-500">...</span>
    )}

    <button
        onClick={() => goToPage(currentPage + 1)}
        disabled={currentPage === totalPages - 1}
        className="p-2 rounded hover:bg-gray-100 disabled:opacity-40"
    >
        <ChevronRight size={18} />
    </button>

    <button
        onClick={() => goToPage(totalPages - 1)}
        disabled={currentPage === totalPages - 1}
        className="p-2 rounded hover:bg-gray-100 disabled:opacity-40"
    >
        <ChevronsRight size={18} />
    </button>
    </div>
);
};