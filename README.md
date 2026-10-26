# ReduceForeFlightLogs

A tiny Python script that shrinks ForeFlight KML flight logs by stripping everything except time and position.

A ForeFlight export is dominated by per-point data arrays (accuracy, course, speed, altitude, bank, pitch) and metadata. If you only need the track, all of that is dead weight. This script keeps every track point at full resolution and writes a clean, standard KML with a structure similar to the one produced by SkyDemon.

## Features

- Keeps **all** track points, with no decimation
- Removes the whole `ExtendedData` block (data arrays and metadata), styles, and other unused elements
- Truncates timestamps from nanoseconds to microseconds (the precision of Python's `datetime`)
- Writes coordinates with the shortest float representation Python can hold
- Adds `START` and `END` placemarks on the first and last points
- Never modifies the original file
- No dependencies: standard library only

## Requirements

- Python 3.9 or newer

## Usage

```bash
python3 main.py 'path/to/file.kml'
```

The output is written next to the input file, with `_reduce` appended to the name:

```
path/to/file.kml  ->  path/to/file_reduce.kml
```

Example:

```
$ python3 main.py fore.kml
Points : 4175
Input  : 1,838,860 bytes
Output : 432,898 bytes (fore_reduce.kml)
Reduced: 76.5%
```

## Output structure

```
kml
└── Document
    ├── Placemark  "START"   (Point, first track position)
    ├── Placemark            (gx:Track with all <when> / <gx:coord> pairs)
    └── Placemark  "END"     (Point, last track position)
```

Example of the resulting track:

```xml
<gx:Track>
  <altitudeMode>absolute</altitudeMode>
  <extrude>1</extrude>
  <when>2026-10-23T09:58:04.997677Z</when>
  <gx:coord>10.833581 44.326889 747.1</gx:coord>
  ...
</gx:Track>
```

## What is removed

| Element | Reason |
|---|---|
| `ExtendedData` / `SchemaData` arrays (`acc_horiz`, `acc_vert`, `course`, `speed_kts`, `altitude`, `bank`, `pitch`) | About 72% of the original file; `bank` and `pitch` are often empty |
| Metadata `<Data>` entries (source, GPS model, flight title, tail number, pilot, notes) | Not needed for the track |
| Styles (colours, line width, icons) | The viewer uses its defaults |
| Duplicate `altitudeMode`, `interpolate`, `open`, `visibility`, empty `name` | Redundant |

## Notes

- Altitude is taken from `gx:coord` (metres). The separate `altitude` array in the original file is in feet and is discarded.
- The script exits with a clear message if the input has no `<gx:Track>`, or if the number of `<when>` and `<gx:coord>` elements differs.
- Tested on a ForeFlight Web export (`Source: ForeFlight Web`).

## Why is the ForeFlight file so much larger than SkyDemon's?

| | SkyDemon | ForeFlight |
|---|---|---|
| Sampling | ~3.6 s, irregular | 1 s, regular |
| Timestamp precision | 7 digits | 9 digits |
| Per-point extra data | none | 7 parallel arrays |
| Event markers | Takeoff / Landing / Log Start / Stop | Start only |