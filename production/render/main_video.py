"""Aurora — 'El Salvador Tax Incentives: Who Qualifies for Up to 10 Years of Relief?' (1920x1080).

Flat 'facts & figures' editorial style. Every animation cue is keyed to the narration timeline
(script/main_timeline.json), so re-voicing the script re-times the film automatically.
"""
import argparse
import math
from pathlib import Path

from aurora_gfx import *  # noqa: F401,F403 - brand system and illustration toolkit
from aurora_gfx import QC
import video_core as vc

W, H = 1920, 1080
LEFT, RIGHT = 140, 1780
CAPTION_ZONE = (150, 912, 1770, 1040)

# ---- Hypothetical economics (illustrative only; not Salvadoran tax liability, not a promised return)
ASSUMED_ANNUAL_TAX_SAVINGS = 30_000
ADDITIONAL_AFTER_TAX_OCCUPANCY_COST = 24_000
REMAINING_ANNUAL_ADVANTAGE = ASSUMED_ANNUAL_TAX_SAVINGS - ADDITIONAL_AFTER_TAX_OCCUPANCY_COST
assert REMAINING_ANNUAL_ADVANTAGE == 6_000, "narration and on-screen arithmetic say $6,000"

SECTIONS = {  # scene id -> (English label, Spanish partner line)
    "hook": ("The question", "La pregunta"),
    "promise": ("In this film", "En este video"),
    "opportunity": ("The opportunity", "La oportunidad"),
    "checks": ("Three checks", "Tres verificaciones"),
    "beneficiary": ("Who benefits", "¿Quién se beneficia?"),
    "economics": ("The arithmetic", "La aritmética"),
    "execution": ("Execution", "Ejecución"),
}


def usd(value):
    return f"${value:,.0f}"


