"""Intent detection, sentiment analysis and text corrections."""

import re
from typing import Any, Dict, List, Tuple


# Definición de intenciones y sus patrones
INTENTS = {
    'precio': [
        'cuánto cuesta', 'precio', 'valor', 'tarifa', 'cuanto vale',
        'cuál es el precio', 'a cuanto', 'costo', 'cuanto cobra'
    ],
    'stock': [
        'disponible', 'hay', 'tienen', 'stock', 'existencia',
        'cuánto hay', 'cantidad disponible', 'disponibilidad'
    ],
    'vender': [
        'vendo', 'tengo', 'ofrezco', 'quiero vender', 'venta',
        'soy proveedor', 'recolecto', 'tengo material'
    ],
    'comprar': [
        'compro', 'necesito', 'busco', 'quiero comprar', 'compra',
        'soy comprador', 'empresa', 'necesitamos'
    ],
    'calidad': [
        'calidad', 'certificado', 'garantía', 'verificación',
        'trazabilidad', 'limpio', 'clasificado'
    ],
    'ubicacion': [
        'dónde', 'ubicación', 'dirección', 'lugar', 'zona',
        'distrito', 'ciudad', 'región'
    ],
    'proceso': [
        'cómo funciona', 'proceso', 'pasos', 'como se hace',
        'procedimiento', 'cómo compro', 'cómo vendo'
    ],
    'contacto': [
        'contacto', 'teléfono', 'correo', 'email', 'whatsapp',
        'comunicarse', 'hablar con alguien'
    ],
    'tiempo': [
        'cuánto demora', 'tiempo', 'plazo', 'cuando',
        'entrega', 'rápido', 'urgente'
    ],
    'pago': [
        'pago', 'pagos', 'forma de pago', 'transferencia',
        'efectivo', 'factura', 'recibo'
    ]
}

# Autocorrección de errores comunes
CORRECTIONS = {
    'aliminio': 'aluminio',
    'aluminio': 'aluminio',
    'alumineo': 'aluminio',
    'acro': 'acero',
    'asero': 'acero',
    'plastico': 'plástico',
    'plastiko': 'plástico',
    'pet': 'PET',
    'hdpe': 'HDPE',
    'cobre': 'cobre',
    'kobre': 'cobre',
    'papel': 'papel',
    'carton': 'cartón',
    'vidrio': 'vidrio',
    'bidrio': 'vidrio',
    'q precio': '¿qué precio?',
    'q es': '¿qué es?',
    'xq': 'por qué',
    'xk': 'por qué',
    'tmb': 'también',
    'tb': 'también',
}

# Patrones de sentimiento
SENTIMENT_PATTERNS = {
    'positive': [
        'gracias', 'perfecto', 'excelente', 'genial', 'bueno',
        'bien', 'me gusta', 'interesante', 'ok', 'vale',
        'súper', 'increíble', 'fantástico'
    ],
    'negative': [
        'mal', 'problema', 'no funciona', 'frustrado', 'molesto',
        'confundido', 'difícil', 'complicado', 'no entiendo',
        'horrible', 'terrible', 'pésimo'
    ],
    'urgent': [
        'urgente', 'rápido', 'ya', 'ahora', 'inmediato',
        'hoy', 'cuanto antes', 'pronto'
    ],
    'question': [
        'cómo', 'qué', 'cuál', 'cuándo', 'dónde', 'por qué',
        '?', 'pregunta', 'duda', 'consulta'
    ]
}


def detect_intent(message: str) -> List[str]:
    """
    Detecta las intenciones del usuario en el mensaje.
    Puede devolver múltiples intenciones.
    """
    message_lower = message.lower()
    detected_intents: List[str] = []
    
    for intent, patterns in INTENTS.items():
        for pattern in patterns:
            if pattern in message_lower:
                if intent not in detected_intents:
                    detected_intents.append(intent)
                break
    
    return detected_intents


def detect_sentiment(message: str) -> Dict[str, bool]:
    """
    Analiza el sentimiento del mensaje.
    Retorna dict con: positive, negative, urgent, question
    """
    message_lower = message.lower()
    
    sentiment = {
        'positive': False,
        'negative': False,
        'urgent': False,
        'question': False
    }
    
    for sentiment_type, patterns in SENTIMENT_PATTERNS.items():
        for pattern in patterns:
            if pattern in message_lower:
                sentiment[sentiment_type] = True
                break
    
    return sentiment


