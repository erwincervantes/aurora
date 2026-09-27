"""Build the static font instances the renderer uses (run from this folder), then install to ~/.fonts.

Per The Aurora Standard v5 (DS-AUR-005, chapter 04): Fraunces carries voice, headlines and hero numerals;
Geist carries every word of running text and UI; Geist Mono labels data. All SIL OFL 1.1, no Reserved
Font Names, so renamed static instances are permitted.
"""
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

FRAUNCES = "Fraunces[SOFT,WONK,opsz,wght].ttf"
FRAUNCES_ITALIC = "Fraunces-Italic[SOFT,WONK,opsz,wght].ttf"
SPECS = [
    (FRAUNCES, "AuroraSerifDisplay", {"wght": 330, "opsz": 144, "SOFT": 0, "WONK": 0}),     # display token
    (FRAUNCES, "AuroraSerifHead", {"wght": 340, "opsz": 144, "SOFT": 0, "WONK": 0}),        # h2 / lead tokens
    (FRAUNCES, "AuroraWordmark", {"wght": 300, "opsz": 144, "SOFT": 20, "WONK": 0}),        # .lockup .wordmark
    (FRAUNCES_ITALIC, "AuroraWordmarkItal", {"wght": 300, "opsz": 144, "SOFT": 20, "WONK": 0}),  # the amber "o"
    (FRAUNCES_ITALIC, "AuroraSerifWonk", {"wght": 340, "opsz": 144, "SOFT": 100, "WONK": 1}),    # --wonk emphasis
    ("Geist[wght].ttf", "AuroraGeistReg", {"wght": 400}),
    ("Geist[wght].ttf", "AuroraGeistMed", {"wght": 500}),
    ("Geist[wght].ttf", "AuroraGeistSemi", {"wght": 600}),
    ("GeistMono[wght].ttf", "AuroraMono", {"wght": 500}),
]

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
