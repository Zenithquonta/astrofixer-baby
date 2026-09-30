"""Chart A: pointing error against astropy for the old and the new sky-to-horizon formula.

Data: app/src/test/resources/precession_reference.json (66 astropy AltAz cases written by
tools/golden/precession_reference.py). Both formulas are re-implemented here exactly as in the Kotlin code:
  new: astro/Pointing.kt   rayFromPos  (IAU 1976 precession J2000 -> date, then IAU 1982 GMST, Meeus 12.4)
  old: app/src/test/.../PrecessionTest.kt  oldRay  (Earth rotation angle applied to J2000 coordinates, no precession)
"""
import json
import math
import os
import numpy as np
import matplotlib.pyplot as plt
import figstyle as fs

D2R = math.pi / 180
AS2R = D2R / 3600


def jd_from_millis(ms):
    return ms / 86400000.0 + 2440587.5


def horizontal(ra, de, h_rad_extra, lat):
    """Unit vector [east, north, up]; h = hour angle in radians (already includes the sidereal angle)."""
    f = lat * D2R
    h = h_rad_extra
    az = math.atan2(math.sin(h), math.cos(h) * math.sin(f) - math.tan(de) * math.cos(f))
    alt = math.asin(math.sin(f) * math.sin(de) + math.cos(f) * math.cos(de) * math.cos(h))
    return np.array([-math.sin(az) * math.cos(alt), -math.cos(az) * math.cos(alt), math.sin(alt)])


def precession_matrix(t):
    zeta = (2306.2181 * t + 0.30188 * t * t + 0.017998 * t ** 3) * AS2R
    z = (2306.2181 * t + 1.09468 * t * t + 0.018203 * t ** 3) * AS2R
    theta = (2004.3109 * t - 0.42665 * t * t - 0.041833 * t ** 3) * AS2R

    def rz(a):
        return np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])

    ry = np.array([[math.cos(theta), 0, -math.sin(theta)], [0, 1, 0], [math.sin(theta), 0, math.cos(theta)]])
    return rz(z) @ ry @ rz(zeta)  # same matrices and order as Pointing.precessionMatrix


def new_ray(ra, dec, ms, lat, lon):
    jd = jd_from_millis(ms)
    d = jd - 2451545.0
    tc = d / 36525
    gmst = (280.46061837 + 360.98564736629 * d + 0.000387933 * tc * tc - tc ** 3 / 38710000) % 360.0
    m = precession_matrix(tc)
    r, de = ra * D2R, dec * D2R
    v = np.array([math.cos(de) * math.cos(r), math.cos(de) * math.sin(r), math.sin(de)])
    vd = m @ v
    ra_d = math.atan2(vd[1], vd[0])
    de_d = math.asin(max(-1.0, min(1.0, vd[2])))
    return horizontal(ra_d, de_d, gmst * D2R + lon * D2R - ra_d, lat)


def old_ray(ra, dec, ms, lat, lon):
    tu = jd_from_millis(ms) - 2451545.0
    angle = 2 * math.pi * (0.7790572732640 + 1.00273781191135448 * tu)
    return horizontal(ra * D2R, dec * D2R, angle + lon * D2R - ra * D2R, lat)


def sep_arcsec(a, b):
    x = np.cross(a, b)
    return math.atan2(np.linalg.norm(x), float(a @ b)) / D2R * 3600


def main():
    path = os.path.join(fs.REPO, "app/src/test/resources/precession_reference.json")
    cases = json.load(open(path))["cases"]
    rows = []
    for c in cases:
        alt, az = c["altDeg"] * D2R, c["azDeg"] * D2R
        ref = np.array([math.sin(az) * math.cos(alt), math.cos(az) * math.cos(alt), math.sin(alt)])
        e_old = sep_arcsec(ref, old_ray(c["ra"], c["dec"], c["timeMillis"], c["lat"], c["lon"]))
        e_new = sep_arcsec(ref, new_ray(c["ra"], c["dec"], c["timeMillis"], c["lat"], c["lon"]))
        year = 2000.0 + (jd_from_millis(c["timeMillis"]) - 2451545.0) / 365.25
        rows.append((c["star"], c["date"], c["site"], year, e_old, e_new))

    old = np.array([r[4] for r in rows])
    new = np.array([r[5] for r in rows])
    print(f"cases: {len(rows)}")
    io, inw = int(old.argmax()), int(new.argmax())
    print(f"old formula: worst {old.max():.1f} arcsec ({rows[io][0]} {rows[io][1]} {rows[io][2]}), median {np.median(old):.1f}, min {old.min():.2f}")
    print(f"new formula: worst {new.max():.1f} arcsec ({rows[inw][0]} {rows[inw][1]} {rows[inw][2]}), median {np.median(new):.1f}, min {new.min():.2f}")
    for date in sorted({r[1] for r in rows}):
        sel = [r for r in rows if r[1] == date]
        print(f"  {date}: n={len(sel):2d}  old max {max(r[4] for r in sel):7.1f}  new max {max(r[5] for r in sel):5.1f}")
    print(f"sites: {sorted({r[2] for r in rows})}; stars: {len({r[0] for r in rows})}")
    if abs(old.max() - 801) > 1.0 or abs(new.max() - 28) > 1.0:
        raise SystemExit(f"DISCREPANCY with paper: old {old.max():.1f} (paper 801), new {new.max():.1f} (paper 28)")

    fs.setup()
    fig, ax = plt.subplots(figsize=(fs.COL_W, 2.35))
    dates = sorted({r[1] for r in rows})
    rng = np.random.default_rng(7)
    for series, idx, colour, marker, label in (("old", 4, fs.ORANGE, "s", "Old formula"), ("new", 5, fs.BLUE, "o", "New formula")):
        xs, ys = [], []
        for r in rows:
            # jitter within +-0.6 year so that the points of one date stay visible
            xs.append(r[3] + rng.uniform(-0.6, 0.6))
            ys.append(r[idx])
        ax.scatter(xs, ys, s=9, marker=marker, facecolor=colour, edgecolor="white", linewidth=0.3, alpha=0.95, label=label, zorder=3)
    ax.set_yscale("log")
    ax.set_ylim(4, 2000)
    ax.set_xlim(1997, 2053)
    ax.set_xticks([2000, 2010, 2020, 2030, 2040])
    ax.set_xlabel("Date of observation (year)")
    ax.set_ylabel("Error against astropy (arcsec)")
    ax.text(2042.5, old.max(), f"worst {old.max():.0f}\u2033", ha="left", va="center", fontsize=7, color=fs.INK)
    ax.text(2042.5, new.max(), f"worst {new.max():.0f}\u2033", ha="left", va="center", fontsize=7, color=fs.INK)
    ax.legend(loc="upper left", ncol=1, handletextpad=0.2, borderaxespad=0.2)
    fs.save(fig, "fig_precession.pdf")


if __name__ == "__main__":
    main()
