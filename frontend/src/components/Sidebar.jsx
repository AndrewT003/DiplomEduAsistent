export default function Sidebar({ documents, onSelect, selected }) {
    return (
        <aside style={{
            width: '260px',
            borderRight: '1px solid #eee',
            padding: '1.5rem 1rem',
            background: '#fafafa'
        }}>
            <h3 style={{ marginBottom: '1rem' }}>Документи</h3>
            {documents.length === 0 && (
                <p style={{ color: '#aaa', fontSize: '13px' }}>
                    Ще немає документів
                </p>
            )}
            {documents.map(doc => (
                <div
                    key={doc.id}
                    onClick={() => onSelect(doc)}
                    style={{
                        padding: '10px 12px',
                        borderRadius: '8px',
                        cursor: 'pointer',
                        marginBottom: '6px',
                        background: selected?.id === doc.id ? '#e8f0fe' : 'transparent',
                        fontWeight: selected?.id === doc.id ? '500' : '400',
                        fontSize: '13px'
                    }}
                >
                    {doc.filename}
                </div>
            ))}
        </aside>
    )
}