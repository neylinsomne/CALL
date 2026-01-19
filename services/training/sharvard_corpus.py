"""
Sharvard Corpus & Phonetic Pangrams for Spanish TTS Training
Academic standard phonetically balanced sentences
"""

# ===========================================
# PHONETIC PANGRAMS (Maximum Information Density)
# ===========================================
PHONETIC_PANGRAMS = [
    # Classic standard - covers all letters including ñ, k, w, and z/c distinction
    "El veloz murciélago hindú comía feliz cardillo y kiwi. La cigüeña tocaba el saxofón detrás del palenque de paja.",
    
    # High fricative and velar density (/x/, /k/)
    "Quelonio y fabuloso, el viejo tejón quejica huye del zoo tras exhibir su vergonzosa panza.",
    
    # Nasalization and palatal sounds
    "Benjamín pidió una bebida de kiwi y fresa; Noé, sin vergüenza, la más exquisita champaña del menú.",
    
    # Vibrantes and liquids focus
    "El ferrocarril recorría rápidamente el irregular terreno rural, resonando entre los cerros.",
    
    # Sibilants and affricates
    "Seis chicos suizos zozobraban en sus chalupas, silbando canciones sin cesar.",
    
    # Complex consonant clusters
    "La abstracta construcción del instrumento extraordinario complementaba la estructura.",
    
    # Prosodic variation
    "¿Qué? ¡Jamás! Pero... ¿por qué no? Seguramente, tal vez, quizás será posible.",
]


# ===========================================
# SHARVARD CORPUS (Phonetically Balanced Lists)
# Based on Harvard Sentences adapted for Spanish
# ===========================================
SHARVARD_LISTS = {
    "lista_01": [
        "El barco de vela cruzó el ancho mar.",
        "La sal da sabor a la comida sosa.",
        "El perro corre por el campo verde.",
        "Mi madre cose la ropa de cama.",
        "El sol brilla en el cielo azul.",
        "La luna llena ilumina la noche.",
        "El niño juega con su pelota roja.",
        "La flor perfuma todo el jardín.",
        "El río fluye hacia el gran océano.",
        "La montaña se eleva sobre el valle.",
    ],
    
    "lista_02": [
        "El gato duerme junto a la chimenea.",
        "La lluvia cae sobre los tejados grises.",
        "El viento sopla entre los árboles altos.",
        "La campana suena en la torre vieja.",
        "El tren pasa por el túnel oscuro.",
        "La abeja vuela de flor en flor.",
        "El pescador lanza su red al agua.",
        "La estrella brilla en el firmamento.",
        "El reloj marca las doce en punto.",
        "La puerta se abre hacia el jardín.",
    ],
    
    "lista_03": [
        "El caballo galopa por la pradera.",
        "La guitarra suena en la noche clara.",
        "El pintor mezcla colores en su paleta.",
        "La mariposa descansa sobre la rama.",
        "El cocinero prepara una sopa caliente.",
        "La ventana muestra el paisaje nevado.",
        "El libro cuenta historias de aventuras.",
        "La fuente mana agua cristalina.",
        "El pájaro canta al amanecer temprano.",
        "La lámpara alumbra todo el cuarto.",
    ],
    
    "lista_04": [
        "El médico atiende a sus pacientes.",
        "La escuela abre sus puertas al alba.",
        "El músico toca el violín con pasión.",
        "La carta llegó desde muy lejos.",
        "El sastre corta la tela con cuidado.",
        "La radio transmite noticias del mundo.",
        "El maestro enseña con paciencia infinita.",
        "La cosecha fue abundante este año.",
        "El camino serpentea por las colinas.",
        "La plaza está llena de palomas.",
    ],
    
    "lista_05": [
        "El zapatero arregla los zapatos viejos.",
        "La cigarra canta durante el verano.",
        "El leñador corta la madera seca.",
        "La huerta produce verduras frescas.",
        "El panadero hornea el pan temprano.",
        "La brisa marina refresca la tarde.",
        "El jardinero poda los rosales blancos.",
        "La chimenea calienta toda la casa.",
        "El pastor cuida su rebaño de ovejas.",
        "La nieve cubre las cumbres altas.",
    ],
    
    # Call center specific phrases
    "lista_call_center": [
        "Buenos días, gracias por llamar a nuestro servicio.",
        "¿En qué puedo ayudarle el día de hoy?",
        "Permítame verificar su información en el sistema.",
        "Le voy a transferir con un especialista ahora.",
        "¿Me puede confirmar su número de teléfono, por favor?",
        "Entiendo perfectamente su situación, le vamos a ayudar.",
        "La solución a su problema es muy sencilla.",
        "Le enviaremos la información a su correo electrónico.",
        "¿Hay algo más en lo que pueda asistirle?",
        "Gracias por su llamada, que tenga un excelente día.",
        "Lamentamos mucho los inconvenientes ocasionados.",
        "Su solicitud ha sido registrada correctamente.",
        "El tiempo estimado de espera es de cinco minutos.",
        "Por favor, manténgase en la línea mientras verifico.",
        "Su caso ha sido escalado al departamento correspondiente.",
    ],
    
    # Diphthongs and hiatus focus
    "lista_diptongos": [
        "El cielo se tiñe de violeta al atardecer.",
        "La ciudad hierve con el bullicio diario.",
        "El buey arrastra el arado pesado.",
        "La viuda cuida su huerto con esmero.",
        "El hielo cubre el lago en invierno.",
        "La suave brisa acaricia los trigales.",
        "El fuelle del acordeón resuena fuerte.",
        "La flauta emite notas muy agudas.",
        "El náufrago espera en la isla desierta.",
        "La pieza del museo es muy valiosa.",
    ],
    
    # Numbers and quantities
    "lista_numeros": [
        "Tengo veintitrés años de experiencia laboral.",
        "El edificio tiene cuarenta y cinco pisos.",
        "Necesito ciento veinte unidades para mañana.",
        "Son mil quinientos pesos en total.",
        "Quedan tres mil doscientos kilómetros de viaje.",
        "La temperatura alcanzó treinta y ocho grados.",
        "El vuelo dura aproximadamente cuatro horas.",
        "Hay doscientas cincuenta personas esperando.",
        "El precio bajó un quince por ciento.",
        "Faltan noventa días para fin de año.",
    ],
}


