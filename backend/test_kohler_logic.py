import fitz
import re

def parse_kohler():
    doc = fitz.open("backend/uploads/Kohler_PriceBook_Nov'25 Edition (1).pdf")
    all_products = []
    
    current_category = "Toilets"
    for page_num in [4, 5, 8, 9]:
        page = doc[page_num]
        
        # Images
        img_records = []
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            width, height = img[2], img[3]
            if width < 50 or height < 50: continue
            
            rects = page.get_image_rects(xref)
            if rects:
                img_records.append({"path": f"kohler_p{page_num}_i{img_index}.jpg", "rect": rects[0]})
        
        blocks = page.get_text("blocks")
        blocks.sort(key=lambda b: (b[1], b[0]))
        
        last_name = ""
        for b in blocks:
            if b[6] != 0: continue
            text = b[4].strip()
            
            x0, y0, x1, y1 = b[:4]
            if x0 < 90 and len(text) < 50 and not 'MRP' in text:
                last_name = text.replace('\n', ' ')
            elif x0 > 100:
                if "K-" in text and "MRP" in text:
                    code_match = re.search(r'K-[\w\d-]+', text)
                    price_match = re.search(r'(?:MRP|`|₹)[:.]?`?([\d,]+.*?)(?=\n|\()', text.replace('\u20b9', '`'), re.IGNORECASE)
                    
                    price = price_match.group(1).replace(",", "").strip() if price_match else "0"
                    code = code_match.group(0) if code_match else ""
                    
                    cx = (x0 + x1) / 2
                    cy = (y0 + y1) / 2
                    
                    # Debug image matching
                    best_img_idx = -1
                    best_dist = float("inf")
                    for i_idx, ir in enumerate(img_records):
                        img_rect = ir["rect"]
                        img_cx = (img_rect.x0 + img_rect.x1) / 2
                        img_cy = (img_rect.y0 + img_rect.y1) / 2
                        
                        dx = abs(img_cx - cx)
                        dy = img_cy - cy
                        dist = (dx**2 + dy**2)**0.5
                        if dist < best_dist and dist < 800:
                            best_dist = dist
                            best_img_idx = i_idx
                            
                    img_path = img_records[best_img_idx]["path"] if best_img_idx != -1 else "NO_IMAGE"
                    
                    print(f"[{last_name} | {code}] PR: {price} -> IMG_DIST: {best_dist:.1f}, {img_path}")

parse_kohler()
