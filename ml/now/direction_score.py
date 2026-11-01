import numpy as np

def rank_headings(u, v, headings):
    # u: predited eastward wind component m/s 
    # v: northward...
    # headings: allowed travel bearings clockwise from north
    if not np.isfinite([u, v]).all():
        raise ValueError("Wind components must be finite.")

    if not headings:
        raise ValueError("Provide at least one allowed heading.")

    results = []
    for heading in headings:
        heading = float(heading) % 360
        angle = np.deg2rad(heading)

        # Positive along-wind means wind moves with the drone.
        along_wind = u * np.sin(angle) + v * np.cos(angle)

        # Positive opposing-wind component.
        headwind = max(0.0, -along_wind)

        results.append({
            "heading_deg": heading,
            "headwind_ms": float(headwind),
            "along_wind_ms": float(along_wind),
        })

        return sorted(results, key=lambda row: row["headwind_ms"])
