import React from "react";

interface ConfirmLogoutProps {
  onConfirm: () => void;
  onCancel: () => void;
}

const ConfirmLogout: React.FC<ConfirmLogoutProps> = ({ onConfirm, onCancel }) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-slate-800 text-white rounded-xl shadow-lg p-6 w-80">
        <h3 className="text-lg font-bold mb-4 text-center">Cerrar sesión</h3>
        <p className="text-sm text-center text-slate-300 mb-6">
          ¿Estás seguro de que deseas cerrar sesión?
        </p>
        <div className="flex justify-around">
          <button
            onClick={onCancel}
            className="px-4 py-2 bg-gray-500 hover:bg-gray-600 rounded-lg transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={onConfirm}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
          >
            Sí, salir
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmLogout;