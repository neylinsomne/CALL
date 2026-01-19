import { useState } from 'react';
import {
    Search, Plus, FileText, Folder, Edit, Trash2,
    Upload, Download, Tag, Clock, Eye
} from 'lucide-react';

// Mock knowledge base data
const MOCK_DOCUMENTS = [
    {
        id: 'doc1',
        title: 'Guía de Productos y Servicios',
        category: 'Productos',
        content: 'Información detallada sobre todos los productos y servicios ofrecidos...',
        tags: ['productos', 'servicios', 'catálogo'],
        updatedAt: '2026-01-18T10:30:00',
        views: 245
    },
    {
        id: 'doc2',
        title: 'Política de Devoluciones',
        category: 'Políticas',
        content: 'El cliente tiene derecho a solicitar devolución dentro de los 30 días...',
        tags: ['devoluciones', 'garantía', 'reembolso'],
        updatedAt: '2026-01-15T14:20:00',
        views: 189
    },
    {
        id: 'doc3',
        title: 'Preguntas Frecuentes - Facturación',
        category: 'FAQ',
        content: 'Respuestas a las preguntas más comunes sobre facturación...',
        tags: ['facturación', 'pagos', 'faq'],
        updatedAt: '2026-01-17T09:45:00',
        views: 412
    },
    {
        id: 'doc4',
        title: 'Procedimiento de Escalamiento',
        category: 'Procedimientos',
        content: 'Pasos para escalar una llamada a supervisor o área especializada...',
        tags: ['escalamiento', 'supervisor', 'procedimiento'],
        updatedAt: '2026-01-10T16:00:00',
        views: 156
    },
    {
        id: 'doc5',
        title: 'Script de Ventas - Plan Premium',
        category: 'Scripts',
        content: 'Buenos días, le comento sobre nuestro plan premium que incluye...',
        tags: ['ventas', 'script', 'premium'],
        updatedAt: '2026-01-19T08:00:00',
        views: 89
    },
];

const CATEGORIES = [
    { name: 'Todos', count: MOCK_DOCUMENTS.length },
    { name: 'Productos', count: 1 },
    { name: 'Políticas', count: 1 },
    { name: 'FAQ', count: 1 },
    { name: 'Procedimientos', count: 1 },
    { name: 'Scripts', count: 1 },
];

function DocumentCard({ doc, onClick }) {
    return (
        <div className="card" style={{ cursor: 'pointer' }} onClick={() => onClick(doc)}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
                    <div style={{
                        width: '48px',
                        height: '48px',
                        borderRadius: '12px',
                        background: 'linear-gradient(135deg, var(--accent-blue), var(--accent-purple))',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                    }}>
                        <FileText size={24} color="white" />
                    </div>
                    <div>
                        <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.25rem' }}>
                            {doc.title}
                        </h3>
                        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '0.5rem' }}>
                            <span className="badge badge-info">{doc.category}</span>
                            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                                <Eye size={12} style={{ marginRight: '0.25rem' }} />
                                {doc.views}
                            </span>
                        </div>
                        <p style={{
                            fontSize: '0.85rem',
                            color: 'var(--text-secondary)',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                            maxWidth: '400px'
                        }}>
                            {doc.content}
                        </p>
                    </div>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button className="btn-icon" onClick={(e) => { e.stopPropagation(); }}>
                        <Edit size={16} />
                    </button>
                    <button className="btn-icon" onClick={(e) => { e.stopPropagation(); }}>
                        <Trash2 size={16} />
                    </button>
                </div>
            </div>

            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem', flexWrap: 'wrap' }}>
                {doc.tags.map(tag => (
                    <span key={tag} style={{
                        padding: '0.2rem 0.5rem',
                        background: 'var(--bg-secondary)',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        color: 'var(--text-muted)'
                    }}>
                        #{tag}
                    </span>
                ))}
            </div>
        </div>
    );
}

