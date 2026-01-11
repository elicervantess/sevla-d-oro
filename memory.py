"""Conversational memory and quick responses for circular economy bot."""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

# Almacenamiento en memoria de conversaciones
conversation_history: Dict[str, List[Dict[str, str]]] = {}
user_profiles: Dict[str, Dict[str, Any]] = {}

# Tiempo de expiración de memoria (30 minutos)
MEMORY_EXPIRATION = timedelta(minutes=30)
last_interaction: Dict[str, datetime] = {}


def clean_expired_memories():
    """Remove expired conversation memories."""
    now = datetime.now()
    expired_users = [
        user for user, last_time in last_interaction.items()
        if now - last_time > MEMORY_EXPIRATION
    ]
    for user in expired_users:
        conversation_history.pop(user, None)
        user_profiles.pop(user, None)
        last_interaction.pop(user, None)


def get_user_history(phone: str, max_messages: int = 10) -> List[Dict[str, str]]:
    """Get conversation history for user."""
    clean_expired_memories()
    return conversation_history.get(phone, [])[-max_messages:]


def add_to_history(phone: str, role: str, content: str):
    """Add message to conversation history."""
    if phone not in conversation_history:
        conversation_history[phone] = []
    
    conversation_history[phone].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })
    
    last_interaction[phone] = datetime.now()
    
    # Limitar a últimos 20 mensajes
    if len(conversation_history[phone]) > 20:
        conversation_history[phone] = conversation_history[phone][-20:]


def detect_user_type(message_history: List[Dict[str, str]]) -> str:
    """Detect if user is provider or buyer based on conversation."""
    all_text = " ".join([m["content"].lower() for m in message_history])
    
    # Keywords para proveedores
    provider_keywords = ["vender", "tengo", "ofrezco", "recolecto", "reciclador", 
                        "material", "stock", "disponible", "vendo"]
    
    # Keywords para compradores
    buyer_keywords = ["comprar", "necesito", "busco", "empresa", "fábrica",
                     "producción", "requiero", "compro"]
    
    provider_score = sum(1 for kw in provider_keywords if kw in all_text)
    buyer_score = sum(1 for kw in buyer_keywords if kw in all_text)
    
    if provider_score > buyer_score:
        return "provider"
    elif buyer_score > provider_score:
        return "buyer"
    return "unknown"


def update_user_profile(phone: str, user_type: Optional[str] = None, interests: Optional[List[str]] = None):
    """Update user profile."""
    if phone not in user_profiles:
        user_profiles[phone] = {
            "type": "unknown",
            "interests": [],
            "created": datetime.now().isoformat()
        }
    
    if user_type:
        user_profiles[phone]["type"] = user_type
    
    if interests:
        existing = set(user_profiles[phone]["interests"])
        existing.update(interests)
        user_profiles[phone]["interests"] = list(existing)
    
    user_profiles[phone]["last_updated"] = datetime.now().isoformat()


def get_user_profile(phone: str) -> Dict[str, Any]:
    """Get user profile."""
    return user_profiles.get(phone, {"type": "unknown", "interests": []})


