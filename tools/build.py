"""The FinnHEMS base at Helsinki-Vantaa (EFHK) as a FlightGear scenery object, lit for the HDR renderer.

Footprint and place from OpenStreetMap (way 25499716, Vesikuja 9; apron way 173915260; osm.json, (c) OpenStreetMap
contributors, ODbL); the front's layout and heights from a 2018 photo of it across runway 15/33 (an EC135 in front
for scale). The building is 44 m along 161 deg and 17.3 m deep, 7.3 m high; along its west front, north to south:
the hangar's blue fabric door (opens: /scenery/finnhems/door-closed), the lettering, a cantilevered canopy box over
the entrance and the office wing, the ground floor glazed behind white posts.

Lights (compositor <light>s, HDR): six high-bays in the hangar, four apron floodlights under the roof edge, three
downlights in the canopy, five uplights on the lettering and nine ceiling panels in the ground-floor offices, their
lenses glowing (Effects/model-pbr); on as the sun sets (sun 4 deg up to 2 deg down), dimmed with /scenery/finnhems/dim (0 full, 1 off), all off with
/scenery/finnhems/lights-off. FlightGear's lights cast no shadows: the floods light a parked helicopter's cockpit
through its roof, so keep them low.

    python3 build.py        writes ../Objects/e020n60/e024n60/: 3351955.stg, finnhems-base.xml/.ac and textures
"""
import json, math, os, random
from PIL import Image, ImageDraw, ImageFont

import acmesh as A

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'Objects', 'e020n60', 'e024n60')
TILE = 3351955                          # SGBucket index of 60.3169 N 24.9833 E
ELEV = 54.30                            # m, the ground at the building's centre (FlightGear 2024.2, WS3: 54.20-54.35 round it)
NAME = 'finnhems-base'

# ---------------------------------------------------------------- frames

LAT0, LON0 = 60.3169388, 24.9833123     # the OSM building's centre; ENU metres (east, north) about it
KE, KN = math.cos(math.radians(LAT0)) * 111320.0, 110950.0
AXIS = 161.0                            # deg true, the building's long axis (its east side 160, office front 162)
AE, AN = math.sin(math.radians(AXIS)), math.cos(math.radians(AXIS))     # u: along the front, north to south
NE, NN = -AN, AE                                                        # v: into the building (east-north-east)
L, D, H = 44.0, 17.3, 7.3               # length, depth, roof height
S_CORNER = (0.92, -22.13)               # OSM's south-west corner: the front's south end
OE, ON = S_CORNER[0] - L * AE, S_CORNER[1] - L * AN                     # the front's north end, u = v = 0
CE, CN = OE + L / 2 * AE + D / 2 * NE, ON + L / 2 * AN + D / 2 * NN    # the model's origin: the building's centre


def enu(u, v):
    return OE + u * AE + v * NE, ON + u * AN + v * NN


def P(u, v, z):
    """Building frame (u along the front, v in, z up) -> FlightGear's object frame (x south, y east, z up)."""
    e, n = enu(u, v)
    return (-(n - CN), e - CE, z)


def N(du, dv, dz=0.0):
    return (-(du * AN + dv * NN), du * AE + dv * NE, dz)


def latlon(e, n):
    return LAT0 + n / KN, LON0 + e / KE


# ---------------------------------------------------------------- textures

PARTS = {                               # flat colours in parts.png: name -> rgb
    'floor': (150, 152, 150), 'wall': (180, 182, 180), 'ceiling': (120, 122, 124), 'post': (228, 228, 224),
    'coping': (150, 152, 154), 'darkglass': (22, 26, 30), 'body': (52, 54, 56), 'metal': (182, 184, 186),
    'carpet': (92, 96, 102), 'office-wall': (226, 222, 212), 'lens': (255, 255, 255), 'frame': (40, 42, 44),
}


