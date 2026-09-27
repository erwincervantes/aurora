"""YouTube thumbnail, 1280x720 (also exported at 1920x1080 for high-DPI)."""
import argparse
from pathlib import Path

import cairo

from aurora_gfx import *  # noqa: F401,F403
import video_core as vc


def draw(ctx):
    set_color(ctx, CREAM)
    ctx.paint()
    kicker(ctx, "El Salvador · Tax incentives", 64, 96, size=20)
    text(ctx, "Up to 10 years", 60, 212, FONT_HEAD, 100, NAVY)
    text(ctx, "of tax relief?", 60, 318, FONT_HEAD_REG, 100, NAVY)
    width = text_width(ctx, "Who qualifies?", FONT_HEAD, 58)
    ctx.rectangle(56, 372, width + 24, 76)
    set_color(ctx, TERRACOTTA)
    ctx.fill()
    text(ctx, "Who qualifies?", 68, 428, FONT_HEAD, 58, NAVY)
    text(ctx, "Not every business does.", 64, 510, FONT_BODY_MED, 32, NAVY)
    wordmark(ctx, 64, 650, 40)
    # illustration panel
    panel(ctx, 760, 40, 480, 640, OCHRE)
    ground_line(ctx, 760, 1240, 560)
    historic_facade(ctx, 800, 560, 300, 260, CREAM, window_fill=COBALT)
    person(ctx, 1170, 560, 150, TEAL, apron=True, arms="present", facing=-1)
    # checklist card overlapping the panel edge
    kicker(ctx, "Year 1", 800, 102, size=16)
    kicker(ctx, "Year 10", 1200, 102, size=16, align="right")
    for year in range(10):
        ctx.rectangle(800 + year * 40, 116, 34, 44)
        set_color(ctx, TEAL)
        ctx.fill_preserve()
        set_color(ctx, NAVY)
        ctx.set_line_width(LINE * 0.8)
        ctx.stroke()
    rounded_rect(ctx, 690, 575, 540, 100, 12)
    set_color(ctx, CREAM)
    ctx.fill_preserve()
    set_color(ctx, NAVY)
    ctx.set_line_width(LINE)
    ctx.stroke()
    for k, (label, fill, mark) in enumerate((("Location", TEAL, "check"), ("Investment", TEAL, "check"), ("Approval", CREAM, "question"))):
        cx = (728, 898, 1082)[k]
        badge(ctx, cx, 625, 18, fill, 1, mark)
        text(ctx, label, cx + 26, 633, FONT_BODY_SEMI, 21, NAVY)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(vc.PRODUCTION.parent / "deliverables"))
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for scale, name in ((1.0, "Aurora_ElSalvador_TaxIncentives_Thumbnail_1280x720.png"),
                        (1.5, "Aurora_ElSalvador_TaxIncentives_Thumbnail_1920x1080.png")):
        surface = cairo.ImageSurface(cairo.FORMAT_RGB24, int(1280 * scale), int(720 * scale))
        ctx = cairo.Context(surface)
        ctx.scale(scale, scale)
        draw(ctx)
        surface.write_to_png(str(out / name))
    svg = cairo.SVGSurface(str(vc.PRODUCTION / "svg" / "thumbnail.svg"), 1280, 720)
    draw(cairo.Context(svg))
    svg.finish()


if __name__ == "__main__":
    main()
