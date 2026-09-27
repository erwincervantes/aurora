"""Aurora Short — 'Up to 10 years of tax relief? Not for every business.' (1080x1920, ~34 s).

Same flat 'facts & figures' system as the main film. Content stays inside the Shorts-safe area:
captions sit above the bottom title overlay (y < 1545) and left of the action buttons (x < 960).
"""
import argparse
from pathlib import Path

from aurora_gfx import *  # noqa: F401,F403
from aurora_gfx import QC
import video_core as vc

W, H = 1080, 1920
LEFT, RIGHT = 80, 1000
CAPTION_ZONE = (80, 1360, 960, 1548)
SECTIONS = {"s_hook": "The question", "s_zone": "Geography", "s_checks": "Eligibility", "s_benef": "Beneficiary"}


class ShortFilm(vc.Film):
    width, height, video_id = W, H, "short"

    def caption_style(self):
        return {"max_chars": 30, "max_rows": 2}

    def line(self, scene, i):
        return self.scenes[scene]["lines"][i]

    def current_scene(self, t):
        scene = self.timeline["scenes"][0]
        for s in self.timeline["scenes"]:
            if t >= s["start"]:
                scene = s
        return scene["id"]

    def draw(self, ctx, t):
        QC.width, QC.height, QC.caption_zone, QC.safe_margin = W, H, CAPTION_ZONE if self.captions_on else None, 60
        scene = self.current_scene(t)
        dark = scene == "s_close" and t > self.scenes["s_close"]["start"] + 0.1
        set_color(ctx, LOGO_INK if dark else PAGE)
        ctx.paint()
        if not dark:
            a = ease_out(prog(t, 0.1, 0.5))
            wordmark(ctx, LEFT, 132, 36, alpha=a)
            index = [s["id"] for s in self.timeline["scenes"]].index(scene) + 1
            text(ctx, f"{index:02d} | {len(self.timeline['scenes']):02d}", RIGHT, 132, MONO, 26, INK, "right", a)
            line(ctx, [(LEFT, 162), (LEFT + (RIGHT - LEFT) * ease_out(prog(t, 0.1, 1.0)), 162)], CORAL, 1.6, alpha=a)
            if scene in SECTIONS:
                section(ctx, t, self.scenes[scene]["start"] + 0.2, SECTIONS[scene], x=LEFT, y=226)
        getattr(self, scene)(ctx, t)
        vc.draw_transition(ctx, t, self.boundaries, W, H)
        if self.captions_on:
            vc.draw_caption(ctx, self.captions, t, 520, 1540, 46, 860)

    # ------------------------------------------------------------ hook
    def s_hook(self, ctx, t):
        l0, l1 = self.line("s_hook", 0), self.line("s_hook", 1)
        a, dy = rise(t, l0["start"])
        text(ctx, "Up to", LEFT, 360 + dy, HEAD, 60, INK, alpha=a)
        count = 1 + int(9 * ease_in_out(prog(t, phrase_time(l0, "ten-year") - 0.2, 1.0)))
        size, baseline = 440, 800
        big_number(ctx, str(count), LEFT - 10, baseline + dy, size, INK, alpha=a)
        ten_w = text_width(ctx, "10", NUM, size)
        text(ctx, "years", LEFT + ten_w + 12, baseline + dy, NUM_MED, 130, INK, alpha=a)
        font(ctx, NUM, size)
        zero = ctx.text_extents("0")
        seat_x = LEFT - 10 + text_width(ctx, "1", NUM, size) + zero.x_bearing + zero.width * 0.3
        person(ctx, seat_x, baseline + zero.y_bearing + dy, 190, WHITE, BLUE, CORAL, seated=True, arms="hold",
               prop="document", coat=True, alpha=ease_out(prog(t, 1.4, 0.5)))
        for year in range(10):
            yp = ease_out(prog(t, 0.8 + year * 0.1, 0.3))
            x = LEFT + year * 92
            line(ctx, [(x, 840), (x, 840 - 18 * yp)], CORAL, 2.4)
            disc(ctx, x, 834 - 18 * yp, 6 * yp, CORAL)
        line(ctx, [(LEFT, 840), (LEFT + 828 * ease_out(prog(t, 0.8, 1.2)), 840)], CORAL, 1.6)
        text(ctx, "of tax relief.", LEFT, 940 + dy, HEAD, 64, INK, alpha=a)
        qa, qdy = rise(t, l1["start"])
        if qa > 0:
            line(ctx, [(LEFT, 1010), (LEFT + 920 * qa, 1010)], CORAL, 1.6)
            text(ctx, "Does your project", LEFT, 1112 + qdy, WONK, 76, CORAL, alpha=qa)
            text(ctx, "qualify?", LEFT, 1200 + qdy, WONK, 76, CORAL, alpha=qa)
            person(ctx, 870, 1320, 300, INK, SKY, GOLD, arms="hold", prop="document", facing=-1,
                   alpha=ease_out(prog(t, l1["start"] + 0.2, 0.5)))

    # ------------------------------------------------------------ geography
    def s_zone(self, ctx, t):
        l0 = self.line("s_zone", 0)
        a, dy = rise(t, l0["start"])
        text(ctx, "San Salvador's Historic Center", LEFT, 350 + dy, HEAD, 64, INK, alpha=a)
        text(ctx, "Within the defined area", LEFT, 412 + dy, SUB, 36, GREY, alpha=a)
        plan = CityPlan(LEFT, 490, 920, 640, cols=6, rows=6, gap=9,
                        perimeter=((1, 1), (5, 1), (5, 3), (6, 3), (6, 5), (2, 5), (2, 4), (1, 4)))
        plan.draw(ctx, t_grid=prog(t, l0["start"], 1.2), t_fill=prog(t, phrase_time(l0, "qualifying new"), 1.4))
        for k, ((c, r), kind) in enumerate((((2, 2), "check"), ((4, 3), "check"), ((5, 4), "question"))):
            cx, cy = plan.block_center(c, r)
            badge(ctx, cx, cy, 30, kind, prog(t, phrase_time(l0, "up to ten") + k * 0.3, 0.8))
        la = ease_out(prog(t, phrase_time(l0, "qualifying new"), 0.5))
        if la > 0:
            pointer(ctx, LEFT, 1176, 20, CORAL, la)
            text(ctx, "Up to 10 years of tax relief for qualifying new investments", LEFT + 32, 1194, SANS_SEMI, 30, INK, alpha=la)
            text(ctx, "Illustrative, not the legal map", LEFT + 32, 1236, SUB, 28, GREY, alpha=la)

    # ------------------------------------------------------------ eligibility
    def s_checks(self, ctx, t):
        ln = self.line("s_checks", 0)
        a, dy = rise(t, ln["start"])
        text(ctx, "Before you count", LEFT, 340 + dy, HEAD, 66, INK, alpha=a)
        text(ctx, "the savings:", LEFT, 414 + dy, HEAD, 66, INK, alpha=a)
        cues = [phrase_time(ln, p) for p in ("the exact location", "the qualifying investment", "the required approval")]
        ends = cues[1:] + [ln["end"]]
        rows = ("Location", "Investment", "Approval")
        for i, title in enumerate(rows):
            y = 530 + i * 110
            appear = ease_out(prog(t, ln["start"] + 0.3 + i * 0.12, 0.5))
            if appear <= 0:
                continue
            active = prog(t, cues[i], 0.4)
            done = prog(t, ends[i] - 0.3, 0.8)
            if done > 0:
                badge(ctx, LEFT + 36, y, 36, "check", done)
            else:
                marker(ctx, LEFT + 36, y, 36, i + 1, mix(RULE, CORAL, active), appear)
            text(ctx, title, LEFT + 100, y + 17, HEAD, 54, INK, alpha=appear * (0.4 + 0.6 * max(active, done)))
        for k in range(3):
            start = cues[k]
            p = prog(t, start, 0.55)
            if p <= 0:
                continue
            with wipe(ctx, LEFT - 10, 890, 940, 380, p, "right") as e:
                rect(ctx, LEFT - 10, 890, 940, 380, PAGE)
                if k == 0:
                    plan = CityPlan(LEFT, 910, 920, 320, cols=5, rows=2, gap=9,
                                    perimeter=((0, 0), (3, 0), (3, 1), (2, 1), (2, 2), (0, 2)))
                    plan.draw(ctx, 1, 1, highlight={(1, 0): (GOLD, prog(t, start + 0.3, 0.4)),
                                                    (3, 1): (CORAL, prog(t, start + 0.6, 0.4))})
                    for (c, r), kind, d in (((1, 0), "check", 0.4), ((3, 1), "cross", 0.7)):
                        cx, cy = plan.block_center(c, r)
                        badge(ctx, cx, cy, 32, kind, prog(t, start + d, 0.8))
                elif k == 1:
                    cx = LEFT
                    for j, (label, dot) in enumerate((("Food", ORANGE), ("Lodging", BLUE), ("Culture", PURPLE),
                                                      ("Restoration", PINK))):
                        cx += pill(ctx, label, cx, 920, WHITE, 28, alpha=ease_out(prog(t, start + j * 0.12, 0.4)),
                                   dot=dot) + 12
                    text(ctx, "Eligible activity, above the minimum", LEFT, 1042, SANS_MED, 30, INK)
                    x0, x1, y = LEFT, LEFT + 900, 1130
                    line(ctx, [(x0, y), (x1, y)], INK, 1.6)
                    for j in range(46):
                        tx = x0 + (x1 - x0) * j / 45
                        line(ctx, [(tx, y), (tx, y - (16 if j % 5 == 0 else 8))], INK, 1.2)
                    fill = ease_out(prog(t, start + 0.3, 1.2)) * 0.8
                    rect(ctx, x0, y + 10, (x1 - x0) * fill, 40, BLUE)
                    mx = x0 + (x1 - x0) * 0.6
                    line(ctx, [(mx, y - 34), (mx, y + 60)], CORAL, 3.4)
                    text(ctx, "Minimum", mx + 12, y - 16, SANS_SEMI, 28, CORAL)
                else:
                    document(ctx, LEFT + 40, 920, 200, 260, 6, prog(t, start, 0.6), rotate=-0.05)
                    stamp(ctx, LEFT + 250, 1130, 76, prog(t, start + 0.5, 0.8))
                    fade = ease_out(prog(t, start + 0.3, 0.5))
                    text(ctx, "APLAN", LEFT + 400, 1020, NUM, 84, INK, alpha=fade)
                    text(ctx, "Historic Center", LEFT + 400, 1074, SANS_MED, 32, INK, alpha=fade)
                    text(ctx, "Planning Authority", LEFT + 400, 1114, SANS_MED, 32, INK, alpha=fade)
            if 0 < e < 1:
                line(ctx, [(LEFT - 10 + 940 * e, 895), (LEFT - 10 + 940 * e, 1265)], CORAL, 2.4)

    # ------------------------------------------------------------ beneficiary
    def s_benef(self, ctx, t):
        l0, l1 = self.line("s_benef", 0), self.line("s_benef", 1)
        a, dy = rise(t, l0["start"])
        text(ctx, "Who receives", LEFT, 340 + dy, HEAD, 72, INK, alpha=a)
        text(ctx, "the benefit?", LEFT, 420 + dy, HEAD, 72, INK, alpha=a)
        resolve = l1["start"]
        groups = [("Owner", "Landlord", INK, SKY, {"prop": "keys", "arms": "hold"}, "check"),
                  ("Operator", "Tenant", WHITE, PURPLE, {"coat": True, "arms": "present", "hair_style": "bun"}, "cross"),
                  ("Developer", "Builds the project", SKY, INK, {"hardhat": True, "arms": "point"}, "question")]
        for i, (title, role, top, bottom_c, pose, final) in enumerate(groups):
            y = 480 + i * 200
            start = phrase_time(l0, "who actually") + i * 0.25
            ra, rdy = rise(t, start)
            if ra <= 0:
                continue
            rect(ctx, LEFT, y + rdy, 920, 180, LIGHT, ra, radius=12)
            ctx.save()
            ctx.rectangle(LEFT, y + rdy, 920, 180)
            ctx.clip()
            person(ctx, LEFT + 100, y + 176 + rdy, 165, top, bottom_c, GOLD if i == 0 else CORAL, alpha=ra, **pose)
            ctx.restore()
            text(ctx, title, LEFT + 210, y + 88 + rdy, HEAD, 48, INK, alpha=ra)
            text(ctx, role, LEFT + 210, y + 132 + rdy, SUB, 30, GREY, alpha=ra)
            kind = final if t > resolve + 0.25 * i else "question"
            bstart = start + 0.2 if kind == "question" else resolve + 0.25 * i
            badge(ctx, LEFT + 850, y + 90 + rdy, 36, kind, prog(t, bstart, 0.8))
        na, ndy = rise(t, phrase_time(l1, "does not"))
        if na > 0:
            rect(ctx, LEFT, 1100 + ndy, 920, 200, CORAL, na, radius=12)
            text_block(ctx, "A landlord's approval does not automatically extend to the tenant.", LEFT + 40, 1172 + ndy,
                       HEAD, 46, WHITE, 840, 1.18, alpha=na)

    # ------------------------------------------------------------ close: a reason to keep watching
    def s_close(self, ctx, t):
        s = self.scenes["s_close"]["start"]
        l0 = self.line("s_close", 0)
        a = ease_out(prog(t, s + 0.2, 0.6))
        wordmark(ctx, W / 2, 330, 80, reverse=True, alpha=a, align="center")
        text(ctx, "LATIN AMERICA EXPANSION", W / 2, 420, MONO, 22, CORAL, "center", a, tracking=3)
        ua, udy = rise(t, l0["start"])
        text(ctx, "Understand the incentive.", W / 2, 560 + udy, HEAD, 66, LOGO_CREAM, "center", ua)
        wa, wdy = rise(t, phrase_time(l0, "economics"))
        text(ctx, "Underwrite the opportunity.", W / 2, 650 + wdy, WONK, 66, AMBER_LT, "center", wa)
        sp = prog(t, phrase_time(l0, "economics") + 0.5, 0.6)
        if sp > 0:
            with pop(ctx, W / 2, 790, sp):
                pill(ctx, "Subscribe to @ConAurora", W / 2, 754, ORANGE, 38, LOGO_INK, SANS_SEMI, pad_x=48, align="center")
        ea, _ = rise(t, phrase_time(l0, "not just"))
        text_block(ctx, "The economics behind expansion, not just the headline incentives.", W / 2, 910, SUB, 32, SKY,
                   820, 1.25, "center", ea)
        np_ = prog(t, phrase_time(l0, "not just") + 0.3, 0.6)
        if np_ > 0:
            with wipe(ctx, LEFT, 1050, 920, 270, np_, "up"):
                rect(ctx, LEFT, 1050, 920, 270, PAGE, radius=14)
                na = ease_out(prog(t, phrase_time(l0, "not just") + 0.5, 0.5))
                text(ctx, "NEXT BREAKDOWN", LEFT + 44, 1108, MONO, 24, CORAL, alpha=na, tracking=2)
                text_block(ctx, "Who actually gets the benefit?", LEFT + 44, 1170, HEAD, 46, INK, 520, 1.12, alpha=na)
                for k, (top, bottom_c, kw) in enumerate(((INK, SKY, {"prop": "keys", "arms": "hold"}),
                                                        (WHITE, PURPLE, {"coat": True, "hair_style": "bun"}),
                                                        (SKY, INK, {"hardhat": True, "arms": "point", "facing": -1}))):
                    person(ctx, 680 + k * 100, 1300, 190, top, bottom_c,
                           alpha=ease_out(prog(t, phrase_time(l0, "not just") + 0.6 + k * 0.15, 0.4)), **kw)


