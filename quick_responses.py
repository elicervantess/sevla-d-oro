"""Quick responses for common queries - Circular Economy Bot."""

QUICK_RESPONSES = {
    # Saludos y bienvenida
    "hola": """¡Hola! 👋 Soy tu asistente de economía circular.

Conectamos **proveedores de materiales reciclables** con **compradores industriales**, eliminando intermediarios y promoviendo la sostenibilidad.

¿Eres proveedor o comprador?
• Escribe PROVEEDOR si vendes materiales
• Escribe COMPRADOR si compras materiales
• Escribe MENÚ para ver opciones""",
    
    # Menú principal
    "menu": """📱 MENÚ PRINCIPAL

1️⃣ Ver **MATERIALES** disponibles
2️⃣ **PRECIOS** por categoría
3️⃣ Cómo **VENDER** materiales
4️⃣ Cómo **COMPRAR** materiales
5️⃣ **BENEFICIOS** de la plataforma
6️⃣ **CONTACTO** y soporte

Escribe el número o palabra clave""",
    
    # Proveedores
    "proveedor": """🌱 ¡Perfecto! Eres **PROVEEDOR**

Te ayudamos a vender tus materiales reciclables directamente a empresas, sin intermediarios.

**¿Qué materiales tienes?**
• Plásticos (PET, HDPE, PP, LDPE)
• Metales (Aluminio, Cobre, Acero)
• Papel y Cartón
• Vidrio
• Especiales (Tetrapak, RAEE)

Escribe la categoría o envía foto del material 📸""",
    
    # Compradores
    "comprador": """🏭 ¡Genial! Eres **COMPRADOR**

Conectamos tu empresa con +120 proveedores verificados.

**Stock disponible:**
📦 Plásticos: >66 toneladas
🔩 Metales: >80 toneladas  
📄 Papel/Cartón: >96 toneladas
🪟 Vidrio: >30 toneladas

**Beneficios:**
✓ Precios directos (sin intermediarios)
✓ Trazabilidad completa
✓ Calidad verificada
✓ Transacciones seguras

¿Qué material necesitas?""",
    
    # Materiales
    "materiales": """📦 MATERIALES DISPONIBLES

🔹 **PLÁSTICOS** (>66 ton)
   PET, HDPE, PP, LDPE
   
🔹 **METALES** (>80 ton)
   Aluminio, Cobre, Acero, Bronce
   
🔹 **PAPEL Y CARTÓN** (>96 ton)
   Papel blanco, Cartón corrugado
   
🔹 **VIDRIO** (>30 ton)
   Transparente, Color
   
🔹 **ESPECIALES**
   Tetrapak, RAEE, Baterías

Escribe la categoría para ver detalles y precios""",
    
    # Precios plásticos
    "precios plasticos": """💰 PRECIOS - PLÁSTICOS

🔹 **PET** (Botellas)
   S/ 1.80/kg | $1,650/ton
   Stock: >66 toneladas

🔹 **HDPE** (Envases)
   S/ 2.20/kg | $2,000/ton
   Stock: 45 toneladas

🔹 **PP** (Tapas)
   S/ 1.90/kg | $1,750/ton
   Stock: 52 toneladas

🔹 **LDPE** (Bolsas)
   S/ 1.50/kg | $1,400/ton
   Stock: 38 toneladas

¿Qué cantidad necesitas?""",
    
    # Precios metales
    "precios metales": """💰 PRECIOS - METALES

🔹 **Aluminio**
   S/ 5.50/kg | $5,200/ton
   Stock: >80 toneladas

🔹 **Cobre**
   S/ 22.00/kg | $20,500/ton
   Stock: 15 toneladas

🔹 **Acero/Hierro**
   S/ 1.20/kg | $1,100/ton
   Stock: >50 toneladas

🔹 **Bronce**
   S/ 12.00/kg | $11,000/ton
   Stock: 12 toneladas

¿Te interesa alguno?""",
    
    # Beneficios
    "beneficios": """✨ BENEFICIOS DE LA PLATAFORMA

**Para Proveedores:**
✓ Vende directo a empresas
✓ Elimina intermediarios (+30% más ganancia)
✓ Pagos seguros y rápidos
✓ Apoyo de +10 municipios

**Para Compradores:**
✓ Reduce costos hasta 40%
✓ Cumple metas ambientales
✓ Trazabilidad completa
✓ Calidad verificada con IA

**Impacto Social:**
🌱 >200 toneladas valorizadas
👨‍👩‍👧 +50 familias beneficiadas
🏘️ +10 distritos activos

¿Quieres empezar?""",
    
    # Cómo vender
    "vender": """📤 CÓMO VENDER MATERIALES

**Proceso simple en 4 pasos:**

1️⃣ **Registra tu material**
   Envía foto o describe qué tienes

2️⃣ **IA verifica calidad**
   Analizamos tipo, estado y precio justo

3️⃣ **Conectamos con compradores**
   Empresas interesadas te contactan

4️⃣ **Transacción segura**
   Pago directo, sin intermediarios

**¿Qué material tienes?**
Envía foto 📸 o describe""",
    
    # Cómo comprar
    "comprar": """📥 CÓMO COMPRAR MATERIALES

**Proceso rápido:**

1️⃣ **Dinos qué necesitas**
   Tipo de material y cantidad

2️⃣ **Vemos disponibilidad**
   Proveedores en tu zona

3️⃣ **Negociación directa**
   Sin intermediarios especuladores

4️⃣ **Entrega coordinada**
   Según tus necesidades

**¿Qué material buscas?**""",
    
    # Contacto
    "contacto": """📞 CONTACTO Y SOPORTE

**Atención inmediata:**
💬 WhatsApp: Este bot 24/7

**Equipo humano:**
📧 Email: soporte@plataforma.pe
📱 Tel: +51 XXX XXX XXX

**Ubicación:**
📍 Operamos en +10 distritos de Lima
🌎 Expansión LATAM en curso

**Aliados:**
🤝 Sinba, Pamolsa, Tetrapak
🏛️ Municipalidades comprometidas

¿En qué más puedo ayudarte?""",
    
    # Stats y logros
    "logros": """🏆 NUESTROS LOGROS

**Impacto Ambiental:**
♻️ +200 toneladas valorizadas
🌱 Cero especulación lograda
🌍 Economía circular activa

**Comunidad:**
👥 +500 usuarios activos
🏪 +120 proveedores
🏭 +20 empresas compradoras

**Cobertura:**
📍 +10 distritos Lima
💰 $5,000 en transacciones
📈 20% del mercado objetivo

**Visión 2026:**
🎯 Expansión nacional
🌎 Red LATAM-to-LATAM
🚀 Capturar mercado de $170M

¿Quieres ser parte?""",
}


