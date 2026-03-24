import { useState, useEffect, forwardRef, useImperativeHandle } from 'react'
import API from '../api/client'
import { useToast } from '../contexts/ToastContext'
import { File, FileText, Pencil, Trash2, X, Check } from 'lucide-react'

const COLORS = {
    bg: '#1a1a1a',
    surface: '#2a2a2a',
    border: '#3a3a3a',
    accent: '#f97316',
    accentHover: '#ea6c0a',
    accentLight: '#3a3a3a',
    muted: '#888888',
    text: '#e0e0e0',
    textLight: '#b0b0b0',
}

const DocumentsSidebar = forwardRef(({ currentDoc, onDocumentSelect, onClose }, ref) => {
    const { showToast } = useToast()
    const [documents, setDocuments] = useState([])
    const [regulatoryDocs, setRegulatoryDocs] = useState([])
    const [loading, setLoading] = useState(true)
    const [editingId, setEditingId] = useState(null)
    const [editingName, setEditingName] = useState('')
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(null)

    useEffect(() => {
        loadDocuments()
    }, [])

    // Експортуємо метод loadDocuments через ref
    useImperativeHandle(ref, () => ({
        loadDocuments
    }))

    async function loadDocuments() {
        setLoading(true)
        try {
            const [docsRes, regDocsRes] = await Promise.all([
                API.get('/documents'),
                API.get('/documents/regulatory')
            ])

            // Фільтруємо звичайні документи (document_type = 'user' або null)
            const userDocs = docsRes.data.filter(d =>
                !d.document_type || d.document_type === 'user'
            )

            setDocuments(userDocs)
            setRegulatoryDocs(regDocsRes.data)
        } catch (error) {
            console.error('Помилка завантаження документів:', error)
            showToast('Помилка завантаження документів', 'error')
        } finally {
            setLoading(false)
        }
    }

    async function handleDelete(docId, docName) {
        try {
            await API.delete(`/documents/${docId}`)
            showToast(`Документ "${docName}" видалено`, 'success')
            setShowDeleteConfirm(null)
            loadDocuments()

            // Якщо видалили поточний документ - скидаємо вибір
            if (currentDoc?.id === docId) {
                onDocumentSelect(null)
            }
        } catch (error) {
            showToast('Помилка видалення документа', 'error')
        }
    }

    async function handleRename(docId) {
        if (!editingName.trim()) {
            showToast('Введіть назву документа', 'error')
            return
        }

        try {
            await API.patch(`/documents/${docId}`, { filename: editingName })
            showToast('Назву змінено', 'success')
            setEditingId(null)
            loadDocuments()
        } catch (error) {
            showToast('Помилка зміни назви', 'error')
        }
    }

    function startEdit(doc) {
        setEditingId(doc.id)
        setEditingName(doc.filename)
    }

    function cancelEdit() {
        setEditingId(null)
        setEditingName('')
    }

    function DocumentItem({ doc, isRegulatory = false }) {
        const isActive = currentDoc?.id === doc.id
        const isEditing = editingId === doc.id

        return (
            <div
                style={{
                    padding: '10px 12px',
                    borderRadius: '8px',
                    marginBottom: '4px',
                    background: isActive ? COLORS.accentLight : 'transparent',
                    border: `1px solid ${isActive ? COLORS.accent : 'transparent'}`,
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    position: 'relative',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                }}
                onClick={() => !isEditing && onDocumentSelect(doc)}
                onMouseEnter={(e) => {
                    if (!isActive && !isEditing) {
                        e.currentTarget.style.background = COLORS.surface
                    }
                }}
                onMouseLeave={(e) => {
                    if (!isActive && !isEditing) {
                        e.currentTarget.style.background = 'transparent'
                    }
                }}
            >
                {/* Icon */}
                <div style={{ flexShrink: 0, display: 'flex', alignItems: 'center' }}>
                    {isRegulatory ? (
                        <FileText size={16} color={isActive ? COLORS.accent : COLORS.muted} />
                    ) : (
                        <File size={16} color={isActive ? COLORS.accent : COLORS.muted} />
                    )}
                </div>

                {/* Name */}
                {isEditing ? (
                    <input
                        type="text"
                        value={editingName}
                        onChange={(e) => setEditingName(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter') handleRename(doc.id)
                            if (e.key === 'Escape') cancelEdit()
                        }}
                        onClick={(e) => e.stopPropagation()}
                        autoFocus
                        style={{
                            flex: 1,
                            padding: '4px 8px',
                            background: COLORS.bg,
                            border: `1px solid ${COLORS.accent}`,
                            borderRadius: '4px',
                            color: COLORS.text,
                            fontSize: '13px',
                            outline: 'none'
                        }}
                    />
                ) : (
                    <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{
                            fontSize: '13px',
                            fontWeight: isActive ? '600' : '400',
                            color: isActive ? COLORS.accent : COLORS.text,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap'
                        }}>
                            {doc.filename}
                        </div>
                        {isRegulatory && doc.regulatory_category && (
                            <div style={{
                                fontSize: '10px',
                                color: COLORS.muted,
                                marginTop: '2px'
                            }}>
                                {doc.regulatory_category}
                            </div>
                        )}
                    </div>
                )}

                {/* Actions */}
                {isEditing ? (
                    <div style={{ display: 'flex', gap: '4px' }} onClick={(e) => e.stopPropagation()}>
                        <button
                            onClick={() => handleRename(doc.id)}
                            style={{
                                padding: '4px 8px',
                                background: COLORS.accent,
                                border: 'none',
                                borderRadius: '4px',
                                color: '#fff',
                                fontSize: '11px',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center'
                            }}
                        >
                            <Check size={14} />
                        </button>
                        <button
                            onClick={cancelEdit}
                            style={{
                                padding: '4px 8px',
                                background: COLORS.border,
                                border: 'none',
                                borderRadius: '4px',
                                color: COLORS.text,
                                fontSize: '11px',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center'
                            }}
                        >
                            <X size={14} />
                        </button>
                    </div>
                ) : (
                    <div
                        style={{ display: 'flex', gap: '2px', opacity: 0 }}
                        className="doc-actions"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <button
                            onClick={() => startEdit(doc)}
                            title="Перейменувати"
                            style={{
                                width: '24px',
                                height: '24px',
                                border: 'none',
                                borderRadius: '4px',
                                background: 'transparent',
                                color: COLORS.text,
                                cursor: 'pointer',
                                fontSize: '12px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center'
                            }}
                            onMouseEnter={(e) => e.currentTarget.style.background = COLORS.border}
                            onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                        >
                            <Pencil size={14} />
                        </button>
                        <button
                            onClick={() => setShowDeleteConfirm(doc.id)}
                            title="Видалити"
                            style={{
                                width: '24px',
                                height: '24px',
                                border: 'none',
                                borderRadius: '4px',
                                background: 'transparent',
                                color: COLORS.text,
                                cursor: 'pointer',
                                fontSize: '12px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center'
                            }}
                            onMouseEnter={(e) => e.currentTarget.style.background = COLORS.border}
                            onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                        >
                            <Trash2 size={14} />
                        </button>
                    </div>
                )}

                {/* Delete Confirmation */}
                {showDeleteConfirm === doc.id && (
                    <div
                        style={{
                            position: 'absolute',
                            top: 0,
                            left: 0,
                            right: 0,
                            bottom: 0,
                            background: COLORS.surface,
                            borderRadius: '8px',
                            border: `1px solid ${COLORS.accent}`,
                            padding: '8px',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '6px',
                            zIndex: 10
                        }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div style={{ fontSize: '11px', color: COLORS.text }}>
                            Видалити документ?
                        </div>
                        <div style={{ display: 'flex', gap: '4px' }}>
                            <button
                                onClick={() => handleDelete(doc.id, doc.filename)}
                                style={{
                                    flex: 1,
                                    padding: '4px',
                                    background: '#ef4444',
                                    border: 'none',
                                    borderRadius: '4px',
                                    color: '#fff',
                                    fontSize: '11px',
                                    cursor: 'pointer',
                                    fontWeight: '600'
                                }}
                            >Видалити</button>
                            <button
                                onClick={() => setShowDeleteConfirm(null)}
                                style={{
                                    flex: 1,
                                    padding: '4px',
                                    background: COLORS.border,
                                    border: 'none',
                                    borderRadius: '4px',
                                    color: COLORS.text,
                                    fontSize: '11px',
                                    cursor: 'pointer'
                                }}
                            >Скасувати</button>
                        </div>
                    </div>
                )}
            </div>
        )
    }

    return (
        <div style={{
            width: '280px',
            height: '100vh',
            background: COLORS.bg,
            borderRight: `1px solid ${COLORS.border}`,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden'
        }}>
            {/* Header */}
            <div style={{
                padding: '16px',
                borderBottom: `1px solid ${COLORS.border}`,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
            }}>
                <div style={{
                    fontSize: '14px',
                    fontWeight: '700',
                    color: COLORS.text
                }}>Документи</div>
                <button
                    onClick={onClose}
                    style={{
                        width: '28px',
                        height: '28px',
                        border: `1px solid ${COLORS.border}`,
                        borderRadius: '6px',
                        background: 'transparent',
                        color: COLORS.muted,
                        cursor: 'pointer',
                        fontSize: '16px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                    }}
                >
                    <X size={18} />
                </button>
            </div>

            {/* Content */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '12px' }}>
                {loading ? (
                    <div style={{
                        padding: '20px',
                        textAlign: 'center',
                        color: COLORS.muted,
                        fontSize: '13px'
                    }}>Завантаження...</div>
                ) : (
                    <>
                        {/* User Documents */}
                        <div style={{ marginBottom: '20px' }}>
                            <div style={{
                                fontSize: '11px',
                                fontWeight: '600',
                                color: COLORS.muted,
                                textTransform: 'uppercase',
                                letterSpacing: '0.5px',
                                marginBottom: '8px',
                                padding: '0 4px'
                            }}>
                                Мої документи ({documents.length})
                            </div>
                            {documents.length === 0 ? (
                                <div style={{
                                    padding: '12px',
                                    fontSize: '12px',
                                    color: COLORS.muted,
                                    textAlign: 'center'
                                }}>Немає документів</div>
                            ) : (
                                documents.map(doc => (
                                    <DocumentItem key={doc.id} doc={doc} />
                                ))
                            )}
                        </div>

                        {/* Regulatory Documents */}
                        <div>
                            <div style={{
                                fontSize: '11px',
                                fontWeight: '600',
                                color: COLORS.muted,
                                textTransform: 'uppercase',
                                letterSpacing: '0.5px',
                                marginBottom: '8px',
                                padding: '0 4px'
                            }}>
                                Нормативні документи ({regulatoryDocs.length})
                            </div>
                            {regulatoryDocs.length === 0 ? (
                                <div style={{
                                    padding: '12px',
                                    fontSize: '12px',
                                    color: COLORS.muted,
                                    textAlign: 'center'
                                }}>Немає документів</div>
                            ) : (
                                regulatoryDocs.map(doc => (
                                    <DocumentItem key={doc.id} doc={doc} isRegulatory />
                                ))
                            )}
                        </div>
                    </>
                )}
            </div>

            <style>{`
                .doc-actions {
                    transition: opacity 0.2s;
                }
                div:hover > .doc-actions {
                    opacity: 1 !important;
                }
            `}</style>
        </div>
    )
})

DocumentsSidebar.displayName = 'DocumentsSidebar'

export default DocumentsSidebar