class MainFilm(vc.Film):
    width, height, video_id = W, H, "main"

    # ------------------------------------------------------------ helpers
    def line(self, scene, i):
        return self.scenes[scene]["lines"][i]

    def current_scene(self, t):
        scene = self.timeline["scenes"][0]
        for s in self.timeline["scenes"]:
            if t >= s["start"]:
                scene = s
        return scene["id"]

    def draw(self, ctx, t):
        QC.width, QC.height, QC.caption_zone = W, H, CAPTION_ZONE if self.captions_on else None
        scene = self.current_scene(t)
        dark = scene == "close" and t > self.scenes["close"]["start"] + 0.1
        set_color(ctx, INK if dark else PAGE)
        ctx.paint()
        if not dark:
            self.header(ctx, t, scene)
        getattr(self, f"scene_{scene}")(ctx, t)
        vc.draw_transition(ctx, t, self.boundaries, W, H)
        if self.captions_on:
            vc.draw_caption(ctx, self.captions, t, W / 2, 1032, 36, 1600)

    def header(self, ctx, t, scene):
        """Running header like a printed report: wordmark left, title + folio right, coral hairline."""
        a = ease_out(prog(t, 0.1, 0.6))
        wordmark(ctx, LEFT, 82, 28, alpha=a)
        index = [s["id"] for s in self.timeline["scenes"]].index(scene) + 1
        folio_w = text(ctx, f"{index:02d} | {len(self.timeline['scenes']):02d}", RIGHT, 82, NUM_MED, 24, INK, "right", a)
        text(ctx, "El Salvador Tax Incentives — 2026", RIGHT - folio_w - 28, 81, ITAL, 20, INK, "right", a)
        line(ctx, [(LEFT, 106), (LEFT + (RIGHT - LEFT) * ease_out(prog(t, 0.2, 1.2)), 106)], CORAL, 1.4, alpha=a)
        if scene in SECTIONS:
            section(ctx, t, self.scenes[scene]["start"] + 0.25, *SECTIONS[scene])

    # ------------------------------------------------------------ 1. hook
    def scene_hook(self, ctx, t):
        l0, l1 = self.line("hook", 0), self.line("hook", 1)
        a, dy = rise(t, l0["start"])
        bottom = text_block(ctx, "A tax incentive can improve your return.", LEFT, 360 + dy, SANS_BOLD, 64, INK, 700,
                            leading=1.14, alpha=a)
        a2, dy2 = rise(t, l1["start"])
        y2 = bottom + 130 + dy2
        text(ctx, "Can it fix a", LEFT, y2, SANS_BOLD, 64, INK, alpha=a2)
        text(ctx, "weak location?", LEFT, y2 + 74, SANS_BOLD, 64, CORAL, alpha=a2)
        text(ctx, "¿Puede un incentivo salvar una mala ubicación?", LEFT, y2 + 132, ITAL, 26, GREY, alpha=a2)
        # street: four facades rise; at "weak location" the street goes quiet around the one with the tag
        weak = ease_in_out(prog(t, phrase_time(l1, "weak location"), 1.2))
        ground = 800
        line(ctx, [(900, ground), (900 + 900 * ease_out(prog(t, 0.1, 0.8)), ground)], RULE, 3)
        buildings = [(930, 180, 300, PINK, "grid"), (1125, 150, 390, BLUE, "grid"),
                     (1290, 240, 270, GOLD, "colonial"), (1545, 190, 340, GREEN, "grid")]
        for k, (bx, bw, bh, color, style) in enumerate(buildings):
            facade(ctx, bx, ground, bw, bh, color, style, prog(t, 0.15 + k * 0.18, 0.7), dim=0 if k == 2 else weak * 0.85)
        lamp(ctx, 1110, ground, 120)
        tree(ctx, 1760, ground, 110)
        for k, (start_x, speed, top, bottom_c) in enumerate(((930, 120, CORAL, INK), (1790, -105, SKY, PURPLE))):
            walk_t = t - 0.8 - k * 0.3
            if walk_t > 0:
                x = start_x + speed * walk_t + (1 if speed > 0 else -1) * 1000 * weak ** 2
                if 880 < x < 1840:
                    person(ctx, x, ground, 190, top, bottom_c, walk=walk_t * 7, facing=1 if speed > 0 else -1,
                           hair_style="bun" if k else "short")
        tag = prog(t, phrase_time(l0, "tax incentive"), 0.9)
        if tag > 0:
            swing = math.sin((t - l0["start"]) * 3.1) * 0.1 * math.exp(-(t - l0["start"]) * 0.6)
            ctx.save()
            ctx.rectangle(880, 130, 940, 700)
            ctx.clip()
            ctx.translate(1410, 130)
            ctx.rotate(swing)
            drop = lerp(-230, 0, ease_back(tag, 1.1))
            line(ctx, [(0, 0), (0, 250 + drop)], INK, 1.6)
            pill(ctx, "Tax incentive", 0, 250 + drop, CORAL, 24, WHITE, SANS_SEMI, align="center")
            ctx.restore()

    # ------------------------------------------------------------ 2. promise
    def scene_promise(self, ctx, t):
        s = self.scenes["promise"]["start"]
        ln = self.line("promise", 0)
        a, dy = rise(t, s + 0.3)
        text(ctx, "El Salvador Tax Incentives", LEFT, 330 + dy, SANS_BOLD, 76, INK, alpha=a)
        a2, dy2 = rise(t, s + 0.6)
        text(ctx, "Who qualifies for up to 10 years of relief?", LEFT, 392 + dy2, ITAL, 40, INK, alpha=a2)
        items = [("which incentive applies", "Which incentive applies", "¿Qué incentivo aplica?"),
                 ("who receives the benefit", "Who receives the benefit", "¿Quién recibe el beneficio?"),
                 ("what remains", "What remains after location and execution costs", "¿Qué queda después de los costos?")]
        for i, (phrase, label, spanish) in enumerate(items):
            start = phrase_time(ln, phrase) - 0.2
            x = LEFT + i * 560
            na, ndy = rise(t, start)
            if na <= 0:
                continue
            big_number(ctx, f"0{i + 1}", x, 640 + ndy, 150, INK, alpha=na)
            ip = prog(t, start + 0.15, 0.8)
            base = 650
            if i == 0:
                document(ctx, x + 250, 470, 120, 160, 5, ip, rotate=0.06)
                stamp(ctx, x + 360, 610, 42, prog(t, start + 0.8, 0.7))
            elif i == 1:
                for k, (top, bottom_c, kw) in enumerate(((GOLD, INK, {"prop": "keys", "arms": "hold"}),
                                                        (WHITE, BLUE, {"coat": True}),
                                                        (SKY, PURPLE, {"hardhat": True, "arms": "point", "facing": -1}))):
                    person(ctx, x + 230 + k * 95, base, 190, top, bottom_c,
                           alpha=ease_out(prog(t, start + 0.25 + k * 0.15, 0.4)), **kw)
            else:
                bars = [(x + 230, 150, BLUE, 0), (x + 310, 120, CORAL, 150), (x + 390, 30, ORANGE, 0)]
                for k, (bx, bh, color, hang) in enumerate(bars):
                    bp = ease_out(prog(t, start + 0.25 + k * 0.2, 0.6))
                    if hang:
                        rect(ctx, bx, base - hang, 60, bh * bp, color)
                    else:
                        rect(ctx, bx, base - bh * bp, 60, bh * bp, color)
            line(ctx, [(x, 686), (x + 480 * ease_out(prog(t, start + 0.1, 0.6)), 686)], CORAL, 1.4)
            pair(ctx, label, spanish, x, 734, 30, SANS_SEMI, alpha=ease_out(prog(t, start + 0.2, 0.5)), max_width=470)

    # ------------------------------------------------------------ 3. opportunity
    def scene_opportunity(self, ctx, t):
        l0, l1, l2 = (self.line("opportunity", i) for i in range(3))
        ten = phrase_time(l0, "up to ten years")
        # the hero numeral counts up to 10 as "up to ten years" is spoken
        count = 1 + int(9 * ease_in_out(prog(t, ten - 0.5, 1.4)))
        na, ndy = rise(t, l0["start"])
        size, baseline = 330, 630
        ten_w = text_width(ctx, "10", NUM, size)
        big_number(ctx, str(count), LEFT - 8, baseline + ndy, size, INK, alpha=na)
        text(ctx, "years", LEFT + ten_w + 10, baseline + ndy, NUM_MED, 100, INK, alpha=na)
        # a reader sits on top of the "0"
        font(ctx, NUM, size)
        zero = ctx.text_extents("0")
        seat_x = LEFT - 8 + text_width(ctx, "1", NUM, size) + zero.x_bearing + zero.width * 0.3
        person(ctx, seat_x, baseline + zero.y_bearing + ndy, 150, WHITE, BLUE, CORAL, seated=True, arms="hold",
               prop="document", coat=True, alpha=ease_out(prog(t, ten + 0.8, 0.5)))
        # ruler ticks: one coral dot per year
        ruler = 666
        for year in range(10):
            yp = ease_out(prog(t, ten - 0.4 + year * 0.14, 0.3))
            x = LEFT + year * 62
            line(ctx, [(x, ruler), (x, ruler - 16 * yp)], CORAL, 2)
            disc(ctx, x, ruler - 6 - 16 * yp, 5 * yp, CORAL)
        line(ctx, [(LEFT, ruler), (LEFT + 9 * 62 * ease_out(prog(t, ten - 0.4, 1.5)), ruler)], CORAL, 1.4)
        swap = ease_in_out(prog(t, l2["start"], 0.5))
        da = ease_out(prog(t, phrase_time(l0, "qualifying new"), 0.6)) * (1 - swap)
        if da > 0:
            pair(ctx, "of income-tax relief, at most, for qualifying new investments in the defined Historic Center.",
                 "Exención del Impuesto sobre la Renta hasta por 10 años.", LEFT, 728, 27, SANS, da, max_width=640)
        if swap > 0:
            text(ctx, "Not every business qualifies.", LEFT, 744, SANS_BOLD, 38, CORAL, alpha=swap)
            text_block(ctx, "Verify current law and regulation before underwriting.", LEFT, 792, SANS, 27, INK, 640, alpha=swap)
        # the defined zone
        plan = CityPlan(900, 180, 880, 500)
        plan.draw(ctx, t_grid=prog(t, l0["start"] + 0.1, 1.4), t_fill=prog(t, phrase_time(l0, "defined Historic"), 1.4))
        la = ease_out(prog(t, phrase_time(l0, "defined Historic") + 0.8, 0.5))
        if la > 0:
            pointer(ctx, 900, 712, 16, CORAL, la)
            text(ctx, "Centro Histórico de San Salvador", 926, 726, SANS_SEMI, 24, INK, alpha=la)
            text(ctx, "Defined perimeter — illustrative, not the legal map", 926, 756, ITAL, 22, GREY, alpha=la)
        ra = ease_out(prog(t, phrase_time(l1, "separate from"), 0.5))
        if ra > 0:
            text(ctx, "Separate nationwide regimes, separate rules:", 900, 812, SANS_MED, 22, INK, alpha=ra)
            cx = 900
            for k, (label, dot) in enumerate((("Tourism", BLUE), ("Free zones", GREEN), ("International services", PURPLE))):
                ka = ease_out(prog(t, phrase_time(l1, "nationwide") + k * 0.18, 0.4))
                cx += pill(ctx, label, cx, 830, LIGHT, 21, alpha=ka, dot=dot) + 10
        for k, ((c, r), kind) in enumerate((((2, 2), "check"), ((5, 3), "check"), ((6, 4), "cross"), ((4, 1), "question"))):
            cx, cy = plan.block_center(c, r)
            badge(ctx, cx, cy, 24, kind, prog(t, l2["start"] + 0.2 + k * 0.35, 0.9))

    # ------------------------------------------------------------ 4. three checks
    def scene_checks(self, ctx, t):
        lines = [self.line("checks", i) for i in range(4)]
        a, dy = rise(t, lines[0]["start"])
        big_number(ctx, "3", LEFT - 6, 560 + dy, 330, INK, alpha=a)
        text_block(ctx, "checks before you model any benefit", LEFT + 190, 400 + dy, SANS_BOLD, 40, INK, 470, 1.15, alpha=a)
        text(ctx, "verificaciones antes de modelar", LEFT + 190, 520 + dy, ITAL, 24, GREY, alpha=a)
        rows = [("Exact location", "Inside the defined perimeter"),
                ("Qualifying investment", "Eligible activity, above the minimum"),
                ("Approval", "Qualified by the Planning Authority (APLAN)")]
        for i, (title, sub) in enumerate(rows):
            y = 640 + i * 88
            appear = ease_out(prog(t, lines[0]["start"] + 0.2 + i * 0.15, 0.5))
            if appear <= 0:
                continue
            active = prog(t, lines[i + 1]["start"], 0.4)
            done = prog(t, lines[i + 1]["end"] - 0.5, 0.8)
            if done > 0:
                badge(ctx, LEFT + 26, y, 26, "check", done)
            else:
                marker(ctx, LEFT + 26, y, 26, i + 1, mix(RULE, CORAL, active), appear)
            text(ctx, title, LEFT + 70, y + 2, SANS_SEMI, 30, INK, alpha=appear * (0.45 + 0.55 * max(active, done)))
            text(ctx, sub, LEFT + 70, y + 36, ITAL, 23, GREY, alpha=appear)
        # right: one illustration per check, each wiping over the last behind a coral rule
        starts = [lines[1]["start"] - 1.2, lines[2]["start"], lines[3]["start"]]
        drawers = [self._check_location, self._check_investment, self._check_approval]
        for k in range(3):
            p = prog(t, starts[k], 0.6)
            if p <= 0:
                continue
            with wipe(ctx, 860, 140, 960, 765, p, "right") as e:
                rect(ctx, 860, 140, 960, 765, PAGE)
                drawers[k](ctx, t, lines)
            if 0 < e < 1:
                line(ctx, [(860 + 960 * e, 150), (860 + 960 * e, 890)], CORAL, 2)

    def _check_location(self, ctx, t, lines):
        l1 = lines[1]
        plan = CityPlan(900, 190, 880, 520, cols=5, rows=4, gap=10,
                        perimeter=((0, 0), (3, 0), (3, 2), (2, 2), (2, 4), (0, 4)))
        inside_t, outside_t = phrase_time(l1, "inside the defined"), phrase_time(l1, "One block outside")
        plan.draw(ctx, t_grid=prog(t, l1["start"] - 1.2, 1.0), t_fill=prog(t, l1["start"] - 0.6, 1.0),
                  highlight={(1, 1): (GOLD, prog(t, inside_t, 0.5)), (3, 1): (CORAL, prog(t, outside_t, 0.5))})
        for (c, r), kind, start in (((1, 1), "check", inside_t), ((3, 1), "cross", outside_t)):
            cx, cy = plan.block_center(c, r)
            badge(ctx, cx, cy, 34, kind, prog(t, start + 0.3, 0.9))
        la, lb = ease_out(prog(t, inside_t, 0.5)), ease_out(prog(t, outside_t, 0.5))
        if la > 0:
            pill(ctx, "Inside the perimeter", 900, 752, LIGHT, 23, alpha=la, dot=GOLD)
            text(ctx, "Orange = defined zone (illustrative)", 900, 846, ITAL, 22, GREY, alpha=la)
        if lb > 0:
            pill(ctx, "One block outside", 1190, 752, LIGHT, 23, alpha=lb, dot=CORAL)

    def _check_investment(self, ctx, t, lines):
        l2 = lines[2]
        start = l2["start"]
        ground = 600
        line(ctx, [(900, ground), (1780, ground)], RULE, 3)
        facade(ctx, 950, ground, 330, 290, PINK, "colonial", prog(t, start, 0.8))
        scaffold(ctx, 930, ground, 370, 300, prog(t, start + 0.6, 1.4))
        crane(ctx, 1440, ground, 330, prog(t, start + 0.3, 1.6), hook=0.5 + 0.12 * math.sin(t * 1.6))
        person(ctx, 1360, ground, 190, SKY, INK, hardhat=True, arms="point", facing=1,
               alpha=ease_out(prog(t, start + 1.0, 0.5)))
        chips = [("Food", "food", ORANGE), ("Lodging", "lodging", BLUE), ("Culture", "lodging", PURPLE),
                 ("Housing", "lodging", GREEN), ("Restoration", "restoration", PINK)]
        cx = 900
        for k, (label, cue, dot) in enumerate(chips):
            ca = ease_out(prog(t, phrase_time(l2, cue) + (0.2 * (k - 1) if cue == "lodging" else 0), 0.45))
            cx += pill(ctx, label, cx, 630, LIGHT, 22, alpha=ca, dot=dot) + 10
        # tape-measure threshold: investment bar grows past the coral "minimum" tick
        th = phrase_time(l2, "above the minimum")
        ta = ease_out(prog(t, th - 1.2, 0.5))
        if ta > 0:
            text(ctx, "Investment vs. minimum threshold", 900, 736, SANS_MED, 22, INK, alpha=ta)
            x0, x1, y = 900, 1760, 800
            line(ctx, [(x0, y), (x1, y)], INK, 1.4, alpha=ta)
            for k in range(0, 87):
                tx = x0 + (x1 - x0) * k / 86
                line(ctx, [(tx, y), (tx, y - (12 if k % 10 == 0 else 6))], INK, 1, alpha=ta)
            fill = ease_out(prog(t, th - 0.6, 1.4)) * 0.8
            rect(ctx, x0, y + 8, (x1 - x0) * fill, 26, BLUE)
            mx = x0 + (x1 - x0) * 0.6
            line(ctx, [(mx, y - 26), (mx, y + 44)], CORAL, 3, alpha=ta)
            text(ctx, "Minimum", mx + 10, y - 12, SANS_SEMI, 21, CORAL, alpha=ta)
            if fill >= 0.6:
                badge(ctx, x0 + (x1 - x0) * fill + 24, y + 21, 18, "check", prog(t, th + 0.3, 0.8))

    def _check_approval(self, ctx, t, lines):
        l3 = lines[3]
        start = l3["start"]
        sa = ease_out(prog(t, start + 0.2, 0.5))
        text(ctx, "APLAN · Ventanilla Única", 1340, 212, SANS_SEMI, 28, INK, "center", alpha=sa)
        text(ctx, "Historic Center Planning Authority · single window", 1340, 246, ITAL, 22, GREY, "center", alpha=sa)
        line(ctx, [(1100, 266), (1100 + 480 * sa, 266)], CORAL, 1.4)
        person(ctx, 1640, 760, 330, WHITE, BLUE, coat=True, arms="hold", facing=-1, hair_style="bun",
               alpha=ease_out(prog(t, start + 0.3, 0.5)))
        walk_in = ease_out(prog(t, start + 0.1, 1.4))
        person(ctx, lerp(900, 1060, walk_in), 820, 360, PURPLE, INK, GOLD, walk=(t - start) * 7 * (1 - walk_in),
               arms="hold", prop="folder", facing=1)
        rect(ctx, 1260, 580, 520, 240, LIGHT)
        rect(ctx, 1240, 566, 560, 22, mix(LIGHT, INK, 0.2))
        qualify = phrase_time(l3, "must qualify")
        dp = ease_out(prog(t, qualify - 0.6, 0.8))
        if dp > 0:
            dx, dy = lerp(1120, 1330, dp), lerp(470, 320, dp)
            document(ctx, dx, dy, 150, 196, 5, 1, rotate=lerp(-0.2, -0.05, dp))
            stamp(ctx, dx + 150, dy + 170, 54, prog(t, phrase_time(l3, "the project") + 0.1, 0.8))
        na = ease_out(prog(t, phrase_time(l3, "No approval"), 0.5))
        if na > 0:
            text(ctx, "No approval, no benefit to model.", 1520, 872, SANS_BOLD, 32, CORAL, "center", alpha=na)

    # ------------------------------------------------------------ 5. beneficiary
    def scene_beneficiary(self, ctx, t):
        l0, l1, l2 = (self.line("beneficiary", i) for i in range(3))
        a, dy = rise(t, l0["start"])
        text(ctx, "Which entity receives the benefit?", LEFT, 318 + dy, SANS_BOLD, 58, INK, alpha=a)
        text(ctx, "¿Qué entidad recibe el beneficio?", LEFT, 364 + dy, ITAL, 28, GREY, alpha=a)
        tp = prog(t, phrase_time(l0, "receives"), 0.6)
        if tp > 0:
            with pop(ctx, W / 2, 432, tp):
                pill(ctx, "Qualified benefit", W / 2, 410, GOLD, 24, INK, SANS_SEMI, align="center")
        groups = [("Owner · landlord", "Propietario", "Owner", 420),
                  ("Operator · tenant", "Operador · inquilino", "operator", 960),
                  ("Developer", "Desarrollador", "developer", 1500)]
        resolve = l2["start"]
        base = 800
        for i, (title, spanish, cue, cx) in enumerate(groups):
            start = phrase_time(l1, cue)
            lp = prog(t, start - 0.3, 0.8)
            if lp > 0:
                solid = i == 0 and t > resolve + 0.4
                pts = partial_polyline([(W / 2, 454), (W / 2, 476), (cx, 476), (cx, 500)], lp)
                line(ctx, pts, CORAL, 2, dash=None if solid else [8, 7])
            gp = prog(t, start, 0.7)
            if gp <= 0:
                continue
            if i == 0:
                facade(ctx, cx - 210, base, 220, 250, PINK, "colonial", gp)
                person(ctx, cx + 100, base, 290, INK, SKY, GOLD, arms="hold", prop="keys", facing=-1,
                       alpha=ease_out(prog(t, start + 0.3, 0.5)))
            elif i == 1:
                storefront(ctx, cx - 220, base, 230, 230, BLUE, ORANGE, gp)
                person(ctx, cx + 90, base, 290, WHITE, PURPLE, CORAL, coat=True, arms="present", facing=-1,
                       hair_style="bun", alpha=ease_out(prog(t, start + 0.3, 0.5)))
            else:
                crane(ctx, cx - 160, base, 260, gp, hook=0.5 + 0.15 * math.sin(t * 1.7))
                person(ctx, cx + 110, base, 290, SKY, INK, GOLD, hardhat=True, arms="point", facing=-1,
                       alpha=ease_out(prog(t, start + 0.3, 0.5)))
            la = ease_out(prog(t, start + 0.3, 0.5))
            text(ctx, title, cx, 846, SANS_SEMI, 30, INK, "center", alpha=la)
            text(ctx, spanish, cx, 880, ITAL, 23, GREY, "center", alpha=la)
            kind = "question"
            if t > resolve + 0.4 and i == 0:
                kind = "check"
            elif t > resolve + 0.9 and i == 1:
                kind = "cross"
            bstart = start + 0.2 if kind == "question" else resolve + (0.4 if i == 0 else 0.9)
            badge(ctx, cx, 500, 22, kind, prog(t, bstart, 0.8))
        na = ease_out(prog(t, phrase_time(l2, "automatically"), 0.5))
        if na > 0:
            label = "Landlord qualified ≠ tenant benefits automatically"
            width = text_width(ctx, label, SANS_SEMI, 23) + 36
            pill(ctx, label, RIGHT - width, 150, CORAL, 23, WHITE, SANS_SEMI, alpha=na)

    # ------------------------------------------------------------ 6. economics
    def scene_economics(self, ctx, t):
        l0, l1, l2 = (self.line("economics", i) for i in range(3))
        a, dy = rise(t, l0["start"])
        pointer(ctx, LEFT, 290 + dy, 16, CORAL, a)
        text(ctx, "Simplified hypothetical · annual, after tax", LEFT + 26, 304 + dy, SANS_SEMI, 26, INK, alpha=a)
        text(ctx, "Hipotético simplificado · anual, después de impuestos", LEFT + 26, 336 + dy, ITAL, 22, GREY, alpha=a)
        t_save, t_minus, t_leaves = (phrase_time(l1, p) for p in ("Thirty", "minus", "leaves"))
        rows = [(t_save, 470, "", ASSUMED_ANNUAL_TAX_SAVINGS, BLUE, "Assumed tax savings"),
                (t_minus, 610, "−", ADDITIONAL_AFTER_TAX_OCCUPANCY_COST, CORAL, "Additional after-tax occupancy costs")]
        for start, y, sign, value, color, label in rows:
            ra, rdy = rise(t, start)
            if ra <= 0:
                continue
            shown = round(value * ease_out(prog(t, start, 1.1)) / 100) * 100
            big_number(ctx, f"{sign}{usd(shown)}", LEFT, y + rdy, 100, INK, alpha=ra)
            rect(ctx, LEFT, y + 22 + rdy, 16, 16, color, ra)
            text(ctx, label, LEFT + 28, y + 38 + rdy, SANS, 24, INK, alpha=ra)
        rule = ease_out(prog(t, t_leaves - 0.3, 0.6))
        line(ctx, [(LEFT, 680), (LEFT + 620 * rule, 680)], CORAL, 2.4)
        ra, rdy = rise(t, t_leaves)
        if ra > 0:
            shown = round(REMAINING_ANNUAL_ADVANTAGE * ease_out(prog(t, t_leaves, 0.9)) / 100) * 100
            big_number(ctx, f"= {usd(shown)}", LEFT, 800 + rdy, 124, INK, alpha=ra)
            rect(ctx, LEFT, 818 + rdy, 16, 16, ORANGE, ra)
            text(ctx, "Remaining annual advantage", LEFT + 28, 834 + rdy, SANS_SEMI, 24, INK, alpha=ra)
        # waterfall chart (flat bars, hairline grid, direct labels)
        base, scale = 620, 12.0 / 1000
        ca = ease_out(prog(t, l0["start"] + 0.4, 0.6))
        for g in (0, 10_000, 20_000, 30_000):
            gy = base - g * scale
            line(ctx, partial_polyline([(1000, gy), (1780, gy)], ca), INK if g == 0 else RULE, 1.4)
            text(ctx, f"${g // 1000}k" if g else "$0", 988, gy + 8, NUM_MED, 22, GREY, "right", alpha=ca)
        bars = [(1040, t_save, 0, ASSUMED_ANNUAL_TAX_SAVINGS, BLUE, "Assumed tax savings"),
                (1300, t_minus, REMAINING_ANNUAL_ADVANTAGE, ASSUMED_ANNUAL_TAX_SAVINGS, CORAL, "Added occupancy cost, after tax"),
                (1560, t_leaves, 0, REMAINING_ANNUAL_ADVANTAGE, ORANGE, "Remaining advantage")]
        for k, (bx, start, low, high, color, label) in enumerate(bars):
            bp = ease_out(prog(t, start, 1.0))
            if bp <= 0:
                continue
            y_low, y_high = base - low * scale, base - high * scale
            y0, y1 = (y_high, y_high + (y_low - y_high) * bp) if k == 1 else (y_low - (y_low - y_high) * bp, y_low)
            rect(ctx, bx, y0, 190, y1 - y0, color)
            va = ease_out(prog(t, start + 0.6, 0.4))
            value = ("−" if k == 1 else "") + usd(high - low)
            if k == 1:
                text(ctx, value, bx + 95, (y0 + y1) / 2 + 14, NUM, 40, WHITE, "center", alpha=va)
            else:
                text(ctx, value, bx + 95, y0 - 14, NUM, 40, INK, "center", alpha=va)
            text_block(ctx, label, bx + 95, base + 34, SANS, 20, GREY, 200, 1.2, "center", alpha=va)
            if k > 0:
                level = base - (ASSUMED_ANNUAL_TAX_SAVINGS if k == 1 else REMAINING_ANNUAL_ADVANTAGE) * scale
                line(ctx, partial_polyline([(bx - 70, level), (bx, level)], bp), INK, 1.4, dash=[5, 5])
        f1 = ease_out(prog(t, l2["start"], 0.6))
        if f1 > 0:
            badge(ctx, 1772, base - REMAINING_ANNUAL_ADVANTAGE * scale - 26, 16, "question", prog(t, l2["start"] + 0.2, 0.8))
            pointer(ctx, 1000, 772, 16, CORAL, f1)
            text(ctx, "Excludes other cost, timing, and risk differences.", 1026, 786, SANS_MED, 24, INK, alpha=f1)
            text(ctx, "Not a calculation of Salvadoran tax liability.", 1026, 822, ITAL, 23, GREY,
                 alpha=ease_out(prog(t, phrase_time(l2, "It's not"), 0.5)))
            text(ctx, "Not a promised return.", 1026, 854, ITAL, 23, GREY,
                 alpha=ease_out(prog(t, phrase_time(l2, "It's not") + 0.4, 0.5)))

    # ------------------------------------------------------------ 7. execution
    def scene_execution(self, ctx, t):
        l0, l1 = self.line("execution", 0), self.line("execution", 1)
        swap = l1["start"]
        if t < swap + 0.7:
            self._execution_risks(ctx, t, l0)
        if t >= swap:
            with wipe(ctx, 0, 130, W, 770, prog(t, swap, 0.6), "right") as e:
                rect(ctx, 0, 130, W, 770, PAGE)
                self._execution_layers(ctx, t, l1)
            if 0 < e < 1:
                line(ctx, [(W * e, 140), (W * e, 890)], CORAL, 2)

    def _execution_risks(self, ctx, t, l0):
        a, dy = rise(t, l0["start"])
        text(ctx, "Execution still decides the outcome", LEFT, 330 + dy, SANS_BOLD, 54, INK, alpha=a)
        items = [("Demand", "Demanda", "demand"), ("Permits", "Permisos", "permits"),
                 ("Utilities", "Servicios", "utilities"), ("Opening delays", "Retrasos de apertura", "opening delays")]
        for i, (label, spanish, cue) in enumerate(items):
            start = phrase_time(l0, cue) - 0.1
            x = LEFT + i * 420
            ip = prog(t, start, 0.8)
            if ip <= 0:
                continue
            base = 650
            if i == 0:
                storefront(ctx, x, base, 170, 190, GREEN, ORANGE, ip)
                for k in range(2):
                    wx = x + 370 - ((t - start) * 55 + k * 110) % 220
                    person(ctx, wx, base, 170, (GOLD, SKY)[k], (INK, PURPLE)[k], walk=(t - start) * 7 + k, facing=-1,
                           hair_style="bun" if k else "short", alpha=ease_out(prog(t, start + 0.3, 0.4)))
            elif i == 1:
                for k in range(3):
                    document(ctx, x + 60 + k * 36, 440 + k * 22, 140, 180, 4, ip, rotate=-0.08 + k * 0.06)
                badge(ctx, x + 270, 610, 30, "question", prog(t, start + 0.7, 0.8))
            elif i == 2:
                facade(ctx, x + 200, base, 150, 170, BLUE, "grid", ip)
                utility_pole(ctx, x + 70, base, 230, ip, math.sin(t * 2))
            else:
                calendar(ctx, x + 60, 450, 200, 190, crossed=clamp((t - start - 0.3) / 3.2))
            na = ease_out(prog(t, start + 0.2, 0.5))
            big_number(ctx, f"0{i + 1}", x, 736, 56, INK, alpha=na)
            text(ctx, label, x + 72, 718, SANS_SEMI, 27, INK, alpha=na)
            text(ctx, spanish, x + 72, 748, ITAL, 22, GREY, alpha=na)
        erase = phrase_time(l0, "erase")
        ea = ease_out(prog(t, erase - 0.5, 0.5))
        if ea > 0:
            text(ctx, "Remaining advantage (hypothetical)", LEFT, 806, ITAL, 22, GREY, alpha=ea)
            full = 700
            remaining = lerp(full, 140, ease_in_out(prog(t, erase, 1.6)))
            rect(ctx, LEFT, 824, remaining, 34, ORANGE, ea)
            if remaining < full - 2:
                ctx.rectangle(LEFT + remaining, 824, full - remaining, 34)
                set_color(ctx, CORAL, ea)
                ctx.set_line_width(1.6)
                ctx.set_dash([7, 6])
                ctx.stroke()
                ctx.set_dash([])

    def _execution_layers(self, ctx, t, l1):
        a, dy = rise(t, l1["start"] + 0.2)
        text(ctx, "Underwrite in two layers", LEFT, 330 + dy, SANS_BOLD, 54, INK, alpha=a)
        columns = [(LEFT, "1 · Base case", "No incentives assumed. It must work on its own.", l1["start"] + 0.3, False),
                   (1000, "2 · Qualified benefit", "Shown separately, only if approved.",
                    phrase_time(l1, "show the qualified"), True)]
        for x, title, sub, start, benefit in columns:
            ca, cdy = rise(t, start)
            if ca <= 0:
                continue
            text(ctx, title, x, 420 + cdy, SANS_SEMI, 36, INK, alpha=ca)
            text(ctx, sub, x, 458 + cdy, ITAL, 24, GREY, alpha=ca)
            base = 820
            line(ctx, [(x, base), (x + 700 * ease_out(prog(t, start + 0.1, 0.6)), base)], INK, 1.4)
            heights = [70, 75, 78, 80, 82] if benefit else [230, 250, 262, 272, 280]
            for k, bh in enumerate(heights):
                bp = ease_out(prog(t, start + 0.3 + k * 0.1, 0.6))
                if bp <= 0:
                    continue
                bx = x + 40 + k * 132
                rect(ctx, bx, base - bh * bp, 92, bh * bp, ORANGE if benefit else INK)
                if benefit:  # awning-style stripes mark it as conditional
                    ctx.save()
                    ctx.rectangle(bx, base - bh * bp, 92, bh * bp)
                    ctx.clip()
                    for s in range(-4, 12):
                        sx = bx + s * 22
                        poly(ctx, [(sx, base), (sx + 9, base), (sx + 99, base - 90), (sx + 90, base - 90)], WHITE, 0.4)
                    ctx.restore()
                text(ctx, f"Yr {k + 1}", bx + 46, base + 30, NUM_MED, 22, GREY, "center", alpha=bp)
            if benefit:
                pill(ctx, "Subject to approval", x, 500, CORAL, 21, WHITE, SANS_SEMI, alpha=ca)
                stamp(ctx, x + 600, 620, 58, prog(t, start + 1.2, 0.8))

    # ------------------------------------------------------------ 8. close
    def scene_close(self, ctx, t):
        s = self.scenes["close"]["start"]
        l0, l1 = self.line("close", 0), self.line("close", 1)
        a = ease_out(prog(t, s + 0.3, 0.7))
        ctx.save()
        ctx.translate(0, (1 - a) * 20)
        wordmark(ctx, W / 2, 290, 116, color=WHITE, fill=ORANGE, alpha=a, align="center")
        ctx.restore()
        text(ctx, "LATIN AMERICA EXPANSION", W / 2, 352, SANS_SEMI, 24, CORAL, "center", a, tracking=3)
        text(ctx, "Expansión en América Latina", W / 2, 386, ITAL, 22, SKY, "center", a)
        ba, bdy = rise(t, phrase_time(l0, "illustrated"))
        text(ctx, "Illustrated breakdowns of incentives, locations, and the real cost to open.", W / 2, 452 + bdy,
             SANS, 30, WHITE, "center", alpha=ba)
        sp = prog(t, l0["start"], 0.6)
        if sp > 0:
            with pop(ctx, W / 2, 536, sp):
                pill(ctx, "Subscribe", W / 2, 504, ORANGE, 32, INK, SANS_BOLD, pad_x=48, align="center")
        ha, _ = rise(t, l0["start"] + 0.6)
        text(ctx, "@ConAurora  ·  conaurora.com", W / 2, 628, SANS_MED, 28, WHITE, "center", alpha=ha)
        np_ = prog(t, l1["start"] - 0.1, 0.6)
        if np_ > 0:
            with wipe(ctx, 380, 676, 1160, 210, np_, "up"):
                rect(ctx, 380, 676, 1160, 210, PAGE, radius=10)
                na = ease_out(prog(t, l1["start"] + 0.2, 0.5))
                text(ctx, "NEXT EPISODE", 420, 724, SANS_SEMI, 20, CORAL, alpha=na, tracking=2)
                text_block(ctx, "Who receives the benefit: the owner, operator, or developer?", 420, 778, SANS_BOLD, 36,
                           INK, 700, 1.15, alpha=na)
                for k, (top, bottom_c, kw) in enumerate(((INK, SKY, {"prop": "keys", "arms": "hold"}),
                                                        (WHITE, PURPLE, {"coat": True, "hair_style": "bun"}),
                                                        (SKY, INK, {"hardhat": True, "arms": "point", "facing": -1}))):
                    fa = ease_out(prog(t, phrase_time(l1, ("owner", "operator", "developer")[k]), 0.5))
                    person(ctx, 1230 + k * 105, 872, 170, top, bottom_c, alpha=fa, **kw)


