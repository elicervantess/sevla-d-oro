"""Conversation memory system with context awareness and intelligence."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class ConversationMemory:
    """Manages conversation history per user."""
    
    def __init__(self, storage_dir: str = "./conversations"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.active_sessions: Dict[str, List[Dict[str, str]]] = {}
        self.user_profiles: Dict[str, Dict[str, Any]] = {}
        self.message_hashes: Dict[str, List[Tuple[str, datetime]]] = {}  # Detect duplicates
        self.material_cart: Dict[str, List[str]] = {}  # Multi-material tracking
    
    def _get_user_file(self, phone: str) -> Path:
        """Get user conversation file path."""
        safe_phone = phone.replace('+', '').replace(':', '_')
        return self.storage_dir / f"{safe_phone}.json"
    
    def add_message(self, phone: str, role: str, content: str):
        """Add message to conversation history."""
        if phone not in self.active_sessions:
            self.active_sessions[phone] = self._load_history(phone)
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        self.active_sessions[phone].append(message)
        
        # Keep only last 20 messages
        if len(self.active_sessions[phone]) > 20:
            self.active_sessions[phone] = self.active_sessions[phone][-20:]
        
        # Save to disk periodically
        if len(self.active_sessions[phone]) % 5 == 0:
            self._save_history(phone)
    
    def get_context(self, phone: str, max_messages: int = 10) -> List[Dict[str, str]]:
        """Get recent conversation context."""
        if phone not in self.active_sessions:
            self.active_sessions[phone] = self._load_history(phone)
        
        # Return last N messages
        return self.active_sessions[phone][-max_messages:]
    
    def _load_history(self, phone: str) -> List[Dict[str, str]]:
        """Load conversation history from disk."""
        user_file = self._get_user_file(phone)
        
        if not user_file.exists():
            return []
        
        try:
            with open(user_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('messages', [])
        except Exception:
            return []
    
    def _save_history(self, phone: str):
        """Save conversation history to disk."""
        user_file = self._get_user_file(phone)
        
        data = {
            'phone': phone,
            'messages': self.active_sessions.get(phone, []),
            'last_updated': datetime.now().isoformat()
        }
        
        with open(user_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def detect_user_type(self, phone: str) -> str:
        """Detect if user is provider or buyer based on conversation."""
        context = self.get_context(phone)
        
        # Simple keyword detection
        all_text = " ".join([msg['content'].lower() for msg in context if msg['role'] == 'user'])
        
        provider_keywords = ['vender', 'vendo', 'tengo material', 'recolecto', 'ofrezco', 'proveedor']
        buyer_keywords = ['comprar', 'compro', 'necesito', 'busco material', 'empresa', 'fabrica']
        
        provider_score = sum(1 for kw in provider_keywords if kw in all_text)
        buyer_score = sum(1 for kw in buyer_keywords if kw in all_text)
        
        if provider_score > buyer_score:
            return "provider"
        elif buyer_score > provider_score:
            return "buyer"
        else:
            return "unknown"
    
    def get_user_profile(self, phone: str) -> Dict[str, Any]:
        """Get or create user profile."""
        if phone not in self.user_profiles:
            user_type = self.detect_user_type(phone)
            self.user_profiles[phone] = {
                'phone': phone,
                'type': user_type,
                'first_seen': datetime.now().isoformat(),
                'message_count': len(self.get_context(phone)),
                'materials_interested': [],
                'last_interaction': datetime.now().isoformat(),
                'needs_followup': False,
                'priority': 'normal'
            }
        
        # Update message count and last interaction
        self.user_profiles[phone]['message_count'] = len(self.get_context(phone))
        self.user_profiles[phone]['last_interaction'] = datetime.now().isoformat()
        
        return self.user_profiles[phone]
    
    def is_duplicate_message(self, phone: str, message: str) -> bool:
        """Check if user sent same message recently."""
        if phone not in self.message_hashes:
            self.message_hashes[phone] = []
        
        # Clean old hashes (>5 min)
        cutoff = datetime.now() - timedelta(minutes=5)
        self.message_hashes[phone] = [
            (msg, ts) for msg, ts in self.message_hashes[phone]
            if ts > cutoff
        ]
        
        # Check if message already sent
        for msg, _ in self.message_hashes[phone]:
            if msg.lower().strip() == message.lower().strip():
                # Same message in last 5 min
                return True
        
        # Add to history
        self.message_hashes[phone].append((message, datetime.now()))
        return False
    
    def add_material_to_cart(self, phone: str, material: str):
        """Track multiple materials user is interested in."""
        if phone not in self.material_cart:
            self.material_cart[phone] = []
        
        if material not in self.material_cart[phone]:
            self.material_cart[phone].append(material)
    
    def get_material_cart(self, phone: str) -> List[str]:
        """Get all materials user asked about."""
        return self.material_cart.get(phone, [])
    
    def get_contextual_suggestion(self, phone: str) -> Optional[str]:
        """Generate smart suggestion based on conversation context."""
        context = self.get_context(phone)
        if len(context) < 2:
            return None
        
        user_profile = self.get_user_profile(phone)
        user_type = user_profile.get('type', 'unknown')
        materials_cart = self.get_material_cart(phone)
        
        # Recent messages (last 3)
        recent = [msg['content'].lower() for msg in context[-3:] if msg['role'] == 'user']
        recent_text = ' '.join(recent)
        
        # Suggestion 1: If asked about price of one material, suggest others in category
        if 'precio' in recent_text and len(materials_cart) == 1:
            material = materials_cart[0]
            if 'PET' in material or 'HDPE' in material or 'PP' in material:
                return "💡 También tenemos otros plásticos (HDPE, PP, LDPE). ¿Te interesa ver sus precios?"
            elif 'Aluminio' in material or 'Cobre' in material:
                return "💡 También manejamos otros metales (Acero, Bronce). ¿Quieres saber más?"
        
        # Suggestion 2: If provider asked stock, suggest connecting with buyers
        if user_type == 'provider' and 'stock' in recent_text:
            return "💡 Tenemos compradores interesados en tu material. ¿Quieres que te conectemos?"
        
        # Suggestion 3: If buyer asked price, suggest volume discounts
        if user_type == 'buyer' and 'precio' in recent_text:
            return "💡 Manejamos descuentos por volumen. ¿Cuántas toneladas necesitas?"
        
        # Suggestion 4: If many materials asked, offer summary
        if len(materials_cart) >= 3:
            materials_str = ', '.join(materials_cart)
            return f"📋 Resumen: Te interesan {materials_str}. ¿Quieres un presupuesto consolidado?"
        
        # Suggestion 5: If long conversation without clear next step
        if len(context) >= 7:
            if user_type == 'provider':
                return "💡 ¿Ya decidiste? Puedo conectarte con compradores ahora mismo."
            elif user_type == 'buyer':
                return "💡 ¿Listo para comprar? Te ayudo a coordinar con proveedores."
        
        return None
    
    def set_priority(self, phone: str, priority: str):
        """Set user priority (normal, high, urgent)."""
        if phone in self.user_profiles:
            self.user_profiles[phone]['priority'] = priority
    
    def needs_followup(self, phone: str) -> bool:
        """Check if user needs follow-up message."""
        if phone not in self.user_profiles:
            return False
        
        profile = self.user_profiles[phone]
        last_interaction = datetime.fromisoformat(profile['last_interaction'])
        
        # Follow-up if last interaction was 2+ days ago and had interest
        time_diff = datetime.now() - last_interaction
        if time_diff.total_seconds() > 172800:  # 2 days
            if len(self.get_material_cart(phone)) > 0:
                return True
        
        return profile.get('needs_followup', False)
    
    def get_conversation_summary(self, phone: str) -> Dict[str, Any]:
        """Get summary of conversation for handoff to human."""
        context = self.get_context(phone, max_messages=20)
        profile = self.get_user_profile(phone)
        materials = self.get_material_cart(phone)
        
        return {
            'phone': phone,
            'user_type': profile['type'],
            'message_count': len(context),
            'materials_interested': materials,
            'first_seen': profile['first_seen'],
            'last_interaction': profile['last_interaction'],
            'priority': profile.get('priority', 'normal'),
            'conversation_preview': [
                f"{msg['role']}: {msg['content'][:100]}"
                for msg in context[-5:]
            ]
        }
    
    def clear_session(self, phone: str):
        """Clear active session (but keep disk history)."""
        if phone in self.active_sessions:
            self._save_history(phone)
            del self.active_sessions[phone]
    
    def get_stats(self) -> Dict[str, int]:
        """Get memory statistics."""
        total_users = len(list(self.storage_dir.glob('*.json')))
        active_sessions = len(self.active_sessions)
        total_messages = sum(len(msgs) for msgs in self.active_sessions.values())
        
        return {
            'total_users': total_users,
            'active_sessions': active_sessions,
            'total_messages_in_memory': total_messages
        }


# Global memory instance
memory = ConversationMemory()
