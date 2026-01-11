"""Sistema de monetización: comisiones, suscripciones y analytics."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List


class RevenueSystem:
    """Gestiona comisiones B2B, suscripciones premium y ventas de analytics."""
    
    def __init__(self, storage_dir: str = "./revenue"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.commissions_file = self.storage_dir / "commissions.json"
        self.subscriptions_file = self.storage_dir / "subscriptions.json"
        self.analytics_clients_file = self.storage_dir / "analytics_clients.json"
        
        self.commissions = self._load_commissions()
        self.subscriptions = self._load_subscriptions()
        self.analytics_clients = self._load_analytics_clients()
        
        # Configuración de comisiones por material (%)
        self.commission_rates = {
            'PET': 5.0,
            'HDPE': 5.5,
            'LDPE': 5.0,
            'PP': 5.5,
            'Aluminio': 7.0,
            'Cobre': 8.0,
            'Acero': 5.0,
            'Cartón': 4.5,
            'Papel': 4.5,
            'Vidrio': 5.0,
            'default': 5.0
        }
        
        # Planes de suscripción
        self.subscription_plans = {
            'basic': {
                'name': 'Básico',
                'price_usd': 50,
                'price_soles': 190,
                'features': [
                    'Acceso a inventario en tiempo real',
                    'Notificaciones de nuevos materiales',
                    'Soporte por email'
                ]
            },
            'professional': {
                'name': 'Profesional',
                'price_usd': 120,
                'price_soles': 450,
                'features': [
                    'Todo lo de Básico',
                    'Herramientas de forecasting',
                    'Proyecciones semanales',
                    'Alertas personalizadas',
                    'Soporte prioritario'
                ]
            },
            'enterprise': {
                'name': 'Empresarial',
                'price_usd': 200,
                'price_soles': 750,
                'features': [
                    'Todo lo de Profesional',
                    'API completa',
                    'Soporte dedicado 24/7',
                    'Descuentos en comisiones',
                    'Reportes personalizados'
                ]
            }
        }
    
    def _load_commissions(self) -> List[Dict[str, Any]]:
        """Carga comisiones desde disco."""
        if not self.commissions_file.exists():
            return []
        
        try:
            with open(self.commissions_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    
    def _load_subscriptions(self) -> List[Dict[str, Any]]:
        """Carga suscripciones desde disco."""
        if not self.subscriptions_file.exists():
            return []
        
        try:
            with open(self.subscriptions_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    
    def _load_analytics_clients(self) -> List[Dict[str, Any]]:
        """Carga clientes de analytics desde disco."""
        if not self.analytics_clients_file.exists():
            return []
        
        try:
            with open(self.analytics_clients_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    
    def _save_commissions(self):
        """Guarda comisiones en disco."""
        with open(self.commissions_file, 'w', encoding='utf-8') as f:
            json.dump(self.commissions, f, ensure_ascii=False, indent=2)
    
    def _save_subscriptions(self):
        """Guarda suscripciones en disco."""
        with open(self.subscriptions_file, 'w', encoding='utf-8') as f:
            json.dump(self.subscriptions, f, ensure_ascii=False, indent=2)
    
    def _save_analytics_clients(self):
        """Guarda clientes de analytics en disco."""
        with open(self.analytics_clients_file, 'w', encoding='utf-8') as f:
            json.dump(self.analytics_clients, f, ensure_ascii=False, indent=2)
    
    def calculate_commission(
        self,
        transaction_id: str,
        material: str,
        quantity_kg: float,
        provider_price: float,
        buyer_price: float
    ) -> Dict[str, Any]:
        """
        Calcula comisión B2B para una transacción.
        
        Args:
            transaction_id: ID de la transacción
            material: Tipo de material
            quantity_kg: Cantidad en kg
            provider_price: Precio pagado al proveedor (S/)
            buyer_price: Precio cobrado al comprador (S/)
        
        Returns:
            dict con desglose de comisión
        """
        # Obtener tasa de comisión
        commission_rate = self.commission_rates.get(material, self.commission_rates['default'])
        
        # Calcular valores
        total_provider = quantity_kg * provider_price
        total_buyer = quantity_kg * buyer_price
        spread = total_buyer - total_provider
        commission_amount = round(spread * (commission_rate / 100), 2)
        
        # Márgenes
        provider_margin = round(((buyer_price - provider_price) / provider_price) * 100, 2)
        
        commission_record = {
            'commission_id': f"COM-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'transaction_id': transaction_id,
            'material': material,
            'quantity_kg': quantity_kg,
            'provider_price_per_kg': provider_price,
            'buyer_price_per_kg': buyer_price,
            'total_provider_payment': round(total_provider, 2),
            'total_buyer_payment': round(total_buyer, 2),
            'spread': round(spread, 2),
            'commission_rate_percent': commission_rate,
            'commission_amount_soles': commission_amount,
            'provider_margin_percent': provider_margin,
            'created_at': datetime.now().isoformat(),
            'status': 'pending'  # pending, paid, disputed
        }
        
        self.commissions.append(commission_record)
        self._save_commissions()
        
        return commission_record
    
    def create_subscription(
        self,
        company_name: str,
        contact_phone: str,
        plan: str,
        duration_months: int = 1
    ) -> Dict[str, Any]:
        """
        Crea una suscripción premium.
        
        Args:
            company_name: Nombre de la empresa
            contact_phone: Teléfono de contacto
            plan: 'basic', 'professional', 'enterprise'
            duration_months: Duración en meses
        
        Returns:
            dict con detalles de suscripción
        """
        if plan not in self.subscription_plans:
            raise ValueError(f"Plan '{plan}' no existe")
        
        plan_info = self.subscription_plans[plan]
        start_date = datetime.now()
        end_date = start_date + timedelta(days=30 * duration_months)
        
        subscription = {
            'subscription_id': f"SUB-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'company_name': company_name,
            'contact_phone': contact_phone,
            'plan': plan,
            'plan_name': plan_info['name'],
            'price_per_month_soles': plan_info['price_soles'],
            'duration_months': duration_months,
            'total_amount_soles': plan_info['price_soles'] * duration_months,
            'features': plan_info['features'],
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'status': 'active',  # active, expired, cancelled
            'created_at': datetime.now().isoformat()
        }
        
        self.subscriptions.append(subscription)
        self._save_subscriptions()
        
        return subscription
    
    def create_analytics_client(
        self,
        client_name: str,
        client_type: str,
        contact_phone: str,
        price_per_month_soles: float,
        dashboards: List[str]
    ) -> Dict[str, Any]:
        """
        Crea un cliente de analytics (municipalidad, ONG, empresa logística).
        
        Args:
            client_name: Nombre del cliente
            client_type: 'municipality', 'ngo', 'logistics'
            contact_phone: Teléfono de contacto
            price_per_month_soles: Precio mensual personalizado
            dashboards: Lista de dashboards contratados
        
        Returns:
            dict con detalles del cliente
        """
        client = {
            'client_id': f"ANA-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'client_name': client_name,
            'client_type': client_type,
            'contact_phone': contact_phone,
            'price_per_month_soles': price_per_month_soles,
            'dashboards': dashboards,
            'start_date': datetime.now().isoformat(),
            'status': 'active',
            'created_at': datetime.now().isoformat()
        }
        
        self.analytics_clients.append(client)
        self._save_analytics_clients()
        
        return client
    
    def get_monthly_revenue(self, year: int, month: int) -> Dict[str, Any]:
        """
        Calcula ingresos totales por mes.
        
        Returns:
            dict con desglose de ingresos
        """
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        # Comisiones del mes
        month_commissions = [
            c for c in self.commissions
            if start_date <= datetime.fromisoformat(c['created_at']) < end_date
            and c['status'] == 'pending'
        ]
        
        commission_revenue = sum(c['commission_amount_soles'] for c in month_commissions)
        
        # Suscripciones activas
        active_subs = [
            s for s in self.subscriptions
            if s['status'] == 'active'
            and datetime.fromisoformat(s['start_date']) <= end_date
            and datetime.fromisoformat(s['end_date']) >= start_date
        ]
        
        subscription_revenue = sum(
            s['price_per_month_soles'] for s in active_subs
        )
        
        # Clientes analytics activos
        active_analytics = [
            c for c in self.analytics_clients
            if c['status'] == 'active'
            and datetime.fromisoformat(c['start_date']) <= end_date
        ]
        
        analytics_revenue = sum(
            c['price_per_month_soles'] for c in active_analytics
        )
        
        total_revenue = commission_revenue + subscription_revenue + analytics_revenue
        
        return {
            'year': year,
            'month': month,
            'commission_revenue_soles': round(commission_revenue, 2),
            'subscription_revenue_soles': round(subscription_revenue, 2),
            'analytics_revenue_soles': round(analytics_revenue, 2),
            'total_revenue_soles': round(total_revenue, 2),
            'commission_count': len(month_commissions),
            'active_subscriptions': len(active_subs),
            'active_analytics_clients': len(active_analytics),
            'revenue_breakdown_percent': {
                'commissions': round((commission_revenue / total_revenue * 100), 1) if total_revenue > 0 else 0,
                'subscriptions': round((subscription_revenue / total_revenue * 100), 1) if total_revenue > 0 else 0,
                'analytics': round((analytics_revenue / total_revenue * 100), 1) if total_revenue > 0 else 0
            }
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas generales del sistema de ingresos."""
        total_commission = sum(c['commission_amount_soles'] for c in self.commissions)
        
        active_subs = len([s for s in self.subscriptions if s['status'] == 'active'])
        active_analytics = len([c for c in self.analytics_clients if c['status'] == 'active'])
        
        # MRR (Monthly Recurring Revenue)
        mrr_subscriptions = sum(
            s['price_per_month_soles'] for s in self.subscriptions if s['status'] == 'active'
        )
        mrr_analytics = sum(
            c['price_per_month_soles'] for c in self.analytics_clients if c['status'] == 'active'
        )
        total_mrr = mrr_subscriptions + mrr_analytics
        
        return {
            'total_commissions': len(self.commissions),
            'total_commission_revenue_soles': round(total_commission, 2),
            'average_commission_soles': round(total_commission / len(self.commissions), 2) if self.commissions else 0,
            'active_subscriptions': active_subs,
            'total_subscriptions': len(self.subscriptions),
            'active_analytics_clients': active_analytics,
            'monthly_recurring_revenue_soles': round(total_mrr, 2),
            'mrr_breakdown': {
                'subscriptions': round(mrr_subscriptions, 2),
                'analytics': round(mrr_analytics, 2)
            }
        }


# Instancia global
revenue_system = RevenueSystem()
