#!/usr/bin/env python3
import argparse
import sys
import xml.etree.ElementTree as ET


def extract_coverage(path: str) -> float | None:
    root = ET.parse(path).getroot()
    if "line-rate" in root.attrib:
        try:
            return float(root.attrib["line-rate"]) * 100.0
        except ValueError:
            pass
    lines_valid = root.attrib.get("lines-valid")
    lines_covered = root.attrib.get("lines-covered")
    if lines_valid is not None and lines_covered is not None:
        lv = int(lines_valid)
        lc = int(lines_covered)
        return 100.0 * lc / max(1, lv)
    covered = 0
    total = 0
    for cl in root.iter("lines"):
        for line in cl.iter("line"):
            total += 1
            if line.attrib.get("hits") not in (None, "0"):
                covered += 1
    if total == 0:
        return None
    return 100.0 * covered / total

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--xml", required=True)
    p.add_argument("--min", type=float, required=True, help="min % of line coverage")
    args = p.parse_args()
    pct = extract_coverage(args.xml)
    if pct is None:
        print("No measured lines; treating as PASS.")
        sys.exit(0)
    print(f"Total line coverage: {pct:.2f}% (threshold {args.min:.2f}%)")
    sys.exit(0 if pct + 1e-9 >= args.min else 2)

if __name__ == "__main__":
    main()
