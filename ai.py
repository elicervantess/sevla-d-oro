"""Advanced AI system for Circular Economy Platform - Industry Grade."""

import base64
import time
from typing import Any, Dict, List, Optional

import httpx
from openai import OpenAI

from database import formatted_product_data
from env import OPENAI_API_KEY, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
from cache_system import cache
from conversation_memory import memory
from quick_responses import get_quick_response, handle_special_command
from intent_detector import analyze_message
from input_validator import normalize_quantity
from business_metrics import metrics
from utils import logger

openai_client = OpenAI(api_key=OPENAI_API_KEY)


def get_response(
    user_message: str,
    phone: str = "unknown",
    system_message: Optional[str] = None,
) -> Optional[str]:
    """
    Get AI response with advanced features:
    - Intent detection & sentiment analysis
    - Conversation memory & context
    - Smart suggestions
    - Duplicate detection
    - Business metrics tracking
    """
    start_time = time.time()
    
    # 0. Analyze message (intents, sentiment, materials, quantities)
    analysis = analyze_message(user_message)
    intents = analysis['intents']
    materials = analysis['materials']
    quantities = analysis['quantities']
    corrected_text = analysis['corrected']
    
    # Show autocorrections if any
    if analysis['corrections']:
        corrections_msg = ", ".join(analysis['corrections'])
        logger.info(f"Autocorrected: {corrections_msg} for {phone}")
    
    # Check for duplicate message
    if memory.is_duplicate_message(phone, user_message):
        context = memory.get_context(phone)
        if len(context) >= 2:
            last_response = context[-1]['content'] if context[-1]['role'] == 'assistant' else None
            if last_response:
                return f"Ya te respondí hace un momento:\n\n{last_response}\n\n¿Necesitas algo más?"
    
    # Track materials in cart
    for material in materials:
        memory.add_material_to_cart(phone, material)
    
    # 1. Handle special commands first
    special_response = handle_special_command(corrected_text)
    if special_response:
        logger.info(f"Special command handled: {corrected_text} for {phone}")
        metrics.track_message(phone, memory.get_user_profile(phone)['type'], intents)
        return special_response
    
    # 2. Check quick responses (instant, no AI needed)
    quick_response = get_quick_response(corrected_text)
    if quick_response:
        logger.info(f"Quick response used for: {corrected_text[:50]}... (phone: {phone})")
        memory.add_message(phone, "user", corrected_text)
        memory.add_message(phone, "assistant", quick_response)
        metrics.track_message(phone, memory.get_user_profile(phone)['type'], intents)
        return quick_response
    
    # 3. Check cache (for AI responses)
    cached_response = cache.get(corrected_text)
    if cached_response:
        logger.info(f"Cache hit for: {corrected_text[:50]}... (phone: {phone})")
        memory.add_message(phone, "user", corrected_text)
        memory.add_message(phone, "assistant", cached_response)
        metrics.track_message(phone, memory.get_user_profile(phone)['type'], intents)
        
        # Add contextual suggestion
        suggestion = memory.get_contextual_suggestion(phone)
        if suggestion:
            return f"{cached_response}\n\n{suggestion}"
        return cached_response
    
    # 4. Get conversation context
    context = memory.get_context(phone, max_messages=10)
    user_profile = memory.get_user_profile(phone)
    
    # Track material inquiry
    if materials:
        metrics.track_material_inquiry(phone, materials)
    
    # Check if hot lead
    normalized_qty = None
    if quantities:
        qty = quantities[0]
        normalized_qty = normalize_quantity(qty['value'], qty['unit'])
    
    is_hot = metrics.is_hot_lead(normalized_qty, len(context), intents)
    if is_hot:
        memory.set_priority(phone, 'high')
        metrics.track_lead(phone, user_profile['type'], materials, normalized_qty, is_hot=True)
        logger.info(f"🔥 HOT LEAD detected: {phone} - {materials} - {normalized_qty}")
    
    # Check if should escalate to human
    should_escalate = metrics.should_escalate_to_human(
        phone, 
        len(context), 
        analysis['sentiment']['urgent']
    )
    if should_escalate:
        logger.info(f"⚠️ Escalating to human: {phone}")
    
    # 5. Build system message if not provided
    if system_message is None:
        system_message = build_system_message(user_profile, analysis)
    
    # 6. Prepare messages for OpenAI
    messages = [{"role": "system", "content": system_message}]
    
    # Add conversation history
    for msg in context:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # Add current message
    messages.append({
        "role": "user",
        "content": user_message
    })
    
    # 7. Call OpenAI with retry logic
    try:
        response_text = call_openai_with_retry(messages)
        
        # 8. Save to memory and cache
        memory.add_message(phone, "user", corrected_text)
        memory.add_message(phone, "assistant", response_text)
        cache.set(corrected_text, response_text)
        
        # 9. Track metrics
        duration = time.time() - start_time
        metrics.track_message(phone, user_profile['type'], intents)
        metrics.track_response_time(duration)
        
        logger.info(
            f"AI response generated for {phone} "
            f"(type: {user_profile['type']}, duration: {duration:.2f}s, "
            f"intents: {intents})"
        )
        
        # 10. Add contextual suggestion
        suggestion = memory.get_contextual_suggestion(phone)
        if suggestion:
            response_text = f"{response_text}\n\n{suggestion}"
        
        return response_text
        
    except Exception as e:
        logger.error(f"AI response failed for {phone}: {str(e)}")
        return "⚠️ Disculpa, ocurrió un error temporal. ¿Puedes repetir tu consulta?"


