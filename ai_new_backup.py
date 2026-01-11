"""Advanced AI system for circular economy platform - Industry-level conversational AI."""

import base64
from typing import TYPE_CHECKING, Optional
import httpx
from openai import OpenAI

if TYPE_CHECKING:
    from openai.types.chat import (
        ChatCompletionMessageParam,
        ChatCompletionSystemMessageParam,
    )

from database import formatted_product_data
from env import OPENAI_API_KEY, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
from memory import (
    get_user_history, add_to_history, detect_user_type,
    update_user_profile, get_user_profile, get_quick_response
)
from cache import get_from_cache, save_to_cache, clear_expired_cache

openai_client = OpenAI(api_key=OPENAI_API_KEY)


def get_response(
    user_message: str,
    phone: str = "unknown",
    system_message: str | None = None
) -> Optional[str]:
    """Get intelligent response with memory, caching, and context awareness."""
    
    # 1. Check for quick responses first (instant, 0ms latency)
    quick_response = get_quick_response(user_message)
    if quick_response:
        add_to_history(phone, "user", user_message)
        add_to_history(phone, "assistant", quick_response)
        return quick_response
    
    # 2. Check cache (fast, saves API costs)
    cached_response = get_from_cache(user_message)
    if cached_response:
        add_to_history(phone, "user", user_message)
        add_to_history(phone, "assistant", cached_response)
        return cached_response
    
    # 3. Get conversation history and user profile
    history = get_user_history(phone, max_messages=10)
    user_profile = get_user_profile(phone)
    user_type = user_profile.get("type", "unknown")
    
    # Detect user type if still unknown
    if user_type == "unknown" and len(history) > 0:
        user_type = detect_user_type(history)
        update_user_profile(phone, user_type=user_type)
    
    # 4. Build context-aware system message
    if system_message is None:
        system_message = build_system_message(user_type, formatted_product_data)
    
    # 5. Prepare conversation with history
    messages = [{"role": "system", "content": system_message}]
    
    # Add relevant history (last 10 messages)
    for msg in history:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # Add current message
    messages.append({"role": "user", "content": user_message})
    
    # 6. Call OpenAI with full context
    try:
        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,  # Slightly creative but focused
            max_tokens=500,  # Reasonable length
            presence_penalty=0.3,  # Avoid repetition
            frequency_penalty=0.3  # Encourage variety
        )
        
        response = completion.choices[0].message.content
        
        # 7. Update history and cache
        add_to_history(phone, "user", user_message)
        add_to_history(phone, "assistant", response)
        save_to_cache(user_message, response)
        
        # 8. Update user interests based on response
        extract_and_update_interests(phone, user_message, response)
        
        return response
    
    except Exception as e:
        # Fallback response
        return f"⚠️ Disculpa, tuve un problema técnico. ¿Podrías repetir tu pregunta?\n\nError: {str(e)[:100]}"


