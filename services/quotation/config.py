# Configuración y Textos para la Cotización

COMPANY_NAME = "PolitechAI"
CONTACT_EMAIL = "contacto@politech.ai"
CONTACT_PHONE = "+57 300 123 4567"

# Configuración de Precios
PRICE_PER_AGENT = 3000000  # COP Mensual
CURRENCY_FMT = "$ {:,.0f} COP"

# Precios Adicionales
PRICE_SETUP_ONPREMISE = "$ 1.000.000 COP"
PRICE_HW_RENTAL = "$ 1.500.000 COP / mes"
PRICE_SENTIMENT = "$ 150.000 COP / mes"
PRICE_CLONING = "$ 400.000 COP / mes"
PRICE_SUPERVISOR = "$ 50.000 COP / mes"

# Estructura: CAPÍTULOS -> SECCIONES
# Cada Capítulo inicia en nueva página. Las secciones dentro van seguidas.

CHAPTERS = [
    {
        "title": "ANEXO A: ACUERDO DE NIVEL DE SERVICIO (SLA) Y CONDICIONES DE SOPORTE",
        "sections": [
            {
                "subtitle": "1. Alcance del Soporte Técnico",
                "content": [
                    {"type": "text", "value": """El servicio de mantenimiento mensual asociado a Nuestro Modelo incluye:"""},
                    {"type": "list", "items": [
                        "Monitoreo proactivo de la disponibilidad de la API (Uptime garantizado del 99.5%).",
                        "Actualizaciones de seguridad del contenedor Docker y dependencias de Python.",
                        "Re-entrenamientos menores trimestrales (ajuste de pronunciación de hasta 50 palabras nuevas).",
                        "Soporte de \"Mesa de Ayuda\" en horario hábil (Lunes a Viernes, 8:00 AM - 6:00 PM, hora Colombia)."
                    ]}
                ]
            },
            {
                "subtitle": "2. Exclusiones de Garantía y Suspensión del Servicio",
                "content": [
                    {"type": "text", "value": """Para garantizar la calidad y eficiencia de nuestro equipo de ingeniería, se establecen las siguientes condiciones estrictas para la prestación del soporte:"""},
                    {"type": "list", "items": [
                        "<b>Conducta y Trato Respetuoso:</b> Nos reservamos el derecho de suspender la asistencia técnica o finalizar la llamada de soporte inmediatamente si el interlocutor o personal del Cliente utiliza lenguaje ofensivo, agresivo, discriminatorio o irrespetuoso hacia nuestro equipo. La reincidencia en este comportamiento podrá ser causal de terminación anticipada del contrato de mantenimiento.",
                        "<b>Adherencia a Flujos Estándar:</b> El soporte técnico cubre exclusivamente el funcionamiento de Nuestro Modelo bajo los flujos de conversación y parámetros técnicos definidos en la fase de diseño. No se aceptarán reclamos ni se brindará soporte por errores derivados de:",
                    ]},
                    {"type": "list", "items": [
                        "Intentos de utilizar el modelo en flujos conversacionales no validados o \"casos borde\" extremos no contemplados en el alcance inicial.",
                        "Manipulación no autorizada del código fuente, los pesos del modelo o la infraestructura del contenedor.",
                        "Integraciones con sistemas de terceros que no fueron certificados durante la entrega."
                    ]}
                ]
            },
            {
                "subtitle": "3. Tiempos de Respuesta y Resolución",
                "content": [
                    {"type": "text", "value": """Los incidentes reportados bajo un uso correcto del sistema se clasificarán de la siguiente manera:"""},
                    {"type": "table", "headers": ["Severidad", "Descripción", "Respuesta", "Resolución"],
                     "colWidths": [1.0, 3.0, 1.0, 1.0],
                     "data": [
                        ["Crítica", "Sistema caído. API no responde o errores 500.", "< 2 Hrs", "< 8 Hrs"],
                        ["Alta", "Funciona con errores graves (voz distorsionada).", "< 4 Hrs", "< 24 Hrs"],
                        ["Media", "Consultas, cambios de parámetros, reportes.", "< 1 Día", "< 3 Días"]
                     ]}
                ]
            }
        ]
    },
    {
        "title": "ANEXO B: MARCO LEGAL Y HABEAS DATA (COLOMBIA)",
        "sections": [
            {
                "subtitle": "1. Cumplimiento Normativo (Ley 1581 de 2012)",
                "content": [
                    {"type": "text", "value": """El desarrollo de la "Identidad Vocal Digital" mediante Nuestro Modelo implica el tratamiento de datos biométricos sensibles (la voz)."""},
                    {"type": "list", "items": [
                        "<b>Encargado del Tratamiento:</b> Actuaremos en calidad de Encargado, limitándonos a procesar los datos exclusivamente para el entrenamiento y fine-tuning del modelo de IA, bajo las instrucciones estrictas del Cliente (Responsable).",
                        "<b>Seguridad de la Información:</b> Los datos de voz y los \"checkpoints\" (archivos de pesos) de Nuestro Modelo se almacenarán en infraestructura cifrada. Garantizamos que estos activos no serán utilizados para entrenar modelos de terceros, ni compartidos externamente, ni utilizados para fines distintos a los contratados."
                    ]}
                ]
            },
            {
                "subtitle": "2. Declaración de Consentimiento Informado",
                "content": [
                    {"type": "text", "value": """El Cliente deberá recabar la siguiente autorización del titular de la voz antes del inicio del proyecto:"""},
                    {"type": "text", "value": """<i>"Yo, [Nombre del Locutor/Titular], identificado con C.C. [Número], autorizo de manera expresa, libre e informada a [Nombre del Cliente] para utilizar mis registros de voz con el fin único de entrenar sistemas de Inteligencia Artificial Generativa (Clonación de Voz). Entiendo que esta autorización permite la generación de audio sintético que imita mi timbre y prosodia para uso corporativo.</i>"""},
                    {"type": "text", "value": """<i>Renuncia de Derechos: El Cliente garantiza que el uso de mi voz sintética se limitará a los fines corporativos estipulados y no se utilizará para fines ilícitos, suplantación de identidad fraudulenta o contenido difamatorio."</i>"""}
                ]
            },
            {
                "subtitle": "3. Marca de Agua (Watermarking)",
                "content": [
                    {"type": "text", "value": """Para proteger la reputación corporativa del Cliente y cumplir con estándares éticos, todo audio generado por Nuestro Modelo incluirá una firma espectral inaudible (Watermark). Esto permite identificar técnicamente el audio como "Generado por IA", ofreciendo trazabilidad y seguridad ante el uso indebido."""}
                ]
            }
        ]
    },
    {
        "title": "ANEXO C: ANÁLISIS DE RETORNO DE INVERSIÓN (ROI)",
        "sections": [
            {
                "subtitle": "Comparativa de Costos: Nuestro Modelo vs. APIs Internacionales",
                "content": [
                    {"type": "text", "value": """El siguiente análisis proyecta el ahorro operativo al implementar Nuestro Modelo (On-Premise/Local) frente al alquiler de voces en la nube, basado en un volumen estándar de operación de 2 millones de caracteres mensuales."""},
                    {"type": "table", "headers": ["Concepto", "API Internacional (SaaS)", "Nuestro Modelo (Propio)"],
                     "colWidths": [1.2, 2.4, 2.4],
                     "data": [
                        ["Modelo de Cobro", "Pago perpetuo por uso (Créditos)", "Inversión Inicial + Mantenimiento Fijo"],
                        ["Costo Operativo", "~USD $200-300 / millón chars. Alto y variable.", "$0 COP marginal. Bajo y predecible."],
                        ["Privacidad", "Datos viajan a servidores externos", "Total. Datos residen en su infraestructura"],
                        ["Propiedad", "Alquiler (Vendor Lock-in)", "Propiedad (Activo del Cliente)"]
                     ]},
                    {"type": "text", "value": """<b>Conclusión Financiera:</b> Aunque la implementación inicial requiere una inversión (CAPEX), Nuestro Modelo elimina el costo por minuto/carácter. Para flujos de alto volumen, el retorno de inversión se alcanza en los primeros meses de operación, generando un ahorro sostenido superior al 80% anual frente a soluciones de API extranjeras."""}
                ]
            }
        ]
    },
    {
        "title": "1. VALORACIÓN OPERATIVA DEL AGENTE IA",
        "sections": [
            {
                "subtitle": "Tarifa Plana de Disponibilidad Total",
                "content": [
                    {"type": "text", "value": """A diferencia de la contratación tradicional, nuestro modelo simplifica la estructura de costos operativos mediante una Tarifa Plana de Disponibilidad Total."""},
                    {"type": "list", "items": [
                        "<b>Canon Mensual por Agente IA:</b> $3.000.000 COP.",
                        "Incluye: Licencia operativa del agente, asignación de espacio en el Dashboard de AI Call Center, y consumo ilimitado de procesamiento en la infraestructura asignada."
                    ]},
                    {"type": "text", "value": """<b>Beneficios de Costo-Eficiencia (La ventaja del "Cero Overtime"):</b><br/>Al contratar un Agente IA bajo este modelo, su empresa obtiene una capacidad productiva imposible de replicar con personal humano por el mismo costo:"""},
                    {"type": "list", "items": [
                        "<b>Disponibilidad 24/7/365:</b> El agente responde llamadas a las 3:00 AM, domingos o festivos sin variaciones en el costo.",
                        "<b>Cero Recargos Laborales:</b> No existen horas extras, recargos nocturnos, dominicales ni costos de seguridad social. El valor de $3M es final, independientemente de si el flujo de llamadas se triplica durante una temporada alta.",
                        "<b>Escalabilidad Elástica:</b> Si su operación requiere 5 agentes más para un evento específico, se activan de inmediato sin procesos de selección o curvas de aprendizaje."
                    ]}
                ]
            }
        ]
    },
    {
        "title": "2. PLATAFORMA INTEGRAL \"AI CALL CENTER\" Y LÓGICA DE NEGOCIO",
        "sections": [
            {
                "subtitle": "Lógica de Negocio Pre-Entrenada",
                "content": [
                    {"type": "text", "value": """A diferencia de soluciones genéricas que entregan una "caja vacía", nuestra propuesta incluye la Lógica de Negocio Pre-Entrenada. El sistema se entrega instruido con los flujos conversacionales, manejo de objeciones y terminología específica de su sector, sin costos ocultos de configuración lógica inicial."""},
                    {"type": "text", "value": """<b>El Entorno de Trabajo (Workspace):</b><br/>Se habilita el acceso a nuestra plataforma propietaria AI Call Center (ver Referencia Visual 1), un entorno centralizado donde conviven la operación automática y la supervisión humana."""},
                    {"type": "list", "items": [
                        "<b>Dashboard en Tiempo Real:</b> Visualización de métricas críticas (Tasa de Resolución, Satisfacción del Cliente, Llamadas por Categoría).",
                        "<b>Gestión Híbrida:</b> Módulo para escalamiento fluido de IA a Agente Humano cuando sea necesario (Human-in-the-loop)."
                    ]}
                ]
            }
        ]
    },
    {
        "title": "3. ESQUEMA DE COSTOS RECURRENTES Y ADICIONALES",
        "sections": [
            {
                "subtitle": "A. Cuentas y Accesos",
                "content": [
                    {"type": "list", "items": [
                        "<b>Cuenta Administrativa (Supervisor):</b> $50.000 COP / mes.",
                        "Permite acceso total a métricas, configuración de campañas, auditoría de grabaciones y gestión de usuarios."
                    ]}
                ]
            },
            {
                "subtitle": "B. Módulo de Identidad Vocal",
                "content": [
                    {"type": "list", "items": [
                        "<b>Opción Estándar (Incluida):</b> Voz neuronal de alta calidad (Stock) predeterminada por la plataforma. Sin costo adicional.",
                        "<b>Opción Clonación de Voz Personalizada (Premium):</b> $400.000 COP / mes por voz.",
                        "Incluye el alojamiento dedicado del modelo de voz clonada (su CEO o Talento de marca) y su mantenimiento para asegurar latencia mínima.",
                        "<i>Nota: La grabación y entrenamiento inicial se cobran en la fase de Setup (ver Anexo D).</i>"
                    ]}
                ]
            },
            {
                "subtitle": "C. Módulo de Inteligencia Emocional (Sentiment Analysis)",
                "content": [
                    {"type": "list", "items": [
                        "<b>Licencia de Análisis de Sentimientos:</b> $150.000 COP / mes por agente activo.",
                        "Habilita el panel de \"Emociones\" en el Dashboard, permitiendo calificar cada interacción (Positiva, Neutra, Negativa) y detectando alertas de clientes insatisfechos en tiempo real."
                    ]}
                ]
            }
        ]
    },
    {
        "title": "4. MODALIDADES DE INFRAESTRUCTURA Y HARDWARE",
        "sections": [
            {
                "subtitle": "OPCIÓN A: Despliegue en Infraestructura del Cliente (On-Premise)",
                "content": [
                    {"type": "text", "value": """El Cliente provee el hardware. Nosotros entregamos el contenedor de software y realizamos la instalación."""},
                    {"type": "list", "items": [
                        "<b>Costo de Estandarización y Despliegue:</b> $1.000.000 COP (Pago Único).",
                        "Cubre la instalación remota, configuración de drivers GPU y virtualización del entorno para asegurar compatibilidad con Nuestro Modelo.",
                        "<b>Requisitos:</b> El Cliente recibirá un \"Anexo Técnico de Hardware\" especificando la GPU (mínimo serie RTX 30/40 o A10G) y RAM requerida.",
                        "<i>Nota: Si el equipo del Cliente requiere formateo, limpieza profunda de S.O. o reparaciones de drivers previos para cumplir los requisitos, se cotizarán horas de soporte adicional.</i>",
                        "<b>Licenciamiento:</b> La instalación otorga una licencia de uso intransferible y ligada a la máquina física (Hardware ID). No se permite la copia o redistribución del contenedor a otras sedes sin una nueva licencia."
                    ]}
                ]
            },
            {
                "subtitle": "OPCIÓN B: Arrendamiento de Hardware (Infrastructure as a Service)",
                "content": [
                    {"type": "text", "value": """Nosotros proveemos el ecosistema de hardware completo, configurado y optimizado para la operación de IA de baja latencia."""},
                    {"type": "list", "items": [
                        "<b>Canon de Arrendamiento:</b> $1.500.000 COP / mes por servidor.",
                        "<b>Capacidad:</b> Un (1) servidor soporta hasta 10 Agentes de IA simultáneos (Inferencia F5-TTS en tiempo real)."
                    ]},
                    {"type": "text", "value": """<b>Kit de Hardware Incluido:</b>"""},
                    {"type": "list", "items": [
                        "<b>Torre de Procesamiento AI:</b> Workstation equipada con GPU NVIDIA (RTX 3090 / 4090 o superior) y refrigeración líquida/aire de alto flujo.",
                        "<b>Consola de Estado (Service Display):</b> Monitor de gestión (formato pequeño 19-22\") para visualización local del estado del servidor, logs de conexión y mantenimiento básico.",
                        "<b>Periféricos de Gestión:</b> Kit básico de teclado/mouse inalámbrico y cableado de red categoría 6."
                    ]},
                    {"type": "text", "value": """<b>Condiciones del Servicio:</b>"""},
                    {"type": "list", "items": [
                        "El equipo se entrega en calidad de préstamo/comodato.",
                        "Cualquier daño físico, pérdida, hurto o cambio de configuración no autorizado (BIOS/Overclocking) será facturado al Cliente por su valor comercial de reposición.",
                        "El mantenimiento preventivo del hardware está incluido en el canon mensual."
                    ]}
                ]
            }
        ]
    },
    {
        "title": "5. INTEGRACIÓN DE DATOS Y API (EXONERACIÓN DE RESPONSABILIDAD)",
        "sections": [
            {
                "subtitle": "Cláusula de Seguridad de Datos Externos",
                "content": [
                    {"type": "text", "value": """El sistema permite la extracción de data mediante nuestra API para alimentar CRMs o bases de datos externas del Cliente."""},
                    {"type": "text", "value": """Si el Cliente opta por extraer la información (transcripciones, audios o metadatos) fuera del ecosistema seguro de Nuestro Modelo mediante API o exportación manual:"""},
                    {"type": "list", "items": [
                        "1. Nuestro Modelo y nuestra empresa se eximen de cualquier responsabilidad sobre la seguridad, tratamiento y custodia de dichos datos una vez abandonan nuestra plataforma.",
                        "2. El Cliente asume total responsabilidad ante incidentes de ciberseguridad, fugas de información o incumplimientos de la Ley 1581 de 2012 que ocurran en sus propios sistemas o en integraciones de terceros no auditadas por nosotros."
                    ]}
                ]
            }
        ]
    },
    {
        "title": "6. METODOLOGÍA DE IMPLEMENTACIÓN Y \"ONBOARDING\" LÓGICO",
        "sections": [
            {
                "subtitle": "Fases del Proceso",
                "content": [
                    {"type": "text", "value": """Para garantizar que el Agente IA no solo hable, sino que resuelva como su mejor vendedor, ejecutamos una fase de inmersión estratégica antes del "Go-Live"."""},
                    {"type": "text", "value": """<b>Tiempo Estimado de Implementación:</b> 4 Semanas (1 Mes Calendario)."""},
                    {"type": "list", "items": [
                        "<b>Semana 1: Inmersión y Levantamiento (Kick-off):</b> Reuniones con sus líderes de equipo para entender la \"Lógica del Negocio\". Recolección de manuales, scripts actuales y grabaciones de llamadas reales para clonar el estilo de atención exitoso.",
                        "<b>Semana 2: Diseño de Flujos y \"Casos Borde\":</b> Nuestros ingenieros diagraman el árbol de decisiones. Definición de reglas de negocio: ¿Qué hacer si el cliente está enojado? ¿Qué hacer si pide un descuento no autorizado?",
                        "<b>Semana 3: Entrenamiento y Simulacros:</b> Pruebas de estrés controladas. El equipo del cliente llama al Agente para intentar \"corcharlo\" o hacerlo fallar, permitiéndonos ajustar las respuestas y la latencia.",
                        "<b>Semana 4: Despliegue y Ajuste Fino:</b> Activación en producción (Go-Live). Durante esta semana, monitoreamos cada llamada para realizar micro-ajustes en la pronunciación o la velocidad de respuesta."
                    ]},
                    {"type": "text", "value": """<i>Nota: Este mes de trabajo de ingeniería y consultoría está incluido en la tarifa de inicio (Setup), asegurando que el Agente se entregue "llave en mano", listo para operar con la identidad de su empresa.</i>"""}
                ]
            }
        ]
    },
    {
        "title": "ANEXO D: METODOLOGÍA DE CALIDAD Y DATOS",
        "sections": [
            {
                "subtitle": "Estándar de Grabación y Cobertura Fonética",
                "content": [
                    {"type": "text", "value": """A diferencia de soluciones genéricas, Nuestro Modelo se entrena utilizando el protocolo Sharvard Corpus adaptado al español. Esta metodología científica asegura la robustez del sistema frente a cualquier texto."""},
                    {"type": "text", "value": """<b>Tabla Comparativa de Calidad:</b>"""},
                    {"type": "table", "headers": ["Variable", "Grabación Estándar", "Nuestro Modelo"],
                     "colWidths": [1.2, 2.4, 2.4],
                     "data": [
                        ["Cobertura", "~85% (Faltan combinaciones fonéticas)", "100% (Guion fonéticamente balanceado)"],
                        ["Estabilidad", "Errores o ruidos en frases largas", "Voz estable y fluida en textos extensos"],
                        ["Prosodia", "Tono monótono o impredecible", "Ajustable según identidad de marca"],
                        ["Resultado", "Voz Robótica Genérica", "Identidad Vocal de Alta Fidelidad"]
                     ]}
                ]
            }
        ]
    },
    {
        "title": "ANEXO LEGAL E: DERECHOS DE IMAGEN Y VOZ",
        "sections": [
            {
                "subtitle": "Responsabilidad sobre el Talento de Voz",
                "content": [
                    {"type": "text", "value": """Para la activación del servicio de "Clonación de Voz Personalizada", nuestra empresa parte de la buena fe respecto a la titularidad de los derechos."""},
                    {"type": "list", "items": [
                        "<b>Declaración del Cliente:</b> Al entregar los audios para el entrenamiento, el Cliente declara y garantiza que ha gestionado, firmado y asegurado todos los derechos legales, laborales y de propiedad intelectual con la persona física (Talento/Locutor) cuya voz será clonada.",
                        "<b>Indemnidad:</b> El Cliente mantendrá indemne a nuestra empresa frente a cualquier reclamación, demanda o litigio presentado por el titular de la voz relacionado con el uso no autorizado, compensación económica o derechos de imagen. Nosotros actuamos meramente como procesadores técnicos de los archivos suministrados."
                    ]}
                ]
            }
        ]
    }
]

LEGAL_DISCLAIMER = """
NOTA IMPORTANTE Y DESCARGO DE RESPONSABILIDAD:
Esta propuesta comercial es de carácter preliminar e informativo. Los precios, términos y condiciones aquí descritos están sujetos a confirmación mediante contrato formal. Validez de la cotización: 15 días calendario a partir de la fecha de emisión. Esta propuesta no constituye un contrato vinculante ni genera obligaciones para las partes hasta la firma del acuerdo definitivo.
"""

CONFIDENTIALITY_NOTICE = """
CONFIDENCIALIDAD:
La información contenida en este documento es propiedad exclusiva de PolitechAI y está destinada únicamente para uso del destinatario. Queda estrictamente prohibida su reproducción, distribución o divulgación a terceros sin autorización previa y por escrito. El incumplimiento de esta cláusula podrá dar lugar a las acciones legales correspondientes.
"""
