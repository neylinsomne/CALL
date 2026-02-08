/**
 * Voice Lab Mock Data
 * Corpus Sharvard, estilos, terminos personalizados y estado del pipeline
 */

// ===========================================
// VOICE STYLES (mirrors config.py STYLES)
// ===========================================
export const VOICE_STYLES = [
    { id: 'neutral', name: 'Neutral', color: '#6b7280', description: 'Tono informativo estandar' },
    { id: 'amable', name: 'Amable', color: '#10b981', description: 'Tono calido y acogedor' },
    { id: 'empatico', name: 'Empatico', color: '#8b5cf6', description: 'Tono comprensivo ante problemas' },
    { id: 'profesional', name: 'Profesional', color: '#3b82f6', description: 'Tono formal y seguro' },
];

// ===========================================
// CORPUS LISTS (from sharvard_corpus.py)
// ===========================================
export const CORPUS_SECTIONS = [
    { title: 'Fonetico', lists: ['pangrams', 'lista_diptongos', 'minimal_pairs', 'challenging'] },
    { title: 'Sharvard General', lists: ['lista_01', 'lista_02', 'lista_03', 'lista_04', 'lista_05'] },
    { title: 'Dominio', lists: ['lista_call_center', 'lista_numeros'] },
    { title: 'Emocional', lists: ['emotional'] },
];

export const CORPUS_LISTS = [
    { id: 'pangrams', name: 'Pangramas Foneticos', category: 'phonetic' },
    { id: 'lista_01', name: 'Lista 01 - General', category: 'sharvard' },
    { id: 'lista_02', name: 'Lista 02 - General', category: 'sharvard' },
    { id: 'lista_03', name: 'Lista 03 - General', category: 'sharvard' },
    { id: 'lista_04', name: 'Lista 04 - General', category: 'sharvard' },
    { id: 'lista_05', name: 'Lista 05 - General', category: 'sharvard' },
    { id: 'lista_call_center', name: 'Call Center', category: 'domain' },
    { id: 'lista_diptongos', name: 'Diptongos', category: 'phonetic' },
    { id: 'lista_numeros', name: 'Numeros', category: 'domain' },
    { id: 'minimal_pairs', name: 'Pares Minimos', category: 'phonetic' },
    { id: 'challenging', name: 'Secuencias Dificiles', category: 'phonetic' },
    { id: 'emotional', name: 'Variaciones Emocionales', category: 'emotional' },
];

