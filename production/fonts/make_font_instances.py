"""Build the static font instances the renderer uses (run from this folder), then install to ~/.fonts.

Oswald (condensed numerals, the hero figures) + Work Sans roman/italic (headings, labels, bilingual lines).
Both SIL OFL 1.1, no Reserved Font Names; renamed instances are permitted.
"""
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

SPECS = [("Oswald[wght].ttf", "AuroraNumSemi", {"wght": 600}),
         ("Oswald[wght].ttf", "AuroraNumMed", {"wght": 500}),
         ("WorkSans[wght].ttf", "AuroraSansReg", {"wght": 400}),
         ("WorkSans[wght].ttf", "AuroraSansMed", {"wght": 500}),
         ("WorkSans[wght].ttf", "AuroraSansSemi", {"wght": 600}),
         ("WorkSans[wght].ttf", "AuroraSansBold", {"wght": 700}),
         ("WorkSans-Italic[wght].ttf", "AuroraSansItal", {"wght": 400})]

for source, family, location in SPECS:
    font = instantiateVariableFont(TTFont(source), location)
    names = font["name"]
    for record in list(names.names):
        if record.nameID in (1, 2, 3, 4, 6, 16, 17):
            names.removeNames(nameID=record.nameID)
    for name_id, value in ((1, family), (2, "Regular"), (3, family), (4, family), (6, family)):
        names.setName(value, name_id, 3, 1, 0x409)
    font["OS/2"].usWeightClass = 400
    font["OS/2"].fsSelection = (font["OS/2"].fsSelection & ~0b1100001) | 0x40
    font["head"].macStyle = 0
    font.save(f"{family}.ttf")
    print(family)
