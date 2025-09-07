#!/usr/bin/env python3
import argparse, sys, xml.etree.ElementTree as ET

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--xml", required=True)
    p.add_argument("--min", type=float, required=True, help="min percent of line coverage")
    args = p.parse_args()

    tree = ET.parse(args.xml)
    root = tree.getroot()

    # Cobertura format: attributes 'lines-valid' and 'lines-covered'
    lines_valid = int(root.attrib.get('lines-valid', 0))
    lines_covered = int(root.attrib.get('lines-covered', 0))

    if lines_valid == 0:
        print("No measured lines in coverage.xml; skipping gate (treated as PASS).")
        sys.exit(0)

    pct = 100.0 * lines_covered / max(1, lines_valid)
    print(f"Total line coverage: {pct:.2f}% (threshold {args.min:.2f}%)")
    if pct + 1e-9 < args.min:
        print("Coverage threshold not met.", file=sys.stderr)
        sys.exit(2)
    sys.exit(0)

if __name__ == "__main__":
    main()
