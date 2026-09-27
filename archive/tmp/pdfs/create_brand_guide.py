from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'output/pdf/guide-de-marque-ferronnerie-du-rouret.pdf'
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

for weight in (400, 500, 600):
    pdfmetrics.registerFont(TTFont(f'Inter-{weight}', f'/private/tmp/Inter-{weight}.ttf'))

ORANGE = colors.HexColor('#D9672B')
CHARCOAL = colors.HexColor('#1C1F22')
SLATE = colors.HexColor('#374151')
WHITE = colors.white
W, H = A4
c = canvas.Canvas(str(OUTPUT), pagesize=(W, H))
c.setTitle('Identité visuelle - La Ferronnerie du Rouret')
c.setAuthor('La Ferronnerie du Rouret')


def label(x, y, value, size=10, color=CHARCOAL, weight=400):
    c.setFont(f'Inter-{weight}', size)
    c.setFillColor(color)
    c.drawString(x, y, value)


def rounded_image(path, x, y, width, height, radius=8):
    c.saveState()
    mask = c.beginPath()
    mask.roundRect(x, y, width, height, radius)
    c.clipPath(mask, stroke=0)
    c.drawImage(str(path), x, y, width, height, mask='auto')
    c.restoreState()


# Actual screen capture of the website header and hero.
rounded_image(ROOT / 'tmp/pdfs/header-hero.png', 38, 555, W - 76, 249, 9)

# Real completed works supplied for the site.
photos = [
    '/Users/sof/Downloads/Pink and Beige Skincare Product Video Promo (1)/5.jpg',
    '/Users/sof/Downloads/Pink and Beige Skincare Product Video Promo (1) 2/6.jpg',
    '/Users/sof/Downloads/Pink and Beige Skincare Product Video Promo (1)/7.jpg',
]
photo_w, photo_h, gap = 165, 92.8, 12
for i, path in enumerate(photos):
    x = 38 + i * (photo_w + gap)
    rounded_image(path, x, 437, photo_w, photo_h, 7)

# Correct service names with a small, text-free photograph.
label(38, 407, 'NOS SERVICES', 9, ORANGE, 600)
services = [
    'Garde-corps',
    'Portails',
    'Portes métalliques',
    'Clôtures',
    'Pergolas & marquises',
    "Rampes d'escalier",
]
for i, service in enumerate(services):
    y = 375 - i * 27
    c.setFillColor(ORANGE)
    c.circle(42, y + 3, 2.5, stroke=0, fill=1)
    label(53, y, service, 9.3, CHARCOAL, 500)

service_photo = ROOT / 'assets/images/services/pergola-marquise-fer-forge-nice-750.webp'
service_crop_path = ROOT / 'tmp/pdfs/services-small.png'
with Image.open(service_photo) as source:
    ImageOps.fit(source.convert('RGB'), (360, 465), method=Image.Resampling.LANCZOS).save(service_crop_path)
rounded_image(service_crop_path, 173, 223, 120, 155, 8)

# Website logo and two brand colors.
logo = svg2rlg(str(ROOT / 'assets/images/logo-la-ferronnerie-du-rouret.svg'))
scale = 102 / logo.width
c.saveState()
c.translate(328, 308)
c.scale(scale, scale)
renderPDF.draw(logo, c, 0, 0)
c.restoreState()

label(320, 290, 'PALETTE', 9, ORANGE, 600)
c.setFillColor(ORANGE)
c.roundRect(320, 249, 32, 32, 5, stroke=0, fill=1)
label(362, 267, 'Orange atelier  #D9672B', 9, CHARCOAL, 600)
label(362, 253, 'Feu de la forge et énergie.', 8, SLATE)
c.setFillColor(CHARCOAL)
c.roundRect(320, 207, 32, 32, 5, stroke=0, fill=1)
label(362, 225, 'Charbon  #1C1F22', 9, CHARCOAL, 600)
label(362, 211, 'Solidité et lisibilité.', 8, SLATE)

# Single concise typography rule.
c.setFillColor(CHARCOAL)
c.roundRect(38, 103, W - 76, 76, 10, stroke=0, fill=1)
label(55, 151, 'TYPOGRAPHIE', 8.5, colors.HexColor('#F6B287'), 600)
label(55, 121, 'Inter', 20, WHITE, 500)
label(141, 124, 'Titres 500  ·  Texte 400  ·  Boutons 600', 9.5, WHITE, 400)

c.showPage()
c.save()
print(OUTPUT)
