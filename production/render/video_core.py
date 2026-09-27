"""Shared render loop, captions/SRT, scene transitions, audio mastering and encoding."""
import json
import math
import multiprocessing as mp
import re
import subprocess
from pathlib import Path

import cairo

from aurora_gfx import (CREAM, NAVY, MINT, YELLOW, BLUE, SALMON, FONT_BODY_MED, QC, clamp, ease_in_out,
                        rounded_rect, set_color, text, text_width, stroke_polyline)

FPS = 30
PRODUCTION = Path(__file__).resolve().parent.parent

# Loudness targets for YouTube delivery (it normalizes to about -14 LUFS; speech mastered to match).
TARGET_LUFS = -14.0
TARGET_TRUE_PEAK = -1.5


def load_timeline(video_id):
    return json.loads((PRODUCTION / "script" / f"{video_id}_timeline.json").read_text())


# ---------------------------------------------------------------- captions
def _balanced_rows(words, max_chars, max_rows):
    """Split words into <= max_rows rows, each <= max_chars, preferring even rows that break after punctuation."""
    joined = " ".join(words)
    if len(joined) <= max_chars and (len(joined) <= max_chars * 0.62 or max_rows < 2):
        return [joined]
    best = None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        if len(a) <= max_chars and len(b) <= max_chars:
            score = max(len(a), len(b)) - (8 if a[-1] in ",:;—" else 0)
            if best is None or score < best[0]:
                best = (score, [a, b])
    if best and max_rows >= 2:
        return best[1]
    return [joined] if len(joined) <= max_chars else None

def _chunk_sentence(sentence, max_chars, max_rows):
    """Fewest caption cards per sentence; prefer breaks at clause punctuation; avoid tiny cards."""
    words = sentence.split()
    n = len(words)
    best = [(0.0, None)] + [(math.inf, None)] * n
    for end in range(1, n + 1):
        for start in range(end):
            if best[start][0] == math.inf or not _balanced_rows(words[start:end], max_chars, max_rows):
                continue
            cost = 10.0
            if end < n and words[end - 1][-1] not in ",:;—":
                cost += 12.0
            if end - start < 4:
                cost += 6.0
            if best[start][0] + cost < best[end][0]:
                best[end] = (best[start][0] + cost, start)
    chunks, end = [], n
    while end > 0:
        start = best[end][1]
        chunks.insert(0, words[start:end])
        end = start
    return chunks

def build_captions(timeline, max_chars=48, max_rows=2):
    """Clause-aware caption chunks, timed proportionally to characters inside each narrated line."""
    captions = []
    lines = [line for scene in timeline["scenes"] for line in scene["lines"]]
    for index, line in enumerate(lines):
        chunks = []
        for sentence in re.split(r"(?<=[.?!])\s+", line["text"]):  # never merge across sentences
            chunks.extend(_chunk_sentence(sentence, max_chars, max_rows))
        total_chars = sum(len(" ".join(c)) for c in chunks)
        cursor = line["start"]
        next_start = lines[index + 1]["start"] if index + 1 < len(lines) else line["end"] + 1.0
        for k, chunk in enumerate(chunks):
            share = (line["end"] - line["start"]) * len(" ".join(chunk)) / total_chars
            end = cursor + share
            display_end = end if k < len(chunks) - 1 else min(line["end"] + 0.35, next_start - 0.04)
            captions.append({"start": round(cursor, 3), "end": round(display_end, 3),
                             "rows": _balanced_rows(chunk, max_chars, max_rows)})
            cursor = end
    return captions

