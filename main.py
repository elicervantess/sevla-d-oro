"""Main API module for the chatbot."""

# ruff: noqa: N803 (Twilio API requires Capitalized variable names)
# ruff: noqa: B008 (fastapi makes use of reusable default function calls)

from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Form, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ai import get_response, identify_image
from audio_processor import audio_processor
from business_metrics import metrics
from rating_system import rating_system
from revenue_system import revenue_system
from transaction_system import transaction_system
from utils import logger
from warehouse_system import warehouse_system
from wsp import send_message

app = FastAPI(title="Selva d'Or - Circular Economy Platform", version="2.0.0")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation errors."""
    exc_str = f"{exc}".replace("\n", " ").replace("   ", " ")
    logger.error(f"{request}: {exc_str}")
    content = {"status_code": 10422, "message": exc_str, "data": None}
    return JSONResponse(
        content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"msg": "up & running"}


@app.post("/message")
def reply(
    From: str = Form(),
    Body: Optional[str] = Form(None),
    MediaUrl0: Optional[str] = Form(None),
    MediaContentType0: Optional[str] = Form(None),
    Latitude: Optional[str] = Form(None),
    Longitude: Optional[str] = Form(None),
) -> str:
    """Reply to a WhatsApp message from the user."""
    user_message = Body
    media_url = MediaUrl0
    media_type = MediaContentType0
    
    # Extract geolocation if available
    lat = float(Latitude) if Latitude else None
    lon = float(Longitude) if Longitude else None
    
    # ========== STEP 1: PROCESS AUDIO ==========
    if media_type and 'audio' in media_type.lower():
        logger.info(f"Processing audio message from {From}")
        if not media_url:
            send_message(From, "⚠️ No se pudo obtener el audio. Intenta de nuevo.")
            return "failure"
        
        transcribed_text = audio_processor.process_audio_message(media_url)
        
        if transcribed_text:
            send_message(From, f"🎤 Escuché: \"{transcribed_text}\"\n\nProcesando tu solicitud...")
            # Procesar el texto transcrito como mensaje normal
            chat_response = get_response(transcribed_text, phone=From)
            
            if chat_response:
                send_message(From, chat_response)
                return "success"
            else:
                send_message(From, "⚠️ Ocurrió un error procesando tu mensaje.")
                return "failure"
        else:
            send_message(From, "⚠️ No pude procesar el audio. Por favor, intenta enviarlo de nuevo o escribe tu mensaje.")
            return "failure"
    
    # ========== STEP 2: PROCESS IMAGE ==========
    if media_type and 'image' in media_type.lower() and media_url:
        logger.info(f"Processing image from {From}")
        
        if not user_message:
            user_message = "Analiza este material reciclable y dame precio"
        
        chat_response = identify_image(user_message, media_url, phone=From)
        
        if chat_response:
            send_message(From, chat_response)
            return "success"
        else:
            send_message(From, "⚠️ Error al analizar la imagen. ¿Puedes intentar con otra foto más clara?")
            return "failure"
    
    # ========== STEP 3: PROCESS TEXT ==========
    if not media_url and not user_message:
        logger.error("No message or media provided")
        return "failure"
    
    if user_message:
        logger.info(f"Replying to text message from {From}")
        
        # Check if it's a rating response
        stars = rating_system.parse_rating_response(user_message)
        if stars:
            user_transactions = transaction_system.get_user_transactions(From)
            if user_transactions:
                last_txn = user_transactions[-1]
                rating_system.submit_rating(
                    last_txn['transaction_id'],
                    From,
                    stars,
                    feedback=user_message if len(user_message) > 5 else None
                )
                rep = rating_system.get_user_reputation(From)
                response = f"""
✅ ¡Gracias por tu calificación de {stars} {'⭐' * stars}!

Tu nivel: *{rep['reward_level'].upper()}* 🏆
Bonus en próximas ventas: *+{rep['bonus_percentage']}%*

