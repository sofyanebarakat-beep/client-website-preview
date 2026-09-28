"""Generate the ironwork badges shown in the About page marquee (one SVG per trade and language)."""
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets/images/about/savoir-faire"
INK = "#374151"
BG = "#F3F6F7"

# Icons are drawn in a 48x48 box.
ICONS = {
    "portails": '<path d="M4 44V10M44 44V10M4 14Q14 4 24 10Q34 4 44 14"/><path d="M11 44V12M17 44V9M24 44V10M31 44V9M37 44V12M4 28H44"/>',
    "garde-corps": '<path d="M2 12H46M2 40H46M6 12V40M42 12V40"/><path d="M14 12V40M22 12V40M30 12V40M38 12V40"/><circle cx="18" cy="26" r="3"/><circle cx="34" cy="26" r="3"/>',
    "clotures": '<path d="M2 18H46M2 36H46"/><path d="M8 44V10L5 13M8 10L11 13M18 44V10L15 13M18 10L21 13M28 44V10L25 13M28 10L31 13M38 44V10L35 13M38 10L41 13"/>',
    "rampes": '<path d="M2 44H12V36H20V28H28V20H36V12H46"/><path d="M4 26L42 4M10 44V23M22 36V16M34 28V9"/>',
    "pergolas": '<path d="M2 12H46M6 12V44M42 12V44M2 18H46"/><path d="M10 12V8M18 12V8M26 12V8M34 12V8M42 12V8"/><path d="M6 26L14 18M42 26L34 18"/>',
    "marquises": '<path d="M6 4V44"/><path d="M6 14L44 20V24L6 18"/><path d="M6 30Q20 30 30 21M14 30V21"/>',
    "fer-forge": '<path d="M4 10H34Q34 18 46 18V22H34L30 26V32H36V38H12V32H18V26Q8 26 4 16Z"/><path d="M14 44H34"/>',
    "sur-mesure": '<rect x="4" y="16" width="40" height="16" rx="2"/><path d="M10 16V22M16 16V25M22 16V22M28 16V25M34 16V22M40 16V25"/>',
    "finitions-ral": '<rect x="6" y="4" width="36" height="12" rx="2"/><path d="M42 10H46V22H24V28"/><rect x="20" y="28" width="8" height="16" rx="2"/>',
    "portes": '<rect x="10" y="4" width="28" height="40" rx="1"/><rect x="15" y="9" width="18" height="12"/><rect x="15" y="25" width="18" height="14"/><path d="M34 22V27"/>',
}

LABELS = {
    "portails": ("Portails", "Gates", "Cancelli"),
    "garde-corps": ("Garde-corps", "Railings", "Parapetti"),
    "clotures": ("Clôtures", "Fences", "Recinzioni"),
    "rampes": ("Rampes d'escalier", "Stair handrails", "Corrimano"),
    "pergolas": ("Pergolas", "Pergolas", "Pergole"),
    "marquises": ("Marquises", "Glass canopies", "Pensiline"),
    "fer-forge": ("Fer forgé", "Wrought iron", "Ferro battuto"),
    "sur-mesure": ("Sur mesure", "Made to measure", "Su misura"),
    "finitions-ral": ("Finitions RAL", "RAL finishes", "Finiture RAL"),
    "portes": ("Portes métalliques", "Metal doors", "Porte metalliche"),
}

TEMPLATE = """<svg width="298" height="157" viewBox="0 0 298 157" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{label}">
<rect width="298" height="157" fill="{bg}"/>
<g transform="translate(125 26)" stroke="{ink}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">{icon}</g>
<text x="149" y="116" text-anchor="middle" fill="{ink}" font-family="Helvetica, Arial, sans-serif" font-size="20" font-weight="600">{label}</text>
</svg>
"""

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for slug, icon in ICONS.items():
        for lang, label in zip(("fr", "en", "it"), LABELS[slug]):
            svg = TEMPLATE.format(label=label.replace("'", "&#39;"), bg=BG, ink=INK, icon=icon)
            (OUT / f"{slug}-{lang}.svg").write_text(svg, encoding="utf-8")

if __name__ == "__main__":
    main()
