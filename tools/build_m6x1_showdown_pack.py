#!/usr/bin/env python3
import argparse, hashlib, io, json, urllib.request, zipfile
from pathlib import Path
from PIL import Image, ImageSequence

SPECIES = [
    (152,'chikorita'),(155,'cyndaquil'),(158,'totodile'),(255,'torchic'),
    (650,'chespin'),(653,'fennekin'),(656,'froakie'),(728,'popplio'),(1289,'sprigatito'),
]
# R5 keeps the established nine BACK providers sealed and adds exactly one
# opponent FRONT canary. Broad FRONT / 901 rollout remains blocked.
FRONT_SPECIES = [(155,'cyndaquil',0.72)]
BASE='https://play.pokemonshowdown.com/sprites/ani-back/'
FRONT_BASE='https://play.pokemonshowdown.com/sprites/ani/'

def sha256(b): return hashlib.sha256(b).hexdigest()

def read_gif(url):
    req=urllib.request.Request(url,headers={'User-Agent':'SoulGold-M6X1-build/1.0'})
    with urllib.request.urlopen(req,timeout=30) as r: raw=r.read()
    return raw,Image.open(io.BytesIO(raw))

def frames_from_gif(files,im,prefix):
    frames=[];canvas_w,canvas_h=im.size
    for i,fr in enumerate(ImageSequence.Iterator(im)):
        rgba=fr.convert('RGBA');bio=io.BytesIO();rgba.save(bio,'PNG',optimize=True)
        path=f'frames/{prefix}_{i:03d}.png';files[path]=bio.getvalue()
        duration=int(fr.info.get('duration',im.info.get('duration',100)) or 100)
        frames.append({'path':path,'duration_ms':max(20,duration)})
    if not frames: raise RuntimeError('no frames for '+prefix)
    return frames,canvas_w,canvas_h

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--rom-sha256',required=True)
    ap.add_argument('--output',required=True)
    a=ap.parse_args()
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
    manifest={
        'format':'SOULGOLD_SHOWDOWN_PACK_V1',
        'pack_id':'SOULGOLD_M6X1R5_BACK9_FRONT_CYNDAQUIL_CANARY_20260905',
        'expected_rom_sha256':a.rom_sha256.lower(),
        'front_providers':[],
        'back_providers':[],
        'source':'Pokemon Showdown ani-back + ani FRONT canary',
        'source_base':BASE,
        'front_source_base':FRONT_BASE,
        'front_rollout':'SINGLE_SPECIES_CANARY',
        'front_canary_species':155,
    }
    files={}
    for species,name in SPECIES:
        url=BASE+name+'.gif';raw,im=read_gif(url)
        frames,canvas_w,canvas_h=frames_from_gif(files,im,f'back_{species}_{name}')
        scale=min(1.0,72.0/max(canvas_w,canvas_h))
        manifest['back_providers'].append({
            'species':species,'name':name,'scale':scale,'canvas_width':canvas_w,'canvas_height':canvas_h,
            'source_url':url,'source_gif_sha256':sha256(raw),'frames':frames,
        })
    for species,name,scale in FRONT_SPECIES:
        url=FRONT_BASE+name+'.gif';raw,im=read_gif(url)
        frames,canvas_w,canvas_h=frames_from_gif(files,im,f'front_{species}_{name}')
        manifest['front_providers'].append({
            'species':species,'name':name,'scale':scale,'canvas_width':canvas_w,'canvas_height':canvas_h,
            'source_url':url,'source_gif_sha256':sha256(raw),'frames':frames,
        })
    if len(manifest['front_providers']) != 1 or manifest['front_providers'][0]['species'] != 155:
        raise RuntimeError('R5 FRONT canary contract violated')
    files['manifest.json']=(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n').encode()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in files.items():z.writestr(name,data)
    print('M6X1_PACK='+str(out))
    print('M6X1_PACK_SHA256='+sha256(out.read_bytes()))
    print('M6X1_BACK_PROVIDERS='+str(len(manifest['back_providers'])))
    print('M6X1_FRONT_PROVIDERS='+str(len(manifest['front_providers'])))
    print('M6X1_FRONT_CANARY_SPECIES=155')
    print('M6X1_FRAMES='+str(sum(len(x['frames']) for x in manifest['back_providers']+manifest['front_providers'])))

if __name__=='__main__':main()
