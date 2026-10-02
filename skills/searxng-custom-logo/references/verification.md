# searxng-custom-logo - verification

Part of the `searxng-custom-logo` skill. Load `SKILL.md` first for the routing table.

## Verify, do not assume

- decode the encoded file back: count ANMF chunks, sum durations, and confirm the
  frames actually differ -- a still image saves happily under an animation's name.
- check the frame SOURCE varies per theme. Blank frames from one variant look
  identical to an encoder bug and will send you chasing the wrong thing.
- sample a **real page** over a full loop (10+ captures ~0.4s apart) to prove
  motion. Opening the file directly reports no motion for an image document.
  Always include a known-good control file in the same test page.
- if part of the mark must stay still, assert it: max change of that band across
  the loop in the SOURCE frames should be 0.00. A few units on the live page is
  resampling jitter on small type, not movement.
- after any resize, measure the boxes: the img, its container, and the neighbour's
  leading edge. Overflowing a container by 24px overlapped the search input by 17px.