def call_openai_with_retry(messages: List[Dict[str, Any]]) -> str:
    """Call OpenAI API with automatic retry on failures."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            completion = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,  # type: ignore
                temperature=0.7,
                max_tokens=500,
            )
            return completion.choices[0].message.content or ""
            
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"OpenAI retry attempt {attempt + 1}: {str(e)}")
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                logger.error(f"OpenAI failed after {max_retries} attempts: {str(e)}")
                raise
    
    return ""  # Fallback (nunca debería llegar aquí)


def build_system_message(user_profile: Dict[str, Any], analysis: Optional[Dict[str, Any]] = None) -> str:
    """Build dynamic system message based on user profile and message analysis."""
    
    user_type = user_profile.get('type', 'unknown')
    
    # Add intent-specific guidance
    intent_guidance = ""
    if analysis and analysis.get('intents'):
        intents = analysis['intents']
        if 'precio' in intents:
            intent_guidance = "\n🎯 Usuario pregunta por PRECIOS. Sé específico con valores de catálogo."
        elif 'stock' in intents:
            intent_guidance = "\n🎯 Usuario pregunta por STOCK. Menciona cantidades disponibles."
        elif 'proceso' in intents:
            intent_guidance = "\n🎯 Usuario pregunta CÓMO FUNCIONA. Explica paso a paso."
        elif 'urgente' in intents or (analysis.get('sentiment', {}).get('urgent')):
            intent_guidance = "\n🚨 URGENTE: Usuario tiene prisa. Responde directo y ofrece contacto inmediato."
    
    base_message = f"""Eres un asistente inteligente de una plataforma de economía circular que conecta proveedores de materiales reciclables con compradores industriales en Perú y LATAM.

🎯 MISIÓN PRINCIPAL:
Eliminar intermediarios especuladores, promover comercio justo, y fomentar sostenibilidad ambiental.

👤 PERFIL DEL USUARIO: {user_type.upper()}
{get_user_type_context(user_type)}{intent_guidance}

📊 CONTEXTO DEL MERCADO:
- Más de 1,100,000 toneladas/año de reciclables en Perú
- Mercado de $170 millones con oportunidades globales de $100 mil millones
- +20,000 empresas en el sector, pero alta informalidad
- Intermediarios capturan hasta 30% del valor (¡nosotros eliminamos esto!)