¿En qué más puedo ayudarte?
""".strip()
                send_message(From, response)
                return "success"
        
        # Get AI response
        chat_response = get_response(user_message, phone=From)

        if chat_response:
            # Add geolocation context if available
            if lat and lon:
                logger.info(f"Location received: {lat}, {lon}")
            
            send_message(From, chat_response)
            return "success"
        else:
            logger.error("Failed to get AI response")
            send_message(From, "⚠️ Ocurrió un error temporal. ¿Puedes repetir tu consulta?")
            return "failure"
    
    return "failure"


# === TRANSACTION & QUOTATION ENDPOINTS ===

@app.post("/create-quotation")
async def create_quotation_endpoint(
    phone: str = Form(),
    material: str = Form(),
    estimated_kg: float = Form(),
    price_per_kg: float = Form()
) -> JSONResponse:
    """Create a quotation with unique code."""
    try:
        quotation = transaction_system.create_quotation(
            phone=phone,
            material=material,
            estimated_kg=estimated_kg,
            price_per_kg=price_per_kg
        )
        
        message = f"""
📋 *COTIZACIÓN GENERADA*

Código: *{quotation['code']}*
Material: {material}
Cantidad estimada: {estimated_kg} kg
Precio: S/ {price_per_kg}/kg
Total estimado: S/ {quotation['total_estimated']}

⏰ Válido hasta: {datetime.fromisoformat(quotation['expires_at']).strftime('%d/%m/%Y %H:%M')}

📸 *Siguiente paso:*
Envía una foto de tu material con el código {quotation['code']} visible para verificar.
""".strip()
        
        send_message(phone, message)
        return JSONResponse(content=quotation, status_code=200)
        
    except Exception as e:
        logger.error(f"Error creating quotation: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/quotation/{code}")
async def get_quotation(code: str) -> JSONResponse:
    """Get quotation by code."""
    quotation = transaction_system.get_quotation_by_code(code)
    
    if not quotation:
        return JSONResponse(content={"error": "Código no encontrado"}, status_code=404)
    
    return JSONResponse(content=quotation, status_code=200)


@app.post("/complete-transaction")
async def complete_transaction_endpoint(
    code: str = Form(),
    actual_kg: float = Form(),
    payment_method: str = Form(),
    warehouse_id: str = Form(),
    final_photo_url: Optional[str] = Form(None),
    notes: Optional[str] = Form(None)
) -> JSONResponse:
    """Complete a transaction after weighing at warehouse."""
    try:
        transaction = transaction_system.complete_transaction(
            code=code,
            actual_kg=actual_kg,
            payment_method=payment_method,
            warehouse_id=warehouse_id,
            final_photo_url=final_photo_url,
            notes=notes
        )
        
        quotation = transaction_system.get_quotation_by_code(code)
        if not quotation:
            return JSONResponse(content={"error": "Cotización no encontrada"}, status_code=404)
        
        phone: str = str(quotation.get('phone', ''))
        
        # Calculate commission
        provider_price = transaction['price_per_kg']
        buyer_price = provider_price * 1.07  # 7% markup for buyer
        
        commission = revenue_system.calculate_commission(
            transaction_id=transaction['transaction_id'],
            material=transaction['material'],
            quantity_kg=actual_kg,
            provider_price=provider_price,
            buyer_price=buyer_price
        )
        
        # Track metrics
        duration_minutes = 0  # Initialize
        created_at_str = quotation.get('created_at', '')
        completed_at_str = transaction.get('completed_at', '')
        if created_at_str and completed_at_str:
            start_time = datetime.fromisoformat(str(created_at_str))
            end_time = datetime.fromisoformat(str(completed_at_str))
            duration_minutes = (end_time - start_time).total_seconds() / 60
        
        # Update warehouse load
        warehouse_system.update_warehouse_load(warehouse_id, actual_kg)
        
        # Track transaction time metric
        if duration_minutes > 0:
            metrics.track_transaction_time(duration_minutes)
        
        # Send confirmation and request rating
        confirmation_msg = f"""
✅ *TRANSACCIÓN COMPLETADA*

ID: {transaction['transaction_id']}
Material: {transaction['material']}
Peso: {actual_kg} kg
Total pagado: S/ {transaction['total_amount']}
Método: {payment_method}

