"""Product catalog data for Selva D' Oro."""

from typing import TypedDict


class MaterialData(TypedDict):
    """Product data structure."""

    item_id: int
    material: str
    price_kg: float
    price_ton: str


def transform_material_data(material_data: list[MaterialData]) -> str:
    """Transform the product data into a format understandable by GPT-4o."""
    transformed_data = "Catálogo de productos Selva D' Oro:\n"
    for material in material_data:
        transformed_data += (
            f"ID: {material['item_id']}, "
            f"Producto: {material['material']}, "
            f"Precio por unidad: {material['price_kg']} PEN, "
            f"Descripción: {material['price_ton']}.\n"
        )
    return transformed_data


material_data: list[MaterialData] = [
    {
        "item_id": 1,
        "material": "MIEL DE ABEJA PURA 250g",
        "price_kg": 18.00,
        "price_ton": "Miel 100% pura de abejas de Chanchamayo, sin aditivos ni preservantes",
    },
    {
        "item_id": 2,
        "material": "MIEL DE ABEJA PURA 500g",
        "price_kg": 32.00,
        "price_ton": "Miel 100% pura de abejas de Chanchamayo, sin aditivos ni preservantes",
    },
    {
        "item_id": 3,
        "material": "MIEL DE ABEJA PURA 1kg",
        "price_kg": 60.00,
        "price_ton": "Miel 100% pura de abejas de Chanchamayo, sin aditivos ni preservantes",
    },
    {
        "item_id": 4,
        "material": "CAFÉ ORGÁNICO EN GRANO 250g",
        "price_kg": 22.00,
        "price_ton": "Café orgánico de Chanchamayo en grano, tostado medio, notas de chocolate y frutos secos",
    },
    {
        "item_id": 5,
        "material": "CAFÉ ORGÁNICO EN GRANO 500g",
        "price_kg": 40.00,
        "price_ton": "Café orgánico de Chanchamayo en grano, tostado medio, notas de chocolate y frutos secos",
    },
    {
        "item_id": 6,
        "material": "CAFÉ ORGÁNICO EN GRANO 1kg",
        "price_kg": 75.00,
        "price_ton": "Café orgánico de Chanchamayo en grano, tostado medio, notas de chocolate y frutos secos",
    },
    {
        "item_id": 7,
        "material": "CAFÉ ORGÁNICO MOLIDO 250g",
        "price_kg": 22.00,
        "price_ton": "Café orgánico de Chanchamayo molido, ideal para cafetera italiana o francesa",
    },
    {
        "item_id": 8,
        "material": "CAFÉ ORGÁNICO MOLIDO 500g",
        "price_kg": 40.00,
        "price_ton": "Café orgánico de Chanchamayo molido, ideal para cafetera italiana o francesa",
    },
    {
        "item_id": 9,
        "material": "COMBO MIEL 500g + CAFÉ 250g",
        "price_kg": 50.00,
        "price_ton": "Combo especial: Miel pura 500g y Café orgánico 250g",
    },
    {
        "item_id": 10,
        "material": "COMBO MIEL 1kg + CAFÉ 500g",
        "price_kg": 95.00,
        "price_ton": "Combo familiar: Miel pura 1kg y Café orgánico 500g",
    },
]

formatted_product_data = transform_material_data(material_data)
