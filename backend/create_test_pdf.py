from reportlab.pdfgen import canvas

c = canvas.Canvas("test_catalog.pdf")
c.drawString(100, 750, "Product Catalog 2024")
c.drawString(100, 730, "Laptop | Model: SuperBook | Price: 75000")
c.drawString(100, 710, "Smartphone | Model: GalaxyZ | Price: 45000")
c.drawString(100, 690, "Headphones | Model: SoundPro | Price: 5000")
c.save()
print("test_catalog.pdf created")