def srt_timestamp(seconds):
    ms = int(round(seconds * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"

def write_srt(captions, path):
    blocks = [f"{i}\n{srt_timestamp(c['start'])} --> {srt_timestamp(c['end'])}\n" + "\n".join(c["rows"]) + "\n"
              for i, c in enumerate(captions, 1)]
    Path(path).write_text("\n".join(blocks), encoding="utf-8")

def draw_caption(ctx, captions, t, center_x, bottom_y, size, max_box_width):
    """Stable open caption: solid navy box, cream Geist text; hard cuts (no motion) for readability."""
    active = [c for c in captions if c["start"] <= t < c["end"]]
    if not active:
        return
    rows = active[0]["rows"]
    line_h = size * 1.28
    widths = [text_width(ctx, r, FONT_BODY_MED, size) for r in rows]
    box_w = min(max_box_width, max(widths) + size * 1.3)
    box_h = line_h * len(rows) + size * 0.62
    x0, y0 = center_x - box_w / 2, bottom_y - box_h
    rounded_rect(ctx, x0, y0, box_w, box_h, 10)
    set_color(ctx, NAVY, 0.94)
    ctx.fill_preserve()
    set_color(ctx, CREAM, 0.9)
    ctx.set_line_width(1.5)
    ctx.stroke()
    for i, row in enumerate(rows):
        baseline = y0 + size * 0.31 + line_h * i + size * 0.98
        text(ctx, row, center_x, baseline, FONT_BODY_MED, size, CREAM, align="center", label=f"caption:{row}", is_caption=True)
    if max(widths) > max_box_width - size * 0.6:
        QC.boxes.append((-999, -999, -998, -998, f"caption too wide: {rows}", True))  # forces a QC flag


# ---------------------------------------------------------------- transitions
TRANSITION_HALF = 0.34
TRANSITION_SETS = [(MINT, YELLOW, BLUE), (SALMON, MINT, YELLOW), (BLUE, SALMON, MINT), (YELLOW, BLUE, SALMON)]

def draw_transition(ctx, t, boundaries, width, height):
    """Three colored bands sweep across and hand over to the next scene at full cover."""
    for index, boundary in enumerate(boundaries):
        if abs(t - boundary) >= TRANSITION_HALF + 0.12:
            continue
        colors = TRANSITION_SETS[index % len(TRANSITION_SETS)]
        vertical = height > width
        bands = len(colors)
        for b, color in enumerate(colors):
            stagger = b * 0.05
            if t < boundary:
                e = ease_in_out(clamp((t - (boundary - TRANSITION_HALF) + stagger) / (TRANSITION_HALF - 0.1)))
                a0, a1 = 0.0, e
            else:
                e = ease_in_out(clamp((t - boundary - stagger) / (TRANSITION_HALF - 0.1)))
                a0, a1 = e, 1.0
            if a1 - a0 <= 0:
                continue
            if vertical:
                band = height / bands
                x, y, w, h = width * a0, band * b, width * (a1 - a0), band
            else:
                band = height / bands
                x, y, w, h = width * a0, band * b, width * (a1 - a0), band
            ctx.rectangle(x, y, w, h)
            set_color(ctx, color)
            ctx.fill()
            for edge in (x, x + w):
                if 1 < edge < width - 1:
                    stroke_polyline(ctx, [(edge, y), (edge, y + h)], NAVY, 3)
            stroke_polyline(ctx, [(x, y + h), (x + w, y + h)], NAVY, 3)


# ---------------------------------------------------------------- render loop
class Film:
    """Subclasses implement draw(ctx, t). Render with Film.render(...)."""
    width = 1920
    height = 1080
    video_id = "main"

    def __init__(self, captions_on=True):
        self.timeline = load_timeline(self.video_id)
        self.duration = self.timeline["duration"]
        self.captions = build_captions(self.timeline, **self.caption_style())
        self.captions_on = captions_on
        self.scenes = {s["id"]: s for s in self.timeline["scenes"]}
        self.boundaries = [s["start"] for s in self.timeline["scenes"][1:]]

    def caption_style(self):
        return {"max_chars": 48, "max_rows": 2}

    def frame(self, t):
        surface = cairo.ImageSurface(cairo.FORMAT_RGB24, self.width, self.height)
        ctx = cairo.Context(surface)
        QC.reset()
        self.draw(ctx, t)
        return surface

    def draw(self, ctx, t):
        raise NotImplementedError


_FILM = None

def _render_frame(index):
    t = index / FPS
    surface = _FILM.frame(t)
    issues = QC.problems()
    return bytes(surface.get_data()), (index, issues) if issues else None

def master_audio(narration_wav, out_wav):
    """Two-pass EBU R128 loudness normalization to the delivery target, 48 kHz."""
    base = f"highpass=f=70,loudnorm=I={TARGET_LUFS}:TP={TARGET_TRUE_PEAK}:LRA=9"
    probe = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(narration_wav), "-af", base + ":print_format=json", "-f", "null", "-"],
                           capture_output=True, text=True)
    stats = json.loads(probe.stderr[probe.stderr.rindex("{"):probe.stderr.rindex("}") + 1])
    second = (f"{base}:measured_I={stats['input_i']}:measured_TP={stats['input_tp']}:measured_LRA={stats['input_lra']}"
              f":measured_thresh={stats['input_thresh']}:offset={stats['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(narration_wav), "-af", second,
                    "-ar", "48000", "-ac", "2", str(out_wav)], check=True)

