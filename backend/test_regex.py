import re

t = 'Size:200x125mmMRP:`8,000'
m = re.search(r'(?:MRP|`|₹)[:.]?`?([\d,]+)', t)
print(m.group(1) if m else None)

t2 = 'Size:200x125mmMRP:`8,0-00'
t3 = 'MRP : ` \n/-\n12,950'

for text in [t, t2, t3]:
    t_comp = re.sub(r'[\s/\-]+', '', text)
    print("t_comp:", t_comp)
    m = re.search(r'(?:MRP|`|₹)[:.]?`?([\d,]+)', t_comp, re.IGNORECASE)
    print("matched:", m.group(1) if m else None)
