#!/usr/bin/env python3
"""Reduce a ForeFlight KML log to a minimal track (time + position only).

Usage:
    python3 main.py 'path/to/file.kml'

Output: 'path/to/file_reduce.kml' (the input file is never modified).
"""

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

KML_NS = "http://www.opengis.net/kml/2.2"
GX_NS = "http://www.google.com/kml/ext/2.2"

ET.register_namespace("", KML_NS)
ET.register_namespace("gx", GX_NS)


def k(tag):
    return f"{{{KML_NS}}}{tag}"


def gx(tag):
    return f"{{{GX_NS}}}{tag}"


def truncate_time(value):
    """Cut fractional seconds to 6 digits (Python datetime precision)."""
    value = value.strip()
    return re.sub(r"(\.\d{6})\d+", r"\1", value)


def fmt(number):
    """Shortest float representation Python can hold; no useless '.0'."""
    f = float(number)
    return str(int(f)) if f.is_integer() else repr(f)


def truncate_coord(value):
    return " ".join(fmt(p) for p in value.split())


def add_marker(doc, name, coord):
    """Add a named point placemark. coord is 'lon lat alt' (space separated)."""
    pm = ET.SubElement(doc, k("Placemark"))
    ET.SubElement(pm, k("name")).text = name
    point = ET.SubElement(pm, k("Point"))
    ET.SubElement(point, k("altitudeMode")).text = "absolute"
    ET.SubElement(point, k("coordinates")).text = ",".join(coord.split())


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python3 main.py 'path/to/file.kml'")

    src = Path(sys.argv[1])
    if not src.is_file():
        sys.exit(f"File not found: {src}")

    dst = src.with_name(f"{src.stem}_r{src.suffix}")

    root = ET.parse(src).getroot()
    track = root.find(f".//{gx('Track')}")
    if track is None:
        sys.exit("No <gx:Track> found in the input file.")

    whens = [truncate_time(e.text) for e in track.findall(k("when"))]
    coords = [truncate_coord(e.text) for e in track.findall(gx("coord"))]
    if len(whens) != len(coords):
        sys.exit(f"Mismatch: {len(whens)} <when> vs {len(coords)} <gx:coord>.")
    if not whens:
        sys.exit("The track contains no points.")

    # Build a brand-new minimal tree
    kml = ET.Element(k("kml"))
    doc = ET.SubElement(kml, k("Document"))

    add_marker(doc, "START", coords[0])

    pm = ET.SubElement(doc, k("Placemark"))
    out_track = ET.SubElement(pm, gx("Track"))
    ET.SubElement(out_track, k("altitudeMode")).text = "absolute"
    ET.SubElement(out_track, k("extrude")).text = "1"
    for w, c in zip(whens, coords):
        ET.SubElement(out_track, k("when")).text = w
        ET.SubElement(out_track, gx("coord")).text = c

    add_marker(doc, "END", coords[-1])

    tree = ET.ElementTree(kml)
    ET.indent(tree, space="  ")
    tree.write(dst, encoding="utf-8", xml_declaration=True)

    in_size, out_size = src.stat().st_size, dst.stat().st_size
    print(f"Points : {len(whens)}")
    print(f"Input  : {in_size:,} bytes")
    print(f"Output : {out_size:,} bytes ({dst})")
    print(f"Reduced: {100 * (1 - out_size / in_size):.1f}%")


if __name__ == "__main__":
    main()