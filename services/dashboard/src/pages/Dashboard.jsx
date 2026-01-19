import {
    Phone,
    Users,
    Clock,
    ThumbsUp,
    TrendingUp,
    TrendingDown,
    Bot,
    UserCheck,
    AlertTriangle,
    Smile
} from 'lucide-react';
import {
    LineChart, Line, AreaChart, Area, BarChart, Bar,
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts';
import { MOCK_METRICS, MOCK_CALLS, MOCK_AGENTS, EMOTIONS, formatDuration, getAgentById } from '../data/mockData';

// Stat Card Component
function StatCard({ title, value, change, changeType, icon: Icon, color }) {
    return (
        <div className="card stat-card" style={{ '--accent': color }}>
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                marginBottom: '1rem'
            }}>
                <div>
                    <div className="stat-value">{value}</div>
                    <div className="stat-label">{title}</div>
                </div>
                <div style={{
                    width: '48px',
                    height: '48px',
                    borderRadius: '12px',
                    background: `linear-gradient(135deg, ${color}22, ${color}44)`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                }}>
                    <Icon size={24} color={color} />
                </div>
            </div>
            {change && (
                <div className={`stat-change ${changeType}`}>
                    {changeType === 'positive' ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                    {change}% vs ayer
                </div>
            )}
        </div>
    );
}

