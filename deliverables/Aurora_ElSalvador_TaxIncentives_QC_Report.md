# QC Report

Measured on the delivered MP4 files with ffprobe / ffmpeg (EBU R128).

| File | Resolution | Duration | Spec | FPS | Video | Audio | Loudness | True peak | Result |
|---|---|---|---|---|---|---|---|---|---|
| Aurora_ElSalvador_TaxIncentives_YouTube_1920x1080.mp4 | 1920×1080 | 96.43 s | 90–100 s | 30/1 | h264 High yuv420p | aac 48000 Hz 2 ch | -14.3 LUFS | -4.3 dBTP | PASS |
| Aurora_ElSalvador_TaxIncentives_YouTube_1920x1080_clean.mp4 | 1920×1080 | 96.43 s | 90–100 s | 30/1 | h264 High yuv420p | aac 48000 Hz 2 ch | -14.3 LUFS | -4.3 dBTP | PASS |
| Aurora_ElSalvador_TaxIncentives_Short_1080x1920.mp4 | 1080×1920 | 32.65 s | 30–35 s | 30/1 | h264 High yuv420p | aac 48000 Hz 2 ch | -14.4 LUFS | -3.8 dBTP | PASS |
| Aurora_ElSalvador_TaxIncentives_Short_1080x1920_clean.mp4 | 1080×1920 | 32.65 s | 30–35 s | 30/1 | h264 High yuv420p | aac 48000 Hz 2 ch | -14.4 LUFS | -3.8 dBTP | PASS |

## Checks

- `Aurora_ElSalvador_TaxIncentives_YouTube_1920x1080.mp4`: per-frame text-bounds QC (clipping outside safe area, overlap with caption zone): 0 of 2893 frames flagged.
- `Aurora_ElSalvador_TaxIncentives_YouTube_1920x1080.mp4`: silences ≥ 1.0 s inside the narration: 0.
- `Aurora_ElSalvador_TaxIncentives_YouTube_1920x1080.mp4`: contact sheet of the encoded file every 3 s → `production/qc/Aurora_ElSalvador_TaxIncentives_YouTube_1920x1080_contact_sheet.png`.
- `Aurora_ElSalvador_TaxIncentives_YouTube_1920x1080_clean.mp4`: per-frame text-bounds QC (clipping outside safe area, overlap with caption zone): 0 of 2893 frames flagged.
- `Aurora_ElSalvador_TaxIncentives_Short_1080x1920.mp4`: per-frame text-bounds QC (clipping outside safe area, overlap with caption zone): 0 of 980 frames flagged.
- `Aurora_ElSalvador_TaxIncentives_Short_1080x1920.mp4`: silences ≥ 1.0 s inside the narration: 0.
- `Aurora_ElSalvador_TaxIncentives_Short_1080x1920.mp4`: contact sheet of the encoded file every 3 s → `production/qc/Aurora_ElSalvador_TaxIncentives_Short_1080x1920_contact_sheet.png`.
- `Aurora_ElSalvador_TaxIncentives_Short_1080x1920_clean.mp4`: per-frame text-bounds QC (clipping outside safe area, overlap with caption zone): 0 of 980 frames flagged.
- Captions (main): 28 cards, 0 time overlaps, ≤ 2 rows, longest row 48 chars, shortest card 1.42 s.
- Captions (short): 15 cards, 0 time overlaps, ≤ 2 rows, longest row 29 chars, shortest card 1.20 s.
- Arithmetic: 30,000 − 24,000 = 6,000 (PASS).
