import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Search, Filter, Phone, PhoneIncoming, PhoneOutgoing,
    Clock, Smile, AlertCircle, ChevronDown, Play
} from 'lucide-react';
import { MOCK_CALLS, MOCK_AGENTS, EMOTIONS, formatDuration, formatDate, getAgentById } from '../data/mockData';

export default function Calls() {
    const navigate = useNavigate();
    const [search, setSearch] = useState('');
    const [agentFilter, setAgentFilter] = useState('');
    const [statusFilter, setStatusFilter] = useState('');
    const [categoryFilter, setCategoryFilter] = useState('');
    const [emotionFilter, setEmotionFilter] = useState('');

    // Filter calls
    const filteredCalls = MOCK_CALLS.filter(call => {
        if (search && !call.caller.name.toLowerCase().includes(search.toLowerCase()) &&
            !call.caller.phone.includes(search)) return false;
        if (agentFilter && call.agentId !== agentFilter) return false;
        if (statusFilter && call.status !== statusFilter) return false;
        if (categoryFilter && call.category !== categoryFilter) return false;
        if (emotionFilter) {
            const dominant = Object.entries(call.emotions.summary).sort((a, b) => b[1] - a[1])[0][0];
            if (dominant !== emotionFilter) return false;
        }
        return true;
    });

    const categories = [...new Set(MOCK_CALLS.map(c => c.category))];

    return (
        <div className="fade-in">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                <div>
                    <h1 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '0.5rem' }}>Llamadas</h1>
                    <p style={{ color: 'var(--text-secondary)' }}>{filteredCalls.length} llamadas encontradas</p>
                </div>
                <button className="btn btn-primary">
                    <Phone size={18} />
                    Nueva Llamada
                </button>
            </div>

            {/* Filters */}
            <div className="card" style={{ marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                    <div style={{ flex: 1, minWidth: '200px', position: 'relative' }}>
                        <Search size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                        <input
                            type="text"
                            className="input"
                            placeholder="Buscar por nombre o teléfono..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            style={{ paddingLeft: '40px' }}
                        />
                    </div>

                    <select
                        className="input select"
                        style={{ width: '180px' }}
                        value={agentFilter}
                        onChange={(e) => setAgentFilter(e.target.value)}
                    >
                        <option value="">Todos los agentes</option>
                        {MOCK_AGENTS.map(agent => (
                            <option key={agent.id} value={agent.id}>{agent.name}</option>
                        ))}
                    </select>

                    <select
                        className="input select"
                        style={{ width: '150px' }}
                        value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value)}
                    >
                        <option value="">Estado</option>
                        <option value="completed">Completada</option>
                        <option value="in-progress">En curso</option>
                        <option value="missed">Perdida</option>
                    </select>

                    <select
                        className="input select"
                        style={{ width: '150px' }}
                        value={categoryFilter}
                        onChange={(e) => setCategoryFilter(e.target.value)}
                    >
                        <option value="">Categoría</option>
                        {categories.map(cat => (
                            <option key={cat} value={cat}>{cat}</option>
                        ))}
                    </select>

                    <select
                        className="input select"
                        style={{ width: '150px' }}
                        value={emotionFilter}
                        onChange={(e) => setEmotionFilter(e.target.value)}
                    >
                        <option value="">Emoción</option>
                        {Object.entries(EMOTIONS).map(([key, val]) => (
                            <option key={key} value={key}>{val.icon} {val.label}</option>
                        ))}
                    </select>
                </div>
            </div>

            {/* Calls Table */}
            <div className="card">
                <div className="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Cliente</th>
                                <th>Tipo</th>
                                <th>Agente</th>
                                <th>Categoría</th>
                                <th>Duración</th>
                                <th>Emoción</th>
                                <th>Estado</th>
                                <th>Fecha</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredCalls.map(call => {
                                const agent = getAgentById(call.agentId);
                                const dominantEmotion = Object.entries(call.emotions.summary)
                                    .sort((a, b) => b[1] - a[1])[0];

                                return (
                                    <tr key={call.id} onClick={() => navigate(`/calls/${call.id}`)} style={{ cursor: 'pointer' }}>
                                        <td>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                                <div className="avatar" style={{ width: '36px', height: '36px', fontSize: '0.85rem' }}>
                                                    {call.caller.name.charAt(0)}
                                                </div>
                                                <div>
                                                    <div style={{ fontWeight: 500 }}>{call.caller.name}</div>
                                                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{call.caller.phone}</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td>
                                            {call.type === 'inbound' ? (
                                                <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: 'var(--accent-green)' }}>
                                                    <PhoneIncoming size={16} /> Entrante
                                                </span>
                                            ) : (
                                                <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: 'var(--accent-blue)' }}>
                                                    <PhoneOutgoing size={16} /> Saliente
                                                </span>
                                            )}
                                        </td>
                                        <td>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                <span className="avatar" style={{ width: '24px', height: '24px', fontSize: '0.7rem' }}>
                                                    {agent?.avatar || '🤖'}
                                                </span>
                                                {agent?.name || 'AI'}
                                            </div>
                                        </td>
                                        <td>{call.category}</td>
                                        <td style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                                            <Clock size={14} color="var(--text-muted)" />
                                            {formatDuration(call.duration)}
                                        </td>
                                        <td>
                                            <span className={`badge emotion-${dominantEmotion[0]}`}>
                                                {EMOTIONS[dominantEmotion[0]]?.icon} {dominantEmotion[1]}%
                                            </span>
                                        </td>
                                        <td>
                                            <span className={`badge badge-${call.status === 'completed' ? 'success' :
                                                    call.status === 'in-progress' ? 'info' : 'danger'
                                                }`}>
                                                {call.status === 'completed' ? 'Completada' :
                                                    call.status === 'in-progress' ? 'En curso' : 'Perdida'}
                                            </span>
                                        </td>
                                        <td style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                                            {formatDate(call.startTime)}
                                        </td>
                                        <td>
                                            <button className="btn-icon" onClick={(e) => { e.stopPropagation(); }}>
                                                <Play size={16} />
                                            </button>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
