#!/usr/bin/env python3
"""build_forum.py - the commented rejig source (.p47u) of WATCH47, for the forum and the PROGRAMS folder of a C47
release (as Logic 47's, Almanac 47's and Zones 47's tools/build_forum.py: '@' header lines, then the steps).

  build/forum/WATCH47.p47u  from build/WATCH47.txt (the steps) and listings/WATCH47_doc.txt (the comments)

The steps are those of build/*.txt, one by one (the same .p47 as the plain listing): indented as the source
(STRUCT, two spaces a level), the partner numbers written (DO 01 ... ENDDO 01). After the '@' metadata, the
narrative of tools/forum/NAME.txt (what the program does and how to use it, in plain words), then the source's
header as technical notes. The source's comment blocks (its REM lines) are '@' lines before the steps they stand
before; the name of a label (LBL :INIT:) is given after ';' on its LBL and on each XEQ / GTO to it. rejig compiles
neither '@' lines nor what follows ';', so the comments take no memory. A line that starts with ';' or '#' would
become a REM step on the calculator (Almanac 47 DEVELOPMENT_NOTES): there are none.

  python3 tools/build_watch47.py   (writes it too)
  rejig: the .p47 of build/forum/WATCH47.p47u must be the size of the one of build/WATCH47.txt.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'build', 'forum')
AUTHOR = 'Victor Valdes'
SOURCE = 'https://github.com/valdesvj/watch47'
COL = 32                              # the column of the ';' comments (wider steps: two spaces after them)

HEAD = {
    'WATCH47': """@ Index:   Watch 47: a tribute to the classic three-button digital watch (alarm, chime, stopwatch, light)
@ Author:  %(author)s
@ Version: %(version)s
@ Source:  %(source)s
@ Tested:  C47 simulator (python/c47sim.py, with a clock that runs): tests/test_watch47.py, every screen of the
@ Tested:  scenarios against a picture drawn separately from the layout (python/layout.py), the times against
@ Tested:  Python's datetime; not yet on a C47 (GRMOD 4 and BUZZ in a program, the KEY? codes 7 4 9 known)
@ Input:   the buttons: 7 LIGHT, 4 MODE, 9 ALARM ON-OFF / 24H / START-STOP; 0 the end
@ Output:  the calculator's time and date with seconds, 12 h (AM / PM) or 24 h, the day of the week;
@ Output:  9 twice quickly shows C47
@
""",
}

STEP = re.compile(r'^\s*(\d+)  (.*)$')
NAMED = re.compile(r'^(\s*)(.*?)\s{4}\((\d+)\)$')            # "XEQ :INIT:    (83)", "DO    (01)"


def narrative(name):
    """tools/forum/NAME.txt: what the program does and how to use it, in plain words, as '@' lines."""
    fn = os.path.join(ROOT, 'tools', 'forum', name + '.txt')
    lines = open(fn, encoding='utf-8').read().rstrip('\n').split('\n')
    return ['@ ' + ln if ln.strip() else '@' for ln in lines] + ['@']


def parse(name):
    """The doc listing: the header comments, then [(indent, step text with names, number, comments before it)]."""
    head, steps, pending = [], [], []
    for ln in open(os.path.join(ROOT, 'listings', name + '_doc.txt'), encoding='utf-8'):
        ln = ln.rstrip('\n')
        m = STEP.match(ln)
        if m:
            body = m.group(2)
            ind = body[:len(body) - len(body.lstrip())]
            steps.append((ind, body.strip(), int(m.group(1)), pending)); pending = []
        elif ln.strip().startswith(';'):
            text = ln.strip()[1:].strip()
            (pending if steps else head).append(text)          # before step 1: the program's header
    return head, steps


PAIRS = ['SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'AL', 'ST']
INDS = ['AM', 'PM', '24H', 'ALM', 'SIG', 'SPL']
CELLS = ['the hour tens', 'the hour units', 'the minutes tens', 'the minutes units', 'the small tens',
         'the small units', 'the date tens', 'the date units', 'the colon', 'the letters', 'the indicators']


def data_notes(name, plain, names):
    """Notes on the numeric labels: {step index: note}."""
    notes = {}
    for k, st in enumerate(plain):
        m = re.fullmatch(r'LBL (\d\d)', st)
        if m and m.group(1) not in names:
            lab = int(m.group(1))
            if lab <= 11:
                notes[k] = 'big digit %s: the words of its side, middle, side columns' % ('C (C47)' if lab == 11 else lab)
            elif lab <= 22:
                notes[k] = 'small digit %s: its words' % ('blank' if lab == 22 else lab - 12)
            elif lab <= 31:
                notes[k] = 'the letters %s: x, then each column (LBL :COL:)' % PAIRS[lab - 23]
            elif lab <= 37:
                notes[k] = 'the indicator %s: x, then each column' % INDS[lab - 32]
    return notes


def build(name):
    head, steps = parse(name)
    plain = open(os.path.join(ROOT, 'build', name + '.txt'), encoding='utf-8').read().split('\n')
    plain = [s for s in plain if s.strip()]
    if len(plain) != len(steps):
        raise SystemExit('%s: %d steps in build/, %d in listings/' % (name, len(plain), len(steps)))
    m = re.search(r'v(\d+\.\d+\.\d+)', head[0])
    version = m.group(1) if m else '?'
    names = {}                                                    # label number -> :NAME:
    for ind, text, n, com in steps:
        mm = NAMED.match(ind + text)
        if mm and mm.group(2).startswith('LBL :'):
            names[mm.group(3)] = mm.group(2)[4:]
    out = [(HEAD[name] % dict(author=AUTHOR, version=version, source=SOURCE)).rstrip('\n')]
    data = data_notes(name, plain, names)
    out += narrative(name)
    out += ['@ ---- Technical notes (from the commented source) ----']
    out += ['@ ' + h if h else '@' for h in head] + ['@', '']
    for k, ((ind, text, n, com), step) in enumerate(zip(steps, plain)):
        if ';' in step or step.lstrip().startswith(('#', '@')):
            raise SystemExit('%s step %d: %r would not survive rejig' % (name, n, step))
        if com:                                                  # the source's comment block: '@' lines (not compiled)
            if com[0].startswith('----') and out[-1] != '':
                out.append('@')
            out += ['@ ' + ind + c if c else '@' for c in com]
        note = ''
        mm = re.fullmatch(r'(LBL|XEQ|GTO) (\d\d)', step)
        if mm and mm.group(2) in names:
            note = names[mm.group(2)] if mm.group(1) == 'LBL' else '-> ' + names[mm.group(2)]
        if k in data:
            note = (note + '  ' if note else '') + data[k]
        line = ind + step
        if note:
            line = line.ljust(COL) + '; ' + note if len(line) < COL else line + '  ; ' + note
        out.append(line)
    os.makedirs(OUT, exist_ok=True)
    fn = os.path.join(OUT, name + '.p47u')
    with open(fn, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(out).rstrip('\n') + '\n')
    ncom = sum(1 for ln in out if ln.startswith('@ ') or re.search(r'\s; ', ln))
    print('build/forum/%s.p47u  %d steps, %d with a comment, version %s' % (name, len(plain), ncom, version))
    return out


if __name__ == '__main__':
    for nm in sys.argv[1:] or ('WATCH47',):
        build(nm)