def main():
    parser = argparse.ArgumentParser(description="Render the Aurora Short.")
    parser.add_argument("--out", default=str(vc.PRODUCTION.parent / "deliverables"))
    parser.add_argument("--stills", nargs="*", type=float)
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--svg", action="store_true")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--qc-only", action="store_true", help="run per-frame text QC without encoding")
    args = parser.parse_args()
    film = ShortFilm(captions_on=not args.clean)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    stem = "Aurora_ElSalvador_TaxIncentives_Short_1080x1920" + ("_clean" if args.clean else "")
    if args.stills:
        for time in args.stills:
            for issue in vc.still(film, time, out / f"short_{time:06.2f}.png"):
                print(f"{time:6.2f}s  {issue}")
        return
    if args.qc_only:
        count, issues = vc.qc_pass(film, stem, args.workers)
        print(f"{stem}: {len(issues)} of {count} frames flagged")
        return
    if args.svg:
        for scene in film.timeline["scenes"]:
            keyframe = max(ln["end"] for ln in scene["lines"]) - 0.1
            vc.svg_frame(film, keyframe, out / f"short_{scene['id']}_keyframe.svg")
        return
    master = vc.PRODUCTION / "audio" / "short_narration_master.wav"
    vc.master_audio(vc.PRODUCTION / "audio" / "short_narration.wav", master)
    issues = vc.render(film, out / f"{stem}.mp4", master, workers=args.workers)
    print(f"rendered {out / stem}.mp4; QC issues on {len(issues)} frames")
    for index, problems in issues[:40]:
        print(f"{index / vc.FPS:7.2f}s  " + " | ".join(sorted(set(problems))))


if __name__ == "__main__":
    main()