def get_quick_response(user_message: str) -> str | None:
    """Check if message matches a quick response."""
    msg_lower = user_message.lower().strip()
    
    # Exact matches first
    if msg_lower in QUICK_RESPONSES:
        return QUICK_RESPONSES[msg_lower]
    
    # Partial matches
    for key, response in QUICK_RESPONSES.items():
        if key in msg_lower:
            return response
    
    return None


# Comandos especiales (empiezan con /)
SPECIAL_COMMANDS = {
    "/menu": lambda: QUICK_RESPONSES["menu"],
    "/ayuda": lambda: QUICK_RESPONSES["menu"],
    "/help": lambda: QUICK_RESPONSES["menu"],
    "/materiales": lambda: QUICK_RESPONSES["materiales"],
    "/precios": lambda: "Escribe: PRECIOS PLASTICOS, PRECIOS METALES, PRECIOS PAPEL",
    "/contacto": lambda: QUICK_RESPONSES["contacto"],
    "/logros": lambda: QUICK_RESPONSES["logros"],
    "/beneficios": lambda: QUICK_RESPONSES["beneficios"],
}


def handle_special_command(message: str) -> str | None:
    """Handle special commands starting with /."""
    if not message.startswith('/'):
        return None
    
    command = message.lower().strip()
    handler = SPECIAL_COMMANDS.get(command)
    
    if handler:
        return handler()
    
    return None
