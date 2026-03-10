import fitz

def get_aquant_category_by_page(page_num_1_indexed):
    # Mapping of starting page to category name
    # Ensure they match the exact title strings required!
    mapping = [
        (4, "FAUCETS & SHOWERING SYSTEMS IN SPECIAL FINISHES"),
        (8, "CLASSICAL CERAMICS BASINS"),
        (9, "CLASSICAL TOILETS"),
        (10, "FAUCETS & SHOWERING SYSTEMS IN SPECIAL FINISHES"),
        (12, "PRESTIGE COLLECTION BASIN MIXERS"),
        (14, "FAUCETS & SHOWERING SYSTEMS IN SPECIAL FINISHES"),
        (28, "SHOWERING SYSTEMS IN SPECIAL FINISHES"),
        (31, "FAUCETS & SPOUTS IN SPECIAL FINISHES"),
        (32, "SHOWERING SYSTEMS IN SPECIAL FINISHES"),
        (38, "HAND SHOWERS IN SPECIAL FINISHES"),
        (39, "BODY JETS & BODY SHOWERS IN SPECIAL FINISHES"),
        (40, "FAUCETS IN SPECIAL FINISHES"),
        (42, "BATH FITTINGS IN SPECIAL FINISHES"),
        (43, "ALLIED PRODUCTS IN SPECIAL FINISHES"),
        (44, "ACCESSORIES IN SPECIAL FINISHES"),
        (50, "FAUCETS & SHOWERING SYSTEMS IN CHROME FINISH"),
        (52, "SHOWERING SYSTEMS IN CHROME FINISH"),
        (53, "CONCEALED CEILING MOUNTED SHOWERS IN CHROME FINISH"),
        (54, "HAND SHOWERS & HEAD SHOWERS IN CHROME FINISH"),
        (55, "ALLIED PRODUCTS IN CHROME FINISH"),
        (56, "SS SHOWER PANELS IN MATT FINISH"),
        (57, "SHOWER PANELS IN SPECIAL & CHROME FINISH"),
        (58, "FLOOR DRAINS IN STAINLESS STEEL"),
        (59, "FLOOR DRAINS IN SPECIAL FINISHES"),
        (60, "KITCHEN FAUCETS IN SPECIAL & CHROME FINISH"),
        (61, "BATH COMPONENTS"),
        (64, "STONE WASH BASINS"),
        (68, "ARTISTIC WASH BASINS IN UNIQUE MATERIALS"),
        (74, "CERAMIC SANITARY WARE IN SPECIAL FINISHES"),
        (79, "CERAMIC BASINS IN SPECIAL FINISHES"),
        (80, "CERAMIC PEDESTAL WASH BASINS"),
        (81, "CERAMIC BASINS IN WHITE & SPECIAL FINISHES"),
        (82, "CERAMIC WASH BASINS"),
        (86, "INTELLIGENT SMART TOILET AQUANEXX SERIES"),
        (88, "TOILETS"),
        (91, "FLUSH TANKS/PLATES & URINAL SENSORS IN SPECIAL & CHROME FINISH"),
        (92, "OUR PROMISE"),
        (93, "CARE INSTRUCTIONS")
    ]
    
    current_cat = None
    for start_pg, cat_name in mapping:
        if page_num_1_indexed >= start_pg:
            current_cat = cat_name
        else:
            break
            
    return current_cat

print("Page 4:", get_aquant_category_by_page(4))
print("Page 7:", get_aquant_category_by_page(7))
print("Page 8:", get_aquant_category_by_page(8))
print("Page 93:", get_aquant_category_by_page(93))
