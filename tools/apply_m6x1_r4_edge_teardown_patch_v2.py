#!/usr/bin/env python3
from pathlib import Path
import argparse,importlib.util


def load_base():
    p=Path(__file__).with_name('apply_m6x1_r4_edge_teardown_patch.py')
    spec=importlib.util.spec_from_file_location('m6x1_r4_edge_base',p)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod


def replace_definition(text:str, signature:str, replacement:str)->str:
    """Replace an actual function definition, never a forward declaration.

    The first R4 attempt searched for the next '{' after a signature. For
    RunBattleSoftwareTick that matched the early forward declaration ending in
    ';' and then consumed the next unrelated function body. This scanner skips
    declarations and accepts only a signature whose next non-whitespace token is
    an opening brace.
    """
    pos=0
    while True:
        start=text.find(signature,pos)
        if start<0:
            raise SystemExit('function definition missing: '+signature)
        j=start+len(signature)
        while j<len(text) and text[j] in ' \t\r\n':
            j+=1
        if j<len(text) and text[j]=='{':
            brace=j
            break
        pos=start+len(signature)

    depth=0
    end=None
    for i in range(brace,len(text)):
        c=text[i]
        if c=='{':
            depth+=1
        elif c=='}':
            depth-=1
            if depth==0:
                end=i+1
                break
    if end is None:
        raise SystemExit('function closing brace missing: '+signature)
    return text[:start]+replacement+text[end:]


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--framework',required=True)
    ap.add_argument('--soulgold',required=True)
    a=ap.parse_args()
    base=load_base()
    base.replace_function=replace_definition
    framework=Path(a.framework);soulgold=Path(a.soulgold)
    java=base.patch_java(framework/'android/m6x1/app/src/main/java/com/showpei/soulgold/m6x1/MainActivity.java')
    rom=base.patch_rom(soulgold/'src/battle_main.c')

    patched=(soulgold/'src/battle_main.c').read_text()
    if patched.count('static void RunBattleSoftwareTick(void)\n{') != 1:
        raise SystemExit('R4 RunBattleSoftwareTick definition count is not exactly one')
    if 'static void RunBattleSoftwareTick(void);' not in patched:
        raise SystemExit('R4 accidentally removed RunBattleSoftwareTick forward declaration')
    print('M6X1_R4_EDGE_TEARDOWN_PATCH_V2=PASS java='+java+' rom='+rom)
    print('definition_boundary=FORWARD_DECLARATION_SAFE')

if __name__=='__main__':
    main()
