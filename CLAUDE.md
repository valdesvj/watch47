# Watch 47: working rules

- Work on a new branch; Victor creates and merges the PRs. Never force-push or rewrite history.
- Commit author: "Victor Valdes" <valdesvj@users.noreply.github.com>.
- Never commit binaries (.p47 files made by rejig).
- Edit the program in programs_rem/WATCH47.txt (commented source), then run python3 tools/build_watch47.py:
  it writes programs/, build/ and listings/. Never edit those three by hand.
- The build fills the marker lines REM ==== GLYPHS, CELL, BEEPS, CHIME, DISS and STATIC and the {NAME}s from
  python/layout.py (the digits, letters, indicators, the case, the buttons): change the screen there; the
  tests compare every screen with layout.mock().
- STRUCT as Elements 47: IF / ELSE / ENDIF, DO / WHILE / ENDDO, indented, no numbers in the source; a test
  right before IF / WHILE; never a test before ELSE, ENDIF, DO, ENDDO. At most 10 IF and 10 DO (the original
  DM42; WATCH47 has 4 DO). Named labels LBL :NAME:. Numeric labels: 00-11 the big digits, 12-22 the small,
  23-31 the letter pairs, 32-37 the indicators. 94 of the 100 local labels are used: prefer arithmetic to a
  new label (`X≠0? 1` gives 1 or the 0 in X).
- Text on the C47 screen: ATEXT in GRFNT 21 (GRFNT 10 for the title). Restore GRFNT 20 and GRMOD 0 before
  the program ends. GRMOD and GRFNT take X: write `3 GRMOD`. AGRAPH words through SINT
  (the dither's as binary literals, as Zones 47's 64 ones).
- The watch's loop: DO / XEQ :TICK: / PAUSE 2 / KEY? 34 / WHILE / ENDDO. Buttons 7 4 9 (KEY? 52 62 54), 0 ends.
- The simulator's clock runs (python/watch47sim.py): 0.17 ms a step, the PAUSE time, the BUZZ lengths.
- Only commands already run on a C47 in Almanac 47, Elements 47 or Zones 47; new here (README): GRMOD 4 with
  AGRAPH and BUZZ in a program. A new command: say so and ask Victor to try it.
- Check every change in the simulator (python3 python/watch47sim.py writes docs/*.png) and with
  python3 tests/test_watch47.py (layout.mock() is the reference picture: a screen change goes in both).
- python/c47sim.py, stdfont.py, tinyfont.py come from Almanac 47 (via MH-10M 47): a fix is made there first,
  then copied here; BUZZ and the TICKS hook (marked watch47) are to be taken there too.
- Work in one repository at a time (this one); the other 47 repositories are for reference only.
- Ask before anything that can't be undone. Pull requests only for watch47.
