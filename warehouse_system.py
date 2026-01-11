"""Sistema de bodegas, geolocalización y asignación de puntos de recogida."""

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class WarehouseSystem:
    """Gestiona bodegas, geolocalización y asignación de puntos de recogida."""
    
    def __init__(self, storage_dir: str = "./warehouses"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.warehouses_file = self.storage_dir / "warehouses.json"
        self.assignments_file = self.storage_dir / "assignments.json"
        
        self.warehouses = self._load_warehouses()
        self.assignments = self._load_assignments()
    
    def _load_warehouses(self) -> List[Dict[str, Any]]:
        """Carga bodegas desde disco."""
        if not self.warehouses_file.exists():
            return self._initialize_default_warehouses()
        
        try:
            with open(self.warehouses_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return self._initialize_default_warehouses()
    
    def _initialize_default_warehouses(self) -> List[Dict[str, Any]]:
        """Inicializa bodegas de ejemplo en Lima."""
        default_warehouses = [
            {
                'warehouse_id': 'WH001',
                'name': 'Bodega San Juan de Lurigancho',
                'address': 'Av. Próceres de la Independencia 1245',
                'district': 'San Juan de Lurigancho',
                'latitude': -11.9932,
                'longitude': -76.9942,
                'capacity_kg': 5000,
                'current_load_kg': 1200,
                'opening_hour': '06:00',
                'closing_hour': '20:00',
                'phone': '+51987654321',
                'active': True,
                'materials_accepted': ['PET', 'HDPE', 'LDPE', 'PP', 'Cartón', 'Papel', 'Vidrio']
            },
            {
                'warehouse_id': 'WH002',
                'name': 'Bodega Villa El Salvador',
                'address': 'Av. El Sol 892',
                'district': 'Villa El Salvador',
                'latitude': -12.2122,
                'longitude': -76.9392,
                'capacity_kg': 3000,
                'current_load_kg': 800,
                'opening_hour': '07:00',
                'closing_hour': '19:00',
                'phone': '+51987654322',
                'active': True,
                'materials_accepted': ['PET', 'Aluminio', 'Acero', 'Cobre', 'Cartón']
            },
            {
                'warehouse_id': 'WH003',
                'name': 'Bodega Ate Vitarte',
                'address': 'Av. Nicolás Ayllón 3456',
                'district': 'Ate',
                'latitude': -12.0464,
                'longitude': -76.9378,
                'capacity_kg': 4000,
                'current_load_kg': 2100,
                'opening_hour': '06:00',
                'closing_hour': '20:00',
                'phone': '+51987654323',
                'active': True,
                'materials_accepted': ['PET', 'HDPE', 'PP', 'Cartón', 'Papel', 'Vidrio', 'Aluminio']
            },
            {
                'warehouse_id': 'WH004',
                'name': 'Bodega Comas',
                'address': 'Av. Túpac Amaru Km 10.5',
                'district': 'Comas',
                'latitude': -11.9389,
                'longitude': -77.0528,
                'capacity_kg': 3500,
                'current_load_kg': 900,
                'opening_hour': '06:30',
                'closing_hour': '19:30',
                'phone': '+51987654324',
                'active': True,
                'materials_accepted': ['PET', 'HDPE', 'LDPE', 'Cartón', 'Papel']
            },
            {
                'warehouse_id': 'WH005',
                'name': 'Bodega Villa María del Triunfo',
                'address': 'Av. Pachacútec 2890',
                'district': 'Villa María del Triunfo',
                'latitude': -12.1592,
                'longitude': -76.9414,
                'capacity_kg': 2500,
                'current_load_kg': 600,
                'opening_hour': '07:00',
                'closing_hour': '18:00',
                'phone': '+51987654325',
                'active': True,
                'materials_accepted': ['PET', 'HDPE', 'Cartón', 'Vidrio']
            }
        ]
        
        self._save_warehouses(default_warehouses)
        return default_warehouses
    
    def _load_assignments(self) -> List[Dict[str, Any]]:
        """Carga asignaciones desde disco."""
        if not self.assignments_file.exists():
            return []
        
        try:
            with open(self.assignments_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    
    def _save_warehouses(self, warehouses: Optional[List[Dict[str, Any]]] = None):
        """Guarda bodegas en disco."""
        data = warehouses if warehouses is not None else self.warehouses
        with open(self.warehouses_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _save_assignments(self):
        """Guarda asignaciones en disco."""
        with open(self.assignments_file, 'w', encoding='utf-8') as f:
            json.dump(self.assignments, f, ensure_ascii=False, indent=2)
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calcula distancia en km entre dos puntos usando fórmula de Haversine.
        
        Returns:
            Distancia en kilómetros
        """
        R = 6371  # Radio de la Tierra en km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        distance = R * c
        return round(distance, 2)
    
    def find_nearest_warehouses(
        self,
        latitude: float,
        longitude: float,
        material: str,
        max_distance_km: float = 5.0,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Encuentra las bodegas más cercanas que acepten el material.
        
        Args:
            latitude: Latitud del usuario
            longitude: Longitud del usuario
            material: Tipo de material
            max_distance_km: Distancia máxima en km
            limit: Número máximo de bodegas a retornar
        
        Returns:
            Lista de bodegas ordenadas por distancia
        """
        candidates: List[Dict[str, Any]] = []
        
        for warehouse in self.warehouses:
            if not warehouse['active']:
                continue
            
            # Verificar si acepta el material
            if material not in warehouse['materials_accepted']:
                continue
            
            # Verificar capacidad (no asignar si está >90% llena)
            utilization = warehouse['current_load_kg'] / warehouse['capacity_kg']
            if utilization > 0.90:
                continue
            
            # Calcular distancia
            distance = self.calculate_distance(
                latitude, longitude,
                warehouse['latitude'], warehouse['longitude']
            )
            
            if distance <= max_distance_km:
                warehouse_info: Dict[str, Any] = warehouse.copy()
                warehouse_info['distance_km'] = distance
                candidates.append(warehouse_info)
        
        # Ordenar por distancia
        candidates_sorted: List[Dict[str, Any]] = sorted(
            candidates, 
            key=lambda x: float(x.get('distance_km', 999.0))
        )
        
        return candidates_sorted[:limit]
    
    def assign_warehouse(
        self,
        phone: str,
        code: str,
        latitude: float,
        longitude: float,
        material: str,
        estimated_kg: float
    ) -> Optional[Dict[str, Any]]:
        """
        Asigna una bodega óptima al usuario.
        
        Returns:
            dict con información de la bodega asignada y detalles
        """
        warehouses = self.find_nearest_warehouses(latitude, longitude, material)
        
        if not warehouses:
            return None
        
        # Seleccionar la primera (más cercana con capacidad)
        assigned = warehouses[0]
        
        # Crear asignación
        assignment = {
            'assignment_id': f"ASG-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'phone': phone,
            'code': code,
            'warehouse_id': assigned['warehouse_id'],
            'warehouse_name': assigned['name'],
            'warehouse_address': assigned['address'],
            'warehouse_phone': assigned['phone'],
            'distance_km': assigned['distance_km'],
            'material': material,
            'estimated_kg': estimated_kg,
            'user_latitude': latitude,
            'user_longitude': longitude,
            'assigned_at': datetime.now().isoformat(),
            'status': 'assigned',  # assigned, arrived, completed, cancelled
            'opening_hours': f"{assigned['opening_hour']} - {assigned['closing_hour']}"
        }
        
        self.assignments.append(assignment)
        self._save_assignments()
        
        return assignment
    
    def is_warehouse_open(self, warehouse_id: str) -> bool:
        """Verifica si una bodega está abierta en este momento."""
        warehouse = next((w for w in self.warehouses if w['warehouse_id'] == warehouse_id), None)
        
        if not warehouse:
            return False
        
        now = datetime.now().time()
        opening = datetime.strptime(warehouse['opening_hour'], '%H:%M').time()
        closing = datetime.strptime(warehouse['closing_hour'], '%H:%M').time()
        
        return opening <= now <= closing
    
    def update_warehouse_load(self, warehouse_id: str, kg_change: float):
        """Actualiza la carga actual de una bodega."""
        for warehouse in self.warehouses:
            if warehouse['warehouse_id'] == warehouse_id:
                warehouse['current_load_kg'] += kg_change
                warehouse['current_load_kg'] = max(0, warehouse['current_load_kg'])
                self._save_warehouses()
                break
    
    def get_warehouse_by_id(self, warehouse_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene información de una bodega por su ID."""
        return next((w for w in self.warehouses if w['warehouse_id'] == warehouse_id), None)
    
    def get_assignment(self, phone: str, code: str) -> Optional[Dict[str, Any]]:
        """Obtiene la asignación de bodega para un código."""
        for assignment in reversed(self.assignments):  # Más reciente primero
            if assignment['phone'] == phone and assignment['code'] == code:
                return assignment
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema de bodegas."""
        total_capacity = sum(w['capacity_kg'] for w in self.warehouses if w['active'])
        total_load = sum(w['current_load_kg'] for w in self.warehouses if w['active'])
        
        active_warehouses = len([w for w in self.warehouses if w['active']])
        
        assignments_by_status: Dict[str, int] = {}
        for assignment in self.assignments:
            status = assignment['status']
            assignments_by_status[status] = assignments_by_status.get(status, 0) + 1
        
        return {
            'active_warehouses': active_warehouses,
            'total_capacity_kg': total_capacity,
            'total_capacity_tons': round(total_capacity / 1000, 2),
            'current_load_kg': total_load,
            'current_load_tons': round(total_load / 1000, 2),
            'utilization_percent': round((total_load / total_capacity) * 100, 2) if total_capacity > 0 else 0,
            'total_assignments': len(self.assignments),
            'assignments_by_status': assignments_by_status
        }


# Instancia global
warehouse_system = WarehouseSystem()
