#!/usr/bin/env python3
"""Build the WATCH47 files from the commented source programs_rem/WATCH47.txt (as MH-10M 47's build).

One program, WATCH47. Named labels (LBL :TICK:) get free local numbers 00-99; the STRUCT commands are checked
and numbered. The drawing steps come from python/layout.py:
  REM ==== GLYPHS  LBL 00-11 the big digits, 12-22 the small (3 words: side, middle, side, bit 0 at the
                   digit's bottom), 23-31 the letters SU MO TU WE TH FR SA AL ST (column words, LBL :COL:),
                   32-37 the indicators AM PM 24H ALM SIG SPL
  REM ==== CELL    LBL :CELL:'s places: the big digits' x by arithmetic, the small ones' x, band, scale
  REM ==== BEEPS   the alarm's four beeps (BUZZ), REM ==== CHIME the chime's one
  REM ==== DISS    the light's dither: 4 passes x 3 bands, the column words R80-R83 (binary), the inside
  REM ==== STATIC  the title, the case, the LCD frame, the buttons and their names
and the {NAME}s in the source (the buttons' places, the 23 ones of a button's inside).
Files written: programs/WATCH47.txt, build/WATCH47.txt, listings/WATCH47_doc.txt, listings/WATCH47_labels.txt,
build/forum/WATCH47.p47u (tools/build_forum.py).
structures(), resolve(), estimate(), source_steps(), labels_text() come from MH-10M 47 (Zones 47, Elements 47).
  python3 tools/build_watch47.py"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'python'))
import layout as L

NAME = 'WATCH47'
NAMED_RE = re.compile(r'(LBL|GTO|XEQ) :([A-Za-z0-9]{1,7}):$')
OPENERS = {'IF': 'ENDIF', 'DO': 'ENDDO', 'REPEAT': 'UNTIL'}
STRUCT = ('IF', 'ELSE', 'ENDIF', 'DO', 'WHILE', 'ENDDO', 'REPEAT', 'UNTIL')
DM42_MAX = 10           # STRUCT_MAX_NUMBER and STRUCT_MAX_NESTING of the original DM42 (R47, DM42n: 255, 63)
NOT_USED = ('FOR', 'NEXT', 'FORₓ', 'NEXTₓ', 'FOR𝑦ˣ', 'FORᵀᴼᴾ')
BAND = 15               # dot rows per band (45 pixel rows, one AGRAPH word)


def is_test(step):
    """A step that leaves a test answer (the firmware's structTest list: the comparisons, the flag and type
    tests ending with ?, the counters, KEY?)."""
    op = step.split(' ')[0]
    return op.endswith('?') or op in ('DSE', 'ISG', 'DSZ', 'ISZ', 'DSL', 'ISE')


def structures(steps):
    """The steps with the partner numbers of the STRUCT commands, as VALID numbers them (manage.c /
    structured.c structWalkProgram): per program, IF, DO and REPEAT in three series from 1, in the order
    the openers appear; ELSE, WHILE, ENDDO, ENDIF, UNTIL take the number of their opener. Stops on what
    VALID refuses (a closer without its opener or of another kind, a structure left open at END or across
    a routine (RTN then LBL), a DO without WHILE, an IF / WHILE / UNTIL without a test just before it) and
    on a test before ELSE, ENDIF, DO, ENDDO, REPEAT or UNTIL: the firmware never skips those (structured.c
    structNoLegacySkip)."""
    out, open_, n = [], [], {}

    def fail(i, msg):
        raise SystemExit('STRUCT, step %d (%s): %s' % (i + 1, steps[i], msg))
    for i, s in enumerate(steps):
        op = s.split(' ')[0]
        prev = steps[i - 1] if i else ''
        if op in NOT_USED:
            fail(i, 'FOR / NEXT not used here (they take the start, end and step off the stack)')
        if op in STRUCT and s != op:
            fail(i, 'written without a number: the build numbers the structures')
        if op in ('IF', 'WHILE', 'UNTIL') and not is_test(prev):
            fail(i, 'no test just before it')
        if op in ('ELSE', 'ENDIF', 'DO', 'ENDDO', 'REPEAT', 'UNTIL') and is_test(prev) and not op == 'UNTIL':
            fail(i, 'a test before it: the firmware never skips a structure step')
        if s == 'END' or (s.startswith('LBL ') and prev == 'RTN'):
            if open_:
                fail(i, 'structure %s %02d still open' % tuple(open_[-1][:2]))
            if s == 'END':
                n = {}
        if op in OPENERS:
            n[op] = n.get(op, 0) + 1
            # the original DM42 (c43 structured.h, OLD_HW): 10 numbers of each kind per program, 10 levels
            if n[op] > DM42_MAX or len(open_) >= DM42_MAX:
                fail(i, 'past the original DM42 limit: %d %s a program, %d levels (structured.h, OLD_HW)'
                     % (DM42_MAX, op, DM42_MAX))
            open_.append([op, n[op], False])
            out.append('%s %02d' % (op, n[op]))
            continue
        if op in STRUCT:
            want = {'ELSE': 'IF', 'ENDIF': 'IF', 'WHILE': 'DO', 'ENDDO': 'DO', 'UNTIL': 'REPEAT'}[op]
            if not open_ or open_[-1][0] != want:
                fail(i, 'no %s open here' % want)
            top = open_[-1]
            if op in ('ELSE', 'WHILE'):
                if top[2]:
                    fail(i, 'a second %s' % op)
                top[2] = True
            if op == 'ENDDO' and not top[2]:
                fail(i, 'a DO without WHILE')
            if op in ('ENDIF', 'ENDDO', 'UNTIL'):
                open_.pop()
            out.append('%s %02d' % (op, top[1]))
            continue
        out.append(s)
    if open_:
        raise SystemExit('STRUCT: %s %02d still open at the end' % tuple(open_[-1][:2]))
    return out


def estimate(steps):
    """Estimated .p47 bytes of a program: 2.3 bytes per command, 2 + its characters per number and
    per binary number, 2 + its UTF-8 bytes per text. Calibrated on Almanac 47's MOON47 (4 836 bytes) and
    NAVFULL (24 160 bytes), within 3 % of both; rejig gives the real size."""
    b = 0.0
    for s in steps:
        if s.startswith('"'):
            b += 2 + len(s.encode('utf-8')) - 2
        elif re.fullmatch(r'-?[\d.]+(E-?\d+)?|[01]+#2', s):
            b += 2 + len(s)
        elif NAMED_RE.match(s):
            b += 3 + len(s.split(':')[1])      # command, 249, length, the name (bytes of the test program)
        else:
            b += 2.3
    return int(round(b))


def resolve(steps):
    """The steps with each named label replaced by a free local number (the fallback file), and the
    numbers: the numbers 00-99 not taken by a numeric label of the first program (the other programs
    have their own local labels), in order. Stops on a name defined twice, a name used but not defined,
    more labels than 00-99."""
    defs = [m.group(2) for s in steps for m in [NAMED_RE.match(s)] if m and m.group(1) == 'LBL']
    dup = sorted({d for d in defs if defs.count(d) > 1})
    if dup:
        raise SystemExit('named labels defined twice: %s' % ', '.join(dup))
    used = {m.group(2) for s in steps for m in [NAMED_RE.match(s)] if m}
    if used - set(defs):
        raise SystemExit('named labels used but not defined: %s' % ', '.join(sorted(used - set(defs))))
    bad = [s for s in steps if re.match(r'(LBL|GTO|XEQ) :', s) and not NAMED_RE.match(s)]
    if bad:
        raise SystemExit('a named label is 1-7 letters or digits between colons: %s' % bad[:3])
    first = steps[:steps.index('END') + 1] if 'END' in steps else steps
    taken = {int(m.group(1)) for s in first for m in [re.fullmatch(r'LBL (\d\d)', s)] if m}
    free = [n for n in range(100) if n not in taken]
    if len(defs) > len(free):
        raise SystemExit('%d named labels, only %d local numbers free' % (len(defs), len(free)))
    num = dict(zip(defs, free))
    return [NAMED_RE.sub(lambda m: '%s %02d' % (m.group(1), num[m.group(2)]), s) for s in steps], num


def programs(steps):
    """The programs of a list of steps (each ends with END)."""
    out, cur = [], []
    for s in steps:
        cur.append(s)
        if s == 'END':
            out.append(cur); cur = []
    return out


def source_steps(lines):
    """The steps of the source lines: no REM, no empty lines, the indentation off."""
    return [ln.strip() for ln in lines if ln.strip() and not ln.lstrip().startswith('REM')]


PAIRS = ['SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'AL', 'ST']
BEEP = (2048, 60)        # Hz, ms
CHIME = (2048, 100)


def band_of(row):
    return max(b for b in L.BANDS if b <= row)


def pair_columns(p):
    a, b = L.letter_columns(p[0]), L.letter_columns(p[1])
    return a + [0] * 6 + b


def ind_columns(text, w):
    """The column words of an indicator (tinyFont), bit 0 at IND_ROW, padded with blank columns to w."""
    px = L.text_px(text, 0, L.IND_ROW, 10)
    cols = [sum(1 << (y - L.IND_ROW) for (x, y) in px if x == c) for c in range(L.width(text, 10))]
    return cols + [0] * (w - len(cols))


def slot_width(slot):
    return max(L.width(t, 10) for b, t, s in L.INDICATORS if s == slot)


CELLS = None


def cells():
    """The 11 cells: (kind, x, row) - digit cells with their size."""
    out = [('big', x, L.MAIN_ROW) for x, c in L.HH] + [('big', x, L.MAIN_ROW) for x, c in L.MM]
    out += [('small', x, L.SS_ROW) for x, c in L.SS] + [('small', x, L.DATE_ROW) for x, c in L.DATE]
    out += [('colon', L.COLON[0], L.MAIN_ROW), ('day', L.DAY[0], L.DAY[1]), ('ind', None, L.IND_ROW)]
    return out


def glyph_steps():
    out = []
    for d in range(12):
        out.append('LBL %02d' % d)
        for w, r in zip(L.BIG.words(d), (80, 81, 82)):
            out += [str(w), 'STO %d' % r]
        out.append('RTN')
    for d in range(11):
        out.append('LBL %02d' % (12 + d))
        for w, r in zip(L.SMALL.words(d), (80, 81, 82)):
            out += [str(w), 'STO %d' % r]
        out.append('RTN')
    width = max(len(pair_columns(p)) for p in PAIRS)
    for i, p in enumerate(PAIRS):
        cols = pair_columns(p); cols += [0] * (width - len(cols))
        out += ['LBL %02d' % (23 + i), str(L.DAY[0]), 'STO 85']
        for w in cols:
            out += [str(w), 'XEQ :COL:']
        out.append('RTN')
    for i, (bit, t, slot) in enumerate(L.INDICATORS):
        out += ['LBL %02d' % (32 + i), str(L.IND_X[slot]), 'STO 85']
        for w in ind_columns(t, slot_width(slot)):
            out += [str(w), 'XEQ :COL:']
        out.append('RTN')
    return out


def cell_steps():
    """LBL :CELL:'s rest: cell R97 (code R74): 8 the colon, 9 the letters, 10 the indicators (their drawers set
    their places); 4-7 small (LBL :CSML:): x = x4 + p ((i - 4) mod 2) + dx IP((i - 4) / 2), the band 37 or 101,
    the scale; 0-3 big: x = x0 + p (i mod 2) + q IP(i / 2)."""
    cs = cells()
    big = [c[1] for c in cs[:4]]; sm = [c[1] for c in cs[4:8]]
    p = big[1] - big[0]; q = big[2] - big[0]
    assert big[3] == big[0] + p + q, big
    ps = sm[1] - sm[0]; dx = sm[2] - sm[0]
    assert sm[3] == sm[0] + ps + dx, sm
    b0, b1 = band_of(cs[4][2]), band_of(cs[6][2])
    s0, s1 = 1 << (cs[4][2] - b0), 1 << (cs[6][2] - b1)
    assert band_of(cs[0][2]) == b0 and cs[0][2] == cs[4][2]
    out = ['RCL 97', '8', 'X=Y?', 'GTO :DCLN:', 'RCL 97', '9', 'X=Y?', 'GTO :DDAY:', 'RCL 97', '10', 'X=Y?',
           'GTO :DIND:', 'RCL 97', '4', 'X≤Y?', 'GTO :CSML:',
           # big: x, band, scale, sizes, glyphs 00-11
           'RCL 97', '2', 'MOD', str(p), '×', 'RCL 97', '2', '÷', 'IP', str(q), '×', '+', str(big[0]), '+', 'STO 85',
           str(b0), 'STO 86', str(s0), 'STO 83', str(L.BIG.t), 'STO 89', str(L.BIG.w - 2 * L.BIG.t), 'STO 90',
           '0', 'STO 88', 'GTO :DDIG:',
           'LBL :CSML:',
           'RCL 97', '4', '-', 'STO 79', '2', 'MOD', str(ps), '×', 'RCL 79', '2', '÷', 'IP', 'STO 79', str(dx), '×', '+',
           str(sm[0]), '+', 'STO 85',
           'RCL 79', str(b1 - b0), '×', str(b0), '+', 'STO 86',
           'RCL 79', str(s1 - s0), '×', str(s0), '+', 'STO 83',
           str(L.SMALL.t), 'STO 89', str(L.SMALL.w - 2 * L.SMALL.t), 'STO 90', '12', 'STO 88', 'GTO :DDIG:']
    return out


def beep_steps():
    out = []
    for i in range(4):
        out += [str(BEEP[0]), str(BEEP[1]), 'BUZZ', '0', str(BEEP[1]), 'BUZZ']
    return out


def chime_steps():
    return [str(CHIME[0]), str(CHIME[1]), 'BUZZ']


BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def dither_phase(x, y):
    return BAYER[y % 4][x % 4] // 4


def diss_steps():
    x0, x1, y0, y1 = L.INSIDE
    n = x1 - x0 + 1
    out = []
    for p in range(4):
        for b in L.BANDS:
            top = min(b + 63, y1)
            for i in range(4):
                w = sum(1 << (y - b) for y in range(b, top + 1) if dither_phase(x0 + i, y) == p)
                out += ['%s#2' % format(w, 'b'), 'STO %d' % (80 + i)]
            out += [str(b), str(x0)] + ['XEQ :Q16:'] * (n // 16) + ['XEQ :Q4:'] * (n % 16 // 4)
            out += ['AGRAPH %d' % (80 + i) for i in range(n % 4)]
        out += ['PAUSE 0']
    return out


BANDS_STATIC = (1, 63, 125, 187)        # 62 rows each (words under 2^62)


def band_runs(px):
    out = []
    for b in BANDS_STATIC:
        cols = [sum(1 << (y - b) for y in range(b, b + 62) if (x, y) in px) for x in range(400)]
        runs, x = [], 0
        while x < 400:
            n = 1
            while x + n < 400 and cols[x + n] == cols[x]:
                n += 1
            if cols[x]:
                runs.append((x, n, cols[x]))
            x += n
        out.append((b, runs))
    return out


def static_steps():
    out = ['21', 'GRFNT', '"%s"' % L.TITLE, str(L.TITLE_ROW), str((400 - L.width(L.TITLE)) // 2), 'ATEXT Z',
           '10', 'GRFNT']
    for t, x, row, f in L.label_texts():
        out += ['"%s"' % t, str(row), str(x), 'ATEXT Z']
    out += ['0', 'GRMOD']
    for b, runs in band_runs(L.outline_pixels()):
        out += [str(b), '0']
        cur = 0
        for x, n, w in runs:
            if x != cur:
                out += ['DROP', str(x)]
            out += [str(w), 'SINT', 'STO 84', 'DROP', str(n), 'STO 73', 'DROP', 'XEQ :RUN:']
            cur = x + n
    return out


MARKERS = {'GLYPHS': glyph_steps, 'CELL': cell_steps, 'BEEPS': beep_steps, 'CHIME': chime_steps, 'DISS': diss_steps,
           'STATIC': static_steps}


def tokens():
    cs = cells()
    t = {'ONES23': str((1 << 23) - 1), 'BAND1': str(L.BANDS[0]), 'BAND2': str(L.BANDS[1]),
         'CLNX': str(L.COLON[0]),
         'CLNW': str(sum(1 << (y - L.BANDS[0]) for y0, y1 in L.COLON[1] for y in range(y0, y1 + 1))),
         'DAYSC': str(1 << (L.DAY[1] - L.BANDS[1])), 'INDSC': str(1 << (L.IND_ROW - L.BANDS[1]))}
    assert band_of(L.MAIN_ROW) == L.BANDS[0] and band_of(L.DAY[1]) == band_of(L.IND_ROW) == L.BANDS[1]
    for k, (x0, x1, y0, y1, s) in L.BUTTONS.items():
        t['B%dX' % k] = str(x0); t['B%dY' % k] = str(y0)
    return t


def expand(lines):
    out, tk = [], tokens()
    for ln in lines:
        m = re.fullmatch(r'(\s*)\{(\w+)\}', ln)
        if m:
            ln = m.group(1) + tk[m.group(2)]
        out.append(ln)
        m = re.match(r'\s*REM ==== (\w+)', ln)
        if m and m.group(1) in MARKERS:
            ind = ln[:len(ln) - len(ln.lstrip())]
            out += [ind + s for s in MARKERS[m.group(1)]()]
    return out


def labels_text(lines, num):
    out = [NAME + ' local labels: name (programs_rem/%s.txt), number (build/%s.txt), what it does' % (NAME, NAME), '']
    for i, ln in enumerate(lines):
        m = NAMED_RE.match(ln)
        if m and m.group(1) == 'LBL':
            j = i
            while j > 0 and lines[j - 1].startswith('REM'):
                j -= 1
            note = lines[j][3:].strip(' -') if j < i else ''
            note = re.sub(r'^(LBL )?:%s:\s*' % m.group(2), '', note)
            out.append(':%s:%s %02d  %s' % (m.group(2), ' ' * (8 - len(m.group(2))), num[m.group(2)], note[:90]))
    return '\n'.join(out) + '\n'


def build():
    src = os.path.join(ROOT, 'programs_rem', NAME + '.txt')
    lines = expand([ln.rstrip() for ln in open(src, encoding='utf-8')])
    steps = source_steps(lines)
    numeric, num = resolve(steps)
    numeric = structures(numeric)
    # R-CLR takes sss.nn with a count: a whole number (a count of 0) gives "Invalid input data" on the C47
    # (Victor's calculator, Oct 24 2026), though c47sim takes it as "to R99"
    bad = [numeric[i - 1] for i, s in enumerate(numeric) if s == 'R-CLR' and re.fullmatch(r'\d+', numeric[i - 1])]
    if bad:
        raise SystemExit('R-CLR with no count (X = %s): write sss.nn' % bad[0])
    if [s for s in steps if s.startswith('LBL "')] != ['LBL "%s"' % NAME] or steps.count('END') != 1:
        raise SystemExit('one program, %s' % NAME)
    listing, n = [], 0
    for ln in lines:
        if not ln.strip():
            continue
        ind = ln[:len(ln) - len(ln.lstrip())]
        if ln.lstrip().startswith('REM'):
            listing.append('      ' + ind + '; ' + ln.lstrip()[3:].strip())
        else:
            extra = '' if numeric[n] == steps[n] else '    (%s)' % numeric[n].split(' ', 1)[1]
            listing.append('%4d  %s' % (n + 1, ind + steps[n] + extra))
            n += 1
    plain = '\n'.join(numeric) + '\n'
    for d in ('programs', 'build', 'listings'):
        os.makedirs(os.path.join(ROOT, d), exist_ok=True)
    for d in ('programs', 'build'):
        with open(os.path.join(ROOT, d, NAME + '.txt'), 'w', encoding='utf-8') as fh:
            fh.write(plain)
    with open(os.path.join(ROOT, 'listings', NAME + '_doc.txt'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(listing) + '\n')
    with open(os.path.join(ROOT, 'listings', NAME + '_labels.txt'), 'w', encoding='utf-8') as fh:
        fh.write(labels_text(lines, num))
    return numeric


if __name__ == '__main__':
    st = build()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import build_forum
    build_forum.build(NAME)                                   # build/forum/WATCH47.p47u, the commented rejig source
    txt = [s for s in st if s.startswith('"')]
    print('%s %5d steps, %2d local labels, longest text %d, about %d bytes (.p47, estimated)' % (
        NAME, len(st), sum(1 for s in st if re.match(r'LBL \d\d', s)), max(len(s) - 2 for s in txt), estimate(st)))
