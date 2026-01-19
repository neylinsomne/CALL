import { useParams, useNavigate } from 'react-router-dom';
import {
    ArrowLeft, Phone, Clock, User, Tag, ThumbsUp,
    Play, Pause, Download, BarChart2, MessageSquare
} from 'lucide-react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    AreaChart, Area
} from 'recharts';
import { MOCK_CALLS, EMOTIONS, formatDuration, formatDate, getAgentById } from '../data/mockData';

export default function CallDetail() {
    const { id } = useParams();
    const navigate = useNavigate();
    const call = MOCK_CALLS.find(c => c.id === id);

    if (!call) {
        return <div>Llamada no encontrada</div>;
    }

    const agent = getAgentById(call.agentId);
    const emotionColors = {
        happy: '#10b981',
        neutral: '#6b7280',
        frustrated: '#f59e0b',
        angry: '#ef4444',
        sad: '#8b5cf6',
        satisfied: '#06b6d4'
    };

    // Transform emotion timeline for chart
    const emotionData = call.emotions.timeline.map(point => ({
        time: formatDuration(point.time),
        value: point.emotion === 'happy' || point.emotion === 'satisfied' ? 1 :
            point.emotion === 'neutral' ? 0 :
                point.emotion === 'frustrated' ? -0.5 : -1,
        emotion: point.emotion,
        confidence: point.confidence
    }));

    return (
        <div className="fade-in">
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '2rem' }}>
                <button className="btn-icon" onClick={() => navigate('/calls')}>
                    <ArrowLeft size={20} />
                </button>
                <div style={{ flex: 1 }}>
                    <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>{call.caller.name}</h1>
                    <p style={{ color: 'var(--text-secondary)' }}>{call.caller.phone} • {formatDate(call.startTime)}</p>
                </div>
                <button className="btn btn-secondary">
                    <Download size={18} />
                    Exportar
                </button>
                <button className="btn btn-primary">
                    <Play size={18} />
                    Reproducir
                </button>
            </div>

            {/* Info Cards */}
            <div className="grid grid-4" style={{ marginBottom: '2rem' }}>
                <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{
                        width: '48px', height: '48px', borderRadius: '12px',
                        background: 'rgba(59, 130, 246, 0.2)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center'
                    }}>
                        <Clock size={24} color="#3b82f6" />
                    </div>
                    <div>
                        <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{formatDuration(call.duration)}</div>
                        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Duración</div>
                    </div>
                </div>

                <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{
                        width: '48px', height: '48px', borderRadius: '12px',
                        background: 'rgba(16, 185, 129, 0.2)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center'
                    }}>
                        <ThumbsUp size={24} color="#10b981" />
                    </div>
                    <div>
                        <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{call.satisfaction || 'N/A'}/5</div>
                        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Satisfacción</div>
                    </div>
                </div>

                <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{
                        width: '48px', height: '48px', borderRadius: '12px',
                        background: 'rgba(139, 92, 246, 0.2)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center'
                    }}>
                        <User size={24} color="#8b5cf6" />
                    </div>
                    <div>
                        <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{agent?.name || 'AI'}</div>
                        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Agente</div>
                    </div>
                </div>

                <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{
                        width: '48px', height: '48px', borderRadius: '12px',
                        background: 'rgba(6, 182, 212, 0.2)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center'
                    }}>
                        <Tag size={24} color="#06b6d4" />
                    </div>
                    <div>
                        <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{call.category}</div>
                        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Categoría</div>
                    </div>
                </div>
            </div>

            <div className="grid grid-2" style={{ marginBottom: '2rem' }}>
                {/* Emotion Timeline */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">📊 Línea de Tiempo Emocional</h3>
                    </div>

                    {call.emotions.timeline.length > 0 && (
                        <div className="chart-container">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={emotionData}>
                                    <defs>
                                        <linearGradient id="emotionGradient" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                    <XAxis dataKey="time" tick={{ fill: '#6b7280', fontSize: 12 }} />
                                    <YAxis
                                        domain={[-1, 1]}
                                        tick={{ fill: '#6b7280', fontSize: 12 }}
                                        tickFormatter={(v) => v === 1 ? '😊' : v === 0 ? '😐' : '😠'}
                                    />
                                    <Tooltip
                                        contentStyle={{ background: '#1a1a24', border: '1px solid rgba(255,255,255,0.1)' }}
                                        formatter={(value, name, props) => [
                                            `${EMOTIONS[props.payload.emotion]?.label} (${Math.round(props.payload.confidence * 100)}%)`,
                                            'Emoción'
                                        ]}
                                    />
                                    <Area type="monotone" dataKey="value" stroke="#3b82f6" fill="url(#emotionGradient)" strokeWidth={2} />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    )}

                    {/* Emotion Summary */}
                    <div style={{ marginTop: '1rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                        {Object.entries(call.emotions.summary).map(([emotion, value]) => (
                            <div key={emotion} style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem',
                                padding: '0.5rem 0.75rem',
                                background: `${emotionColors[emotion]}15`,
                                borderRadius: '8px',
                                fontSize: '0.85rem'
                            }}>
                                <span>{EMOTIONS[emotion]?.icon}</span>
                                <span style={{ color: emotionColors[emotion], fontWeight: 600 }}>{value}%</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Call Metrics */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">📈 Métricas de la Llamada</h3>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                        <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: '12px' }}>
                            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--accent-blue)' }}>
                                {call.metrics?.wordsPerMinute || 'N/A'}
                            </div>
                            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Palabras/min</div>
                        </div>

                        <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: '12px' }}>
                            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--accent-purple)' }}>
                                {call.metrics?.silencePercentage || 0}%
                            </div>
                            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Silencio</div>
                        </div>

                        <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: '12px' }}>
                            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--accent-yellow)' }}>
                                {call.metrics?.interruptionCount || 0}
                            </div>
                            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Interrupciones</div>
                        </div>

                        <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: '12px' }}>
                            <div style={{
                                fontSize: '1.5rem',
                                fontWeight: 700,
                                color: call.metrics?.sentimentScore > 0 ? 'var(--accent-green)' : 'var(--accent-red)'
                            }}>
                                {call.metrics?.sentimentScore > 0 ? '+' : ''}{call.metrics?.sentimentScore || 0}
                            </div>
                            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Sentimiento</div>
                        </div>
                    </div>

                    {/* Resolution Status */}
                    <div style={{
                        marginTop: '1rem',
                        padding: '1rem',
                        background: call.resolution === 'resolved' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                        borderRadius: '12px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.75rem'
                    }}>
                        <div style={{
                            width: '40px',
                            height: '40px',
                            borderRadius: '10px',
                            background: call.resolution === 'resolved' ? '#10b981' : '#f59e0b',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '1.25rem'
                        }}>
                            {call.resolution === 'resolved' ? '✓' : '↗'}
                        </div>
                        <div>
                            <div style={{ fontWeight: 600 }}>
                                {call.resolution === 'resolved' ? 'Caso Resuelto' : 'Caso Escalado'}
                            </div>
                            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                                {call.resolution === 'resolved' ? 'El cliente quedó satisfecho' : 'Transferido a supervisor'}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Transcript */}
            <div className="card">
                <div className="card-header">
                    <h3 className="card-title">💬 Transcripción</h3>
                    <button className="btn btn-secondary btn-sm">
                        <Download size={14} />
                        Descargar
                    </button>
                </div>

                <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                    {call.transcript.length > 0 ? (
                        call.transcript.map((msg, i) => (
                            <div key={i} style={{
                                display: 'flex',
                                gap: '1rem',
                                padding: '1rem',
                                background: msg.role === 'agent' ? 'rgba(59, 130, 246, 0.05)' : 'transparent',
                                borderRadius: '8px',
                                marginBottom: '0.5rem'
                            }}>
                                <div className="avatar" style={{
                                    width: '32px',
                                    height: '32px',
                                    fontSize: '0.8rem',
                                    background: msg.role === 'agent' ? 'var(--gradient-primary)' : 'rgba(255,255,255,0.1)',
                                    flexShrink: 0
                                }}>
                                    {msg.role === 'agent' ? '🤖' : call.caller.name.charAt(0)}
                                </div>
                                <div style={{ flex: 1 }}>
                                    <div style={{
                                        display: 'flex',
                                        justifyContent: 'space-between',
                                        marginBottom: '0.25rem'
                                    }}>
                                        <span style={{ fontWeight: 500, fontSize: '0.9rem' }}>
                                            {msg.role === 'agent' ? 'AI Agent' : call.caller.name}
                                        </span>
                                        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                                            {formatDuration(msg.time)}
                                        </span>
                                    </div>
                                    <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>{msg.text}</p>
                                </div>
                            </div>
                        ))
                    ) : (
                        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                            Transcripción no disponible para esta llamada
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
