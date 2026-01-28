// Mock Data for AI Call Center Dashboard
// Users, Agents, Calls, Emotions, Metrics

// ===========================================
// USERS (Authentication)
// ===========================================
export const MOCK_USERS = [
    {
        id: 'user-1',
        email: 'admin@callcenter.com',
        password: 'admin123',
        name: 'Admin Usuario',
        role: 'admin',
        avatar: 'AU'
    },
    {
        id: 'user-2',
        email: 'supervisor@callcenter.com',
        password: 'super123',
        name: 'María Supervisor',
        role: 'supervisor',
        avatar: 'MS'
    },
    {
        id: 'user-3',
        email: 'agent@callcenter.com',
        password: 'agent123',
        name: 'Carlos Agent',
        role: 'agent',
        avatar: 'CA'
    }
];

// ===========================================
// AGENTS
// ===========================================
export const MOCK_AGENTS = [
    {
        id: 'agent-1',
        name: 'Ana García',
        avatar: 'AG',
        status: 'online',
        department: 'Ventas',
        totalCalls: 156,
        avgDuration: 245,
        satisfaction: 4.8,
        resolutionRate: 92,
        avgResponseTime: 8
    },
    {
        id: 'agent-2',
        name: 'Carlos López',
        avatar: 'CL',
        status: 'busy',
        department: 'Soporte',
        totalCalls: 203,
        avgDuration: 312,
        satisfaction: 4.5,
        resolutionRate: 88,
        avgResponseTime: 12
    },
    {
        id: 'agent-3',
        name: 'María Rodríguez',
        avatar: 'MR',
        status: 'online',
        department: 'Facturación',
        totalCalls: 178,
        avgDuration: 198,
        satisfaction: 4.9,
        resolutionRate: 95,
        avgResponseTime: 6
    },
    {
        id: 'agent-4',
        name: 'AI Assistant',
        avatar: 'AI',
        status: 'online',
        department: 'AI',
        totalCalls: 1245,
        avgDuration: 156,
        satisfaction: 4.2,
        resolutionRate: 78,
        avgResponseTime: 1
    },
    {
        id: 'agent-5',
        name: 'Pedro Martínez',
        avatar: 'PM',
        status: 'offline',
        department: 'Ventas',
        totalCalls: 134,
        avgDuration: 267,
        satisfaction: 4.6,
        resolutionRate: 85,
        avgResponseTime: 10
    }
];

// ===========================================
// EMOTIONS
// ===========================================
export const EMOTIONS = {
    happy: { label: 'Feliz', color: '#10b981', icon: null },
    neutral: { label: 'Neutral', color: '#6b7280', icon: null },
    frustrated: { label: 'Frustrado', color: '#f59e0b', icon: null },
    angry: { label: 'Enojado', color: '#ef4444', icon: null },
    sad: { label: 'Triste', color: '#8b5cf6', icon: null },
    satisfied: { label: 'Satisfecho', color: '#06b6d4', icon: null }
};

