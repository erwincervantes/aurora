# Aurora production files: El Salvador Tax Incentives

These are the editable source files for the YouTube video, the Short and the thumbnail. Everything is code-driven: change the script, re-voice it, and every animation cue and caption re-times itself automatically.

```
production/
  script/     main_script.json, short_script.json   ← edit narration here
              *_timeline.json                        ← generated: exact spoken spans per line
  audio/      *_narration.wav (raw TTS), *_narration_master.wav (−14 LUFS, 48 kHz stereo)
  captions/   *.en.srt (identical to the burned-in captions)
  render/     aurora_gfx.py      brand constants, easing, text QC, illustration components
              video_core.py      render loop, captions/SRT, transitions, audio mastering, encode
              main_video.py      8 scenes of the 16:9 film; hypothetical economics as named constants
              short_video.py     5 scenes of the 9:16 Short (Shorts-safe layout)
              thumbnail.py       1280×720 + 1920×1080 thumbnail (+ SVG)
              narrate.py         line-by-line TTS → narration WAV + timeline
              export_captions.py SRT export (asserts no overlapping captions)
              write_script_doc.py narration script document with timecodes
  svg/        editable vector keyframes per scene + thumbnail (Illustrator / Figma / Inkscape)
  fonts/      Fraunces, Geist, Geist Mono (SIL OFL 1.1) and the static instances the renderer uses
```

## Rebuild

```bash
pip install --break-system-packages pycairo numpy soundfile sherpa-onnx fonttools pillow
apt-get install -y ffmpeg libcairo2-dev
cd production/fonts && python3 make_font_instances.py && cp Aurora*.ttf ~/.fonts/ && fc-cache -f   # Fraunces, Geist, Geist Mono
cd ../render
export AURORA_TTS_MODEL_DIR=/path/to/kokoro-int8-en-v0_19   # see "Voice" below
python3 narrate.py --script ../script/main_script.json       # --dry-run lists lines only
python3 narrate.py --script ../script/short_script.json
python3 main_video.py            # captioned 1920×1080 → deliverables/
python3 main_video.py --clean    # no burned-in captions (upload with the SRT instead)
python3 short_video.py && python3 short_video.py --clean
python3 thumbnail.py && python3 export_captions.py && python3 write_script_doc.py
python3 main_video.py --stills 12 40.5 --out /tmp/review   # review frames; prints any text-bounds QC issues
python3 main_video.py --svg --out ../svg                   # editable vector keyframes
```

A full 16:9 render takes about 3 minutes on 4 CPU cores.

## Key settings

- **Hypothetical economics** are named constants at the top of `main_video.py`: `ASSUMED_ANNUAL_TAX_SAVINGS`, `ADDITIONAL_AFTER_TAX_OCCUPANCY_COST` and the derived `REMAINING_ANNUAL_ADVANTAGE`. Chart heights, count-ups and labels all derive from them. An `assert` stops the render if the result stops matching the narrated $6,000.
- **Visual system** is set in `aurora_gfx.py`: a flat, outline-free editorial style directed by the Madrid en Cifras 2020 reference spreads. It has an off-white page (#F1F1F4), indigo condensed hero numerals (#2D2B6E), coral section labels and hairline rules (#E5474E), italic grey secondary lines, tall geometric figures, and an orange block map with white street gaps. The chart colors are blue #3A6BC8 for savings, coral #E5474E for costs and orange #F29A3A for what remains. They pass the colour-blind separation and lightness checks, and every bar carries a direct label. Logo and type follow The Aurora Standard v5 (DS-AUR-005). The logo is the locked lockup: a mark of twelve heritage-spectrum ticks on a faint ring, plus the wordmark "aur*o*ra" in Fraunces 300 (opsz 144, SOFT 20). The italic "o" is amber-dark #8A5E27 on light backgrounds and amber-light #D9AE7A on dark; the wordmark is ink #1A2236 on light and cream on dark, never recoloured. Fraunces 330/340 carries headlines and hero numerals; Geist 400/500/600 carries text and UI; Geist Mono 500 carries labels, folios and axis values. There is one Fraunces wonky-italic emphasis per view at most. All fonts are SIL OFL 1.1, in `fonts/`.
- **Pacing** is set per script in `pacing` (lead-in and gaps) and `voice.speed`.
- **Loudness targets** are `TARGET_LUFS = -14`, `TARGET_TRUE_PEAK = -1.5` in `video_core.py`.

## Voice

The narration is an original synthetic voice: **Kokoro-82M v0.19** (Apache-2.0), int8 ONNX export, run locally with sherpa-onnx, speaker `af_sarah`. It does not imitate any real person. The model files (134 MB) are not committed because they exceed GitHub's per-file limit. They ship inside the npm package `n8n-nodes-ttsbro@0.1.6` (Apache-2.0) under `package/kokoro-int8-en-v0_19/`. Point `AURORA_TTS_MODEL_DIR` at that folder. To swap in a human voice-over, replace `audio/*_narration.wav` and adjust the line times in `script/*_timeline.json`; the film re-times from those.

No music is used. None was supplied, and no licensed track was available to this environment.

## Provenance of artwork

All illustrations are original vector drawings generated by the code in `render/`. No stock, AI-generated imagery or third-party artwork is used. Style direction follows screenshots of *Madrid en Cifras 2020* (Romualdo Faura) that you supplied. The Behance page itself is blocked from this environment. No artwork, figures, maps or layouts from it were traced or copied; only the general system (palette logic, type pairing, flat figures, numeral-led layout) was adopted.
