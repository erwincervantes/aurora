"""Aurora — 'El Salvador Tax Incentives: Who Qualifies for Up to 10 Years of Relief?' (1920x1080).

Every animation cue is keyed to the narration timeline (script/main_timeline.json), so re-voicing
the script re-times the film automatically.
"""
import argparse
import math
from pathlib import Path

import cairo

from aurora_gfx import *  # noqa: F401,F403 - brand system and illustration toolkit
from aurora_gfx import QC
import video_core as vc

W, H = 1920, 1080
LEFT = 140
CAPTION_ZONE = (150, 912, 1770, 1040)
CONTENT_BOTTOM = 900

# ---- Hypothetical economics (illustrative only; not Salvadoran tax liability, not a promised return)
ASSUMED_ANNUAL_TAX_SAVINGS = 30_000
ADDITIONAL_AFTER_TAX_OCCUPANCY_COST = 24_000
REMAINING_ANNUAL_ADVANTAGE = ASSUMED_ANNUAL_TAX_SAVINGS - ADDITIONAL_AFTER_TAX_OCCUPANCY_COST
assert REMAINING_ANNUAL_ADVANTAGE == 6_000, "narration and on-screen arithmetic say $6,000"


def usd(value):
    return f"${value:,.0f}"


class MainFilm(vc.Film):
    width, height, video_id = W, H, "main"

    # ------------------------------------------------------------ helpers
    def line(self, scene, i):
        return self.scenes[scene]["lines"][i]

    def at(self, scene, i, phrase=None):
        line = self.line(scene, i)
        return phrase_time(line, phrase) if phrase else line["start"]

    def current_scene(self, t):
        scene = self.timeline["scenes"][0]
        for s in self.timeline["scenes"]:
            if t >= s["start"]:
                scene = s
        return scene["id"]

    def draw(self, ctx, t):
        QC.width, QC.height, QC.caption_zone = W, H, CAPTION_ZONE if self.captions_on else None
        scene = self.current_scene(t)
        dark = scene == "close"
        set_color(ctx, NAVY if dark and t > self.scenes["close"]["start"] + 0.2 else CREAM)
        ctx.paint()
        getattr(self, f"scene_{scene}")(ctx, t)
        if not dark:
            self.header(ctx, t, scene)
        vc.draw_transition(ctx, t, self.boundaries, W, H)
        if self.captions_on:
            vc.draw_caption(ctx, self.captions, t, W / 2, 1032, 36, 1600)

    def header(self, ctx, t, scene):
        a = ease_out(prog(t, 0.15, 0.6))
        wordmark(ctx, 110, 96, 34, alpha=a)
        chapter = self.scenes[scene].get("chapter", "")
        if chapter:
            ca, _ = rise(ctx, t, self.scenes[scene]["start"] + 0.35)
            kicker(ctx, chapter, 1810, 92, alpha=ca, align="right")
        stroke_polyline(ctx, [(110, 122), (110 + 1700 * ease_out(prog(t, 0.2, 1.2)), 122)], NAVY, 1.2, alpha=0.35 * a)

    # ------------------------------------------------------------ 1. hook
    def scene_hook(self, ctx, t):
        c0, c1 = self.at("hook", 0), self.at("hook", 1)
        px, py, pw, ph = 980, 160, 820, 720
        panel(ctx, px, py, pw, ph, TEAL, prog(t, 0.0, 0.75), "up")
        ground = 800
        ctx.save()
        ctx.rectangle(px, py, pw, ph)
        ctx.clip()
        ground_line(ctx, px, px + pw, ground, prog(t, 0.3, 0.8))
        weak = prog(t, phrase_time(self.line("hook", 1), "weak location"), 1.2)
        historic_facade(ctx, 1120, ground, 540, 460, OCHRE, line_p=prog(t, 0.35, 1.7), fill_p=prog(t, 1.35, 0.6),
                        shutters=weak * 1.1)
        # foot traffic: two passers-by early; at "weak location" the street empties
        for k, (start_x, speed, shirt, h) in enumerate(((1010, 150, TERRACOTTA, 170), (1780, -120, COBALT, 158))):
            walk_t = t - 0.9 - k * 0.3
            if walk_t > 0:
                x = start_x + speed * walk_t
                leave = weak * 1.0
                x += (1 if speed > 0 else -1) * 900 * leave ** 2
                person(ctx, x, ground, h, shirt, walk=walk_t * 7, facing=1 if speed > 0 else -1)
        ctx.restore()
        # the incentive tag swings in on a string from the panel top
        tag_p = prog(t, phrase_time(self.line("hook", 0), "tax incentive"), 0.9)
        if tag_p > 0:
            swing = math.sin((t - c0) * 3.1) * 0.12 * math.exp(-(t - c0) * 0.6)
            ctx.save()
            ctx.rectangle(px, py, pw, ph)  # tag descends from the panel edge, never over the header
            ctx.clip()
            ctx.translate(1250, py)
            ctx.rotate(swing)
            drop = lerp(-260, 0, ease_back(tag_p, 1.1))
            stroke_polyline(ctx, [(0, 0), (0, 64 + drop)], NAVY, 2)
            chip(ctx, "Tax incentive", 0, 64 + drop, OCHRE, size=26, align="center")
            ctx.restore()
        a, dy = rise(ctx, t, c0)
        bottom = text_block(ctx, "A tax incentive can improve your return.", LEFT, 380 + dy, FONT_HEAD, 70, NAVY, 740,
                            leading=1.14, alpha=a)
        a2, dy2 = rise(ctx, t, c1)
        y2 = bottom + 150 + dy2
        width = text(ctx, "Can it fix a", LEFT, y2, FONT_HEAD_REG, 70, NAVY, alpha=a2)
        y3 = y2 + 80
        hl = ease_out(prog(t, phrase_time(self.line("hook", 1), "weak location"), 0.7))
        w_weak = text_width(ctx, "weak location?", FONT_HEAD_REG, 70)
        if hl > 0:
            ctx.rectangle(LEFT - 6, y3 - 50, (w_weak + 12) * hl, 66)
            set_color(ctx, TERRACOTTA)
            ctx.fill()
        text(ctx, "weak location?", LEFT, y3, FONT_HEAD_REG, 70, NAVY, alpha=a2)

    # ------------------------------------------------------------ 2. promise
    def scene_promise(self, ctx, t):
        s = self.scenes["promise"]["start"]
        line = self.line("promise", 0)
        a, dy = rise(ctx, t, s + 0.3)
        kicker(ctx, "El Salvador · Business expansion", LEFT, 222 + dy, alpha=a)
        text(ctx, "El Salvador Tax Incentives", LEFT, 318 + dy, FONT_HEAD, 80, NAVY, alpha=a)
        a2, dy2 = rise(ctx, t, s + 0.6)
        text(ctx, "Who qualifies for up to 10 years of relief?", LEFT, 394 + dy2, FONT_HEAD_REG, 50, NAVY, alpha=a2)
        items = [("which incentive applies", TEAL, "Which incentive applies"),
                 ("who receives the benefit", TERRACOTTA, "Who receives the benefit"),
                 ("what remains", COBALT, "What remains after location and execution costs")]
        for i, (phrase, color, label) in enumerate(items):
            start = phrase_time(line, phrase) - 0.15
            x, y, w, h = LEFT + i * 560, 470, 520, 400
            p = prog(t, start, 0.6)
            panel(ctx, x, y, w, h, color, p, "up")
            if p <= 0:
                continue
            ia = ease_out(prog(t, start + 0.25, 0.5))
            kicker(ctx, f"0{i + 1}", x + 30, y + 48, alpha=ia)
            ctx.save()
            ctx.rectangle(x, y, w, h)
            ctx.clip()
            ip = prog(t, start + 0.2, 1.0)
            if i == 0:
                document(ctx, x + 170, y + 70, 150, 190, CREAM, 5, ip, ip)
                stamp(ctx, x + 330, y + 215, 52, prog(t, start + 1.0, 0.7))
            elif i == 1:
                ground_line(ctx, x + 60, x + w - 60, y + 272, ip)
                for k, (shirt, kw) in enumerate(((OCHRE, {"prop": "folder", "arms": "hold"}), (TEAL, {"apron": True}),
                                                 (COBALT, {"hardhat": True, "arms": "point", "facing": -1}))):
                    fa = ease_out(prog(t, start + 0.3 + k * 0.2, 0.5))
                    person(ctx, x + 150 + k * 110, y + 272, 170, shirt, alpha=fa, **kw)
            else:
                base = y + 270
                bars = [(x + 120, 190, TEAL), (x + 230, 150, TERRACOTTA), (x + 340, 40, OCHRE)]
                ground_line(ctx, x + 90, x + 440, base, ip)
                for k, (bx, bh, bc) in enumerate(bars):
                    bp = ease_out(prog(t, start + 0.3 + k * 0.25, 0.6))
                    top = base - 190 if k == 1 else base - bh * bp
                    height = bh * bp
                    if k == 1:
                        ctx.rectangle(bx, top, 80, height)
                    else:
                        ctx.rectangle(bx, base - height, 80, height)
                    set_color(ctx, bc)
                    ctx.fill_preserve()
                    set_color(ctx, NAVY)
                    ctx.set_line_width(LINE)
                    ctx.stroke()
            ctx.restore()
            text_block(ctx, label, x + 30, y + 330, FONT_HEAD, 34, NAVY, w - 60, leading=1.12,
                       p=prog(t, start + 0.3, 1.0))

    # ------------------------------------------------------------ 3. opportunity
    def scene_opportunity(self, ctx, t):
        s = self.scenes["opportunity"]["start"]
        l0, l1, l2 = (self.line("opportunity", i) for i in range(3))
        a, dy = rise(ctx, t, l0["start"])
        kicker(ctx, "San Salvador · Historic Center", LEFT, 222 + dy, alpha=a)
        text_block(ctx, "Up to 10 years of income-tax relief", LEFT, 300, FONT_HEAD, 66, NAVY, 680, leading=1.12,
                   p=prog(t, l0["start"] + 0.1, 1.2))
        text_block(ctx, "For qualifying new investments inside the defined Historic Center.", LEFT, 468, FONT_BODY, 28,
                   NAVY, 640, leading=1.3, p=prog(t, phrase_time(l0, "qualifying new"), 1.2))
        # ten-year bar: fills as "up to ten years" is spoken
        ten = phrase_time(l0, "up to ten years")
        kicker(ctx, "Up to", LEFT, 590, alpha=ease_out(prog(t, ten - 0.3, 0.4)), size=18)
        for year in range(10):
            yp = ease_out(prog(t, ten - 0.2 + year * 0.12, 0.35))
            if yp <= 0:
                continue
            x = LEFT + year * 64
            ctx.rectangle(x, 606, 58, 44 * yp)
            set_color(ctx, OCHRE)
            ctx.fill_preserve()
            set_color(ctx, NAVY)
            ctx.set_line_width(LINE * 0.8)
            ctx.stroke()
        la = ease_out(prog(t, ten + 1.2, 0.5))
        text(ctx, "Year 1", LEFT, 686, FONT_BODY_MED, 20, NAVY, alpha=la)
        text(ctx, "Year 10", LEFT + 9 * 64 + 58, 686, FONT_BODY_MED, 20, NAVY, "right", alpha=la)
        # not every business qualifies
        np_ = prog(t, l2["start"], 0.6)
        panel(ctx, LEFT, 730, 640, 132, TERRACOTTA, np_, "right")
        if np_ > 0:
            na = ease_out(prog(t, l2["start"] + 0.3, 0.5))
            text(ctx, "Not every business qualifies.", LEFT + 28, 784, FONT_HEAD, 36, NAVY, alpha=na)
            text(ctx, "Verify current law and regulation before underwriting.", LEFT + 28, 830, FONT_BODY, 23, NAVY,
                 alpha=ease_out(prog(t, phrase_time(l2, "verify"), 0.5)))
        # right: the plan and its defined perimeter
        px, py, pw, ph = 880, 160, 920, 730
        panel(ctx, px, py, pw, ph, COBALT, prog(t, s + 0.1, 0.7), "up")
        plan = CityPlan(915, 190, 850, 490)
        plan.draw(ctx, t_grid=prog(t, l0["start"] + 0.2, 1.4), t_perimeter=prog(t, phrase_time(l0, "defined Historic"), 1.6),
                  t_fill=prog(t, phrase_time(l0, "may receive"), 1.4))
        # plaza block inside the zone
        if prog(t, l0["start"] + 1.4, 0.1) > 0:
            bx, by, bw, bh = plan.block_rect(3, 2)
            ctx.arc(bx + bw / 2, by + bh / 2, min(bw, bh) * 0.24, 0, 2 * math.pi)
            set_color(ctx, CREAM)
            ctx.fill_preserve()
            set_color(ctx, NAVY)
            ctx.set_line_width(LINE * 0.7)
            ctx.stroke()
        lg = ease_out(prog(t, phrase_time(l0, "defined Historic") + 1.0, 0.5))
        if lg > 0:
            stroke_polyline(ctx, [(915, 716), (975, 716)], NAVY, LINE * 1.4, dash=[14, 9], alpha=lg)
            text(ctx, "Defined Historic Center perimeter (illustrative)", 992, 724, FONT_BODY_MED, 22, NAVY, alpha=lg)
        # nationwide regimes: separate rules
        cp = prog(t, phrase_time(l1, "separate from"), 0.6)
        if cp > 0:
            panel(ctx, 910, 752, 860, 118, CREAM, cp, "right", radius=10)
            ca = ease_out(prog(t, phrase_time(l1, "separate from") + 0.3, 0.5))
            kicker(ctx, "Nationwide regimes · separate rules", 936, 790, alpha=ca, size=18)
            cx = 936
            for k, label in enumerate(("Tourism", "Free zones", "International services")):
                ka = ease_out(prog(t, phrase_time(l1, "nationwide") + k * 0.2, 0.4))
                cx += chip(ctx, label, cx, 808, PAPER, size=22, alpha=ka) + 12
        # which businesses inside the zone qualify?
        for k, ((c, r), fill, mark) in enumerate((((2, 1), TEAL, "check"), ((4, 3), TEAL, "check"),
                                                 ((5, 2), TERRACOTTA, "cross"), ((1, 2), OCHRE, "question"))):
            bp = prog(t, l2["start"] + 0.2 + k * 0.35, 0.9)
            if bp > 0:
                cx, cy = plan.block_center(c, r)
                badge(ctx, cx, cy, 24, fill, bp, mark)

    # ------------------------------------------------------------ 4. three checks
    def scene_checks(self, ctx, t):
        s = self.scenes["checks"]["start"]
        lines = [self.line("checks", i) for i in range(4)]
        a, dy = rise(ctx, t, lines[0]["start"])
        text(ctx, "Three checks", LEFT, 250 + dy, FONT_HEAD, 62, NAVY, alpha=a)
        rows = [("Exact location", "Inside the defined perimeter", COBALT),
                ("Qualifying investment", "Eligible activity, above the minimum", OCHRE),
                ("Approval", "Qualified by the Planning Authority", TEAL)]
        for i, (title, sub, color) in enumerate(rows):
            y = 320 + i * 180
            appear = ease_out(prog(t, lines[0]["start"] + 0.2 + i * 0.2, 0.5))
            active = prog(t, lines[i + 1]["start"], 0.45)
            done = prog(t, lines[i + 1]["end"] - 0.5, 0.8)
            if appear <= 0:
                continue
            rounded_rect(ctx, LEFT, y, 660, 150, 12)
            set_color(ctx, CREAM)
            ctx.fill()
            if active > 0:
                ctx.save()
                rounded_rect(ctx, LEFT, y, 660, 150, 12)
                ctx.clip()
                ctx.rectangle(LEFT, y, 660 * ease_in_out(active), 150)
                set_color(ctx, color)
                ctx.fill()
                ctx.restore()
            rounded_rect(ctx, LEFT, y, 660, 150, 12)
            set_color(ctx, NAVY, appear)
            ctx.set_line_width(LINE)
            ctx.stroke()
            if done > 0:
                badge(ctx, LEFT + 70, y + 75, 36, CREAM, done, "check")
            else:
                ctx.arc(LEFT + 70, y + 75, 36, 0, 2 * math.pi)
                set_color(ctx, CREAM, appear)
                ctx.fill_preserve()
                set_color(ctx, NAVY, appear)
                ctx.set_line_width(LINE)
                ctx.stroke()
                text(ctx, str(i + 1), LEFT + 70, y + 89, FONT_HEAD, 38, NAVY, "center", alpha=appear)
            text(ctx, title, LEFT + 130, y + 68, FONT_HEAD, 38, NAVY, alpha=appear)
            text(ctx, sub, LEFT + 130, y + 110, FONT_BODY, 25, NAVY, alpha=appear * (0.55 + 0.45 * active))
        # right panel: one illustration per check, each wiping over the last
        px, py, pw, ph = 880, 160, 920, 730
        starts = [s + 0.1] + [lines[i]["start"] for i in (2, 3)]
        colors = [COBALT, OCHRE, TEAL]
        for k in range(3):
            p = prog(t, starts[k], 0.6)
            if p <= 0:
                continue
            ctx.save()
            e = ease_in_out(p)
            if k == 0:
                ctx.rectangle(px - 4, py + ph * (1 - e) - 4, pw + 8, ph * e + 8)
            else:
                ctx.rectangle(px - 4, py - 4, pw * e + 8, ph + 8)
            ctx.clip()
            ctx.rectangle(px, py, pw, ph)
            set_color(ctx, colors[k])
            ctx.fill()
            [self._check_location, self._check_investment, self._check_approval][k](ctx, t, lines)
            ctx.restore()
            ctx.rectangle(px, py, pw, ph)
            set_color(ctx, NAVY)
            ctx.set_line_width(LINE)
            ctx.stroke()
            if k > 0 and p < 1:
                edge = px + pw * e
                stroke_polyline(ctx, [(edge, py), (edge, py + ph)], NAVY, LINE)

    def _check_location(self, ctx, t, lines):
        l1 = lines[1]
        plan = CityPlan(920, 200, 840, 540, cols=4, rows=3, gap=28,
                        perimeter=((0, 0), (2, 0), (2, 2), (3, 2), (3, 3), (0, 3)))
        inside_p = prog(t, phrase_time(l1, "inside the defined"), 0.7)
        outside_p = prog(t, phrase_time(l1, "One block outside"), 0.7)
        plan.draw(ctx, t_grid=prog(t, lines[0]["start"], 1.0), t_perimeter=prog(t, lines[0]["start"] + 0.5, 1.4),
                  t_fill=0, highlight={(1, 1): (TEAL, inside_p), (2, 1): (TERRACOTTA, outside_p)})
        for (c, r), p, fill, mark in (((1, 1), inside_p, TEAL, "check"), ((2, 1), outside_p, TERRACOTTA, "cross")):
            if p > 0:
                cx, cy = plan.block_center(c, r)
                badge(ctx, cx, cy, 34, CREAM, prog(t, (phrase_time(l1, "inside the defined") if mark == "check" else phrase_time(l1, "One block outside")) + 0.3, 0.9), mark)
        la = ease_out(prog(t, phrase_time(l1, "inside the defined"), 0.5))
        if la > 0:
            chip(ctx, "Inside the perimeter", 920, 790, TEAL, size=24, alpha=la)
        lb = ease_out(prog(t, phrase_time(l1, "One block outside"), 0.5))
        if lb > 0:
            chip(ctx, "One block outside", 1210, 790, TERRACOTTA, size=24, alpha=lb)

    def _check_investment(self, ctx, t, lines):
        l2 = lines[2]
        start = l2["start"]
        ground_line(ctx, 900, 1780, 600, prog(t, start, 0.6))
        historic_facade(ctx, 960, 600, 330, 300, CREAM, line_p=prog(t, start + 0.1, 1.2), fill_p=prog(t, start + 0.8, 0.5),
                        window_fill=COBALT)
        scaffold(ctx, 940, 600, 370, 300, prog(t, start + 0.8, 1.4))
        crane(ctx, 1450, 600, 330, prog(t, start + 0.4, 1.6), hook_y=0.5 + 0.12 * math.sin(t * 1.6))
        person(ctx, 1360, 600, 150, COBALT, hardhat=True, arms="point", facing=1,
               alpha=ease_out(prog(t, start + 1.2, 0.5)))
        chips = [("Food", "food", TEAL), ("Lodging", "lodging", TERRACOTTA), ("Culture", "lodging", COBALT),
                 ("Housing", "lodging", CREAM), ("Restoration", "restoration", TEAL)]
        cx = 920
        for k, (label, cue, fill) in enumerate(chips):
            ca = ease_out(prog(t, phrase_time(l2, cue) + (0.2 * (k - 1) if cue == "lodging" else 0), 0.45))
            cx += chip(ctx, label, cx, 628, fill, size=22, alpha=ca) + 10
        # investment vs. minimum threshold
        th = phrase_time(l2, "above the minimum")
        ta = ease_out(prog(t, th - 1.2, 0.5))
        if ta > 0:
            kicker(ctx, "Investment vs. minimum threshold", 920, 738, alpha=ta, size=18)
            rounded_rect(ctx, 920, 756, 840, 40, 20)
            set_color(ctx, CREAM, ta)
            ctx.fill()
            fill = ease_out(prog(t, th - 0.6, 1.4)) * 0.8
            if fill > 0:
                rounded_rect(ctx, 920, 756, 840 * fill, 40, 20)
                set_color(ctx, COBALT)
                ctx.fill()
            rounded_rect(ctx, 920, 756, 840, 40, 20)
            set_color(ctx, NAVY, ta)
            ctx.set_line_width(LINE)
            ctx.stroke()
            mx = 920 + 840 * 0.6
            stroke_polyline(ctx, [(mx, 742), (mx, 810)], NAVY, LINE * 1.2, alpha=ta)
            text(ctx, "Minimum", mx + 10, 830, FONT_BODY_MED, 20, NAVY, alpha=ta)
            if fill >= 0.6:
                badge(ctx, 920 + 840 * fill + 26, 776, 20, TEAL, prog(t, th + 0.3, 0.8), "check")

    def _check_approval(self, ctx, t, lines):
        l3 = lines[3]
        start = l3["start"]
        sa = ease_out(prog(t, start + 0.2, 0.5))
        rounded_rect(ctx, 1110, 196, 460, 64, 8)
        set_color(ctx, CREAM, sa)
        ctx.fill_preserve()
        set_color(ctx, NAVY, sa)
        ctx.set_line_width(LINE)
        ctx.stroke()
        text(ctx, "APLAN · Ventanilla Única", 1340, 238, FONT_BODY_SEMI, 26, NAVY, "center", alpha=sa)
        stroke_polyline(ctx, [(1180, 196), (1180, 170)], NAVY, 2, alpha=sa)
        stroke_polyline(ctx, [(1500, 196), (1500, 170)], NAVY, 2, alpha=sa)
        person(ctx, 1680, 700, 250, COBALT, arms="hold", facing=-1, alpha=ease_out(prog(t, start + 0.3, 0.5)))
        walk_in = ease_out(prog(t, start + 0.1, 1.4))
        person(ctx, lerp(900, 1090, walk_in), 760, 290, TERRACOTTA, walk=(t - start) * 7 * (1 - walk_in), arms="hold",
               prop="folder", facing=1)
        ctx.rectangle(1240, 560, 540, 200)
        set_color(ctx, PAPER)
        ctx.fill_preserve()
        set_color(ctx, NAVY)
        ctx.set_line_width(LINE)
        ctx.stroke()
        stroke_polyline(ctx, [(1240, 590), (1780, 590)], NAVY, LINE * 0.7)
        qualify = phrase_time(l3, "must qualify")
        dp = ease_out(prog(t, qualify - 0.6, 0.8))
        if dp > 0:
            document(ctx, lerp(1130, 1290, dp), lerp(470, 300, dp), 150, 196, CREAM, 5, 1, 1, rotate=lerp(-0.2, -0.05, dp))
            stamp(ctx, lerp(1130, 1290, dp) + 150, lerp(470, 300, dp) + 170, 56, prog(t, phrase_time(l3, "the project") + 0.1, 0.8))
        na = ease_out(prog(t, phrase_time(l3, "No approval"), 0.5))
        if na > 0:
            text(ctx, "No approval, no benefit to model.", 1340, 840, FONT_HEAD, 36, NAVY, "center", alpha=na)

    # ------------------------------------------------------------ 5. beneficiary
    def scene_beneficiary(self, ctx, t):
        l0, l1, l2 = (self.line("beneficiary", i) for i in range(3))
        a, dy = rise(ctx, t, l0["start"])
        text(ctx, "Which entity receives the benefit?", W / 2, 240 + dy, FONT_HEAD, 62, NAVY, "center", alpha=a)
        ta = ease_back(prog(t, phrase_time(l0, "receives"), 0.6))
        if ta > 0:
            ctx.save()
            ctx.translate(W / 2, 312)
            ctx.scale(ta, ta)
            chip(ctx, "Qualified benefit", 0, -24, OCHRE, size=26, align="center")
            ctx.restore()
        cards = [("Owner · landlord", "Holds the property", OCHRE, "owner"),
                 ("Operator · tenant", "Runs the business", TEAL, "operator"),
                 ("Developer", "Builds the project", COBALT, "developer")]
        resolve = l2["start"]
        for i, (title, sub, color, key) in enumerate(cards):
            start = phrase_time(l1, key.capitalize() if key == "owner" else key)
            x, y, w, h = 170 + i * 560, 430, 460, 390
            cx = x + w / 2
            lp = prog(t, start - 0.3, 0.8)
            if lp > 0:
                solid = key == "owner" and t > resolve + 0.4
                pts = partial_polyline([(W / 2, 336), (W / 2, 376), (cx, 376), (cx, y)], lp)
                stroke_polyline(ctx, pts, NAVY, LINE, dash=None if solid else [10, 8])
            panel(ctx, x, y, w, h, color, prog(t, start, 0.6), "up")
            if prog(t, start, 0.6) <= 0:
                continue
            ctx.save()
            ctx.rectangle(x, y, w, h)
            ctx.clip()
            ip = prog(t, start + 0.2, 1.1)
            ground_line(ctx, x + 30, x + w - 30, y + 250, ip)
            if key == "owner":
                historic_facade(ctx, x + 70, y + 250, 200, 170, CREAM, ip, prog(t, start + 0.8, 0.4))
                person(ctx, x + 340, y + 250, 150, OCHRE, arms="hold", prop="folder", facing=-1, alpha=ease_out(prog(t, start + 0.6, 0.5)))
            elif key == "operator":
                storefront(ctx, x + 60, y + 250, 210, 190, CREAM, TERRACOTTA, ip, prog(t, start + 0.8, 0.4))
                person(ctx, x + 350, y + 250, 150, TEAL, apron=True, arms="present", facing=-1, alpha=ease_out(prog(t, start + 0.6, 0.5)))
            else:
                crane(ctx, x + 100, y + 250, 200, ip, hook_y=0.5 + 0.15 * math.sin(t * 1.7))
                person(ctx, x + 350, y + 250, 150, OCHRE, hardhat=True, arms="point", facing=-1, alpha=ease_out(prog(t, start + 0.6, 0.5)))
            ctx.restore()
            text(ctx, title, x + 28, y + 318, FONT_HEAD, 36, NAVY, alpha=ease_out(prog(t, start + 0.3, 0.5)))
            text(ctx, sub, x + 28, y + 358, FONT_BODY, 24, NAVY, alpha=ease_out(prog(t, start + 0.4, 0.5)))
            mark = "question"
            fill = CREAM
            if t > resolve + 0.4 and key == "owner":
                mark, fill = "check", TEAL
            elif t > resolve + 0.9 and key == "operator":
                mark, fill = "cross", TERRACOTTA
            bstart = start + 0.2 if mark == "question" else resolve + (0.4 if key == "owner" else 0.9)
            badge(ctx, cx, 404, 22, fill, prog(t, bstart, 0.8), mark)
        na = ease_out(prog(t, phrase_time(l2, "automatically"), 0.5))
        if na > 0:
            chip(ctx, "Landlord qualified ≠ tenant benefits automatically", W / 2, 846, TERRACOTTA, size=24, alpha=na, align="center")

    # ------------------------------------------------------------ 6. economics
    def scene_economics(self, ctx, t):
        l0, l1, l2 = (self.line("economics", i) for i in range(3))
        a, dy = rise(ctx, t, l0["start"])
        chip(ctx, "Simplified hypothetical", LEFT, 176 + dy, TERRACOTTA, size=22, alpha=a)
        text_block(ctx, "Annual after-tax comparison", LEFT, 300, FONT_HEAD, 58, NAVY, 700, leading=1.1,
                   p=prog(t, l0["start"] + 0.2, 1.0))
        t_save, t_minus, t_leaves = (phrase_time(l1, p) for p in ("Thirty", "minus", "leaves"))
        rows = [(t_save, "Assumed tax savings", ASSUMED_ANNUAL_TAX_SAVINGS, "", TEAL),
                (t_minus, "Additional after-tax occupancy costs", ADDITIONAL_AFTER_TAX_OCCUPANCY_COST, "−", TERRACOTTA)]
        for k, (start, label, value, sign, color) in enumerate(rows):
            y = 480 + k * 96
            ra, rdy = rise(ctx, t, start)
            if ra <= 0:
                continue
            ctx.rectangle(LEFT, y - 30 + rdy, 14, 40)
            set_color(ctx, color, ra)
            ctx.fill()
            text_block(ctx, label, LEFT + 32, y + rdy, FONT_BODY, 27, NAVY, 380, leading=1.15, alpha=ra)
            shown = value * ease_out(prog(t, start, 1.1))
            text(ctx, f"{sign}{usd(round(shown / 100) * 100)}", 820, y + 6 + rdy, FONT_HEAD, 46, NAVY, "right", alpha=ra)
        rule = ease_out(prog(t, t_leaves - 0.3, 0.6))
        stroke_polyline(ctx, partial_polyline([(LEFT, 640), (820, 640)], rule), NAVY, LINE * 1.3)
        ra, rdy = rise(ctx, t, t_leaves)
        if ra > 0:
            vw = text_width(ctx, f"= {usd(REMAINING_ANNUAL_ADVANTAGE)}", FONT_HEAD, 54)
            ctx.rectangle(820 - vw - 14, 668 + rdy, vw + 28, 72)
            set_color(ctx, OCHRE, ra)
            ctx.fill()
            text(ctx, "Remaining annual advantage", LEFT + 32, 716 + rdy, FONT_BODY_SEMI, 27, NAVY, alpha=ra)
            shown = REMAINING_ANNUAL_ADVANTAGE * ease_out(prog(t, t_leaves, 0.9))
            text(ctx, f"= {usd(round(shown / 100) * 100)}", 820, 724 + rdy, FONT_HEAD, 54, NAVY, "right", alpha=ra)
        # waterfall chart
        base, scale = 640, 13.0 / 1000  # px per dollar
        ca = ease_out(prog(t, l0["start"] + 0.4, 0.6))
        kicker(ctx, "USD per year · after tax · hypothetical", 1000, 196, alpha=ca, size=18)
        for g in (0, 10_000, 20_000, 30_000):
            gy = base - g * scale
            stroke_polyline(ctx, partial_polyline([(1000, gy), (1790, gy)], ca), NAVY, 1.2 if g else LINE, alpha=0.3 if g else 1)
            text(ctx, f"${g // 1000}k" if g else "$0", 990, gy + 7, FONT_BODY_MED, 20, NAVY, "right", alpha=ca)
        bars = [(1050, t_save, 0, ASSUMED_ANNUAL_TAX_SAVINGS, TEAL, "Assumed tax savings"),
                (1310, t_minus, REMAINING_ANNUAL_ADVANTAGE, ASSUMED_ANNUAL_TAX_SAVINGS, TERRACOTTA, "Added occupancy cost, after tax"),
                (1570, t_leaves, 0, REMAINING_ANNUAL_ADVANTAGE, OCHRE, "Remaining advantage")]
        for k, (bx, start, low, high, color, label) in enumerate(bars):
            bp = ease_out(prog(t, start, 1.0))
            if bp <= 0:
                continue
            y_low, y_high = base - low * scale, base - high * scale
            if k == 1:  # the cost bar hangs down from the savings level
                y0, y1 = y_high, y_high + (y_low - y_high) * bp
            else:
                y0, y1 = y_low - (y_low - y_high) * bp, y_low
            ctx.rectangle(bx, y0, 190, y1 - y0)
            set_color(ctx, color)
            ctx.fill_preserve()
            set_color(ctx, NAVY)
            ctx.set_line_width(LINE)
            ctx.stroke()
            va = ease_out(prog(t, start + 0.6, 0.4))
            value_text = ("−" if k == 1 else "") + usd(high - low)
            if k == 1:
                text(ctx, value_text, bx + 95, (y0 + y1) / 2 + 10, FONT_BODY_SEMI, 28, NAVY, "center", alpha=va)
            else:
                text(ctx, value_text, bx + 95, y0 - 14, FONT_BODY_SEMI, 28, NAVY, "center", alpha=va)
            text_block(ctx, label, bx + 95, base + 36, FONT_BODY, 21, NAVY, 200, leading=1.2, align="center", alpha=va)
            if k > 0:  # connector from previous bar
                prev_level = base - (ASSUMED_ANNUAL_TAX_SAVINGS if k == 1 else REMAINING_ANNUAL_ADVANTAGE) * scale
                stroke_polyline(ctx, partial_polyline([(bx - 70, prev_level), (bx, prev_level)], bp), NAVY, 1.6, dash=[6, 6])
        # what the arithmetic leaves out
        f1 = ease_out(prog(t, l2["start"], 0.6))
        if f1 > 0:
            ghost_top = base - (REMAINING_ANNUAL_ADVANTAGE + 5_000) * scale
            stroke_polyline(ctx, [(1570, base - REMAINING_ANNUAL_ADVANTAGE * scale), (1570, ghost_top), (1760, ghost_top),
                                  (1760, base - REMAINING_ANNUAL_ADVANTAGE * scale)], NAVY, 1.8, dash=[8, 7], alpha=f1)
            badge(ctx, 1665, ghost_top - 4, 20, CREAM, prog(t, l2["start"] + 0.2, 0.8), "question")
        panel(ctx, LEFT, 790, 1640, 96, PAPER, prog(t, l2["start"], 0.6), "right", radius=10)
        if f1 > 0:
            text(ctx, "Excludes other cost, timing, and risk differences.", LEFT + 28, 830, FONT_BODY_MED, 25, NAVY,
                 alpha=ease_out(prog(t, l2["start"] + 0.3, 0.5)))
            text(ctx, "Not a calculation of Salvadoran tax liability. Not a promised return.", LEFT + 28, 866, FONT_BODY, 25,
                 NAVY, alpha=ease_out(prog(t, phrase_time(l2, "It's not"), 0.5)))

    # ------------------------------------------------------------ 7. execution
    def scene_execution(self, ctx, t):
        l0, l1 = self.line("execution", 0), self.line("execution", 1)
        swap = l1["start"]
        if t < swap + 0.4:
            self._execution_risks(ctx, t, l0)
        if t >= swap:
            p = prog(t, swap, 0.6)
            ctx.save()
            e = ease_in_out(p)
            ctx.rectangle(0, 130, W * e, CONTENT_BOTTOM - 130 + 4)
            ctx.clip()
            set_color(ctx, CREAM)
            ctx.paint()
            self._execution_layers(ctx, t, l1)
            ctx.restore()
            if p < 1:
                stroke_polyline(ctx, [(W * e, 130), (W * e, CONTENT_BOTTOM)], NAVY, LINE)

    def _execution_risks(self, ctx, t, l0):
        a, dy = rise(ctx, t, l0["start"])
        text(ctx, "Execution still decides the outcome", LEFT, 250 + dy, FONT_HEAD, 58, NAVY, alpha=a)
        tiles = [("Demand", "demand", TEAL), ("Permits", "permits", OCHRE), ("Utilities", "utilities", COBALT),
                 ("Opening delays", "opening delays", TERRACOTTA)]
        for i, (label, cue, color) in enumerate(tiles):
            start = phrase_time(l0, cue) - 0.1
            x, y, w, h = LEFT + i * 420, 310, 380, 370
            p = prog(t, start, 0.55)
            panel(ctx, x, y, w, h, color, p, "up")
            if p <= 0:
                continue
            ip = prog(t, start + 0.15, 1.0)
            ctx.save()
            ctx.rectangle(x, y, w, h)
            ctx.clip()
            ground_line(ctx, x + 20, x + w - 20, y + 270, ip)
            if i == 0:
                storefront(ctx, x + 40, y + 270, 170, 170, CREAM, TERRACOTTA, ip, prog(t, start + 0.5, 0.4))
                for k in range(2):
                    wx = x + 380 - ((t - start) * 60 + k * 90) % 200
                    person(ctx, wx, y + 270, 120, (OCHRE, COBALT)[k], walk=(t - start) * 7 + k, facing=-1,
                           alpha=ease_out(prog(t, start + 0.4, 0.4)))
            elif i == 1:
                for k in range(3):
                    document(ctx, x + 90 + k * 34, y + 60 + k * 20, 140, 180, CREAM, 4, ip, ip, rotate=-0.08 + k * 0.06)
                badge(ctx, x + 290, y + 220, 30, CREAM, prog(t, start + 0.8, 0.8), "question")
            elif i == 2:
                utility_pole(ctx, x + 110, y + 270, 220, ip, math.sin(t * 2))
            else:
                calendar_icon(ctx, x + 100, y + 70, 180, 170, flip=clamp((t - start - 0.3) / 3.5))
            ctx.restore()
            text(ctx, label, x + 24, y + 330, FONT_HEAD, 34, NAVY, alpha=ease_out(prog(t, start + 0.3, 0.5)))
        # the thin advantage erodes
        erase = phrase_time(l0, "erase")
        ea = ease_out(prog(t, erase - 0.5, 0.5))
        if ea > 0:
            kicker(ctx, "Remaining advantage (hypothetical)", LEFT, 736, alpha=ea, size=18)
            full = 700
            remaining = lerp(full, 150, ease_in_out(prog(t, erase, 1.6)))
            ctx.rectangle(LEFT, 756, remaining, 44)
            set_color(ctx, OCHRE, ea)
            ctx.fill_preserve()
            set_color(ctx, NAVY, ea)
            ctx.set_line_width(LINE)
            ctx.stroke()
            if remaining < full - 2:
                ctx.rectangle(LEFT + remaining, 756, full - remaining, 44)
                set_color(ctx, NAVY, ea)
                ctx.set_line_width(1.6)
                ctx.set_dash([8, 7])
                ctx.stroke()
                ctx.set_dash([])

    def _execution_layers(self, ctx, t, l1):
        a, dy = rise(ctx, t, l1["start"] + 0.2)
        text(ctx, "Underwrite in two layers", LEFT, 250 + dy, FONT_HEAD, 58, NAVY, alpha=a)
        columns = [(LEFT, "1 · Base case", "No incentives assumed. It must work on its own.", CREAM, l1["start"] + 0.3, False),
                   (1000, "2 · Qualified benefit", "Shown separately, only if approved.", OCHRE,
                    phrase_time(l1, "show the qualified"), True)]
        for x, title, sub, fill, start, dashed in columns:
            p = prog(t, start, 0.6)
            panel(ctx, x, 300, 780, 580, PAPER if not dashed else CREAM, p, "up")
            if p <= 0:
                continue
            ca = ease_out(prog(t, start + 0.25, 0.5))
            text(ctx, title, x + 36, 368, FONT_HEAD, 42, NAVY, alpha=ca)
            text(ctx, sub, x + 36, 412, FONT_BODY, 25, NAVY, alpha=ca)
            base = 810
            ground_line(ctx, x + 36, x + 744, base, prog(t, start + 0.2, 0.6))
            heights = [250, 270, 285, 295, 300] if not dashed else [70, 75, 78, 80, 82]
            for k, bh in enumerate(heights):
                bp = ease_out(prog(t, start + 0.35 + k * 0.1, 0.6))
                if bp <= 0:
                    continue
                bx = x + 70 + k * 136
                ctx.rectangle(bx, base - bh * bp, 96, bh * bp)
                set_color(ctx, fill if not dashed else OCHRE)
                ctx.fill_preserve()
                set_color(ctx, NAVY)
                ctx.set_line_width(LINE)
                if dashed:
                    ctx.set_dash([9, 6])
                ctx.stroke()
                ctx.set_dash([])
                text(ctx, f"Yr {k + 1}", bx + 48, base + 30, FONT_BODY_MED, 20, NAVY, "center", alpha=bp)
            if dashed:
                chip(ctx, "Subject to approval", x + 36, 450, TERRACOTTA, size=22, alpha=ca)
                stamp(ctx, x + 620, 560, 60, prog(t, start + 1.2, 0.8))

    # ------------------------------------------------------------ 8. close
    def scene_close(self, ctx, t):
        s = self.scenes["close"]["start"]
        l0, l1 = self.line("close", 0), self.line("close", 1)
        a = ease_out(prog(t, s + 0.3, 0.7))
        ctx.save()
        ctx.translate(0, (1 - a) * 20)
        wordmark(ctx, W / 2, 300, 120, color=CREAM, fill=OCHRE, alpha=a, align="center")
        ctx.restore()
        kicker(ctx, "Latin America Expansion", W / 2, 362, alpha=a, color=CREAM, size=24, align="center")
        ba, bdy = rise(ctx, t, phrase_time(l0, "illustrated"))
        text(ctx, "Illustrated breakdowns of incentives, locations, and the real cost to open.", W / 2, 440 + bdy,
             FONT_BODY, 30, CREAM, "center", alpha=ba)
        sp = ease_back(prog(t, l0["start"], 0.6))
        if sp > 0:
            ctx.save()
            ctx.translate(W / 2, 530)
            ctx.scale(sp, sp)
            rounded_rect(ctx, -170, -40, 340, 80, 40)
            set_color(ctx, OCHRE)
            ctx.fill_preserve()
            set_color(ctx, CREAM)
            ctx.set_line_width(LINE)
            ctx.stroke()
            text(ctx, "Subscribe", 0, 12, FONT_BODY_SEMI, 34, NAVY, "center")
            ctx.restore()
        ha, _ = rise(ctx, t, l0["start"] + 0.6)
        text(ctx, "@ConAurora  ·  conaurora.com", W / 2, 628, FONT_BODY_MED, 28, CREAM, "center", alpha=ha)
        np_ = prog(t, l1["start"] - 0.1, 0.6)
        panel(ctx, 380, 680, 1160, 200, CREAM, np_, "up", radius=14)
        if np_ > 0:
            na = ease_out(prog(t, l1["start"] + 0.2, 0.5))
            kicker(ctx, "Next episode", 420, 726, alpha=na, size=20)
            text_block(ctx, "Who receives the benefit: the owner, operator, or developer?", 420, 780, FONT_HEAD, 38,
                       NAVY, 700, leading=1.15, alpha=na)
            for k, (shirt, kw) in enumerate(((OCHRE, {"prop": "folder", "arms": "hold"}), (TEAL, {"apron": True}),
                                             (COBALT, {"hardhat": True, "arms": "point", "facing": -1}))):
                fa = ease_out(prog(t, phrase_time(l1, ("owner", "operator", "developer")[k]), 0.5))
                person(ctx, 1230 + k * 100, 858, 150, shirt, alpha=fa, **kw)


