# Watch 47: development notes

## Oct 24, 2026 - v0.1.0, the first version

- Idea (Victor): a simulator of the classic three-button digital watch he loves, the buttons on the keys 7, 4
  and 9; then: the light with a pixel effect, "Tribute to the best watch ever" on the screen, the alarm and the
  hourly sound, the calculator's time, date and seconds, AM / PM and 24 h; the Easter egg showing C47.
- The face is an original drawing (python/layout.py): a case with two outlines and cut corners, the LCD, three
  buttons with their C47 key inside and their names beside; no maker's design or name.
- Modes as the watch: time, alarm, stopwatch, time setting (4). The Easter egg: the watch shows a word while
  the right button is held; KEY? cannot tell a held key, so here 9 twice within 1 s (12 / 24 h twice: back as
  it was) shows C47 2 s.
- The time: Date→ⅅ Time→ℸ ⅅℸ→J + WOFF (days), in seconds IP((JD + 0.5) 86400 + 0.5); a new day: the date
  (Fliegel - Van Flandern, as Zones 47) and the weekday (N + 1) mod 7; a new minute: the alarm, the chime.
  Setting: seconds / hour / minutes as seconds on WOFF; month / day as the day number of the new date (LBL :JDN:;
  the month's length from the 1st of the next month) minus today's.
- Drawing: the LCD's inside in AGRAPH bands of 64 rows from rows 37 and 101 (the third, 165-186, has no
  cell); each cell writes whole columns (GRMOD 1), lit the inverse (GRMOD 4); cells are drawn only when their
  code changes (targets R50-R60, shown R61-R71). Words of a glyph from its bottom, x 2^(rows above the band).
- The light: four XOR passes of a 4 x 4 Bayer dither (each pass 4 pixels of every 4 x 4), PAUSE 0 after each:
  after four the screen is the lit drawing exactly, so nothing is redrawn and the cache stays right. The same
  four passes put it back after 1.5 s.
- Labels: the 100 local labels were short (110 at first): the cells' places by arithmetic in LBL :CELL: (the
  build writes it and checks the layout fits the formula), and branches made arithmetic: the 12 / 24 h hour and
  its indicator, the stopwatch's 7, the mode key (mode(2 - mode)(3 - mode)/2 is 1 for the alarm mode only),
  the alarm / chime cycle k = (1 - a)(3 - c) + ac. 94 used.
- WSET: the last digit 24h + 2 alarm + 4 chime, then the alarm's hhmm (a first decoding read the bits from the
  whole number: the alarm's time leaked into them; found by the alarm test).
- R-CLR 20 (a count of 0: to R99): R-CLR 20.80 is out of range (20 + 80 reaches 100). Done at the start too:
  the registers may hold the user's numbers.
- c47sim: BUZZ (recorded, its length on the clock) and a TICKS hook added, marked watch47. python/watch47sim.py
  runs the clock: 0.17 ms a step, the PAUSE time when no key comes, the BUZZ lengths.
- Tests (tests/test_watch47.py): every screen of five clock runs and a session against layout.mock() pixel for
  pixel; the time against datetime (12 AM, 12 PM, New Year, 29 Feb 2028, an offset); the alarm, the chime,
  the alarm setting (WSET), the time setting (WOFF), the stopwatch split, C47, the end.
- Steps: the start 6 950; a tick 414; a dissolve pass 796 (the light on in about 0.55 s); 3 460 steps, 13.5 KB.

## Oct 24, 2026 - the standby check (as MH-10M 47, Zones 47, Logic 47, Elements 47)

- Victor: a program waiting for a key went to standby and needed several presses to come back. LBL :WAKE: after
  KEY? with no key: the clock's JD against the last pass's (R91); more than 30 s: the program ends as with 0
  (R34 = 82); the loop runs on R94 (freed: the button's 23 ones written where they are used). 95 labels.
- watch47sim: an event (t, ('sleep', s)) moves the clock s seconds at a key wait with no key. Tests: 10 min ends
  the program cleanly, 5 s does not.

## Oct 24, 2026 - "Invalid input data" at the start: R-CLR 20

- Victor's C47 stopped at the start with "Invalid input data". A debug copy (WDBG, a number stored after each
  stage of the start) showed it: R-CLR with X = 20 (no count; c47sim and Almanac 47's notes read it as "to R99")
  is refused by the calculator. Now 20.79 R-CLR (R20-R98) and 0 STO 99, at the start and the end; the build
  stops on an R-CLR with no count. To tell Almanac 47 (c47sim's R-CLR: a count of 0 is an error there).

## Oct 24, 2026 - the stopwatch's 1/100 (Victor: the hundredths were not right)

- TICKS is 100 ms (the C47 reference; its STOPW app shows tenths): no hundredths for a program. Victor chose: while
  it runs a spinning digit, (7 E + 3) mod 10 (E the tenths), x running x (1 - split); stopped or split: 0.
- The loop pauses PAUSE 1 while the stopwatch runs in its mode (running x mode(mode - 1)(3 - mode)/2, then
  X≠0? PAUSE 1, X=0? PAUSE 2): about 4 updates a second (was 3; the redraw of the spinning digit costs some).
  Almanac 47 warns that keys can fall outside a short PAUSE: to check on the C47 (9 and 7 while it runs).
- watch47sim: the PAUSE before the wait's KEY? looked for within 3 lines. Tests: the digit changes while running,
  0 stopped and split, more than 3.5 updates a second.

## To do

1. Run on Victor's C47 (convert build/WATCH47.txt with rejig): GRMOD 4 and BUZZ in a program are new here.
2. BUZZ and the TICKS hook into Almanac 47's c47sim.
3. Ideas: a tick only when the second changes (fewer steps, longer battery); the alarm's snooze? (the watch
   has none).
