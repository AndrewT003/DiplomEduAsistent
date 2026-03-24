import axios from 'axios'

// Використовуємо /api/ для production (через nginx proxy) або localhost для dev
const API = axios.create({
    baseURL: import.meta.env.VITE_API_URL || '/api',
})

// Interceptor для автоматичного додавання токену до всіх запитів
API.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token')
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

// Interceptor для обробки помилок авторизації
API.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Якщо токен протермінований - видаляємо його
            localStorage.removeItem('access_token')
            // Перенаправляємо на логін (якщо не на публічній сторінці)
            if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
                window.location.href = '/login'
            }
        }
        return Promise.reject(error)
    }
)

export default API