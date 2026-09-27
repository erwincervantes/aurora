"""Aurora Short — 'Up to 10 years of tax relief? Not for every business.' (1080x1920, ~34 s).

Layout keeps content inside the Shorts-safe area: captions sit above the bottom title overlay
(y < 1545) and stay left of the right-hand action buttons (x < 960).
"""
import argparse
import math
from pathlib import Path

from aurora_gfx import *  # noqa: F401,F403
from aurora_gfx import QC
import video_core as vc

W, H = 1080, 1920
LEFT = 80
RIGHT = 1000
CAPTION_ZONE = (80, 1360, 960, 1548)


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
        dark = scene == "s_close" and t > self.scenes["s_close"]["start"] + 0.2
        set_color(ctx, NAVY if dark else CREAM)
        ctx.paint()
        getattr(self, scene)(ctx, t)
        if scene != "s_close":
            a = ease_out(prog(t, 0.1, 0.5))
            wordmark(ctx, LEFT, 150, 42, alpha=a)
            kicker(ctx, "El Salvador", RIGHT, 146, alpha=a, align="right", size=22)
            stroke_polyline(ctx, [(LEFT, 184), (LEFT + 920 * ease_out(prog(t, 0.1, 1.0)), 184)], NAVY, 1.2, alpha=0.35 * a)
        vc.draw_transition(ctx, t, self.boundaries, W, H)
        if self.captions_on:
            vc.draw_caption(ctx, self.captions, t, 520, 1540, 46, 860)

    # ------------------------------------------------------------ hook
    def s_hook(self, ctx, t):
        l0, l1 = self.line("s_hook", 0), self.line("s_hook", 1)
        text_block(ctx, "Up to 10 years of tax relief?", LEFT, 330, FONT_HEAD, 104, NAVY, 900, leading=1.08,
                   p=prog(t, l0["start"], 1.1))
        panel(ctx, LEFT, 580, 920, 540, MINT, prog(t, 0.2, 0.7), "up")
        ctx.save()
        ctx.rectangle(LEFT, 580, 920, 540)
        ctx.clip()
        ground_line(ctx, LEFT, LEFT + 920, 1040, prog(t, 0.5, 0.6))
        historic_facade(ctx, 260, 1040, 440, 320, YELLOW, prog(t, 0.5, 1.6), prog(t, 1.5, 0.5))
        for year in range(10):
            yp = ease_out(prog(t, phrase_time(l0, "ten years") + year * 0.08, 0.3))
            if yp > 0:
                ctx.rectangle(LEFT + 60 + year * 82, 610, 74, 34 * yp)
                set_color(ctx, YELLOW)
                ctx.fill_preserve()
                set_color(ctx, NAVY)
                ctx.set_line_width(LINE * 0.8)
                ctx.stroke()
        person(ctx, 820, 1040, 190, SALMON, arms="present", facing=-1, alpha=ease_out(prog(t, 1.2, 0.5)))
        ctx.restore()
        answers = [(phrase_time(l1, "For qualifying"), "Qualifying investments", "Potentially", MINT, "check"),
                   (phrase_time(l1, "For every"), "Every business", "No", SALMON, "cross")]
        for k, (start, who, verdict, color, mark) in enumerate(answers):
            y = 1150 + k * 100
            a, dy = rise(ctx, t, start)
            if a <= 0:
                continue
            rounded_rect(ctx, LEFT, y + dy, 920, 84, 14)
            set_color(ctx, color, a)
            ctx.fill_preserve()
            set_color(ctx, NAVY, a)
            ctx.set_line_width(LINE)
            ctx.stroke()
            badge(ctx, LEFT + 46, y + 42 + dy, 26, CREAM, prog(t, start + 0.2, 0.8), mark)
            text(ctx, who, LEFT + 92, y + 55 + dy, FONT_BODY_MED, 34, NAVY, alpha=a)
            text(ctx, verdict, LEFT + 890, y + 57 + dy, FONT_HEAD, 40, NAVY, "right", alpha=a)

    # ------------------------------------------------------------ zone
    def s_zone(self, ctx, t):
        l0 = self.line("s_zone", 0)
        kicker(ctx, "San Salvador", LEFT, 262, alpha=rise(ctx, t, l0["start"])[0])
        text_block(ctx, "One defined Historic Center, not the whole country", LEFT, 350, FONT_HEAD, 70, NAVY, 900,
                   leading=1.1, p=prog(t, l0["start"] + 0.1, 1.2))
        panel(ctx, LEFT, 540, 920, 680, BLUE, prog(t, self.scenes["s_zone"]["start"] + 0.1, 0.6), "up")
        plan = CityPlan(110, 570, 860, 540, cols=5, rows=4, gap=20,
                        perimeter=((1, 1), (4, 1), (4, 3), (3, 3), (3, 4), (1, 4)))
        plan.draw(ctx, t_grid=prog(t, l0["start"], 1.2), t_perimeter=prog(t, phrase_time(l0, "San Salvador"), 1.4),
                  t_fill=prog(t, phrase_time(l0, "defined Historic"), 1.0))
        la = ease_out(prog(t, phrase_time(l0, "defined Historic"), 0.5))
        if la > 0:
            stroke_polyline(ctx, [(110, 1162), (170, 1162)], NAVY, LINE * 1.4, dash=[14, 9], alpha=la)
            text(ctx, "Defined perimeter (illustrative)", 186, 1171, FONT_BODY_MED, 28, NAVY, alpha=la)

    # ------------------------------------------------------------ checks
    def s_checks(self, ctx, t):
        lines = [self.line("s_checks", i) for i in range(4)]
        a, dy = rise(ctx, t, lines[0]["start"])
        text(ctx, "Three checks", LEFT, 300 + dy, FONT_HEAD, 88, NAVY, alpha=a)
        rows = [("Location", "Inside the defined perimeter", BLUE),
                ("Investment", "Eligible activity, above the minimum", YELLOW),
                ("Approval", "Qualified by the Planning Authority", MINT)]
        for i, (title, sub, color) in enumerate(rows):
            y = 360 + i * 190
            appear = ease_out(prog(t, lines[0]["start"] + 0.15 + i * 0.15, 0.5))
            if appear <= 0:
                continue
            active = prog(t, lines[i + 1]["start"], 0.4)
            done = prog(t, lines[i + 1]["end"] - 0.4, 0.8)
            rounded_rect(ctx, LEFT, y, 920, 164, 14)
            set_color(ctx, CREAM)
            ctx.fill()
            if active > 0:
                ctx.save()
                rounded_rect(ctx, LEFT, y, 920, 164, 14)
                ctx.clip()
                ctx.rectangle(LEFT, y, 920 * ease_in_out(active), 164)
                set_color(ctx, color)
                ctx.fill()
                ctx.restore()
            rounded_rect(ctx, LEFT, y, 920, 164, 14)
            set_color(ctx, NAVY, appear)
            ctx.set_line_width(LINE)
            ctx.stroke()
            if done > 0:
                badge(ctx, LEFT + 80, y + 82, 42, CREAM, done, "check")
            else:
                ctx.arc(LEFT + 80, y + 82, 42, 0, 2 * math.pi)
                set_color(ctx, CREAM, appear)
                ctx.fill_preserve()
                set_color(ctx, NAVY, appear)
                ctx.stroke()
                text(ctx, str(i + 1), LEFT + 80, y + 98, FONT_HEAD, 46, NAVY, "center", alpha=appear)
            text(ctx, title, LEFT + 150, y + 74, FONT_HEAD, 50, NAVY, alpha=appear)
            text(ctx, sub, LEFT + 150, y + 124, FONT_BODY, 30, NAVY, alpha=appear * (0.55 + 0.45 * active))
        # illustration strip under the list, one per check
        x, y, w, h = LEFT, 960, 920, 360
        for k in range(3):
            p = prog(t, lines[k + 1]["start"], 0.55)
            if p <= 0:
                continue
            ctx.save()
            ctx.rectangle(x - 4, y - 4, w * ease_in_out(p) + 8, h + 8)
            ctx.clip()
            ctx.rectangle(x, y, w, h)
            set_color(ctx, rows[k][2])
            ctx.fill()
            start = lines[k + 1]["start"]
            if k == 0:
                plan = CityPlan(110, 990, 860, 300, cols=4, rows=2, gap=24, perimeter=((0, 0), (2, 0), (2, 2), (0, 2)))
                plan.draw(ctx, t_grid=prog(t, start, 0.8), t_perimeter=prog(t, start + 0.3, 1.0), t_fill=0,
                          highlight={(1, 0): (MINT, prog(t, start + 0.8, 0.5)), (2, 1): (SALMON, prog(t, start + 1.2, 0.5))})
                for (c, r), mark, delay in (((1, 0), "check", 1.0), ((2, 1), "cross", 1.4)):
                    cx, cy = plan.block_center(c, r)
                    badge(ctx, cx, cy, 30, CREAM, prog(t, start + delay, 0.8), mark)
            elif k == 1:
                cx = 110
                for j, (label, fill) in enumerate((("Food", MINT), ("Lodging", SALMON), ("Culture", BLUE), ("Restoration", CREAM))):
                    cx += chip(ctx, label, cx, 1000, fill, size=28, alpha=ease_out(prog(t, start + j * 0.15, 0.4))) + 12
                kicker(ctx, "Investment vs. minimum", 110, 1130, alpha=ease_out(prog(t, start + 0.4, 0.4)), size=22)
                rounded_rect(ctx, 110, 1152, 860, 56, 28)
                set_color(ctx, CREAM)
                ctx.fill()
                fill = ease_out(prog(t, start + 0.6, 1.4)) * 0.8
                if fill > 0:
                    rounded_rect(ctx, 110, 1152, 860 * fill, 56, 28)
                    set_color(ctx, BLUE)
                    ctx.fill()
                rounded_rect(ctx, 110, 1152, 860, 56, 28)
                set_color(ctx, NAVY)
                ctx.set_line_width(LINE)
                ctx.stroke()
                mx = 110 + 860 * 0.6
                stroke_polyline(ctx, [(mx, 1136), (mx, 1224)], NAVY, LINE * 1.3)
                text(ctx, "Minimum", mx + 12, 1262, FONT_BODY_MED, 26, NAVY)
            else:
                document(ctx, 170, 990, 190, 250, CREAM, 6, prog(t, start, 0.8), prog(t, start, 0.8), rotate=-0.05)
                stamp(ctx, 380, 1190, 72, prog(t, start + 0.9, 0.8))
                text(ctx, "APLAN", 560, 1110, FONT_HEAD, 58, NAVY, alpha=ease_out(prog(t, start + 0.4, 0.5)))
                text(ctx, "Historic Center", 560, 1160, FONT_BODY_MED, 30, NAVY, alpha=ease_out(prog(t, start + 0.5, 0.5)))
                text(ctx, "Planning Authority", 560, 1200, FONT_BODY_MED, 30, NAVY, alpha=ease_out(prog(t, start + 0.5, 0.5)))
            ctx.restore()
            ctx.rectangle(x, y, w, h)
            set_color(ctx, NAVY)
            ctx.set_line_width(LINE)
            ctx.stroke()

    # ------------------------------------------------------------ beneficiary
    def s_benef(self, ctx, t):
        l0 = self.line("s_benef", 0)
        a, dy = rise(ctx, t, l0["start"])
        text(ctx, "Who receives it?", LEFT, 300 + dy, FONT_HEAD, 88, NAVY, alpha=a)
        resolve = phrase_time(l0, "A landlord")
        cards = [("Owner · landlord", YELLOW, {"prop": "folder", "arms": "hold"}, "check"),
                 ("Operator · tenant", MINT, {"apron": True, "arms": "present"}, "cross"),
                 ("Developer", BLUE, {"hardhat": True, "arms": "point"}, "question")]
        for i, (label, color, pose, final) in enumerate(cards):
            y = 370 + i * 250
            start = l0["start"] + 0.3 + i * 0.3
            panel(ctx, LEFT, y, 920, 220, color, prog(t, start, 0.5), "right")
            if prog(t, start, 0.5) <= 0:
                continue
            ctx.save()
            ctx.rectangle(LEFT, y, 920, 220)
            ctx.clip()
            person(ctx, LEFT + 110, y + 208, 180, CREAM if color != CREAM else PAPER, alpha=ease_out(prog(t, start + 0.2, 0.4)), **pose)
            ctx.restore()
            text(ctx, label, LEFT + 230, y + 128, FONT_HEAD, 52, NAVY, alpha=ease_out(prog(t, start + 0.2, 0.4)))
            mark = final if t > resolve + 0.2 * i else "question"
            fill = {"check": MINT, "cross": SALMON, "question": CREAM}[mark]
            bstart = start + 0.2 if mark == "question" else resolve + 0.2 * i
            badge(ctx, LEFT + 840, y + 110, 40, fill, prog(t, bstart, 0.8), mark)
        na, ndy = rise(ctx, t, phrase_time(l0, "automatically"))
        if na > 0:
            rounded_rect(ctx, LEFT, 1130 + ndy, 920, 170, 16)
            set_color(ctx, SALMON, na)
            ctx.fill_preserve()
            set_color(ctx, NAVY, na)
            ctx.set_line_width(LINE)
            ctx.stroke()
            text(ctx, "Landlord approved ≠", LEFT + 40, 1200 + ndy, FONT_HEAD, 50, NAVY, alpha=na)
            text(ctx, "tenant benefits automatically", LEFT + 40, 1262 + ndy, FONT_HEAD_REG, 46, NAVY, alpha=na)

    # ------------------------------------------------------------ close
    def s_close(self, ctx, t):
        s = self.scenes["s_close"]["start"]
        l0 = self.line("s_close", 0)
        a = ease_out(prog(t, s + 0.3, 0.6))
        wordmark(ctx, W / 2, 360, 120, color=CREAM, fill=YELLOW, alpha=a, align="center")
        kicker(ctx, "Latin America Expansion", W / 2, 430, alpha=a, color=CREAM, size=26, align="center")
        sp = ease_back(prog(t, l0["start"] + 0.1, 0.6))
        if sp > 0:
            ctx.save()
            ctx.translate(W / 2, 540)
            ctx.scale(sp, sp)
            rounded_rect(ctx, -190, -48, 380, 96, 48)
            set_color(ctx, YELLOW)
            ctx.fill_preserve()
            set_color(ctx, CREAM)
            ctx.set_line_width(LINE)
            ctx.stroke()
            text(ctx, "Subscribe", 0, 14, FONT_BODY_SEMI, 42, NAVY, "center")
            ctx.restore()
        text(ctx, "@ConAurora", W / 2, 660, FONT_BODY_MED, 36, CREAM, "center", alpha=rise(ctx, t, l0["start"] + 0.5)[0])
        np_ = prog(t, phrase_time(l0, "the next breakdown") - 0.2, 0.6)
        panel(ctx, LEFT, 730, 920, 580, CREAM, np_, "up", radius=18)
        if np_ > 0:
            na = ease_out(prog(t, phrase_time(l0, "the next breakdown"), 0.5))
            kicker(ctx, "Next breakdown", LEFT + 50, 800, alpha=na, size=24)
            text_block(ctx, "Who actually gets the benefit: owner, operator, or developer?", LEFT + 50, 876, FONT_HEAD, 54,
                       NAVY, 820, leading=1.14, alpha=na)
            ground_line(ctx, LEFT + 50, LEFT + 870, 1250, prog(t, phrase_time(l0, "owner") - 0.4, 0.6))
            for k, (shirt, kw) in enumerate(((YELLOW, {"prop": "folder", "arms": "hold"}), (MINT, {"apron": True}),
                                             (BLUE, {"hardhat": True, "arms": "point", "facing": -1}))):
                fa = ease_out(prog(t, phrase_time(l0, ("owner", "operator", "developer")[k]), 0.5))
                person(ctx, 300 + k * 240, 1250, 200, shirt, alpha=fa, **kw)


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
    if args.stills:
        for time in args.stills:
            for issue in vc.still(film, time, out / f"short_{time:06.2f}.png"):
                print(f"{time:6.2f}s  {issue}")
        return
    if args.qc_only:
        stem = "Aurora_ElSalvador_TaxIncentives_Short_1080x1920" + ("_clean" if args.clean else "")
        count, issues = vc.qc_pass(film, stem, args.workers)
        print(f"{stem}: {len(issues)} of {count} frames flagged")
        return
    if args.svg:
        for scene in film.timeline["scenes"]:
            keyframe = max(line["end"] for line in scene["lines"]) - 0.1
            vc.svg_frame(film, keyframe, out / f"short_{scene['id']}_keyframe.svg")
        return
    master = vc.PRODUCTION / "audio" / "short_narration_master.wav"
    vc.master_audio(vc.PRODUCTION / "audio" / "short_narration.wav", master)
    name = "Aurora_ElSalvador_TaxIncentives_Short_1080x1920" + ("_clean" if args.clean else "") + ".mp4"
    issues = vc.render(film, out / name, master, workers=args.workers)
    print(f"rendered {out / name}; QC issues on {len(issues)} frames")
    for index, problems in issues[:40]:
        print(f"{index / vc.FPS:7.2f}s  " + " | ".join(sorted(set(problems))))


if __name__ == "__main__":
    main()
