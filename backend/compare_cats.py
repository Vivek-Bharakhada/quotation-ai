import fitz

def map_kohler_category(text):
    t = text.upper()
    
    if "FRENCH GOLD" in t: return "French Gold"
    if "BRUSHED BRONZE" in t: return "Brushed Bronze"
    if "MATE BLACK" in t or "MATTE BLACK" in t: return "Matte Black"
    if "BRUSHED ROSE GOLD" in t: return "Brushed Rose Gold"
    if "ROSE GOLD" in t: return "Rose Gold"
    if "VIBRANT" in t: return "Vibrant Finishes"
    
    if "SMART TOILET" in t or "C3" in t or "BIDET" in t or "CLEANSING SEAT" in t:
        return "Smart Toilets & Bidet Seats"
    if "WALL HUNG TOILET" in t or "1 PC TOILET" in t or "ONE-PIECE" in t or "WALL HUNG" in t or "WALL-HUNG" in t or "ESCALE" in t or "VEIL" in t or "TRACE" in t:
        return "1 pc Toilets & Wall Hungs"
    if "IN-WALL TANK" in t or "CONCEALED CISTERN" in t or "CONCEALED TANK" in t:
        return "In-Wall Tanks"
    if "FACEPLATE" in t or "PNEUMATIC" in t or "FLUSH VALVE" in t:
        return "Faceplates"
    if "TOILET" in t: return "Toilets"
    
    if "MIRROR" in t: return "Mirrors"
    if "VANIT" in t: return "Vanities"
    if "WASH BASIN" in t or "VESSEL" in t or "LAVATOR" in t or "PEDESTAL" in t or "BASIN" in t: return "Wash Basins"
    
    if "KITCHEN" in t or "SINK" in t: return "Kitchen Sinks & Faucets"
    if "STEAM" in t: return "Steam"
    if "ENCLOSURE" in t or "LIB" in t or "SINGULIER" in t or "GLASS" in t: return "Shower Enclosures"
    if "SHOWERING" in t or "SHOWER" in t or "BATH AND SHOWER" in t or "BATH & SHOWER" in t: return "Showering"
    if "BATHTUB" in t or "BATH FILLER" in t or "BATH SPOUT" in t: return "Bathtubs & Bath Fillers"
    
    if "FAUCET" in t or "SPOUT" in t or "MIXER" in t or "TAP" in t: return "Faucets"
    if "ACCESSOR" in t or "TOWEL" in t or "BRUSH HOLDER" in t or "ROBE HOOK" in t: return "Accessories"
    if "COMMERCIAL" in t: return "Commercial Products"
    if "CLEANI" in t: return "Cleaning Solutions"
    if "FITTING" in t: return "Fittings"
    
    return None

doc = fitz.open("uploads/Kohler_PriceBook_Nov'25 Edition (1).pdf")
cat = "Toilets"
for i in range(5, 100):
   for b in doc[i].get_text("blocks"):
       if b[6] == 0:
           t_clean = b[4].replace('\n', ' ').strip()
           # Detect header usually y0 < 100
           if b[1] < 100:
               mapped = map_kohler_category(t_clean)
               if mapped: cat = mapped
       if b[6] == 0 and b[0] > 100 and "K-" in b[4] and "MRP" in b[4]:
           print(f"Page {i+1} maps to: {cat} -> {b[4][:30].replace(chr(10),' ').strip()}")
           break