def main():
    parser = argparse.ArgumentParser(description="Render the Aurora main film.")
    parser.add_argument("--out", default=str(vc.PRODUCTION.parent / "deliverables"))
    parser.add_argument("--stills", nargs="*", type=float, help="render PNG stills at these times instead of video")
    parser.add_argument("--clean", action="store_true", help="render without burned-in captions")
    parser.add_argument("--svg", action="store_true", help="export editable SVG keyframes per scene")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--qc-only", action="store_true", help="run per-frame text QC without encoding")
    args = parser.parse_args()
    film = MainFilm(captions_on=not args.clean)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    stem = "Aurora_ElSalvador_TaxIncentives_YouTube_1920x1080" + ("_clean" if args.clean else "")
    if args.stills:
        for time in args.stills:
            for issue in vc.still(film, time, out / f"main_{time:06.2f}.png"):
                print(f"{time:6.2f}s  {issue}")
        return
    if args.qc_only:
        count, issues = vc.qc_pass(film, stem, args.workers)
        print(f"{stem}: {len(issues)} of {count} frames flagged")
        return
    if args.svg:
        for scene in film.timeline["scenes"]:
            keyframe = max(ln["end"] for ln in scene["lines"]) - 0.1
            vc.svg_frame(film, keyframe, out / f"main_{scene['id']}_keyframe.svg")
        return
    master = vc.PRODUCTION / "audio" / "main_narration_master.wav"
    vc.master_audio(vc.PRODUCTION / "audio" / "main_narration.wav", master)
    issues = vc.render(film, out / f"{stem}.mp4", master, workers=args.workers)
    print(f"rendered {out / stem}.mp4; QC issues on {len(issues)} frames")
    for index, problems in issues[:40]:
        print(f"{index / vc.FPS:7.2f}s  " + " | ".join(sorted(set(problems))))


if __name__ == "__main__":
    main()