// ===========================================
// CALLS
// ===========================================
export const MOCK_CALLS = [
    {
        id: 'call-001',
        caller: { name: 'Juan Pérez', phone: '+57 300 123 4567', email: 'juan@email.com' },
        agentId: 'agent-4',
        type: 'inbound',
        status: 'completed',
        duration: 245,
        startTime: '2026-01-19T10:30:00',
        endTime: '2026-01-19T10:34:05',
        category: 'Consulta General',
        resolution: 'resolved',
        satisfaction: 5,
        emotions: {
            timeline: [
                { time: 0, emotion: 'neutral', confidence: 0.85 },
                { time: 60, emotion: 'frustrated', confidence: 0.72 },
                { time: 120, emotion: 'neutral', confidence: 0.80 },
                { time: 180, emotion: 'happy', confidence: 0.88 },
                { time: 245, emotion: 'satisfied', confidence: 0.92 }
            ],
            summary: { happy: 35, neutral: 40, frustrated: 20, angry: 0, sad: 5 }
        },
        transcript: [
            { role: 'agent', text: 'Buenos días, gracias por llamar. ¿En qué puedo ayudarle?', time: 0 },
            { role: 'user', text: 'Hola, tengo un problema con mi factura del mes pasado.', time: 8 },
            { role: 'agent', text: 'Entiendo, permítame verificar su cuenta. ¿Me puede proporcionar su número de cédula?', time: 15 },
            { role: 'user', text: '1234567890', time: 25 },
            { role: 'agent', text: 'Perfecto. Veo que hay un cargo adicional. Fue por un servicio especial que solicitó.', time: 60 },
            { role: 'user', text: 'Ah, no recuerdo haber solicitado eso...', time: 75 },
            { role: 'agent', text: 'Lo verifico... Efectivamente, fue una activación automática. Puedo cancelarlo y hacer un ajuste.', time: 120 },
            { role: 'user', text: '¡Excelente! Eso me ayudaría mucho.', time: 180 },
            { role: 'agent', text: 'Listo, el ajuste se verá reflejado en su próxima factura. ¿Hay algo más?', time: 220 },
            { role: 'user', text: 'No, muchas gracias. Excelente atención.', time: 235 }
        ],
        metrics: {
            wordsPerMinute: 145,
            silencePercentage: 12,
            interruptionCount: 1,
            sentimentScore: 0.78
        }
    },
    {
        id: 'call-002',
        caller: { name: 'María Santos', phone: '+57 310 987 6543', email: 'maria@email.com' },
        agentId: 'agent-1',
        type: 'inbound',
        status: 'completed',
        duration: 423,
        startTime: '2026-01-19T11:15:00',
        endTime: '2026-01-19T11:22:03',
        category: 'Reclamo',
        resolution: 'escalated',
        satisfaction: 3,
        emotions: {
            timeline: [
                { time: 0, emotion: 'frustrated', confidence: 0.78 },
                { time: 100, emotion: 'angry', confidence: 0.85 },
                { time: 200, emotion: 'angry', confidence: 0.80 },
                { time: 300, emotion: 'frustrated', confidence: 0.75 },
                { time: 423, emotion: 'neutral', confidence: 0.70 }
            ],
            summary: { happy: 5, neutral: 20, frustrated: 45, angry: 30, sad: 0 }
        },
        transcript: [
            { role: 'agent', text: 'Buenos días, ¿en qué puedo servirle?', time: 0 },
            { role: 'user', text: 'Llevo una semana esperando que me solucionen el problema del internet!', time: 5 },
            { role: 'agent', text: 'Lamento mucho los inconvenientes. Déjeme revisar su caso...', time: 15 }
        ],
        metrics: {
            wordsPerMinute: 178,
            silencePercentage: 8,
            interruptionCount: 5,
            sentimentScore: -0.45
        }
    },
    {
        id: 'call-003',
        caller: { name: 'Roberto Díaz', phone: '+57 320 456 7890', email: 'roberto@email.com' },
        agentId: 'agent-4',
        type: 'outbound',
        status: 'completed',
        duration: 312,
        startTime: '2026-01-19T09:00:00',
        endTime: '2026-01-19T09:05:12',
        category: 'Ventas',
        resolution: 'resolved',
        satisfaction: 4,
        emotions: {
            timeline: [
                { time: 0, emotion: 'neutral', confidence: 0.82 },
                { time: 100, emotion: 'neutral', confidence: 0.78 },
                { time: 200, emotion: 'happy', confidence: 0.85 },
                { time: 312, emotion: 'satisfied', confidence: 0.88 }
            ],
            summary: { happy: 40, neutral: 50, frustrated: 5, angry: 0, sad: 5 }
        },
        transcript: [],
        metrics: {
            wordsPerMinute: 132,
            silencePercentage: 15,
            interruptionCount: 0,
            sentimentScore: 0.62
        }
    },
    {
        id: 'call-004',
        caller: { name: 'Laura Gómez', phone: '+57 315 111 2222', email: 'laura@email.com' },
        agentId: 'agent-3',
        type: 'inbound',
        status: 'in-progress',
        duration: 156,
        startTime: '2026-01-19T14:30:00',
        category: 'Facturación',
        emotions: {
            timeline: [
                { time: 0, emotion: 'neutral', confidence: 0.80 }
            ],
            summary: { happy: 20, neutral: 70, frustrated: 10, angry: 0, sad: 0 }
        },
        transcript: [],
        metrics: {}
    },
    {
        id: 'call-005',
        caller: { name: 'Andrés Vargas', phone: '+57 318 333 4444', email: 'andres@email.com' },
        agentId: 'agent-2',
        type: 'inbound',
        status: 'completed',
        duration: 567,
        startTime: '2026-01-19T08:45:00',
        endTime: '2026-01-19T08:54:27',
        category: 'Soporte Técnico',
        resolution: 'resolved',
        satisfaction: 5,
        emotions: {
            timeline: [
                { time: 0, emotion: 'frustrated', confidence: 0.75 },
                { time: 150, emotion: 'neutral', confidence: 0.80 },
                { time: 300, emotion: 'neutral', confidence: 0.82 },
                { time: 450, emotion: 'happy', confidence: 0.88 },
                { time: 567, emotion: 'satisfied', confidence: 0.92 }
            ],
            summary: { happy: 30, neutral: 45, frustrated: 20, angry: 0, sad: 5 }
        },
        transcript: [],
        metrics: {
            wordsPerMinute: 156,
            silencePercentage: 10,
            interruptionCount: 2,
            sentimentScore: 0.55
        }
    }
];

