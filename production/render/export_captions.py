"""Write SRT caption files for both videos from the narration timelines (same chunks as the burned-in captions)."""
import argparse
from pathlib import Path

import video_core as vc

CAPTION_STYLES = {"main": {"max_chars": 48, "max_rows": 2}, "short": {"max_chars": 30, "max_rows": 2}}
FILE_NAMES = {"main": "Aurora_ElSalvador_TaxIncentives_YouTube_1920x1080.en.srt",
              "short": "Aurora_ElSalvador_TaxIncentives_Short_1080x1920.en.srt"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(vc.PRODUCTION.parent / "deliverables"))
    args = parser.parse_args()
    for video_id, style in CAPTION_STYLES.items():
        captions = vc.build_captions(vc.load_timeline(video_id), **style)
        for i in range(len(captions) - 1):  # QC: captions never overlap in time
            assert captions[i]["end"] <= captions[i + 1]["start"], (video_id, i)
        for folder in (Path(args.out), vc.PRODUCTION / "captions"):
            folder.mkdir(parents=True, exist_ok=True)
            vc.write_srt(captions, folder / FILE_NAMES[video_id])
        print(f"{video_id}: {len(captions)} captions, last ends {captions[-1]['end']:.2f}s")


if __name__ == "__main__":
    main()