✨ LOGROS DE LA PLATAFORMA:
- +200 toneladas valorizadas
- +50 familias recicladoras beneficiadas
- +120 proveedores activos
- +20 empresas compradoras conectadas
- +10 distritos con alianzas municipales
- 0% especulación garantizada

{formatted_product_data}

🗣️ ESTILO DE COMUNICACIÓN:
- SÉ HUMANO: conversacional, empático, profesional
- SÉ CONCISO: máximo 3 párrafos por respuesta
- USA EMOJIS: moderadamente (máx 3 por mensaje)
- ENGAGEMENT: siempre termina con pregunta o call-to-action
- DETECTA INTENCIÓN: si habla de vender/comprar, guía el proceso
- EDUCATIVO: explica beneficios de economía circular

⚠️ RESTRICCIÓN CRÍTICA:
SOLO responde sobre materiales reciclables, economía circular, sostenibilidad y la plataforma.
Si preguntan sobre otros temas: "Lo siento, soy especialista en materiales reciclables y economía circular. ¿Te puedo ayudar con eso?"

📋 INFORMACIÓN CLAVE A DESTACAR:
- Stock disponible: Plásticos (66+ ton), Metales (80+ ton), Papel (96+ ton)
- Precios justos sin intermediarios
- Trazabilidad con IA
- Transacciones seguras
- Impacto social y ambiental real

🎯 OBJETIVOS:
1. Identificar si usuario es proveedor o comprador
2. Conectar oferta con demanda
3. Educar sobre economía circular
4. Facilitar transacciones justas
5. Promover sostenibilidad

RECUERDA: Cada conversación es una oportunidad para:
- Eliminar un intermediario especulador
- Ayudar a una familia recicladora
- Reducir la huella de carbono de una empresa
- Construir una economía más circular y justa"""

    return base_message


def get_user_type_context(user_type: str) -> str:
    """Get context text based on user type."""
    contexts = {
        "provider": """El usuario es un PROVEEDOR (reciclador, familia, organización).
        
Enfoque:
- Mostrar cómo vender directo a empresas
- Destacar eliminación de intermediarios (+30% más ganancia)
- Explicar proceso simple de registro
- Ofrecer análisis de material con IA (si envía foto)
- Mencionar apoyo municipal y pagos seguros""",
        
        "buyer": """El usuario es un COMPRADOR (empresa industrial, fabricante).
        
Enfoque:
- Mostrar disponibilidad de materiales
- Destacar reducción de costos (hasta 40%)
- Explicar calidad verificada con IA
- Ofrecer trazabilidad completa
- Mencionar cumplimiento de metas ESG""",
        
        "unknown": """Tipo de usuario AÚN NO IDENTIFICADO.
        
Tarea prioritaria:
- Hacer preguntas para identificar si es proveedor o comprador
- Ej: "¿Tienes materiales para vender o estás buscando comprar?"
- Ser amigable y educativo sobre la plataforma"""
    }
    
    return contexts.get(user_type, contexts["unknown"])


def identify_image(user_message: str, product_image_url: str, phone: str = "unknown") -> Optional[str]:
    """
    Analyze recyclable material images with AI Vision.
    Identifies material type, quality, estimated weight, and fair price.
    """
    start_time = time.time()
    
    # Download image from Twilio
    try:
        auth = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        response = httpx.get(
            product_image_url,
            auth=auth,
            timeout=30.0,
            follow_redirects=True
        )
        response.raise_for_status()
        
        # Convert to base64
        image_data = base64.b64encode(response.content).decode("utf-8")
        content_type = response.headers.get("content-type", "image/jpeg")
        
        # Validate image type
        if not any(img_type in content_type for img_type in ['image/jpeg', 'image/png', 'image/webp']):
            logger.warning(f"Invalid image type: {content_type}")
            return "⚠️ Formato de imagen no válido. Por favor envía JPG, PNG o WEBP."
        
        image_url_data = f"data:{content_type};base64,{image_data}"
        
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error downloading image for {phone}: {e.response.status_code}")
        return "⚠️ No pude descargar la imagen. Por favor, intenta enviarla de nuevo."
    except Exception as e:
        logger.error(f"Image download failed for {phone}: {str(e)}")
        return "⚠️ Error al descargar la imagen. ¿Puedes intentar enviarla de nuevo?"
    
    # Get user profile for context
    user_profile = memory.get_user_profile(phone)
    
    # Build vision system message
    system_message = f"""Eres un experto en identificación de materiales reciclables con IA.