// Generate more calls
for (let i = 6; i <= 50; i++) {
    const emotions = Object.keys(EMOTIONS);
    const randomEmotion = emotions[Math.floor(Math.random() * emotions.length)];
    const randomAgent = MOCK_AGENTS[Math.floor(Math.random() * MOCK_AGENTS.length)];
    const duration = Math.floor(Math.random() * 600) + 60;

    MOCK_CALLS.push({
        id: `call-${String(i).padStart(3, '0')}`,
        caller: {
            name: `Cliente ${i}`,
            phone: `+57 3${Math.floor(Math.random() * 100000000).toString().padStart(8, '0')}`,
            email: `cliente${i}@email.com`
        },
        agentId: randomAgent.id,
        type: Math.random() > 0.7 ? 'outbound' : 'inbound',
        status: 'completed',
        duration,
        startTime: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
        category: ['Ventas', 'Soporte', 'Facturación', 'Reclamo', 'Consulta'][Math.floor(Math.random() * 5)],
        resolution: Math.random() > 0.3 ? 'resolved' : 'escalated',
        satisfaction: Math.floor(Math.random() * 3) + 3,
        emotions: {
            timeline: [],
            summary: {
                happy: Math.floor(Math.random() * 40),
                neutral: Math.floor(Math.random() * 50),
                frustrated: Math.floor(Math.random() * 30),
                angry: Math.floor(Math.random() * 15),
                sad: Math.floor(Math.random() * 10)
            }
        },
        metrics: {
            wordsPerMinute: Math.floor(Math.random() * 50) + 120,
            silencePercentage: Math.floor(Math.random() * 20),
            interruptionCount: Math.floor(Math.random() * 5),
            sentimentScore: (Math.random() * 2 - 1).toFixed(2)
        }
    });
}

