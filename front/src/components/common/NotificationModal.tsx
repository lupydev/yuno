import { useEffect, useState } from "react";
import { Check } from "lucide-react";

interface NotificationProps {
  message: string;
  isOpen: boolean;
  onClose: () => void;
}

export function Notification({
  message,
  isOpen,
  onClose,
}: Readonly<NotificationProps>) {
  const [visible, setVisible] = useState(isOpen);

  useEffect(() => {
    if (isOpen) {
      setVisible(true);
      const timer = setTimeout(() => {
        setVisible(false);
        onClose();
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [isOpen, onClose]);

  if (!visible) return null;

  return (
    <div className="fixed top-5 left-1/2 z-50 -translate-x-1/2 rounded-xl bg-[#12202d] border border-gray-700 p-4 shadow-lg flex items-center gap-2 text-white">
      <Check className="text-green-500" />
      <span>{message}</span>
    </div>
  );
}
