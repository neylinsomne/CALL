import {
    BarChart, Bar, LineChart, Line, AreaChart, Area, PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import { Calendar, Download, Filter } from 'lucide-react';
import { MOCK_METRICS, EMOTIONS } from '../data/mockData';

export default function Analytics() {
    const metrics = MOCK_METRICS;
    const pieColors = ['#10b981', '#6b7280', '#f59e0b', '#ef4444', '#8b5cf6'];

    // Transform emotion trends for stacked area chart
    const emotionTrends = metrics.trends.emotions;

    return (
        <div className="fade-in">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                <div>
                    <h1 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '0.5rem' }}>Analytics</h1>
                    <p style={{ color: 'var(--text-secondary)' }}>Análisis detallado del rendimiento</p>
                </div>
                <div style={{ display: 'flex', gap: '1rem' }}>
                    <button className="btn btn-secondary">
                        <Calendar size={18} />
                        Últimos 7 días
                    </button>
                    <button className="btn btn-primary">
                        <Download size={18} />
                        Exportar Reporte
                    </button>
                </div>
            </div>

            {/* KPI Summary */}
            <div className="grid grid-4" style={{ marginBottom: '2rem' }}>
                {[
                    { label: 'Llamadas Totales', value: '1,245', change: '+12%', positive: true },
                    { label: 'Tiempo Promedio', value: '4:23', change: '-8%', positive: true },
                    { label: 'Satisfacción', value: '4.6', change: '+5%', positive: true },
                    { label: 'Tasa Resolución', value: '89%', change: '+3%', positive: true },
                ].map(kpi => (
                    <div key={kpi.label} className="card stat-card">
                        <div className="stat-value">{kpi.value}</div>
                        <div className="stat-label">{kpi.label}</div>
                        <div className={`stat-change ${kpi.positive ? 'positive' : 'negative'}`}>
                            {kpi.change}
                        </div>
                    </div>
                ))}
            </div>

            {/* Charts Row 1 */}
            <div className="grid grid-2" style={{ marginBottom: '2rem' }}>
                {/* Calls Trend */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">📈 Tendencia de Llamadas</h3>
                    </div>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={metrics.trends.calls}>
                                <defs>
                                    <linearGradient id="callsGradient" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                <XAxis dataKey="date" tick={{ fill: '#6b7280', fontSize: 12 }} tickFormatter={(v) => v.split('-')[2]} />
                                <YAxis tick={{ fill: '#6b7280', fontSize: 12 }} />
                                <Tooltip contentStyle={{ background: '#1a1a24', border: '1px solid rgba(255,255,255,0.1)' }} />
                                <Area type="monotone" dataKey="value" stroke="#3b82f6" fill="url(#callsGradient)" strokeWidth={2} />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Satisfaction Trend */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">⭐ Tendencia de Satisfacción</h3>
                    </div>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={metrics.trends.satisfaction}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                <XAxis dataKey="date" tick={{ fill: '#6b7280', fontSize: 12 }} tickFormatter={(v) => v.split('-')[2]} />
                                <YAxis domain={[4, 5]} tick={{ fill: '#6b7280', fontSize: 12 }} />
                                <Tooltip contentStyle={{ background: '#1a1a24', border: '1px solid rgba(255,255,255,0.1)' }} />
                                <Line type="monotone" dataKey="value" stroke="#10b981" strokeWidth={3} dot={{ fill: '#10b981', strokeWidth: 2 }} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Charts Row 2 */}
            <div className="grid grid-2" style={{ marginBottom: '2rem' }}>
                {/* Emotions Trend */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">😊 Tendencia de Emociones</h3>
                    </div>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={emotionTrends}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                <XAxis dataKey="date" tick={{ fill: '#6b7280', fontSize: 12 }} tickFormatter={(v) => v.split('-')[2]} />
                                <YAxis tick={{ fill: '#6b7280', fontSize: 12 }} />
                                <Tooltip contentStyle={{ background: '#1a1a24', border: '1px solid rgba(255,255,255,0.1)' }} />
                                <Legend />
                                <Area type="monotone" dataKey="happy" stackId="1" stroke="#10b981" fill="#10b981" fillOpacity={0.6} name="Feliz" />
                                <Area type="monotone" dataKey="neutral" stackId="1" stroke="#6b7280" fill="#6b7280" fillOpacity={0.6} name="Neutral" />
                                <Area type="monotone" dataKey="frustrated" stackId="1" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.6} name="Frustrado" />
                                <Area type="monotone" dataKey="angry" stackId="1" stroke="#ef4444" fill="#ef4444" fillOpacity={0.6} name="Enojado" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Emotion Distribution Pie */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">🎯 Distribución de Emociones</h3>
                    </div>
                    <div className="chart-container" style={{ display: 'flex', alignItems: 'center' }}>
                        <ResponsiveContainer width="60%" height="100%">
                            <PieChart>
                                <Pie
                                    data={Object.entries(metrics.emotionDistribution).map(([key, value]) => ({
                                        name: EMOTIONS[key]?.label || key,
                                        value,
                                        icon: EMOTIONS[key]?.icon
                                    }))}
                                    dataKey="value"
                                    nameKey="name"
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={90}
                                    paddingAngle={3}
                                >
                                    {Object.keys(metrics.emotionDistribution).map((key, index) => (
                                        <Cell key={key} fill={pieColors[index % pieColors.length]} />
                                    ))}
                                </Pie>
                                <Tooltip contentStyle={{ background: '#1a1a24', border: '1px solid rgba(255,255,255,0.1)' }} />
                            </PieChart>
                        </ResponsiveContainer>
                        <div>
                            {Object.entries(metrics.emotionDistribution).map(([key, value], i) => (
                                <div key={key} style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.75rem',
                                    marginBottom: '0.75rem'
                                }}>
                                    <div style={{
                                        width: '12px',
                                        height: '12px',
                                        borderRadius: '3px',
                                        background: pieColors[i]
                                    }} />
                                    <span style={{ fontSize: '1rem' }}>{EMOTIONS[key]?.icon}</span>
                                    <span style={{ flex: 1 }}>{EMOTIONS[key]?.label}</span>
                                    <span style={{ fontWeight: 600 }}>{value}%</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Charts Row 3 */}
            <div className="grid grid-2">
                {/* Calls by Hour */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">🕐 Llamadas por Hora</h3>
                    </div>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={metrics.byHour}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                <XAxis dataKey="hour" tick={{ fill: '#6b7280', fontSize: 12 }} />
                                <YAxis tick={{ fill: '#6b7280', fontSize: 12 }} />
                                <Tooltip contentStyle={{ background: '#1a1a24', border: '1px solid rgba(255,255,255,0.1)' }} />
                                <Bar dataKey="calls" fill="#8b5cf6" radius={[4, 4, 0, 0]} name="Llamadas" />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Category Distribution */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">📊 Llamadas por Categoría</h3>
                    </div>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={metrics.byCategory} layout="vertical">
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                <XAxis type="number" tick={{ fill: '#6b7280', fontSize: 12 }} />
                                <YAxis type="category" dataKey="name" tick={{ fill: '#6b7280', fontSize: 12 }} width={80} />
                                <Tooltip contentStyle={{ background: '#1a1a24', border: '1px solid rgba(255,255,255,0.1)' }} />
                                <Bar dataKey="count" fill="#06b6d4" radius={[0, 4, 4, 0]} name="Cantidad" />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>
        </div>
    );
}