// ===========================================
// DASHBOARD METRICS
// ===========================================
export const MOCK_METRICS = {
    today: {
        totalCalls: 156,
        avgDuration: 234,
        satisfaction: 4.6,
        resolutionRate: 89,
        aiHandled: 67,
        humanRequired: 33
    },
    trends: {
        calls: [
            { date: '2026-01-13', value: 120 },
            { date: '2026-01-14', value: 145 },
            { date: '2026-01-15', value: 132 },
            { date: '2026-01-16', value: 178 },
            { date: '2026-01-17', value: 165 },
            { date: '2026-01-18', value: 189 },
            { date: '2026-01-19', value: 156 }
        ],
        satisfaction: [
            { date: '2026-01-13', value: 4.5 },
            { date: '2026-01-14', value: 4.6 },
            { date: '2026-01-15', value: 4.4 },
            { date: '2026-01-16', value: 4.7 },
            { date: '2026-01-17', value: 4.6 },
            { date: '2026-01-18', value: 4.8 },
            { date: '2026-01-19', value: 4.6 }
        ],
        emotions: [
            { date: '2026-01-13', happy: 35, neutral: 45, frustrated: 15, angry: 5 },
            { date: '2026-01-14', happy: 40, neutral: 42, frustrated: 12, angry: 6 },
            { date: '2026-01-15', happy: 32, neutral: 48, frustrated: 14, angry: 6 },
            { date: '2026-01-16', happy: 45, neutral: 40, frustrated: 10, angry: 5 },
            { date: '2026-01-17', happy: 42, neutral: 43, frustrated: 11, angry: 4 },
            { date: '2026-01-18', happy: 48, neutral: 38, frustrated: 10, angry: 4 },
            { date: '2026-01-19', happy: 44, neutral: 41, frustrated: 11, angry: 4 }
        ]
    },
    byCategory: [
        { name: 'Consulta', count: 45, percentage: 29 },
        { name: 'Soporte', count: 38, percentage: 24 },
        { name: 'Facturación', count: 32, percentage: 21 },
        { name: 'Ventas', count: 25, percentage: 16 },
        { name: 'Reclamo', count: 16, percentage: 10 }
    ],
    byHour: [
        { hour: '08:00', calls: 12 },
        { hour: '09:00', calls: 28 },
        { hour: '10:00', calls: 35 },
        { hour: '11:00', calls: 42 },
        { hour: '12:00', calls: 25 },
        { hour: '13:00', calls: 18 },
        { hour: '14:00', calls: 32 },
        { hour: '15:00', calls: 38 },
        { hour: '16:00', calls: 45 },
        { hour: '17:00', calls: 30 }
    ],
    emotionDistribution: {
        happy: 38,
        neutral: 42,
        frustrated: 14,
        angry: 4,
        sad: 2
    },
    // ===========================================
    // SENTIMENT ANALYSIS METRICS
    // ===========================================
    sentiment: {
        // Net Promoter Score (-100 to 100)
        nps: {
            score: 42,
            promoters: 58,  // 9-10 rating
            passives: 26,   // 7-8 rating  
            detractors: 16, // 0-6 rating
            trend: [
                { date: '2026-01-13', value: 38 },
                { date: '2026-01-14', value: 40 },
                { date: '2026-01-15', value: 35 },
                { date: '2026-01-16', value: 45 },
                { date: '2026-01-17', value: 43 },
                { date: '2026-01-18', value: 48 },
                { date: '2026-01-19', value: 42 }
            ]
        },
        // Customer Satisfaction Score (1-5)
        csat: {
            score: 4.6,
            distribution: [
                { rating: 5, count: 89, percentage: 57 },
                { rating: 4, count: 42, percentage: 27 },
                { rating: 3, count: 15, percentage: 10 },
                { rating: 2, count: 6, percentage: 4 },
                { rating: 1, count: 4, percentage: 2 }
            ],
            trend: [
                { date: '2026-01-13', value: 4.5 },
                { date: '2026-01-14', value: 4.6 },
                { date: '2026-01-15', value: 4.4 },
                { date: '2026-01-16', value: 4.7 },
                { date: '2026-01-17', value: 4.6 },
                { date: '2026-01-18', value: 4.8 },
                { date: '2026-01-19', value: 4.6 }
            ]
        },
        // Customer Effort Score (1-7, lower is better)
        ces: {
            score: 2.3,
            effortLevels: [
                { level: 'Muy Facil', count: 67, percentage: 43 },
                { level: 'Facil', count: 52, percentage: 33 },
                { level: 'Neutral', count: 22, percentage: 14 },
                { level: 'Dificil', count: 12, percentage: 8 },
                { level: 'Muy Dificil', count: 3, percentage: 2 }
            ]
        },
        // Positive-to-Negative ratio
        pta: {
            ratio: 3.8,
            positive: 76,
            negative: 20,
            neutral: 4
        },
        // Emotion Intensity Score (0-100)
        emotionIntensity: {
            average: 62,
            byEmotion: {
                happy: { intensity: 78, frequency: 38 },
                neutral: { intensity: 45, frequency: 42 },
                frustrated: { intensity: 72, frequency: 14 },
                angry: { intensity: 85, frequency: 4 },
                sad: { intensity: 58, frequency: 2 }
            }
        },
        // Sentiment Rubrics
        rubrics: {
            vocal: {
                tone: 72,       // Voice tone positivity (0-100)
                pace: 65,       // Speaking pace appropriateness (0-100)
                clarity: 88,    // Voice clarity (0-100)
                energy: 70      // Energy level (0-100)
            },
            linguistic: {
                politeness: 85,     // Polite language usage (0-100)
                empathy: 78,        // Empathetic expressions (0-100)
                professionalism: 92,// Professional vocabulary (0-100)
                resolution: 80      // Solution-oriented language (0-100)
            },
            behavioral: {
                patience: 75,       // Patience indicators (0-100)
                engagement: 82,     // Active engagement (0-100)
                frustrationTolerance: 68,  // Handling difficult moments (0-100)
                rapport: 77         // Building rapport (0-100)
            }
        },
        // First Call Resolution impact on sentiment
        fcrImpact: {
            resolved: { avgSentiment: 0.78, count: 139 },
            escalated: { avgSentiment: -0.23, count: 17 }
        }
    }
};

// ===========================================
// HELPER FUNCTIONS
// ===========================================
export const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${String(secs).padStart(2, '0')}`;
};

export const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit'
    });
};

export const getAgentById = (id) => MOCK_AGENTS.find(a => a.id === id);

export const authenticateUser = (email, password) => {
    const user = MOCK_USERS.find(u => u.email === email && u.password === password);
    return user ? { ...user, password: undefined } : null;
};
