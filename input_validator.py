"""Input validation for materials, quantities, and business data."""

import re
from typing import Any, Dict, List, Optional, Tuple


# Materiales válidos del catálogo
VALID_MATERIALS = {
    'plasticos': ['PET', 'HDPE', 'LDPE', 'PP'],
    'metales': ['Aluminio', 'Cobre', 'Acero', 'Bronce'],
    'papel': ['Papel Blanco', 'Papel Periódico'],
    'carton': ['Cartón Corrugado', 'Cartón Compacto'],
    'vidrio': ['Vidrio Transparente', 'Vidrio de Color'],
    'especiales': ['Tetrapak', 'Baterías de Plomo']
}

# Rangos válidos de cantidades
QUANTITY_RANGES = {
    'kg': {'min': 1, 'max': 100000},
    'toneladas': {'min': 0.001, 'max': 1000},
    'gramos': {'min': 100, 'max': 1000000}
}


def validate_material(material: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Valida si el material existe en el catálogo.
    Retorna: (es_valido, material_normalizado, categoria)
    """
    material_lower = material.lower().strip()
    
    # Buscar en todas las categorías
    for category, materials in VALID_MATERIALS.items():
        for valid_material in materials:
            if material_lower in valid_material.lower() or valid_material.lower() in material_lower:
                return True, valid_material, category
    
    # Sugerencias si no encuentra
    suggestions: List[str] = []
    for category, materials in VALID_MATERIALS.items():
        for valid_material in materials:
            # Similitud básica por caracteres comunes
            if any(char in valid_material.lower() for char in material_lower.split()):
                suggestions.append(valid_material)
    
    if suggestions:
        return False, None, f"¿Quisiste decir: {', '.join(suggestions[:3])}?"
    
    return False, None, None


def validate_quantity(value: float, unit: str) -> Tuple[bool, Optional[str]]:
    """
    Valida si la cantidad está en rango válido.
    Retorna: (es_valido, mensaje_error)
    """
    unit_lower = unit.lower()
    
    # Normalizar unidad
    if unit_lower in ['ton', 'toneladas', 'tonelada', 't']:
        unit_key = 'toneladas'
    elif unit_lower in ['kg', 'kilo', 'kilos', 'kilogramos']:
        unit_key = 'kg'
    elif unit_lower in ['gramos', 'gr', 'g', 'gramo']:
        unit_key = 'gramos'
    else:
        return False, f"Unidad '{unit}' no reconocida. Usa: kg, toneladas o gramos"
    
    # Validar rango
    if unit_key not in QUANTITY_RANGES:
        return False, "Unidad no válida"
    
    limits = QUANTITY_RANGES[unit_key]
    
    if value < limits['min']:
        return False, f"Cantidad mínima: {limits['min']} {unit_key}"
    
    if value > limits['max']:
        return False, f"Cantidad máxima: {limits['max']} {unit_key}"
    
    return True, None


def normalize_quantity(value: float, unit: str) -> Dict[str, Any]:
    """
    Normaliza cantidades a kg y toneladas.
    Retorna: {kg: float, toneladas: float, original: str}
    """
    unit_lower = unit.lower()
    
    # Convertir todo a kg primero
    if unit_lower in ['ton', 'toneladas', 'tonelada', 't']:
        kg = value * 1000
    elif unit_lower in ['kg', 'kilo', 'kilos', 'kilogramos']:
        kg = value
    elif unit_lower in ['gramos', 'gr', 'g', 'gramo']:
        kg = value / 1000
    else:
        kg = value  # default
    
    toneladas = kg / 1000
    
    return {
        'kg': round(kg, 2),
        'toneladas': round(toneladas, 3),
        'original': f"{value} {unit}"
    }


def validate_phone(phone: str) -> Tuple[bool, Optional[str]]:
    """
    Valida formato de teléfono peruano.
    Retorna: (es_valido, telefono_normalizado)
    """
    # Limpiar caracteres
    clean = re.sub(r'[^\d+]', '', phone)
    
    # Patrones válidos para Perú
    patterns = [
        r'^\+51\d{9}$',  # +51999999999
        r'^51\d{9}$',    # 51999999999
        r'^\d{9}$'       # 999999999
    ]
    
    for pattern in patterns:
        if re.match(pattern, clean):
            # Normalizar a formato +51
            if clean.startswith('+51'):
                return True, clean
            elif clean.startswith('51'):
                return True, f"+{clean}"
            else:
                return True, f"+51{clean}"
    
    return False, None


def validate_email(email: str) -> bool:
    """Valida formato de email."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_price(price: float, currency: str = 'S/') -> Tuple[bool, Optional[str]]:
    """
    Valida que el precio sea razonable.
    Retorna: (es_valido, mensaje_error)
    """
    if price < 0:
        return False, "El precio no puede ser negativo"
    
    if currency == 'S/' and price > 100:  # S/ 100 por kg es muy alto
        return False, "Precio parece muy alto, verifica"
    
    if currency == '$' and price > 50000:  # $ 50k por tonelada es muy alto
        return False, "Precio parece muy alto, verifica"
    
    return True, None


def validate_business_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Valida datos completos de negociación.
    Retorna: (es_valido, lista_de_errores)
    """
    errors: List[str] = []
    
    # Validar campos requeridos
    required_fields = ['material', 'quantity', 'unit']
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"Falta campo requerido: {field}")
    
    # Validar material
    if 'material' in data:
        is_valid, _, _ = validate_material(data['material'])
        if not is_valid:
            errors.append(f"Material no válido: {data['material']}")
    
    # Validar cantidad
    if 'quantity' in data and 'unit' in data:
        is_valid, error_msg = validate_quantity(data['quantity'], data['unit'])
        if not is_valid:
            errors.append(error_msg or "Cantidad no válida")
    
    # Validar teléfono si está presente
    if 'phone' in data and data['phone']:
        is_valid, _ = validate_phone(data['phone'])
        if not is_valid:
            errors.append("Teléfono no válido (debe ser formato peruano)")
    
    # Validar email si está presente
    if 'email' in data and data['email']:
        if not validate_email(data['email']):
            errors.append("Email no válido")
    
    return len(errors) == 0, errors


def suggest_correction(input_text: str, valid_options: List[str]) -> Optional[str]:
    """
    Sugiere la opción más similar del catálogo.
    Usa distancia de Levenshtein simplificada.
    """
    input_lower = input_text.lower()
    best_match = None
    best_score = 0
    
    for option in valid_options:
        option_lower = option.lower()
        
        # Calcular similitud por caracteres comunes
        common_chars = sum(1 for c in input_lower if c in option_lower)
        similarity = common_chars / max(len(input_lower), len(option_lower))
        
        if similarity > best_score and similarity > 0.5:  # 50% similitud mínima
            best_score = similarity
            best_match = option
    
    return best_match


def format_validation_error(errors: List[str]) -> str:
    """
    Formatea errores de validación en mensaje amigable.
    """
    if not errors:
        return ""
    
    if len(errors) == 1:
        return f"⚠️ {errors[0]}"
    
    error_list = "\n".join([f"• {error}" for error in errors])
    return f"⚠️ Encontré algunos problemas:\n{error_list}"
