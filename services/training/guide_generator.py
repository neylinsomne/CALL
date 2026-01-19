"""
Corpus Guide Generator
Generates recording guides for voice training based on corpus research
"""

from typing import List, Dict, Optional
from sharvard_corpus import (
    PHONETIC_PANGRAMS, 
    SHARVARD_LISTS, 
    MINIMAL_PAIRS,
    CHALLENGING_SEQUENCES,
    EMOTIONAL_SENTENCES,
    get_all_training_sentences,
    get_call_center_corpus
)


# ===========================================
# PREDEFINED VOCABULARY LISTS
# ===========================================

# Technology & Social Media
TECH_VOCABULARY = [
    "Facebook", "Instagram", "WhatsApp", "Twitter", "TikTok", "YouTube",
    "LinkedIn", "Google", "Microsoft", "Apple", "Amazon", "Netflix",
    "Spotify", "Uber", "WiFi", "Bluetooth", "email", "software", "hardware",
    "internet", "streaming", "smartphone", "laptop", "tablet", "desktop",
    "app", "aplicación", "cuenta", "usuario", "contraseña", "perfil",
    "publicación", "post", "comentario", "like", "seguidor", "mensajes",
    "notificación", "actualización", "descarga", "subir", "compartir",
    "enlace", "link", "hashtag", "viral", "trending", "influencer"
]

# Banking & Finance
FINANCE_VOCABULARY = [
    "cuenta corriente", "cuenta de ahorros", "tarjeta de crédito",
    "tarjeta de débito", "transferencia", "transacción", "saldo",
    "estado de cuenta", "extracto", "pago", "factura", "cuota",
    "intereses", "comisión", "retiro", "depósito", "cajero automático",
    "banca en línea", "clave dinámica", "token", "autenticación",
    "fraude", "bloqueo", "desbloqueo", "límite de crédito"
]

# Customer Service
CUSTOMER_SERVICE_VOCABULARY = [
    "atención al cliente", "servicio técnico", "soporte",
    "reclamación", "queja", "solicitud", "trámite", "gestión",
    "seguimiento", "número de caso", "ticket", "referencia",
    "tiempo de espera", "agente", "supervisor", "escalamiento",
    "resolución", "compensación", "reembolso", "garantía"
]

# Telecommunications
TELECOM_VOCABULARY = [
    "plan de datos", "gigas", "minutos", "mensajes", "roaming",
    "cobertura", "señal", "antena", "torre", "red móvil",
    "fibra óptica", "banda ancha", "velocidad", "megas",
    "instalación", "técnico", "módem", "router", "SIM card",
    "portabilidad", "prepago", "pospago", "facturación"
]


# ===========================================
# GUIDE TEMPLATES
# ===========================================

GUIDE_TEMPLATES = {
    "call_center_basico": {
        "name": "Call Center Básico",
        "description": "Frases esenciales para un agente de call center",
        "items": [
            # Saludos
            "Buenos días, gracias por llamar",
            "Buenas tardes, bienvenido a",
            "Buenas noches, ¿en qué puedo ayudarle?",
            
            # Identificación
            "¿Me puede proporcionar su número de cédula?",
            "¿Cuál es su número de cuenta?",
            "¿Puede confirmar su nombre completo?",
            "¿Cuál es su correo electrónico registrado?",
            
            # Pausa y espera
            "Un momento por favor mientras verifico",
            "Permítame consultar esa información",
            "Gracias por esperar",
            "Disculpe la demora",
            
            # Confirmación
            "Perfecto, he registrado su solicitud",
            "Su trámite ha sido procesado exitosamente",
            "En breve recibirá la confirmación",
            
            # Transferencia
            "Le voy a transferir con un especialista",
            "Lo comunico con el área correspondiente",
            
            # Despedida
            "¿Hay algo más en lo que pueda ayudarle?",
            "Gracias por llamar, que tenga un excelente día",
            "Fue un placer atenderle",
        ]
    },
    
    "numeros_fechas": {
        "name": "Números y Fechas",
        "description": "Práctica de pronunciación de números y fechas",
        "items": [
            "cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve",
            "diez", "once", "doce", "trece", "catorce", "quince",
            "veinte", "treinta", "cuarenta", "cincuenta",
            "cien", "doscientos", "quinientos", "mil",
            "primero de enero", "quince de marzo", "veinticinco de diciembre",
            "dos mil veinticinco", "el año pasado", "el próximo mes",
            "a las tres de la tarde", "a las nueve de la mañana",
        ]
    },
    
    "fonetico_completo": {
        "name": "Cobertura Fonética Completa",
        "description": "Pangramas y oraciones para cobertura fonética total",
        "items": PHONETIC_PANGRAMS + CHALLENGING_SEQUENCES
    },
    
    "tecnologia": {
        "name": "Vocabulario Tecnológico",
        "description": "Términos de tecnología y redes sociales",
        "items": TECH_VOCABULARY
    },
    
    "finanzas": {
        "name": "Vocabulario Financiero",
        "description": "Términos bancarios y financieros",
        "items": FINANCE_VOCABULARY
    },
    
    "telecomunicaciones": {
        "name": "Vocabulario Telecomunicaciones",
        "description": "Términos de telefonía e internet",
        "items": TELECOM_VOCABULARY
    },
    
    "emocional": {
        "name": "Variaciones Emocionales",
        "description": "Frases con diferentes tonos emocionales",
        "items": (
            EMOTIONAL_SENTENCES["neutral"] + 
            EMOTIONAL_SENTENCES["pregunta"] + 
            EMOTIONAL_SENTENCES["enfasis"] + 
            EMOTIONAL_SENTENCES["disculpa"]
        )
    },
}


