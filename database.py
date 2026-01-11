"""Recyclable materials catalog for circular economy platform."""

from typing import Dict, List, TypedDict


class MaterialData(TypedDict):
    """Recyclable material data structure."""

    item_id: int
    material: str
    price_kg: float
    price_ton: str
    category: str
    stock_available: str


def transform_material_data(material_data: List[MaterialData]) -> str:
    """Transform material data into AI-readable format."""
    transformed_data = "📦 CATÁLOGO DE MATERIALES RECICLABLES:\n\n"
    
    categories: Dict[str, List[MaterialData]] = {}
    for material in material_data:
        cat: str = material['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(material)
    
    for category, materials in categories.items():
        transformed_data += f"🔹 {category.upper()}:\n"
        for mat in materials:
            transformed_data += (
                f"  • {mat['material']}\n"
                f"    - Precio: S/ {mat['price_kg']:.2f}/kg | {mat['price_ton']}/tonelada\n"
                f"    - Stock disponible: {mat['stock_available']}\n"
                f"    - ID: #{mat['item_id']}\n\n"
            )
    
    return transformed_data


material_data: List[MaterialData] = [
    # PLÁSTICOS - Mayor volumen disponible
    {
        "item_id": 1,
        "material": "PET (Polietileno Tereftalato) - Botellas",
        "price_kg": 1.80,
        "price_ton": "1,650",
        "category": "Plásticos",
        "stock_available": ">66 toneladas en stock"
    },
    {
        "item_id": 2,
        "material": "HDPE (Polietileno Alta Densidad) - Envases",
        "price_kg": 2.20,
        "price_ton": "2,000",
        "category": "Plásticos",
        "stock_available": "45 toneladas disponibles"
    },
    {
        "item_id": 3,
        "material": "LDPE (Polietileno Baja Densidad) - Bolsas",
        "price_kg": 1.50,
        "price_ton": "1,400",
        "category": "Plásticos",
        "stock_available": "38 toneladas disponibles"
    },
    {
        "item_id": 4,
        "material": "PP (Polipropileno) - Tapas y recipientes",
        "price_kg": 1.90,
        "price_ton": "1,750",
        "category": "Plásticos",
        "stock_available": "52 toneladas disponibles"
    },
    
    # METALES - Alto valor
    {
        "item_id": 5,
        "material": "Aluminio - Latas y perfiles",
        "price_kg": 5.50,
        "price_ton": "5,200",
        "category": "Metales",
        "stock_available": ">80 toneladas en stock"
    },
    {
        "item_id": 6,
        "material": "Cobre - Cables y tuberías",
        "price_kg": 22.00,
        "price_ton": "20,500",
        "category": "Metales",
        "stock_available": "15 toneladas disponibles"
    },
    {
        "item_id": 7,
        "material": "Acero - Chatarra y estructuras",
        "price_kg": 1.20,
        "price_ton": "1,100",
        "category": "Metales",
        "stock_available": "120 toneladas disponibles"
    },
    {
        "item_id": 8,
        "material": "Bronce - Piezas industriales",
        "price_kg": 18.00,
        "price_ton": "17,000",
        "category": "Metales",
        "stock_available": "8 toneladas disponibles"
    },
    
    # PAPEL Y CARTÓN
    {
        "item_id": 9,
        "material": "Papel Blanco - Oficina y archivo",
        "price_kg": 0.80,
        "price_ton": "750",
        "category": "Papel",
        "stock_available": ">96 toneladas en stock"
    },
    {
        "item_id": 10,
        "material": "Papel Periódico",
        "price_kg": 0.45,
        "price_ton": "420",
        "category": "Papel",
        "stock_available": "67 toneladas disponibles"
    },
    {
        "item_id": 11,
        "material": "Cartón Corrugado - Cajas",
        "price_kg": 0.60,
        "price_ton": "550",
        "category": "Cartón",
        "stock_available": "85 toneladas disponibles"
    },
    {
        "item_id": 12,
        "material": "Cartón Compacto - Empaques",
        "price_kg": 0.70,
        "price_ton": "650",
        "category": "Cartón",
        "stock_available": "42 toneladas disponibles"
    },
    
    # VIDRIO
    {
        "item_id": 13,
        "material": "Vidrio Transparente - Botellas",
        "price_kg": 0.35,
        "price_ton": "320",
        "category": "Vidrio",
        "stock_available": "55 toneladas disponibles"
    },
    {
        "item_id": 14,
        "material": "Vidrio de Color - Ámbar/Verde",
        "price_kg": 0.30,
        "price_ton": "280",
        "category": "Vidrio",
        "stock_available": "38 toneladas disponibles"
    },
    
    # ESPECIALES - Tetrapak y otros
    {
        "item_id": 15,
        "material": "Tetrapak - Envases multicapa",
        "price_kg": 0.85,
        "price_ton": "800",
        "category": "Especiales",
        "stock_available": "25 toneladas disponibles"
    },
    {
        "item_id": 16,
        "material": "Baterías de Plomo - Reciclaje especializado",
        "price_kg": 3.50,
        "price_ton": "3,200",
        "category": "Especiales",
        "stock_available": "12 toneladas disponibles"
    }
]

formatted_product_data = transform_material_data(material_data)
