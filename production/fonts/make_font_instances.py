"""Build the static Fraunces/Geist instances used by the renderer (run from this folder), then install to ~/.fonts."""
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
specs=[("Fraunces[SOFT,WONK,opsz,wght].ttf","AuroraFrauncesSemi",dict(wght=600,opsz=72,SOFT=0,WONK=0)),
       ("Fraunces[SOFT,WONK,opsz,wght].ttf","AuroraFrauncesReg",dict(wght=400,opsz=72,SOFT=0,WONK=0)),
       ("Geist[wght].ttf","AuroraGeistReg",dict(wght=400)),
       ("Geist[wght].ttf","AuroraGeistMed",dict(wght=500)),
       ("Geist[wght].ttf","AuroraGeistSemi",dict(wght=600))]
for src,fam,loc in specs:
    f=TTFont(src); f=instantiateVariableFont(f,loc)
    n=f["name"]
    for rec in list(n.names):
        if rec.nameID in (1,4,6,16,17,3): n.removeNames(nameID=rec.nameID)
    for nid,val in [(1,fam),(2,"Regular"),(4,fam),(6,fam),(3,fam)]: n.setName(val,nid,3,1,0x409)
    f["OS/2"].usWeightClass=400; f["OS/2"].fsSelection=(f["OS/2"].fsSelection & ~0b1100001)|0x40
    f.save(f"{fam}.ttf"); print(fam)