def main():
    parser = argparse.ArgumentParser(description="Render the Aurora main film.")
    parser.add_argument("--out", default=str(vc.PRODUCTION.parent / "deliverables"))
    parser.add_argument("--stills", nargs="*", type=float, help="render PNG stills at these times instead of video")
    parser.add_argument("--contact-sheet", action="store_true", help="render a still every 2 s for review")
    parser.add_argument("--clean", action="store_true", help="render without burned-in captions")
    parser.add_argument("--svg", action="store_true", help="export editable SVG keyframes per scene")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--qc-only", action="store_true", help="run per-frame text QC without encoding")
    args = parser.parse_args()
    film = MainFilm(captions_on=not args.clean)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.stills or args.contact_sheet:
        times = args.stills or [x * 2.0 for x in range(int(film.duration / 2) + 1)]
        for time in times:
            issues = vc.still(film, time, out / f"main_{time:06.2f}.png")
            for issue in issues:
                print(f"{time:6.2f}s  {issue}")
        return
    if args.qc_only:
        stem = "Aurora_ElSalvador_TaxIncentives_YouTube_1920x1080" + ("_clean" if args.clean else "")
        count, issues = vc.qc_pass(film, stem, args.workers)
        print(f"{stem}: {len(issues)} of {count} frames flagged")
        return
    if args.svg:
        for scene in film.timeline["scenes"]:
            keyframe = max(line["end"] for line in scene["lines"]) - 0.1
            vc.svg_frame(film, keyframe, out / f"main_{scene['id']}_keyframe.svg")
        return
    master = vc.PRODUCTION / "audio" / "main_narration_master.wav"
    vc.master_audio(vc.PRODUCTION / "audio" / "main_narration.wav", master)
    name = "Aurora_ElSalvador_TaxIncentives_YouTube_1920x1080" + ("_clean" if args.clean else "") + ".mp4"
    issues = vc.render(film, out / name, master, workers=args.workers)
    print(f"rendered {out / name}; QC issues on {len(issues)} frames")
    for index, problems in issues[:40]:
        print(f"{index / vc.FPS:7.2f}s  " + " | ".join(sorted(set(problems))))


if __name__ == "__main__":
    main()
