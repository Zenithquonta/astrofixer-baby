"""Chart B: plate-solver centre error and solve time per synthetic test image.

Data: JUnit XML of org.astrofixxer.astro.PlateSolverTest from the JVM harness (gradle test), whose system-out
prints one line per case: name, time in ms, Solved/Failed, and for solved cases the centre error in arcsec.
Set PLATESOLVER_XML to another file; default is the snapshot figures/data/PlateSolverTest.xml. Only lines before the
'=== plate solver summary' marker are used (the summary repeats them).
"""
import os
import re
import xml.etree.ElementTree as ET
import numpy as np
import matplotlib.pyplot as plt
import figstyle as fs

# A snapshot of the JVM harness output is kept in figures/data/ so that the chart is stable; timings vary from run to
# run on a shared machine. build_figures.sh replaces it with a fresh run when RUN_JVM_HARNESS is set.
DEFAULT = os.path.join(fs.OUT, "data", "PlateSolverTest.xml")

GROUPS = [  # (regex on case name, label)
    (r"^wide 60x45 blind", "Wide 60×45°, blind"),
    (r"^wide 60x45 hint", "Wide, hint 15° off"),
    (r"^wide 60x45 mirrored", "Wide, mirrored, blind"),
    (r"^wide, -?\d% corner distortion", "Wide, 1–2% distortion"),
    (r"^12 degree field blind", "12° field, blind"),
    (r"^medium 5 deg with hint", "5° field, hinted"),
    (r"^eyepiece 1 deg", "1° eyepiece, hinted"),
]
LINE = re.compile(r"^(?P<name>.+?)\s+(?P<ms>\d+)\s+ms\s+(?P<res>Solved|Failed)(?P<rest>.*)$")


def parse(path):
    root = ET.parse(path).getroot()
    out = root.find("system-out").text
    out = out.split("=== plate solver summary")[0]
    rows = []
    for ln in out.splitlines():
        m = LINE.match(ln.strip())
        if not m:
            continue
        d = {"name": m["name"], "ms": int(m["ms"]), "solved": m["res"] == "Solved", "rest": m["rest"]}
        e = re.search(r'centre err ([\d.]+)"', m["rest"])
        d["err"] = float(e[1]) if e else None
        rows.append(d)
    return rows


def main():
    path = os.environ.get("PLATESOLVER_XML", DEFAULT)
    rows = parse(path)
    solved = [r for r in rows if r["solved"]]
    failed = [r for r in rows if not r["solved"]]
    print(f"source: {path}")
    print(f"case lines: {len(rows)}  solved: {len(solved)}  failed (negative or expected-fail): {len(failed)}")
    grouped = []
    for rx, label in GROUPS:
        g = [r for r in solved if re.search(rx, r["name"])]
        grouped.append((label, g))
        if g:
            print(f"{label:28s} n={len(g)}  err {min(r['err'] for r in g):5.1f}-{max(r['err'] for r in g):5.1f} arcsec"
                  f"  time {min(r['ms'] for r in g)}-{max(r['ms'] for r in g)} ms")
    assert sum(len(g) for _, g in grouped) == len(solved), "some solved cases fall in no group"
    print(f"negative cases: {len(failed)}; time {min(r['ms'] for r in failed)}-{max(r['ms'] for r in failed)} ms")

    fs.setup()
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(fs.COL_W, 2.3), sharey=True, gridspec_kw={"wspace": 0.08})
    ys = np.arange(len(grouped))[::-1]
    rng = np.random.default_rng(3)
    for y, (label, g) in zip(ys, grouped):
        jit = rng.uniform(-0.16, 0.16, len(g))
        a1.scatter([r["err"] for r in g], y + jit, s=9, marker="o", facecolor=fs.BLUE, edgecolor="white", linewidth=0.3, zorder=3)
        a2.scatter([r["ms"] for r in g], y + jit, s=9, marker="s", facecolor=fs.ORANGE, edgecolor="white", linewidth=0.3, zorder=3)
    a1.set_xscale("log")
    a1.set_xlim(0.05, 60)
    a1.set_xlabel("Centre error (arcsec)")
    a2.set_xlim(0, 600)
    a2.set_xticks([0, 200, 400, 600])
    a2.set_xlabel("Solve time (ms)")
    a1.set_yticks(ys)
    a1.set_yticklabels([f"{lab} ({len(g)})" for lab, g in grouped])
    a1.set_ylim(-0.6, len(grouped) - 0.4)
    a1.grid(axis="y", visible=False)
    a2.grid(axis="y", visible=False)
    a2.tick_params(left=False)
    a2.spines["left"].set_visible(False)
    fs.save(fig, "fig_solver.pdf")


if __name__ == "__main__":
    main()
