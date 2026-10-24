"""watch47sim.py - run build/WATCH47.txt in the C47 simulator (c47sim.py, from Almanac 47) with a clock that
runs: a virtual time t (seconds) moves 0.17 ms a step (Almanac 47's measure), the PAUSE time while no key
comes, and the length of each BUZZ; Date→ⅅ / Time→ℸ read the start + t, TICKS is 10 t.
  run(events, start, until, wset, woff)  events: (t, key) in time order (KEY 7 4 9 0 as C47 codes below),
                                         or (t, ('sleep', s)): a standby of s seconds (no key);
                                         returns the snapshots (t, pixels, registers) at every key wait, c
  png(fn, pix)                           a PNG of one screen
  python3 python/watch47sim.py           writes docs/*.png and prints the step counts"""
import os, struct, sys, zlib
from datetime import datetime
from decimal import Decimal as D

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import c47sim

PROG = os.environ.get('WATCH47_PROG') or os.path.join(ROOT, 'build', 'WATCH47.txt')
W, H = 400, 240
LCD_BG, LCD_ON = (199, 205, 186), (34, 38, 30)
A, B, C, END = 52, 62, 54, 82          # the buttons 7 (LIGHT), 4 (MODE), 9; 0 the end
STEP = 0.00017


def jd(dt):
    """The JD of a datetime (the calculator's local time)."""
    y, m = dt.year, dt.month
    a = (14 - m) // 12; yy = y + 4800 - a; mm = m + 12 * a - 3
    n = dt.day + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - yy // 100 + yy // 400 - 32045
    return D(n) - D('0.5') + (D(dt.hour) * 3600 + dt.minute * 60 + dt.second) / D(86400)


class Snap:
    diss = False

    def __init__(self, t, pix, reg, steps):
        self.t, self.reg, self.steps = t, dict(reg), steps
        self.pix = {(x, H - 1 - y) for y, x in pix if 0 <= y < H and 0 <= x < W}


def run(events=(), start=datetime(2026, 10, 24, 13, 54, 30), until=None, wset=None, woff=None, prog=PROG,
        snaps=True):
    c = c47sim.load([prog])
    c.s = [D(0)] * 4; c.pix = []; c.keys = []; c.steps = 0; c.frames = []; c.keyskip = True
    if wset is not None:
        c.reg['WSET'] = D(str(wset))
    if woff is not None:
        c.reg['WOFF'] = D(str(woff))
    ev = list(events); st = {'t': 0.0}; out = []; j0 = jd(start)
    if until is None:
        until = (ev[-1][0] if ev else 0) + 0.5
    c.ticks = lambda: int(st['t'] * 10 + 1e-9)

    def on_buzz(ms):
        st['t'] += ms / 1000.0
    c.on_buzz = on_buzz

    def count(op, x):
        st['t'] += STEP
        if op in ('Date→ⅅ', 'Time→ℸ'):
            c.clock = j0 + D(repr(st['t'])) / D(86400); st['tclock'] = st['t']
        elif op == 'PAUSE':
            n = int(c.lines[c.at].split()[1])
            nxt = next((l for l in c.lines[c.at + 1:c.at + 4] if l.startswith('KEY?')), '')   # the wait's KEY?
            if n == 0 and snaps:                      # PAUSE 0: a pass of the light's dissolve, shown
                out.append(Snap(st['t'], c.pix, c.reg, c.steps)); out[-1].diss = True
            if nxt.startswith('KEY?'):
                if ev and ev[0][0] <= st['t'] + n / 10.0:
                    st['t'] = max(st['t'], ev[0][0])
                else:
                    st['t'] += n / 10.0
        elif op == 'KEY?':
            if snaps:
                out.append(Snap(st['t'], c.pix, c.reg, c.steps)); out[-1].tclock = st.get('tclock')
            if ev and ev[0][0] <= st['t'] + 1e-9 and isinstance(ev[0][1], tuple):
                st['t'] += ev.pop(0)[1][1]            # ('sleep', s): the calculator in standby s seconds, no key
                c.keys = []
            elif ev and ev[0][0] <= st['t'] + 1e-9:
                c.keys = [ev.pop(0)[1]]
            else:
                c.keys = []
                if not ev and st['t'] >= until:
                    raise StopIteration
    c.count = count
    try:
        c.run('WATCH47', maxsteps=10 ** 9)
        c.ended = True
    except StopIteration:
        c.ended = False
    c.t = st['t']
    return out, c


def png(fn, pix, scale=3, border=12):
    w, h = W * scale + 2 * border, H * scale + 2 * border
    buf = bytearray(bytes(LCD_BG) * (w * h))
    dot = bytes(LCD_ON) * scale
    for x, r in pix:
        for dy in range(scale):
            o = ((border + r * scale + dy) * w + border + x * scale) * 3
            buf[o:o + len(dot)] = dot
    raw = b''.join(b'\x00' + bytes(buf[y * w * 3:(y + 1) * w * 3]) for y in range(h))

    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    with open(fn, 'wb') as fh:
        fh.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                 + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def last_before(sn, t, diss=False):
    return [s for s in sn if s.t <= t and s.diss == diss][-1]


if __name__ == '__main__':
    os.makedirs(os.path.join(ROOT, 'docs'), exist_ok=True)
    # 7 light; 4 alarm; 7 its setting (the hour flashes), 4 back; 4 stopwatch, 9 start, 7 split; 4 setting, 4 time;
    # 9 9 quickly: C47
    sn, c = run([(2, A), (5, B), (7, A), (9, B), (9.5, B), (10, C), (13.0, A), (14.5, B), (15.5, B), (16.5, C), (16.8, C)],
                until=18, wset=2 + 4 + 10 * 730)
    shots = [('WATCH47_time.png', last_before(sn, 1.9), 'the time, 12 h, Sat 24 Oct 13:54'),
             ('WATCH47_dissolve.png', [s for s in sn if s.diss][1], 'the light: a pass of the dissolve'),
             ('WATCH47_light.png', last_before(sn, 3), 'lit'),
             ('WATCH47_alarm.png', last_before(sn, 6.9), 'alarm mode: AL 7:30 AM, ALM and SIG'),
             ('WATCH47_alarmset.png', [s for s in sn if 7.1 < s.t < 8.9 and int(s.reg.get('49', 0)) == 0][-1],
              'alarm setting: the hour flashing'),
             ('WATCH47_stopwatch.png', last_before(sn, 14.4), "stopwatch, split at 3 s"),
             ('WATCH47_c47.png', last_before(sn, 17.9), "the Easter egg: 9 twice")]
    for fn, s, what in shots:
        png(os.path.join(ROOT, 'docs', fn), s.pix)
        print('docs/%-24s %s' % (fn, what))
    print('start: %d steps' % sn[0].steps)
