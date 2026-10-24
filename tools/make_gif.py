#!/usr/bin/env python3
"""Write docs/WATCH47_tour.gif: WATCH47 in the C47 simulator with its clock running: the time; 7 the light (the
dissolve's passes shown); 4 the alarm; 4 the stopwatch, 9 start, 7 split; 4 4 back to the time; 9 9: C47.
A frame per key wait (about 0.3 s), each pass of the dissolve 0.1 s. Needs Pillow.
  python3 tools/build_watch47.py && python3 tools/make_gif.py"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'python'))
import watch47sim as S
from PIL import Image

SCALE, BORDER = 2, 8
EVENTS = [(2.5, S.A), (6, S.B), (8, S.B), (9, S.C), (12, S.A), (14, S.A), (15, S.B), (15.4, S.B), (17, S.C),
          (17.3, S.C)]


def image(pix):
    w, h = S.W * SCALE + 2 * BORDER, S.H * SCALE + 2 * BORDER
    im = Image.new('P', (w, h), 0)
    im.putpalette(list(S.LCD_BG) + list(S.LCD_ON) + [0] * 762)
    px = im.load()
    for x, r in pix:
        for dy in range(SCALE):
            for dx in range(SCALE):
                px[BORDER + x * SCALE + dx, BORDER + r * SCALE + dy] = 1
    return im


def main():
    sn, c = S.run(EVENTS, until=20, wset=2 + 4 + 10 * 730)
    sn = sn[1:]
    ims = [image(s.pix) for s in sn]
    dur = [100 if s.diss else max(100, int(1000 * (b.t - s.t))) for s, b in zip(sn, sn[1:] + sn[-1:])]
    fn = os.path.join(ROOT, 'docs', 'WATCH47_tour.gif')
    ims[0].save(fn, save_all=True, append_images=ims[1:], duration=dur, loop=0, optimize=True)
    print('%s: %d frames, %d bytes' % (os.path.relpath(fn, ROOT), len(ims), os.path.getsize(fn)))


if __name__ == '__main__':
    main()
