#!/usr/bin/env python3
import argparse, hashlib, io, json, urllib.request, zipfile
from pathlib import Path
from PIL import Image, ImageSequence

SPECIES = [
    (152,'chikorita'),(155,'cyndaquil'),(158,'totodile'),(255,'torchic'),
    (650,'chespin'),(653,'fennekin'),(656,'froakie'),(728,'popplio'),(1289,'sprigatito'),
]
BASE='https://play.pokemonshowdown.com/sprites/ani-back/'

def sha256(b): return hashlib.sha256(b).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--rom-sha256',required=True)
    ap.add_argument('--output',required=True)
    a=ap.parse_args()
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
    manifest={
        'format':'SOULGOLD_SHOWDOWN_PACK_V1',
        'pack_id':'SOULGOLD_M6X1_STARTERS_BACK_20260904',
        'expected_rom_sha256':a.rom_sha256.lower(),
        'front_providers':[],
        'back_providers':[],
        'source':'Pokemon Showdown ani-back',
        'source_base':BASE,
    }
    files={}
    for species,name in SPECIES:
        url=BASE+name+'.gif'
        req=urllib.request.Request(url,headers={'User-Agent':'SoulGold-M6X1-build/1.0'})
        with urllib.request.urlopen(req,timeout=30) as r: raw=r.read()
        im=Image.open(io.BytesIO(raw))
        frames=[]; canvas_w,canvas_h=im.size
        scale=min(1.0,72.0/max(canvas_w,canvas_h))
        for i,fr in enumerate(ImageSequence.Iterator(im)):
            rgba=fr.convert('RGBA')
            bio=io.BytesIO();rgba.save(bio,'PNG',optimize=True)
            path=f'frames/{species}_{name}_{i:03d}.png';files[path]=bio.getvalue()
            duration=int(fr.info.get('duration',im.info.get('duration',100)) or 100)
            frames.append({'path':path,'duration_ms':max(20,duration)})
        if not frames: raise RuntimeError('no frames for '+name)
        manifest['back_providers'].append({
            'species':species,'name':name,'scale':scale,'canvas_width':canvas_w,'canvas_height':canvas_h,
            'source_url':url,'source_gif_sha256':sha256(raw),'frames':frames,
        })
    files['manifest.json']=(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n').encode()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in files.items():z.writestr(name,data)
    print('M6X1_PACK='+str(out))
    print('M6X1_PACK_SHA256='+sha256(out.read_bytes()))
    print('M6X1_BACK_PROVIDERS='+str(len(manifest['back_providers'])))
    print('M6X1_FRAMES='+str(sum(len(x['frames']) for x in manifest['back_providers'])))

if __name__=='__main__':main()
