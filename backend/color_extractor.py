"""
Color Code Extractor for Aquant Products

Extracts color codes from product codes (e.g., 2637AB → 2637 + AB)
and creates color-specific variants for better search matching.
"""

import re
from typing import Dict, List, Tuple, Optional

# Color code mapping - from pdf_reader.py and Aquant PDF
COLOR_CODE_NAMES = {
    # Aquant Finishes
    "AB": "Antique Bronze",
    "AC": "Antique Chrome",
    "AN": "Antique Nickel",
    "BRG": "Brushed Rose Gold",
    "BG": "Brushed Gold",
    "CP": "Chrome Plated",
    "CH": "Chrome",
    "G": "Gold",
    "GG": "Graphite Grey",
    "MB": "Matt Black",
    "RG": "Rose Gold",
    "W": "White",
    "WN": "Walnut",
    "WG": "White Glass",
    
    # Kohler & Plumber Finishes
    "CB": "Chrome Black",
    "CGY": "Chrome Grey",
    "CW": "Chrome White",
    "BCK": "Matt Black",
    "WTE": "Matt White",
    "GRY": "Matt Grey",
    "BCG": "Black Champagne Gold",
    "CNG": "Champagne Gold",
    "RGD": "Rose Gold",
    "GM": "Gun Metal",
    "SSF": "Brushed Stainless Steel",
    "ORB": "Oil Rubbed Bronze",
    "SN": "Satin Nickel",
}

def extract_color_code(product_code: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract color code from product code.
    
    Examples:
        "2637AB" → ("2637", "AB")
        "K-28362IN-CP" → ("K-28362IN", "CP")
        "9272" → ("9272", None)
    
    Returns:
        (base_code, color_code) or (code, None) if no color detected
    """
    if not product_code:
        return None, None
    
    product_code = product_code.strip().upper()
    
    # Try to match patterns with color codes
    # Pattern 1: Code ending with known color code (2-3 chars)
    for color in sorted(COLOR_CODE_NAMES.keys(), key=len, reverse=True):
        if product_code.endswith(color):
            base = product_code[:-len(color)].strip()
            if base and len(base) >= 2:  # Must have a real code
                return base, color
    
    return product_code, None


def should_create_color_variant(product_item: Dict) -> bool:
    """
    Check if this product should have color variants created.
    
    Products should have variants if:
    - Brand is Aquant, Kohler, or Plumber
    - Text contains a product code with a color suffix
    """
    brand = product_item.get("brand", "").lower()
    if brand not in ("aquant", "kohler", "plumber"):
        return False
    
    text = product_item.get("text", "")
    name = product_item.get("name", "")
    code = product_item.get("code", "")
    
    # Check if code already has a color
    search_text = f"{code} {text} {name}".upper()
    
    base, color = extract_color_code(code)
    return color is not None


def create_color_variants(product_item: Dict) -> List[Dict]:
    """
    Create color-specific variants of a product.
    
    Extracts color code from product code and creates separate
    product entries for search.
    
    Returns:
        List of product dictionaries (including original and variants)
    """
    products = [product_item]  # Always include original
    
    code = product_item.get("code", "").strip()
    if not code:
        return products
    
    base_code, color = extract_color_code(code)
    
    if not color or color not in COLOR_CODE_NAMES:
        return products
    
    color_name = COLOR_CODE_NAMES[color]
    
    # Create a variant with color info in text
    variant = product_item.copy()
    
    # Update the text to include color name prominently
    original_text = variant.get("text", "")
    original_name = variant.get("name", "")
    
    # Add color to description
    if color_name not in original_text and color_name not in original_name:
        variant["text"] = f"{original_name} - {color_name}\n{original_text}"
        variant["name"] = f"{original_name} ({color_name})"
    
    # Also add color code for search
    if color not in variant.get("text", ""):
        variant["text"] = f"Color: {color_name}\nCode: {color}\n{variant['text']}"
    
    # Update code to be base code for variant (so 2637AB finds as 2637)
    variant["code"] = base_code
    
    products.append(variant)
    
    return products


def expand_products_with_colors(items: List[Dict], brand: str) -> List[Dict]:
    """
    Expand product list to include color variants.
    
    Takes list of products and creates color-specific variants.
    This helps match products when searching by color.
    
    Args:
        items: List of product dictionaries
        brand: Brand name (Aquant, Kohler, Plumber, etc)
    
    Returns:
        Expanded list of products with color variants
    """
    expanded = []
    
    for item in items:
        item = item.copy()
        item["brand"] = brand  # Ensure brand is set
        
        # Create color variants
        variants = create_color_variants(item)
        expanded.extend(variants)
    
    return expanded


if __name__ == "__main__":
    # Test the color extraction
    test_codes = [
        "2637AB",
        "K-28362IN-CP",
        "9272",
        "2631G",
        "1871AB+W",
        "K-2543IN-4-CP"
    ]
    
    print("Color Code Extraction Tests:")
    print("=" * 60)
    for code in test_codes:
        base, color = extract_color_code(code)
        color_name = COLOR_CODE_NAMES.get(color, "Unknown") if color else "No Color"
        print(f"{code:20} → Base: {base:15} Color: {color} ({color_name})")
