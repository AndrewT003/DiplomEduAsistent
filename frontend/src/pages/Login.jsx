import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from '../contexts/ToastContext'

const COLORS = {
    bg: '#1a1a1a',
    surface: '#2a2a2a',
    border: '#3a3a3a',
    accent: '#f97316',
    accentHover: '#ea6c0a',
    accentLight: '#3a3a3a',
    muted: '#888888',
    text: '#e0e0e0',
    inputBg: '#3a3a3a',
}

export default function Login() {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [loading, setLoading] = useState(false)
    const { login } = useAuth()
    const { showToast } = useToast()
    const navigate = useNavigate()

    async function handleSubmit(e) {
        e.preventDefault()
        if (!email || !password) {
            showToast('Заповніть всі поля', 'error')
            return
        }

        setLoading(true)
        try {
            await login(email, password)
            showToast('Успішний вхід!', 'success')
            // Використовуємо window.location для примусового перезавантаження
            window.location.href = '/'
        } catch (error) {
            const errorMsg = error.response?.data?.detail || 'Помилка входу'
            showToast(errorMsg, 'error')
            setLoading(false)
        }
    }

    return (
        <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '100vh',
            background: COLORS.bg,
            padding: '20px'
        }}>
            <div style={{
                width: '100%',
                maxWidth: '420px',
                background: COLORS.surface,
                border: `1px solid ${COLORS.border}`,
                borderRadius: '16px',
                padding: '32px',
                boxShadow: '0 8px 32px rgba(0,0,0,0.3)'
            }}>
                {/* Logo */}
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    marginBottom: '24px'
                }}>
                    <div style={{
                        width: '48px',
                        height: '48px',
                        background: COLORS.accent,
                        borderRadius: '12px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#fff',
                        fontSize: '24px',
                        fontWeight: '700',
                        boxShadow: '0 4px 12px rgba(249,115,22,0.3)'
                    }}>E</div>
                </div>

                <h1 style={{
                    fontSize: '24px',
                    fontWeight: '700',
                    color: COLORS.text,
                    textAlign: 'center',
                    marginBottom: '8px'
                }}>Вхід до EduAssistant</h1>

                <p style={{
                    fontSize: '13px',
                    color: COLORS.muted,
                    textAlign: 'center',
                    marginBottom: '32px'
                }}>Введіть ваші дані для входу</p>

                <form onSubmit={handleSubmit}>
                    {/* Email */}
                    <div style={{ marginBottom: '20px' }}>
                        <label style={{
                            display: 'block',
                            fontSize: '13px',
                            fontWeight: '600',
                            color: COLORS.text,
                            marginBottom: '8px'
                        }}>Email</label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="your@email.com"
                            disabled={loading}
                            style={{
                                width: '100%',
                                padding: '12px 16px',
                                background: COLORS.inputBg,
                                border: `1px solid ${COLORS.border}`,
                                borderRadius: '10px',
                                fontSize: '14px',
                                color: COLORS.text,
                                outline: 'none',
                                transition: 'border-color 0.2s',
                                boxSizing: 'border-box'
                            }}
                            onFocus={(e) => e.target.style.borderColor = COLORS.accent}
                            onBlur={(e) => e.target.style.borderColor = COLORS.border}
                        />
                    </div>

                    {/* Password */}
                    <div style={{ marginBottom: '24px' }}>
                        <label style={{
                            display: 'block',
                            fontSize: '13px',
                            fontWeight: '600',
                            color: COLORS.text,
                            marginBottom: '8px'
                        }}>Пароль</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="••••••••"
                            disabled={loading}
                            style={{
                                width: '100%',
                                padding: '12px 16px',
                                background: COLORS.inputBg,
                                border: `1px solid ${COLORS.border}`,
                                borderRadius: '10px',
                                fontSize: '14px',
                                color: COLORS.text,
                                outline: 'none',
                                transition: 'border-color 0.2s',
                                boxSizing: 'border-box'
                            }}
                            onFocus={(e) => e.target.style.borderColor = COLORS.accent}
                            onBlur={(e) => e.target.style.borderColor = COLORS.border}
                        />
                    </div>

                    {/* Submit Button */}
                    <button
                        type="submit"
                        disabled={loading || !email || !password}
                        style={{
                            width: '100%',
                            padding: '14px',
                            background: loading || !email || !password ? COLORS.border : COLORS.accent,
                            border: 'none',
                            borderRadius: '10px',
                            color: '#fff',
                            fontSize: '15px',
                            fontWeight: '600',
                            cursor: loading || !email || !password ? 'not-allowed' : 'pointer',
                            boxShadow: loading || !email || !password ? 'none' : '0 4px 12px rgba(249,115,22,0.3)',
                            transition: 'all 0.2s'
                        }}
                        onMouseEnter={(e) => {
                            if (!loading && email && password) {
                                e.target.style.background = COLORS.accentHover
                            }
                        }}
                        onMouseLeave={(e) => {
                            if (!loading && email && password) {
                                e.target.style.background = COLORS.accent
                            }
                        }}
                    >
                        {loading ? 'Вхід...' : 'Увійти'}
                    </button>
                </form>

                {/* Register Link */}
                <div style={{
                    marginTop: '24px',
                    textAlign: 'center',
                    fontSize: '13px',
                    color: COLORS.muted
                }}>
                    Ще не маєте акаунту?{' '}
                    <Link
                        to="/register"
                        style={{
                            color: COLORS.accent,
                            textDecoration: 'none',
                            fontWeight: '600'
                        }}
                        onMouseEnter={(e) => e.target.style.textDecoration = 'underline'}
                        onMouseLeave={(e) => e.target.style.textDecoration = 'none'}
                    >
                        Зареєструватися
                    </Link>
                </div>
            </div>
        </div>
    )
}