# ===========================================
# MINIMAL PAIRS (Disambiguation Training)
# ===========================================
MINIMAL_PAIRS = {
    # /r/ vs /rr/
    "r_rr": [
        ("pero", "perro"),
        ("caro", "carro"),
        ("cero", "cerro"),
        ("moro", "morro"),
        ("para", "parra"),
    ],
    
    # /b/ vs /v/ (same in Spanish, but spelling variation)
    "b_v": [
        ("baca", "vaca"),
        ("bello", "vello"),
        ("bienes", "vienes"),
    ],
    
    # /s/ vs /z/ (Peninsular distinction)
    "s_z": [
        ("casa", "caza"),
        ("coser", "cocer"),
        ("sumo", "zumo"),
    ],
    
    # /n/ vs /ñ/
    "n_ñ": [
        ("ano", "año"),
        ("mono", "moño"),
        ("cana", "caña"),
    ],
}


# ===========================================
# CHALLENGING SEQUENCES
# ===========================================
CHALLENGING_SEQUENCES = [
    # Consonant clusters
    "La construcción del instrumento requiere abstracción.",
    "El extraordinario espectáculo impresionó al inspector.",
    "La transcripción del manuscrito describe estructuras complejas.",
    
    # Rapid articulation
    "Tres tristes tigres tragaban trigo en un trigal.",
    "El cielo está enladrillado, ¿quién lo desenladrillará?",
    "Pablito clavó un clavito, ¿qué clavito clavó Pablito?",
    
    # Long words
    "La electroencefalografía es extraordinariamente especializada.",
    "El otorrinolaringólogo diagnosticó faringoamigdalitis.",
    "La internacionalización provocó desestabilización económica.",
]


