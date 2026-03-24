import { createContext, useContext, useState, useCallback } from 'react'
import { CheckCircle, XCircle, AlertTriangle, Info } from 'lucide-react'

const ToastContext = createContext(null)

export function ToastProvider({ children }) {
    const [toasts, setToasts] = useState([])

    const showToast = useCallback((message, type = 'error') => {
        const id = Date.now()
        setToasts(prev => [...prev, { id, message, type }])

        // Автоматично прибираємо toast через 4 секунди
        setTimeout(() => {
            setToasts(prev => prev.filter(t => t.id !== id))
        }, 4000)
    }, [])

    const removeToast = useCallback((id) => {
        setToasts(prev => prev.filter(t => t.id !== id))
    }, [])

    return (
        <ToastContext.Provider value={{ showToast, removeToast }}>
            {children}
            <ToastContainer toasts={toasts} onRemove={removeToast} />
        </ToastContext.Provider>
    )
}

export function useToast() {
    const context = useContext(ToastContext)
    if (!context) {
        throw new Error('useToast має використовуватись всередині ToastProvider')
    }
    return context
}

function ToastContainer({ toasts, onRemove }) {
    return (
        <div style={{
            position: 'fixed',
            top: '16px',
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 10000,
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
            pointerEvents: 'none',
            width: '100%',
            maxWidth: '600px',
            padding: '0 16px'
        }}>
            {toasts.map(toast => (
                <Toast
                    key={toast.id}
                    message={toast.message}
                    type={toast.type}
                    onClose={() => onRemove(toast.id)}
                />
            ))}
        </div>
    )
}

function Toast({ message, type, onClose }) {
    const colors = {
        error: {
            bg: '#2a2a2a',
            border: '#ef4444',
            text: '#ef4444',
            icon: XCircle
        },
        success: {
            bg: '#2a2a2a',
            border: '#10b981',
            text: '#10b981',
            icon: CheckCircle
        },
        warning: {
            bg: '#2a2a2a',
            border: '#f97316',
            text: '#f97316',
            icon: AlertTriangle
        },
        info: {
            bg: '#2a2a2a',
            border: '#3b82f6',
            text: '#3b82f6',
            icon: Info
        }
    }

    const style = colors[type] || colors.error
    const IconComponent = style.icon

    return (
        <div style={{
            background: style.bg,
            border: `1px solid ${style.border}`,
            borderRadius: '12px',
            padding: '14px 16px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
            pointerEvents: 'auto',
            animation: 'slideDown 0.3s ease-out',
            minWidth: '320px'
        }}>
            <span style={{ flexShrink: 0, display: 'flex', alignItems: 'center' }}>
                <IconComponent size={18} color={style.text} />
            </span>
            <span style={{
                flex: 1,
                fontSize: '13px',
                lineHeight: '1.5',
                color: '#e0e0e0'
            }}>
                {message}
            </span>
            <button
                onClick={onClose}
                style={{
                    background: 'transparent',
                    border: 'none',
                    color: '#888',
                    fontSize: '18px',
                    cursor: 'pointer',
                    padding: '0 4px',
                    lineHeight: 1,
                    flexShrink: 0
                }}
            >
                ×
            </button>
            <style>{`
                @keyframes slideDown {
                    from {
                        opacity: 0;
                        transform: translateY(-20px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }
            `}</style>
        </div>
    )
}