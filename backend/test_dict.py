import fitz, glob
doc = fitz.open(glob.glob('uploads/*.pdf')[0])
page = doc[7]
d = page.get_text("dict")
lines = []
for block in d["blocks"]:
    if block["type"] == 0: # text
        for line in block["lines"]:
            text = "".join([span["text"] for span in line["spans"]])
            lines.append({
                "text": text,
                "bbox": fitz.Rect(line["bbox"])
            })

for l in lines:
    if "9009" in l["text"] or "9006" in l["text"]:
        print(f"y0: {l['bbox'].y0:.1f}, text: {l['text']}")