// ===========================================
// CORPUS SENTENCES (all from sharvard_corpus.py)
// ===========================================
export const CORPUS_SENTENCES = [
    // --- PANGRAMS (7) ---
    { id: 'pang-1', listId: 'pangrams', text: 'El veloz murcielago hindu comia feliz cardillo y kiwi. La ciguena tocaba el saxofon detras del palenque de paja.', styleLabel: 'neutral', hasRecording: true, recordingDuration: 8.2, quality: 0.92 },
    { id: 'pang-2', listId: 'pangrams', text: 'Quelonio y fabuloso, el viejo tejon quejica huye del zoo tras exhibir su vergonzosa panza.', styleLabel: 'neutral', hasRecording: true, recordingDuration: 6.1, quality: 0.88 },
    { id: 'pang-3', listId: 'pangrams', text: 'Benjamin pidio una bebida de kiwi y fresa; Noe, sin verguenza, la mas exquisita champana del menu.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'pang-4', listId: 'pangrams', text: 'El ferrocarril recorria rapidamente el irregular terreno rural, resonando entre los cerros.', styleLabel: 'neutral', hasRecording: true, recordingDuration: 5.8, quality: 0.90 },
    { id: 'pang-5', listId: 'pangrams', text: 'Seis chicos suizos zozobraban en sus chalupas, silbando canciones sin cesar.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'pang-6', listId: 'pangrams', text: 'La abstracta construccion del instrumento extraordinario complementaba la estructura.', styleLabel: 'profesional', hasRecording: true, recordingDuration: 5.4, quality: 0.85 },
    { id: 'pang-7', listId: 'pangrams', text: '¿Que? ¡Jamas! Pero... ¿por que no? Seguramente, tal vez, quizas sera posible.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },

    // --- LISTA 01 (10) ---
    { id: 'sh01-01', listId: 'lista_01', text: 'El barco de vela cruzo el ancho mar.', styleLabel: 'neutral', hasRecording: true, recordingDuration: 3.1, quality: 0.91 },
    { id: 'sh01-02', listId: 'lista_01', text: 'La sal da sabor a la comida sosa.', styleLabel: 'neutral', hasRecording: true, recordingDuration: 2.8, quality: 0.89 },
    { id: 'sh01-03', listId: 'lista_01', text: 'El perro corre por el campo verde.', styleLabel: 'neutral', hasRecording: true, recordingDuration: 2.9, quality: 0.93 },
    { id: 'sh01-04', listId: 'lista_01', text: 'Mi madre cose la ropa de cama.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'sh01-05', listId: 'lista_01', text: 'El sol brilla en el cielo azul.', styleLabel: 'neutral', hasRecording: true, recordingDuration: 2.5, quality: 0.94 },
    { id: 'sh01-06', listId: 'lista_01', text: 'La luna llena ilumina la noche.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'sh01-07', listId: 'lista_01', text: 'El nino juega con su pelota roja.', styleLabel: 'amable', hasRecording: true, recordingDuration: 3.0, quality: 0.87 },
    { id: 'sh01-08', listId: 'lista_01', text: 'La flor perfuma todo el jardin.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'sh01-09', listId: 'lista_01', text: 'El rio fluye hacia el gran oceano.', styleLabel: 'neutral', hasRecording: true, recordingDuration: 3.2, quality: 0.90 },
    { id: 'sh01-10', listId: 'lista_01', text: 'La montana se eleva sobre el valle.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },

    // --- LISTA 02 (10) ---
    { id: 'sh02-01', listId: 'lista_02', text: 'El gato duerme junto a la chimenea.', styleLabel: 'neutral', hasRecording: true, recordingDuration: 3.0, quality: 0.88 },
    { id: 'sh02-02', listId: 'lista_02', text: 'La lluvia cae sobre los tejados grises.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'sh02-03', listId: 'lista_02', text: 'El viento sopla entre los arboles altos.', styleLabel: 'neutral', hasRecording: true, recordingDuration: 3.1, quality: 0.86 },
    { id: 'sh02-04', listId: 'lista_02', text: 'La campana suena en la torre vieja.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'sh02-05', listId: 'lista_02', text: 'El tren pasa por el tunel oscuro.', styleLabel: 'neutral', hasRecording: true, recordingDuration: 2.7, quality: 0.91 },
    { id: 'sh02-06', listId: 'lista_02', text: 'La abeja vuela de flor en flor.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'sh02-07', listId: 'lista_02', text: 'El pescador lanza su red al agua.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'sh02-08', listId: 'lista_02', text: 'La estrella brilla en el firmamento.', styleLabel: 'neutral', hasRecording: true, recordingDuration: 2.9, quality: 0.87 },
    { id: 'sh02-09', listId: 'lista_02', text: 'El reloj marca las doce en punto.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'sh02-10', listId: 'lista_02', text: 'La puerta se abre hacia el jardin.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },

    // --- LISTA 03 (10) ---
    { id: 'sh03-01', listId: 'lista_03', text: 'El caballo galopa por la pradera.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'sh03-02', listId: 'lista_03', text: 'La guitarra suena en la noche clara.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'sh03-03', listId: 'lista_03', text: 'El pintor mezcla colores en su paleta.', styleLabel: 'neutral', hasRecording: true, recordingDuration: 3.3, quality: 0.85 },
    { id: 'sh03-04', listId: 'lista_03', text: 'La mariposa descansa sobre la rama.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'sh03-05', listId: 'lista_03', text: 'El cocinero prepara una sopa caliente.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'sh03-06', listId: 'lista_03', text: 'La ventana muestra el paisaje nevado.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'sh03-07', listId: 'lista_03', text: 'El libro cuenta historias de aventuras.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'sh03-08', listId: 'lista_03', text: 'La fuente mana agua cristalina.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'sh03-09', listId: 'lista_03', text: 'El pajaro canta al amanecer temprano.', styleLabel: 'amable', hasRecording: true, recordingDuration: 3.1, quality: 0.86 },
    { id: 'sh03-10', listId: 'lista_03', text: 'La lampara alumbra todo el cuarto.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },

    // --- LISTA 04 (10) ---
    { id: 'sh04-01', listId: 'lista_04', text: 'El medico atiende a sus pacientes.', styleLabel: 'profesional', hasRecording: true, recordingDuration: 2.9, quality: 0.90 },
    { id: 'sh04-02', listId: 'lista_04', text: 'La escuela abre sus puertas al alba.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'sh04-03', listId: 'lista_04', text: 'El musico toca el violin con pasion.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'sh04-04', listId: 'lista_04', text: 'La carta llego desde muy lejos.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'sh04-05', listId: 'lista_04', text: 'El sastre corta la tela con cuidado.', styleLabel: 'profesional', hasRecording: true, recordingDuration: 3.0, quality: 0.88 },
    { id: 'sh04-06', listId: 'lista_04', text: 'La radio transmite noticias del mundo.', styleLabel: 'neutral', hasRecording: true, recordingDuration: 2.8, quality: 0.91 },
    { id: 'sh04-07', listId: 'lista_04', text: 'El maestro ensena con paciencia infinita.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'sh04-08', listId: 'lista_04', text: 'La cosecha fue abundante este ano.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'sh04-09', listId: 'lista_04', text: 'El camino serpentea por las colinas.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'sh04-10', listId: 'lista_04', text: 'La plaza esta llena de palomas.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },

    // --- LISTA 05 (10) ---
    { id: 'sh05-01', listId: 'lista_05', text: 'El zapatero arregla los zapatos viejos.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'sh05-02', listId: 'lista_05', text: 'La cigarra canta durante el verano.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'sh05-03', listId: 'lista_05', text: 'El lenador corta la madera seca.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'sh05-04', listId: 'lista_05', text: 'La huerta produce verduras frescas.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'sh05-05', listId: 'lista_05', text: 'El panadero hornea el pan temprano.', styleLabel: 'amable', hasRecording: true, recordingDuration: 2.7, quality: 0.84 },
    { id: 'sh05-06', listId: 'lista_05', text: 'La brisa marina refresca la tarde.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'sh05-07', listId: 'lista_05', text: 'El jardinero poda los rosales blancos.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'sh05-08', listId: 'lista_05', text: 'La chimenea calienta toda la casa.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'sh05-09', listId: 'lista_05', text: 'El pastor cuida su rebano de ovejas.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'sh05-10', listId: 'lista_05', text: 'La nieve cubre las cumbres altas.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },

    // --- CALL CENTER (15) ---
    { id: 'shcc-01', listId: 'lista_call_center', text: 'Buenos dias, gracias por llamar a nuestro servicio.', styleLabel: 'amable', hasRecording: true, recordingDuration: 3.5, quality: 0.94 },
    { id: 'shcc-02', listId: 'lista_call_center', text: '¿En que puedo ayudarle el dia de hoy?', styleLabel: 'amable', hasRecording: true, recordingDuration: 2.8, quality: 0.92 },
    { id: 'shcc-03', listId: 'lista_call_center', text: 'Permitame verificar su informacion en el sistema.', styleLabel: 'profesional', hasRecording: true, recordingDuration: 3.2, quality: 0.89 },
    { id: 'shcc-04', listId: 'lista_call_center', text: 'Le voy a transferir con un especialista ahora.', styleLabel: 'profesional', hasRecording: true, recordingDuration: 3.0, quality: 0.87 },
    { id: 'shcc-05', listId: 'lista_call_center', text: '¿Me puede confirmar su numero de telefono, por favor?', styleLabel: 'neutral', hasRecording: true, recordingDuration: 3.4, quality: 0.90 },
    { id: 'shcc-06', listId: 'lista_call_center', text: 'Entiendo perfectamente su situacion, le vamos a ayudar.', styleLabel: 'empatico', hasRecording: true, recordingDuration: 3.6, quality: 0.93 },
    { id: 'shcc-07', listId: 'lista_call_center', text: 'La solucion a su problema es muy sencilla.', styleLabel: 'profesional', hasRecording: true, recordingDuration: 2.9, quality: 0.88 },
    { id: 'shcc-08', listId: 'lista_call_center', text: 'Le enviaremos la informacion a su correo electronico.', styleLabel: 'neutral', hasRecording: true, recordingDuration: 3.3, quality: 0.91 },
    { id: 'shcc-09', listId: 'lista_call_center', text: '¿Hay algo mas en lo que pueda asistirle?', styleLabel: 'amable', hasRecording: true, recordingDuration: 2.7, quality: 0.95 },
    { id: 'shcc-10', listId: 'lista_call_center', text: 'Gracias por su llamada, que tenga un excelente dia.', styleLabel: 'amable', hasRecording: true, recordingDuration: 3.1, quality: 0.94 },
    { id: 'shcc-11', listId: 'lista_call_center', text: 'Lamentamos mucho los inconvenientes ocasionados.', styleLabel: 'empatico', hasRecording: true, recordingDuration: 3.0, quality: 0.91 },
    { id: 'shcc-12', listId: 'lista_call_center', text: 'Su solicitud ha sido registrada correctamente.', styleLabel: 'profesional', hasRecording: true, recordingDuration: 2.8, quality: 0.89 },
    { id: 'shcc-13', listId: 'lista_call_center', text: 'El tiempo estimado de espera es de cinco minutos.', styleLabel: 'neutral', hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shcc-14', listId: 'lista_call_center', text: 'Por favor, mantengase en la linea mientras verifico.', styleLabel: 'profesional', hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shcc-15', listId: 'lista_call_center', text: 'Su caso ha sido escalado al departamento correspondiente.', styleLabel: 'profesional', hasRecording: false, recordingDuration: null, quality: null },

    // --- DIPTONGOS (10) ---
    { id: 'shdi-01', listId: 'lista_diptongos', text: 'El cielo se tine de violeta al atardecer.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shdi-02', listId: 'lista_diptongos', text: 'La ciudad hierve con el bullicio diario.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shdi-03', listId: 'lista_diptongos', text: 'El buey arrastra el arado pesado.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shdi-04', listId: 'lista_diptongos', text: 'La viuda cuida su huerto con esmero.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shdi-05', listId: 'lista_diptongos', text: 'El hielo cubre el lago en invierno.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shdi-06', listId: 'lista_diptongos', text: 'La suave brisa acaricia los trigales.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shdi-07', listId: 'lista_diptongos', text: 'El fuelle del acordeon resuena fuerte.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shdi-08', listId: 'lista_diptongos', text: 'La flauta emite notas muy agudas.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shdi-09', listId: 'lista_diptongos', text: 'El naufrago espera en la isla desierta.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shdi-10', listId: 'lista_diptongos', text: 'La pieza del museo es muy valiosa.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },

    // --- NUMEROS (10) ---
    { id: 'shnu-01', listId: 'lista_numeros', text: 'Tengo veintitres anos de experiencia laboral.', styleLabel: 'neutral', hasRecording: true, recordingDuration: 3.1, quality: 0.88 },
    { id: 'shnu-02', listId: 'lista_numeros', text: 'El edificio tiene cuarenta y cinco pisos.', styleLabel: 'neutral', hasRecording: true, recordingDuration: 2.9, quality: 0.90 },
    { id: 'shnu-03', listId: 'lista_numeros', text: 'Necesito ciento veinte unidades para manana.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shnu-04', listId: 'lista_numeros', text: 'Son mil quinientos pesos en total.', styleLabel: 'neutral', hasRecording: true, recordingDuration: 2.5, quality: 0.92 },
    { id: 'shnu-05', listId: 'lista_numeros', text: 'Quedan tres mil doscientos kilometros de viaje.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shnu-06', listId: 'lista_numeros', text: 'La temperatura alcanzo treinta y ocho grados.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shnu-07', listId: 'lista_numeros', text: 'El vuelo dura aproximadamente cuatro horas.', styleLabel: 'neutral', hasRecording: true, recordingDuration: 2.8, quality: 0.87 },
    { id: 'shnu-08', listId: 'lista_numeros', text: 'Hay doscientas cincuenta personas esperando.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shnu-09', listId: 'lista_numeros', text: 'El precio bajo un quince por ciento.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shnu-10', listId: 'lista_numeros', text: 'Faltan noventa dias para fin de ano.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },

    // --- PARES MINIMOS (14) ---
    { id: 'shmp-01', listId: 'minimal_pairs', text: 'Digo pero, no digo perro.', styleLabel: 'neutral', hasRecording: true, recordingDuration: 2.3, quality: 0.86 },
    { id: 'shmp-02', listId: 'minimal_pairs', text: 'Digo caro, no digo carro.', styleLabel: 'neutral', hasRecording: true, recordingDuration: 2.1, quality: 0.88 },
    { id: 'shmp-03', listId: 'minimal_pairs', text: 'Digo cero, no digo cerro.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shmp-04', listId: 'minimal_pairs', text: 'Digo moro, no digo morro.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shmp-05', listId: 'minimal_pairs', text: 'Digo para, no digo parra.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shmp-06', listId: 'minimal_pairs', text: 'Digo baca, no digo vaca.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shmp-07', listId: 'minimal_pairs', text: 'Digo bello, no digo vello.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shmp-08', listId: 'minimal_pairs', text: 'Digo bienes, no digo vienes.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shmp-09', listId: 'minimal_pairs', text: 'Digo casa, no digo caza.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shmp-10', listId: 'minimal_pairs', text: 'Digo coser, no digo cocer.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shmp-11', listId: 'minimal_pairs', text: 'Digo sumo, no digo zumo.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shmp-12', listId: 'minimal_pairs', text: 'Digo ano, no digo ano.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shmp-13', listId: 'minimal_pairs', text: 'Digo mono, no digo mono.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shmp-14', listId: 'minimal_pairs', text: 'Digo cana, no digo cana.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },

    // --- SECUENCIAS DIFICILES (9) ---
    { id: 'shch-01', listId: 'challenging', text: 'La construccion del instrumento requiere abstraccion.', styleLabel: 'profesional', hasRecording: true, recordingDuration: 3.8, quality: 0.83 },
    { id: 'shch-02', listId: 'challenging', text: 'El extraordinario espectaculo impresiono al inspector.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shch-03', listId: 'challenging', text: 'La transcripcion del manuscrito describe estructuras complejas.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shch-04', listId: 'challenging', text: 'Tres tristes tigres tragaban trigo en un trigal.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shch-05', listId: 'challenging', text: 'El cielo esta enladrillado, ¿quien lo desenladrillara?', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shch-06', listId: 'challenging', text: 'Pablito clavo un clavito, ¿que clavito clavo Pablito?', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shch-07', listId: 'challenging', text: 'La electroencefalografia es extraordinariamente especializada.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shch-08', listId: 'challenging', text: 'El otorrinolaringologo diagnostico faringoamigdalitis.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shch-09', listId: 'challenging', text: 'La internacionalizacion provoco desestabilizacion economica.', styleLabel: null, hasRecording: false, recordingDuration: null, quality: null },

    // --- VARIACIONES EMOCIONALES (12) ---
    { id: 'shem-01', listId: 'emotional', text: 'El informe esta listo para su revision.', styleLabel: 'neutral', hasRecording: true, recordingDuration: 2.6, quality: 0.91 },
    { id: 'shem-02', listId: 'emotional', text: 'La reunion comienza a las tres de la tarde.', styleLabel: 'neutral', hasRecording: true, recordingDuration: 2.9, quality: 0.89 },
    { id: 'shem-03', listId: 'emotional', text: 'Los documentos se encuentran en la carpeta azul.', styleLabel: 'neutral', hasRecording: true, recordingDuration: 3.0, quality: 0.90 },
    { id: 'shem-04', listId: 'emotional', text: '¿Podria indicarme donde queda la oficina principal?', styleLabel: 'amable', hasRecording: true, recordingDuration: 3.2, quality: 0.87 },
    { id: 'shem-05', listId: 'emotional', text: '¿Cuanto tiempo tomara procesar mi solicitud?', styleLabel: 'neutral', hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shem-06', listId: 'emotional', text: '¿Es posible reprogramar la cita para manana?', styleLabel: 'amable', hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shem-07', listId: 'emotional', text: 'Es absolutamente necesario que revise estos datos.', styleLabel: 'profesional', hasRecording: true, recordingDuration: 3.1, quality: 0.88 },
    { id: 'shem-08', listId: 'emotional', text: 'Le aseguro que su problema sera resuelto hoy mismo.', styleLabel: 'empatico', hasRecording: true, recordingDuration: 3.3, quality: 0.92 },
    { id: 'shem-09', listId: 'emotional', text: 'Definitivamente contamos con la mejor solucion disponible.', styleLabel: 'profesional', hasRecording: false, recordingDuration: null, quality: null },
    { id: 'shem-10', listId: 'emotional', text: 'Lamento mucho la demora en atender su llamada.', styleLabel: 'empatico', hasRecording: true, recordingDuration: 3.0, quality: 0.93 },
    { id: 'shem-11', listId: 'emotional', text: 'Pedimos disculpas por cualquier inconveniente causado.', styleLabel: 'empatico', hasRecording: true, recordingDuration: 2.8, quality: 0.91 },
    { id: 'shem-12', listId: 'emotional', text: 'Sentimos no poder ayudarle en esta ocasion.', styleLabel: 'empatico', hasRecording: false, recordingDuration: null, quality: null },
];

// ===========================================
// CUSTOM TERMS
// ===========================================
export const TERM_CATEGORIES = [
    { id: 'client-brands', name: 'Marcas Cliente' },
    { id: 'acronyms', name: 'Acronimos' },
    { id: 'technical', name: 'Terminos Tecnicos' },
    { id: 'names', name: 'Nombres Propios' },
    { id: 'numbers', name: 'Numeros Especiales' },
];

export const CUSTOM_TERMS = [
    { id: 'ct-1', term: 'Bancolombia', phonetic: 'ban.ko.lom.bja', category: 'client-brands', context: 'Nombre del banco cliente', hasAudio: true, audioDuration: 1.4 },
    { id: 'ct-2', term: 'PSE', phonetic: 'pe.se.e', category: 'acronyms', context: 'Pagos Seguros en Linea - deletrear', hasAudio: false, audioDuration: null },
    { id: 'ct-3', term: 'SOAT', phonetic: 'so.at', category: 'acronyms', context: 'Seguro Obligatorio de Accidentes de Transito', hasAudio: true, audioDuration: 1.1 },
    { id: 'ct-4', term: 'Daviplata', phonetic: 'da.bi.pla.ta', category: 'client-brands', context: 'Billetera digital Davivienda', hasAudio: true, audioDuration: 1.3 },
    { id: 'ct-5', term: 'Nequi', phonetic: 'ne.ki', category: 'client-brands', context: 'Billetera digital Bancolombia', hasAudio: true, audioDuration: 0.9 },
    { id: 'ct-6', term: 'CDT', phonetic: 'se.de.te', category: 'acronyms', context: 'Certificado de Deposito a Termino', hasAudio: false, audioDuration: null },
    { id: 'ct-7', term: 'API REST', phonetic: 'a.pi rest', category: 'technical', context: 'Interfaz de programacion', hasAudio: false, audioDuration: null },
    { id: 'ct-8', term: 'webhook', phonetic: 'web.juk', category: 'technical', context: 'Callback HTTP automatico', hasAudio: false, audioDuration: null },
];

// ===========================================
// PIPELINE STATUS
// ===========================================
export const PIPELINE_STATUS = {
    currentRun: {
        id: 'run_a3b7c2d1',
        startedAt: '2026-01-19T08:00:00',
        status: 'running',
        currentStage: 'evolve',
        elapsedSeconds: 14520,
    },
    stages: [
        { id: 'reference', name: 'Referencia (F5-TTS)', status: 'completed', elapsedSeconds: 750, details: { stylesGenerated: ['neutral', 'amable', 'empatico', 'profesional'] } },
        { id: 'evolve', name: 'Evolucion (KVoiceWalk)', status: 'running', elapsedSeconds: null, progress: 67, details: { currentStyle: 'empatico', stepsCompleted: 6700, stepsTotal: 10000, improvements: 23, currentBestScore: 78.4 } },
        { id: 'validate', name: 'Validacion', status: 'pending', elapsedSeconds: null, details: null },
        { id: 'deploy', name: 'Despliegue', status: 'pending', elapsedSeconds: null, details: null },
    ],
    styleScores: [
        { style: 'neutral', targetSimilarity: 0.82, selfSimilarity: 0.91, featureSimilarity: 0.78, overall: 85.3, valid: true },
        { style: 'amable', targetSimilarity: 0.79, selfSimilarity: 0.88, featureSimilarity: 0.75, overall: 81.1, valid: true },
        { style: 'empatico', targetSimilarity: 0.74, selfSimilarity: 0.86, featureSimilarity: 0.71, overall: 78.4, valid: true },
        { style: 'profesional', targetSimilarity: 0.0, selfSimilarity: 0.0, featureSimilarity: 0.0, overall: 0.0, valid: false },
    ],
    evolutionHistory: [
        { step: 0, neutral: 62.1, amable: 58.3, empatico: 55.2, profesional: 0 },
        { step: 1000, neutral: 68.4, amable: 64.1, empatico: 61.8, profesional: 0 },
        { step: 2000, neutral: 72.3, amable: 69.5, empatico: 66.2, profesional: 0 },
        { step: 3000, neutral: 75.8, amable: 73.2, empatico: 70.1, profesional: 0 },
        { step: 4000, neutral: 78.1, amable: 75.8, empatico: 72.9, profesional: 0 },
        { step: 5000, neutral: 80.5, amable: 77.4, empatico: 74.8, profesional: 0 },
        { step: 6000, neutral: 82.7, amable: 79.1, empatico: 76.3, profesional: 0 },
        { step: 7000, neutral: 84.0, amable: 80.2, empatico: 77.5, profesional: 0 },
        { step: 8000, neutral: 84.8, amable: 80.8, empatico: 78.0, profesional: 0 },
        { step: 9000, neutral: 85.1, amable: 81.0, empatico: 78.3, profesional: 0 },
        { step: 10000, neutral: 85.3, amable: 81.1, empatico: 78.4, profesional: 0 },
    ],
    recentRuns: [
        { id: 'run_a3b7c2d1', date: '2026-01-19', status: 'running', styles: 4, bestScore: 85.3 },
        { id: 'run_f1e2d3c4', date: '2026-01-17', status: 'completed', styles: 4, bestScore: 82.1 },
        { id: 'run_b5a6c7d8', date: '2026-01-14', status: 'failed', styles: 2, bestScore: 71.5 },
    ],
};