def render(film, out_path, audio_wav, workers=4, limit=None):
    """Render every frame through cairo, encode H.264 High / AAC, return QC issues."""
    global _FILM
    _FILM = film
    frame_count = int(math.ceil(film.duration * FPS)) if limit is None else limit
    command = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
               "-f", "rawvideo", "-pix_fmt", "bgr0", "-s", f"{film.width}x{film.height}", "-r", str(FPS), "-i", "-",
               "-i", str(audio_wav),
               "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
               "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high", "-tune", "animation",
               "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
               "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out_path)]
    encoder = subprocess.Popen(command, stdin=subprocess.PIPE)
    issues = []
    with mp.get_context("fork").Pool(workers) as pool:
        for data, problem in pool.imap(_render_frame, range(frame_count), chunksize=8):
            encoder.stdin.write(data)
            if problem:
                issues.append(problem)
    encoder.stdin.close()
    encoder.wait()
    if encoder.returncode != 0:
        raise RuntimeError("ffmpeg failed")
    qc_dir = PRODUCTION / "qc"
    qc_dir.mkdir(exist_ok=True)
    (qc_dir / f"{Path(out_path).stem}.render_qc.json").write_text(json.dumps(
        {"frames_rendered": frame_count, "frames_with_text_issues": len(issues),
         "issues": [{"t": round(i / FPS, 3), "problems": p} for i, p in issues]}, indent=2))
    return issues

def _qc_frame(index):
    _FILM.frame(index / FPS)
    issues = QC.problems()
    return (index, issues) if issues else None

def qc_pass(film, stem, workers=4):
    """Re-run the per-frame text-bounds QC without encoding (same frames as the delivered file)."""
    global _FILM
    _FILM = film
    frame_count = int(math.ceil(film.duration * FPS))
    with mp.get_context("fork").Pool(workers) as pool:
        issues = [r for r in pool.imap(_qc_frame, range(frame_count), chunksize=8) if r]
    qc_dir = PRODUCTION / "qc"
    qc_dir.mkdir(exist_ok=True)
    (qc_dir / f"{stem}.render_qc.json").write_text(json.dumps(
        {"frames_rendered": frame_count, "frames_with_text_issues": len(issues),
         "issues": [{"t": round(i / FPS, 3), "problems": p} for i, p in issues]}, indent=2))
    return frame_count, issues

def still(film, t, path):
    film.frame(t).write_to_png(str(path))
    return QC.problems()

def svg_frame(film, t, path):
    """Editable vector export of a frame (open in Illustrator/Figma/Inkscape)."""
    surface = cairo.SVGSurface(str(path), film.width, film.height)
    ctx = cairo.Context(surface)
    QC.reset()
    film.draw(ctx, t)
    surface.finish()
