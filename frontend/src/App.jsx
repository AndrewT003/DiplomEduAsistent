import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'

// Компонент для захисту приватних роутів
function ProtectedRoute({ children }) {
    const { isAuthenticated, loading } = useAuth()

    if (loading) {
        return (
            <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100vh',
                background: '#1a1a1a',
                color: '#e0e0e0',
                fontSize: '14px'
            }}>
                Завантаження...
            </div>
        )
    }

    return isAuthenticated ? children : <Navigate to="/login" replace />
}

// Компонент для публічних роутів (логін, реєстрація)
function PublicRoute({ children }) {
    const { isAuthenticated, loading } = useAuth()

    if (loading) {
        return (
            <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100vh',
                background: '#1a1a1a',
                color: '#e0e0e0',
                fontSize: '14px'
            }}>
                Завантаження...
            </div>
        )
    }

    return isAuthenticated ? <Navigate to="/" replace /> : children
}

export default function App() {
    return (
        <BrowserRouter>
            <Routes>
                {/* Публічні роути */}
                <Route path="/login" element={
                    <PublicRoute>
                        <Login />
                    </PublicRoute>
                } />
                <Route path="/register" element={
                    <PublicRoute>
                        <Register />
                    </PublicRoute>
                } />

                {/* Приватні роути */}
                <Route path="/" element={
                    <ProtectedRoute>
                        <Home />
                    </ProtectedRoute>
                } />

                {/* Редірект на головну */}
                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
        </BrowserRouter>
    )
}