# AI Assistance Policy

## How this project uses AI

This project was **developed with the help of AI** — Claude (Anthropic) — as a cooperation. AI assisted with brainstorming, code generation, and documentation, but I reviewed all output, validated results against reference implementations, and take full responsibility for the work and any mistakes.

## Responsible use

- ✅ **I checked the results** — Every screen of the program in the C47 simulator (with a running clock) is compared pixel for pixel with a picture drawn separately from the layout, and every time and date with Python's `datetime`, across midnight, New Year and a leap day (`tests/test_watch47.py`)
- ✅ **I maintained domain expertise** — I guide the AI with design decisions based on the classic three-button digital watch I have worn, and how its modes and buttons work
- ✅ **I take full responsibility** — The work is mine; any errors are mine to fix
- ✅ **I'm transparent** — This file documents how AI was used

## Testing & Validation

- Simulator tests: the C47 program in `python/c47sim.py` (from Almanac 47), every screen and every text checked
- The reference picture (python/layout.py, mock()) written separately from the program's drawing
- To be tested on real C47 hardware before each release

## License

This does not affect the GNU GPL-3.0 license. All code remains open-source and fully accessible.

---

*For more details, see `NOTICE` and the development documentation.*
