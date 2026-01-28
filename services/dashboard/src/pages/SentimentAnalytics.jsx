import { useState } from 'react';
import {
    BarChart, Bar, LineChart, Line, AreaChart, Area, PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, RadarChart,
    PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts';
import { Calendar, Download, TrendingUp, TrendingDown, AlertCircle, CheckCircle } from 'lucide-react';
import { MOCK_METRICS } from '../data/mockData';

// Gauge Component for scores
function ScoreGauge({ value, max, label, color, description }) {
    const percentage = (value / max) * 100;
    const isGood = value >= (max * 0.6);

    return (
        <div className="card" style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                {label}
            </div>
            <div style={{ position: 'relative', margin: '0 auto', width: '120px', height: '60px' }}>
                <svg viewBox="0 0 120 60" style={{ width: '100%' }}>
                    {/* Background arc */}
                    <path
                        d="M 10 55 A 50 50 0 0 1 110 55"
                        fill="none"
                        stroke="var(--bg-secondary)"
                        strokeWidth="10"
                        strokeLinecap="round"
                    />
                    {/* Value arc */}
                    <path
                        d="M 10 55 A 50 50 0 0 1 110 55"
                        fill="none"
                        stroke={color}
                        strokeWidth="10"
                        strokeLinecap="round"
                        strokeDasharray={`${percentage * 1.57} 157`}
                    />
                </svg>
            </div>
            <div style={{ fontSize: '2rem', fontWeight: 700, color, marginTop: '0.5rem' }}>
                {typeof value === 'number' && value % 1 !== 0 ? value.toFixed(1) : value}
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                {description}
            </div>
        </div>
    );
}

// Metric Card with trend
function MetricCard({ title, value, unit, trend, trendValue, color, icon: Icon }) {
    const isPositive = trendValue > 0;
    return (
        <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                        {title}
                    </div>
                    <div style={{ fontSize: '2rem', fontWeight: 700, color }}>
                        {value}{unit}
                    </div>
                </div>
                <div style={{
                    width: '48px', height: '48px', borderRadius: '12px',
                    background: `${color}22`, display: 'flex', alignItems: 'center', justifyContent: 'center'
                }}>
                    {Icon && <Icon size={24} color={color} />}
                </div>
            </div>
            {trend && (
                <div style={{
                    display: 'flex', alignItems: 'center', gap: '0.5rem',
                    marginTop: '0.75rem', fontSize: '0.85rem',
                    color: isPositive ? 'var(--accent-green)' : 'var(--accent-red)'
                }}>
                    {isPositive ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                    {isPositive ? '+' : ''}{trendValue}% vs semana anterior
                </div>
            )}
        </div>
    );
}

// Rubric Progress Bar
function RubricBar({ label, value, color }) {
    const getColor = (v) => {
        if (v >= 80) return 'var(--accent-green)';
        if (v >= 60) return 'var(--accent-blue)';
        if (v >= 40) return 'var(--accent-yellow)';
        return 'var(--accent-red)';
    };

    return (
        <div style={{ marginBottom: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.85rem' }}>{label}</span>
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: color || getColor(value) }}>
                    {value}%
                </span>
            </div>
            <div className="progress-bar">
                <div
                    className="progress-fill"
                    style={{ width: `${value}%`, background: color || getColor(value) }}
                />
            </div>
        </div>
    );
}

export default function SentimentAnalytics() {
    const { sentiment } = MOCK_METRICS;
    const [activeTab, setActiveTab] = useState('overview');

    // Prepare radar data for rubrics
    const vocalRadarData = Object.entries(sentiment.rubrics.vocal).map(([key, value]) => ({
        subject: key.charAt(0).toUpperCase() + key.slice(1),
        value,
        fullMark: 100
    }));

    const linguisticRadarData = Object.entries(sentiment.rubrics.linguistic).map(([key, value]) => ({
        subject: key.charAt(0).toUpperCase() + key.slice(1),
        value,
        fullMark: 100
    }));

    const behavioralRadarData = Object.entries(sentiment.rubrics.behavioral).map(([key, value]) => ({
        subject: key.charAt(0).toUpperCase() + key.slice(1),
        value,
        fullMark: 100
    }));

    // NPS Distribution data
    const npsData = [
        { name: 'Promotores', value: sentiment.nps.promoters, color: '#10b981' },
        { name: 'Pasivos', value: sentiment.nps.passives, color: '#f59e0b' },
        { name: 'Detractores', value: sentiment.nps.detractors, color: '#ef4444' }
    ];

    return (
        <div className="fade-in">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                <div>
                    <h1 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '0.5rem' }}>
                        Analisis de Sentimiento
                    </h1>
                    <p style={{ color: 'var(--text-secondary)' }}>
                        Metricas NPS, CSAT, CES y rubricas de evaluacion
                    </p>
                </div>
                <div style={{ display: 'flex', gap: '1rem' }}>
                    <button className="btn btn-secondary">
                        <Calendar size={18} />
                        Ultimos 7 dias
                    </button>
                    <button className="btn btn-primary">
                        <Download size={18} />
                        Exportar
                    </button>
                </div>
            </div>

            {/* Tabs */}
            <div className="tabs" style={{ marginBottom: '2rem' }}>
                <button
                    className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
                    onClick={() => setActiveTab('overview')}
                >
                    Resumen
                </button>
                <button
                    className={`tab ${activeTab === 'nps' ? 'active' : ''}`}
                    onClick={() => setActiveTab('nps')}
                >
                    NPS
                </button>
                <button
                    className={`tab ${activeTab === 'csat' ? 'active' : ''}`}
                    onClick={() => setActiveTab('csat')}
                >
                    CSAT
                </button>
                <button
                    className={`tab ${activeTab === 'rubrics' ? 'active' : ''}`}
                    onClick={() => setActiveTab('rubrics')}
                >
                    Rubricas
                </button>
            </div>

            {activeTab === 'overview' && (
                <>
                    {/* Main Metrics */}
                    <div className="grid grid-4" style={{ marginBottom: '2rem' }}>
                        <ScoreGauge
                            value={sentiment.nps.score}
                            max={100}
                            label="NPS"
                            color={sentiment.nps.score > 0 ? '#10b981' : '#ef4444'}
                            description="Net Promoter Score"
                        />
                        <ScoreGauge
                            value={sentiment.csat.score}
                            max={5}
                            label="CSAT"
                            color="#3b82f6"
                            description="Customer Satisfaction"
                        />
                        <ScoreGauge
                            value={sentiment.ces.score}
                            max={7}
                            label="CES"
                            color={sentiment.ces.score < 3 ? '#10b981' : '#f59e0b'}
                            description="Customer Effort (menor=mejor)"
                        />
                        <ScoreGauge
                            value={sentiment.pta.ratio}
                            max={5}
                            label="PTA"
                            color="#8b5cf6"
                            description="Positive-to-Negative Ratio"
                        />
                    </div>

                    {/* Additional Metrics */}
                    <div className="grid grid-3" style={{ marginBottom: '2rem' }}>
                        <MetricCard
                            title="Intensidad Emocional Promedio"
                            value={sentiment.emotionIntensity.average}
                            unit="%"
                            trend={true}
                            trendValue={5}
                            color="#8b5cf6"
                        />
                        <MetricCard
                            title="Sentimiento Positivo"
                            value={sentiment.pta.positive}
                            unit="%"
                            trend={true}
                            trendValue={8}
                            color="#10b981"
                            icon={CheckCircle}
                        />
                        <MetricCard
                            title="Sentimiento Negativo"
                            value={sentiment.pta.negative}
                            unit="%"
                            trend={true}
                            trendValue={-12}
                            color="#ef4444"
                            icon={AlertCircle}
                        />
                    </div>

                    {/* FCR Impact */}
                    <div className="grid grid-2" style={{ marginBottom: '2rem' }}>
                        <div className="card">
                            <h3 style={{ marginBottom: '1rem' }}>Impacto FCR en Sentimiento</h3>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                                <div style={{
                                    padding: '1.5rem',
                                    background: 'rgba(16, 185, 129, 0.1)',
                                    borderRadius: '12px',
                                    textAlign: 'center'
                                }}>
                                    <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                                        Casos Resueltos
                                    </div>
                                    <div style={{ fontSize: '2rem', fontWeight: 700, color: '#10b981' }}>
                                        +{(sentiment.fcrImpact.resolved.avgSentiment * 100).toFixed(0)}%
                                    </div>
                                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                                        {sentiment.fcrImpact.resolved.count} llamadas
                                    </div>
                                </div>
                                <div style={{
                                    padding: '1.5rem',
                                    background: 'rgba(239, 68, 68, 0.1)',
                                    borderRadius: '12px',
                                    textAlign: 'center'
                                }}>
                                    <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                                        Casos Escalados
                                    </div>
                                    <div style={{ fontSize: '2rem', fontWeight: 700, color: '#ef4444' }}>
                                        {(sentiment.fcrImpact.escalated.avgSentiment * 100).toFixed(0)}%
                                    </div>
                                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                                        {sentiment.fcrImpact.escalated.count} llamadas
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="card">
                            <h3 style={{ marginBottom: '1rem' }}>Intensidad por Emocion</h3>
                            {Object.entries(sentiment.emotionIntensity.byEmotion).map(([key, data]) => (
                                <div key={key} style={{ marginBottom: '0.75rem' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.25rem' }}>
                                        <span style={{ textTransform: 'capitalize' }}>{key}</span>
                                        <span>Intensidad: {data.intensity}% | Frecuencia: {data.frequency}%</span>
                                    </div>
                                    <div className="progress-bar" style={{ height: '6px' }}>
                                        <div className="progress-fill" style={{
                                            width: `${data.intensity}%`,
                                            background: key === 'happy' ? '#10b981' :
                                                key === 'angry' ? '#ef4444' :
                                                    key === 'frustrated' ? '#f59e0b' : '#6b7280'
                                        }} />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </>
            )}

            {activeTab === 'nps' && (
                <>
                    <div className="grid grid-2" style={{ marginBottom: '2rem' }}>
                        <div className="card">
                            <h3 style={{ marginBottom: '1rem' }}>Net Promoter Score (NPS)</h3>
                            <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                                <div style={{ fontSize: '4rem', fontWeight: 700, color: sentiment.nps.score > 0 ? '#10b981' : '#ef4444' }}>
                                    {sentiment.nps.score > 0 ? '+' : ''}{sentiment.nps.score}
                                </div>
                                <div style={{ color: 'var(--text-muted)' }}>
                                    Rango: -100 a +100
                                </div>
                            </div>
                            <div className="chart-container">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={npsData} layout="vertical">
                                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                        <XAxis type="number" domain={[0, 100]} tick={{ fill: '#6b7280' }} />
                                        <YAxis type="category" dataKey="name" tick={{ fill: '#6b7280' }} width={100} />
                                        <Tooltip contentStyle={{ background: '#1a1a24', border: '1px solid rgba(255,255,255,0.1)' }} />
                                        <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                                            {npsData.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={entry.color} />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        </div>

                        <div className="card">
                            <h3 style={{ marginBottom: '1rem' }}>Tendencia NPS</h3>
                            <div className="chart-container" style={{ height: '300px' }}>
                                <ResponsiveContainer width="100%" height="100%">
                                    <AreaChart data={sentiment.nps.trend}>
                                        <defs>
                                            <linearGradient id="npsGradient" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                                                <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                                            </linearGradient>
                                        </defs>
                                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                        <XAxis dataKey="date" tickFormatter={(v) => v.split('-')[2]} tick={{ fill: '#6b7280' }} />
                                        <YAxis domain={[0, 100]} tick={{ fill: '#6b7280' }} />
                                        <Tooltip contentStyle={{ background: '#1a1a24', border: '1px solid rgba(255,255,255,0.1)' }} />
                                        <Area type="monotone" dataKey="value" stroke="#10b981" fill="url(#npsGradient)" strokeWidth={2} />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    </div>

                    {/* NPS Formula Explanation */}
                    <div className="card">
                        <h3 style={{ marginBottom: '1rem' }}>Formula NPS</h3>
                        <div style={{
                            padding: '1.5rem',
                            background: 'var(--bg-secondary)',
                            borderRadius: '12px',
                            fontFamily: 'monospace',
                            textAlign: 'center',
                            marginBottom: '1rem'
                        }}>
                            NPS = % Promotores - % Detractores = {sentiment.nps.promoters}% - {sentiment.nps.detractors}% = <strong style={{ color: '#10b981' }}>{sentiment.nps.score}</strong>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
                            <div style={{ textAlign: 'center', padding: '1rem', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '8px' }}>
                                <div style={{ fontWeight: 600, color: '#10b981' }}>Promotores (9-10)</div>
                                <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{sentiment.nps.promoters}%</div>
                            </div>
                            <div style={{ textAlign: 'center', padding: '1rem', background: 'rgba(245, 158, 11, 0.1)', borderRadius: '8px' }}>
                                <div style={{ fontWeight: 600, color: '#f59e0b' }}>Pasivos (7-8)</div>
                                <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{sentiment.nps.passives}%</div>
                            </div>
                            <div style={{ textAlign: 'center', padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '8px' }}>
                                <div style={{ fontWeight: 600, color: '#ef4444' }}>Detractores (0-6)</div>
                                <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{sentiment.nps.detractors}%</div>
                            </div>
                        </div>
                    </div>
                </>
            )}

            {activeTab === 'csat' && (
                <div className="grid grid-2">
                    <div className="card">
                        <h3 style={{ marginBottom: '1rem' }}>Distribucion CSAT</h3>
                        <div className="chart-container" style={{ height: '300px' }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={sentiment.csat.distribution}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                    <XAxis dataKey="rating" tick={{ fill: '#6b7280' }} />
                                    <YAxis tick={{ fill: '#6b7280' }} />
                                    <Tooltip contentStyle={{ background: '#1a1a24', border: '1px solid rgba(255,255,255,0.1)' }} />
                                    <Bar dataKey="percentage" fill="#3b82f6" radius={[4, 4, 0, 0]} name="%" />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    <div className="card">
                        <h3 style={{ marginBottom: '1rem' }}>Customer Effort Score (CES)</h3>
                        {sentiment.ces.effortLevels.map((level, i) => (
                            <RubricBar
                                key={level.level}
                                label={level.level}
                                value={level.percentage}
                                color={i < 2 ? '#10b981' : i === 2 ? '#f59e0b' : '#ef4444'}
                            />
                        ))}
                    </div>
                </div>
            )}

            {activeTab === 'rubrics' && (
                <>
                    <div className="grid grid-3" style={{ marginBottom: '2rem' }}>
                        {/* Vocal Rubrics */}
                        <div className="card">
                            <h3 style={{ marginBottom: '1rem' }}>Rubrica Vocal</h3>
                            <div style={{ height: '250px' }}>
                                <ResponsiveContainer width="100%" height="100%">
                                    <RadarChart data={vocalRadarData}>
                                        <PolarGrid stroke="rgba(255,255,255,0.1)" />
                                        <PolarAngleAxis dataKey="subject" tick={{ fill: '#6b7280', fontSize: 11 }} />
                                        <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#6b7280' }} />
                                        <Radar name="Vocal" dataKey="value" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.4} />
                                    </RadarChart>
                                </ResponsiveContainer>
                            </div>
                            <div style={{ marginTop: '1rem' }}>
                                {Object.entries(sentiment.rubrics.vocal).map(([key, value]) => (
                                    <RubricBar key={key} label={key} value={value} />
                                ))}
                            </div>
                        </div>

                        {/* Linguistic Rubrics */}
                        <div className="card">
                            <h3 style={{ marginBottom: '1rem' }}>Rubrica Linguistica</h3>
                            <div style={{ height: '250px' }}>
                                <ResponsiveContainer width="100%" height="100%">
                                    <RadarChart data={linguisticRadarData}>
                                        <PolarGrid stroke="rgba(255,255,255,0.1)" />
                                        <PolarAngleAxis dataKey="subject" tick={{ fill: '#6b7280', fontSize: 11 }} />
                                        <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#6b7280' }} />
                                        <Radar name="Linguistic" dataKey="value" stroke="#10b981" fill="#10b981" fillOpacity={0.4} />
                                    </RadarChart>
                                </ResponsiveContainer>
                            </div>
                            <div style={{ marginTop: '1rem' }}>
                                {Object.entries(sentiment.rubrics.linguistic).map(([key, value]) => (
                                    <RubricBar key={key} label={key} value={value} />
                                ))}
                            </div>
                        </div>

                        {/* Behavioral Rubrics */}
                        <div className="card">
                            <h3 style={{ marginBottom: '1rem' }}>Rubrica Comportamental</h3>
                            <div style={{ height: '250px' }}>
                                <ResponsiveContainer width="100%" height="100%">
                                    <RadarChart data={behavioralRadarData}>
                                        <PolarGrid stroke="rgba(255,255,255,0.1)" />
                                        <PolarAngleAxis dataKey="subject" tick={{ fill: '#6b7280', fontSize: 11 }} />
                                        <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#6b7280' }} />
                                        <Radar name="Behavioral" dataKey="value" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.4} />
                                    </RadarChart>
                                </ResponsiveContainer>
                            </div>
                            <div style={{ marginTop: '1rem' }}>
                                {Object.entries(sentiment.rubrics.behavioral).map(([key, value]) => (
                                    <RubricBar key={key} label={key} value={value} />
                                ))}
                            </div>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}