// Emotion Distribution Component
function EmotionDistribution({ data }) {
    const colors = {
        happy: '#10b981',
        neutral: '#6b7280',
        frustrated: '#f59e0b',
        angry: '#ef4444',
        sad: '#8b5cf6'
    };

    return (
        <div className="card">
            <div className="card-header">
                <h3 className="card-title">Distribución de Emociones</h3>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Hoy</span>
            </div>

            <div className="emotion-meter" style={{ marginBottom: '1.5rem' }}>
                <div className="emotion-bar">
                    {Object.entries(data).map(([emotion, value]) => (
                        <div
                            key={emotion}
                            className="emotion-segment"
                            style={{
                                width: `${value}%`,
                                background: colors[emotion],
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center'
                            }}
                            title={`${EMOTIONS[emotion]?.label}: ${value}%`}
                        >
                            {value > 10 && <span style={{ fontSize: '0.75rem' }}>{EMOTIONS[emotion]?.icon}</span>}
                        </div>
                    ))}
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '0.5rem' }}>
                {Object.entries(data).map(([emotion, value]) => (
                    <div key={emotion} style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '1.25rem' }}>{EMOTIONS[emotion]?.icon}</div>
                        <div style={{ fontSize: '0.9rem', fontWeight: 600 }}>{value}%</div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                            {EMOTIONS[emotion]?.label}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

// Recent Calls Component
function RecentCalls({ calls }) {
    return (
        <div className="card">
            <div className="card-header">
                <h3 className="card-title">Llamadas Recientes</h3>
                <a href="/calls" style={{ fontSize: '0.85rem', color: 'var(--accent-blue)' }}>Ver todas</a>
            </div>

            {calls.slice(0, 5).map(call => {
                const agent = getAgentById(call.agentId);
                const dominantEmotion = Object.entries(call.emotions.summary)
                    .sort((a, b) => b[1] - a[1])[0];

                return (
                    <div key={call.id} className="call-card">
                        <div className="call-avatar">{call.caller.name.charAt(0)}</div>
                        <div className="call-info">
                            <div className="call-name">{call.caller.name}</div>
                            <div className="call-meta">
                                <span>{call.category}</span>
                                <span>•</span>
                                <span>{formatDuration(call.duration)}</span>
                                <span>•</span>
                                <span>{agent?.name || 'AI'}</span>
                            </div>
                        </div>
                        <div className="call-stats">
                            <span className={`badge emotion-${dominantEmotion[0]}`}>
                                {EMOTIONS[dominantEmotion[0]]?.icon} {dominantEmotion[1]}%
                            </span>
                            <span className={`badge badge-${call.resolution === 'resolved' ? 'success' : 'warning'}`}>
                                {call.resolution === 'resolved' ? 'Resuelto' : 'Escalado'}
                            </span>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}

// Agent Performance Component
function AgentPerformance({ agents }) {
    return (
        <div className="card">
            <div className="card-header">
                <h3 className="card-title">Rendimiento de Agentes</h3>
                <a href="/agents" style={{ fontSize: '0.85rem', color: 'var(--accent-blue)' }}>Ver todos</a>
            </div>

            <div className="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Agente</th>
                            <th>Llamadas</th>
                            <th>Satisfacción</th>
                            <th>Resolución</th>
                        </tr>
                    </thead>
                    <tbody>
                        {agents.slice(0, 5).map(agent => (
                            <tr key={agent.id}>
                                <td>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                        <div className="avatar" style={{ width: '32px', height: '32px', fontSize: '0.8rem' }}>
                                            {agent.avatar}
                                        </div>
                                        <div>
                                            <div style={{ fontWeight: 500 }}>{agent.name}</div>
                                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{agent.department}</div>
                                        </div>
                                    </div>
                                </td>
                                <td>{agent.totalCalls}</td>
                                <td>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        <Smile size={16} color="var(--accent-yellow)" />
                                        {agent.satisfaction.toFixed(1)}
                                    </div>
                                </td>
                                <td>
                                    <div className="progress-bar" style={{ width: '80px' }}>
                                        <div className="progress-fill" style={{ width: `${agent.resolutionRate}%` }} />
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

export default function Dashboard() {
    const metrics = MOCK_METRICS;
    const pieColors = ['#3b82f6', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b'];

    return (
        <div className="fade-in">
            <div style={{ marginBottom: '2rem' }}>
                <h1 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '0.5rem' }}>Dashboard</h1>
                <p style={{ color: 'var(--text-secondary)' }}>Resumen de actividad del call center</p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-4" style={{ marginBottom: '2rem' }}>
                <StatCard
                    title="Llamadas Hoy"
                    value={metrics.today.totalCalls}
                    change={12}
                    changeType="positive"
                    icon={Phone}
                    color="#3b82f6"
                />
                <StatCard
                    title="Tiempo Promedio"
                    value={formatDuration(metrics.today.avgDuration)}
                    change={5}
                    changeType="negative"
                    icon={Clock}
                    color="#8b5cf6"
                />
                <StatCard
                    title="Satisfacción"
                    value={metrics.today.satisfaction.toFixed(1)}
                    change={3}
                    changeType="positive"
                    icon={ThumbsUp}
                    color="#10b981"
                />
                <StatCard
                    title="Tasa Resolución"
                    value={`${metrics.today.resolutionRate}%`}
                    change={2}
                    changeType="positive"
                    icon={UserCheck}
                    color="#06b6d4"
                />
            </div>

            {/* AI vs Human Stats */}
            <div className="grid grid-2" style={{ marginBottom: '2rem' }}>
                <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
                    <div style={{
                        width: '80px',
                        height: '80px',
                        borderRadius: '50%',
                        background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                    }}>
                        <Bot size={40} color="white" />
                    </div>
                    <div>
                        <div style={{ fontSize: '2rem', fontWeight: 700 }}>{metrics.today.aiHandled}%</div>
                        <div style={{ color: 'var(--text-secondary)' }}>Manejadas por AI</div>
                        <div style={{ fontSize: '0.85rem', color: 'var(--accent-green)', marginTop: '0.25rem' }}>
                            Sin intervención humana
                        </div>
                    </div>
                </div>

                <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
                    <div style={{
                        width: '80px',
                        height: '80px',
                        borderRadius: '50%',
                        background: 'linear-gradient(135deg, #f59e0b, #ef4444)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                    }}>
                        <AlertTriangle size={40} color="white" />
                    </div>
                    <div>
                        <div style={{ fontSize: '2rem', fontWeight: 700 }}>{metrics.today.humanRequired}%</div>
                        <div style={{ color: 'var(--text-secondary)' }}>Requirieron Humano</div>
                        <div style={{ fontSize: '0.85rem', color: 'var(--accent-yellow)', marginTop: '0.25rem' }}>
                            Escaladas a agente
                        </div>
                    </div>
                </div>
            </div>

            {/* Charts Row */}
            <div className="grid grid-2" style={{ marginBottom: '2rem' }}>
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">Llamadas por Día</h3>
                    </div>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={metrics.trends.calls}>
                                <defs>
                                    <linearGradient id="colorCalls" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                <XAxis dataKey="date" tick={{ fill: '#6b7280', fontSize: 12 }} tickFormatter={(v) => v.split('-')[2]} />
                                <YAxis tick={{ fill: '#6b7280', fontSize: 12 }} />
                                <Tooltip contentStyle={{ background: '#1a1a24', border: '1px solid rgba(255,255,255,0.1)' }} />
                                <Area type="monotone" dataKey="value" stroke="#3b82f6" fill="url(#colorCalls)" strokeWidth={2} />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">Llamadas por Categoría</h3>
                    </div>
                    <div className="chart-container" style={{ display: 'flex', alignItems: 'center' }}>
                        <ResponsiveContainer width="50%" height="100%">
                            <PieChart>
                                <Pie
                                    data={metrics.byCategory}
                                    dataKey="count"
                                    nameKey="name"
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={50}
                                    outerRadius={80}
                                    paddingAngle={2}
                                >
                                    {metrics.byCategory.map((entry, index) => (
                                        <Cell key={entry.name} fill={pieColors[index % pieColors.length]} />
                                    ))}
                                </Pie>
                                <Tooltip contentStyle={{ background: '#1a1a24', border: '1px solid rgba(255,255,255,0.1)' }} />
                            </PieChart>
                        </ResponsiveContainer>
                        <div style={{ flex: 1 }}>
                            {metrics.byCategory.map((cat, i) => (
                                <div key={cat.name} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                                    <div style={{ width: '12px', height: '12px', borderRadius: '3px', background: pieColors[i] }} />
                                    <span style={{ flex: 1, fontSize: '0.9rem' }}>{cat.name}</span>
                                    <span style={{ fontWeight: 600 }}>{cat.percentage}%</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Emotion Distribution */}
            <EmotionDistribution data={metrics.emotionDistribution} />

            {/* Recent Calls and Agent Performance */}
            <div className="grid grid-2" style={{ marginTop: '2rem' }}>
                <RecentCalls calls={MOCK_CALLS} />
                <AgentPerformance agents={MOCK_AGENTS} />
            </div>
        </div>
    );
}
