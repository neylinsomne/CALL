import { useState } from 'react';
import {
    Search, UserPlus, Phone, Clock, ThumbsUp, TrendingUp,
    Circle, MoreVertical
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { MOCK_AGENTS, formatDuration } from '../data/mockData';

function AgentCard({ agent }) {
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

    return (
        <div className="card" style={{ position: 'relative' }}>
            {/* Status indicator */}
            <div style={{
                position: 'absolute',
                top: '1rem',
                right: '1rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
            }}>
                <Circle size={8} fill={statusColors[agent.status]} color={statusColors[agent.status]} />
                <span style={{ fontSize: '0.8rem', color: statusColors[agent.status] }}>
                    {statusLabels[agent.status]}
                </span>
            </div>

            {/* Avatar and Name */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
                <div className="avatar" style={{ width: '56px', height: '56px', fontSize: '1.25rem' }}>
                    {agent.avatar}
                </div>
                <div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>{agent.name}</div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{agent.department}</div>
                </div>
            </div>

            {/* Stats Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
                <div style={{ padding: '0.75rem', background: 'var(--bg-secondary)', borderRadius: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                        <Phone size={14} color="var(--accent-blue)" />
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Llamadas</span>
                    </div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 600 }}>{agent.totalCalls}</div>
                </div>

                <div style={{ padding: '0.75rem', background: 'var(--bg-secondary)', borderRadius: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                        <Clock size={14} color="var(--accent-purple)" />
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Tiempo Prom.</span>
                    </div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 600 }}>{formatDuration(agent.avgDuration)}</div>
                </div>

                <div style={{ padding: '0.75rem', background: 'var(--bg-secondary)', borderRadius: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                        <ThumbsUp size={14} color="var(--accent-green)" />
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Satisfacción</span>
                    </div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 600 }}>{agent.satisfaction.toFixed(1)}</div>
                </div>

                <div style={{ padding: '0.75rem', background: 'var(--bg-secondary)', borderRadius: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                        <TrendingUp size={14} color="var(--accent-cyan)" />
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Resolución</span>
                    </div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 600 }}>{agent.resolutionRate}%</div>
                </div>
            </div>

            {/* Response Time */}
            <div style={{ marginTop: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Tiempo de respuesta</span>
                    <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>{agent.avgResponseTime}s</span>
                </div>
                <div className="progress-bar">
                    <div
                        className="progress-fill"
                        style={{
                            width: `${100 - (agent.avgResponseTime / 30 * 100)}%`,
                            background: agent.avgResponseTime <= 10 ? 'var(--accent-green)' :
                                agent.avgResponseTime <= 20 ? 'var(--accent-yellow)' : 'var(--accent-red)'
                        }}
                    />
                </div>
            </div>
        </div>
    );
}

export default function Agents() {
    const [search, setSearch] = useState('');
    const [departmentFilter, setDepartmentFilter] = useState('');
    const [statusFilter, setStatusFilter] = useState('');

    const departments = [...new Set(MOCK_AGENTS.map(a => a.department))];

    const filteredAgents = MOCK_AGENTS.filter(agent => {
        if (search && !agent.name.toLowerCase().includes(search.toLowerCase())) return false;
        if (departmentFilter && agent.department !== departmentFilter) return false;
        if (statusFilter && agent.status !== statusFilter) return false;
        return true;
    });

    // Chart data
    const performanceData = MOCK_AGENTS.map(a => ({
        name: a.name.split(' ')[0],
        calls: a.totalCalls,
        satisfaction: a.satisfaction * 20 // Scale to 100
    }));

    return (
        <div className="fade-in">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                <div>
                    <h1 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '0.5rem' }}>Agentes</h1>
                    <p style={{ color: 'var(--text-secondary)' }}>
                        {filteredAgents.filter(a => a.status === 'online').length} disponibles de {filteredAgents.length}
                    </p>
                </div>
                <button className="btn btn-primary">
                    <UserPlus size={18} />
                    Agregar Agente
                </button>
            </div>

            {/* Summary Stats */}
            <div className="grid grid-4" style={{ marginBottom: '2rem' }}>
                {[
                    { label: 'Total Agentes', value: MOCK_AGENTS.length, color: 'var(--accent-blue)' },
                    { label: 'Disponibles', value: MOCK_AGENTS.filter(a => a.status === 'online').length, color: 'var(--accent-green)' },
                    { label: 'En Llamada', value: MOCK_AGENTS.filter(a => a.status === 'busy').length, color: 'var(--accent-yellow)' },
                    { label: 'Desconectados', value: MOCK_AGENTS.filter(a => a.status === 'offline').length, color: 'var(--text-muted)' },
                ].map(stat => (
                    <div key={stat.label} className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                        <div style={{
                            width: '48px',
                            height: '48px',
                            borderRadius: '12px',
                            background: `${stat.color}22`,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '1.5rem',
                            fontWeight: 700,
                            color: stat.color
                        }}>
                            {stat.value}
                        </div>
                        <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>{stat.label}</div>
                    </div>
                ))}
            </div>

            {/* Performance Chart */}
            <div className="card" style={{ marginBottom: '2rem' }}>
                <div className="card-header">
                    <h3 className="card-title">Rendimiento por Agente</h3>
                </div>
                <div className="chart-container">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={performanceData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                            <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 12 }} />
                            <YAxis tick={{ fill: '#6b7280', fontSize: 12 }} />
                            <Tooltip contentStyle={{ background: '#1a1a24', border: '1px solid rgba(255,255,255,0.1)' }} />
                            <Bar dataKey="calls" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Llamadas" />
                            <Bar dataKey="satisfaction" fill="#10b981" radius={[4, 4, 0, 0]} name="Satisfacción" />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Filters */}
            <div className="card" style={{ marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', gap: '1rem' }}>
                    <div style={{ flex: 1, position: 'relative' }}>
                        <Search size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                        <input
                            type="text"
                            className="input"
                            placeholder="Buscar agente..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            style={{ paddingLeft: '40px' }}
                        />
                    </div>

                    <select
                        className="input select"
                        style={{ width: '180px' }}
                        value={departmentFilter}
                        onChange={(e) => setDepartmentFilter(e.target.value)}
                    >
                        <option value="">Departamento</option>
                        {departments.map(dept => (
                            <option key={dept} value={dept}>{dept}</option>
                        ))}
                    </select>

                    <select
                        className="input select"
                        style={{ width: '150px' }}
                        value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value)}
                    >
                        <option value="">Estado</option>
                        <option value="online">Disponible</option>
                        <option value="busy">En llamada</option>
                        <option value="offline">Desconectado</option>
                    </select>
                </div>
            </div>

            {/* Agent Cards Grid */}
            <div className="grid grid-3">
                {filteredAgents.map(agent => (
                    <AgentCard key={agent.id} agent={agent} />
                ))}
            </div>
        </div>
    );
}
