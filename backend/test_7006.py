import fitz, glob

with open('out.txt', 'w', encoding='utf-8') as f:
    for pdf_path in glob.glob('uploads/*.pdf'):
        doc = fitz.open(pdf_path)
        for p in range(len(doc)):
            text = doc[p].get_text("text")
            if '7006' in text:
                f.write(f"File: {pdf_path}, Page: {p}\n")
                f.write("---\n")
                d = doc[p].get_text("dict")
                for block in d.get("blocks", []):
                    if block.get("type") == 0:
                        for line in block.get("lines", []):
                            line_text = "".join(span.get("text", "") for span in line.get("spans", [])).strip()
                            if '7006' in line_text or 'MRP' in line_text or 'Size' in line_text or '7106' in line_text:
                                f.write(f"y0: {line['bbox'][1]:.1f}, x0: {line['bbox'][0]:.1f}, text: {line_text}\n")
