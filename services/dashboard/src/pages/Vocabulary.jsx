import { useState } from 'react';
import {
    Mic, Upload, Play, Pause, Trash2, Download,
    FolderOpen, Plus, Check, X, Volume2, FileText
} from 'lucide-react';

// Mock vocabulary data
const MOCK_CATEGORIES = [
    { id: 'cat-tech', name: 'Tecnología', wordCount: 20, audioCount: 15 },
    { id: 'cat-brands', name: 'Marcas', wordCount: 15, audioCount: 12 },
    { id: 'cat-names', name: 'Nombres Propios', wordCount: 30, audioCount: 8 },
    { id: 'cat-greetings', name: 'Saludos', wordCount: 10, audioCount: 10 },
    { id: 'cat-phrases', name: 'Frases Comunes', wordCount: 25, audioCount: 18 },
];

const MOCK_WORDS = [
    { id: 'w1', word: 'Facebook', phonetic: 'ˈfeɪsbʊk', category: 'cat-tech', hasAudio: true, duration: 1.2 },
    { id: 'w2', word: 'Instagram', phonetic: 'ˈɪnstəɡræm', category: 'cat-tech', hasAudio: true, duration: 1.4 },
    { id: 'w3', word: 'WhatsApp', phonetic: 'ˈwɒtsæp', category: 'cat-tech', hasAudio: true, duration: 1.1 },
    { id: 'w4', word: 'Twitter', phonetic: 'ˈtwɪtər', category: 'cat-tech', hasAudio: false },
    { id: 'w5', word: 'Netflix', phonetic: 'ˈnetflɪks', category: 'cat-tech', hasAudio: true, duration: 1.3 },
    { id: 'w6', word: 'Google', phonetic: 'ˈɡuːɡəl', category: 'cat-tech', hasAudio: true, duration: 0.9 },
    { id: 'w7', word: 'Microsoft', phonetic: 'ˈmaɪkrəsɒft', category: 'cat-brands', hasAudio: false },
    { id: 'w8', word: 'Amazon', phonetic: 'ˈæməzɒn', category: 'cat-brands', hasAudio: true, duration: 1.1 },
    { id: 'w9', word: 'Buenos días', phonetic: null, category: 'cat-greetings', hasAudio: true, duration: 1.5 },
    { id: 'w10', word: 'Gracias por llamar', phonetic: null, category: 'cat-phrases', hasAudio: true, duration: 2.1 },
];

const TRAINING_GUIDES = [
    { id: 'g1', name: 'Call Center Básico', items: 25, duration: 8, completed: 20 },
    { id: 'g2', name: 'Cobertura Fonética', items: 50, duration: 15, completed: 35 },
    { id: 'g3', name: 'Vocabulario Técnico', items: 30, duration: 10, completed: 10 },
];

