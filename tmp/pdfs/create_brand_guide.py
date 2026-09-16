from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'output/pdf/guide-de-marque-ferronnerie-du-rouret.pdf'
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

for weight in (400, 500, 600):
    pdfmetrics.registerFont(TTFont(f'Inter-{weight}', f'/private/tmp/Inter-{weight}.ttf'))

ORANGE = colors.HexColor('#D9672B')
CHARCOAL = colors.HexColor('#1C1F22')
SLATE = colors.HexColor('#374151')
MIST = colors.HexColor('#F3F6F7')
WHITE = colors.white
W, H = landscape(A4)
c = canvas.Canvas(str(OUTPUT), pagesize=(W, H))
c.setTitle('Identité visuelle - La Ferronnerie du Rouret')
c.setAuthor('La Ferronnerie du Rouret')


def label(x, y, value, size=10, color=CHARCOAL, weight=400):
    c.setFont(f'Inter-{weight}', size)
    c.setFillColor(color)
    c.drawString(x, y, value)


# Vector logo from the website.
logo = svg2rlg(str(ROOT / 'assets/images/logo-la-ferronnerie-du-rouret.svg'))
scale = 130 / logo.width
c.saveState()
c.translate(40, 451)
c.scale(scale, scale)
renderPDF.draw(logo, c, 0, 0)
c.restoreState()

label(210, 522, 'LA FERRONNERIE DU ROURET', 23, CHARCOAL, 600)
label(210, 491, 'Identité visuelle', 15, ORANGE, 500)
label(210, 466, "L'élégance du métal, la qualité garantie.", 11, SLATE, 400)
c.setStrokeColor(ORANGE)
c.setLineWidth(2.5)
c.line(40, 444, W - 40, 444)

# Three real photographs provided by the user.
photos = [
    ('/Users/sof/Downloads/Pink and Beige Skincare Product Video Promo (1)/5.jpg', 'PORTAIL'),
    ('/Users/sof/Downloads/Pink and Beige Skincare Product Video Promo (1) 2/6.jpg', 'GARDE-CORPS'),
    ('/Users/sof/Downloads/Pink and Beige Skincare Product Video Promo (1)/7.jpg', 'CLÔTURE'),
]
photo_w = 246
photo_h = 138.375
photo_gap = 12
for i, (path, title) in enumerate(photos):
    x = 40 + i * (photo_w + photo_gap)
    c.drawImage(path, x, 284, width=photo_w, height=photo_h, preserveAspectRatio=True, anchor='c')
    label(x, 266, title, 8.5, SLATE, 600)

# Two brand colors and their meanings.
card_y, card_h, card_w = 150, 96, 375
for x in (40, 427):
    c.setFillColor(MIST)
    c.roundRect(x, card_y, card_w, card_h, 10, stroke=0, fill=1)

c.setFillColor(ORANGE)
c.roundRect(54, 164, 67, 67, 7, stroke=0, fill=1)
label(138, 218, 'Orange atelier', 13, CHARCOAL, 600)
label(138, 198, '#D9672B', 10, ORANGE, 600)
label(138, 178, 'Feu de la forge, énergie, accent.', 9.3, SLATE)

c.setFillColor(CHARCOAL)
c.roundRect(441, 164, 67, 67, 7, stroke=0, fill=1)
label(525, 218, 'Charbon', 13, CHARCOAL, 600)
label(525, 198, '#1C1F22', 10, CHARCOAL, 600)
label(525, 178, 'Solidité, titres et lisibilité.', 9.3, SLATE)

# Single concise type rule.
c.setFillColor(CHARCOAL)
c.roundRect(40, 65, W - 80, 65, 10, stroke=0, fill=1)
label(57, 105, 'TYPOGRAPHIE', 9, colors.HexColor('#F6B287'), 600)
label(171, 103, 'Inter', 18, WHITE, 500)
label(171, 82, 'Titres 500  ·  Texte 400  ·  Boutons 600', 10, WHITE, 400)

label(40, 36, 'Photos réelles fournies par le client', 8, SLATE, 400)
label(W - 112, 36, 'GUIDE EXPRESS', 8, SLATE, 600)
c.showPage()
c.save()
print(OUTPUT)
