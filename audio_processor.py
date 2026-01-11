"""Procesamiento de mensajes de audio de WhatsApp."""

import base64
import logging
from typing import Dict, Optional, Any

import httpx
from openai import OpenAI

from env import OPENAI_API_KEY, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN

logger = logging.getLogger(__name__)
openai_client = OpenAI(api_key=OPENAI_API_KEY)


class AudioProcessor:
    """Procesa audios de WhatsApp y los transcribe a texto."""
    
    def __init__(self):
        self.supported_formats = ['.ogg', '.opus', '.mp3', '.m4a', '.wav']
    
    def download_audio(self, audio_url: str) -> Optional[bytes]:
        """
        Descarga el archivo de audio desde Twilio.
        
        Args:
            audio_url: URL del archivo de audio de Twilio
        
        Returns:
            bytes del archivo de audio o None si falla
        """
        try:
            auth_str = f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}"
            auth_bytes = auth_str.encode('utf-8')
            auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
            
            headers = {
                'Authorization': f'Basic {auth_b64}'
            }
            
            # Seguir redirects (Twilio usa 307 para redirigir a CloudFront)
            response = httpx.get(audio_url, headers=headers, timeout=30.0, follow_redirects=True)
            response.raise_for_status()
            
            logger.info(f"Audio downloaded successfully: {len(response.content)} bytes")
            return response.content
            
        except Exception as e:
            logger.error(f"Error downloading audio: {str(e)}")
            return None
    
    def transcribe_audio(self, audio_bytes: bytes, filename: str = "audio.ogg") -> Optional[str]:
        """
        Transcribe audio usando OpenAI Whisper API.
        
        Args:
            audio_bytes: bytes del archivo de audio
            filename: nombre del archivo (para determinar formato)
        
        Returns:
            Texto transcrito o None si falla
        """
        try:
            # Crear archivo temporal en memoria
            from io import BytesIO
            audio_file = BytesIO(audio_bytes)
            audio_file.name = filename
            
            # Transcribir con Whisper
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="es",  # Español
                response_format="text"
            )
            
            transcribed_text = transcript.strip() if isinstance(transcript, str) else transcript.text.strip()
            
            logger.info(f"Audio transcribed: '{transcribed_text[:100]}...'")
            return transcribed_text
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            return None
    
    def process_audio_message(self, audio_url: str) -> Optional[str]:
        """
        Procesa un mensaje de audio completo: descarga y transcribe.
        
        Args:
            audio_url: URL del audio de Twilio
        
        Returns:
            Texto transcrito o None si falla
        """
        logger.info(f"Processing audio message from: {audio_url}")
        
        # Descargar audio
        audio_bytes = self.download_audio(audio_url)
        if not audio_bytes:
            return None
        
        # Determinar formato
        filename = "audio.ogg"  # WhatsApp usa .ogg por defecto
        if 'MediaContentType' in audio_url:
            if 'opus' in audio_url.lower():
                filename = "audio.opus"
            elif 'mp3' in audio_url.lower():
                filename = "audio.mp3"
            elif 'm4a' in audio_url.lower():
                filename = "audio.m4a"
        
        # Transcribir
        transcribed_text = self.transcribe_audio(audio_bytes, filename)
        
        return transcribed_text
    
    def extract_intent_from_audio(self, transcribed_text: str) -> Dict[str, Any]:
        """
        Analiza el texto transcrito para extraer intención y datos clave.
        
        Returns:
            dict con: intents, materials, quantities, sentiment
        """
        from intent_detector import analyze_message
        
        # Usar el analizador existente
        analysis = analyze_message(transcribed_text)
        
        # Agregar flag de que vino de audio
        analysis['source'] = 'audio'
        analysis['original_text'] = transcribed_text
        
        logger.info(f"Audio intent analysis: {analysis['intents']}, materials: {analysis['materials']}")
        
        return analysis


# Instancia global
audio_processor = AudioProcessor()