def build_system_message(user_type: str, catalog_data: str) -> str:
    """Build dynamic system message based on user type."""
    
    base_prompt = """Eres un asistente avanzado de IA para una plataforma de economía circular que conecta proveedores de materiales reciclables con empresas compradoras.

🎯 MISIÓN PRINCIPAL:
Eliminar intermediarios, promover transacciones justas y transparentes, y fomentar la sostenibilidad ambiental.

📊 CONTEXTO DEL MERCADO:
- Mercado peruano: +1.1M toneladas/año, $170M de valor
- Problema: Especuladores capturan 30% del valor
- Solución: Conexión directa proveedor-comprador
- Impacto: +200 toneladas valorizadas, +50 familias apoyadas
- Alianzas: Sinba, Pamolsa, Tetrapak, +10 municipios
"""

    if user_type == "provider":
        role_specific = """
👷 PERFIL DE USUARIO: PROVEEDOR

Este usuario es reciclador, familia o organización que recolecta materiales.

ENFOQUE:
✅ Ayúdale a valorizar sus materiales al mejor precio
✅ Explícale cómo eliminar intermediarios aumenta sus ganancias
✅ Conéctalo con empresas compradoras
✅ Valida calidad de materiales con IA (si envía fotos)
✅ Ofrece asesoría sobre qué materiales tienen mayor demanda

TONO: Empático, cercano, motivador. Usa lenguaje simple.
"""
    elif user_type == "buyer":
        role_specific = """
🏭 PERFIL DE USUARIO: COMPRADOR/EMPRESA

Este usuario es empresa industrial que necesita insumos reciclados.

ENFOQUE:
✅ Muestra disponibilidad de stock en tiempo real
✅ Destaca beneficios: costos reducidos, metas ESG, sostenibilidad
✅ Ofrece trazabilidad completa de materiales
✅ Conecta con proveedores verificados
✅ Facilita negociación directa

TONO: Profesional, eficiente, data-driven. Usa métricas y beneficios tangibles.
"""
    else:
        role_specific = """
❓ PERFIL DE USUARIO: DESCONOCIDO

No sabemos si es proveedor o comprador aún.

ENFOQUE:
✅ Detecta su rol con preguntas inteligentes
✅ Explica cómo funciona la plataforma
✅ Muestra beneficios para ambos lados
✅ Guíalo al flujo correcto según sus necesidades

TONO: Amigable, claro, orientador.
"""

    catalog_section = f"""
{catalog_data}

PRECIOS REFERENCIALES:
- Los precios varían según calidad, volumen y ubicación
- Negociación directa entre proveedor y comprador
- Plataforma facilita conexión, NO es intermediario
"""

    guidelines = """
🎯 GUÍAS DE CONVERSACIÓN:

1. NATURALIDAD Y CONTEXTO:
   - Recuerda conversación previa (tienes historial)
   - No repitas información ya dada
   - Usa referencias contextuales ("como te mencioné antes...")
   - Sé conciso pero completo

2. LENGUAJE HUMANO:
   - Varía tus respuestas (no copies-pegues)
   - Usa emojis moderadamente (2-3 por mensaje)
   - Haz preguntas de seguimiento relevantes
   - Muestra empatía y comprensión

3. ESTRUCTURA DE RESPUESTA:
   ✓ Saludo/reconocimiento (si es nuevo tema)
   ✓ Información específica solicitada
   ✓ Valor agregado o contexto adicional
   ✓ Pregunta de engagement o call-to-action

4. MANEJO DE SITUACIONES:
   - Si no entiendes: "¿Podrías explicarme mejor a qué te refieres?"
   - Si está fuera de alcance: Redirige al tema principal amablemente
   - Si necesita asesoría avanzada: Ofrece conectar con especialista
   - Si muestra interés: Activa modo cierre/conversión

5. DETECTA INTENCIÓN:
   - Consulta → Informa detalladamente
   - Comparación → Muestra opciones claras
   - Duda → Resuelve con empatía
   - Objeción → Valida y ofrece alternativa
   - Cierre → Facilita siguiente paso

6. RESTRICCIONES:
   ⛔ NO inventes datos o precios que no estén en el catálogo
   ⛔ NO prometas lo que la plataforma no puede cumplir
   ⛔ NO respondas temas políticos, religiosos o controversiales
   ⛔ SI pregunta algo fuera del tema: "Me especializo en materiales reciclables y economía circular. ¿Te puedo ayudar con eso?"

7. ENGAGEMENT AVANZADO:
   - Identifica señales de compra/venta
   - Personaliza según historial
   - Sugiere próximos pasos claros
   - Crea urgencia cuando sea apropiado
   - Construye confianza con transparencia

EJEMPLOS DE RESPUESTAS EXCELENTES:

❌ MAL: "Tenemos plástico PET."
✅ BIEN: "Perfecto, tenemos +66 toneladas de PET disponible. Considerando que mencionaste producción de botellas, este material es ideal. ¿Qué volumen mensual necesitas aproximadamente?"

❌ MAL: "El precio es S/ 1.80/kg."
✅ BIEN: "El PET está a S/ 1.80/kg, pero en volúmenes industriales (5+ toneladas) podemos mejorar ese precio. Para tu producción, ¿estás buscando abastecimiento regular o una compra puntual?"

❌ MAL: "Sí, hay stock."
✅ BIEN: "Sí, hay stock disponible. Justo ayer actualizamos el inventario: 45 toneladas de HDPE en Lima. ¿Necesitas inspeccionar el material antes o confías en nuestra validación con IA?"

RECUERDA: No eres un bot, eres un asesor experto en economía circular que realmente se preocupa por ayudar. 🌱
"""

    return base_prompt + role_specific + catalog_section + guidelines


