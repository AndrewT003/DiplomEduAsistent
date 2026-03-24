import { useState } from 'react'
import API from '../api/client'

export default function MaterialCard({ doc }) {
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(false)
    const [activeType, setActiveType] = useState(null)

    const types = [
        { key: 'summary',    label: 'Конспект' },
        { key: 'quiz',       label: 'Тест' },
        { key: 'flashcards', label: 'Флеш-картки' },
        { key: 'glossary',   label: 'Глосарій' },
    ]

    async function generate(type) {
        setLoading(true)
        setActiveType(type)
        setResult(null)
        try {
            const res = await API.post(`/generate/${doc.id}?type=${type}`)
            setResult(res.data.result)
        } catch {
            setResult('Помилка генерації. Перевір чи працює бекенд.')
        } finally {
            setLoading(false)
        }
    }

    async function download(type) {
        const res = await API.get(`/download/${doc.id}/${type}`, {
            responseType: 'blob'
        })
        const url = URL.createObjectURL(res.data)
        const a = document.createElement('a')
        a.href = url
        a.download = `${type}_${doc.filename}.docx`
        a.click()
    }

    return (
        <div style={{ marginTop: '2rem' }}>
            <h2 style={{ marginBottom: '1rem', fontSize: '18px' }}>
                {doc.filename}
            </h2>

            <div style={{ display: 'flex', gap: '10px', marginBottom: '1.5rem' }}>
                {types.map(t => (
                    <button
                        key={t.key}
                        onClick={() => generate(t.key)}
                        style={{
                            padding: '10px 20px',
                            borderRadius: '8px',
                            border: 'none',
                            cursor: 'pointer',
                            background: activeType === t.key ? '#3b5bdb' : '#e9ecef',
                            color: activeType === t.key ? '#fff' : '#333',
                            fontWeight: '500',
                            fontSize: '14px',
                        }}
                    >
                        {t.label}
                    </button>
                ))}
            </div>

            {loading && (
                <p style={{ color: '#888' }}>Генерація...</p>
            )}

            {result && (
                <div>
                    <div style={{
                        background: '#f8f9fa',
                        border: '1px solid #dee2e6',
                        borderRadius: '12px',
                        padding: '1.5rem',
                        whiteSpace: 'pre-wrap',
                        fontSize: '14px',
                        lineHeight: '1.7',
                        maxHeight: '400px',
                        overflowY: 'auto',
                        marginBottom: '1rem'
                    }}>
                        {result}
                    </div>
                    <button
                        onClick={() => download(activeType)}
                        style={{
                            padding: '10px 24px',
                            background: '#2f9e44',
                            color: '#fff',
                            border: 'none',
                            borderRadius: '8px',
                            cursor: 'pointer',
                            fontWeight: '500',
                            fontSize: '14px',
                        }}
                    >
                        Завантажити .docx
                    </button>
                </div>
            )}
        </div>
    )
}