def autocorrect_text(message: str) -> Tuple[str, List[str]]:
    """
    Corrige errores comunes de tipeo.
    Retorna: (texto_corregido, lista_de_correcciones)
    """
    corrected = message
    corrections_made: List[str] = []
    
    # Correcciones palabra por palabra
    words = message.split()
    corrected_words: List[str] = []
    
    for word in words:
        word_lower = word.lower()
        if word_lower in CORRECTIONS:
            corrected_word = CORRECTIONS[word_lower]
            corrected_words.append(corrected_word)
            corrections_made.append(f"{word} → {corrected_word}")
        else:
            corrected_words.append(word)
    
    corrected = ' '.join(corrected_words)
    
    return corrected, corrections_made


def extract_materials(message: str) -> List[str]:
    """
    Extrae nombres de materiales mencionados en el mensaje.
    """
    material_patterns = {
        'PET': ['pet', 'polietileno tereftalato', 'botellas plástico'],
        'HDPE': ['hdpe', 'polietileno alta densidad', 'envases plástico'],
        'LDPE': ['ldpe', 'polietileno baja densidad', 'bolsas'],
        'PP': ['pp', 'polipropileno', 'tapas'],
        'Aluminio': ['aluminio', 'aliminio', 'latas'],
        'Cobre': ['cobre', 'kobre', 'cables'],
        'Acero': ['acero', 'acro', 'chatarra'],
        'Bronce': ['bronce'],
        'Papel': ['papel', 'papeles'],
        'Cartón': ['cartón', 'carton', 'cajas'],
        'Vidrio': ['vidrio', 'vidio', 'botellas vidrio'],
        'Tetrapak': ['tetrapak', 'tetrapack']
    }
    
    message_lower = message.lower()
    materials: List[str] = []
    
    for material, patterns in material_patterns.items():
        for pattern in patterns:
            if pattern in message_lower:
                if material not in materials:
                    materials.append(material)
                break
    
    return materials


def extract_quantities(message: str) -> List[Dict[str, Any]]:
    """
    Extrae cantidades mencionadas (kg, toneladas, etc).
    Retorna lista de {value: float, unit: str}
    """
    # Patrones: "50 kg", "5 toneladas", "medio kilo", "5 ton"
    patterns = [
        r'(\d+\.?\d*)\s*(kg|kilo|kilos|kilogramos)',
        r'(\d+\.?\d*)\s*(ton|toneladas?|t)',
        r'(medio|media)\s*(kilo|tonelada)',
        r'(\d+)\s*(gramos?|gr|g)'
    ]
    
    quantities: List[Dict[str, Any]] = []
    
    for pattern in patterns:
        matches = re.finditer(pattern, message.lower())
        for match in matches:
            value_str = match.group(1)
            unit = match.group(2)
            
            # Convertir a número
            if value_str in ['medio', 'media']:
                value = 0.5
            else:
                value = float(value_str)
            
            # Normalizar unidad
            if unit in ['ton', 'toneladas', 'tonelada', 't']:
                normalized_unit = 'toneladas'
            elif unit in ['kg', 'kilo', 'kilos', 'kilogramos']:
                normalized_unit = 'kg'
            elif unit in ['gramos', 'gr', 'g', 'gramo']:
                normalized_unit = 'gramos'
            else:
                normalized_unit = unit
            
            quantities.append({
                'value': value,
                'unit': normalized_unit,
                'original': match.group(0)
            })
    
    return quantities


def analyze_message(message: str) -> Dict[str, Any]:
    """
    Análisis completo del mensaje.
    Retorna dict con: intents, sentiment, materials, quantities, corrected_text
    """
    # Autocorrección primero
    corrected_text, corrections = autocorrect_text(message)
    
    # Análisis sobre texto corregido
    intents = detect_intent(corrected_text)
    sentiment = detect_sentiment(corrected_text)
    materials = extract_materials(corrected_text)
    quantities = extract_quantities(corrected_text)
    
    return {
        'original': message,
        'corrected': corrected_text,
        'corrections': corrections,
        'intents': intents,
        'sentiment': sentiment,
        'materials': materials,
        'quantities': quantities,
        'has_question': sentiment['question'],
        'is_urgent': sentiment['urgent']
    }
