"""layout.py - the screen of WATCH47: a three-button digital watch (alarm, chime, stopwatch).
An original face: the case, the LCD, the three buttons (C47 keys 7, 4, 9); 7-segment digits, the day letters
(the C47 standardFont doubled), the indicators. Used by tools/build_watch47.py (the program's drawing steps)
and by the tests and mock() (a picture of a state without running the program).
Screen 400 x 240, row 0 = the bottom (as ATEXT and AGRAPH on the C47)."""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stdfont import STD, code
from tinyfont import TINY


# ---- 7-segment digits: (height, width, thickness, left/right columns) ----
class Seg:
    def __init__(self, h, w, t):
        self.h, self.w, self.t = h, w, t
        m = h // 2
        r = lambda a, b: sum(1 << y for y in range(a, b + 1))
        self.seg = {'d': r(0, t - 1), 'g': r(m - t // 2, m - t // 2 + t - 1), 'a': r(h - t, h - 1),
                    'e': r(t + 1, m - t // 2 - 2), 'c': r(t + 1, m - t // 2 - 2),
                    'f': r(m - t // 2 + t + 1, h - t - 2), 'b': r(m - t // 2 + t + 1, h - t - 2)}

    def words(self, d):
        """The words of the left, middle and right columns of digit d (10: blank), bit 0 = the bottom row."""
        s = DIGITS[d]
        return (sum(self.seg[x] for x in 'ef' if x in s), sum(self.seg[x] for x in 'agd' if x in s),
                sum(self.seg[x] for x in 'bc' if x in s))

    def columns(self, d):
        l, m, r = self.words(d)
        return [l] * self.t + [m] * (self.w - 2 * self.t) + [r] * self.t


DIGITS = {0: 'abcdef', 1: 'bc', 2: 'abdeg', 3: 'abcdg', 4: 'bcfg', 5: 'acdfg', 6: 'acdefg', 7: 'abc',
          8: 'abcdefg', 9: 'abcdfg', 10: '', 11: 'adef'}       # 11: the C of the Easter egg C47
BIG, SMALL = Seg(56, 30, 6), Seg(30, 17, 4)      # the time; the seconds and the date

# ---- the case, the LCD, the buttons ----
CASE = (64, 335, 4, 215)            # x0, x1, row0, row1 (rounded corners of 8)
LCD = (92, 307, 36, 187)            # the frame; inside x 93-306, rows 37-186
BUTTONS = {7: (54, 63, 148, 172, 'L'), 4: (54, 63, 60, 84, 'L'), 9: (336, 345, 148, 172, 'R')}
BUTTON_TEXT = {7: ['LIGHT'], 4: ['MODE'], 9: ['ALARM', '24H', 'START']}
BUTTON_KEY = {7: '7', 4: '4', 9: '9'}     # the C47 key, inside the button (tinyFont)

# ---- the LCD's parts ----
HH = [(102, 1), (138, 0)]            # (x, cell) the hour's tens and units: BIG at row 66
MM = [(188, 3), (224, 2)]            # the minutes
MAIN_ROW = 44
COLON = (174, [(57, 62), (79, 84)])  # x (4 wide), the dots' rows
SS = [(264, 5), (284, 4)]            # the seconds: SMALL at row 66
SS_ROW = 44
DATE = [(262, 7), (282, 6)]          # the date (or the month, a field being set): SMALL at row 130
DATE_ROW = 130
DAY = (104, 130)                     # the day's two letters: x, row (the standardFont doubled)
IND_ROW = 140                        # the indicators: tinyFont, between the day and the date
# slot 0: AM, PM or 24H (one at a time, the same columns); then ALM, SIG (the hourly chime), SPL (split)
INDICATORS = [(1, 'AM', 0), (2, 'PM', 0), (4, '24H', 0), (8, 'ALM', 1), (16, 'SIG', 2), (32, 'SPL', 3)]
IND_X = [158, 180, 202, 224]         # the slots' x
TITLE = 'Tribute to the best watch ever'
TITLE_ROW = 218
BANDS = [37, 101, 165]               # the AGRAPH bands of the LCD's inside: 64 rows (the last 22)
INSIDE = (93, 306, 37, 186)


def text_px(text, x, row, font=21):
    """The pixels (x, row) of ATEXT text at x, row (the glyph box's bottom), as c47sim.atext draws them."""
    f = TINY if font == 10 else STD
    cp = 1 if font == 21 else 0
    px = set()
    for ch in text:
        cb, cg, ca, ra, rg, rb, rows = f.get(code(ch), f[0x3f])
        for r, v in enumerate(rows):
            for c in range(cg):
                if v >> (cg - 1 - c) & 1:
                    px.add((x + cb + c, row + rb + rg - 1 - r))
        x += cb + cg + ca - cp
    return px


def width(text, font=21):
    f = TINY if font == 10 else STD
    cp = 1 if font == 21 else 0
    return sum(f.get(code(ch), f[0x3f])[0] + f.get(code(ch), f[0x3f])[1] + f.get(code(ch), f[0x3f])[2] - cp
               for ch in text)


def letter_columns(ch):
    """A day letter: the standardFont glyph doubled (2 x 2 pixels a dot): its column words, bit 0 at the
    bottom of the glyph box."""
    cb, cg, ca, ra, rg, rb, rows = STD[code(ch)]
    cols = []
    for c in range(cg):
        w = 0
        for r, v in enumerate(rows):
            if v >> (cg - 1 - c) & 1:
                y = 2 * (rg - 1 - r)
                w |= 3 << y
        cols += [w, w]
    return cols


def outline_pixels():
    """The case (rounded), the LCD frame, the buttons."""
    px = set()

    def rect(x0, x1, y0, y1, rnd=0):
        for x in range(x0, x1 + 1):
            for y in (y0, y1):
                d = min(x - x0, x1 - x)
                if d >= rnd:
                    px.add((x, y))
        for y in range(y0, y1 + 1):
            for x in (x0, x1):
                d = min(y - y0, y1 - y)
                if d >= rnd:
                    px.add((x, y))
        for i in range(rnd):                    # the corners: a diagonal
            for cx, cy, sx, sy in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
                px.add((cx + sx * i, cy + sy * (rnd - i)))
    rect(*CASE, rnd=8)
    rect(CASE[0] + 4, CASE[1] - 4, CASE[2] + 4, CASE[3] - 4, rnd=6)
    rect(*LCD)
    for k, (x0, x1, y0, y1, side) in BUTTONS.items():
        rect(x0, x1, y0, y1)
    return px


def label_texts():
    """The buttons' texts: the C47 key inside each button, its functions beside it (tinyFont, 9 rows a line,
    centred on the button): (text, x, row, font)."""
    out = []
    for k, (x0, x1, y0, y1, side) in BUTTONS.items():
        kt = BUTTON_KEY[k]
        out.append((kt, (x0 + x1 + 1 - width(kt, 10)) // 2, (y0 + y1) // 2 - 4, 10))
        lines = BUTTON_TEXT[k]
        top = (y0 + y1) // 2 + 9 * len(lines) // 2 - 8
        for i, t in enumerate(lines):
            w = width(t, 10)
            x = x0 - 4 - w if side == 'L' else x1 + 4
            out.append((t, x, top - 9 * i, 10))
    return out


def mock(state):
    """A picture (set of (x, row)) of a state: hh mm ss (texts of 2 characters, ' ' blank), day (2 letters),
    date (2 characters), ind (the indicator bits), hint (a text), light (True: the LCD inverted)."""
    px = set(outline_pixels())
    for t, x, row, f in label_texts():
        px |= text_px(t, x, row, f)

    def seg(sg, x, row, ch):
        d = 10 if ch == ' ' else 11 if ch == 'C' else int(ch)
        for i, w in enumerate(sg.columns(d)):
            for y in range(64):
                if w >> y & 1:
                    px.add((x + i, row + y))
    for (x, c), ch in zip(HH, state['hh']):
        seg(BIG, x, MAIN_ROW, ch)
    for (x, c), ch in zip(MM, state['mm']):
        seg(BIG, x, MAIN_ROW, ch)
    for (x, c), ch in zip(SS, state['ss']):
        seg(SMALL, x, SS_ROW, ch)
    for (x, c), ch in zip(DATE, state['date']):
        seg(SMALL, x, DATE_ROW, ch)
    if state.get('colon', True):
        for y0, y1 in COLON[1]:
            for x in range(COLON[0], COLON[0] + 5):
                for y in range(y0, y1 + 1):
                    px.add((x, y))
    x = DAY[0]
    for ch in state['day']:
        for i, w in enumerate(letter_columns(ch)):
            for y in range(64):
                if w >> y & 1:
                    px.add((x + i, DAY[1] + y))
        x += len(letter_columns(ch)) + 6
    for bit, t, slot in INDICATORS:
        if state.get('ind', 0) & bit:
            px |= text_px(t, IND_X[slot], IND_ROW, 10)
    px |= text_px(TITLE, (400 - width(TITLE)) // 2, TITLE_ROW)
    if state.get('light'):
        x0, x1, y0, y1 = INSIDE
        px ^= {(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)}
    for k in state.get('pressed', ()):
        x0, x1, y0, y1, s = BUTTONS[k]
        px ^= {(x, y) for x in range(x0 + 1, x1) for y in range(y0 + 1, y1)}
    return px