# Respuestas predefinidas instantáneas
QUICK_RESPONSES = {
    "hola": """¡Hola! 👋 Bienvenido a nuestra plataforma de economía circular.

Conectamos proveedores de materiales reciclables con empresas compradoras, eliminando intermediarios y promoviendo sostenibilidad 🌱

¿Eres proveedor o comprador?
• Escribe PROVEEDOR si vendes materiales
• Escribe COMPRADOR si buscas insumos reciclados""",
    
    "menu": """📋 MENÚ PRINCIPAL

1️⃣ Ver catálogo de materiales
2️⃣ Consultar precios
3️⃣ ¿Cómo funciona?
4️⃣ Alianzas y beneficios
5️⃣ Hablar con asesor

Escribe el número o dime qué necesitas 👇""",
    
    "proveedor": """¡Perfecto! 🎯 Eres proveedor de materiales reciclables.

Con nosotros puedes:
✅ Publicar tus materiales disponibles
✅ Conectar con empresas compradoras
✅ Obtener precios justos (0% intermediarios)
✅ Recibir pagos seguros y rápidos

📦 Materiales que aceptamos:
• Plásticos (PET, HDPE, LDPE, PP)
• Metales (Aluminio, Cobre, Acero)
• Papel y Cartón
• Vidrio
• Tetrapak y especiales

¿Qué material tienes disponible?""",
    
    "comprador": """¡Excelente! 🏭 Eres empresa compradora.

Te ofrecemos:
✅ Acceso a +200 toneladas de materiales
✅ Precios competitivos sin intermediarios
✅ Calidad verificada con IA
✅ Trazabilidad completa
✅ Envíos a nivel nacional

🎯 ¿Qué material necesitas para tu producción?

Escribe el tipo (plásticos, metales, papel, etc.) o escribe CATÁLOGO para ver todo.""",
    
    "catalogo": """📦 CATÁLOGO DE MATERIALES DISPONIBLES

🔹 PLÁSTICOS (+66 toneladas)
   PET, HDPE, LDPE, PP
   S/ 1.50 - 2.20/kg

🔹 METALES (+80 toneladas)
   Aluminio, Cobre, Acero, Bronce
   S/ 1.20 - 22.00/kg

🔹 PAPEL (+96 toneladas)
   Blanco, Periódico
   S/ 0.45 - 0.80/kg

🔹 CARTÓN (85+ toneladas)
   Corrugado, Compacto
   S/ 0.60 - 0.70/kg

🔹 VIDRIO (55+ toneladas)
   Transparente, Color
   S/ 0.30 - 0.35/kg

Para detalles específicos, menciona el material que te interesa 👇""",
    
    "precios": """💰 LISTA DE PRECIOS

Los precios varían según:
• Calidad del material
• Volumen de compra
• Ubicación geográfica

📊 Rangos generales:
• Plásticos: S/ 1.50 - 2.20/kg
• Aluminio: S/ 5.50/kg
• Cobre: S/ 22.00/kg
• Papel: S/ 0.45 - 0.80/kg
• Vidrio: S/ 0.30 - 0.35/kg

Para cotización exacta:
1. Indícame el material
2. Cantidad que necesitas/tienes
3. Tu ubicación

¿Qué material te interesa?""",
    
    "como funciona": """🔄 ¿CÓMO FUNCIONA?

PARA PROVEEDORES:
1. Publicas tu material (tipo, cantidad)
2. Nuestra IA valida calidad
3. Te conectamos con compradores
4. Negocian precio directo
5. Reciben pago seguro

PARA COMPRADORES:
1. Buscas el material que necesitas
2. Comparas proveedores y precios
3. Contactas directamente al proveedor
4. Coordinan logística
5. Pagan de forma segura

✨ VENTAJAS:
• 0% intermediarios
• Precios justos
• Transacciones seguras
• Trazabilidad completa
• Impacto ambiental positivo

¿Tienes alguna pregunta específica?""",
    
    "beneficios": """🌟 BENEFICIOS DE LA PLATAFORMA

PARA PROVEEDORES 👷:
✅ Elimina especuladores (+30% más ganancias)
✅ Acceso a empresas grandes
✅ Pagos seguros y rápidos
✅ Apoyo de 10+ municipios
✅ Capacitación y herramientas

PARA COMPRADORES 🏭:
✅ Reduce costos de producción
✅ Cumple metas ESG y sostenibilidad
✅ Trazabilidad de materiales
✅ Red de +120 proveedores verificados
✅ Stock disponible 24/7

IMPACTO SOCIAL 🌱:
• +200 toneladas valorizadas
• +50 familias recicladoras apoyadas
• Alianzas con Sinba, Pamolsa, Tetrapak
• Movimiento hacia economía circular

¿Quieres empezar a operar?""",
    
    "ayuda": """🆘 CENTRO DE AYUDA

Puedo ayudarte con:
• Ver materiales disponibles
• Consultar precios específicos
• Registrarte como proveedor/comprador
• Conectarte con empresas
• Resolver dudas sobre el proceso

También puedes usar comandos:
/menu - Ver menú principal
/catalogo - Ver todos los materiales
/precios - Lista de precios
/contacto - Hablar con asesor

¿En qué específicamente te ayudo?"""
}

# Comandos especiales
SPECIAL_COMMANDS = {
    "/menu": "menu",
    "/catalogo": "catalogo",
    "/precios": "precios",
    "/ayuda": "ayuda",
    "/help": "ayuda",
    "/start": "hola",
    "/info": "como funciona",
    "/beneficios": "beneficios",
}


def get_quick_response(message: str) -> str | None:
    """Get predefined quick response if applicable."""
    msg_lower = message.lower().strip()
    
    # Check special commands first
    if msg_lower in SPECIAL_COMMANDS:
        return QUICK_RESPONSES.get(SPECIAL_COMMANDS[msg_lower])
    
    # Check for keywords in message
    for keyword, response in QUICK_RESPONSES.items():
        if keyword in msg_lower:
            return response
    
    return None