function DocumentViewer({ doc, onClose }) {
    return (
        <div className="modal-overlay active" onClick={onClose}>
            <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: '700px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
                    <div>
                        <h2 style={{ marginBottom: '0.5rem' }}>{doc.title}</h2>
                        <div style={{ display: 'flex', gap: '1rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                            <span><Tag size={14} /> {doc.category}</span>
                            <span><Clock size={14} /> {new Date(doc.updatedAt).toLocaleDateString()}</span>
                            <span><Eye size={14} /> {doc.views} vistas</span>
                        </div>
                    </div>
                    <button className="btn-icon" onClick={onClose}>✕</button>
                </div>

                <div style={{
                    padding: '1.5rem',
                    background: 'var(--bg-secondary)',
                    borderRadius: '12px',
                    marginBottom: '1.5rem',
                    maxHeight: '400px',
                    overflowY: 'auto'
                }}>
                    <p style={{ lineHeight: 1.8 }}>{doc.content}</p>
                </div>

                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
                    {doc.tags.map(tag => (
                        <span key={tag} className="badge badge-neutral">#{tag}</span>
                    ))}
                </div>

                <div style={{ display: 'flex', gap: '1rem' }}>
                    <button className="btn btn-secondary" style={{ flex: 1 }}>
                        <Edit size={16} /> Editar
                    </button>
                    <button className="btn btn-primary" style={{ flex: 1 }}>
                        <Download size={16} /> Exportar
                    </button>
                </div>
            </div>
        </div>
    );
}

export default function KnowledgeBase() {
    const [search, setSearch] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('Todos');
    const [selectedDoc, setSelectedDoc] = useState(null);

    const filteredDocs = MOCK_DOCUMENTS.filter(doc => {
        if (selectedCategory !== 'Todos' && doc.category !== selectedCategory) return false;
        if (search && !doc.title.toLowerCase().includes(search.toLowerCase()) &&
            !doc.content.toLowerCase().includes(search.toLowerCase())) return false;
        return true;
    });

    return (
        <div className="fade-in">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                <div>
                    <h1 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '0.5rem' }}>
                        📚 Base de Conocimiento
                    </h1>
                    <p style={{ color: 'var(--text-secondary)' }}>
                        Documentación y scripts para el agente AI
                    </p>
                </div>
                <div style={{ display: 'flex', gap: '1rem' }}>
                    <button className="btn btn-secondary">
                        <Upload size={18} /> Importar
                    </button>
                    <button className="btn btn-primary">
                        <Plus size={18} /> Nuevo Documento
                    </button>
                </div>
            </div>

            {/* Stats */}
            <div className="grid grid-4" style={{ marginBottom: '2rem' }}>
                <div className="card stat-card">
                    <div className="stat-value">{MOCK_DOCUMENTS.length}</div>
                    <div className="stat-label">Documentos</div>
                </div>
                <div className="card stat-card">
                    <div className="stat-value">{CATEGORIES.length - 1}</div>
                    <div className="stat-label">Categorías</div>
                </div>
                <div className="card stat-card">
                    <div className="stat-value">{MOCK_DOCUMENTS.reduce((acc, d) => acc + d.views, 0)}</div>
                    <div className="stat-label">Consultas Totales</div>
                </div>
                <div className="card stat-card">
                    <div className="stat-value">98%</div>
                    <div className="stat-label">Tasa de Respuesta</div>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '250px 1fr', gap: '1.5rem' }}>
                {/* Categories */}
                <div className="card">
                    <h3 style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                        Categorías
                    </h3>
                    {CATEGORIES.map(cat => (
                        <div
                            key={cat.name}
                            className={`nav-item ${selectedCategory === cat.name ? 'active' : ''}`}
                            onClick={() => setSelectedCategory(cat.name)}
                        >
                            <Folder size={18} />
                            <span>{cat.name}</span>
                            <span style={{ marginLeft: 'auto', fontSize: '0.8rem' }}>{cat.count}</span>
                        </div>
                    ))}
                </div>

                {/* Documents */}
                <div>
                    <div style={{ marginBottom: '1rem', position: 'relative' }}>
                        <Search size={18} style={{
                            position: 'absolute',
                            left: '12px',
                            top: '50%',
                            transform: 'translateY(-50%)',
                            color: 'var(--text-muted)'
                        }} />
                        <input
                            type="text"
                            className="input"
                            placeholder="Buscar documentos..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            style={{ paddingLeft: '40px', width: '100%' }}
                        />
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        {filteredDocs.map(doc => (
                            <DocumentCard key={doc.id} doc={doc} onClick={setSelectedDoc} />
                        ))}
                    </div>
                </div>
            </div>

            {selectedDoc && (
                <DocumentViewer doc={selectedDoc} onClose={() => setSelectedDoc(null)} />
            )}
        </div>
    );
}
