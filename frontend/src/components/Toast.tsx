import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';

type ToastType = 'success' | 'error' | 'info';

interface Toast {
  id: number;
  message: string;
  type: ToastType;
  exiting?: boolean;
}

interface ToastContextType {
  toast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextType>({ toast: () => {} });

export const useToast = () => useContext(ToastContext);

let nextId = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const toast = useCallback((message: string, type: ToastType = 'info') => {
    const id = nextId++;
    setToasts(prev => [...prev, { id, message, type }]);

    // Start exit animation after 3.5s
    setTimeout(() => {
      setToasts(prev => prev.map(t => t.id === id ? { ...t, exiting: true } : t));
    }, 3500);

    // Remove after animation completes
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 4000);
  }, []);

  const colors: Record<ToastType, string> = {
    success: 'var(--accent-green)',
    error: 'var(--accent-red)',
    info: 'var(--accent-blue)',
  };

  const icons: Record<ToastType, string> = {
    success: '\u2713',
    error: '\u2717',
    info: '\u24D8',
  };

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div style={{
        position: 'fixed',
        bottom: '24px',
        left: '50%',
        transform: 'translateX(-50%)',
        display: 'flex',
        flexDirection: 'column-reverse',
        gap: '8px',
        zIndex: 9999,
        pointerEvents: 'none',
        maxWidth: '90vw',
      }}>
        {toasts.map(t => (
          <div key={t.id} style={{
            padding: '12px 20px',
            borderRadius: '12px',
            color: '#fff',
            fontWeight: 500,
            fontSize: '0.95rem',
            boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
            animation: t.exiting ? 'toast-slide-out 0.3s ease-in forwards' : 'toast-slide-in 0.3s ease-out',
            pointerEvents: 'auto',
            background: colors[t.type],
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            direction: 'rtl',
            backdropFilter: 'blur(8px)',
            minWidth: '200px',
            justifyContent: 'center',
          }}>
            <span style={{ fontSize: '1.1rem' }}>{icons[t.type]}</span>
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
