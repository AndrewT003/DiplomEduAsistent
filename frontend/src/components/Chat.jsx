import { useState } from 'react'
import API from '../api/client'

export default function Chat({ doc }) {
    const [messages, setMessages] = useState([])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)

    async function sendMessage() {
        if (!input.trim()) return

        const question = input
        setInput('')
        setLoading(true)

        const userMsg = { role: 'user', content: question }
        const updatedMessages = [...messages, userMsg]
        setMessages(updatedMessages)

        const startTime = Date.now()

        try {
            const res = await API.post(`/chat/${doc.id}`, {
                question,
                history: messages
            })

            // Мінімальна затримка 1000ms для показу анімації
            const elapsed = Date.now() - startTime
            const minDelay = 1000
            if (elapsed < minDelay) {
                await new Promise(resolve => setTimeout(resolve, minDelay - elapsed))
            }

            setMessages([
                ...updatedMessages,
                { role: 'assistant', content: res.data.answer }
            ])
        } catch {
            setMessages([
                ...updatedMessages,
                { role: 'assistant', content: 'Помилка з\'єднання з сервером.' }
            ])
        } finally {
            setLoading(false)
        }
    }

    function handleKey(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            sendMessage()
        }
    }

    return (
        <div style={{
            marginTop: '2rem',
            border: '1px solid #dee2e6',
            borderRadius: '12px',
            overflow: 'hidden'
        }}>
            <div style={{
                padding: '12px 16px',
                background: '#3b5bdb',
                color: '#fff',
                fontWeight: '500',
                fontSize: '14px'
            }}>
                Чат з документом — {doc.filename}
            </div>

            <div style={{
                height: '380px',
                overflowY: 'auto',
                padding: '1rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
                background: '#f8f9fa'
            }}>
                {messages.length === 0 && (
                    <p style={{ color: '#aaa', fontSize: '13px', textAlign: 'center', marginTop: '2rem' }}>
                        Постав питання по документу — я відповім на основі його змісту
                    </p>
                )}

                {messages.map((msg, i) => (
                    <div key={i} style={{
                        display: 'flex',
                        justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start'
                    }}>
                        <div style={{
                            maxWidth: '75%',
                            padding: '10px 14px',
                            borderRadius: msg.role === 'user' ? '12px 12px 0 12px' : '12px 12px 12px 0',
                            background: msg.role === 'user' ? '#3b5bdb' : '#fff',
                            color: msg.role === 'user' ? '#fff' : '#333',
                            fontSize: '14px',
                            lineHeight: '1.6',
                            border: msg.role === 'assistant' ? '1px solid #dee2e6' : 'none',
                            whiteSpace: 'pre-wrap'
                        }}>
                            {msg.content}
                        </div>
                    </div>
                ))}

                {loading && (
                    <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                        <div style={{
                            padding: '10px 14px',
                            borderRadius: '12px 12px 12px 0',
                            background: '#fff',
                            border: '1px solid #dee2e6',
                            fontSize: '14px',
                            color: '#aaa'
                        }}>
                            <div style={{
                                display: 'flex',
                                gap: '5px',
                                alignItems: 'center'
                            }}>
                                <span style={{
                                    width: '8px',
                                    height: '8px',
                                    backgroundColor: '#999',
                                    borderRadius: '50%',
                                    display: 'inline-block',
                                    animation: 'wave 0.8s ease-in-out infinite',
                                    animationDelay: '0s'
                                }}></span>
                                <span style={{
                                    width: '8px',
                                    height: '8px',
                                    backgroundColor: '#999',
                                    borderRadius: '50%',
                                    display: 'inline-block',
                                    animation: 'wave 0.8s ease-in-out infinite',
                                    animationDelay: '0.15s'
                                }}></span>
                                <span style={{
                                    width: '8px',
                                    height: '8px',
                                    backgroundColor: '#999',
                                    borderRadius: '50%',
                                    display: 'inline-block',
                                    animation: 'wave 0.8s ease-in-out infinite',
                                    animationDelay: '0.3s'
                                }}></span>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            <div style={{
                display: 'flex',
                gap: '8px',
                padding: '12px',
                background: '#fff',
                borderTop: '1px solid #dee2e6'
            }}>
        <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Постав питання по документу..."
            rows={2}
            style={{
                flex: 1,
                resize: 'none',
                border: '1px solid #dee2e6',
                borderRadius: '8px',
                padding: '8px 12px',
                fontSize: '14px',
                fontFamily: 'inherit',
                outline: 'none'
            }}
        />
                <button
                    onClick={sendMessage}
                    disabled={loading || !input.trim()}
                    style={{
                        padding: '8px 20px',
                        background: loading || !input.trim() ? '#adb5bd' : '#3b5bdb',
                        color: '#fff',
                        border: 'none',
                        borderRadius: '8px',
                        cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
                        fontWeight: '500',
                        fontSize: '14px',
                        alignSelf: 'flex-end'
                    }}
                >
                    Надіслати
                </button>
            </div>
        </div>
    )
}