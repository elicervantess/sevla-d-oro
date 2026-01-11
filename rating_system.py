"""Sistema de ratings, feedback y reputación de usuarios."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


class RatingSystem:
    """Gestiona ratings, feedback y sistema de reputación."""
    
    def __init__(self, storage_dir: str = "./ratings"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.ratings_file = self.storage_dir / "ratings.json"
        self.user_reputation_file = self.storage_dir / "reputation.json"
        
        self.ratings = self._load_ratings()
        self.reputation = self._load_reputation()
    
    def _load_ratings(self) -> List[Dict[str, Any]]:
        """Carga ratings desde disco."""
        if not self.ratings_file.exists():
            return []
        
        try:
            with open(self.ratings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    
    def _load_reputation(self) -> Dict[str, Dict[str, Any]]:
        """Carga reputación de usuarios desde disco."""
        if not self.user_reputation_file.exists():
            return {}
        
        try:
            with open(self.user_reputation_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def _save_ratings(self):
        """Guarda ratings en disco."""
        with open(self.ratings_file, 'w', encoding='utf-8') as f:
            json.dump(self.ratings, f, ensure_ascii=False, indent=2)
    
    def _save_reputation(self):
        """Guarda reputación en disco."""
        with open(self.user_reputation_file, 'w', encoding='utf-8') as f:
            json.dump(self.reputation, f, ensure_ascii=False, indent=2)
    
    def submit_rating(
        self,
        transaction_id: str,
        phone: str,
        stars: int,
        feedback: Optional[str] = None,
        categories: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """
        Registra un rating para una transacción.
        
        Args:
            transaction_id: ID de la transacción
            phone: Teléfono del usuario
            stars: Calificación 1-5 estrellas
            feedback: Comentario opcional
            categories: Ratings por categoría (ej: {'speed': 5, 'quality': 4, 'price': 5})
        
        Returns:
            dict con el rating creado
        """
        if not 1 <= stars <= 5:
            raise ValueError("Stars must be between 1 and 5")
        
        rating = {
            'rating_id': f"RAT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'transaction_id': transaction_id,
            'phone': phone,
            'stars': stars,
            'feedback': feedback,
            'categories': categories or {},
            'created_at': datetime.now().isoformat(),
            'helpful_count': 0
        }
        
        self.ratings.append(rating)
        self._save_ratings()
        
        # Actualizar reputación del usuario
        self._update_user_reputation(phone, stars)
        
        return rating
    
    def _update_user_reputation(self, phone: str, new_stars: int):
        """Actualiza la reputación de un usuario con un nuevo rating."""
        if phone not in self.reputation:
            self.reputation[phone] = {
                'phone': phone,
                'total_ratings': 0,
                'average_stars': 0.0,
                'stars_distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                'total_transactions': 0,
                'reward_level': 'bronze',  # bronze, silver, gold, platinum
                'bonus_percentage': 0.0,
                'last_updated': datetime.now().isoformat()
            }
        
        rep = self.reputation[phone]
        
        # Actualizar contadores
        rep['total_ratings'] += 1
        rep['stars_distribution'][new_stars] += 1
        
        # Recalcular promedio
        total_stars = sum(stars * count for stars, count in rep['stars_distribution'].items())
        rep['average_stars'] = round(total_stars / rep['total_ratings'], 2)
        
        # Actualizar nivel de recompensa
        rep['reward_level'] = self._calculate_reward_level(rep['total_ratings'], rep['average_stars'])
        rep['bonus_percentage'] = self._get_bonus_percentage(rep['reward_level'])
        rep['last_updated'] = datetime.now().isoformat()
        
        self._save_reputation()
    
    def _calculate_reward_level(self, total_ratings: int, avg_stars: float) -> str:
        """Calcula el nivel de recompensa basado en historial."""
        if total_ratings >= 50 and avg_stars >= 4.7:
            return 'platinum'
        elif total_ratings >= 25 and avg_stars >= 4.5:
            return 'gold'
        elif total_ratings >= 10 and avg_stars >= 4.0:
            return 'silver'
        else:
            return 'bronze'
    
    def _get_bonus_percentage(self, level: str) -> float:
        """Retorna el porcentaje de bonus según nivel."""
        bonuses = {
            'bronze': 0.0,
            'silver': 2.0,
            'gold': 5.0,
            'platinum': 8.0
        }
        return bonuses.get(level, 0.0)
    
    def get_user_reputation(self, phone: str) -> Dict[str, Any]:
        """Obtiene la reputación de un usuario."""
        if phone not in self.reputation:
            return {
                'phone': phone,
                'total_ratings': 0,
                'average_stars': 0.0,
                'reward_level': 'bronze',
                'bonus_percentage': 0.0,
                'message': 'Usuario nuevo - comienza a construir tu reputación'
            }
        
        return self.reputation[phone]
    
    def request_rating(self, transaction_id: str, phone: str) -> str:
        """
        Genera un mensaje para solicitar rating después de una transacción.
        
        Returns:
            Mensaje de solicitud de rating
        """
        rep = self.get_user_reputation(phone)
        
        message = f"""