USUARIO: {user_profile.get('type', 'unknown').upper()}

TU TAREA:
Analiza la imagen y proporciona:
1. Tipo exacto de material (PET, HDPE, aluminio, cartón, etc.)
2. Calidad visual (excelente/buena/regular/mala)
3. Cantidad estimada (si es visible)
4. Precio justo según nuestro catálogo
5. Recomendaciones para el usuario

{formatted_product_data}

FORMATO DE RESPUESTA:

📸 **Análisis de Imagen**

🔍 **Material:** [Nombre - Ej: PET o Aluminio]

✨ **Calidad:** [Excelente/Buena/Regular/Mala + breve razón]

⚖️ **Cantidad:** [Si visible: "~X kg", sino: "No visible"]

💰 **Precio:** S/ [X.XX]/kg

📋 **Recomendaciones:**
• [Consejo específico 1]
• [Consejo específico 2]

{get_next_steps_for_user_type(user_profile.get('type', 'unknown'))}

IMPORTANTE:
- Si NO es reciclable: indica claramente
- Si calidad es mala: sé honesto pero constructivo
- Siempre da el precio justo (revisa catálogo arriba)
- Termina con pregunta o acción clara
- Sé breve y preciso (máximo 200 palabras)"""
    
    # Call OpenAI Vision
    try:
        messages = [
            {"role": "system", "content": system_message},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_message or "Analiza este material reciclable"},
                    {"type": "image_url", "image_url": {"url": image_url_data, "detail": "auto"}}
                ]
            }
        ]
        
        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,  # type: ignore
            max_tokens=500,
            temperature=0.7
        )
        
        result = completion.choices[0].message.content
        
        if not result:
            return "⚠️ No pude analizar la imagen. Por favor, intenta con otra foto."
        
        # Log analytics
        duration = time.time() - start_time
        logger.info(
            f"✅ Image analysis completed for {phone} "
            f"(type: {user_profile['type']}, duration: {duration:.2f}s)"
        )
        
        # Save to memory
        memory.add_message(phone, "user", f"[Imagen enviada: {user_message}]")
        memory.add_message(phone, "assistant", result)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Image analysis failed for {phone}: {str(e)}")
        return "⚠️ Error al analizar la imagen. ¿Puedes intentar con otra foto más clara?"


def get_next_steps_for_user_type(user_type: str) -> str:
    """Get contextual next steps based on user type."""
    steps = {
        "provider": """
🚀 **Próximos Pasos para Vender:**
1. Confirma cantidad disponible
2. Te conectamos con compradores interesados
3. Negociación directa (sin intermediarios)
4. Pago seguro al entregar

¿Cuánto material tienes disponible?""",
        
        "buyer": """
🚀 **Próximos Pasos para Comprar:**
1. Confirma cantidad que necesitas
2. Verificamos disponibilidad en tu zona
3. Conectamos con proveedores
4. Coordinamos entrega

¿Cuántas toneladas necesitas?""",
        
        "unknown": """
¿Tienes este material para **vender** o estás buscando **comprar**?"""
    }
    
    return steps.get(user_type, steps["unknown"])