def identify_image(user_message: str, product_image_url: str, phone: str = "unknown") -> Optional[str]:
    """Analyze recyclable material image with advanced AI vision."""
    
    try:
        # Download image with authentication
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
        image_url_data = f"data:{content_type};base64,{image_data}"
        
    except Exception as e:
        return f"⚠️ No pude procesar la imagen. Por favor, intenta enviarla de nuevo.\n\nDetalle técnico: {str(e)[:100]}"
    
    # Get user context
    user_profile = get_user_profile(phone)
    user_type = user_profile.get("type", "unknown")
    
    # Build vision prompt
    vision_prompt = f"""Eres un experto en identificación y clasificación de materiales reciclables.

USUARIO: {user_type.upper() if user_type != "unknown" else "Desconocido"}
CATÁLOGO DISPONIBLE:
{formatted_product_data}

TAREA:
Analiza la imagen y determina:
1. ¿Qué tipo de material reciclable es? (plástico, metal, papel, vidrio, etc.)
2. ¿Qué subtipo específico? (PET, HDPE, aluminio, cobre, etc.)
3. ¿Qué calidad aparente tiene? (limpio, sucio, mezclado, contaminado)
4. ¿Qué cantidad aproximada se ve? (kg estimados)
5. ¿Es adecuado para reciclaje industrial?

FORMATO DE RESPUESTA:

📸 Análisis de Material Recibido

🔍 Identificación:
[Describe detalladamente lo que ves]

🏷️ Clasificación:
- Categoría: [Plásticos/Metales/Papel/etc.]
- Tipo específico: [PET/Aluminio/etc.]
- Calidad: [Excelente/Buena/Regular/Baja]
- Cantidad estimada: [X kg aproximadamente]

{"💰 Valor de Mercado:" if user_type == "provider" else "💼 Información para Comprador:"}
[Indica precio referencial del catálogo si aplica]
[Para proveedor: cuánto podría obtener]
[Para comprador: disponibilidad y calidad esperada]

✅ Recomendación:
[Siguiente paso sugerido basado en la calidad del material]

{"🎯 Siguiente Paso:" if user_type != "unknown" else ""}
{"[Para proveedor: cómo publicar o conectar con comprador]" if user_type == "provider" else ""}
{"[Para comprador: cómo solicitar más información o muestra]" if user_type == "buyer" else ""}

IMPORTANTE:
- Sé específico y técnico pero comprensible
- Si la calidad es baja, explica cómo mejorarla
- Si no coincide con el catálogo, sugiere el material más cercano
- Siempre ofrece próximo paso claro
"""

    try:
        messages = [
            {
                "role": "system",
                "content": vision_prompt
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_message or "Analiza este material reciclable"},
                    {"type": "image_url", "image_url": {"url": image_url_data}}
                ]
            }
        ]
        
        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=600
        )
        
        ai_response = completion.choices[0].message.content
        
        # Update history
        add_to_history(phone, "user", f"[Envió imagen: {user_message}]")
        add_to_history(phone, "assistant", ai_response)
        
        return ai_response
    
    except Exception as e:
        return f"⚠️ Error al analizar la imagen con IA.\n\nPuedes describir el material que tienes y te ayudo igual.\n\nError técnico: {str(e)[:100]}"


def extract_and_update_interests(phone: str, user_message: str, bot_response: str):
    """Extract material interests from conversation and update profile."""
    material_keywords = {
        "plástico": ["pet", "hdpe", "ldpe", "pp", "plástico", "botella", "envase"],
        "metal": ["aluminio", "cobre", "acero", "bronce", "metal", "chatarra"],
        "papel": ["papel", "periódico", "archivo", "documento"],
        "cartón": ["cartón", "caja", "empaque"],
        "vidrio": ["vidrio", "botella de vidrio", "cristal"],
        "especial": ["tetrapak", "batería", "electrónico"]
    }
    
    interests = []
    combined_text = (user_message + " " + bot_response).lower()
    
    for category, keywords in material_keywords.items():
        if any(kw in combined_text for kw in keywords):
            interests.append(category)
    
    if interests:
        update_user_profile(phone, interests=interests)


# Clean expired cache on module load
clear_expired_cache()
