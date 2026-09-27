"""YouTube thumbnail, 1280x720 (also exported at 1920x1080 for high-DPI)."""
import argparse
from pathlib import Path

import cairo

from aurora_gfx import *  # noqa: F401,F403
import video_core as vc


def draw(ctx):
    set_color(ctx, PAGE)
    ctx.paint()
    wordmark(ctx, 56, 64, 26)
    text(ctx, "EL SALVADOR · TAX INCENTIVES", 1224, 62, SANS_SEMI, 18, CORAL, "right", tracking=1.5)
    line(ctx, [(56, 84), (1224, 84)], CORAL, 1.4)
    text(ctx, "Up to", 60, 176, HEAD, 50, INK)
    size, baseline = 330, 520
    big_number(ctx, "10", 48, baseline, size)
    ten_w = text_width(ctx, "10", NUM, size)
    text(ctx, "years", 48 + ten_w + 10, baseline, NUM_MED, 96, INK)
    font(ctx, NUM, size)
    zero = ctx.text_extents("0")
    seat_x = 48 + text_width(ctx, "1", NUM, size) + zero.x_bearing + zero.width * 0.3
    person(ctx, seat_x, baseline + zero.y_bearing, 140, WHITE, BLUE, CORAL, seated=True, arms="hold", prop="document", coat=True)
    text(ctx, "of tax relief?", 60, 600, HEAD, 50, INK)
    pill(ctx, "Who qualifies?", 56, 626, CORAL, 32, WHITE, SANS_SEMI, pad_x=22)
    plan = CityPlan(760, 120, 470, 340, cols=5, rows=4, gap=7,
                    perimeter=((1, 0), (4, 0), (4, 2), (5, 2), (5, 4), (2, 4), (2, 3), (1, 3)))
    plan.draw(ctx)
    for (c, r), kind in (((2, 1), "check"), ((3, 2), "check"), ((4, 3), "cross")):
        cx, cy = plan.block_center(c, r)
        badge(ctx, cx, cy, 20, kind, 1)
    for k, (label, kind) in enumerate((("Location", "check"), ("Investment", "check"), ("Approval", "question"))):
        y = 500 + k * 62
        badge(ctx, 784, y, 20, kind, 1)
        text(ctx, label, 816, y + 10, SANS_SEMI, 30, INK)
    person(ctx, 1150, 690, 220, INK, SKY, GOLD, arms="point", prop=None, facing=-1)


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
