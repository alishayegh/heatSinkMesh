#!/usr/bin/env python3
import argparse
import re
import subprocess
import sys


def parse_bounding_box(stl_path):
    """Executes surfaceCheck and extracts min and max bounding box vectors."""
    try:
        cmd = f"surfaceCheck {stl_path}"
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, check=True
        )
        output = result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error executing surfaceCheck on {stl_path}:\n{e.stderr}")
        sys.exit(1)

    # Regex to capture bounding box coordinates
    pattern = r"Bounding Box\s*:\s*\(\s*([-\d.eE]+)\s+([-\d.eE]+)\s+([-\d.eE]+)\s*\)\s*\(\s*([-\d.eE]+)\s+([-\d.eE]+)\s+([-\d.eE]+)\s*\)"
    match = re.search(pattern, output)

    if not match:
        print(
            "Error: Could not extract bounding box from surfaceCheck output."
        )
        sys.exit(1)

    coords = [float(x) for x in match.groups()]
    min_pt = coords[0:3]  # [Xmin, Ymin, Zmin]
    max_pt = coords[3:6]  # [Xmax, Ymax, Zmax]

    return min_pt, max_pt


def calculate_vertices(min_pt, max_pt, snap_directions, scales):
    """Calculates scaled blockMesh vertices snapped to a given plane."""
    x1, y1, z1 = min_pt
    x2, y2, z2 = max_pt

    # Dimensions along each axis
    lx, ly, lz = x2 - x1, y2 - y1, z2 - z1

    # Center of geometry
    cx, cy, cz = (x1 + x2) / 2.0, (y1 + y2) / 2.0, (z1 + z2) / 2.0

    # Extract 3 scaling factors
    scaleX = scales[0]
    scaleY = scales[1]
    scaleZ = scales[2]

    # Scaled dimensions
    sx_l, sy_l, sz_l = scaleX * lx, scaleY * ly, scaleZ * lz

    # Default scaled bounds centered on STL geometry
    bx1, bx2 = cx - sx_l / 2.0, cx + sx_l / 2.0
    by1, by2 = cy - sy_l / 2.0, cy + sy_l / 2.0
    bz1, bz2 = cz - sz_l / 2.0, cz + sz_l / 2.0

    # Apply plane snapping logic
    for snap_direction in snap_directions:
        if snap_direction == "minY":
            by1 = y1
            by2 = y1 + scaleY * ly
        elif snap_direction == "maxY":
            by2 = y2
            by1 = y2 - sy_l
        elif snap_direction == "minX":
            bx1 = x1
            bx2 = x1 + scaleX * lx
        elif snap_direction == "maxX":
            bx2 = x2
            bx1 = x2 - sx_l
        elif snap_direction == "minZ":
            bz1 = z1
            bz2 = z1 + scaleZ * lz
        elif snap_direction == "maxZ":
            bz2 = z2
            bz1 = z2 - sz_l

    # Standard OpenFOAM 8-vertex ordering
    vertices = [
        (bx1, by1, bz1),  # 0
        (bx2, by1, bz1),  # 1
        (bx2, by2, bz1),  # 2
        (bx1, by2, bz1),  # 3
        (bx1, by1, bz2),  # 4
        (bx2, by1, bz2),  # 5
        (bx2, by2, bz2),  # 6
        (bx1, by2, bz2),  # 7
    ]

    return vertices


def print_blockMesh_vertices(vertices):
    """Outputs OpenFOAM formatted vertices list."""
    print("\nvertices")
    print("(")
    for i, v in enumerate(vertices):
        print(f"    ({v[0]:.6f} {v[1]:.6f} {v[2]:.6f}) // {i}")
    print(");")


def main():
    parser = argparse.ArgumentParser(
        description="Generate OpenFOAM blockMesh vertices snapped to surface boundary."
    )
    parser.add_argument(
        "surface", type=str, help="Path to STL surface file (e.g. Surfaces/sink.stl)"
    )
    parser.add_argument(
        "-snap",
        type=str,
        nargs="+",
        required=True,
        choices=["minX", "maxX", "minY", "maxY", "minZ", "maxZ"],
        help="Direction(s) to snap blockMesh boundary",
    )
    parser.add_argument(
        "-scales",
        type=float,
        nargs=3,
        required=True,
        metavar=("SCALE_X", "SCALE_Y", "SCALE_Z"),
        help="Scaling factors along X, Y, and Z axes relative to STL dimensions",
    )

    args = parser.parse_args()

    # 1. Parse Bounding Box from STL
    min_pt, max_pt = parse_bounding_box(args.surface)

    # 2. Compute 8 vertices
    vertices = calculate_vertices(
        min_pt,
        max_pt,
        args.snap,
        args.scales,
    )

    # 3. Print OpenFOAM blockMesh dict compatible block
    print_blockMesh_vertices(vertices)


if __name__ == "__main__":
    main()
