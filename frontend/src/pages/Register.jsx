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

export default function Register() {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [confirmPassword, setConfirmPassword] = useState('')
    const [loading, setLoading] = useState(false)
    const { register } = useAuth()
    const { showToast } = useToast()
    const navigate = useNavigate()

    async function handleSubmit(e) {
        e.preventDefault()

        if (!email || !password || !confirmPassword) {
            showToast('Заповніть всі поля', 'error')
            return
        }

        if (password.length < 6) {
            showToast('Пароль має бути не менше 6 символів', 'error')
            return
        }

        if (password !== confirmPassword) {
            showToast('Паролі не співпадають', 'error')
            return
        }

        setLoading(true)
        try {
            await register(email, password)
            showToast('Реєстрація успішна!', 'success')
            // Використовуємо window.location для примусового перезавантаження
            window.location.href = '/'
        } catch (error) {
            const errorMsg = error.response?.data?.detail || 'Помилка реєстрації'
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
                }}>Реєстрація</h1>

                <p style={{
                    fontSize: '13px',
                    color: COLORS.muted,
                    textAlign: 'center',
                    marginBottom: '32px'
                }}>Створіть акаунт для використання EduAssistant</p>

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
                    <div style={{ marginBottom: '20px' }}>
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
                        <div style={{
                            fontSize: '11px',
                            color: COLORS.muted,
                            marginTop: '4px'
                        }}>Мінімум 6 символів</div>
                    </div>

                    {/* Confirm Password */}
                    <div style={{ marginBottom: '24px' }}>
                        <label style={{
                            display: 'block',
                            fontSize: '13px',
                            fontWeight: '600',
                            color: COLORS.text,
                            marginBottom: '8px'
                        }}>Підтвердіть пароль</label>
                        <input
                            type="password"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
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
                        disabled={loading || !email || !password || !confirmPassword}
                        style={{
                            width: '100%',
                            padding: '14px',
                            background: loading || !email || !password || !confirmPassword ? COLORS.border : COLORS.accent,
                            border: 'none',
                            borderRadius: '10px',
                            color: '#fff',
                            fontSize: '15px',
                            fontWeight: '600',
                            cursor: loading || !email || !password || !confirmPassword ? 'not-allowed' : 'pointer',
                            boxShadow: loading || !email || !password || !confirmPassword ? 'none' : '0 4px 12px rgba(249,115,22,0.3)',
                            transition: 'all 0.2s'
                        }}
                        onMouseEnter={(e) => {
                            if (!loading && email && password && confirmPassword) {
                                e.target.style.background = COLORS.accentHover
                            }
                        }}
                        onMouseLeave={(e) => {
                            if (!loading && email && password && confirmPassword) {
                                e.target.style.background = COLORS.accent
                            }
                        }}
                    >
                        {loading ? 'Реєстрація...' : 'Зареєструватися'}
                    </button>
                </form>

                {/* Login Link */}
                <div style={{
                    marginTop: '24px',
                    textAlign: 'center',
                    fontSize: '13px',
                    color: COLORS.muted
                }}>
                    Вже маєте акаунт?{' '}
                    <Link
                        to="/login"
                        style={{
                            color: COLORS.accent,
                            textDecoration: 'none',
                            fontWeight: '600'
                        }}
                        onMouseEnter={(e) => e.target.style.textDecoration = 'underline'}
                        onMouseLeave={(e) => e.target.style.textDecoration = 'none'}
                    >
                        Увійти
                    </Link>
                </div>
            </div>
        </div>
    )
}