"""
Spanish Text Normalizer for TTS
Expands abbreviations, numbers, and special characters to spoken form
"""

import re
from typing import Optional


# ===========================================
# Number to Words Conversion
# ===========================================
UNITS = ['', 'uno', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete', 'ocho', 'nueve']
TEENS = ['diez', 'once', 'doce', 'trece', 'catorce', 'quince', 'dieciséis', 'diecisiete', 'dieciocho', 'diecinueve']
TENS = ['', 'diez', 'veinte', 'treinta', 'cuarenta', 'cincuenta', 'sesenta', 'setenta', 'ochenta', 'noventa']
HUNDREDS = ['', 'ciento', 'doscientos', 'trescientos', 'cuatrocientos', 'quinientos', 'seiscientos', 'setecientos', 'ochocientos', 'novecientos']


def number_to_words(n: int) -> str:
    """Convert integer to Spanish words"""
    if n == 0:
        return 'cero'
    if n < 0:
        return 'menos ' + number_to_words(-n)
    
    if n == 100:
        return 'cien'
    
    if n < 10:
        return UNITS[n]
    
    if n < 20:
        return TEENS[n - 10]
    
    if n < 30:
        if n == 20:
            return 'veinte'
        return 'veinti' + UNITS[n - 20]
    
    if n < 100:
        tens, units = divmod(n, 10)
        if units == 0:
            return TENS[tens]
        return TENS[tens] + ' y ' + UNITS[units]
    
    if n < 1000:
        hundreds, remainder = divmod(n, 100)
        if remainder == 0:
            return HUNDREDS[hundreds] if hundreds != 1 else 'cien'
        return HUNDREDS[hundreds] + ' ' + number_to_words(remainder)
    
    if n < 1000000:
        thousands, remainder = divmod(n, 1000)
        if thousands == 1:
            prefix = 'mil'
        else:
            prefix = number_to_words(thousands) + ' mil'
        if remainder == 0:
            return prefix
        return prefix + ' ' + number_to_words(remainder)
    
    if n < 1000000000:
        millions, remainder = divmod(n, 1000000)
        if millions == 1:
            prefix = 'un millón'
        else:
            prefix = number_to_words(millions) + ' millones'
        if remainder == 0:
            return prefix
        return prefix + ' ' + number_to_words(remainder)
    
    # Billions
    billions, remainder = divmod(n, 1000000000)
    if billions == 1:
        prefix = 'mil millones'
    else:
        prefix = number_to_words(billions) + ' mil millones'
    if remainder == 0:
        return prefix
    return prefix + ' ' + number_to_words(remainder)


def decimal_to_words(decimal_str: str) -> str:
    """Convert decimal numbers to Spanish words"""
    parts = decimal_str.split('.')
    integer_part = number_to_words(int(parts[0]))
    
    if len(parts) == 1 or parts[1] == '':
        return integer_part
    
    # Read decimal digits individually
    decimal_part = ' '.join([UNITS[int(d)] if d != '0' else 'cero' for d in parts[1]])
    return integer_part + ' punto ' + decimal_part


# ===========================================
# Abbreviations
# ===========================================
ABBREVIATIONS = {
    # Titles
    'Dr.': 'Doctor',
    'Dra.': 'Doctora',
    'Sr.': 'Señor',
    'Sra.': 'Señora',
    'Srta.': 'Señorita',
    'Lic.': 'Licenciado',
    'Ing.': 'Ingeniero',
    'Arq.': 'Arquitecto',
    'Prof.': 'Profesor',
    
    # Units
    'km': 'kilómetros',
    'km/h': 'kilómetros por hora',
    'm': 'metros',
    'cm': 'centímetros',
    'mm': 'milímetros',
    'kg': 'kilogramos',
    'g': 'gramos',
    'mg': 'miligramos',
    'l': 'litros',
    'ml': 'mililitros',
    'h': 'horas',
    'min': 'minutos',
    's': 'segundos',
    
    # Common
    'etc.': 'etcétera',
    'vs.': 'versus',
    'ej.': 'ejemplo',
    'p.ej.': 'por ejemplo',
    'núm.': 'número',
    'pág.': 'página',
    'tel.': 'teléfono',
    'aprox.': 'aproximadamente',
    
    # Organizations
    'S.A.': 'Sociedad Anónima',
    'S.L.': 'Sociedad Limitada',
    'CIA': 'compañía',
    'Co.': 'compañía',
}


# ===========================================
# Special Patterns
# ===========================================
def expand_currency(match) -> str:
    """Expand currency patterns"""
    amount = match.group(1).replace(',', '')
    currency = match.group(2) if match.lastindex >= 2 else ''
    
    try:
        num = float(amount)
        if num == int(num):
            words = number_to_words(int(num))
        else:
            words = decimal_to_words(amount)
    except:
        return match.group(0)
    
    currency_map = {
        '$': 'dólares',
        '€': 'euros',
        '£': 'libras',
        '¥': 'yenes',
        'USD': 'dólares',
        'EUR': 'euros',
        'COP': 'pesos colombianos',
        'MXN': 'pesos mexicanos',
    }
    
    currency_word = currency_map.get(currency, currency)
    return words + ' ' + currency_word


def expand_percentage(match) -> str:
    """Expand percentage patterns"""
    num = match.group(1)
    try:
        if '.' in num or ',' in num:
            words = decimal_to_words(num.replace(',', '.'))
        else:
            words = number_to_words(int(num))
    except:
        return match.group(0)
    return words + ' por ciento'


def expand_time(match) -> str:
    """Expand time patterns (e.g., 14:30)"""
    hours = int(match.group(1))
    minutes = int(match.group(2))
    
    if minutes == 0:
        return number_to_words(hours) + ' en punto'
    elif minutes == 30:
        return number_to_words(hours) + ' y media'
    elif minutes == 15:
        return number_to_words(hours) + ' y cuarto'
    else:
        return number_to_words(hours) + ' y ' + number_to_words(minutes)


def expand_date(match) -> str:
    """Expand date patterns (e.g., 15/03/2024)"""
    day = int(match.group(1))
    month = int(match.group(2))
    year = int(match.group(3))
    
    months = ['', 'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
              'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
    
    return number_to_words(day) + ' de ' + months[month] + ' de ' + number_to_words(year)


def expand_ordinal(num: int) -> str:
    """Convert number to ordinal"""
    ordinals = {
        1: 'primero', 2: 'segundo', 3: 'tercero', 4: 'cuarto', 5: 'quinto',
        6: 'sexto', 7: 'séptimo', 8: 'octavo', 9: 'noveno', 10: 'décimo',
        11: 'undécimo', 12: 'duodécimo', 13: 'decimotercero', 14: 'decimocuarto',
        15: 'decimoquinto', 16: 'decimosexto', 17: 'decimoséptimo',
        18: 'decimoctavo', 19: 'decimonoveno', 20: 'vigésimo'
    }
    return ordinals.get(num, number_to_words(num))


# ===========================================
# Main Normalizer
# ===========================================
def normalize_text(text: str) -> str:
    """
    Normalize Spanish text for TTS
    
    Performs:
    - Number to words conversion
    - Abbreviation expansion
    - Currency/percentage expansion
    - Time/date expansion
    - Symbol replacement
    """
    result = text
    
    # Replace abbreviations (case sensitive)
    for abbr, expansion in ABBREVIATIONS.items():
        result = result.replace(abbr, expansion)
    
    # Expand currency (e.g., $100, 50€, 1,000 USD)
    result = re.sub(r'([\$€£¥])(\d+(?:[.,]\d+)?)', 
                    lambda m: expand_currency(type('Match', (), {'group': lambda s, i: m.group(i) if i <= m.lastindex else '', 'lastindex': m.lastindex})()), 
                    result)
    result = re.sub(r'(\d+(?:[.,]\d+)?)\s*(USD|EUR|COP|MXN|€|\$)', expand_currency, result)
    
    # Expand percentages (e.g., 50%, 3.5%)
    result = re.sub(r'(\d+(?:[.,]\d+)?)\s*%', expand_percentage, result)
    
    # Expand times (e.g., 14:30, 9:00)
    result = re.sub(r'(\d{1,2}):(\d{2})', expand_time, result)
    
    # Expand dates (e.g., 15/03/2024, 15-03-2024)
    result = re.sub(r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})', expand_date, result)
    
    # Expand standalone numbers
    def replace_number(match):
        num_str = match.group(0).replace(',', '').replace('.', '', match.group(0).count('.') - 1)
        try:
            if '.' in num_str:
                return decimal_to_words(num_str)
            else:
                return number_to_words(int(num_str))
        except:
            return match.group(0)
    
    result = re.sub(r'\b\d+(?:,\d{3})*(?:\.\d+)?\b', replace_number, result)
    
    # Replace symbols
    symbol_map = {
        '&': ' y ',
        '+': ' más ',
        '=': ' igual a ',
        '@': ' arroba ',
        '#': ' número ',
        '/': ' barra ',
        '°': ' grados ',
    }
    for symbol, replacement in symbol_map.items():
        result = result.replace(symbol, replacement)
    
    # Clean up multiple spaces
    result = re.sub(r'\s+', ' ', result).strip()
    
    return result


# ===========================================
# Phonetic Validation
# ===========================================
SPANISH_PHONEMES = {
    'vowels': set('aeiouáéíóú'),
    'consonants': set('bcdfghjklmnñpqrstvwxyz'),
    'special': {'ch', 'll', 'rr', 'gu', 'qu'}
}


def check_phonetic_coverage(texts: list) -> dict:
    """
    Analyze phonetic coverage of a text corpus
    Returns missing phonemes and coverage statistics
    """
    all_text = ' '.join(texts).lower()
    
    # Check vowels
    found_vowels = set(c for c in all_text if c in SPANISH_PHONEMES['vowels'])
    missing_vowels = SPANISH_PHONEMES['vowels'] - found_vowels
    
    # Check consonants
    found_consonants = set(c for c in all_text if c in SPANISH_PHONEMES['consonants'])
    missing_consonants = SPANISH_PHONEMES['consonants'] - found_consonants
    
    # Check special digraphs
    found_special = set()
    for digraph in SPANISH_PHONEMES['special']:
        if digraph in all_text:
            found_special.add(digraph)
    missing_special = SPANISH_PHONEMES['special'] - found_special
    
    # Calculate coverage
    total_phonemes = len(SPANISH_PHONEMES['vowels']) + len(SPANISH_PHONEMES['consonants']) + len(SPANISH_PHONEMES['special'])
    found_total = len(found_vowels) + len(found_consonants) + len(found_special)
    
    return {
        'coverage_percent': (found_total / total_phonemes) * 100,
        'missing_vowels': list(missing_vowels),
        'missing_consonants': list(missing_consonants),
        'missing_special': list(missing_special),
        'total_phonemes': total_phonemes,
        'found_phonemes': found_total
    }


if __name__ == "__main__":
    # Test examples
    tests = [
        "El Dr. García tiene 45 años y pesa 80kg.",
        "La temperatura es de 23.5°C con 60% de humedad.",
        "El vuelo sale a las 14:30 y cuesta $1,500 USD.",
        "Nació el 15/03/1990 en la calle 5 núm. 123.",
        "Velocidad máxima: 120km/h en autopista.",
    ]
    
    print("=== Spanish Text Normalizer Test ===\n")
    for text in tests:
        normalized = normalize_text(text)
        print(f"Original:   {text}")
        print(f"Normalized: {normalized}")
        print()