function WordCard({ word, onRecord, onPlay }) {
    return (
        <div className="card" style={{ padding: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '0.25rem' }}>
                        {word.word}
                    </div>
                    {word.phonetic && (
                        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                            /{word.phonetic}/
                        </div>
                    )}
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    {word.hasAudio ? (
                        <>
                            <button className="btn-icon" onClick={() => onPlay(word)} title="Reproducir">
                                <Play size={16} />
                            </button>
                            <span className="badge badge-success">
                                <Check size={12} /> {word.duration}s
                            </span>
                        </>
                    ) : (
                        <button className="btn btn-primary btn-sm" onClick={() => onRecord(word)}>
                            <Mic size={14} /> Grabar
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}

function RecordingModal({ word, onClose, onSave }) {
    const [isRecording, setIsRecording] = useState(false);
    const [hasRecording, setHasRecording] = useState(false);

    const toggleRecording = () => {
        if (isRecording) {
            setIsRecording(false);
            setHasRecording(true);
        } else {
            setIsRecording(true);
            setHasRecording(false);
        }
    };

    return (
        <div className="modal-overlay active" onClick={onClose}>
            <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: '400px' }}>
                <h2 style={{ marginBottom: '1.5rem' }}>🎤 Grabar: {word.word}</h2>

                <div style={{
                    textAlign: 'center',
                    padding: '2rem',
                    background: 'var(--bg-secondary)',
                    borderRadius: '12px',
                    marginBottom: '1.5rem'
                }}>
                    <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>{word.word}</div>
                    {word.phonetic && (
                        <div style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
                            /{word.phonetic}/
                        </div>
                    )}

                    <button
                        onClick={toggleRecording}
                        style={{
                            width: '80px',
                            height: '80px',
                            borderRadius: '50%',
                            border: 'none',
                            background: isRecording ? 'var(--accent-red)' : 'var(--gradient-primary)',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            margin: '0 auto',
                            animation: isRecording ? 'pulse 1s infinite' : 'none'
                        }}
                    >
                        {isRecording ? <Pause size={32} color="white" /> : <Mic size={32} color="white" />}
                    </button>

                    <div style={{ marginTop: '1rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                        {isRecording ? 'Grabando... Click para detener' :
                            hasRecording ? '✓ Grabación lista' : 'Click para grabar'}
                    </div>
                </div>

                <div style={{ display: 'flex', gap: '1rem' }}>
                    <button className="btn btn-secondary" style={{ flex: 1 }} onClick={onClose}>
                        Cancelar
                    </button>
                    <button
                        className="btn btn-primary"
                        style={{ flex: 1 }}
                        disabled={!hasRecording}
                        onClick={() => { onSave(word); onClose(); }}
                    >
                        Guardar
                    </button>
                </div>
            </div>
        </div>
    );
}

export default function Vocabulary() {
    const [selectedCategory, setSelectedCategory] = useState(null);
    const [search, setSearch] = useState('');
    const [showRecording, setShowRecording] = useState(null);
    const [activeTab, setActiveTab] = useState('words'); // words, guides, training

    const filteredWords = MOCK_WORDS.filter(w => {
        if (selectedCategory && w.category !== selectedCategory) return false;
        if (search && !w.word.toLowerCase().includes(search.toLowerCase())) return false;
        return true;
    });

    const totalWords = MOCK_WORDS.length;
    const wordsWithAudio = MOCK_WORDS.filter(w => w.hasAudio).length;
    const coverage = Math.round((wordsWithAudio / totalWords) * 100);

    return (
        <div className="fade-in">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                <div>
                    <h1 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '0.5rem' }}>
                        🎤 Vocabulario y Entrenamiento de Voz
                    </h1>
                    <p style={{ color: 'var(--text-secondary)' }}>
                        Gestiona el corpus de audio para fine-tuning del modelo TTS
                    </p>
                </div>
                <div style={{ display: 'flex', gap: '1rem' }}>
                    <button className="btn btn-secondary">
                        <Upload size={18} /> Importar
                    </button>
                    <button className="btn btn-primary">
                        <Plus size={18} /> Nueva Palabra
                    </button>
                </div>
            </div>

            {/* Stats */}
            <div className="grid grid-4" style={{ marginBottom: '2rem' }}>
                <div className="card stat-card">
                    <div className="stat-value">{totalWords}</div>
                    <div className="stat-label">Palabras Totales</div>
                </div>
                <div className="card stat-card" style={{ '--accent': 'var(--accent-green)' }}>
                    <div className="stat-value" style={{ color: 'var(--accent-green)' }}>{wordsWithAudio}</div>
                    <div className="stat-label">Con Audio</div>
                </div>
                <div className="card stat-card" style={{ '--accent': 'var(--accent-yellow)' }}>
                    <div className="stat-value" style={{ color: 'var(--accent-yellow)' }}>{totalWords - wordsWithAudio}</div>
                    <div className="stat-label">Pendientes</div>
                </div>
                <div className="card stat-card" style={{ '--accent': 'var(--accent-purple)' }}>
                    <div className="stat-value" style={{ color: 'var(--accent-purple)' }}>{coverage}%</div>
                    <div className="stat-label">Cobertura</div>
                </div>
            </div>

            {/* Tabs */}
            <div className="tabs" style={{ marginBottom: '1.5rem' }}>
                <button
                    className={`tab ${activeTab === 'words' ? 'active' : ''}`}
                    onClick={() => setActiveTab('words')}
                >
                    📝 Palabras
                </button>
                <button
                    className={`tab ${activeTab === 'guides' ? 'active' : ''}`}
                    onClick={() => setActiveTab('guides')}
                >
                    📋 Guías de Grabación
                </button>
                <button
                    className={`tab ${activeTab === 'training' ? 'active' : ''}`}
                    onClick={() => setActiveTab('training')}
                >
                    🎓 Entrenamiento
                </button>
            </div>

            {activeTab === 'words' && (
                <div style={{ display: 'grid', gridTemplateColumns: '250px 1fr', gap: '1.5rem' }}>
                    {/* Categories Sidebar */}
                    <div className="card">
                        <h3 style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                            Categorías
                        </h3>
                        <div
                            className={`nav-item ${!selectedCategory ? 'active' : ''}`}
                            onClick={() => setSelectedCategory(null)}
                        >
                            <FolderOpen size={18} />
                            <span>Todas</span>
                            <span style={{ marginLeft: 'auto', fontSize: '0.8rem' }}>{MOCK_WORDS.length}</span>
                        </div>
                        {MOCK_CATEGORIES.map(cat => (
                            <div
                                key={cat.id}
                                className={`nav-item ${selectedCategory === cat.id ? 'active' : ''}`}
                                onClick={() => setSelectedCategory(cat.id)}
                            >
                                <FolderOpen size={18} />
                                <span>{cat.name}</span>
                                <span style={{ marginLeft: 'auto', fontSize: '0.8rem' }}>{cat.wordCount}</span>
                            </div>
                        ))}
                    </div>

                    {/* Words Grid */}
                    <div>
                        <div style={{ marginBottom: '1rem' }}>
                            <input
                                type="text"
                                className="input"
                                placeholder="Buscar palabra..."
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                style={{ maxWidth: '300px' }}
                            />
                        </div>
                        <div className="grid grid-3">
                            {filteredWords.map(word => (
                                <WordCard
                                    key={word.id}
                                    word={word}
                                    onRecord={(w) => setShowRecording(w)}
                                    onPlay={(w) => console.log('Play', w)}
                                />
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {activeTab === 'guides' && (
                <div className="grid grid-3">
                    {TRAINING_GUIDES.map(guide => (
                        <div key={guide.id} className="card">
                            <h3 style={{ marginBottom: '0.5rem' }}>{guide.name}</h3>
                            <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '1rem' }}>
                                {guide.items} elementos • ~{guide.duration} min
                            </div>
                            <div style={{ marginBottom: '1rem' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                    <span style={{ fontSize: '0.85rem' }}>Progreso</span>
                                    <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>
                                        {guide.completed}/{guide.items}
                                    </span>
                                </div>
                                <div className="progress-bar">
                                    <div
                                        className="progress-fill"
                                        style={{ width: `${(guide.completed / guide.items) * 100}%` }}
                                    />
                                </div>
                            </div>
                            <button className="btn btn-primary" style={{ width: '100%' }}>
                                <Mic size={16} /> Continuar Grabación
                            </button>
                        </div>
                    ))}
                </div>
            )}

            {activeTab === 'training' && (
                <div className="card">
                    <h3 style={{ marginBottom: '1rem' }}>🎓 Estado del Entrenamiento</h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem' }}>
                        <div style={{ padding: '1.5rem', background: 'var(--bg-secondary)', borderRadius: '12px', textAlign: 'center' }}>
                            <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>📊</div>
                            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--accent-blue)' }}>
                                {(MOCK_WORDS.filter(w => w.hasAudio).reduce((acc, w) => acc + (w.duration || 0), 0) / 60).toFixed(1)} min
                            </div>
                            <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Audio Total</div>
                        </div>
                        <div style={{ padding: '1.5rem', background: 'var(--bg-secondary)', borderRadius: '12px', textAlign: 'center' }}>
                            <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🎯</div>
                            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--accent-green)' }}>92%</div>
                            <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Cobertura Fonética</div>
                        </div>
                        <div style={{ padding: '1.5rem', background: 'var(--bg-secondary)', borderRadius: '12px', textAlign: 'center' }}>
                            <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>✨</div>
                            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--accent-purple)' }}>-23 LUFS</div>
                            <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Normalización</div>
                        </div>
                    </div>

                    <div style={{ marginTop: '2rem' }}>
                        <h4 style={{ marginBottom: '1rem' }}>Configuración de Entrenamiento</h4>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                            <div>
                                <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>
                                    Modelo Base
                                </label>
                                <select className="input select">
                                    <option>jpgallegoar/F5-Spanish</option>
                                </select>
                            </div>
                            <div>
                                <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>
                                    Precisión
                                </label>
                                <select className="input select">
                                    <option>BF16 (Recomendado)</option>
                                    <option>FP16</option>
                                    <option>FP32</option>
                                </select>
                            </div>
                        </div>
                        <button className="btn btn-primary" style={{ marginTop: '1.5rem' }}>
                            🚀 Iniciar Fine-tuning
                        </button>
                    </div>
                </div>
            )}

            {/* Recording Modal */}
            {showRecording && (
                <RecordingModal
                    word={showRecording}
                    onClose={() => setShowRecording(null)}
                    onSave={(w) => console.log('Save', w)}
                />
            )}
        </div>
    );
}
