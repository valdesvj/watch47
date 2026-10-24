#!/usr/bin/env python3
"""tests/test_watch47.py - WATCH47 in the C47 simulator with a running clock (python/watch47sim.py).
  1. Every screen of the scenarios (each key wait) against a picture drawn separately from python/layout.py
     (layout.mock) from what the program shows: the whole screen, pixel for pixel (title, case, buttons, the key
     inverted, the light).
  2. The time and date against Python's datetime at each clock read, across midnight, New Year and a leap day,
     12 h (12 AM, 12 PM) and 24 h, with an offset (WOFF).
  3. The alarm (beeps from its minute, a button stops them), the chime (one beep on the hour), the setting
     (seconds, hour, minutes, month, day; WOFF and WSET kept), the stopwatch (against the clock), the C47 egg,
     the end (the stack, LASTx, R20-R99, the screen).
  python3 tools/build_watch47.py && python3 tests/test_watch47.py"""
import os, sys
from datetime import datetime, timedelta
from decimal import Decimal as D

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'python'))
import watch47sim as S
import layout as L

A, B, C, END = S.A, S.B, S.C, S.END
PAIRS = ['SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'AL', 'ST']
DAYS = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']        # datetime.weekday()
FAIL = []


def check(ok, what):
    if not ok:
        FAIL.append(what); print('FAIL', what)


def r(s, n):
    return int(s.reg.get(str(n), D(0)))      # a register never stored is 0


def ch(code):
    return ' ' if code == 10 else 'C' if code == 11 else str(code)


def state(s):
    """The state the program shows (R61-R71), for layout.mock."""
    sh = [r(s, 61 + i) for i in range(11)]
    pressed = [k for k, b in L.BUTTONS.items() if b[0] == r(s, 92) and b[2] == r(s, 93)]
    return dict(hh=ch(sh[0]) + ch(sh[1]), mm=ch(sh[2]) + ch(sh[3]), ss=ch(sh[4]) + ch(sh[5]),
                date=ch(sh[6]) + ch(sh[7]), colon=sh[8] == 1, day=PAIRS[sh[9]], ind=sh[10],
                light=r(s, 22) == 1, pressed=pressed)


def screens(sn, what):
    bad = 0
    for i, s in enumerate(sn):
        if s.diss:
            continue
        want = {(x, S.H - 1 - y) for x, y in L.mock(state(s))}
        if s.pix != want:
            bad += 1
            if bad <= 3:
                check(False, '%s: screen at t %.2f is not the layout picture (%d pixels differ)'
                      % (what, s.t, len(s.pix ^ want)))
    return bad


def expected(start, s, woff=0):
    """The watch's time at the snapshot's clock read (to the nearest second, as the program)."""
    return start + timedelta(days=woff) + timedelta(seconds=round(s.tclock))


def time_cells(t, h24):
    h = t.hour if h24 else (t.hour + 11) % 12 + 1
    ind = 4 if h24 else (1 if t.hour < 12 else 2)
    return ('%2d' % h, '%02d' % t.minute, '%02d' % t.second, '%2d' % t.day, DAYS[t.weekday()], ind)


def check_times(sn, start, h24, woff, what):
    bad = 0
    for s in sn:
        if s.diss or r(s, 20) != 0 or r(s, 38) > 0 or s.tclock is None:
            continue
        st = state(s); t = expected(start, s, woff)
        hh, mm, ss, dd, day, ind = time_cells(t, h24)
        got = (st['hh'], st['mm'], st['ss'], st['date'], st['day'], st['ind'] & 7)
        if got != (hh, mm, ss, dd, day, ind):
            bad += 1
            if bad <= 3:
                check(False, '%s t %.2f: shows %s, want %s (%s)' % (what, s.t, got, (hh, mm, ss, dd, day, ind), t))
    return bad


# ---------------------------------------------------------------- 1, 2: the time and the screens
for start, h24, woff, what in [
        (datetime(2026, 10, 24, 13, 54, 30), 0, 0, 'Sat afternoon, 12 h'),
        (datetime(2026, 12, 31, 23, 59, 55), 1, 0, 'New Year, 24 h'),
        (datetime(2026, 12, 31, 23, 59, 55), 0, 0, 'New Year, 12 h (12 AM)'),
        (datetime(2028, 2, 28, 11, 59, 57), 0, 0, 'leap day, 12 PM'),
        (datetime(2026, 10, 24, 13, 54, 30), 1, D('0.25'), 'offset 6 h, 24 h')]:
    sn, c = S.run([], start=start, until=8, wset=h24, woff=woff)
    check(check_times(sn, start, h24, float(woff), what) == 0, what + ': the time')
    check(screens(sn, what) == 0, what + ': the screens')

# a session: light, alarm mode and its setting, stopwatch and split, setting mode, C47
EV = [(2, A), (5, B), (7, A), (9, B), (9.5, B), (10, C), (13.0, A), (14.5, B), (15.5, B), (16.5, C), (16.8, C),
      (19, B), (19.5, A), (20, B), (20.5, B), (21, B)]
sn, c = S.run(EV, until=22, wset=2 + 4 + 10 * 730)
check(screens(sn, 'session') == 0, 'session: the screens')
lit = [s for s in sn if not s.diss and r(s, 22) == 1]
check(lit and min(s.t for s in lit) >= 2 and max(s.t for s in lit) <= 4.1, 'the light: on after 7, off 1.5 s later')
check(len([s for s in sn if s.diss]) == 8, 'the light: 4 passes on, 4 off (%d)' % len([s for s in sn if s.diss]))
egg = [s for s in sn if r(s, 38) > 0 and not s.diss]
check(egg and state(egg[-1])['hh'] + state(egg[-1])['mm'] == ' C47', 'C47 after 9 9')
check(r(sn[-1], 24) == 0, 'C47: the 12 / 24 h setting as it was')
sw = [s for s in sn if r(s, 20) == 2 and 13.3 < s.t < 14.4]
check(sw and all(state(s)['mm'] == '03' and state(s)['ss'] == '00' and state(s)['ind'] & 32 for s in sw),
      'stopwatch: split at 3.0 s shown with SPL')

# ---------------------------------------------------------------- 3. alarm, chime
start = datetime(2026, 10, 24, 13, 54, 50)
sn, c = S.run([(15, A)], start=start, until=17, wset=2 + 10 * 1355)
ring = [s for s in sn if r(s, 37) > 0]
check(ring and ring[0].t >= 10 and ring[0].t < 11, 'the alarm rings at 13:55:00 (t %.2f)' % (ring[0].t if ring else -1))
check(len(getattr(c, 'buzz', [])) >= 8 * 4, 'the alarm beeps (%d BUZZ)' % len(getattr(c, 'buzz', [])))
check(r(sn[-1], 37) == 0 and r(sn[-1], 20) == 0, 'a button stops it and does nothing else')
sn, c = S.run([], start=datetime(2026, 10, 24, 13, 59, 57), until=5, wset=4)
check(getattr(c, 'buzz', []) == [(2048, 100)], 'the chime: one beep at 14:00 (%s)' % getattr(c, 'buzz', []))
sn, c = S.run([], start=datetime(2026, 10, 24, 13, 59, 57), until=5, wset=0)
check(not getattr(c, 'buzz', []), 'no chime when it is off')

# alarm setting: 4 alarm, 9 (none -> ALM), 7 hour, 9 9 (+2 h), 7 minutes, 9 (+1), 4 end
sn, c = S.run([(2, B), (2.5, C), (3, A), (3.5, C), (4, C), (4.5, A), (5, C), (5.5, B)], until=6.5, wset=10 * 730)
check(c.reg.get('WSET') == D(2 + 10 * 931), 'alarm set to 9:31, ALM on: WSET %s' % c.reg.get('WSET'))

# ---------------------------------------------------------------- 3. time setting
start = datetime(2026, 10, 24, 13, 54, 40)
# 4 4 4: setting; 9 seconds (40 -> 00, next minute); 7 hour 9; 7 minutes 9; 7 month 9; 7 day 9 9; 4 4 time
sn, c = S.run([(2, B), (2.3, B), (2.6, B), (3, C), (3.5, A), (4, C), (4.5, A), (5, C), (5.5, A), (6, C), (6.5, A),
               (7, C), (7.5, C), (8, B)], start=start, until=9)
woff = float(c.reg.get('WOFF'))
t_now = start + timedelta(seconds=round(sn[-1].tclock))
w = start + timedelta(days=woff) + timedelta(seconds=round(sn[-1].tclock))
# what the watch must show: the clock at 3 s: seconds to 00 + 1 min, then + 1 h, + 1 min, November, day 24 + 2
t3 = start + timedelta(seconds=3)
want = t3.replace(second=0) + timedelta(minutes=1) + timedelta(hours=1) + timedelta(minutes=1)
want = want.replace(month=11, day=26) + (t_now - t3).__class__(seconds=round(sn[-1].tclock) - 3)
check(abs((w - want).total_seconds()) <= 1, 'setting: the watch %s, want about %s (WOFF %s)' % (w, want, woff))
check(screens(sn, 'setting') == 0, 'setting: the screens')

# ---------------------------------------------------------------- the end
import c47sim
sn, c = S.run([(2, END)], until=3)
check(c.ended, 'the end with 0')
c2 = c47sim.load([S.PROG])
sn, c = S.run([(1.5, END)], until=2)
check(all(c.reg.get(str(n), D(0)) == 0 for n in range(20, 100)), 'the end: R20-R99 cleared')
check(c.pix == [] and c.grmod == 0 and c.grfnt == 20, 'the end: screen cleared, GRMOD 0, GRFNT 20')

# ---------------------------------------------------------------- the stopwatch's 1/100 and its speed
sn, c = S.run([(2, B), (2.5, B), (3, C), (6, C), (8, C), (9, A)], until=11)
run = [s for s in sn if 3.5 < s.t < 5.9 and not s.diss]
check(len(set(r(s, 55) for s in run)) >= 4, 'running: the 1/100 digit changes (%s)' % [r(s, 55) for s in run])
check(len(run) / 2.4 > 3.5, 'running: about 4 updates a second (%.1f)' % (len(run) / 2.4))
st = [s for s in sn if 6.6 < s.t < 7.9]
check(st and all(r(s, 55) == 0 for s in st), 'stopped: the 1/100 digit 0')
sp = [s for s in sn if 9.5 < s.t < 10.9]
check(sp and all(r(s, 55) == 0 and r(s, 33) == 1 for s in sp), 'split: the 1/100 digit 0')

# ---------------------------------------------------------------- standby (LBL :WAKE:)
sn, c = S.run([(3, ('sleep', 600))], until=6)
check(c.ended, 'standby: after 10 min with no key the program ends')
check(c.pix == [] and c.grmod == 0 and all(c.reg.get(str(n), D(0)) == 0 for n in range(20, 100)),
      'standby: the screen cleared, R20-R99 cleared')
sn, c = S.run([(3, ('sleep', 5))], until=6)
check(not c.ended, 'a gap of 5 s: the watch runs on')

print('ALL OK' if not FAIL else '%d FAILED' % len(FAIL))
sys.exit(1 if FAIL else 0)
