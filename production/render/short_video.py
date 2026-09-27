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
SECTIONS = {"s_hook": ("The question", "La pregunta"), "s_zone": ("The zone", "La zona"),
            "s_checks": ("Three checks", "Tres verificaciones"), "s_benef": ("Who benefits", "¿Quién se beneficia?")}


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
        set_color(ctx, INK if dark else PAGE)
        ctx.paint()
        if not dark:
            a = ease_out(prog(t, 0.1, 0.5))
            wordmark(ctx, LEFT, 132, 36, alpha=a)
            index = [s["id"] for s in self.timeline["scenes"]].index(scene) + 1
            text(ctx, f"{index:02d} | {len(self.timeline['scenes']):02d}", RIGHT, 132, NUM_MED, 30, INK, "right", a)
            line(ctx, [(LEFT, 162), (LEFT + (RIGHT - LEFT) * ease_out(prog(t, 0.1, 1.0)), 162)], CORAL, 1.6, alpha=a)
            if scene in SECTIONS:
                section(ctx, t, self.scenes[scene]["start"] + 0.2, *SECTIONS[scene], x=LEFT, y=226)
        getattr(self, scene)(ctx, t)
        vc.draw_transition(ctx, t, self.boundaries, W, H)
        if self.captions_on:
            vc.draw_caption(ctx, self.captions, t, 520, 1540, 46, 860)

    # ------------------------------------------------------------ hook
    def s_hook(self, ctx, t):
        l0, l1 = self.line("s_hook", 0), self.line("s_hook", 1)
        a, dy = rise(t, l0["start"])
        text(ctx, "Up to", LEFT, 360 + dy, SANS_BOLD, 60, INK, alpha=a)
        count = 1 + int(9 * ease_in_out(prog(t, phrase_time(l0, "ten years") - 0.3, 1.0)))
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
        text(ctx, "of tax relief?", LEFT, 940 + dy, SANS_BOLD, 64, INK, alpha=a)
        answers = [(phrase_time(l1, "For qualifying"), "Qualifying investments", "Potentially", "check"),
                   (phrase_time(l1, "For every"), "Every business", "No", "cross")]
        for k, (start, who, verdict, kind) in enumerate(answers):
            y = 1010 + k * 112
            ra, rdy = rise(t, start)
            if ra <= 0:
                continue
            rect(ctx, LEFT, y + rdy, 920, 92, WHITE, ra, radius=10)
            badge(ctx, LEFT + 50, y + 46 + rdy, 28, kind, prog(t, start + 0.1, 0.8))
            text(ctx, who, LEFT + 100, y + 58 + rdy, SANS_SEMI, 34, INK, alpha=ra)
            text(ctx, verdict, LEFT + 890, y + 64 + rdy, NUM, 50, CORAL if kind == "cross" else GREEN, "right", ra)

    # ------------------------------------------------------------ zone
    def s_zone(self, ctx, t):
        l0 = self.line("s_zone", 0)
        text_block(ctx, "One defined Historic Center, not the whole country", LEFT, 350, SANS_BOLD, 62, INK, 900,
                   1.12, p=prog(t, l0["start"], 1.2))
        plan = CityPlan(LEFT, 540, 920, 620, cols=6, rows=6, gap=9,
                        perimeter=((1, 1), (5, 1), (5, 3), (6, 3), (6, 5), (2, 5), (2, 4), (1, 4)))
        plan.draw(ctx, t_grid=prog(t, l0["start"], 1.2), t_fill=prog(t, phrase_time(l0, "San Salvador"), 1.4))
        la = ease_out(prog(t, phrase_time(l0, "defined Historic"), 0.5))
        if la > 0:
            pointer(ctx, LEFT, 1204, 20, CORAL, la)
            text(ctx, "Centro Histórico de San Salvador", LEFT + 32, 1222, SANS_SEMI, 34, INK, alpha=la)
            text(ctx, "Illustrative, not the legal map", LEFT + 32, 1264, ITAL, 30, GREY, alpha=la)

    # ------------------------------------------------------------ checks
    def s_checks(self, ctx, t):
        lines = [self.line("s_checks", i) for i in range(4)]
        a, dy = rise(t, lines[0]["start"])
        big_number(ctx, "3", LEFT - 6, 560 + dy, 300, INK, alpha=a)
        text(ctx, "checks", LEFT + 190, 470 + dy, SANS_BOLD, 64, INK, alpha=a)
        text(ctx, "verificaciones", LEFT + 190, 520 + dy, ITAL, 32, GREY, alpha=a)
        rows = [("Location", "Inside the defined perimeter"), ("Investment", "Eligible activity, above the minimum"),
                ("Approval", "Qualified by the Planning Authority")]
        for i, (title, sub) in enumerate(rows):
            y = 650 + i * 110
            appear = ease_out(prog(t, lines[0]["start"] + 0.15 + i * 0.12, 0.5))
            if appear <= 0:
                continue
            active = prog(t, lines[i + 1]["start"], 0.4)
            done = prog(t, lines[i + 1]["end"] - 0.4, 0.8)
            if done > 0:
                badge(ctx, LEFT + 34, y, 34, "check", done)
            else:
                marker(ctx, LEFT + 34, y, 34, i + 1, mix(RULE, CORAL, active), appear)
            text(ctx, title, LEFT + 92, y + 4, SANS_SEMI, 42, INK, alpha=appear * (0.45 + 0.55 * max(active, done)))
            text(ctx, sub, LEFT + 92, y + 44, ITAL, 29, GREY, alpha=appear)
        for k in range(3):
            start = lines[k + 1]["start"]
            p = prog(t, start, 0.55)
            if p <= 0:
                continue
            with wipe(ctx, LEFT - 10, 990, 940, 350, p, "right") as e:
                rect(ctx, LEFT - 10, 990, 940, 350, PAGE)
                if k == 0:
                    plan = CityPlan(LEFT, 1000, 920, 300, cols=5, rows=2, gap=9,
                                    perimeter=((0, 0), (3, 0), (3, 1), (2, 1), (2, 2), (0, 2)))
                    plan.draw(ctx, 1, 1, highlight={(1, 0): (GOLD, prog(t, start + 0.4, 0.4)),
                                                    (3, 1): (CORAL, prog(t, start + 0.8, 0.4))})
                    for (c, r), kind, d in (((1, 0), "check", 0.6), ((3, 1), "cross", 1.0)):
                        cx, cy = plan.block_center(c, r)
                        badge(ctx, cx, cy, 32, kind, prog(t, start + d, 0.8))
                elif k == 1:
                    cx = LEFT
                    for j, (label, dot) in enumerate((("Food", ORANGE), ("Lodging", BLUE), ("Culture", PURPLE),
                                                      ("Restoration", PINK))):
                        cx += pill(ctx, label, cx, 1010, WHITE, 28, alpha=ease_out(prog(t, start + j * 0.15, 0.4)),
                                   dot=dot) + 12
                    text(ctx, "Investment vs. minimum", LEFT, 1118, SANS_MED, 28, INK)
                    x0, x1, y = LEFT, LEFT + 900, 1200
                    line(ctx, [(x0, y), (x1, y)], INK, 1.6)
                    for j in range(46):
                        tx = x0 + (x1 - x0) * j / 45
                        line(ctx, [(tx, y), (tx, y - (16 if j % 5 == 0 else 8))], INK, 1.2)
                    fill = ease_out(prog(t, start + 0.5, 1.4)) * 0.8
                    rect(ctx, x0, y + 10, (x1 - x0) * fill, 40, BLUE)
                    mx = x0 + (x1 - x0) * 0.6
                    line(ctx, [(mx, y - 34), (mx, y + 60)], CORAL, 3.4)
                    text(ctx, "Minimum", mx + 12, y - 16, SANS_SEMI, 28, CORAL)
                else:
                    document(ctx, LEFT + 40, 1010, 200, 260, 6, prog(t, start, 0.8), rotate=-0.05)
                    stamp(ctx, LEFT + 250, 1220, 76, prog(t, start + 0.8, 0.8))
                    fade = ease_out(prog(t, start + 0.4, 0.5))
                    text(ctx, "APLAN", LEFT + 400, 1110, NUM, 84, INK, alpha=fade)
                    text(ctx, "Historic Center", LEFT + 400, 1164, SANS_MED, 32, INK, alpha=fade)
                    text(ctx, "Planning Authority", LEFT + 400, 1204, SANS_MED, 32, INK, alpha=fade)
                    text(ctx, "Ventanilla Única", LEFT + 400, 1246, ITAL, 30, GREY, alpha=fade)
            if 0 < e < 1:
                line(ctx, [(LEFT - 10 + 940 * e, 995), (LEFT - 10 + 940 * e, 1335)], CORAL, 2.4)

    # ------------------------------------------------------------ beneficiary
    def s_benef(self, ctx, t):
        l0 = self.line("s_benef", 0)
        a, dy = rise(t, l0["start"])
        text(ctx, "Who receives it?", LEFT, 350 + dy, SANS_BOLD, 76, INK, alpha=a)
        text(ctx, "¿Quién lo recibe?", LEFT, 400 + dy, ITAL, 34, GREY, alpha=a)
        resolve = phrase_time(l0, "A landlord")
        groups = [("Owner · landlord", "Propietario", INK, SKY, {"prop": "keys", "arms": "hold"}, "check"),
                  ("Operator · tenant", "Operador · inquilino", WHITE, PURPLE,
                   {"coat": True, "arms": "present", "hair_style": "bun"}, "cross"),
                  ("Developer", "Desarrollador", SKY, INK, {"hardhat": True, "arms": "point"}, "question")]
        for i, (title, spanish, top, bottom_c, pose, final) in enumerate(groups):
            y = 470 + i * 215
            start = l0["start"] + 0.3 + i * 0.25
            ra, rdy = rise(t, start)
            if ra <= 0:
                continue
            rect(ctx, LEFT, y + rdy, 920, 195, LIGHT, ra, radius=12)
            ctx.save()
            ctx.rectangle(LEFT, y + rdy, 920, 195)
            ctx.clip()
            person(ctx, LEFT + 100, y + 190 + rdy, 175, top, bottom_c, GOLD if i == 0 else CORAL, alpha=ra, **pose)
            ctx.restore()
            text(ctx, title, LEFT + 210, y + 92 + rdy, SANS_SEMI, 44, INK, alpha=ra)
            text(ctx, spanish, LEFT + 210, y + 136 + rdy, ITAL, 30, GREY, alpha=ra)
            kind = final if t > resolve + 0.25 * i else "question"
            bstart = start + 0.2 if kind == "question" else resolve + 0.25 * i
            badge(ctx, LEFT + 850, y + 97 + rdy, 36, kind, prog(t, bstart, 0.8))
        na, ndy = rise(t, phrase_time(l0, "automatically"))
        if na > 0:
            rect(ctx, LEFT, 1135 + ndy, 920, 180, CORAL, na, radius=12)
            text(ctx, "Landlord approved ≠", LEFT + 40, 1208 + ndy, SANS_BOLD, 50, WHITE, alpha=na)
            text(ctx, "tenant benefits automatically", LEFT + 40, 1270 + ndy, SANS, 44, WHITE, alpha=na)

    # ------------------------------------------------------------ close
    def s_close(self, ctx, t):
        s = self.scenes["s_close"]["start"]
        l0 = self.line("s_close", 0)
        a = ease_out(prog(t, s + 0.3, 0.6))
        wordmark(ctx, W / 2, 380, 120, color=WHITE, fill=ORANGE, alpha=a, align="center")
        text(ctx, "LATIN AMERICA EXPANSION", W / 2, 448, SANS_SEMI, 28, CORAL, "center", a, tracking=3)
        text(ctx, "Expansión en América Latina", W / 2, 490, ITAL, 28, SKY, "center", a)
        sp = prog(t, l0["start"] + 0.1, 0.6)
        if sp > 0:
            with pop(ctx, W / 2, 596, sp):
                pill(ctx, "Subscribe", W / 2, 560, ORANGE, 40, INK, SANS_BOLD, pad_x=56, align="center")
        text(ctx, "@ConAurora", W / 2, 706, SANS_MED, 38, WHITE, "center", alpha=rise(t, l0["start"] + 0.5)[0])
        np_ = prog(t, phrase_time(l0, "the next breakdown") - 0.2, 0.6)
        if np_ > 0:
            with wipe(ctx, LEFT, 770, 920, 560, np_, "up"):
                rect(ctx, LEFT, 770, 920, 560, PAGE, radius=14)
                na = ease_out(prog(t, phrase_time(l0, "the next breakdown"), 0.5))
                text(ctx, "NEXT BREAKDOWN", LEFT + 50, 836, SANS_SEMI, 26, CORAL, alpha=na, tracking=2)
                text_block(ctx, "Who actually gets the benefit: owner, operator, or developer?", LEFT + 50, 906,
                           SANS_BOLD, 52, INK, 820, 1.14, alpha=na)
                for k, (top, bottom_c, kw) in enumerate(((INK, SKY, {"prop": "keys", "arms": "hold"}),
                                                        (WHITE, PURPLE, {"coat": True, "hair_style": "bun"}),
                                                        (SKY, INK, {"hardhat": True, "arms": "point", "facing": -1}))):
                    fa = ease_out(prog(t, phrase_time(l0, ("owner", "operator", "developer")[k]), 0.5))
                    person(ctx, 300 + k * 240, 1290, 200, top, bottom_c, alpha=fa, **kw)


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
