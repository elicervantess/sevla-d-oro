"""Business metrics tracking and analytics."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class BusinessMetrics:
    """Tracks business KPIs and user behavior."""
    
    def __init__(self, storage_dir: str = "./metrics"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.metrics_file = self.storage_dir / "business_metrics.json"
        self.leads_file = self.storage_dir / "leads.json"
        
        # Load existing metrics
        self.metrics = self._load_metrics()
        self.leads = self._load_leads()
    
    def _load_metrics(self) -> Dict[str, Any]:
        """Load metrics from disk."""
        if not self.metrics_file.exists():
            return self._initialize_metrics()
        
        try:
            with open(self.metrics_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return self._initialize_metrics()
    
    def _initialize_metrics(self) -> Dict[str, Any]:
        """Initialize empty metrics structure."""
        return {
            'total_conversations': 0,
            'total_messages': 0,
            'providers_count': 0,
            'buyers_count': 0,
            'unknown_count': 0,
            'materials_consulted': {},
            'intents_detected': {},
            'hot_leads': [],
            'conversion_funnel': {
                'inquiry': 0,
                'negotiation': 0,
                'closed': 0
            },
            'response_times': [],
            'last_updated': datetime.now().isoformat()
        }
    
    def _load_leads(self) -> List[Dict[str, Any]]:
        """Load leads from disk."""
        if not self.leads_file.exists():
            return []
        
        try:
            with open(self.leads_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    
    def _save_metrics(self):
        """Save metrics to disk."""
        self.metrics['last_updated'] = datetime.now().isoformat()
        with open(self.metrics_file, 'w', encoding='utf-8') as f:
            json.dump(self.metrics, f, ensure_ascii=False, indent=2)
    
    def _save_leads(self):
        """Save leads to disk."""
        with open(self.leads_file, 'w', encoding='utf-8') as f:
            json.dump(self.leads, f, ensure_ascii=False, indent=2)
    
    def track_message(self, phone: str, user_type: str, intents: List[str]):
        """Track a new message."""
        self.metrics['total_messages'] += 1
        
        # Track intents
        for intent in intents:
            if intent not in self.metrics['intents_detected']:
                self.metrics['intents_detected'][intent] = 0
            self.metrics['intents_detected'][intent] += 1
        
        self._save_metrics()
    
    def track_conversation_start(self, phone: str, user_type: str):
        """Track new conversation."""
        self.metrics['total_conversations'] += 1
        
        if user_type == 'provider':
            self.metrics['providers_count'] += 1
        elif user_type == 'buyer':
            self.metrics['buyers_count'] += 1
        else:
            self.metrics['unknown_count'] += 1
        
        self._save_metrics()
    
    def track_material_inquiry(self, phone: str, materials: List[str]):
        """Track material consultation."""
        for material in materials:
            if material not in self.metrics['materials_consulted']:
                self.metrics['materials_consulted'][material] = 0
            self.metrics['materials_consulted'][material] += 1
        
        # Update conversion funnel
        self.metrics['conversion_funnel']['inquiry'] += 1
        
        self._save_metrics()
    
    def track_lead(self, phone: str, user_type: str, materials: List[str], 
                   quantity: Optional[Dict[str, Any]] = None, 
                   is_hot: bool = False):
        """Track a new lead."""
        lead = {
            'phone': phone,
            'user_type': user_type,
            'materials': materials,
            'quantity': quantity,
            'is_hot': is_hot,
            'timestamp': datetime.now().isoformat(),
            'status': 'new'
        }
        
        # Check if lead already exists
        existing_lead = next((l for l in self.leads if l['phone'] == phone), None)
        if existing_lead:
            # Update existing lead
            existing_lead.update(lead)
        else:
            self.leads.append(lead)
        
        # Track hot lead
        if is_hot and phone not in self.metrics['hot_leads']:
            self.metrics['hot_leads'].append(phone)
        
        self._save_leads()
        self._save_metrics()
    
    def track_negotiation(self, phone: str):
        """Track when user enters negotiation phase."""
        self.metrics['conversion_funnel']['negotiation'] += 1
        
        # Update lead status
        lead = next((l for l in self.leads if l['phone'] == phone), None)
        if lead:
            lead['status'] = 'negotiating'
            self._save_leads()
        
        self._save_metrics()
    
    def track_close(self, phone: str, success: bool = True):
        """Track closed deal."""
        self.metrics['conversion_funnel']['closed'] += 1
        
        # Update lead status
        lead = next((l for l in self.leads if l['phone'] == phone), None)
        if lead:
            lead['status'] = 'closed' if success else 'lost'
            lead['closed_at'] = datetime.now().isoformat()
            self._save_leads()
        
        self._save_metrics()
    
    def track_response_time(self, duration_seconds: float):
        """Track bot response time."""
        self.metrics['response_times'].append(duration_seconds)
        
        # Keep only last 1000 response times
        if len(self.metrics['response_times']) > 1000:
            self.metrics['response_times'] = self.metrics['response_times'][-1000:]
        
        self._save_metrics()
    
    def get_top_materials(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most consulted materials."""
        materials = self.metrics['materials_consulted']
        sorted_materials = sorted(materials.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {'material': mat, 'count': count}
            for mat, count in sorted_materials[:limit]
        ]
    
    def get_conversion_rate(self) -> Dict[str, float]:
        """Calculate conversion rates."""
        funnel = self.metrics['conversion_funnel']
        
        inquiry_to_negotiation = 0.0
        if funnel['inquiry'] > 0:
            inquiry_to_negotiation = (funnel['negotiation'] / funnel['inquiry']) * 100
        
        negotiation_to_close = 0.0
        if funnel['negotiation'] > 0:
            negotiation_to_close = (funnel['closed'] / funnel['negotiation']) * 100
        
        overall = 0.0
        if funnel['inquiry'] > 0:
            overall = (funnel['closed'] / funnel['inquiry']) * 100
        
        return {
            'inquiry_to_negotiation': round(inquiry_to_negotiation, 2),
            'negotiation_to_close': round(negotiation_to_close, 2),
            'overall': round(overall, 2)
        }
    
    def get_avg_response_time(self) -> float:
        """Get average response time in seconds."""
        times = self.metrics['response_times']
        if not times:
            return 0.0
        return round(sum(times) / len(times), 2)
    
    def get_hot_leads(self) -> List[Dict[str, Any]]:
        """Get all hot leads."""
        return [lead for lead in self.leads if lead.get('is_hot', False)]
    
    def get_dashboard(self) -> Dict[str, Any]:
        """Get complete dashboard metrics."""
        return {
            'overview': {
                'total_conversations': self.metrics['total_conversations'],
                'total_messages': self.metrics['total_messages'],
                'providers': self.metrics['providers_count'],
                'buyers': self.metrics['buyers_count'],
                'unknown': self.metrics['unknown_count']
            },
            'top_materials': self.get_top_materials(5),
            'conversion_rates': self.get_conversion_rate(),
            'avg_response_time': self.get_avg_response_time(),
            'hot_leads_count': len(self.get_hot_leads()),
            'funnel': self.metrics['conversion_funnel'],
            'top_intents': sorted(
                self.metrics['intents_detected'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }
    
    def should_escalate_to_human(self, phone: str, message_count: int, 
                                  has_urgent: bool = False) -> bool:
        """Determine if conversation should be escalated to human."""
        # Escalate if >5 messages without clear resolution
        if message_count > 5:
            return True
        
        # Escalate if urgent sentiment detected
        if has_urgent:
            return True
        
        # Escalate if hot lead
        if phone in self.metrics['hot_leads']:
            return True
        
        return False
    
    def is_hot_lead(self, quantity: Optional[Dict[str, Any]], 
                     message_count: int, intents: List[str]) -> bool:
        """Determine if this is a hot lead."""
        # Hot if quantity >10 toneladas
        if quantity and quantity.get('toneladas', 0) >= 10:
            return True
        
        # Hot if many messages indicating serious interest
        if message_count >= 5 and ('comprar' in intents or 'vender' in intents):
            return True
        
        # Hot if mentions specific business needs
        business_intents = {'comprar', 'vender', 'precio', 'stock', 'proceso'}
        if len(set(intents) & business_intents) >= 3:
            return True
        
        return False


# Global metrics instance
metrics = BusinessMetrics()
