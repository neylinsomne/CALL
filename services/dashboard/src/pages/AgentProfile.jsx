import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    ArrowLeft, Phone, Clock, ThumbsUp, TrendingUp,
    Play, MessageSquare, Calendar, Star, Target
} from 'lucide-react';
import {
    LineChart, Line, AreaChart, Area, BarChart, Bar,
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { MOCK_AGENTS, MOCK_CALLS, EMOTIONS, formatDuration, formatDate, getAgentById } from '../data/mockData';

// Get agent's calls
function getAgentCalls(agentId) {
    return MOCK_CALLS.filter(c => c.agentId === agentId).slice(0, 20);
}

// Performance data for chart
function getPerformanceData(agentId) {
    return [
        { day: 'Lun', calls: 28, satisfaction: 4.5 },
        { day: 'Mar', calls: 32, satisfaction: 4.7 },
        { day: 'Mie', calls: 25, satisfaction: 4.4 },
        { day: 'Jue', calls: 35, satisfaction: 4.8 },
        { day: 'Vie', calls: 30, satisfaction: 4.6 },
        { day: 'Sab', calls: 15, satisfaction: 4.9 },
        { day: 'Dom', calls: 12, satisfaction: 4.5 },
    ];
}

function CallInteractionCard({ call, onClick }) {
    const dominantEmotion = Object.entries(call.emotions.summary)
        .sort((a, b) => b[1] - a[1])[0];

    return (
        <div
            className="card"
            style={{ padding: '1rem', cursor: 'pointer', marginBottom: '0.75rem' }}
            onClick={() => onClick(call)}
        >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    <div className="avatar" style={{ width: '40px', height: '40px' }}>
                        {call.caller.name.charAt(0)}
                    </div>
                    <div>
                        <div style={{ fontWeight: 600 }}>{call.caller.name}</div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                            {call.category} • {formatDuration(call.duration)}
                        </div>
                    </div>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    <span className={`badge emotion-${dominantEmotion[0]}`}>
                        {EMOTIONS[dominantEmotion[0]]?.icon}
                    </span>
                    {call.satisfaction && (
                        <span className="badge badge-success">
                            <Star size={12} /> {call.satisfaction}
                        </span>
                    )}
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {formatDate(call.startTime)}
                    </span>
                </div>
            </div>

            {/* Mini emotion bar */}
            <div style={{ marginTop: '0.75rem' }}>
                <div className="emotion-bar" style={{ height: '6px', borderRadius: '3px' }}>
                    {Object.entries(call.emotions.summary).map(([emotion, value]) => (
                        <div
                            key={emotion}
                            style={{
                                width: `${value}%`,
                                height: '100%',
                                background: EMOTIONS[emotion]?.color || '#6b7280'
                            }}
                        />
                    ))}
                </div>
            </div>
        </div>
    );
}

export default function AgentProfile() {
    const { id } = useParams();
    const navigate = useNavigate();
    const agent = MOCK_AGENTS.find(a => a.id === id) || MOCK_AGENTS[0];
    const agentCalls = getAgentCalls(agent.id);
    const performanceData = getPerformanceData(agent.id);

    const statusColors = {
        online: '#10b981',
        busy: '#f59e0b',
        offline: '#6b7280'
    };

    const statusLabels = {
        online: 'Disponible',
        busy: 'En llamada',
        offline: 'Desconectado'
    };

    // Calculate emotion stats from calls
    const emotionStats = agentCalls.reduce((acc, call) => {
        Object.entries(call.emotions.summary).forEach(([emotion, value]) => {
            acc[emotion] = (acc[emotion] || 0) + value;
        });
        return acc;
    }, {});

    const totalEmotions = Object.values(emotionStats).reduce((a, b) => a + b, 0);

    return (
        <div className="fade-in">
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '2rem' }}>
                <button className="btn-icon" onClick={() => navigate('/agents')}>
                    <ArrowLeft size={20} />
                </button>
                <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                    <div className="avatar" style={{
                        width: '80px',
                        height: '80px',
                        fontSize: '2rem',
                        position: 'relative'
                    }}>
                        {agent.avatar}
                        <div style={{
                            position: 'absolute',
                            bottom: '4px',
                            right: '4px',
                            width: '16px',
                            height: '16px',
                            borderRadius: '50%',
                            background: statusColors[agent.status],
                            border: '2px solid var(--bg-primary)'
                        }} />
                    </div>
                    <div>
                        <h1 style={{ fontSize: '1.75rem', fontWeight: 700 }}>{agent.name}</h1>
                        <div style={{ display: 'flex', gap: '1rem', color: 'var(--text-secondary)' }}>
                            <span>{agent.department}</span>
                            <span>•</span>
                            <span style={{ color: statusColors[agent.status] }}>{statusLabels[agent.status]}</span>
                        </div>
                    </div>
                </div>
                <button className="btn btn-primary">
                    <MessageSquare size={18} /> Enviar Mensaje
                </button>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-4" style={{ marginBottom: '2rem' }}>
                <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{
                        width: '48px', height: '48px', borderRadius: '12px',
                        background: 'rgba(59, 130, 246, 0.2)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center'
                    }}>
                        <Phone size={24} color="#3b82f6" />
                    </div>
                    <div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{agent.totalCalls}</div>
                        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Llamadas Totales</div>
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
                        <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{agent.satisfaction.toFixed(1)}</div>
                        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Satisfacción</div>
                    </div>
                </div>

                <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{
                        width: '48px', height: '48px', borderRadius: '12px',
                        background: 'rgba(139, 92, 246, 0.2)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center'
                    }}>
                        <Clock size={24} color="#8b5cf6" />
                    </div>
                    <div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{formatDuration(agent.avgDuration)}</div>
                        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Tiempo Promedio</div>
                    </div>
                </div>

                <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{
                        width: '48px', height: '48px', borderRadius: '12px',
                        background: 'rgba(6, 182, 212, 0.2)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center'
                    }}>
                        <Target size={24} color="#06b6d4" />
                    </div>
                    <div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{agent.resolutionRate}%</div>
                        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Tasa Resolución</div>
                    </div>
                </div>
            </div>

            <div className="grid grid-2" style={{ marginBottom: '2rem' }}>
                {/* Performance Chart */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">📈 Rendimiento Semanal</h3>
                    </div>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={performanceData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                <XAxis dataKey="day" tick={{ fill: '#6b7280', fontSize: 12 }} />
                                <YAxis tick={{ fill: '#6b7280', fontSize: 12 }} />
                                <Tooltip contentStyle={{ background: '#1a1a24', border: '1px solid rgba(255,255,255,0.1)' }} />
                                <Bar dataKey="calls" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Llamadas" />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Emotion Distribution */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">😊 Emociones en Llamadas</h3>
                    </div>
                    <div style={{ padding: '1rem 0' }}>
                        {Object.entries(emotionStats).map(([emotion, value]) => {
                            const percent = Math.round((value / totalEmotions) * 100);
                            return (
                                <div key={emotion} style={{ marginBottom: '1rem' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                        <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                            {EMOTIONS[emotion]?.icon} {EMOTIONS[emotion]?.label}
                                        </span>
                                        <span style={{ fontWeight: 600 }}>{percent}%</span>
                                    </div>
                                    <div className="progress-bar">
                                        <div
                                            className="progress-fill"
                                            style={{
                                                width: `${percent}%`,
                                                background: EMOTIONS[emotion]?.color || '#6b7280'
                                            }}
                                        />
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>

            {/* Interactions List */}
            <div className="card">
                <div className="card-header">
                    <h3 className="card-title">📞 Historial de Interacciones</h3>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                        {agentCalls.length} llamadas recientes
                    </span>
                </div>

                <div style={{ maxHeight: '500px', overflowY: 'auto' }}>
                    {agentCalls.map(call => (
                        <CallInteractionCard
                            key={call.id}
                            call={call}
                            onClick={(c) => navigate(`/calls/${c.id}`)}
                        />
                    ))}
                </div>
            </div>
        </div>
    );
}
