"""Synthesize narration line-by-line and build the timeline that drives animation cues and captions.

Usage:
    AURORA_TTS_MODEL_DIR=/path/to/kokoro-int8-en-v0_19 python3 narrate.py --script ../script/main_script.json

Outputs (next to the script's id):
    ../audio/<id>_narration.wav       mono 24 kHz narration, silence-trimmed lines with fixed gaps
    ../script/<id>_timeline.json      per-scene and per-line start/end times (seconds)
"""
import argparse
import json
import os
from pathlib import Path

import numpy as np
import soundfile as sf

# Pacing constants: gaps are what make synthetic narration sound unhurried.
LEAD_IN_SEC = 0.6          # silence before first line (lets the opening frame settle)
GAP_WITHIN_SCENE_SEC = 0.38
GAP_BETWEEN_SCENES_SEC = 0.75
TAIL_SEC = 1.6             # hold on end card after final line
SILENCE_THRESHOLD = 0.004  # amplitude below which leading/trailing samples are trimmed


def load_tts(model_dir: Path, threads: int):
    import sherpa_onnx
    kokoro = sherpa_onnx.OfflineTtsKokoroModelConfig(
        model=str(model_dir / "model.int8.onnx"),
        voices=str(model_dir / "voices.bin"),
        tokens=str(model_dir / "tokens.txt"),
        data_dir=str(model_dir / "espeak-ng-data"),
    )
    config = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(kokoro=kokoro, num_threads=threads))
    return sherpa_onnx.OfflineTts(config)


def trim_silence(samples: np.ndarray, sample_rate: int) -> np.ndarray:
    loud = np.where(np.abs(samples) > SILENCE_THRESHOLD)[0]
    if len(loud) == 0:
        return samples
    pad = int(0.03 * sample_rate)  # keep a breath of room so consonants aren't clipped
    return samples[max(0, loud[0] - pad): min(len(samples), loud[-1] + pad)]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--script", required=True)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--dry-run", action="store_true", help="print the line list without synthesizing")
    args = parser.parse_args()

    script_path = Path(args.script).resolve()
    script = json.loads(script_path.read_text())
    if args.dry_run:
        for scene in script["scenes"]:
            for line in scene["lines"]:
                print(f"[{scene['id']}] {line}")
        return

    model_dir = Path(os.environ["AURORA_TTS_MODEL_DIR"])
    tts = load_tts(model_dir, args.threads)
    voice = script["voice"]
    pacing = script.get("pacing", {})
    global LEAD_IN_SEC, GAP_WITHIN_SCENE_SEC, GAP_BETWEEN_SCENES_SEC, TAIL_SEC
    LEAD_IN_SEC = pacing.get("lead_in", LEAD_IN_SEC)
    GAP_WITHIN_SCENE_SEC = pacing.get("gap_within", GAP_WITHIN_SCENE_SEC)
    GAP_BETWEEN_SCENES_SEC = pacing.get("gap_between", GAP_BETWEEN_SCENES_SEC)
    TAIL_SEC = pacing.get("tail", TAIL_SEC)

    chunks, cursor = [], LEAD_IN_SEC
    sample_rate = tts.sample_rate
    chunks.append(np.zeros(int(LEAD_IN_SEC * sample_rate), dtype=np.float32))
    timeline = {"id": script["id"], "sample_rate": sample_rate, "scenes": []}

    for scene_index, scene in enumerate(script["scenes"]):
        scene_entry = {"id": scene["id"], "chapter": scene.get("chapter", ""), "start": cursor, "lines": []}
        for line_index, text in enumerate(scene["lines"]):
            audio = tts.generate(text, sid=voice["sid"], speed=voice["speed"])
            samples = trim_silence(np.asarray(audio.samples, dtype=np.float32), sample_rate)
            duration = len(samples) / sample_rate
            scene_entry["lines"].append({"text": text, "start": round(cursor, 3), "end": round(cursor + duration, 3)})
            chunks.append(samples)
            cursor += duration
            is_last_line = line_index == len(scene["lines"]) - 1
            is_last_scene = scene_index == len(script["scenes"]) - 1
            gap = TAIL_SEC if (is_last_line and is_last_scene) else (GAP_BETWEEN_SCENES_SEC if is_last_line else GAP_WITHIN_SCENE_SEC)
            chunks.append(np.zeros(int(gap * sample_rate), dtype=np.float32))
            cursor += gap
            print(f"{scene['id']:>12} {duration:5.2f}s  {text[:70]}")
        # Scene boundary sits mid-gap so transitions land in silence, not on a word.
        scene_entry["end"] = round(cursor - (0 if scene_index == len(script["scenes"]) - 1 else GAP_BETWEEN_SCENES_SEC / 2), 3)
        scene_entry["start"] = round(scene_entry["start"] if scene_index == 0 else timeline["scenes"][-1]["end"], 3)
        timeline["scenes"].append(scene_entry)
    timeline["scenes"][0]["start"] = 0.0

    narration = np.concatenate(chunks)
    timeline["duration"] = round(len(narration) / sample_rate, 3)
    out_audio = script_path.parent.parent / "audio" / f"{script['id']}_narration.wav"
    out_timeline = script_path.parent / f"{script['id']}_timeline.json"
    sf.write(out_audio, narration, sample_rate, subtype="PCM_16")
    out_timeline.write_text(json.dumps(timeline, indent=2))
    print(f"total {timeline['duration']:.2f}s -> {out_audio}")


if __name__ == "__main__":
    main()
