"""Sistema de transacciones con códigos únicos y validación."""

import json
import random
import string
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


class TransactionSystem:
    """Gestiona transacciones con códigos únicos, precios con expiración y verificación."""
    
    def __init__(self, storage_dir: str = "./transactions"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.transactions_file = self.storage_dir / "transactions.json"
        self.codes_file = self.storage_dir / "active_codes.json"
        
        self.transactions = self._load_transactions()
        self.active_codes = self._load_codes()
    
    def _load_transactions(self) -> List[Dict[str, Any]]:
        """Carga transacciones desde disco."""
        if not self.transactions_file.exists():
            return []
        
        try:
            with open(self.transactions_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    
    def _load_codes(self) -> Dict[str, Dict[str, Any]]:
        """Carga códigos activos desde disco."""
        if not self.codes_file.exists():
            return {}
        
        try:
            with open(self.codes_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def _save_transactions(self):
        """Guarda transacciones en disco."""
        with open(self.transactions_file, 'w', encoding='utf-8') as f:
            json.dump(self.transactions, f, ensure_ascii=False, indent=2)
    
    def _save_codes(self):
        """Guarda códigos activos en disco."""
        with open(self.codes_file, 'w', encoding='utf-8') as f:
            json.dump(self.active_codes, f, ensure_ascii=False, indent=2)
    
    def generate_unique_code(self) -> str:
        """Genera un código único alfanumérico."""
        while True:
            code = '#' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if code not in self.active_codes:
                return code
    
    def create_quotation(
        self,
        phone: str,
        material: str,
        estimated_kg: float,
        price_per_kg: float,
        valid_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Crea una cotización con código único y validez temporal.
        
        Returns:
            dict con code, price, expiration, total_estimated
        """
        code = self.generate_unique_code()
        now = datetime.now()
        expiration = now + timedelta(hours=valid_hours)
        
        quotation = {
            'code': code,
            'phone': phone,
            'material': material,
            'estimated_kg': estimated_kg,
            'price_per_kg': price_per_kg,
            'total_estimated': round(estimated_kg * price_per_kg, 2),
            'created_at': now.isoformat(),
            'expires_at': expiration.isoformat(),
            'status': 'pending',  # pending, photo_uploaded, completed, expired, cancelled
            'photo_url': None,
            'verified': False
        }
        
        self.active_codes[code] = quotation
        self._save_codes()
        
        return quotation
    
    def validate_code(self, code: str) -> tuple[bool, Optional[str]]:
        """
        Valida si un código existe y está vigente.
        
        Returns:
            (is_valid, error_message)
        """
        if code not in self.active_codes:
            return False, "Código no existe"
        
        quotation = self.active_codes[code]
        expiration = datetime.fromisoformat(quotation['expires_at'])
        
        if datetime.now() > expiration:
            quotation['status'] = 'expired'
            self._save_codes()
            return False, "Código expirado (válido 24h)"
        
        if quotation['status'] == 'completed':
            return False, "Código ya fue utilizado"
        
        return True, None
    
    def attach_photo_to_code(self, code: str, photo_url: str) -> tuple[bool, str]:
        """Asocia una foto a un código de cotización."""
        is_valid, error = self.validate_code(code)
        
        if not is_valid:
            return False, error or "Código inválido"
        
        self.active_codes[code]['photo_url'] = photo_url
        self.active_codes[code]['status'] = 'photo_uploaded'
        self.active_codes[code]['photo_uploaded_at'] = datetime.now().isoformat()
        self._save_codes()
        
        return True, "Foto verificada correctamente"
    
    def complete_transaction(
        self,
        code: str,
        actual_kg: float,
        payment_method: str,
        warehouse_id: str,
        final_photo_url: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Completa una transacción después del pesaje en bodega.
        
        Args:
            code: Código de la cotización
            actual_kg: Peso real medido
            payment_method: 'cash', 'yape', 'transfer', 'plin'
            warehouse_id: ID de la bodega donde se realizó
            final_photo_url: Foto del material pesado
            notes: Notas adicionales
        
        Returns:
            dict con detalles de la transacción completada
        """
        is_valid, error = self.validate_code(code)
        
        if not is_valid:
            raise ValueError(error)
        
        quotation = self.active_codes[code]
        
        # Calcular valores finales
        price_per_kg = quotation['price_per_kg']
        total_amount = round(actual_kg * price_per_kg, 2)
        weight_difference = round(actual_kg - quotation['estimated_kg'], 2)
        weight_difference_percent = round((weight_difference / quotation['estimated_kg']) * 100, 2)
        
        # Crear transacción completa
        transaction = {
            'transaction_id': f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}-{code[1:4]}",
            'code': code,
            'phone': quotation['phone'],
            'material': quotation['material'],
            'estimated_kg': quotation['estimated_kg'],
            'actual_kg': actual_kg,
            'weight_difference_kg': weight_difference,
            'weight_difference_percent': weight_difference_percent,
            'price_per_kg': price_per_kg,
            'total_amount': total_amount,
            'payment_method': payment_method,
            'warehouse_id': warehouse_id,
            'initial_photo_url': quotation.get('photo_url'),
            'final_photo_url': final_photo_url,
            'created_at': quotation['created_at'],
            'completed_at': datetime.now().isoformat(),
            'notes': notes,
            'status': 'completed'
        }
        
        # Actualizar código como completado
        self.active_codes[code]['status'] = 'completed'
        self.active_codes[code]['transaction_id'] = transaction['transaction_id']
        
        # Guardar transacción
        self.transactions.append(transaction)
        
        self._save_transactions()
        self._save_codes()
        
        return transaction
    
    def get_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene una transacción por su ID."""
        for txn in self.transactions:
            if txn['transaction_id'] == transaction_id:
                return txn
        return None
    
    def get_user_transactions(self, phone: str) -> List[Dict[str, Any]]:
        """Obtiene todas las transacciones de un usuario."""
        return [txn for txn in self.transactions if txn['phone'] == phone]
    
    def get_quotation_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Obtiene una cotización por su código."""
        return self.active_codes.get(code)
    
    def clean_expired_codes(self) -> int:
        """Limpia códigos expirados y retorna cantidad eliminada."""
        now = datetime.now()
        expired_count = 0
        
        codes_to_remove: List[str] = []
        for code, quotation in self.active_codes.items():
            expiration = datetime.fromisoformat(quotation['expires_at'])
            if now > expiration and quotation['status'] == 'pending':
                quotation['status'] = 'expired'
                codes_to_remove.append(code)
                expired_count += 1
        
        # Remover códigos expirados muy antiguos (más de 7 días)
        cutoff = now - timedelta(days=7)
        for code in codes_to_remove:
            expiration = datetime.fromisoformat(self.active_codes[code]['expires_at'])
            if expiration < cutoff:
                del self.active_codes[code]
        
        self._save_codes()
        return expired_count
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema de transacciones."""
        completed = [t for t in self.transactions if t['status'] == 'completed']
        
        total_volume_kg = sum(t['actual_kg'] for t in completed)
        total_value = sum(t['total_amount'] for t in completed)
        
        weight_errors = [abs(t['weight_difference_percent']) for t in completed]
        avg_weight_error = sum(weight_errors) / len(weight_errors) if weight_errors else 0
        
        payment_methods: Dict[str, int] = {}
        for t in completed:
            method = t['payment_method']
            payment_methods[method] = payment_methods.get(method, 0) + 1
        
        return {
            'total_transactions': len(completed),
            'total_volume_kg': round(total_volume_kg, 2),
            'total_volume_tons': round(total_volume_kg / 1000, 2),
            'total_value_soles': round(total_value, 2),
            'average_transaction_kg': round(total_volume_kg / len(completed), 2) if completed else 0,
            'average_weight_error_percent': round(avg_weight_error, 2),
            'payment_methods': payment_methods,
            'active_quotations': len([c for c in self.active_codes.values() if c['status'] == 'pending']),
            'pending_photos': len([c for c in self.active_codes.values() if c['status'] == 'photo_uploaded'])
        }


# Instancia global
transaction_system = TransactionSystem()
