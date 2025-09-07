#!/usr/bin/env python3
import argparse, xml.etree.ElementTree as ET

def read_cov_percent(path):
    root = ET.parse(path).getroot()
    if 'line-rate' in root.attrib:
        return float(root.attrib['line-rate']) * 100.0
    lv = root.attrib.get('lines-valid')
    lc = root.attrib.get('lines-covered')
    if lv and lc:
        return 100.0 * (int(lc) / max(1, int(lv)))
    total = 0; covered = 0
    for ln in root.iter('line'):
        total += 1
        if ln.attrib.get('hits') not in (None, '0'):
            covered += 1
    return 100.0 * covered / max(1, total)

def color(p):
    if p >= 95: return "#4c1"
    if p >= 90: return "#97CA00"
    if p >= 80: return "#a4a61d"
    if p >= 70: return "#dfb317"
    if p >= 60: return "#fe7d37"
    return "#e05d44"

SVG = '''<svg xmlns="http://www.w3.org/2000/svg" width="150" height="20" role="img" aria-label="coverage: {pct:.1f}%">
  <linearGradient id="s" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient>
  <mask id="m"><rect width="150" height="20" rx="3" fill="#fff"/></mask>
  <g mask="url(#m)">
    <rect width="80" height="20" fill="#555"/>
    <rect x="80" width="70" height="20" fill="{col}"/>
    <rect width="150" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="40" y="15">coverage</text>
    <text x="113" y="15">{pct:.1f}%</text>
  </g>
</svg>'''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xml", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    pct = read_cov_percent(args.xml)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(SVG.format(pct=pct, col=color(pct)))

if __name__ == "__main__":
    main()