✅ *Transacción completada exitosamente*

¿Cómo fue tu experiencia?

Califica de 1 a 5 estrellas:
⭐ - Muy mala
⭐⭐ - Mala
⭐⭐⭐ - Regular
⭐⭐⭐⭐ - Buena
⭐⭐⭐⭐⭐ - Excelente

Tu nivel actual: *{rep['reward_level'].upper()}* 🏆
Bonus en próximas ventas: *+{rep['bonus_percentage']}%*

Responde con el número de estrellas (1-5)
""".strip()
        
        return message
    
    def parse_rating_response(self, message: str) -> Optional[int]:
        """
        Parsea la respuesta del usuario para extraer rating.
        
        Returns:
            Número de estrellas (1-5) o None si no es válido
        """
        # Buscar número del 1 al 5
        for char in message:
            if char.isdigit():
                stars = int(char)
                if 1 <= stars <= 5:
                    return stars
        
        # Contar estrellas (⭐)
        star_count = message.count('⭐') or message.count('*')
        if 1 <= star_count <= 5:
            return star_count
        
        return None
    
    def get_incentive_message(self, phone: str) -> Optional[str]:
        """
        Genera mensaje de incentivo basado en reputación.
        
        Returns:
            Mensaje de incentivo o None
        """
        rep = self.get_user_reputation(phone)
        
        if rep['total_ratings'] == 0:
            return "🎁 *Primera transacción*: Completa tu venta y recibe un bonus de bienvenida"
        
        if rep['reward_level'] == 'bronze' and rep['total_ratings'] >= 5:
            return f"🥈 ¡Estás cerca de nivel SILVER! ({rep['total_ratings']}/10 transacciones)"
        
        if rep['reward_level'] == 'silver' and rep['total_ratings'] >= 15:
            return f"🥇 ¡A punto de nivel GOLD! ({rep['total_ratings']}/25 transacciones)"
        
        if rep['reward_level'] == 'gold' and rep['total_ratings'] >= 35:
            return f"💎 ¡Próximo a PLATINUM! ({rep['total_ratings']}/50 transacciones)"
        
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema de ratings."""
        if not self.ratings:
            return {
                'total_ratings': 0,
                'average_stars': 0.0,
                'satisfaction_rate': 0.0
            }
        
        total_stars = sum(r['stars'] for r in self.ratings)
        avg_stars = total_stars / len(self.ratings)
        
        satisfied = len([r for r in self.ratings if r['stars'] >= 4])
        satisfaction_rate = (satisfied / len(self.ratings)) * 100
        
        stars_distribution = {i: 0 for i in range(1, 6)}
        for rating in self.ratings:
            stars_distribution[rating['stars']] += 1
        
        levels_distribution = {
            'bronze': 0,
            'silver': 0,
            'gold': 0,
            'platinum': 0
        }
        for rep in self.reputation.values():
            levels_distribution[rep['reward_level']] += 1
        
        return {
            'total_ratings': len(self.ratings),
            'average_stars': round(avg_stars, 2),
            'satisfaction_rate': round(satisfaction_rate, 1),
            'stars_distribution': stars_distribution,
            'total_users_with_reputation': len(self.reputation),
            'reward_levels': levels_distribution,
            'ratings_last_7_days': len([r for r in self.ratings 
                if datetime.fromisoformat(r['created_at']) > datetime.now() - timedelta(days=7)])
        }


# Instancia global
rating_system = RatingSystem()
