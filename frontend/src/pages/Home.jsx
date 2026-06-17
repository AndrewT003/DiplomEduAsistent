import { useState, useRef, useEffect } from 'react'
import API from '../api/client'
import { useToast } from '../contexts/ToastContext'
import { useAuth } from '../contexts/AuthContext'
import DocumentsSidebar from '../components/DocumentsSidebar'
import {
    Sparkles, ChevronLeft, ChevronRight, File, FileText,
    AlertCircle, AlertTriangle, Info, CheckCircle2,
    XCircle, HelpCircle, Menu, Upload, FileCheck,
    BarChart3, Search, ClipboardList, MapPin, Tag, Lightbulb, Check, Paperclip, LogOut, CornerRightUp
} from 'lucide-react'

const COLORS = {
    bg: '#1a1a1a',
    surface: '#2a2a2a',
    surfaceAlt: '#2a2a2a',
    border: '#3a3a3a',
    accent: '#f97316',
    accentHover: '#ea6c0a',
    accentLight: '#3a3a3a',
    accentText: '#ea6c0a',
    muted: '#888888',
    text: '#e0e0e0',
    textLight: '#b0b0b0',
    userBubble: '#f97316',
    aiBubble: '#3a3a3a',
    inputBg: '#3a3a3a',
}

function ValidationReportView({ report, colors, validationCategories, timestamp }) {
    const severityColors = {
        critical: '#ef4444',
        major: '#f97316',
        minor: '#eab308',
        info: '#3b82f6'
    }

    const categoryLabels = {
        content: 'Змістовна',
        formatting: 'Форматна',
        structure: 'Структурна',
        references: 'Посилання'
    }

    const severityIcon = (severity) => {
        const icons = {
            critical: <AlertCircle size={18} color={severityColors.critical} />,
            major: <AlertTriangle size={18} color={severityColors.major} />,
            minor: <Info size={18} color={severityColors.minor} />,
            info: <Info size={18} color={severityColors.info} />
        }
        return icons[severity] || icons.info
    }

    const complianceIcon = (compliance) => {
        const icons = {
            pass: <CheckCircle2 size={24} color={complianceColors.pass} />,
            partial: <AlertTriangle size={24} color={complianceColors.partial} />,
            fail: <XCircle size={24} color={complianceColors.fail} />,
            unknown: <HelpCircle size={24} color={complianceColors.unknown} />
        }
        return icons[compliance] || icons.unknown
    }

    const complianceColors = {
        pass: '#10b981',
        partial: '#f97316',
        fail: '#ef4444',
        unknown: '#6b7280'
    }

    return (
        <div style={{
            background: colors.surface,
            border: `1px solid ${colors.border}`,
            borderRadius: '14px',
            padding: '24px',
            fontSize: '13px',
            lineHeight: '1.8',
            color: colors.text
        }}>
            {/* Header */}
            <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                marginBottom: '24px',
                paddingBottom: '16px',
                borderBottom: `2px solid ${colors.border}`
            }}>
                <span style={{ fontSize: '32px' }}>
                    {complianceIcon(report.overall_compliance)}
                </span>
                <div>
                    <h2 style={{
                        fontSize: '18px',
                        fontWeight: '700',
                        margin: 0,
                        color: colors.text
                    }}>Звіт валідації документа</h2>
                    <div style={{
                        fontSize: '14px',
                        fontWeight: '600',
                        marginTop: '4px',
                        color: complianceColors[report.overall_compliance]
                    }}>
                        Статус: {report.overall_compliance.toUpperCase()}
                    </div>
                </div>
            </div>

            {/* Validation Info */}
            {(validationCategories || timestamp) && (
                <div style={{
                    background: colors.inputBg,
                    borderRadius: '10px',
                    padding: '12px 16px',
                    marginBottom: '20px',
                    fontSize: '12px'
                }}>
                    {timestamp && (
                        <div style={{
                            color: colors.muted,
                            marginBottom: validationCategories && validationCategories.length > 0 ? '8px' : '0'
                        }}>
                            <strong>Дата валідації:</strong> {timestamp}
                        </div>
                    )}
                    <div>
                        <div style={{ color: colors.muted, marginBottom: '8px', fontSize: '11px' }}>
                            <strong>Категорії перевірки:</strong>
                        </div>
                        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                            {validationCategories && validationCategories.length > 0 ? (
                                validationCategories.map(cat => (
                                    <span key={cat} style={{
                                        padding: '4px 10px',
                                        background: colors.accent + '20',
                                        border: `1px solid ${colors.accent}`,
                                        borderRadius: '6px',
                                        fontSize: '11px',
                                        fontWeight: '600',
                                        color: colors.accent
                                    }}>
                                        {categoryLabels[cat] || cat}
                                    </span>
                                ))
                            ) : (
                                <span style={{
                                    padding: '4px 10px',
                                    background: colors.accent + '20',
                                    border: `1px solid ${colors.accent}`,
                                    borderRadius: '6px',
                                    fontSize: '11px',
                                    fontWeight: '600',
                                    color: colors.accent
                                }}>
                                    Всі категорії
                                </span>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Score */}
            <div style={{
                background: colors.inputBg,
                borderRadius: '10px',
                padding: '16px',
                marginBottom: '20px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
            }}>
                <div>
                    <div style={{ fontSize: '12px', color: colors.muted, marginBottom: '4px' }}>
                        Оцінка відповідності
                    </div>
                    <div style={{ fontSize: '24px', fontWeight: '700', color: colors.accent }}>
                        {(report.compliance_score * 100).toFixed(1)}%
                    </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '12px', color: colors.muted, marginBottom: '4px' }}>
                        Всього проблем
                    </div>
                    <div style={{ fontSize: '24px', fontWeight: '700', color: colors.text }}>
                        {report.summary.total_issues}
                    </div>
                </div>
            </div>

            {/* Summary */}
            {report.summary.total_issues > 0 && (
                <div style={{ marginBottom: '24px' }}>
                    <h3 style={{
                        fontSize: '15px',
                        fontWeight: '600',
                        marginBottom: '12px',
                        color: colors.text,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                    }}>
                        <BarChart3 size={18} />
                        Підсумок проблем
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px' }}>
                        {[
                            { severity: 'critical', label: 'Критичні' },
                            { severity: 'major', label: 'Важливі' },
                            { severity: 'minor', label: 'Незначні' },
                            { severity: 'info', label: 'Інформаційні' }
                        ].map(item => (
                            <div key={item.severity} style={{
                                background: colors.inputBg,
                                borderLeft: `3px solid ${severityColors[item.severity]}`,
                                borderRadius: '6px',
                                padding: '10px 12px',
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center'
                            }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    {severityIcon(item.severity)}
                                    <span style={{ fontSize: '12px', color: colors.textLight }}>
                                        {item.label}
                                    </span>
                                </div>
                                <span style={{
                                    fontSize: '16px',
                                    fontWeight: '600',
                                    color: severityColors[item.severity]
                                }}>
                                    {report.summary[item.severity]}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Issues */}
            {report.issues && report.issues.length > 0 && (
                <div>
                    <h3 style={{
                        fontSize: '15px',
                        fontWeight: '600',
                        marginBottom: '12px',
                        color: colors.text,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                    }}>
                        <Search size={18} />
                        Виявлені проблеми
                    </h3>

                    {['critical', 'major', 'minor', 'info'].map(severity => {
                        const severityIssues = report.issues.filter(i => i.severity === severity)
                        if (severityIssues.length === 0) return null

                        return (
                            <div key={severity} style={{ marginBottom: '20px' }}>
                                <div style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '8px',
                                    marginBottom: '10px',
                                    fontSize: '14px',
                                    fontWeight: '600',
                                    color: severityColors[severity]
                                }}>
                                    {severityIcon(severity)}
                                    <span>
                                        {severity === 'critical' ? 'Критичні проблеми' :
                                         severity === 'major' ? 'Важливі проблеми' :
                                         severity === 'minor' ? 'Незначні проблеми' : 'Інформаційні зауваження'}
                                    </span>
                                </div>

                                {severityIssues.map((issue, idx) => (
                                    <div key={idx} style={{
                                        background: colors.inputBg,
                                        borderLeft: `3px solid ${severityColors[severity]}`,
                                        borderRadius: '8px',
                                        padding: '14px',
                                        marginBottom: '10px'
                                    }}>
                                        <div style={{
                                            fontSize: '13px',
                                            fontWeight: '600',
                                            marginBottom: '8px',
                                            color: colors.text
                                        }}>
                                            {idx + 1}. {issue.description}
                                        </div>

                                        <div style={{ fontSize: '11px', color: colors.muted, marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                            <ClipboardList size={12} /> <strong>Норматив:</strong> {issue.regulatory_doc_name}
                                        </div>

                                        <div style={{ fontSize: '11px', color: colors.muted, marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                            <MapPin size={12} /> <strong>Розділ:</strong> {issue.section}
                                        </div>

                                        <div style={{ fontSize: '11px', color: colors.muted, marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                            <Tag size={12} /> <strong>Категорія:</strong> {issue.category}
                                        </div>

                                        {issue.user_doc_fragment && (
                                            <div style={{
                                                background: colors.surface,
                                                borderRadius: '6px',
                                                padding: '8px',
                                                marginTop: '8px',
                                                marginBottom: '8px',
                                                fontSize: '11px',
                                                color: colors.textLight,
                                                fontStyle: 'italic',
                                                display: 'flex',
                                                gap: '6px'
                                            }}>
                                                <FileText size={12} style={{ flexShrink: 0, marginTop: '2px' }} />
                                                <span>"{issue.user_doc_fragment.substring(0, 150)}..."</span>
                                            </div>
                                        )}

                                        {issue.recommendation && (
                                            <div style={{
                                                marginTop: '8px',
                                                padding: '8px',
                                                background: colors.surface,
                                                borderRadius: '6px',
                                                fontSize: '12px',
                                                color: colors.text,
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: '6px'
                                            }}>
                                                <Lightbulb size={14} style={{ flexShrink: 0 }} />
                                                <span><strong>Рекомендація:</strong> {issue.recommendation}</span>
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )
                    })}
                </div>
            )}

            {/* No Issues */}
            {report.summary.total_issues === 0 && (
                <div style={{
                    textAlign: 'center',
                    padding: '32px',
                    background: colors.inputBg,
                    borderRadius: '10px',
                    color: '#10b981'
                }}>
                    <div style={{ fontSize: '48px', marginBottom: '12px' }}>🎉</div>
                    <div style={{ fontSize: '16px', fontWeight: '600', marginBottom: '8px' }}>
                        Проблем не виявлено!
                    </div>
                    <div style={{ fontSize: '13px', color: colors.muted }}>
                        Документ повністю відповідає всім нормативним вимогам
                    </div>
                </div>
            )}
        </div>
    )
}

export default function Home() {
    const { showToast } = useToast()
    const { user, logout } = useAuth()
    const [showUserMenu, setShowUserMenu] = useState(false)
    const [showDocsSidebar, setShowDocsSidebar] = useState(false)
    const [messages, setMessages] = useState([
        {
            role: 'assistant',
            content: 'Привіт! Я AI асистент для навчальних матеріалів. Завантаж документ і я допоможу створити конспект, тест, флеш-картки або відповім на твої питання по темі.'
        }
    ])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [loadingChatHistory, setLoadingChatHistory] = useState(false)
    const [currentDoc, setCurrentDoc] = useState(null)
    const [uploading, setUploading] = useState(false)
    const [previews, setPreviews] = useState([])
    const [previewIndex, setPreviewIndex] = useState(0)
    const [sidebarOpen, setSidebarOpen] = useState(false)
    const [showUploadMenu, setShowUploadMenu] = useState(false)
    const [showActionsPopup, setShowActionsPopup] = useState(false)
    const [showRegulatoryDialog, setShowRegulatoryDialog] = useState(false)
    const [showValidationDialog, setShowValidationDialog] = useState(false)
    const [regulatoryDocs, setRegulatoryDocs] = useState([])
    const [pendingRegulatoryFile, setPendingRegulatoryFile] = useState(null)
    const fileRef = useRef(null)
    const bottomRef = useRef(null)
    const uploadMenuRef = useRef(null)
    const userMenuRef = useRef(null)
    const docsSidebarRef = useRef(null)

    const preview = previews[previewIndex] || null

    const typeLabels = {
        summary: 'Конспект',
        quiz: 'Тест',
        flashcards: 'Флеш-картки',
        glossary: 'Глосарій',
        validation: 'Звіт валідації'
    }

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    useEffect(() => {
        function handleClickOutside(event) {
            if (uploadMenuRef.current && !uploadMenuRef.current.contains(event.target)) {
                setShowUploadMenu(false)
            }
            if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
                setShowUserMenu(false)
            }
        }
        document.addEventListener('mousedown', handleClickOutside)
        return () => document.removeEventListener('mousedown', handleClickOutside)
    }, [])

    // Завантажуємо історію чату при зміні документа
    useEffect(() => {
        setLoadingChatHistory(true)

        // Невелика затримка для плавної анімації
        setTimeout(() => {
            const chatKey = currentDoc ? `chat_doc_${currentDoc.id}` : 'chat_general'
            const savedMessages = localStorage.getItem(chatKey)

            if (savedMessages) {
                try {
                    setMessages(JSON.parse(savedMessages))
                } catch (e) {
                    console.error('Помилка завантаження історії чату:', e)
                    // Якщо помилка - встановлюємо дефолтне повідомлення
                    setMessages([{
                        role: 'assistant',
                        content: 'Привіт! Я AI асистент для навчальних матеріалів. Завантаж документ і я допоможу створити конспект, тест, флеш-картки або відповім на твої питання по темі.'
                    }])
                }
            } else {
                // Якщо немає збереженої історії - дефолтне повідомлення
                setMessages([{
                    role: 'assistant',
                    content: 'Привіт! Я AI асистент для навчальних матеріалів. Завантаж документ і я допоможу створити конспект, тест, флеш-картки або відповім на твої питання по темі.'
                }])
            }

            setLoadingChatHistory(false)
        }, 300)
    }, [currentDoc])

    // Зберігаємо історію чату при зміні messages
    useEffect(() => {
        if (messages.length > 0) {
            const chatKey = currentDoc ? `chat_doc_${currentDoc.id}` : 'chat_general'
            localStorage.setItem(chatKey, JSON.stringify(messages))
        }
    }, [messages, currentDoc])

    // Завантажуємо нормативні документи при старті
    useEffect(() => {
        async function loadRegulatoryDocs() {
            try {
                const res = await API.get('/documents/regulatory')
                setRegulatoryDocs(res.data || [])
                console.log(`Завантажено ${res.data?.length || 0} нормативних документів`)
            } catch (err) {
                console.error('Помилка завантаження нормативних документів:', err)
            }
        }
        loadRegulatoryDocs()
    }, [])

    async function handleFileUpload(file, isRegulatory, category = null, tags = null) {
        if (!file) return
        setUploading(true)
        setShowUploadMenu(false)

        // Додаємо файл в чат зі сторони користувача
        const categoryLabel = category ? ` (${category})` : ''
        addMessage('user', `${file.name}${categoryLabel}`)

        const formData = new FormData()
        formData.append('file', file)

        if (isRegulatory) {
            if (category) formData.append('regulatory_category', category)
            if (tags) formData.append('tags', tags)
        }

        try {
            const endpoint = isRegulatory ? '/upload/regulatory' : '/upload'
            const res = await API.post(endpoint, formData)

            if (isRegulatory) {
                setRegulatoryDocs(prev => [...prev, res.data])
                const status = res.data.status === 'exists' || res.data.status === 'exists_by_hash' ? 'вже є в базі' : 'додано'
                showToast(`Нормативний документ "${file.name}" ${status}!`, 'success')
                // Оновлюємо список документів
                refreshDocumentsList()
            } else {
                setCurrentDoc(res.data)
                const status = res.data.status === 'exists' || res.data.status === 'exists_by_hash' ? 'вже є в базі' : 'завантажено'
                showToast(`Документ "${file.name}" ${status}!`, 'success')
                setShowActionsPopup(true)
                // Оновлюємо список документів
                refreshDocumentsList()
            }
        } catch (err) {
            const errorMsg = err.response?.data?.detail || 'Помилка завантаження файлу'
            showToast(errorMsg, 'error')
        } finally {
            setUploading(false)
        }
    }

    function handleFileSelect(isRegulatory) {
        const input = document.createElement('input')
        input.type = 'file'
        input.accept = '.pdf,.docx'
        input.onchange = (e) => {
            const file = e.target.files[0]
            if (file) {
                if (isRegulatory) {
                    // Для нормативних документів показуємо діалог вибору категорії
                    setPendingRegulatoryFile(file)
                    setShowRegulatoryDialog(true)
                    setShowUploadMenu(false)
                } else {
                    handleFileUpload(file, false)
                }
            }
        }
        input.click()
    }

    function addMessage(role, content, extra = {}) {
        setMessages(prev => [...prev, { role, content, ...extra }])
    }

    function detectMaterialType(text) {
        const t = text.toLowerCase()
        if (t.includes('конспект')) return 'summary'
        if (t.includes('тест') || t.includes('питання')) return 'quiz'
        if (t.includes('флеш') || t.includes('картк')) return 'flashcards'
        if (t.includes('глосарій') || t.includes('терміни')) return 'glossary'
        return null
    }

    async function sendMessage() {
        if (!input.trim() || loading) return
        const question = input.trim()
        setInput('')
        addMessage('user', question)
        setLoading(true)
        try {
            if (!currentDoc) {
                const res = await API.post('/chat/general', { question, history: messages })
                addMessage('assistant', res.data.answer)
                return
            }
            const materialType = detectMaterialType(question)
            if (materialType) {
                addMessage('assistant', 'Генерую, зачекай...')
                const res = await API.post(`/generate/${currentDoc.id}?type=${materialType}`)
                const content = res.data.result
                setMessages(prev => {
                    const updated = [...prev]
                    updated[updated.length - 1] = {
                        role: 'assistant',
                        content: `${typeLabels[materialType]} готовий! Переглянь у правій панелі.`,
                        materialType,
                        docId: currentDoc.id
                    }
                    return updated
                })
                setPreviews(prev => {
                    const updated = [...prev, { content, materialType, docId: currentDoc.id }]
                    setPreviewIndex(updated.length - 1)
                    return updated
                })
                setSidebarOpen(true)
                setShowDocsSidebar(false) // Закриваємо лівий sidebar
            } else {
                const res = await API.post(`/chat/${currentDoc.id}`, { question, history: messages })
                addMessage('assistant', res.data.answer)
            }
        } catch (err) {
            const errorMsg = err.response?.data?.detail || 'Виникла помилка при обробці запиту'
            showToast(errorMsg, 'error')
            addMessage('assistant', 'Виникла помилка. Спробуй ще раз.')
        } finally {
            setLoading(false)
        }
    }

    async function validateDocument(selectedCategories = []) {
        if (!currentDoc) return
        setLoading(true)
        setShowActionsPopup(false)

        const categoryText = selectedCategories.length > 0
            ? ` (${selectedCategories.join(', ')})`
            : ' (всі категорії)'

        addMessage('assistant', `Валідую документ${categoryText}...`)

        try {
            const body = selectedCategories.length > 0
                ? { categories: selectedCategories }
                : {}

            const res = await API.post(`/validate/${currentDoc.id}`, body)
            const result = res.data

            addMessage('assistant', `Валідація завершена! Звіт у правій панелі.`)

            setPreviews(prev => {
                const updated = [...prev, {
                    content: result,
                    materialType: 'validation',
                    docId: currentDoc.id,
                    isValidation: true,
                    validationCategories: selectedCategories,
                    timestamp: new Date().toLocaleString('uk-UA'),
                    reportId: result.report_id  // Зберігаємо ID звіту для завантаження
                }]
                setPreviewIndex(updated.length - 1)
                return updated
            })
            setSidebarOpen(true)
            setShowDocsSidebar(false) // Закриваємо лівий sidebar
        } catch (err) {
            console.error('Validation error:', err)
            console.error('Error response:', err.response?.data)
            const errorMsg = err.response?.data?.detail || 'Помилка валідації документу'

            // Якщо помилка про відсутність чанків - пропонуємо переіндексацію
            if (errorMsg.includes('проіндексованого вмісту') || errorMsg.includes('не містить текстового вмісту')) {
                const shouldReindex = window.confirm(
                    `${errorMsg}\n\nХочете спробувати переіндексувати документ автоматично?`
                )
                if (shouldReindex) {
                    await reindexDocument(currentDoc.id)
                    return
                }
            }

            showToast(errorMsg, 'error')
        } finally {
            setLoading(false)
        }
    }

    async function reindexDocument(docId) {
        setLoading(true)
        addMessage('assistant', '🔄 Переіндексую документ...')

        try {
            await API.post(`/documents/${docId}/reindex`)
            showToast('Документ успішно переіндексовано!', 'success')
            addMessage('assistant', '✅ Документ переіндексовано. Спробуйте валідацію ще раз.')
        } catch (err) {
            const errorMsg = err.response?.data?.detail || 'Помилка переіндексації'
            showToast(errorMsg, 'error')
            addMessage('assistant', `❌ Помилка: ${errorMsg}`)
        } finally {
            setLoading(false)
        }
    }

    async function checkDocumentHealth(docId) {
        try {
            const res = await API.get(`/documents/${docId}/diagnostic`)
            const diag = res.data

            console.log('Document diagnostic:', diag)

            let message = `📊 Діагностика документа:\n\n`
            message += `📄 Файл: ${diag.filename}\n`
            message += `📈 Статус: ${diag.status}\n`
            message += `🗄️ Чанків у Qdrant: ${diag.qdrant_chunks}\n`
            message += `✅ Готовий до валідації: ${diag.is_ready_for_validation ? 'Так' : 'Ні'}\n`

            if (diag.has_issues) {
                message += `\n⚠️ Проблеми:\n`
                diag.issues.forEach(issue => {
                    message += `  • ${issue}\n`
                })
            }

            addMessage('assistant', message)

            if (!diag.is_ready_for_validation) {
                const shouldFix = window.confirm('Документ має проблеми. Спробувати виправити автоматично?')
                if (shouldFix) {
                    await reindexDocument(docId)
                }
            }
        } catch (err) {
            console.error('Diagnostic error:', err)
            showToast('Помилка діагностики', 'error')
        }
    }

    async function downloadDocx(docId, materialType) {
        try {
            const res = await API.get(`/download/${docId}/${materialType}`, { responseType: 'blob' })
            const url = URL.createObjectURL(res.data)
            const a = document.createElement('a')
            a.href = url
            a.download = `${materialType}.docx`
            a.click()
            showToast('Файл успішно завантажено', 'success')
        } catch (err) {
            const errorMsg = err.response?.data?.detail || 'Помилка завантаження файлу'
            showToast(errorMsg, 'error')
        }
    }

    async function downloadValidationReport(docId, reportId) {
        try {
            const url = reportId
                ? `/validate/${docId}/report/${reportId}/download`
                : `/validate/${docId}/report/download`
            const res = await API.get(url, { responseType: 'blob' })
            const blobUrl = URL.createObjectURL(res.data)
            const a = document.createElement('a')
            a.href = blobUrl
            a.download = `validation_report_${docId}.docx`
            a.click()
            showToast('Звіт успішно завантажено', 'success')
        } catch (err) {
            const errorMsg = err.response?.data?.detail || 'Помилка завантаження звіту валідації'
            showToast(errorMsg, 'error')
        }
    }

    function handleKey(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            sendMessage()
        }
    }

    // Діалог вибору категорії нормативного документу
    const RegulatoryDialog = () => {
        const [category, setCategory] = useState('')
        const [tags, setTags] = useState('')

        const categories = [
            { value: 'content', label: 'Змістовна валідація', desc: 'Закони, положення (що має бути)' },
            { value: 'formatting', label: 'Форматна валідація', desc: 'ДСТУ, шрифти, відступи (як має виглядати)' },
            { value: 'structure', label: 'Структурна валідація', desc: 'Вимоги до розділів та порядку' },
            { value: 'references', label: 'Валідація посилань', desc: 'Вимоги до цитування' }
        ]

        return (
            <div style={{
                position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                background: 'rgba(0,0,0,0.7)', zIndex: 3000,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                padding: '20px'
            }}
                 onClick={() => {
                     setShowRegulatoryDialog(false)
                     setPendingRegulatoryFile(null)
                 }}
            >
                <div
                    onClick={(e) => e.stopPropagation()}
                    style={{
                        background: COLORS.surface,
                        border: `1px solid ${COLORS.border}`,
                        borderRadius: '16px',
                        padding: '24px',
                        maxWidth: '500px',
                        width: '100%',
                        boxShadow: '0 8px 32px rgba(0,0,0,0.5)'
                    }}
                >
                    <h3 style={{ fontSize: '16px', fontWeight: '600', color: COLORS.text, marginBottom: '8px' }}>
                        Категорія нормативного документу
                    </h3>
                    <p style={{ fontSize: '13px', color: COLORS.muted, marginBottom: '20px' }}>
                        {pendingRegulatoryFile?.name}
                    </p>

                    <div style={{ marginBottom: '20px' }}>
                        {categories.map(cat => (
                            <label
                                key={cat.value}
                                style={{
                                    display: 'flex',
                                    alignItems: 'flex-start',
                                    gap: '12px',
                                    padding: '12px',
                                    background: category === cat.value ? COLORS.accentLight : 'transparent',
                                    border: `1px solid ${category === cat.value ? COLORS.accent : COLORS.border}`,
                                    borderRadius: '10px',
                                    marginBottom: '8px',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s'
                                }}
                            >
                                <input
                                    type="radio"
                                    name="category"
                                    value={cat.value}
                                    checked={category === cat.value}
                                    onChange={(e) => setCategory(e.target.value)}
                                    style={{ marginTop: '2px' }}
                                />
                                <div style={{ flex: 1 }}>
                                    <div style={{ fontSize: '14px', fontWeight: '600', color: COLORS.text, marginBottom: '4px' }}>
                                        {cat.label}
                                    </div>
                                    <div style={{ fontSize: '12px', color: COLORS.muted }}>
                                        {cat.desc}
                                    </div>
                                </div>
                            </label>
                        ))}
                    </div>

                    <div style={{ marginBottom: '20px' }}>
                        <label style={{ fontSize: '13px', color: COLORS.text, display: 'block', marginBottom: '8px' }}>
                            Теги (опціонально, через кому)
                        </label>
                        <input
                            type="text"
                            value={tags}
                            onChange={(e) => setTags(e.target.value)}
                            placeholder="ДСТУ, освіта, 2024"
                            style={{
                                width: '100%',
                                padding: '10px 12px',
                                background: COLORS.inputBg,
                                border: `1px solid ${COLORS.border}`,
                                borderRadius: '8px',
                                fontSize: '13px',
                                color: COLORS.text,
                                outline: 'none'
                            }}
                        />
                    </div>

                    <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                        <button
                            onClick={() => {
                                setShowRegulatoryDialog(false)
                                setPendingRegulatoryFile(null)
                            }}
                            style={{
                                padding: '10px 20px',
                                background: 'transparent',
                                border: `1px solid ${COLORS.border}`,
                                borderRadius: '8px',
                                color: COLORS.text,
                                fontSize: '13px',
                                cursor: 'pointer'
                            }}
                        >
                            Скасувати
                        </button>
                        <button
                            onClick={() => {
                                handleFileUpload(pendingRegulatoryFile, true, category, tags.trim() || null)
                                setShowRegulatoryDialog(false)
                                setPendingRegulatoryFile(null)
                            }}
                            disabled={!category}
                            style={{
                                padding: '10px 20px',
                                background: category ? COLORS.accent : COLORS.border,
                                border: 'none',
                                borderRadius: '8px',
                                color: '#fff',
                                fontSize: '13px',
                                cursor: category ? 'pointer' : 'not-allowed',
                                fontWeight: '600'
                            }}
                        >
                            Завантажити
                        </button>
                    </div>
                </div>
            </div>
        )
    }

    // Діалог вибору категорій валідації
    const ValidationDialog = () => {
        const [selectedCategories, setSelectedCategories] = useState([])

        const categories = [
            { value: 'content', label: 'Змістовна', desc: 'Перевірити зміст' },
            { value: 'formatting', label: 'Форматна', desc: 'Перевірити оформлення' },
            { value: 'structure', label: 'Структурна', desc: 'Перевірити структуру' },
            { value: 'references', label: 'Посилання', desc: 'Перевірити цитування' }
        ]

        const toggleCategory = (cat) => {
            setSelectedCategories(prev =>
                prev.includes(cat) ? prev.filter(c => c !== cat) : [...prev, cat]
            )
        }

        return (
            <div style={{
                position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                background: 'rgba(0,0,0,0.7)', zIndex: 3000,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                padding: '20px'
            }}
                 onClick={() => setShowValidationDialog(false)}
            >
                <div
                    onClick={(e) => e.stopPropagation()}
                    style={{
                        background: COLORS.surface,
                        border: `1px solid ${COLORS.border}`,
                        borderRadius: '16px',
                        padding: '24px',
                        maxWidth: '500px',
                        width: '100%',
                        boxShadow: '0 8px 32px rgba(0,0,0,0.5)'
                    }}
                >
                    <h3 style={{ fontSize: '16px', fontWeight: '600', color: COLORS.text, marginBottom: '8px' }}>
                        Вибір типу валідації
                    </h3>
                    <p style={{ fontSize: '13px', color: COLORS.muted, marginBottom: '20px' }}>
                        Оберіть які типи перевірки виконати (якщо нічого не обрано - перевіряються всі)
                    </p>

                    <div style={{ marginBottom: '20px' }}>
                        {categories.map(cat => (
                            <label
                                key={cat.value}
                                style={{
                                    display: 'flex',
                                    alignItems: 'flex-start',
                                    gap: '12px',
                                    padding: '12px',
                                    background: selectedCategories.includes(cat.value) ? COLORS.accentLight : 'transparent',
                                    border: `1px solid ${selectedCategories.includes(cat.value) ? COLORS.accent : COLORS.border}`,
                                    borderRadius: '10px',
                                    marginBottom: '8px',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s'
                                }}
                                onClick={() => toggleCategory(cat.value)}
                            >
                                <input
                                    type="checkbox"
                                    checked={selectedCategories.includes(cat.value)}
                                    onChange={() => toggleCategory(cat.value)}
                                    style={{ marginTop: '2px' }}
                                />
                                <div style={{ flex: 1 }}>
                                    <div style={{ fontSize: '14px', fontWeight: '600', color: COLORS.text, marginBottom: '4px' }}>
                                        {cat.label}
                                    </div>
                                    <div style={{ fontSize: '12px', color: COLORS.muted }}>
                                        {cat.desc}
                                    </div>
                                </div>
                            </label>
                        ))}
                    </div>

                    <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                        <button
                            onClick={() => setShowValidationDialog(false)}
                            style={{
                                padding: '10px 20px',
                                background: 'transparent',
                                border: `1px solid ${COLORS.border}`,
                                borderRadius: '8px',
                                color: COLORS.text,
                                fontSize: '13px',
                                cursor: 'pointer'
                            }}
                        >
                            Скасувати
                        </button>
                        <button
                            onClick={() => {
                                validateDocument(selectedCategories)
                                setShowValidationDialog(false)
                            }}
                            style={{
                                padding: '10px 20px',
                                background: COLORS.accent,
                                border: 'none',
                                borderRadius: '8px',
                                color: '#fff',
                                fontSize: '13px',
                                cursor: 'pointer',
                                fontWeight: '600'
                            }}
                        >
                            {selectedCategories.length > 0
                                ? `Валідувати (${selectedCategories.length})`
                                : 'Валідувати все'}
                        </button>
                    </div>
                </div>
            </div>
        )
    }

    function handleDocumentSelect(doc) {
        setCurrentDoc(doc)

        // Нормативні документи не додаємо в чат і не показуємо popup меню
        const isRegulatory = doc?.document_type === 'regulatory' || doc?.regulatory_category

        if (doc && !isRegulatory) {
            addMessage('user', `Обрано документ: ${doc.filename}`)
            setShowActionsPopup(true)
        }
    }

    function refreshDocumentsList() {
        // Викликаємо метод оновлення в DocumentsSidebar через ref
        if (docsSidebarRef.current?.loadDocuments) {
            docsSidebarRef.current.loadDocuments()
        }
    }

    return (
        <div style={{ display: 'flex', height: '100vh', background: '#000', justifyContent: 'center' }}>
            {/* Documents Sidebar */}
            <div style={{
                position: 'fixed',
                left: 0,
                top: 0,
                height: '100vh',
                zIndex: 1000,
                transform: showDocsSidebar ? 'translateX(0)' : 'translateX(-100%)',
                transition: 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                pointerEvents: showDocsSidebar ? 'auto' : 'none'
            }}>
                <DocumentsSidebar
                    ref={docsSidebarRef}
                    currentDoc={currentDoc}
                    onDocumentSelect={handleDocumentSelect}
                    onClose={() => setShowDocsSidebar(false)}
                />
            </div>

            <div style={{ display: 'flex', height: '100vh', width: '100%', maxWidth: sidebarOpen ? '1400px' : '900px', background: COLORS.bg, gap: '12px', overflow: 'hidden', transition: 'max-width 0.3s ease' }}>

            {/* LEFT — Chat */}
            <div style={{
                flex: 1, display: 'flex', flexDirection: 'column',
                background: COLORS.surface, minWidth: 0,
                borderRight: sidebarOpen ? `1px solid ${COLORS.border}` : 'none'
            }}>

                {/* Header */}
                <div style={{
                    padding: '14px 20px',
                    borderBottom: `1px solid ${COLORS.border}`,
                    display: 'flex', alignItems: 'center', gap: '10px',
                    background: COLORS.surface
                }}>
                    {/* Menu Button */}
                    <button
                        onClick={() => setShowDocsSidebar(!showDocsSidebar)}
                        title="Документи"
                        style={{
                            width: '32px',
                            height: '32px',
                            border: `1px solid ${showDocsSidebar ? COLORS.accent : COLORS.border}`,
                            borderRadius: '8px',
                            background: showDocsSidebar ? COLORS.accentLight : 'transparent',
                            cursor: 'pointer',
                            fontSize: '16px',
                            color: showDocsSidebar ? COLORS.accent : COLORS.muted,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            transition: 'all .2s'
                        }}
                    >
                        <Menu size={18} />
                    </button>

                    <div style={{
                        width: '32px', height: '32px',
                        background: COLORS.accent,
                        borderRadius: '10px',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        color: '#fff', fontSize: '13px', fontWeight: '700',
                        boxShadow: '0 2px 8px rgba(249,115,22,0.3)'
                    }}>E</div>
                    <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: '700', fontSize: '14px', color: COLORS.text }}>EduAssistant</div>
                        {currentDoc
                            ? <div style={{ fontSize: '11px', color: COLORS.accentText, fontWeight: '500' }}>{currentDoc.filename}</div>
                            : <div style={{ fontSize: '11px', color: COLORS.muted }}>AI асистент для навчання</div>
                        }
                    </div>
                    {/* User Menu */}
                    <div ref={userMenuRef} style={{ position: 'relative' }}>
                        <button
                            onClick={() => setShowUserMenu(!showUserMenu)}
                            title={user?.email}
                            style={{
                                padding: '6px',
                                border: `1px solid ${COLORS.border}`,
                                borderRadius: '8px',
                                background: showUserMenu ? COLORS.accentLight : 'transparent',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                transition: 'all .2s'
                            }}
                        >
                            <div style={{
                                width: '32px',
                                height: '32px',
                                borderRadius: '50%',
                                background: '#6b7280',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                color: '#fff',
                                fontSize: '14px',
                                fontWeight: '600'
                            }}>
                                {user?.email?.charAt(0).toUpperCase() || 'U'}
                            </div>
                        </button>

                        {showUserMenu && (
                            <div style={{
                                position: 'absolute',
                                top: '40px',
                                right: '0',
                                background: COLORS.surface,
                                border: `1px solid ${COLORS.border}`,
                                borderRadius: '10px',
                                boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
                                minWidth: '180px',
                                zIndex: 1000,
                                overflow: 'hidden'
                            }}>
                                <div style={{
                                    padding: '12px 16px',
                                    borderBottom: `1px solid ${COLORS.border}`,
                                    fontSize: '12px',
                                    color: COLORS.muted
                                }}>
                                    {user?.email}
                                </div>
                                <button
                                    onClick={async () => {
                                        try {
                                            await logout()
                                            showToast('Ви успішно вийшли', 'success')
                                        } catch (error) {
                                            showToast('Помилка виходу', 'error')
                                        }
                                    }}
                                    style={{
                                        width: '100%',
                                        padding: '12px 16px',
                                        background: 'transparent',
                                        border: 'none',
                                        color: COLORS.text,
                                        fontSize: '13px',
                                        textAlign: 'left',
                                        cursor: 'pointer',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '10px',
                                        transition: 'background 0.2s'
                                    }}
                                    onMouseEnter={(e) => e.target.style.background = COLORS.accentLight}
                                    onMouseLeave={(e) => e.target.style.background = 'transparent'}
                                >
                                    <LogOut size={16} />
                                    <span>Вийти</span>
                                </button>
                            </div>
                        )}
                    </div>
                    <button
                        onClick={() => {
                            setSidebarOpen(prev => !prev)
                            // Закриваємо лівий sidebar при відкритті правого
                            if (!sidebarOpen) {
                                setShowDocsSidebar(false)
                            }
                        }}
                        title={sidebarOpen ? 'Закрити панель' : 'Відкрити панель'}
                        style={{
                            width: '32px', height: '32px',
                            border: `1px solid ${sidebarOpen ? COLORS.accent : COLORS.border}`,
                            borderRadius: '8px',
                            background: sidebarOpen ? COLORS.accentLight : 'transparent',
                            cursor: 'pointer', fontSize: '14px',
                            color: sidebarOpen ? COLORS.accent : COLORS.muted,
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            transition: 'all .2s'
                        }}
                    >
                        {sidebarOpen ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
                    </button>
                </div>

                {/* Messages */}
                <div style={{
                    flex: 1, overflowY: 'auto', padding: '20px',
                    display: 'flex', flexDirection: 'column', gap: '16px',
                    background: COLORS.bg
                }}>
                    {loadingChatHistory && (
                        <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            padding: '40px',
                            gap: '12px'
                        }}>
                            <div style={{
                                width: '20px',
                                height: '20px',
                                border: `3px solid ${COLORS.border}`,
                                borderTop: `3px solid ${COLORS.accent}`,
                                borderRadius: '50%',
                                animation: 'spin 0.8s linear infinite'
                            }} />
                            <span style={{
                                fontSize: '13px',
                                color: COLORS.muted
                            }}>Завантаження історії чату...</span>
                        </div>
                    )}

                    {!loadingChatHistory && messages.map((msg, i) => (
                        <div key={i} style={{
                            display: 'flex',
                            justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                            gap: '10px', alignItems: 'flex-start'
                        }}>
                            {msg.role === 'assistant' && (
                                <div style={{
                                    width: '28px', height: '28px', flexShrink: 0,
                                    background: COLORS.accent,
                                    borderRadius: '8px',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    color: '#fff', fontSize: '10px', fontWeight: '700', marginTop: '2px',
                                    boxShadow: '0 2px 6px rgba(249,115,22,0.25)'
                                }}>E</div>
                            )}
                            <div style={{ maxWidth: '80%' }}>
                                <div style={{
                                    padding: '11px 15px',
                                    borderRadius: msg.role === 'user' ? '18px 4px 18px 18px' : '4px 18px 18px 18px',
                                    background: msg.role === 'user' ? COLORS.userBubble : COLORS.surface,
                                    color: msg.role === 'user' ? '#fff' : COLORS.text,
                                    fontSize: '13px', lineHeight: '1.7',
                                    whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                                    border: msg.role === 'assistant' ? `1px solid ${COLORS.border}` : 'none',
                                    boxShadow: msg.role === 'assistant' ? '0 1px 4px rgba(0,0,0,0.04)' : 'none'
                                }}>
                                    {msg.content}
                                </div>
                                {msg.materialType && (
                                    <div style={{
                                        marginTop: '5px', fontSize: '11px',
                                        color: COLORS.accentText, fontWeight: '500'
                                    }}>
                                        Результат у правій панелі →
                                    </div>
                                )}
                            </div>
                            {msg.role === 'user' && (
                                <div style={{
                                    width: '28px', height: '28px', flexShrink: 0,
                                    background: '#6b7280',
                                    borderRadius: '50%',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    color: '#fff', fontSize: '10px', fontWeight: '700', marginTop: '2px',
                                    boxShadow: '0 2px 6px rgba(107,114,128,0.25)'
                                }}>
                                    {user?.email?.charAt(0).toUpperCase() || 'U'}
                                </div>
                            )}
                        </div>
                    ))}

                    {loading && (
                        <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
                            <div style={{
                                width: '28px', height: '28px', flexShrink: 0,
                                background: COLORS.accent,
                                borderRadius: '8px',
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                color: '#fff', fontSize: '10px', fontWeight: '700',
                                boxShadow: '0 2px 6px rgba(249,115,22,0.25)'
                            }}>E</div>
                            <div style={{
                                padding: '11px 15px', background: COLORS.surface,
                                border: `1px solid ${COLORS.border}`,
                                borderRadius: '4px 18px 18px 18px',
                                fontSize: '16px', color: COLORS.muted, letterSpacing: '3px'
                            }}>···</div>
                        </div>
                    )}
                    <div ref={bottomRef} />
                </div>

                {/* Input */}
                <div style={{
                    padding: '12px 20px 20px',
                    background: COLORS.surface,
                    borderTop: `1px solid ${COLORS.border}`,
                    position: 'relative'
                }}>
                    <div style={{
                        background: COLORS.inputBg,
                        borderRadius: '16px',
                        padding: '10px 12px',
                        display: 'flex', alignItems: 'flex-end', gap: '8px',
                        border: `1px solid ${COLORS.border}`
                    }}>
                        <div style={{ position: 'relative' }} ref={uploadMenuRef}>
                            <button
                                onClick={() => setShowUploadMenu(!showUploadMenu)}
                                disabled={uploading}
                                title="Завантажити документ"
                                style={{
                                    width: '32px', height: '32px', flexShrink: 0,
                                    border: `1px solid ${COLORS.border}`, borderRadius: '8px',
                                    background: COLORS.surface, cursor: 'pointer',
                                    fontSize: '16px', color: uploading ? COLORS.muted : COLORS.accent,
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    lineHeight: 1, transition: 'all .2s'
                                }}
                            >
                                <Paperclip size={18} />
                            </button>

                            {showUploadMenu && (
                                <div style={{
                                    position: 'absolute',
                                    bottom: '40px',
                                    left: '0',
                                    background: COLORS.surface,
                                    border: `1px solid ${COLORS.border}`,
                                    borderRadius: '12px',
                                    boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
                                    minWidth: '240px',
                                    zIndex: 1000,
                                    overflow: 'hidden'
                                }}>
                                    <button
                                        onClick={() => handleFileSelect(true)}
                                        style={{
                                            width: '100%',
                                            padding: '12px 16px',
                                            background: 'transparent',
                                            border: 'none',
                                            borderBottom: `1px solid ${COLORS.border}`,
                                            color: COLORS.text,
                                            fontSize: '13px',
                                            textAlign: 'left',
                                            cursor: 'pointer',
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '10px',
                                            transition: 'background 0.2s'
                                        }}
                                        onMouseEnter={(e) => e.target.style.background = COLORS.accentLight}
                                        onMouseLeave={(e) => e.target.style.background = 'transparent'}
                                    >
                                        <ClipboardList size={16} />
                                        <span>Додати нормативний документ</span>
                                    </button>
                                    <button
                                        onClick={() => handleFileSelect(false)}
                                        style={{
                                            width: '100%',
                                            padding: '12px 16px',
                                            background: 'transparent',
                                            border: 'none',
                                            color: COLORS.text,
                                            fontSize: '13px',
                                            textAlign: 'left',
                                            cursor: 'pointer',
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '10px',
                                            transition: 'background 0.2s'
                                        }}
                                        onMouseEnter={(e) => e.target.style.background = COLORS.accentLight}
                                        onMouseLeave={(e) => e.target.style.background = 'transparent'}
                                    >
                                        <FileText size={16} />
                                        <span>Додати документ для опрацювання</span>
                                    </button>
                                </div>
                            )}
                        </div>
                        {currentDoc && (
                            <button
                                onClick={() => setShowActionsPopup(!showActionsPopup)}
                                title="Дії з документом"
                                style={{
                                    width: '32px',
                                    height: '32px',
                                    flexShrink: 0,
                                    border: `1px solid ${COLORS.border}`,
                                    borderRadius: '8px',
                                    background: COLORS.surface,
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    transition: 'transform 0.3s ease',
                                    transform: showActionsPopup ? 'rotate(180deg)' : 'rotate(0deg)'
                                }}
                            >
                                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                                    <path
                                        d="M4 6L8 10L12 6"
                                        stroke={COLORS.accent}
                                        strokeWidth="2"
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                    />
                                </svg>
                            </button>
                        )}
                        <textarea
                            value={input}
                            onChange={e => setInput(e.target.value)}
                            onKeyDown={handleKey}
                            placeholder={currentDoc
                                ? 'конспект, тест, флеш-картки або питання...'
                                : 'Напиши щось або завантаж документ...'}
                            rows={1}
                            style={{
                                flex: 1, resize: 'none', border: 'none', outline: 'none',
                                fontSize: '13px', fontFamily: 'inherit',
                                lineHeight: '1.6', background: 'transparent',
                                maxHeight: '100px', overflowY: 'auto', color: COLORS.text
                            }}
                            onInput={e => {
                                e.target.style.height = 'auto'
                                e.target.style.height = e.target.scrollHeight + 'px'
                            }}
                        />
                        <button
                            onClick={sendMessage}
                            disabled={loading || !input.trim()}
                            style={{
                                width: '32px', height: '32px', flexShrink: 0,
                                background: loading || !input.trim()
                                    ? COLORS.border
                                    : COLORS.accent,
                                border: 'none', borderRadius: '8px',
                                cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
                                color: '#fff', fontSize: '14px',
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                boxShadow: loading || !input.trim() ? 'none' : '0 2px 8px rgba(249,115,22,0.35)',
                                transition: 'all .2s'
                            }}
                        ><CornerRightUp size={16} /></button>
                    </div>
                    <p style={{ fontSize: '11px', color: COLORS.muted, textAlign: 'center', marginTop: '8px' }}>
                        EduAssistant відповідає на основі завантаженого документу
                    </p>
                </div>
            </div>

            {/* RIGHT — Preview sidebar */}
            <div style={{
                width: sidebarOpen ? '420px' : '0px',
                flexShrink: 0,
                display: 'flex',
                flexDirection: 'column',
                background: COLORS.surfaceAlt,
                borderLeft: sidebarOpen ? `1px solid ${COLORS.border}` : 'none',
                overflow: 'hidden',
                transition: 'width .25s ease'
            }}>
                {previews.length > 0 ? (
                    <>
                        <div style={{
                            padding: '14px 20px',
                            borderBottom: `1px solid ${COLORS.border}`,
                            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                            minWidth: '420px',
                            background: COLORS.surface
                        }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                <div style={{ display: 'flex', gap: '4px' }}>
                                    <button
                                        onClick={() => setPreviewIndex(i => Math.max(0, i - 1))}
                                        disabled={previewIndex === 0}
                                        style={{
                                            width: '28px', height: '28px',
                                            border: `1px solid ${COLORS.border}`, borderRadius: '7px',
                                            background: previewIndex === 0 ? 'transparent' : COLORS.accentLight,
                                            cursor: previewIndex === 0 ? 'not-allowed' : 'pointer',
                                            color: previewIndex === 0 ? COLORS.muted : COLORS.accent,
                                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                                            fontSize: '15px', transition: 'all .2s'
                                        }}
                                    >‹</button>
                                    <button
                                        onClick={() => setPreviewIndex(i => Math.min(previews.length - 1, i + 1))}
                                        disabled={previewIndex === previews.length - 1}
                                        style={{
                                            width: '28px', height: '28px',
                                            border: `1px solid ${COLORS.border}`, borderRadius: '7px',
                                            background: previewIndex === previews.length - 1 ? 'transparent' : COLORS.accentLight,
                                            cursor: previewIndex === previews.length - 1 ? 'not-allowed' : 'pointer',
                                            color: previewIndex === previews.length - 1 ? COLORS.muted : COLORS.accent,
                                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                                            fontSize: '15px', transition: 'all .2s'
                                        }}
                                    >›</button>
                                </div>
                                <div>
                                    <div style={{ fontWeight: '600', fontSize: '14px', color: COLORS.text }}>
                                        {preview ? typeLabels[preview.materialType] : ''}
                                    </div>
                                    <div style={{ fontSize: '11px', color: COLORS.muted }}>
                                        {preview?.isValidation && preview?.validationCategories?.length > 0 ? (
                                            `${preview.validationCategories.map(cat => ({
                                                content: 'Змістовна',
                                                formatting: 'Форматна',
                                                structure: 'Структурна',
                                                references: 'Посилання'
                                            })[cat]).join(', ')} • ${previewIndex + 1}/${previews.length}`
                                        ) : preview?.isValidation ? (
                                            `Всі категорії • ${previewIndex + 1}/${previews.length}`
                                        ) : (
                                            `${previewIndex + 1} / ${previews.length}`
                                        )}
                                    </div>
                                </div>
                            </div>
                            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                {preview && (
                                    <button
                                        onClick={() => {
                                            if (preview.isValidation) {
                                                downloadValidationReport(preview.docId, preview.reportId)
                                            } else {
                                                downloadDocx(preview.docId, preview.materialType)
                                            }
                                        }}
                                        style={{
                                            padding: '6px 14px',
                                            background: COLORS.accent,
                                            color: '#fff', border: 'none', borderRadius: '8px',
                                            fontSize: '12px', cursor: 'pointer', fontWeight: '600',
                                            boxShadow: '0 2px 8px rgba(249,115,22,0.3)'
                                        }}
                                    >Завантажити .docx</button>
                                )}
                                <button
                                    onClick={() => setSidebarOpen(false)}
                                    style={{
                                        width: '28px', height: '28px',
                                        border: `1px solid ${COLORS.border}`, borderRadius: '7px',
                                        background: 'transparent', cursor: 'pointer',
                                        fontSize: '16px', color: COLORS.muted,
                                        display: 'flex', alignItems: 'center', justifyContent: 'center'
                                    }}
                                >×</button>
                            </div>
                        </div>

                        <div style={{ flex: 1, overflowY: 'auto', padding: '20px', minWidth: '420px' }}>
                            {preview && (
                                preview.isValidation ? (
                                    <ValidationReportView
                                        report={preview.content}
                                        colors={COLORS}
                                        validationCategories={preview.validationCategories}
                                        timestamp={preview.timestamp}
                                    />
                                ) : (
                                    <div style={{
                                        background: COLORS.surface,
                                        border: `1px solid ${COLORS.border}`,
                                        borderRadius: '14px', padding: '20px',
                                        fontSize: '13px', lineHeight: '1.8', color: COLORS.text,
                                        whiteSpace: 'pre-wrap', wordBreak: 'break-word', minHeight: '200px',
                                        boxShadow: '0 2px 12px rgba(108,71,255,0.06)'
                                    }}>
                                        {preview.content}
                                    </div>
                                )
                            )}
                        </div>
                    </>
                ) : (
                    <div style={{
                        flex: 1, display: 'flex', flexDirection: 'column',
                        alignItems: 'center', justifyContent: 'center',
                        padding: '24px', textAlign: 'center', minWidth: '420px'
                    }}>
                        <div style={{
                            width: '52px', height: '52px',
                            background: COLORS.accentLight,
                            borderRadius: '14px', display: 'flex', alignItems: 'center',
                            justifyContent: 'center', fontSize: '24px', marginBottom: '14px'
                        }}>
                            <FileText size={28} color={COLORS.accent} />
                        </div>
                        <div style={{ fontSize: '13px', fontWeight: '600', marginBottom: '6px', color: COLORS.text }}>
                            Попередній перегляд
                        </div>
                        <div style={{ fontSize: '12px', color: COLORS.muted, lineHeight: '1.6' }}>
                            Згенеруй матеріал — він з'явиться тут
                        </div>
                    </div>
                )}
            </div>

            {/* Actions Popup */}
            {showActionsPopup && currentDoc && (
                <div style={{
                    position: 'fixed',
                    bottom: '20px',
                    left: '50%',
                    transform: 'translateX(-50%)',
                    background: COLORS.surface,
                    border: `1px solid ${COLORS.border}`,
                    borderRadius: '16px',
                    boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
                    padding: '20px',
                    zIndex: 2000,
                    minWidth: '500px',
                    maxWidth: '90vw',
                    animation: 'slideUp 0.3s ease-out'
                }}>
                    <div style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        marginBottom: '16px'
                    }}>
                        <div>
                            <div style={{ fontSize: '15px', fontWeight: '600', color: COLORS.text, marginBottom: '4px' }}>
                                Що зробити з документом?
                            </div>
                            <div style={{ fontSize: '12px', color: COLORS.muted }}>
                                {currentDoc.filename}
                            </div>
                        </div>
                        <button
                            onClick={() => setShowActionsPopup(false)}
                            style={{
                                width: '28px',
                                height: '28px',
                                border: `1px solid ${COLORS.border}`,
                                borderRadius: '8px',
                                background: 'transparent',
                                cursor: 'pointer',
                                fontSize: '16px',
                                color: COLORS.muted,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center'
                            }}
                        >×</button>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>
                        {[
                            { type: 'summary', label: 'Конспект' },
                            { type: 'quiz', label: 'Тест' },
                            { type: 'flashcards', label: 'Флеш-картки' },
                            { type: 'glossary', label: 'Глосарій' },
                            { type: 'validate', label: 'Валідувати документ' }
                        ].map((action, idx) => (
                            <button
                                key={action.type}
                                onClick={async () => {
                                    // Додаємо повідомлення від користувача
                                    addMessage('user', action.label)

                                    setShowActionsPopup(false)
                                    if (action.type === 'validate') {
                                        if (regulatoryDocs.length === 0) {
                                            showToast('Спочатку завантажте хоча б один нормативний документ!', 'warning')
                                            return
                                        }
                                        setShowValidationDialog(true)
                                    } else {
                                        setLoading(true)
                                        addMessage('assistant', `Генерую ${action.label.toLowerCase()}...`)
                                        try {
                                            const res = await API.post(`/generate/${currentDoc.id}?type=${action.type}`)
                                            const content = res.data.result
                                            setMessages(prev => {
                                                const updated = [...prev]
                                                updated[updated.length - 1] = {
                                                    role: 'assistant',
                                                    content: `${action.label} готовий! Переглянь у правій панелі.`,
                                                    materialType: action.type,
                                                    docId: currentDoc.id
                                                }
                                                return updated
                                            })
                                            setPreviews(prev => {
                                                const updated = [...prev, { content, materialType: action.type, docId: currentDoc.id }]
                                                setPreviewIndex(updated.length - 1)
                                                return updated
                                            })
                                            setSidebarOpen(true)
                                        } catch (err) {
                                            const errorMsg = err.response?.data?.detail || 'Помилка генерації матеріалу'
                                            showToast(errorMsg, 'error')
                                        } finally {
                                            setLoading(false)
                                        }
                                    }
                                }}
                                disabled={action.type === 'validate' && regulatoryDocs.length === 0}
                                style={{
                                    padding: '12px 16px',
                                    background: 'transparent',
                                    borderTop: idx === 0 ? 'none' : `1px solid ${COLORS.border}`,
                                    borderLeft: 'none',
                                    borderRight: 'none',
                                    borderBottom: 'none',
                                    cursor: action.type === 'validate' && regulatoryDocs.length === 0
                                        ? 'not-allowed'
                                        : 'pointer',
                                    fontSize: '14px',
                                    fontWeight: '500',
                                    color: COLORS.text,
                                    textAlign: 'left',
                                    transition: 'background 0.2s',
                                    opacity: action.type === 'validate' && regulatoryDocs.length === 0 ? 0.5 : 1
                                }}
                                onMouseEnter={(e) => {
                                    if (!(action.type === 'validate' && regulatoryDocs.length === 0)) {
                                        e.currentTarget.style.background = COLORS.inputBg
                                    }
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.background = 'transparent'
                                }}
                            >
                                {action.label}
                                {action.type === 'validate' && regulatoryDocs.length === 0 && (
                                    <span style={{ fontSize: '11px', color: COLORS.muted, marginLeft: '8px' }}>
                                        (потрібні нормативи)
                                    </span>
                                )}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* Діалоги */}
            {showRegulatoryDialog && <RegulatoryDialog />}
            {showValidationDialog && <ValidationDialog />}

            <style>{`
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            `}</style>
            </div>
        </div>
    )
}