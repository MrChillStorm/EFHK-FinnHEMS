"""Flat-shaded painter's preview of the model (AC3D) from a camera in the object frame (x south, y east, z up).

    python3 preview.py out.png cam_x cam_y cam_z [fov_deg]      looks at the origin
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
AC = os.path.join(HERE, '..', 'Objects', 'e020n60', 'e024n60', 'finnhems-base.ac')
COL = {'facade': (70, 72, 76), 'roof': (60, 60, 58), 'door': (45, 60, 150), 'parts': (150, 150, 150),
       'interior': (190, 190, 186), 'glass': (40, 60, 80), 'letters': (240, 240, 240), 'apron': (95, 95, 92)}


def load():
    L = open(AC).read().split('\n'); polys = []; i = 0; name = None; V = None
    while i < len(L):
        t = L[i].split()
        if t and t[0] == 'name':
            name = L[i].split(None, 1)[1].strip('"')
        elif t and t[0] == 'numvert':
            n = int(t[1]); V = np.array([list(map(float, L[i + 1 + k].split())) for k in range(n)]); i += n
        elif t and t[0] == 'refs':
            n = int(t[1]); idx = [int(L[i + 1 + k].split()[0]) for k in range(n)]; i += n
            P = V[idx]; polys.append((name, np.c_[P[:, 0], -P[:, 2], P[:, 1]]))     # ac (x, z, -y) -> (x, y, z)
        i += 1
    return polys


def render(out, cam, fov=40.0, target=(0, 0, 3)):
    cam, target = np.array(cam, float), np.array(target, float)
    f = target - cam; f /= np.linalg.norm(f); r = np.cross(f, [0, 0, 1]); r /= np.linalg.norm(r); u = np.cross(r, f)
    W, H = 1600, 700; k = W / 2 / math.tan(math.radians(fov / 2)); sun = np.array([0.3, -0.5, 0.8]); sun /= np.linalg.norm(sun)
    img = Image.new('RGB', (W, H), (150, 180, 210)); d = ImageDraw.Draw(img); items = []
    for name, P in load():
        c = P - cam; z = c @ f
        if (z < 0.5).any():
            continue
        n = np.cross(P[1] - P[0], P[2] - P[0]); nn = np.linalg.norm(n)
        if nn < 1e-9:
            continue
        n /= nn
        if n @ (cam - P[0]) < 0 and name not in ('glass', 'letters'):
            continue                                              # back face
        if name.startswith('lens'):
            col = (255, 250, 220)
        else:
            s = 0.55 + 0.45 * max(0.0, n @ sun); col = tuple(int(v * s) for v in COL.get(name, (200, 0, 200)))
        xy = [(W / 2 + k * (q @ r) / zz, H / 2 - k * (q @ u) / zz) for q, zz in zip(c, z)]
        items.append((z.mean(), xy, col, name))
    for z, xy, col, name in sorted(items, key=lambda t: -t[0]):
        d.polygon(xy, fill=col, outline=None if name == 'apron' else tuple(max(0, v - 25) for v in col))
    img.save(out)


if __name__ == '__main__':
    a = sys.argv
    render(a[1], (float(a[2]), float(a[3]), float(a[4])), float(a[5]) if len(a) > 5 else 40.0)
