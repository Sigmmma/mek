#!/usr/bin/python
import re
import fileinput

print("# y forward, z up")
v_index = 1
line_segments = []

for input_line in fileinput.input():
    m = re.match("\\tCoordinate3 { point\\[([ ,.\\-\\d]+)\\] }", input_line)
    if not m:
        continue
    verts = [vs.strip().split(" ") for vs in m.group(1).strip().split(",")]
    line_segments.append([])
    for v in verts:
        print("v " + " ".join(v))
        line_segments[-1].append(str(v_index))
        v_index += 1
for segment in line_segments:
    print("l " + " ".join(segment))
