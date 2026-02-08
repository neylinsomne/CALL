import { useState } from 'react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
    ResponsiveContainer, Legend
} from 'recharts';
import {
    Mic, Play, Pause, Plus, Check, X, Upload, Download,
    FolderOpen, Tag, Activity, Zap, Shield, ChevronRight,
    Clock, BarChart3, Volume2, Search, Loader
} from 'lucide-react';
import {
    VOICE_STYLES, CORPUS_SECTIONS, CORPUS_LISTS, CORPUS_SENTENCES,
    CUSTOM_TERMS, TERM_CATEGORIES, PIPELINE_STATUS
} from '../data/voiceLabData';


// ===========================================
// Sub-Components
// ===========================================

function SentenceCard({ sentence, onRecord, onPlay, onLabelChange }) {
    const currentStyle = VOICE_STYLES.find(s => s.id === sentence.styleLabel);

    return (
        <div className="card" style={{ padding: '1rem' }}>
            <div style={{ marginBottom: '0.75rem', lineHeight: 1.6, fontSize: '0.95rem' }}>
                {sentence.text}
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    <select
                        className="input select"
                        value={sentence.styleLabel || ''}
                        onChange={(e) => onLabelChange(sentence.id, e.target.value)}
                        style={{
                            width: '140px',
                            padding: '0.3rem 0.6rem',
                            fontSize: '0.8rem',
                            borderColor: currentStyle?.color || 'var(--border)',
                        }}
                    >
                        <option value="">Sin etiqueta</option>
                        {VOICE_STYLES.map(s => (
                            <option key={s.id} value={s.id}>{s.name}</option>
                        ))}
                    </select>
                    {currentStyle && (
                        <div style={{
                            width: '10px', height: '10px', borderRadius: '50%',
                            background: currentStyle.color, flexShrink: 0,
                        }} />
                    )}
                </div>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    {sentence.quality != null && (
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                            {Math.round(sentence.quality * 100)}%
                        </span>
                    )}
                    {sentence.hasRecording ? (
                        <>
                            <button className="btn-icon" onClick={() => onPlay(sentence)} title="Reproducir">
                                <Play size={16} />
                            </button>
                            <span className="badge badge-success">
                                <Check size={12} /> {sentence.recordingDuration}s
                            </span>
                        </>
                    ) : (
                        <button className="btn btn-primary btn-sm" onClick={() => onRecord(sentence)}>
                            <Mic size={14} /> Grabar
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}


function TermCard({ term, onRecord, onPlay }) {
    return (
        <div className="card" style={{ padding: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '0.25rem' }}>
                        {term.term}
                    </div>
                    {term.phonetic && (
                        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                            /{term.phonetic}/
                        </div>
                    )}
                    {term.context && (
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                            {term.context}
                        </div>
                    )}
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    {term.hasAudio ? (
                        <>
                            <button className="btn-icon" onClick={() => onPlay(term)} title="Reproducir">
                                <Play size={16} />
                            </button>
                            <span className="badge badge-success">
                                <Check size={12} /> {term.audioDuration}s
                            </span>
                        </>
                    ) : (
                        <button className="btn btn-primary btn-sm" onClick={() => onRecord(term)}>
                            <Mic size={14} /> Grabar
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}


function RecordingModal({ item, onClose, onSave }) {
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

    const displayText = item.text || item.term || '';
    const displayStyle = VOICE_STYLES.find(s => s.id === item.styleLabel);

    return (
        <div className="modal-overlay active" onClick={onClose}>
            <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: '500px' }}>
                <h2 style={{ marginBottom: '1.5rem' }}>Grabar Audio</h2>

                <div style={{
                    textAlign: 'center', padding: '2rem',
                    background: 'var(--bg-secondary)', borderRadius: '12px',
                    marginBottom: '1.5rem',
                }}>
                    <div style={{ fontSize: '1.2rem', lineHeight: 1.6, marginBottom: '1rem' }}>
                        {displayText}
                    </div>
                    {displayStyle && (
                        <div style={{ marginBottom: '1.5rem' }}>
                            <span className="badge" style={{
                                background: displayStyle.color + '22',
                                color: displayStyle.color,
                                border: `1px solid ${displayStyle.color}44`,
                            }}>
                                {displayStyle.name}
                            </span>
                        </div>
                    )}

                    <button
                        onClick={toggleRecording}
                        style={{
                            width: '80px', height: '80px', borderRadius: '50%',
                            border: 'none',
                            background: isRecording ? 'var(--accent-red)' : 'var(--gradient-primary)',
                            cursor: 'pointer',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            margin: '0 auto',
                            animation: isRecording ? 'pulse 1s infinite' : 'none',
                        }}
                    >
                        {isRecording ? <Pause size={32} color="white" /> : <Mic size={32} color="white" />}
                    </button>

                    <div style={{ marginTop: '1rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                        {isRecording ? 'Grabando... Click para detener' :
                            hasRecording ? 'Grabacion lista' : 'Click para grabar'}
                    </div>
                </div>

                <div style={{ display: 'flex', gap: '1rem' }}>
                    <button className="btn btn-secondary" style={{ flex: 1 }} onClick={onClose}>
                        Cancelar
                    </button>
                    <button
                        className="btn btn-primary" style={{ flex: 1 }}
                        disabled={!hasRecording}
                        onClick={() => { onSave(item); onClose(); }}
                    >
                        Guardar
                    </button>
                </div>
            </div>
        </div>
    );
}


function AddTermModal({ onClose, onSave }) {
    const [form, setForm] = useState({ term: '', phonetic: '', category: 'technical', context: '' });

    return (
        <div className="modal-overlay active" onClick={onClose}>
            <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: '450px' }}>
                <h2 style={{ marginBottom: '1.5rem' }}>Nuevo Termino</h2>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    <div>
                        <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                            Termino
                        </label>
                        <input
                            className="input"
                            value={form.term}
                            onChange={e => setForm({ ...form, term: e.target.value })}
                            placeholder="Ej: Bancolombia"
                        />
                    </div>
                    <div>
                        <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                            Fonetica (IPA)
                        </label>
                        <input
                            className="input"
                            value={form.phonetic}
                            onChange={e => setForm({ ...form, phonetic: e.target.value })}
                            placeholder="Ej: ban.ko.lom.bja"
                        />
                    </div>
                    <div>
                        <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                            Categoria
                        </label>
                        <select
                            className="input select"
                            value={form.category}
                            onChange={e => setForm({ ...form, category: e.target.value })}
                        >
                            {TERM_CATEGORIES.map(c => (
                                <option key={c.id} value={c.id}>{c.name}</option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                            Contexto de uso
                        </label>
                        <input
                            className="input"
                            value={form.context}
                            onChange={e => setForm({ ...form, context: e.target.value })}
                            placeholder="Ej: Nombre del banco del cliente"
                        />
                    </div>
                </div>

                <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
                    <button className="btn btn-secondary" style={{ flex: 1 }} onClick={onClose}>
                        Cancelar
                    </button>
                    <button
                        className="btn btn-primary" style={{ flex: 1 }}
                        disabled={!form.term.trim()}
                        onClick={() => {
                            onSave({
                                id: `ct-${Date.now()}`,
                                ...form,
                                hasAudio: false,
                                audioDuration: null,
                            });
                            onClose();
                        }}
                    >
                        Guardar
                    </button>
                </div>
            </div>
        </div>
    );
}


function PipelineStageIndicator({ stages }) {
    const stageIcons = { reference: Volume2, evolve: Activity, validate: Shield, deploy: Zap };

    return (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0', marginBottom: '2rem' }}>
            {stages.map((stage, i) => {
                const Icon = stageIcons[stage.id] || Activity;
                const isCompleted = stage.status === 'completed';
                const isRunning = stage.status === 'running';
                const isPending = stage.status === 'pending';

                const circleColor = isCompleted ? 'var(--accent-green)' : isRunning ? 'var(--accent-blue)' : 'rgba(255,255,255,0.15)';
                const lineColor = isCompleted ? 'var(--accent-green)' : 'rgba(255,255,255,0.1)';

                return (
                    <div key={stage.id} style={{ display: 'flex', alignItems: 'center' }}>
                        <div style={{ textAlign: 'center' }}>
                            <div style={{
                                width: '50px', height: '50px', borderRadius: '50%',
                                background: circleColor, display: 'flex',
                                alignItems: 'center', justifyContent: 'center',
                                animation: isRunning ? 'pulse 2s infinite' : 'none',
                                border: isPending ? '2px dashed rgba(255,255,255,0.2)' : 'none',
                            }}>
                                {isCompleted ? <Check size={24} color="white" /> :
                                    isRunning ? <Loader size={24} color="white" /> :
                                        <Icon size={24} color="rgba(255,255,255,0.4)" />}
                            </div>
                            <div style={{ fontSize: '0.75rem', marginTop: '0.5rem', color: isPending ? 'var(--text-muted)' : 'var(--text-primary)', maxWidth: '90px' }}>
                                {stage.name}
                            </div>
                            {isRunning && stage.progress != null && (
                                <div style={{ fontSize: '0.7rem', color: 'var(--accent-blue)', marginTop: '0.25rem' }}>
                                    {stage.progress}%
                                </div>
                            )}
                            {isCompleted && stage.elapsedSeconds != null && (
                                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                                    {Math.round(stage.elapsedSeconds / 60)}min
                                </div>
                            )}
                        </div>
                        {i < stages.length - 1 && (
                            <div style={{
                                width: '60px', height: '3px',
                                background: lineColor, margin: '0 0.25rem',
                                marginBottom: '2rem',
                                borderStyle: isPending ? 'dashed' : 'solid',
                            }} />
                        )}
                    </div>
                );
            })}
        </div>
    );
}


// ===========================================
// Main Page
// ===========================================

export default function VoiceLab() {
    const [activeTab, setActiveTab] = useState('corpus');
    const [selectedList, setSelectedList] = useState(null);
    const [selectedTermCategory, setSelectedTermCategory] = useState(null);
    const [search, setSearch] = useState('');
    const [styleFilter, setStyleFilter] = useState(null);
    const [showRecording, setShowRecording] = useState(null);
    const [showAddTerm, setShowAddTerm] = useState(false);
    const [sentences, setSentences] = useState(CORPUS_SENTENCES);
    const [terms, setTerms] = useState(CUSTOM_TERMS);

    // Data labeling handler
    const handleLabelChange = (sentenceId, style) => {
        setSentences(prev => prev.map(s =>
            s.id === sentenceId ? { ...s, styleLabel: style || null } : s
        ));
    };

    // Computed stats
    const totalSentences = sentences.length;
    const recordedSentences = sentences.filter(s => s.hasRecording).length;
    const labeledSentences = sentences.filter(s => s.styleLabel).length;

    // Filtered sentences
    const filteredSentences = sentences.filter(s => {
        if (selectedList && s.listId !== selectedList) return false;
        if (styleFilter && s.styleLabel !== styleFilter) return false;
        if (search && !s.text.toLowerCase().includes(search.toLowerCase())) return false;
        return true;
    });

    // Filtered terms
    const filteredTerms = terms.filter(t => {
        if (selectedTermCategory && t.category !== selectedTermCategory) return false;
        if (search && !t.term.toLowerCase().includes(search.toLowerCase())) return false;
        return true;
    });

    // Style label counts
    const styleCounts = VOICE_STYLES.map(style => ({
        ...style,
        count: sentences.filter(s => s.styleLabel === style.id).length,
    }));

    // List sentence counts
    const getListCounts = (listId) => {
        const listSentences = sentences.filter(s => s.listId === listId);
        const recorded = listSentences.filter(s => s.hasRecording).length;
        return { total: listSentences.length, recorded };
    };

    return (
        <div className="fade-in">
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                <div>
                    <h1 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '0.5rem' }}>
                        Voice Lab - Destilacion de Voz
                    </h1>
                    <p style={{ color: 'var(--text-secondary)' }}>
                        Corpus, etiquetado de estilos y pipeline de destilacion F5-TTS a Kokoro
                    </p>
                </div>
                <div style={{ display: 'flex', gap: '1rem' }}>
                    <button className="btn btn-secondary">
                        <Download size={18} /> Exportar
                    </button>
                    <button className="btn btn-primary">
                        <Upload size={18} /> Importar Audio
                    </button>
                </div>
            </div>

            {/* Stats */}
            <div className="grid grid-4" style={{ marginBottom: '2rem' }}>
                <div className="card stat-card">
                    <div className="stat-value">{totalSentences}</div>
                    <div className="stat-label">Oraciones Totales</div>
                </div>
                <div className="card stat-card" style={{ '--accent': 'var(--accent-green)' }}>
                    <div className="stat-value" style={{ color: 'var(--accent-green)' }}>{recordedSentences}</div>
                    <div className="stat-label">Grabadas</div>
                </div>
                <div className="card stat-card" style={{ '--accent': 'var(--accent-purple)' }}>
                    <div className="stat-value" style={{ color: 'var(--accent-purple)' }}>{labeledSentences}</div>
                    <div className="stat-label">Etiquetadas</div>
                </div>
                <div className="card stat-card" style={{ '--accent': 'var(--accent-blue)' }}>
                    <div className="stat-value" style={{ color: 'var(--accent-blue)' }}>
                        {PIPELINE_STATUS.currentRun.status === 'running' ? 'Activo' : 'Inactivo'}
                    </div>
                    <div className="stat-label">Pipeline</div>
                </div>
            </div>

            {/* Tabs */}
            <div className="tabs" style={{ marginBottom: '1.5rem' }}>
                <button className={`tab ${activeTab === 'corpus' ? 'active' : ''}`} onClick={() => setActiveTab('corpus')}>
                    Corpus Sharvard
                </button>
                <button className={`tab ${activeTab === 'custom-terms' ? 'active' : ''}`} onClick={() => setActiveTab('custom-terms')}>
                    Terminos Custom
                </button>
                <button className={`tab ${activeTab === 'pipeline' ? 'active' : ''}`} onClick={() => setActiveTab('pipeline')}>
                    Pipeline
                </button>
            </div>

            {/* ================================ */}
            {/* TAB: CORPUS                      */}
            {/* ================================ */}
            {activeTab === 'corpus' && (
                <div style={{ display: 'grid', gridTemplateColumns: '250px 1fr', gap: '1.5rem' }}>
                    {/* Sidebar - Corpus Lists */}
                    <div className="card" style={{ alignSelf: 'start' }}>
                        <div
                            className={`nav-item ${!selectedList ? 'active' : ''}`}
                            onClick={() => setSelectedList(null)}
                        >
                            <FolderOpen size={18} />
                            <span>Todas</span>
                            <span style={{ marginLeft: 'auto', fontSize: '0.8rem' }}>{totalSentences}</span>
                        </div>

                        {CORPUS_SECTIONS.map(section => (
                            <div key={section.title}>
                                <div style={{
                                    fontSize: '0.7rem', color: 'var(--text-muted)',
                                    textTransform: 'uppercase', letterSpacing: '0.05em',
                                    padding: '0.75rem 0.5rem 0.25rem', fontWeight: 600,
                                }}>
                                    {section.title}
                                </div>
                                {section.lists.map(listId => {
                                    const list = CORPUS_LISTS.find(l => l.id === listId);
                                    if (!list) return null;
                                    const counts = getListCounts(listId);
                                    return (
                                        <div
                                            key={listId}
                                            className={`nav-item ${selectedList === listId ? 'active' : ''}`}
                                            onClick={() => setSelectedList(listId)}
                                        >
                                            <FolderOpen size={16} />
                                            <span style={{ fontSize: '0.85rem' }}>{list.name}</span>
                                            <span style={{ marginLeft: 'auto', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                                {counts.recorded}/{counts.total}
                                            </span>
                                        </div>
                                    );
                                })}
                            </div>
                        ))}
                    </div>

                    {/* Main Content - Sentences */}
                    <div>
                        {/* Filters */}
                        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
                            <input
                                type="text" className="input"
                                placeholder="Buscar oracion..."
                                value={search} onChange={e => setSearch(e.target.value)}
                                style={{ maxWidth: '280px' }}
                            />
                            <div style={{ display: 'flex', gap: '0.5rem' }}>
                                <button
                                    className={`btn btn-sm ${!styleFilter ? 'btn-primary' : 'btn-secondary'}`}
                                    onClick={() => setStyleFilter(null)}
                                >
                                    Todas
                                </button>
                                {styleCounts.map(style => (
                                    <button
                                        key={style.id}
                                        className={`btn btn-sm ${styleFilter === style.id ? 'btn-primary' : 'btn-secondary'}`}
                                        onClick={() => setStyleFilter(styleFilter === style.id ? null : style.id)}
                                        style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}
                                    >
                                        <div style={{
                                            width: '8px', height: '8px', borderRadius: '50%',
                                            background: style.color,
                                        }} />
                                        {style.name} ({style.count})
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Sentence Grid */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                            {filteredSentences.map(sentence => (
                                <SentenceCard
                                    key={sentence.id}
                                    sentence={sentence}
                                    onRecord={s => setShowRecording(s)}
                                    onPlay={s => console.log('Play', s.id)}
                                    onLabelChange={handleLabelChange}
                                />
                            ))}
                            {filteredSentences.length === 0 && (
                                <div className="card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                                    No se encontraron oraciones con los filtros aplicados
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* ================================ */}
            {/* TAB: CUSTOM TERMS                */}
            {/* ================================ */}
            {activeTab === 'custom-terms' && (
                <div style={{ display: 'grid', gridTemplateColumns: '250px 1fr', gap: '1.5rem' }}>
                    {/* Sidebar - Term Categories */}
                    <div className="card" style={{ alignSelf: 'start' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                            <h3 style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>Categorias</h3>
                        </div>
                        <div
                            className={`nav-item ${!selectedTermCategory ? 'active' : ''}`}
                            onClick={() => setSelectedTermCategory(null)}
                        >
                            <FolderOpen size={18} />
                            <span>Todas</span>
                            <span style={{ marginLeft: 'auto', fontSize: '0.8rem' }}>{terms.length}</span>
                        </div>
                        {TERM_CATEGORIES.map(cat => (
                            <div
                                key={cat.id}
                                className={`nav-item ${selectedTermCategory === cat.id ? 'active' : ''}`}
                                onClick={() => setSelectedTermCategory(cat.id)}
                            >
                                <FolderOpen size={18} />
                                <span>{cat.name}</span>
                                <span style={{ marginLeft: 'auto', fontSize: '0.8rem' }}>
                                    {terms.filter(t => t.category === cat.id).length}
                                </span>
                            </div>
                        ))}
                    </div>

                    {/* Main Content - Terms */}
                    <div>
                        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', alignItems: 'center' }}>
                            <input
                                type="text" className="input"
                                placeholder="Buscar termino..."
                                value={search} onChange={e => setSearch(e.target.value)}
                                style={{ maxWidth: '280px' }}
                            />
                            <button className="btn btn-primary" onClick={() => setShowAddTerm(true)}>
                                <Plus size={16} /> Nuevo Termino
                            </button>
                        </div>
                        <div className="grid grid-3">
                            {filteredTerms.map(term => (
                                <TermCard
                                    key={term.id}
                                    term={term}
                                    onRecord={t => setShowRecording(t)}
                                    onPlay={t => console.log('Play term', t.id)}
                                />
                            ))}
                        </div>
                        {filteredTerms.length === 0 && (
                            <div className="card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                                No se encontraron terminos
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* ================================ */}
            {/* TAB: PIPELINE                    */}
            {/* ================================ */}
            {activeTab === 'pipeline' && (
                <div>
                    {/* Pipeline Stage Indicator */}
                    <div className="card" style={{ marginBottom: '1.5rem', padding: '2rem' }}>
                        <h3 style={{ marginBottom: '1.5rem', textAlign: 'center' }}>
                            Estado del Pipeline
                            {PIPELINE_STATUS.currentRun.status === 'running' && (
                                <span className="badge badge-info" style={{ marginLeft: '0.75rem' }}>
                                    <Loader size={12} /> {PIPELINE_STATUS.currentRun.id}
                                </span>
                            )}
                        </h3>
                        <PipelineStageIndicator stages={PIPELINE_STATUS.stages} />
                    </div>

                    {/* Style Scores */}
                    <h3 style={{ marginBottom: '1rem' }}>Scores por Estilo</h3>
                    <div className="grid grid-4" style={{ marginBottom: '1.5rem' }}>
                        {PIPELINE_STATUS.styleScores.map(score => {
                            const style = VOICE_STYLES.find(s => s.id === score.style);
                            return (
                                <div key={score.style} className="card" style={{ padding: '1.25rem' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                            <div style={{
                                                width: '12px', height: '12px', borderRadius: '50%',
                                                background: style?.color || '#666',
                                            }} />
                                            <span style={{ fontWeight: 600 }}>{style?.name || score.style}</span>
                                        </div>
                                        <span className={`badge ${score.valid ? 'badge-success' : 'badge-danger'}`}>
                                            {score.valid ? 'Valido' : 'Pendiente'}
                                        </span>
                                    </div>
                                    <div style={{ fontSize: '2rem', fontWeight: 700, color: style?.color || '#666', marginBottom: '1rem' }}>
                                        {score.overall > 0 ? score.overall.toFixed(1) : '--'}
                                    </div>

                                    {/* Sub-scores */}
                                    {[
                                        { label: 'Target Sim', value: score.targetSimilarity, threshold: 0.70 },
                                        { label: 'Self Sim', value: score.selfSimilarity, threshold: 0.85 },
                                        { label: 'Features', value: score.featureSimilarity, threshold: 0 },
                                    ].map(metric => (
                                        <div key={metric.label} style={{ marginBottom: '0.5rem' }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '0.25rem' }}>
                                                <span style={{ color: 'var(--text-muted)' }}>{metric.label}</span>
                                                <span>{metric.value > 0 ? (metric.value * 100).toFixed(0) + '%' : '--'}</span>
                                            </div>
                                            <div className="progress-bar" style={{ height: '4px' }}>
                                                <div
                                                    className="progress-fill"
                                                    style={{
                                                        width: `${metric.value * 100}%`,
                                                        background: metric.value >= metric.threshold ? 'var(--accent-green)' : 'var(--accent-yellow)',
                                                    }}
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            );
                        })}
                    </div>

                    {/* Evolution Chart + Config */}
                    <div className="grid grid-2" style={{ marginBottom: '1.5rem' }}>
                        <div className="card" style={{ padding: '1.5rem' }}>
                            <h3 style={{ marginBottom: '1rem' }}>Evolucion de Score</h3>
                            <ResponsiveContainer width="100%" height={300}>
                                <LineChart data={PIPELINE_STATUS.evolutionHistory}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                    <XAxis dataKey="step" stroke="rgba(255,255,255,0.3)" fontSize={12} />
                                    <YAxis domain={[50, 100]} stroke="rgba(255,255,255,0.3)" fontSize={12} />
                                    <Tooltip contentStyle={{ background: '#1a1a24', border: '1px solid rgba(255,255,255,0.1)' }} />
                                    <Legend />
                                    {VOICE_STYLES.map(style => (
                                        <Line
                                            key={style.id}
                                            type="monotone"
                                            dataKey={style.id}
                                            stroke={style.color}
                                            name={style.name}
                                            strokeWidth={2}
                                            dot={false}
                                        />
                                    ))}
                                </LineChart>
                            </ResponsiveContainer>
                        </div>

                        <div className="card" style={{ padding: '1.5rem' }}>
                            <h3 style={{ marginBottom: '1rem' }}>Configuracion</h3>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                                {[
                                    { label: 'Walk Steps', value: '10,000' },
                                    { label: 'Diversidad', value: '0.01 - 0.15' },
                                    { label: 'Poblacion', value: '10 candidatos' },
                                    { label: 'Early Termination', value: '98% del mejor' },
                                    { label: 'Target Sim (peso)', value: '48%' },
                                    { label: 'Self Sim (peso)', value: '50%' },
                                    { label: 'Feature Sim (peso)', value: '2%' },
                                    { label: 'Umbral Speaker', value: '>= 0.70' },
                                    { label: 'Umbral Self-Sim', value: '>= 0.85' },
                                ].map(item => (
                                    <div key={item.label} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                        <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{item.label}</span>
                                        <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>{item.value}</span>
                                    </div>
                                ))}
                            </div>

                            <button className="btn btn-primary" style={{ width: '100%', marginTop: '1.5rem' }}>
                                <Zap size={16} /> Iniciar Pipeline
                            </button>
                        </div>
                    </div>

                    {/* Run History */}
                    <div className="card" style={{ padding: '1.5rem' }}>
                        <h3 style={{ marginBottom: '1rem' }}>Historial de Ejecuciones</h3>
                        <table className="table">
                            <thead>
                                <tr>
                                    <th>Run ID</th>
                                    <th>Fecha</th>
                                    <th>Estado</th>
                                    <th>Estilos</th>
                                    <th>Mejor Score</th>
                                </tr>
                            </thead>
                            <tbody>
                                {PIPELINE_STATUS.recentRuns.map(run => (
                                    <tr key={run.id}>
                                        <td style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>{run.id}</td>
                                        <td>{run.date}</td>
                                        <td>
                                            <span className={`badge ${run.status === 'completed' ? 'badge-success' : run.status === 'running' ? 'badge-info' : 'badge-danger'}`}>
                                                {run.status === 'completed' ? 'Completado' : run.status === 'running' ? 'En curso' : 'Fallido'}
                                            </span>
                                        </td>
                                        <td>{run.styles}</td>
                                        <td style={{ fontWeight: 600 }}>{run.bestScore}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Modals */}
            {showRecording && (
                <RecordingModal
                    item={showRecording}
                    onClose={() => setShowRecording(null)}
                    onSave={item => console.log('Saved recording for', item.id)}
                />
            )}
            {showAddTerm && (
                <AddTermModal
                    onClose={() => setShowAddTerm(false)}
                    onSave={newTerm => setTerms(prev => [...prev, newTerm])}
                />
            )}
        </div>
    );
}
