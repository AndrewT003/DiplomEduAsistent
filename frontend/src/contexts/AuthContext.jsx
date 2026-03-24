import { createContext, useContext, useState, useEffect } from 'react'
import API from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null)
    const [loading, setLoading] = useState(true)

    // Перевіряємо чи є токен при завантаженні
    useEffect(() => {
        const token = localStorage.getItem('access_token')
        if (token) {
            // Перевіряємо чи токен валідний
            fetchCurrentUser()
        } else {
            setLoading(false)
        }
    }, [])

    const fetchCurrentUser = async () => {
        try {
            const response = await API.get('/auth/me')
            setUser(response.data)
        } catch (error) {
            console.error('Помилка отримання користувача:', error)
            // Якщо токен невалідний - видаляємо його
            localStorage.removeItem('access_token')
            setUser(null)
        } finally {
            setLoading(false)
        }
    }

    const login = async (email, password) => {
        const response = await API.post('/auth/login', { email, password })
        const { session, user: userData } = response.data

        // Зберігаємо токен
        localStorage.setItem('access_token', session.access_token)
        setUser(userData)

        return userData
    }

    const register = async (email, password) => {
        const response = await API.post('/auth/register', { email, password })
        const { session, user: userData } = response.data

        // Зберігаємо токен
        localStorage.setItem('access_token', session.access_token)
        setUser(userData)

        return userData
    }

    const logout = async () => {
        try {
            await API.post('/auth/logout')
        } catch (error) {
            console.error('Помилка при logout:', error)
        } finally {
            // Завжди видаляємо токен локально
            localStorage.removeItem('access_token')
            setUser(null)
        }
    }

    const value = {
        user,
        login,
        register,
        logout,
        loading,
        isAuthenticated: !!user
    }

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    )
}

export function useAuth() {
    const context = useContext(AuthContext)
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider')
    }
    return context
}
