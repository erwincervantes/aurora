"""Measure the delivered files (not the renderer) and write the QC report + contact sheets."""
import json
import re
import subprocess
from pathlib import Path

from PIL import Image

import video_core as vc
from export_captions import CAPTION_STYLES
from main_video import ASSUMED_ANNUAL_TAX_SAVINGS, ADDITIONAL_AFTER_TAX_OCCUPANCY_COST, REMAINING_ANNUAL_ADVANTAGE

DELIVERABLES = vc.PRODUCTION.parent / "deliverables"
SPEC = {  # file stem -> (width, height, min seconds, max seconds, video id)
    "Aurora_ElSalvador_TaxIncentives_YouTube_1920x1080": (1920, 1080, 90, 100, "main"),
    "Aurora_ElSalvador_TaxIncentives_YouTube_1920x1080_clean": (1920, 1080, 90, 100, "main"),
    "Aurora_ElSalvador_TaxIncentives_Short_1080x1920": (1080, 1920, 30, 35, "short"),
    "Aurora_ElSalvador_TaxIncentives_Short_1080x1920_clean": (1080, 1920, 30, 35, "short"),
}


def probe(path):
    data = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
                                     capture_output=True, text=True, check=True).stdout)
    video = next(s for s in data["streams"] if s["codec_type"] == "video")
    audio = next(s for s in data["streams"] if s["codec_type"] == "audio")
    return data["format"], video, audio


def loudness(path):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-map", "0:a", "-af", "ebur128=peak=true",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    summary = err[err.rindex("Summary:"):]
    integrated = float(re.search(r"I:\s+(-?[\d.]+) LUFS", summary).group(1))
    true_peak = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", summary).group(1))
    return integrated, true_peak


def silences(path, min_len=1.0):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-map", "0:a",
                          "-af", f"silencedetect=noise=-45dB:d={min_len}", "-f", "null", "-"], capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", err)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    return list(zip(starts, ends + [None] * (len(starts) - len(ends))))


def contact_sheet(path, out, width, height, every=3.0, duration=100.0, cols=6):
    thumb_w = 320 if width > height else 180
    thumb_h = int(thumb_w * height / width)
    times = [t for t in [x * every + 0.5 for x in range(int(duration / every) + 1)] if t < duration - 0.4]
    frames = []
    for t in times:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t}", "-i", str(path), "-frames:v", "1",
                              "-vf", f"scale={thumb_w}:{thumb_h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                             capture_output=True, check=True).stdout
        frames.append(Image.frombytes("RGB", (thumb_w, thumb_h), raw))
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * thumb_w, rows * thumb_h), "white")
    for i, frame in enumerate(frames):
        sheet.paste(frame, ((i % cols) * thumb_w, (i // cols) * thumb_h))
    sheet.save(out)


def main():
    lines = ["# QC Report", "", "Measured on the delivered MP4 files with ffprobe / ffmpeg (EBU R128).", "",
             "| File | Resolution | Duration | Spec | FPS | Video | Audio | Loudness | True peak | Result |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    notes = []
    for stem, (width, height, low, high, video_id) in SPEC.items():
        path = DELIVERABLES / f"{stem}.mp4"
        if not path.exists():
            lines.append(f"| {path.name} | — | — | — | — | — | — | — | — | **MISSING** |")
            continue
        fmt, video, audio = probe(path)
        duration = float(fmt["duration"])
        integrated, true_peak = loudness(path)
        ok = (int(video["width"]), int(video["height"])) == (width, height) and low <= duration <= high \
            and true_peak <= -1.0 and abs(integrated + 14) <= 1.0
        lines.append(f"| {path.name} | {video['width']}×{video['height']} | {duration:.2f} s | {low}–{high} s | "
                     f"{video['r_frame_rate']} | {video['codec_name']} {video.get('profile', '')} {video['pix_fmt']} | "
                     f"{audio['codec_name']} {audio['sample_rate']} Hz {audio['channels']} ch | {integrated:.1f} LUFS | "
                     f"{true_peak:.1f} dBTP | {'PASS' if ok else '**CHECK**'} |")
        render_qc = vc.PRODUCTION / "qc" / f"{stem}.render_qc.json"
        if render_qc.exists():
            rq = json.loads(render_qc.read_text())
            notes.append(f"- `{path.name}`: per-frame text-bounds QC (clipping outside safe area, overlap with caption zone): "
                         f"{rq['frames_with_text_issues']} of {rq['frames_rendered']} frames flagged.")
        if not stem.endswith("_clean"):
            gaps = [(a, b) for a, b in silences(path) if b is not None and a > 0.5 and b < duration - 1.5]
            notes.append(f"- `{path.name}`: silences ≥ 1.0 s inside the narration: {len(gaps)}"
                         + (f" ({', '.join(f'{a:.1f}–{b:.1f}s' for a, b in gaps)})" if gaps else "") + ".")
            sheet = vc.PRODUCTION / "qc" / f"{stem}_contact_sheet.png"
            sheet.parent.mkdir(exist_ok=True)
            contact_sheet(path, sheet, width, height, duration=duration)
            notes.append(f"- `{path.name}`: contact sheet of the encoded file every 3 s → `production/qc/{sheet.name}`.")
    for video_id, style in CAPTION_STYLES.items():
        captions = vc.build_captions(vc.load_timeline(video_id), **style)
        overlaps = sum(1 for a, b in zip(captions, captions[1:]) if a["end"] > b["start"])
        longest = max(len(r) for c in captions for r in c["rows"])
        shortest = min(c["end"] - c["start"] for c in captions)
        notes.append(f"- Captions ({video_id}): {len(captions)} cards, {overlaps} time overlaps, ≤ 2 rows, longest row "
                     f"{longest} chars, shortest card {shortest:.2f} s.")
    notes.append(f"- Arithmetic: {ASSUMED_ANNUAL_TAX_SAVINGS:,} − {ADDITIONAL_AFTER_TAX_OCCUPANCY_COST:,} = "
                 f"{REMAINING_ANNUAL_ADVANTAGE:,} ({'PASS' if ASSUMED_ANNUAL_TAX_SAVINGS - ADDITIONAL_AFTER_TAX_OCCUPANCY_COST == 6000 else 'FAIL'}).")
    lines += ["", "## Checks", ""] + notes
    (DELIVERABLES / "Aurora_ElSalvador_TaxIncentives_QC_Report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