📍 Bodega: {warehouse_id}
⏱️ Tiempo total: {int(duration_minutes)} minutos
""".strip()
        
        send_message(phone, confirmation_msg)
        
        # Request rating
        rating_msg = rating_system.request_rating(transaction['transaction_id'], phone)
        send_message(phone, rating_msg)
        
        return JSONResponse(content={
            'transaction': transaction,
            'commission': commission
        }, status_code=200)
        
    except Exception as e:
        logger.error(f"Error completing transaction: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


# === WAREHOUSE & GEOLOCATION ENDPOINTS ===

@app.post("/assign-warehouse")
async def assign_warehouse_endpoint(
    phone: str = Form(),
    code: str = Form(),
    latitude: float = Form(),
    longitude: float = Form(),
    material: str = Form(),
    estimated_kg: float = Form()
) -> JSONResponse:
    """Assign nearest warehouse to user."""
    try:
        assignment = warehouse_system.assign_warehouse(
            phone=phone,
            code=code,
            latitude=latitude,
            longitude=longitude,
            material=material,
            estimated_kg=estimated_kg
        )
        
        if not assignment:
            return JSONResponse(
                content={"error": "No hay bodegas disponibles cerca"},
                status_code=404
            )
        
        message = f"""
📍 *BODEGA ASIGNADA*

🏪 {assignment['warehouse_name']}
📌 {assignment['warehouse_address']}
📞 {assignment['warehouse_phone']}

📏 Distancia: {assignment['distance_km']} km
⏰ Horario: {assignment['opening_hours']}

*Instrucciones:*
1. Muestra este mensaje al llegar
2. Código de verificación: {code}
3. Lleva tu material para pesaje

¿Necesitas indicaciones para llegar?
""".strip()
        
        send_message(phone, message)
        return JSONResponse(content=assignment, status_code=200)
        
    except Exception as e:
        logger.error(f"Error assigning warehouse: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/warehouses/near")
async def get_nearby_warehouses(
    lat: float,
    lon: float,
    material: str,
    max_distance: float = 5.0
) -> JSONResponse:
    """Find nearby warehouses."""
    warehouses = warehouse_system.find_nearest_warehouses(
        latitude=lat,
        longitude=lon,
        material=material,
        max_distance_km=max_distance
    )
    
    return JSONResponse(content=warehouses, status_code=200)


# === RATING & FEEDBACK ENDPOINTS ===

@app.post("/submit-rating")
async def submit_rating_endpoint(
    transaction_id: str = Form(),
    phone: str = Form(),
    stars: int = Form(),
    feedback: Optional[str] = Form(None)
) -> JSONResponse:
    """Submit a rating for a transaction."""
    try:
        rating = rating_system.submit_rating(
            transaction_id=transaction_id,
            phone=phone,
            stars=stars,
            feedback=feedback
        )
        
        rep = rating_system.get_user_reputation(phone)
        
        message = f"""
✅ ¡Gracias por tu calificación!

Tu nivel: *{rep['reward_level'].upper()}* 🏆
Promedio: {rep['average_stars']} ⭐
Bonus: +{rep['bonus_percentage']}% en próximas ventas

Sigue así para desbloquear más beneficios!
""".strip()
        
        send_message(phone, message)
        return JSONResponse(content=rating, status_code=200)
        
    except Exception as e:
        logger.error(f"Error submitting rating: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/reputation/{phone}")
async def get_reputation(phone: str) -> JSONResponse:
    """Get user reputation."""
    reputation = rating_system.get_user_reputation(phone)
    return JSONResponse(content=reputation, status_code=200)


# === DASHBOARD & ANALYTICS ENDPOINTS ===

@app.get("/dashboard")
async def get_dashboard() -> JSONResponse:
    """Get comprehensive dashboard with all metrics."""
    dashboard = {
        'business_metrics': metrics.get_dashboard_stats(),
        'kpis': metrics.get_kpis(),
        'transactions': transaction_system.get_statistics(),
        'warehouses': warehouse_system.get_statistics(),
        'ratings': rating_system.get_statistics(),
        'revenue': revenue_system.get_statistics(),
        'timestamp': datetime.now().isoformat()
    }
    
    return JSONResponse(content=dashboard, status_code=200)


@app.get("/revenue/monthly/{year}/{month}")
async def get_monthly_revenue(year: int, month: int) -> JSONResponse:
    """Get monthly revenue breakdown."""
    revenue = revenue_system.get_monthly_revenue(year, month)
    return JSONResponse(content=revenue, status_code=200)


@app.get("/transactions/user/{phone}")
async def get_user_transactions(phone: str) -> JSONResponse:
    """Get all transactions for a user."""
    transactions = transaction_system.get_user_transactions(phone)
    return JSONResponse(content=transactions, status_code=200)