# ===========================================
# GUIDE GENERATOR FUNCTIONS
# ===========================================

def get_available_templates() -> Dict[str, dict]:
    """Get all available guide templates"""
    return {
        key: {
            "name": val["name"],
            "description": val["description"],
            "item_count": len(val["items"]),
            "estimated_minutes": len(val["items"]) * 5 / 60
        }
        for key, val in GUIDE_TEMPLATES.items()
    }


def generate_guide_from_template(template_key: str) -> Dict:
    """Generate a recording guide from a template"""
    if template_key not in GUIDE_TEMPLATES:
        raise ValueError(f"Template '{template_key}' not found")
    
    template = GUIDE_TEMPLATES[template_key]
    return {
        "name": template["name"],
        "description": template["description"],
        "items": template["items"],
        "estimated_duration_minutes": len(template["items"]) * 5 / 60
    }


def generate_custom_guide(
    name: str,
    words: List[str],
    include_phonetic: bool = True,
    include_call_center: bool = True,
    include_numbers: bool = False
) -> Dict:
    """Generate a custom recording guide"""
    items = list(words)
    
    if include_phonetic:
        items.extend(PHONETIC_PANGRAMS[:2])
    
    if include_call_center:
        items.extend(SHARVARD_LISTS.get("lista_call_center", [])[:10])
    
    if include_numbers:
        items.extend(GUIDE_TEMPLATES["numeros_fechas"]["items"][:15])
    
    return {
        "name": name,
        "description": f"Guía personalizada con {len(items)} elementos",
        "items": items,
        "estimated_duration_minutes": len(items) * 5 / 60
    }


def generate_complete_training_guide() -> Dict:
    """Generate a comprehensive training guide"""
    items = []
    
    # Start with pangrams
    items.extend(PHONETIC_PANGRAMS)
    
    # Add Sharvard lists
    for list_name, sentences in SHARVARD_LISTS.items():
        items.extend(sentences)
    
    # Add challenging sequences
    items.extend(CHALLENGING_SEQUENCES)
    
    # Add minimal pairs
    for category, pairs in MINIMAL_PAIRS.items():
        for word1, word2 in pairs:
            items.append(f"Digo {word1}, luego {word2}.")
    
    # Add emotional variations
    for emotion, sentences in EMOTIONAL_SENTENCES.items():
        items.extend(sentences)
    
    return {
        "name": "Guía de Entrenamiento Completa",
        "description": "Cobertura fonética total para entrenamiento de alta calidad",
        "items": items,
        "estimated_duration_minutes": len(items) * 6 / 60  # 6 seconds avg for sentences
    }


def export_guide_to_text(guide: Dict, output_path: str):
    """Export guide to readable text file"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# {guide['name']}\n")
        f.write(f"# {guide.get('description', '')}\n")
        f.write(f"# Total: {len(guide['items'])} elementos\n")
        f.write(f"# Duración estimada: {guide.get('estimated_duration_minutes', 0):.1f} minutos\n")
        f.write("\n# Instrucciones:\n")
        f.write("# - Lea cada línea de forma natural, como si hablara\n")
        f.write("# - Pause 2-3 segundos entre oraciones\n")
        f.write("# - Mantenga un volumen y distancia constante al micrófono\n")
        f.write("# - Hidratese para evitar ruidos de boca\n\n")
        f.write("=" * 60 + "\n\n")
        
        for i, item in enumerate(guide['items'], 1):
            f.write(f"{i:03d}. {item}\n\n")
    
    print(f"Guía exportada a: {output_path}")


# ===========================================
# CLI
# ===========================================
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Guías de grabación disponibles:")
        print("-" * 40)
        for key, info in get_available_templates().items():
            print(f"  {key}")
            print(f"    {info['name']} - {info['item_count']} items ({info['estimated_minutes']:.0f} min)")
        print()
        print("Uso: python guide_generator.py <template> [output.txt]")
        print("     python guide_generator.py --complete [output.txt]")
        sys.exit(0)
    
    template = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else "guia_grabacion.txt"
    
    if template == "--complete":
        guide = generate_complete_training_guide()
    else:
        guide = generate_guide_from_template(template)
    
    export_guide_to_text(guide, output)