# ===========================================
# EMOTIONAL VARIATIONS
# ===========================================
EMOTIONAL_SENTENCES = {
    "neutral": [
        "El informe está listo para su revisión.",
        "La reunión comienza a las tres de la tarde.",
        "Los documentos se encuentran en la carpeta azul.",
    ],
    "pregunta": [
        "¿Podría indicarme dónde queda la oficina principal?",
        "¿Cuánto tiempo tomará procesar mi solicitud?",
        "¿Es posible reprogramar la cita para mañana?",
    ],
    "enfasis": [
        "Es absolutamente necesario que revise estos datos.",
        "Le aseguro que su problema será resuelto hoy mismo.",
        "Definitivamente contamos con la mejor solución disponible.",
    ],
    "disculpa": [
        "Lamento mucho la demora en atender su llamada.",
        "Pedimos disculpas por cualquier inconveniente causado.",
        "Sentimos no poder ayudarle en esta ocasión.",
    ],
}


# ===========================================
# GENERATION FUNCTIONS
# ===========================================
def get_all_training_sentences() -> list:
    """Get all sentences for comprehensive training"""
    sentences = []
    
    # Add pangrams
    sentences.extend(PHONETIC_PANGRAMS)
    
    # Add all Sharvard lists
    for list_name, list_sentences in SHARVARD_LISTS.items():
        sentences.extend(list_sentences)
    
    # Add minimal pair sentences
    for category, pairs in MINIMAL_PAIRS.items():
        for word1, word2 in pairs:
            sentences.append(f"Digo {word1}, no digo {word2}.")
            sentences.append(f"La palabra es {word2}, con doble erre.")
    
    # Add challenging sequences
    sentences.extend(CHALLENGING_SEQUENCES)
    
    # Add emotional variations
    for emotion, emotion_sentences in EMOTIONAL_SENTENCES.items():
        sentences.extend(emotion_sentences)
    
    return sentences


def get_minimal_corpus() -> list:
    """Get minimum required sentences for basic training (50 sentences)"""
    sentences = []
    sentences.extend(PHONETIC_PANGRAMS[:3])
    sentences.extend(SHARVARD_LISTS["lista_01"])
    sentences.extend(SHARVARD_LISTS["lista_call_center"][:10])
    sentences.extend(SHARVARD_LISTS["lista_numeros"][:5])
    sentences.extend(CHALLENGING_SEQUENCES[:3])
    return sentences[:50]


def get_call_center_corpus() -> list:
    """Get sentences optimized for call center training"""
    sentences = []
    sentences.extend(SHARVARD_LISTS["lista_call_center"])
    sentences.extend(SHARVARD_LISTS["lista_numeros"])
    sentences.extend(EMOTIONAL_SENTENCES["neutral"])
    sentences.extend(EMOTIONAL_SENTENCES["pregunta"])
    sentences.extend(EMOTIONAL_SENTENCES["enfasis"])
    sentences.extend(EMOTIONAL_SENTENCES["disculpa"])
    sentences.extend(PHONETIC_PANGRAMS[:2])
    return sentences


def export_corpus_for_recording(output_path: str, corpus_type: str = "full"):
    """Export corpus to text file for recording sessions"""
    if corpus_type == "full":
        sentences = get_all_training_sentences()
    elif corpus_type == "minimal":
        sentences = get_minimal_corpus()
    elif corpus_type == "call_center":
        sentences = get_call_center_corpus()
    else:
        sentences = get_all_training_sentences()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Corpus para Grabación TTS\n")
        f.write(f"# Total de oraciones: {len(sentences)}\n")
        f.write("# Instrucciones: Lea cada oración de forma natural, con pausas entre oraciones.\n\n")
        
        for i, sentence in enumerate(sentences, 1):
            f.write(f"{i:03d}. {sentence}\n")
    
    print(f"Corpus exportado a {output_path} ({len(sentences)} oraciones)")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        output = sys.argv[1]
        corpus_type = sys.argv[2] if len(sys.argv) > 2 else "full"
        export_corpus_for_recording(output, corpus_type)
    else:
        print("=== Spanish TTS Training Corpus ===\n")
        print(f"Full corpus: {len(get_all_training_sentences())} sentences")
        print(f"Minimal corpus: {len(get_minimal_corpus())} sentences")
        print(f"Call center corpus: {len(get_call_center_corpus())} sentences")
        print("\nUsage: python sharvard_corpus.py output.txt [full|minimal|call_center]")
