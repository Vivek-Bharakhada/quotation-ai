import fitz
doc = fitz.open("backend/uploads/Kohler_PriceBook_Nov'25 Edition (1).pdf")
pix = doc[0].get_pixmap(dpi=150)
pix.save('frontend/public/kohler_cover.jpg')
print("Saved kohler cover")
