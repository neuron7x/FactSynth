#!/usr/bin/env python3
import argparse, xml.etree.ElementTree as ET
def read_pct(p):
r=ET.parse(p).getroot()
if 'line-rate' in r.attrib: return float(r.attrib['line-rate'])*100.0
lv=r.attrib.get('lines-valid'); lc=r.attrib.get('lines-covered')
return 100.0*(int(lc)/max(1,int(lv))) if lv and lc else 0.0
def col(p): return "#4c1" if p>=95 else "#97CA00" if p>=90 else "#dfb317"
SVG='''<svg xmlns="http://www.w3.org/2000/svg" width="150" height="20"><rect width="80" height="20" fill="#555"/><rect x="80" width="70" height="20" fill="{c}"/><g fill="#fff" font-family="DejaVu Sans,Verdana,sans-serif" font-size="11"><text x="40" y="14" text-anchor="middle">coverage</text><text x="115" y="14" text-anchor="middle">{p:.1f}%</text></g></svg>'''
if __name__=="__main__":
ap=argparse.ArgumentParser(); ap.add_argument("--xml",required=True); ap.add_argument("--out",required=True); a=ap.parse_args()
pct=read_pct(a.xml); open(a.out,"w").write(SVG.format(p=pct,c=col(pct)))
