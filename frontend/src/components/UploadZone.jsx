import { useState } from 'react'
import API from '../api/client'

export default function UploadZone({ onUpload }) {
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    async function handleFile(e) {
        const file = e.target.files[0]
        if (!file) return

        setLoading(true)
        setError(null)

        const formData = new FormData()
        formData.append('file', file)

        try {
            const res = await API.post('/upload', formData)
            onUpload(res.data)
        } catch (err) {
            setError('Помилка завантаження файлу')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div style={{ margin: '2rem 0' }}>
            <label style={{
                display: 'block',
                border: '2px dashed #ccc',
                borderRadius: '12px',
                padding: '3rem',
                textAlign: 'center',
                cursor: 'pointer'
            }}>
                <input
                    type="file"
                    accept=".pdf,.docx"
                    onChange={handleFile}
                    style={{ display: 'none' }}
                />
                {loading
                    ? 'Завантаження...'
                    : 'Натисни або перетягни PDF / DOCX файл'}
            </label>
            {error && <p style={{ color: 'red' }}>{error}</p>}
        </div>
    )
}