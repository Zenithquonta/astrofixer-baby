"""Chart C: what the bundled data holds.

(a) Deep-sky objects by type, counted from app/src/main/assets/sky_catalog.json.gz (field "dso", key "t";
    layout read by astro/Catalog.kt: root.dso[].t is Ga/Oc/Gc/Ne).
(b) Solver stars per magnitude bin, decoded from app/src/main/assets/solver_stars.bin with the layout documented
    in astro/SolverStars.kt (header, cells, offsets, then 5-byte records whose last byte is the magnitude).
"""
import collections
import gzip
import json
import os
import struct
import numpy as np
import matplotlib.pyplot as plt
import figstyle as fs

TYPE_LABELS = {"Ga": "Galaxies", "Ne": "Nebulae", "Oc": "Open clusters", "Gc": "Globular clusters"}


def read_solver_mags(path):
    data = open(path, "rb").read()
    assert data[:4] == b"AFSS", "not a solver star file"
    version, bands = struct.unpack_from("<HH", data, 4)
    (count,) = struct.unpack_from("<I", data, 8)
    mag_min, mag_step, mag_limit = struct.unpack_from("<fff", data, 12)
    cells = struct.unpack_from("<%dH" % bands, data, 24)
    total = sum(cells)
    off_at = 24 + 2 * bands
    rec_at = off_at + 4 * (total + 1)
    assert len(data) == rec_at + 5 * count, "wrong file size"
    rec = np.frombuffer(data, dtype=np.uint8, count=5 * count, offset=rec_at).reshape(count, 5)
    mags = mag_min + rec[:, 4].astype(np.float64) * mag_step
    return dict(version=version, bands=bands, count=count, mag_min=mag_min, mag_step=mag_step,
                mag_limit=mag_limit, size=len(data)), mags


def main():
    cat = json.load(gzip.open(os.path.join(fs.REPO, "app/src/main/assets/sky_catalog.json.gz")))
    types = collections.Counter(o["t"] for o in cat["dso"])
    print(f"deep-sky objects: {len(cat['dso'])}; stars in catalogue: {len(cat['stars'])}; boundary edges: {len(cat['boundaries'])}")
    for k, v in types.most_common():
        print(f"  {k} {TYPE_LABELS[k]:17s} {v:6d}  ({100 * v / len(cat['dso']):.1f}%)")

    hdr, mags = read_solver_mags(os.path.join(fs.REPO, "app/src/main/assets/solver_stars.bin"))
    print(f"solver_stars.bin: {hdr['count']} stars, {hdr['size']} bytes ({hdr['size'] / 1e6:.2f} MB), version {hdr['version']}, "
          f"bands {hdr['bands']}, magnitude limit {hdr['mag_limit']:.1f}, brightest {mags.min():.2f}, faintest {mags.max():.2f}")
    edges = [-2, 4, 5, 6, 7, 8, 9, 10, 10.55]
    labels = ["<4", "4–5", "5–6", "6–7", "7–8", "8–9", "9–10", "10–10.5"]
    # half-open bins [lo, hi); a star at exactly 10.5 stays in the last bin (upper edge 10.55)
    counts, _ = np.histogram(mags, bins=edges)
    assert counts.sum() == hdr["count"]
    for lab, c in zip(labels, counts):
        print(f"  mag {lab:10s} {c:7d}")
    print(f"  brighter than 6.0: {(mags < 6.0).sum()}; brighter than 8.0: {(mags < 8.0).sum()}; up to 10.0: {(mags <= 10.0).sum()}")

    fs.setup()
    fig, (a, b) = plt.subplots(1, 2, figsize=(fs.COL_W, 2.0), gridspec_kw={"width_ratios": [1, 1.25], "wspace": 0.5})
    order = [k for k, _ in types.most_common()]
    ys = np.arange(len(order))[::-1]
    vals = [types[k] for k in order]
    a.barh(ys, vals, color=fs.BLUE, height=0.62, zorder=3)
    for y, v in zip(ys, vals):
        a.text(v + 1500, y, f"{v:,}", va="center", ha="left", fontsize=6.5, color=fs.INK)
    a.set_yticks(ys)
    a.set_yticklabels([TYPE_LABELS[k] for k in order], fontsize=6.5)
    a.set_xlim(0, 135000)
    a.set_xticks([0, 40000, 80000])
    a.set_xticklabels(["0", "40k", "80k"])
    a.set_xlabel("Objects")
    a.set_title("(a) Deep-sky objects", fontsize=7.5, loc="left")
    a.grid(axis="y", visible=False)

    xs = np.arange(len(labels))
    b.bar(xs, counts, color=fs.ORANGE, width=0.72, zorder=3)
    for x, c in zip(xs, counts):
        if c >= 5000:
            b.text(x, c + 6000, f"{c / 1000:.0f}k" if c >= 10000 else f"{c / 1000:.1f}k", ha="center", va="bottom", fontsize=6)
    b.set_xticks(xs)
    b.set_xticklabels(labels, rotation=45, ha="right", fontsize=6.5)
    b.set_ylim(0, 260000)
    b.set_yticks([0, 100000, 200000])
    b.set_yticklabels(["0", "100k", "200k"])
    b.set_xlabel("V magnitude")
    b.set_ylabel("Stars")
    b.set_title("(b) Solver stars", fontsize=7.5, loc="left")
    b.grid(axis="x", visible=False)
    fs.save(fig, "fig_data.pdf")


if __name__ == "__main__":
    main()