def textures():
    rnd = random.Random(7)
    def noisy(w, h, rgb, amp):
        im = Image.new('RGB', (w, h)); px = im.load()
        for y in range(h):
            for x in range(w):
                d = rnd.randint(-amp, amp)
                px[x, y] = tuple(max(0, min(255, c + d)) for c in rgb)
        return im
    im = noisy(128, 256, (66, 68, 71), 3); d = ImageDraw.Draw(im)          # cladding: 1.2 m panels, 2.4 m high
    d.line([(0, 0), (0, 255)], fill=(38, 39, 41), width=2); d.line([(2, 0), (2, 255)], fill=(82, 84, 87))
    d.line([(0, 0), (127, 0)], fill=(52, 53, 56))
    im.save(os.path.join(OUT, 'facade.png'))
    im = Image.new('RGB', (64, 128)); d = ImageDraw.Draw(im)                # fabric door: a fold every 0.55 m
    for y in range(128):
        t = y / 128.0
        s = 0.80 + 0.35 * math.sin(math.pi * t) - (0.35 if y > 123 else 0)
        d.line([(0, y), (63, y)], fill=tuple(int(c * s) for c in (40, 56, 140)))
    im.save(os.path.join(OUT, 'door.png'))
    noisy(256, 256, (58, 58, 57), 6).save(os.path.join(OUT, 'roof.png'))   # bitumen felt, 4 m
    im = noisy(512, 512, (80, 80, 78), 9)                                   # asphalt, 8 m
    d = ImageDraw.Draw(im)
    for _ in range(40):
        x, y = rnd.randrange(512), rnd.randrange(512)
        d.line([(x, y), (x + rnd.randint(-40, 40), y + rnd.randint(-40, 40))], fill=(66, 66, 65), width=1)
    im.save(os.path.join(OUT, 'apron.png'))
    im = Image.new('RGB', (64, 64), (255, 0, 255)); d = ImageDraw.Draw(im)  # flat colours, 8 px cells
    for k, rgb in enumerate(PARTS.values()):
        x, y = 8 * (k % 8), 8 * (k // 8); d.rectangle([x, y, x + 7, y + 7], fill=rgb)
    im.save(os.path.join(OUT, 'parts.png'))
    im = Image.new('RGBA', (2048, 512), (255, 255, 255, 0)); d = ImageDraw.Draw(im)   # the lettering, white
    f = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf', 400)
    w = d.textlength('FinnHEMS', font=f)
    d.text((1024, 256), 'FinnHEMS', font=f, fill=(250, 250, 250, 255), anchor='mm')
    im.save(os.path.join(OUT, 'letters.png'))
    return w


def part(name):
    k = list(PARTS).index(name)
    return ((8 * (k % 8) + 4) / 64.0, 1 - (8 * (k // 8) + 4) / 64.0)


# ---------------------------------------------------------------- geometry helpers

def quad(o, pts, uvs, normal):
    o.face([P(*p) for p in pts], uvs, N(*normal))


def wall(o, a, b, z0, z1, normal, pu=1.2, pv=2.4, s0=0.0):
    """A vertical wall from a to b (u, v), z0 to z1, its texture tiled every pu along and pv up."""
    s1 = s0 + math.hypot(b[0] - a[0], b[1] - a[1])
    quad(o, [(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)],
         [(s0 / pu, z0 / pv), (s1 / pu, z0 / pv), (s1 / pu, z1 / pv), (s0 / pu, z1 / pv)], normal)


def flat(o, u0, u1, v0, v1, z, up, uv=None, pu=4.0):
    uvs = uv and [uv] * 4 or [(u0 / pu, v0 / pu), (u1 / pu, v0 / pu), (u1 / pu, v1 / pu), (u0 / pu, v1 / pu)]
    quad(o, [(u0, v0, z), (u1, v0, z), (u1, v1, z), (u0, v1, z)], uvs, (0, 0, 1 if up else -1))


def box(o, u0, u1, v0, v1, z0, z1, uv, bottom=False):
    c = [uv] * 4
    quad(o, [(u0, v0, z1), (u1, v0, z1), (u1, v1, z1), (u0, v1, z1)], c, (0, 0, 1))
    if bottom:
        quad(o, [(u0, v0, z0), (u1, v0, z0), (u1, v1, z0), (u0, v1, z0)], c, (0, 0, -1))
    for (a, b, n) in (((u0, v0), (u1, v0), (0, -1)), ((u1, v0), (u1, v1), (1, 0)), ((u1, v1), (u0, v1), (0, 1)),
                      ((u0, v1), (u0, v0), (-1, 0))):
        quad(o, [(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)], c, n)


def cylinder(o, cu, cv, r, z0, z1, uv, n=14, top=True):
    ring = [(cu + r * math.cos(2 * math.pi * k / n), cv + r * math.sin(2 * math.pi * k / n)) for k in range(n)]
    for k in range(n):
        a, b = ring[k], ring[(k + 1) % n]; m = math.atan2((a[1] + b[1]) / 2 - cv, (a[0] + b[0]) / 2 - cu)
        quad(o, [(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)], [uv] * 4,
             (math.cos(m), math.sin(m)))
    if top:
        quad(o, [(p[0], p[1], z1) for p in ring], [uv] * n, (0, 0, 1))


def disc(o, cu, cv, r, z, uv, up, n=14):
    quad(o, [(cu + r * math.cos(2 * math.pi * k / n), cv + r * math.sin(2 * math.pi * k / n), z) for k in range(n)],
         [uv] * n, (0, 0, 1 if up else -1))


def room(o, poly, z0, z1, floor, walls, ceiling, skip=(), pv=None):
    """A room's inside: floor, ceiling and walls facing in (poly counter-clockwise in u, v), but the walls in skip."""
    quad(o, [(u, v, z0) for u, v in poly], [floor] * len(poly), (0, 0, 1))
    quad(o, [(u, v, z1) for u, v in poly], [ceiling] * len(poly), (0, 0, -1))
    for k, (a, b) in enumerate(zip(poly, poly[1:] + poly[:1])):
        if k not in skip:
            quad(o, [(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)], [walls] * 4,
                 (-(b[1] - a[1]), b[0] - a[0]))


def earclip(poly):
    """Triangles of a simple polygon (x, y), counter-clockwise."""
    pts = list(range(len(poly))); tris = []
    cross = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    def inside(p, a, b, c):
        return cross(a, b, p) >= 0 and cross(b, c, p) >= 0 and cross(c, a, p) >= 0
    while len(pts) > 3:
        for k in range(len(pts)):
            i, j, m = pts[k - 1], pts[k], pts[(k + 1) % len(pts)]
            a, b, c = poly[i], poly[j], poly[m]
            if abs(cross(a, b, c)) <= 1e-9:                 # collinear: drop the point
                pts.pop(k); break
            if cross(a, b, c) < 0:
                continue
            if any(inside(poly[q], a, b, c) for q in pts if q not in (i, j, m)):
                continue
            tris.append((i, j, m)); pts.pop(k); break
        else:
            break
    return tris + [tuple(pts)] if len(pts) == 3 else tris


# ---------------------------------------------------------------- the building

DOOR = (0.4, 9.8, 7.0)                  # u from, to; height
GLAZE_Z, RECESS = 2.1, 1.2              # the ground floor's glazing: top, set back
CANOPY = (20.3, 28.7, 2.5, 6.7, 2.2, 3.2)   # u from, to; z bottom, top; out at the bottom, the top
POSTS = (10.5, 14.9, 19.3, 24.0, 28.8, 33.4, 37.9, 43.4)
LETTERS = (10.6, 19.5, 4.6, 6.4)        # u from, to; z from, to
WINDOWS = ((28.9, 32.7), (39.4, 43.1))  # the office's upper windows, u; z 3.8 to 5.2
HANGAR = [(0.3, 0.3), (9.9, 0.3), (9.9, 5.5), (18.8, 5.5), (18.8, 17.0), (0.3, 17.0)]
OFFICE = [(9.9, RECESS), (43.6, RECESS), (43.6, 5.2), (9.9, 5.2)]
FLOOR_Z = 0.10                          # floors above the apron (0.04)


def build():
    tex_w = textures()
    fac = A.Obj('facade', 'facade.png'); roof = A.Obj('roof', 'roof.png'); door = A.Obj('door', 'door.png')
    parts = A.Obj('parts', 'parts.png'); inside = A.Obj('interior', 'parts.png'); glass = A.Obj('glass', None, A.GLASS)
    letters = A.Obj('letters', 'letters.png'); apron = A.Obj('apron', 'apron.png')
    lens = {k: A.Obj('lens-' + k, 'parts.png') for k in ('highbay', 'flood', 'downlight', 'washer', 'office', 'off')}
    d0, d1, dh = DOOR
    # front (v = 0): around the door, the upper facade, the glazed ground floor set back behind posts
    wall(fac, (0, 0), (d0, 0), 0, H, (0, -1))
    wall(fac, (d0, 0), (d1, 0), dh, H, (0, -1), s0=d0)
    wall(fac, (d1, 0), (L, 0), GLAZE_Z, H, (0, -1), s0=d1)
    wall(fac, (L - 0.3, 0), (L, 0), 0, GLAZE_Z, (0, -1), s0=L - 0.3)
    flat(fac, d1, L - 0.3, 0, RECESS, GLAZE_Z, False, pu=1.2)                     # the soffit over the glazing
    wall(fac, (d1, 0), (d1, RECESS), 0, GLAZE_Z, (1, 0))
    wall(fac, (L - 0.3, RECESS), (L - 0.3, 0), 0, GLAZE_Z, (-1, 0))
    quad(glass, [(d1, RECESS, 0), (L - 0.3, RECESS, 0), (L - 0.3, RECESS, GLAZE_Z), (d1, RECESS, GLAZE_Z)], [(0, 0)] * 4,
         (0, -1))
    for u in POSTS:
        box(parts, u - 0.12, u + 0.12, -0.05, 0.19, 0, GLAZE_Z, part('post'))
    # the door's reveal and the door, a fabric door bunching up under its head as it opens
    wall(fac, (d0, 0), (d0, 0.3), 0, dh, (1, 0)); wall(fac, (d1, 0.3), (d1, 0), 0, dh, (-1, 0))
    flat(fac, d0, d1, 0, 0.3, dh, False, pu=1.2)
    for normal in ((0, -1), (0, 1)):
        quad(door, [(d0, 0.15, 0), (d1, 0.15, 0), (d1, 0.15, dh), (d0, 0.15, dh)],
             [(0, 0), ((d1 - d0) / 2, 0), ((d1 - d0) / 2, dh / 0.55), (0, dh / 0.55)], normal)
    # ends, back, roof and its coping
    wall(fac, (0, D), (0, 0), 0, H, (-1, 0)); wall(fac, (L, 0), (L, D), 0, H, (1, 0)); wall(fac, (L, D), (0, D), 0, H, (0, 1))
    flat(roof, 0, L, 0, D, H, True)
    for (u0, u1, v0, v1) in ((0, L, -0.05, 0.25), (0, L, D - 0.25, D + 0.05), (-0.05, 0.25, 0, D), (L - 0.25, L + 0.05, 0, D)):
        box(parts, u0, u1, v0, v1, H, H + 0.25, part('coping'))
    # the canopy box over the entrance: its front leans out toward the top
    cu0, cu1, cz0, cz1, co0, co1 = CANOPY
    flat(fac, cu0, cu1, -co1, 0, cz1, True, pu=1.2)
    flat(fac, cu0, cu1, -co0, 0, cz0, False, pu=1.2)
    quad(parts, [(cu0, -co0, cz0), (cu1, -co0, cz0), (cu1, -co1, cz1), (cu0, -co1, cz1)], [part('darkglass')] * 4,
         (0, -(cz1 - cz0), -(co1 - co0)))
    for u, s in ((cu0, -1), (cu1, 1)):
        quad(fac, [(u, 0, cz0), (u, -co0, cz0), (u, -co1, cz1), (u, 0, cz1)],
             [(0, cz0 / 2.4), (co0 / 1.2, cz0 / 2.4), (co1 / 1.2, cz1 / 2.4), (0, cz1 / 2.4)], (s, 0))
    # lettering and upper windows
    lu0, lu1, lz0, lz1 = LETTERS
    quad(letters, [(lu0, -0.04, lz0), (lu1, -0.04, lz0), (lu1, -0.04, lz1), (lu0, -0.04, lz1)],
         [(0, 0), (1, 0), (1, 1), (0, 1)], (0, -1))
    for u0, u1 in WINDOWS:
        quad(parts, [(u0, -0.02, 3.8), (u1, -0.02, 3.8), (u1, -0.02, 5.2), (u0, -0.02, 5.2)], [part('darkglass')] * 4, (0, -1))
        box(parts, u0 - 0.05, u1 + 0.05, -0.08, 0, 3.75, 3.8, part('frame'))
    # roof equipment (from the photo): vent stacks, two units, a mast and lamp poles at the edge
    for u, v in ((14.1, 4.0), (16.0, 6.5), (18.5, 3.5), (29.1, 5.0), (38.8, 4.5)):
        cylinder(parts, u, v, 0.32, H, H + 0.9, part('metal'))
        cylinder(parts, u, v, 0.45, H + 0.9, H + 1.05, part('metal'))
    for u, v in ((22.5, 9.0), (33.0, 12.0)):
        box(parts, u - 0.7, u + 0.7, v - 0.5, v + 0.5, H, H + 0.9, part('metal'))
    cylinder(parts, 32.5, 8.0, 0.05, H, H + 3.0, part('metal'), n=6)
    for u in (9.9, 38.2):
        cylinder(parts, u, 0.6, 0.05, H, H + 1.6, part('body'), n=6)
        box(parts, u - 0.15, u + 0.15, 0.45, 0.75, H + 1.6, H + 1.8, part('body'), bottom=True)
    # inside: the hangar (L-shaped round the offices) and the ground floor offices behind the glazing
    room(inside, HANGAR, FLOOR_Z, dh, part('floor'), part('wall'), part('ceiling'), skip=(0,))
    wall(inside, (0.3, 0.3), (d0, 0.3), FLOOR_Z, dh, (0, 1)); wall(inside, (d1, 0.3), (9.9, 0.3), FLOOR_Z, dh, (0, 1))
    room(inside, OFFICE, FLOOR_Z, 2.8, part('carpet'), part('office-wall'), part('ceiling'), skip=(0,))
    wall(inside, (9.9, RECESS), (43.6, RECESS), GLAZE_Z, 2.8, (0, 1))
    # the apron: OSM's, and in front of the building to its line; world-aligned texture so overlaps match
    lights = fixtures(parts, lens)
    apron_polys = [osm_apron(), [enu(-4, -8), enu(L + 2, -8), enu(L + 2, 0.02), enu(-4, 0.02)]]
    for poly in apron_polys:
        if sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1])) < 0:   # clockwise (east, north)
            poly = poly[::-1]
        for tri in earclip([(e, n) for e, n in poly]):
            ps = [poly[t] for t in tri]
            apron.face([(-(n - CN), e - CE, 0.04) for e, n in ps], [((e - CE) / 8, (n - CN) / 8) for e, n in ps], (0, 0, 1))
    objs = [fac, roof, door, parts, inside, glass, letters, apron] + list(lens.values())
    A.write(os.path.join(OUT, NAME + '.ac'), objs)
    write_xml(lights)
    write_stg()
    print('letters %.0f px wide; %d lights' % (tex_w, len(lights)))


def osm_apron():
    d = json.load(open(os.path.join(HERE, 'osm.json')))
    way = next(e for e in d['elements'] if e['id'] == 173915260)
    pts = [((p['lon'] - LON0) * KE, (p['lat'] - LAT0) * KN) for p in way['geometry']]
    return pts[:-1] if pts[0] == pts[-1] else pts


# ---------------------------------------------------------------- lights

WARM, NEUTRAL, COOL = (1.0, 0.86, 0.70), (1.0, 0.93, 0.84), (1.0, 0.97, 0.92)   # 3000, 4000, 5000 K
SUN_OFF, SUN_ON = 1.50, 1.60            # sun-angle-rad (from the zenith): off with the sun 4 deg up, full 2 deg down
# The HDR pipeline has no photometric units, and its range from night to day is compressed: a unit of its radiance is
# about 635 cd/m2 by day (from its sun: a flat spectrum of 1 W/(m2 sr nm), 73,000 cd/m2, comes out of fgdata's
# Shaders/HDR/atmos_spectral.glsl at a luminance of 115) and about 1 cd/m2 at night (from its night ambient). The
# lights keep their cd and the lenses their cd/m2, converted by UNITS: units per cd as the sun goes from 6 deg up to
# 6 deg down, geometric between.
HDR_CD = 635.0
UNITS = [(math.radians(90 - el), HDR_CD ** -min(1.0, max(0.0, (el + 6) / 12))) for el in range(6, -7, -1)]
LENS_NITS = {'highbay': (1500, NEUTRAL), 'flood': (2500, COOL), 'downlight': (800, WARM),   # cd/m2: far below a
             'washer': (300, NEUTRAL), 'office': (200, WARM)}                                # real LED's, or they bloom


def fixtures(parts, lens):
    """The fixtures' bodies and lenses, and their lights: (name, position, aim or None, rgb, cd, cutoff, exponent,
    range) in the object frame."""
    out = []
    def spot(name, at, aim, rgb, cd, half, rng):
        """A spot of peak intensity cd, half of it at `half` deg off its axis. FlightGear's cone has a hard edge, so
        its exponent (cos^e) and cutoff fade it to 3 % there."""
        e = math.log(0.5) / math.log(math.cos(math.radians(half)))
        cut = math.degrees(math.acos(0.03 ** (1 / e)))
        out.append((name, P(*at), P(*aim), rgb, cd, round(cut, 1), round(e, 2), rng))
    lu, lo = part('lens'), part('frame')
    dark = lens['off']
    for k, (u, v) in enumerate(((5.0, 3.0), (5.0, 9.5), (5.0, 15.0), (12.0, 9.5), (12.0, 15.0), (17.0, 12.0))):
        cylinder(parts, u, v, 0.23, 6.75, DOOR[2], part('body'), top=False)
        disc(lens['highbay'], u, v, 0.21, 6.74, lu, False); disc(dark, u, v, 0.21, 6.745, lo, False)
        spot('highbay-%d' % k, (u, v, 6.7), (u, v, 0), NEUTRAL, 1500, 45, 20)
    for k, u in enumerate((3.0, 14.0, 33.0, 41.0)):
        box(parts, u - 0.25, u + 0.25, -0.35, -0.05, 6.85, 7.15, part('body'), bottom=True)
        for o, vv, c in ((lens['flood'], -0.36, lu), (dark, -0.355, lo)):
            quad(o, [(u - 0.22, vv, 6.88), (u + 0.22, vv, 6.88), (u + 0.22, vv, 7.12), (u - 0.22, vv, 7.12)], [c] * 4,
                 (0, -1, -0.4))
        spot('flood-%d' % k, (u, -0.4, 6.95), (u, -18.0, 0), COOL, 2500, 28, 60)
    for k, u in enumerate((22.0, 24.5, 27.0)):
        disc(lens['downlight'], u, -1.4, 0.09, CANOPY[2] - 0.01, lu, False)
        disc(dark, u, -1.4, 0.09, CANOPY[2] - 0.005, lo, False)
        spot('downlight-%d' % k, (u, -1.4, CANOPY[2] - 0.05), (u, -1.4, 0), WARM, 250, 35, 8)
    for k, u in enumerate((11.0, 12.9, 14.8, 16.7, 18.6)):          # five, so that every letter is lit
        box(parts, u - 0.15, u + 0.15, -0.35, -0.10, 3.88, 3.98, part('body'), bottom=True)
        flat(lens['washer'], u - 0.12, u + 0.12, -0.32, -0.13, 3.99, True, uv=lu)
        flat(dark, u - 0.12, u + 0.12, -0.32, -0.13, 3.985, True, uv=lo)
        spot('washer-%d' % k, (u, -0.45, 4.05), (u, 0, 5.5), NEUTRAL, 80, 30, 4)
    for k, u in enumerate([12.0 + 3.8 * i for i in range(9)]):
        flat(lens['office'], u - 0.3, u + 0.3, 2.9, 3.5, 2.79, False, uv=lu)
        flat(dark, u - 0.3, u + 0.3, 2.9, 3.5, 2.795, False, uv=part('wall'))
        out.append(('office-%d' % k, P(u, 3.2, 2.7), None, WARM, 60, 0, 0, 6))
    return out


# ---------------------------------------------------------------- XML and STG

def write_xml(lights):
    x = ['<?xml version="1.0" encoding="UTF-8"?>', '',
         '<!-- The FinnHEMS base at EFHK: written by tools/build.py (see there for sources). HDR lights; door:',
         '     /scenery/finnhems/door-closed, lights: /scenery/finnhems/dim (0-1), /scenery/finnhems/lights-off -->', '',
         '<PropertyList>', '',
         '  <path>%s.ac</path>' % NAME, '']
    def effect(parent, objs, params):
        x.extend(['  <effect>', '    <inherits-from>%s</inherits-from>' % parent, '    <parameters>'] +
                 ['      ' + p for p in params] + ['    </parameters>'] +
                 ['    <object-name>%s</object-name>' % o for o in objs] + ['  </effect>', ''])
    effect('Effects/model-default', ['facade', 'roof', 'parts', 'interior', 'lens-off'],
           ['<pbr-metallic type="float"> 0.0 </pbr-metallic>', '<pbr-roughness type="float"> 0.75 </pbr-roughness>'])
    effect('Effects/model-default', ['apron'], ['<pbr-roughness type="float"> 0.95 </pbr-roughness>'])
    effect('Effects/model-default', ['door'], ['<pbr-roughness type="float"> 0.6 </pbr-roughness>'])
    effect('Effects/model-default', ['letters'], ['<alpha-cutoff type="float"> 0.5 </alpha-cutoff>',
                                                  '<pbr-roughness type="float"> 0.5 </pbr-roughness>'])
    for k, (nits, rgb) in LENS_NITS.items():
        effect('Effects/model-pbr', ['lens-' + k],
               ['<emissive-factor type="vec3d"> 0 0 0 </emissive-factor>',
                '<base-color-factor type="vec4d"> 1 1 1 1 </base-color-factor>', '<metallic-factor type="float"> 0 </metallic-factor>',
                '<roughness-factor type="float"> 0.3 </roughness-factor>'])
    # the lenses' glow, cd/m2 faded in with the sun, dimmed, and converted (UNITS)
    for k, (nits, rgb) in LENS_NITS.items():
        x.extend(['  <animation>', '    <type>pbr</type>', '    <object-name>lens-%s</object-name>' % k, '    <emissive-factor>'])
        for c, v in zip(('red', 'green', 'blue'), rgb):
            x.extend(['      <%s>' % c] + level_xml(nits * v, '        ') + ['      </%s>' % c])
        x.extend(['    </emissive-factor>', '  </animation>', ''])
    top = P(0, 0, DOOR[2])
    x.extend(['  <animation>', '    <type>scale</type>', '    <object-name>door</object-name>',
              '    <property>/scenery/finnhems/door-closed</property>',
              '    <x-factor> 0 </x-factor>', '    <x-offset> 1 </x-offset>', '    <y-factor> 0 </y-factor>',
              '    <y-offset> 1 </y-offset>', '    <z-factor> 0.88 </z-factor>', '    <z-offset> 0.12 </z-offset>',
              '    <center>', '      <x-m> %.3f </x-m>' % top[0], '      <y-m> %.3f </y-m>' % top[1],
              '      <z-m> %.3f </z-m>' % top[2], '    </center>', '  </animation>', ''])
    for name, p, aim, rgb, cd, cut, e, rng in lights:
        x.extend(['  <light>', '    <name>%s</name>' % name, '    <type>%s</type>' % ('spot' if aim else 'point'),
                  '    <position>', '      <x-m> %.3f </x-m>' % p[0], '      <y-m> %.3f </y-m>' % p[1],
                  '      <z-m> %.3f </z-m>' % p[2], '    </position>'])
        if aim:
            x.extend(['    <direction>', '      <lookat-x-m> %.3f </lookat-x-m>' % aim[0],
                      '      <lookat-y-m> %.3f </lookat-y-m>' % aim[1], '      <lookat-z-m> %.3f </lookat-z-m>' % aim[2],
                      '    </direction>'])
        x.extend(['    <color>', '      <r> %.2f </r>' % rgb[0], '      <g> %.2f </g>' % rgb[1], '      <b> %.2f </b>' % rgb[2],
                  '    </color>', '    <intensity>'] + level_xml(cd, '      ') + ['    </intensity>'])
        if aim:
            x.extend(['    <spot-exponent> %g </spot-exponent>' % e, '    <spot-cutoff> %g </spot-cutoff>' % cut])
        x.extend(['    <range-m> %g </range-m>' % rng, '  </light>', ''])
    x.extend(['  <animation>', '    <type>select</type>'] + ['    <object-name>%s</object-name>' % l[0] for l in lights] +
             ['    <condition>', '      <not><property>/scenery/finnhems/lights-off</property></not>', '    </condition>',
              '  </animation>', ''])
    x.extend(['  <animation>', '    <type>select</type>'] + ['    <object-name>lens-%s</object-name>' % k for k in LENS_NITS] +
             ['    <condition>', '      <and>', '        <not><property>/scenery/finnhems/lights-off</property></not>',
              '        <greater-than><property>/sim/time/sun-angle-rad</property><value> %.3f </value></greater-than>'
              % ((SUN_OFF + SUN_ON) / 2),
              '        <less-than><property>/scenery/finnhems/dim</property><value> 0.99 </value></less-than>', '      </and>',
              '    </condition>', '  </animation>', '', '</PropertyList>', ''])
    open(os.path.join(OUT, NAME + '.xml'), 'w').write('\n'.join(x))


def level_xml(cd, ind):
    """A light's intensity (cd) or a lens's luminance (cd/m2), in the pipeline's units: faded in as the sun sets,
    dimmed with /scenery/finnhems/dim and converted (UNITS)."""
    def table(rows):
        return ([ind + '    <table>', ind + '      <property>/sim/time/sun-angle-rad</property>'] +
                [ind + '      <entry><ind> %.4f </ind><dep> %.6g </dep></entry>' % r for r in rows] + [ind + '    </table>'])
    return ([ind + '<expression>', ind + '  <product>'] + table([(SUN_OFF, 0), (SUN_ON, 1)]) + table(UNITS) +
            [ind + '    <difference>', ind + '      <value> 1 </value>', ind + '      <property>/scenery/finnhems/dim</property>',
             ind + '    </difference>', ind + '    <value> %g </value>' % cd, ind + '  </product>', ind + '</expression>'])


def write_stg():
    lat, lon = latlon(CE, CN)
    open(os.path.join(OUT, '%d.stg' % TILE), 'w').write(
        '# The FinnHEMS base, written by tools/build.py\nOBJECT_STATIC %s.xml %.7f %.7f %.2f 0\n' % (NAME, lon, lat, ELEV))


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    build()
