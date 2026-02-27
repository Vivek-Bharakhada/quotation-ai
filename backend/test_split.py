import sys; sys.path.append('backend')
from pdf_reader import extract_content, fitz

text_block = "2592 CP\nMRP : ` 26,250/-\n2592 BRG - Brushed Rose Gold\n2592 BG - Brushed Gold"

def parse_block(text, master_price="0"):
    import re
    # Extract explicit block price
    block_price = master_price
    t_comp = re.sub(r'[\s/\-]+', '', text)
    pm = re.search(r'(?:MRP|`|₹)[:.]?`?([\d,]+)', t_comp, re.IGNORECASE)
    if pm:
        block_price = pm.group(1).replace(",", "")
        
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    products = []
    current_prod = {"name": "", "text": "", "price": block_price}
    
    # helper
    def is_code(t):
        w = t.split()[0] if t.split() else ""
        if w.isdigit() and 4 <= len(w) <= 7: return True
        return bool(re.match(r'^[A-Z]{1,3}-\d+|^\d{3,}-[A-Z]', w))
        
    for l in lines:
        if is_code(l) and not ('MRP' in l.upper()):
            # start new product
            if current_prod["name"]:
                products.append(current_prod)
            
            # extract inline price if any, else inherit block price
            inline_price = block_price
            lp_comp = re.sub(r'[\s/\-]+', '', l)
            im = re.search(r'(?:MRP|`|₹)[:.]?`?([\d,]+)', lp_comp, re.IGNORECASE)
            if im:
                inline_price = im.group(1)
            
            current_prod = {"name": l[:120], "text": l, "price": inline_price}
        else:
            if not current_prod["name"] and not 'MRP' in l.upper():
                current_prod["name"] = l[:120]
            current_prod["text"] += "\n" + l
            
            lp_comp = re.sub(r'[\s/\-]+', '', l)
            im = re.search(r'(?:MRP|`|₹)[:.]?`?([\d,]+)', lp_comp, re.IGNORECASE)
            if im:
                current_prod["price"] = im.group(1).replace(",", "")
                # also update block price backward compat
                if not products: block_price = current_prod["price"]
                
    if current_prod["name"]:
        products.append(current_prod)
        
    return products

print(parse_block(text_block, "32500"))
