import { X } from "lucide-react";
import type { ReactNode } from "react";

interface SimpleModalProps {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    children: (helpers: { onClose: () => void }) => ReactNode;
}

export function SimpleModal({
    isOpen,
    onClose,
    title,
    children,
}: Readonly<SimpleModalProps>) {
    if (!isOpen) {
        return null;
    }

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
            onClick={onClose}
        >
            {/* Target */}
            <div
                className="relative w-full max-w-lg rounded-xl bg-[#12202d] border border-gray-700 p-6 shadow-lg"
                onClick={(e) => e.stopPropagation()}
            >
                {/* header */}
                <div className="flex items-center justify-between border-b border-gray-700 pb-4">
                    <h2 className="text-xl font-semibold text-white">
                        {title}
                    </h2>
                    <button
                        onClick={onClose}
                        className="rounded-full p-1 text-gray-400 transition-colors hover:bg-gray-700 hover:text-white"
                    >
                        <X size={24} />
                    </button>
                </div>

                {/* form */}
                <div className="mt-6">{children({ onClose })}</div>
            </div>
        </div>
    );
}
