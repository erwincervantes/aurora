"""Aurora editorial illustration toolkit (pycairo) — flat 'facts & figures' style.

Look: cool off-white page, indigo condensed numerals as heroes, coral section labels and rules,
grey secondary lines, flat outline-free figures and facades, orange block maps with
white street lines and small numbered markers. Everything is original vector drawing.
"""
import math
from contextlib import contextmanager

import cairo


# ---------------------------------------------------------------- brand system
def hex_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))

def mix(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))

PAGE = hex_rgb("#F1F1F4")      # cool off-white page
INK = hex_rgb("#2D2B6E")       # indigo: numerals, headings, text
CORAL = hex_rgb("#E5474E")     # section labels, rules, data lines
GREY = hex_rgb("#7E8197")      # italic secondary lines
RULE = hex_rgb("#D3D5DF")      # gridlines, inactive map blocks
LIGHT = hex_rgb("#E3E4EB")     # quiet surfaces
WHITE = hex_rgb("#FBFBFD")
# illustration fills (flat, no outlines)
ORANGE = hex_rgb("#F29A3A")    # map mass, remaining advantage
GOLD = hex_rgb("#F6B73C")
BLUE = hex_rgb("#3A6BC8")      # savings
SKY = hex_rgb("#9CC2EA")
PINK = hex_rgb("#EE82A9")
RED = hex_rgb("#D8402E")
GREEN = hex_rgb("#3E9E5A")
PURPLE = hex_rgb("#7C5AA0")
SKIN = hex_rgb("#F2A08C")
DARK = hex_rgb("#2A2438")      # hair, shoes

# Type per The Aurora Standard v5 (chapter 04): Fraunces = voice/headlines/numerals, Geist = text/UI,
# Geist Mono = labels and data. Italic is emphasis, not texture: WONK is used at most once per view.
NUM = "AuroraSerifDisplay"     # Fraunces 330, opsz 144: hero numerals (display token)
NUM_MED = "AuroraSerifDisplay"
HEAD = "AuroraSerifHead"       # Fraunces 340: headlines (h2 / lead tokens)
WONK = "AuroraSerifWonk"       # Fraunces italic, opsz 144 SOFT 100 WONK 1: the single emphasis per view
SANS = "AuroraGeistReg"        # Geist 400: body
SANS_MED = "AuroraGeistMed"    # Geist 500
SANS_SEMI = "AuroraGeistSemi"  # Geist 600: small uppercase subheads, UI emphasis
SUB = "AuroraGeistReg"         # secondary lines (set plainly, in grey)
MONO = "AuroraMono"            # Geist Mono 500: labels, folios, axis values

# Logo colours are locked by the design system (misuse rule: never recolour the wordmark or aperture).
LOGO_INK = hex_rgb("#1A2236")
LOGO_CREAM = hex_rgb("#FAF7F1")
AMBER_DK = hex_rgb("#8A5E27")
AMBER_LT = hex_rgb("#D9AE7A")
HERITAGE = [hex_rgb(h) for h in ("#2CA354", "#6BBE50", "#6EC6AF", "#3B5FAA", "#BF97C5", "#ED2C6D",
                                 "#EE4137", "#EF4937", "#F58634", "#F8DF26", "#2CA354", "#6BBE50")]

HAIR = 1.6                     # hairline weight for rules, grids, cranes


# ---------------------------------------------------------------- timing
def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))

def prog(t, start, duration):
    if duration <= 0:
        return 1.0 if t >= start else 0.0
    return clamp((t - start) / duration)

def ease_out(x):
    return 1 - (1 - x) ** 3

def ease_in_out(x):
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2

def ease_back(x, overshoot=1.4):
    x = clamp(x)
    return 1 + (overshoot + 1) * (x - 1) ** 3 + overshoot * (x - 1) ** 2

def lerp(a, b, x):
    return a + (b - a) * x

def phrase_time(line, phrase):
    """Estimate when `phrase` is spoken inside a timeline line (character-proportional)."""
    index = line["text"].find(phrase)
    if index < 0:
        raise ValueError(f"phrase not in line: {phrase!r}")
    return line["start"] + (line["end"] - line["start"]) * index / len(line["text"])


# ---------------------------------------------------------------- QC registry
class QC:
    """Collects visible device-space text boxes each frame to flag clipping and caption collisions."""
    width = 1920
    height = 1080
    safe_margin = 40
    caption_zone = None
    boxes = []

    @classmethod
    def reset(cls):
        cls.boxes = []

    @classmethod
    def register(cls, ctx, x0, y0, x1, y1, label, is_caption=False):
        cx0, cy0, cx1, cy1 = ctx.clip_extents()
        x0, y0, x1, y1 = max(x0, cx0), max(y0, cy0), min(x1, cx1), min(y1, cy1)
        if x1 <= x0 or y1 <= y0:
            return
        corners = [ctx.user_to_device(x, y) for x, y in ((x0, y0), (x1, y0), (x0, y1), (x1, y1))]
        xs, ys = [c[0] for c in corners], [c[1] for c in corners]
        cls.boxes.append((min(xs), min(ys), max(xs), max(ys), label, is_caption))

    @classmethod
    def problems(cls):
        issues = []
        for x0, y0, x1, y1, label, is_caption in cls.boxes:
            m = cls.safe_margin
            if x0 < m - 1 or y0 < m - 1 or x1 > cls.width - m + 1 or y1 > cls.height - m + 1:
                issues.append(f"outside safe area: {label!r} ({x0:.0f},{y0:.0f},{x1:.0f},{y1:.0f})")
            if cls.caption_zone and not is_caption:
                cx0, cy0, cx1, cy1 = cls.caption_zone
                if x0 < cx1 and x1 > cx0 and y0 < cy1 and y1 > cy0:
                    issues.append(f"overlaps caption zone: {label!r}")
        return issues


# ---------------------------------------------------------------- primitives
def set_color(ctx, color, alpha=1.0):
    ctx.set_source_rgba(color[0], color[1], color[2], alpha)

def rounded_rect(ctx, x, y, w, h, r):
    r = max(0.0, min(r, abs(w) / 2, abs(h) / 2))
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()

def rect(ctx, x, y, w, h, color, alpha=1.0, radius=0):
    if w <= 0 or h <= 0:
        return
    if radius:
        rounded_rect(ctx, x, y, w, h, radius)
    else:
        ctx.rectangle(x, y, w, h)
    set_color(ctx, color, alpha)
    ctx.fill()

def disc(ctx, cx, cy, r, color, alpha=1.0):
    if r <= 0:
        return
    ctx.new_path()
    ctx.arc(cx, cy, r, 0, 2 * math.pi)
    set_color(ctx, color, alpha)
    ctx.fill()

def poly(ctx, points, color, alpha=1.0):
    ctx.new_path()
    ctx.move_to(*points[0])
    for p in points[1:]:
        ctx.line_to(*p)
    ctx.close_path()
    set_color(ctx, color, alpha)
    ctx.fill()

def partial_polyline(points, fraction, closed=False):
    pts = list(points) + ([points[0]] if closed else [])
    segs = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    budget = sum(segs) * clamp(fraction)
    out = [pts[0]]
    for i, seg in enumerate(segs):
        if budget >= seg:
            out.append(pts[i + 1])
            budget -= seg
        else:
            if seg > 0 and budget > 0:
                a, b = pts[i], pts[i + 1]
                out.append((lerp(a[0], b[0], budget / seg), lerp(a[1], b[1], budget / seg)))
            break
    return out

def line(ctx, points, color=INK, width=HAIR, dash=None, alpha=1.0, cap=cairo.LINE_CAP_ROUND):
    if len(points) < 2:
        return
    ctx.new_path()
    ctx.move_to(*points[0])
    for p in points[1:]:
        ctx.line_to(*p)
    ctx.set_line_width(width)
    ctx.set_line_cap(cap)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    set_color(ctx, color, alpha)
    if dash:
        ctx.set_dash(dash)
    ctx.stroke()
    ctx.set_dash([])

def check_mark(ctx, cx, cy, size, p=1.0, color=WHITE, width=None):
    pts = [(cx - size * 0.38, cy + size * 0.02), (cx - size * 0.1, cy + size * 0.3), (cx + size * 0.4, cy - size * 0.3)]
    line(ctx, partial_polyline(pts, p), color, width or max(3, size * 0.17))

def cross_mark(ctx, cx, cy, size, p=1.0, color=WHITE, width=None):
    s, w = size * 0.3, width or max(3, size * 0.16)
    line(ctx, partial_polyline([(cx - s, cy - s), (cx + s, cy + s)], clamp(p * 2)), color, w)
    line(ctx, partial_polyline([(cx + s, cy - s), (cx - s, cy + s)], clamp(p * 2 - 1)), color, w)

@contextmanager
def grow(ctx, cx, base_y, p, overshoot=1.2):
    """Objects rise out of the ground line (scale Y from the base) — the house reveal."""
    s = ease_back(clamp(p), overshoot) if p < 1 else 1.0
    ctx.save()
    ctx.translate(cx, base_y)
    ctx.scale(1, max(0.0001, s))
    ctx.translate(-cx, -base_y)
    yield s
    ctx.restore()

@contextmanager
def pop(ctx, cx, cy, p, overshoot=1.6):
    s = ease_back(clamp(p), overshoot) if p < 1 else 1.0
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(max(0.0001, s), max(0.0001, s))
    ctx.translate(-cx, -cy)
    yield s
    ctx.restore()

@contextmanager
def wipe(ctx, x, y, w, h, p, direction="right"):
    e = ease_in_out(clamp(p))
    ctx.save()
    if direction == "right":
        ctx.rectangle(x, y, w * e, h)
    elif direction == "left":
        ctx.rectangle(x + w * (1 - e), y, w * e, h)
    elif direction == "up":
        ctx.rectangle(x, y + h * (1 - e), w, h * e)
    else:
        ctx.rectangle(x, y, w, h * e)
    ctx.clip()
    yield e
    ctx.restore()


# ---------------------------------------------------------------- text
def font(ctx, face, size):
    ctx.select_font_face(face, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    options = cairo.FontOptions()
    options.set_antialias(cairo.ANTIALIAS_GRAY)
    options.set_hint_style(cairo.HINT_STYLE_NONE)
    options.set_hint_metrics(cairo.HINT_METRICS_OFF)
    ctx.set_font_options(options)

def text_width(ctx, s, face, size, tracking=0.0):
    font(ctx, face, size)
    return ctx.text_extents(s).x_advance + tracking * max(0, len(s) - 1)

def text(ctx, s, x, y, face, size, color=INK, align="left", alpha=1.0, tracking=0.0, label="text", is_caption=False):
    """One line, baseline at y. Returns drawn width."""
    font(ctx, face, size)
    width = text_width(ctx, s, face, size, tracking)
    if align == "center":
        x -= width / 2
    elif align == "right":
        x -= width
    set_color(ctx, color, alpha)
    if tracking:
        cursor = x
        for ch in s:
            ctx.move_to(cursor, y)
            ctx.show_text(ch)
            cursor += ctx.text_extents(ch).x_advance + tracking
    else:
        ctx.move_to(x, y)
        ctx.show_text(s)
    ctx.new_path()
    if label is not None and alpha > 0.02:
        ascent, descent = ctx.font_extents()[0], ctx.font_extents()[1]
        QC.register(ctx, x, y - ascent * 0.8, x + width, y + descent * 0.6, s if label == "text" else label, is_caption)
    return width

def wrap(ctx, s, face, size, max_width):
    words, lines, current = s.split(), [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if text_width(ctx, trial, face, size) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

def text_block(ctx, s, x, y, face, size, color=INK, max_width=800, leading=1.2, align="left", alpha=1.0, p=None, stagger=0.12):
    """Wrapped paragraph; optional p animates lines rising in. Returns the last baseline y."""
    lines = wrap(ctx, s, face, size, max_width)
    for i, ln in enumerate(lines):
        la, dy = alpha, 0.0
        if p is not None:
            lp = ease_out(clamp((p - i * stagger) / 0.6))
            la, dy = alpha * lp, (1 - lp) * size * 0.35
        if la > 0:
            text(ctx, ln, x, y + i * size * leading + dy, face, size, color, align, la)
    return y + (len(lines) - 1) * size * leading

def rise(t, start, duration=0.55):
    """(alpha, dy) for a reveal that rises into place and then stays perfectly still."""
    p = ease_out(prog(t, start, duration))
    return p, (1 - p) * 18

def section(ctx, t, start, label, secondary=None, x=140, y=196, align="left"):
    """Coral uppercase section label, with an optional italic secondary line."""
    a, dy = rise(t, start)
    if a <= 0:
        return
    text(ctx, label.upper(), x, y + dy, MONO, 20, CORAL, align, a, tracking=2.0)
    if secondary:
        text(ctx, secondary, x, y + 30 + dy, SUB, 22, CORAL, align, a * 0.75)

def pair(ctx, primary, secondary, x, y, size=26, face=SANS, alpha=1.0, align="left", max_width=None, color=INK):
    """Primary line + optional italic grey secondary line. Returns bottom baseline."""
    if max_width:
        y = text_block(ctx, primary, x, y, face, size, color, max_width, 1.22, align, alpha)
    else:
        text(ctx, primary, x, y, face, size, color, align, alpha)
    if secondary:
        y2 = y + size * 1.25
        if max_width:
            return text_block(ctx, secondary, x, y2, SUB, size * 0.92, GREY, max_width, 1.22, align, alpha)
        text(ctx, secondary, x, y2, SUB, size * 0.92, GREY, align, alpha)
        return y2
    return y

def pill(ctx, label, x, y, fill, size=24, color=INK, face=SANS_MED, pad_x=18, alpha=1.0, align="left", dot=None):
    """Flat rounded label. (x, y) is top-left (or top-center). Returns width."""
    h = size * 1.8
    w = text_width(ctx, label, face, size) + pad_x * 2 + (size * 0.9 if dot else 0)
    if align == "center":
        x -= w / 2
    rounded_rect(ctx, x, y, w, h, h / 2)
    set_color(ctx, fill, alpha)
    ctx.fill()
    tx = x + pad_x
    if dot:
        disc(ctx, tx + size * 0.3, y + h / 2, size * 0.3, dot, alpha)
        tx += size * 0.9
    text(ctx, label, tx, y + h * 0.5 + size * 0.36, face, size, color, alpha=alpha)
    return w

def marker(ctx, cx, cy, r, label, fill=INK, p=1.0, color=WHITE):
    """Numbered circle marker (map / list index) with condensed numeral."""
    if p <= 0:
        return
    with pop(ctx, cx, cy, p):
        disc(ctx, cx, cy, r, fill)
        text(ctx, str(label), cx, cy + r * 0.38, NUM, r * 1.05, color, "center", label=None)

def badge(ctx, cx, cy, r, kind, p=1.0):
    """Flat status badge: check (green), cross (coral), question (gold)."""
    if p <= 0:
        return
    fill = {"check": GREEN, "cross": CORAL, "question": GOLD}[kind]
    with pop(ctx, cx, cy, prog(p, 0, 0.5)):
        disc(ctx, cx, cy, r, fill)
        mp = prog(p, 0.4, 0.6)
        if kind == "check":
            check_mark(ctx, cx, cy, r * 1.15, mp)
        elif kind == "cross":
            cross_mark(ctx, cx, cy, r * 1.15, mp)
        elif mp > 0:
            text(ctx, "?", cx, cy + r * 0.42, NUM, r * 1.3, INK, "center", alpha=mp, label=None)

def big_number(ctx, s, x, y, size, color=INK, align="left", alpha=1.0):
    return text(ctx, s, x, y, NUM, size, color, align, alpha, label=f"number:{s}")

def pointer(ctx, x, y, size=16, color=INK, alpha=1.0):
    """Small downward triangle bullet (▼) that introduces a note."""
    poly(ctx, [(x, y), (x + size, y), (x + size / 2, y + size * 0.85)], color, alpha)


# ---------------------------------------------------------------- figures
def person(ctx, x, feet_y, h, top=WHITE, bottom=BLUE, accent=CORAL, skin=SKIN, hair=DARK, shoes=DARK,
           walk=0.0, facing=1, arms="down", coat=False, hardhat=False, prop=None, alpha=1.0, seated=False,
           hair_style="short"):
    """Tall geometric editorial figure, flat fills, no outlines.

    arms: down | hold | point | wave | present | hip.  prop: folder | document | keys | tablet | magnifier.
    seated: sits on a surface at feet_y (legs forward and down).
    """
    ctx.save()
    ctx.push_group()
    ctx.translate(x, feet_y)
    ctx.scale(facing, 1)
    r = 0.062 * h
    head_cy = -h + r
    torso_top = head_cy + r + 0.035 * h
    torso_h = 0.33 * h
    hip = torso_top + torso_h
    leg_w = 0.085 * h
    swing = math.sin(walk) * 0.34
    shoe_h, shoe_w = 0.035 * h, 0.13 * h

    # legs
    if seated:
        seat = 0.0
        shift = hip - seat  # figure drawn so hips rest on the seat line
        ctx.translate(0, -shift)
        for dx, c in ((-0.02 * h, mix(bottom, DARK, 0.15)), (0.03 * h, bottom)):
            rect(ctx, dx - leg_w / 2, hip - leg_w, 0.22 * h, leg_w, c)               # thigh forward
            rect(ctx, dx + 0.22 * h - leg_w * 1.05, hip - leg_w, leg_w, 0.3 * h, c)  # shin down
            rect(ctx, dx + 0.22 * h - leg_w * 1.05, hip - leg_w + 0.3 * h - shoe_h / 2, shoe_w, shoe_h, shoes, radius=shoe_h / 2)
    else:
        leg_len = -hip - shoe_h * 0.6
        for sign, c in ((-1, mix(bottom, DARK, 0.15)), (1, bottom)):
            angle = swing * sign
            ctx.save()
            ctx.translate(sign * 0.05 * h * 0.9, hip)
            ctx.rotate(-angle)
            rect(ctx, -leg_w / 2, -0.01 * h, leg_w, leg_len, c)
            rect(ctx, -leg_w / 2, leg_len - shoe_h * 0.4, shoe_w, shoe_h, shoes, radius=shoe_h / 2)
            ctx.restore()

    # torso (and coat skirt)
    tw = 0.3 * h
    coat_len = 0.2 * h if coat else 0.0
    ctx.new_path()
    ctx.move_to(-tw / 2, torso_top + 0.04 * h)
    ctx.curve_to(-tw / 2, torso_top, -tw / 2 + 0.01 * h, torso_top, -tw / 2 + 0.05 * h, torso_top)
    ctx.line_to(tw / 2 - 0.05 * h, torso_top)
    ctx.curve_to(tw / 2 - 0.01 * h, torso_top, tw / 2, torso_top, tw / 2, torso_top + 0.04 * h)
    ctx.line_to(tw / 2 * (1.05 if coat else 0.92), hip + coat_len)
    ctx.line_to(-tw / 2 * (1.05 if coat else 0.92), hip + coat_len)
    ctx.close_path()
    set_color(ctx, top)
    ctx.fill()
    # shirt V and collar accent
    poly(ctx, [(-0.045 * h, torso_top), (0.045 * h, torso_top), (0, torso_top + 0.1 * h)], accent)
    if coat:
        line(ctx, [(0, torso_top + 0.1 * h), (0, hip + coat_len)], mix(top, INK, 0.18), 2)
        rect(ctx, 0.05 * h, torso_top + 0.13 * h, 0.05 * h, 0.012 * h, mix(top, INK, 0.25))  # pocket badge
    # neck
    rect(ctx, -0.022 * h, head_cy + r * 0.6, 0.044 * h, 0.05 * h, skin)

    # arms: rounded bars in the torso colour, skin hands
    shoulder_y = torso_top + 0.03 * h
    arm_len = 0.34 * h
    arm_w = 0.07 * h
    poses = {"down": (-0.05 + swing * 0.7, -0.05 - swing * 0.7), "hold": (1.2, 0.9), "point": (1.55, 0.05),
             "wave": (2.75, 0.05), "present": (1.0, 0.12), "hip": (0.1, -0.5)}
    front, back = poses.get(arms, poses["down"])
    hands = []
    for sx, angle, shade in ((-tw / 2 + 0.02 * h, back, mix(top, DARK, 0.12)), (tw / 2 - 0.02 * h, front, top)):
        ex = sx + math.sin(angle) * arm_len
        ey = shoulder_y + math.cos(angle) * arm_len
        ctx.new_path()
        ctx.move_to(sx, shoulder_y)
        ctx.line_to(ex, ey)
        ctx.set_line_width(arm_w)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        set_color(ctx, shade)
        ctx.stroke()
        disc(ctx, ex, ey, 0.03 * h, skin)
        hands.append((ex, ey))
    fx, fy = hands[1]
    if prop == "folder":
        rect(ctx, fx - 0.02 * h, fy - 0.1 * h, 0.16 * h, 0.12 * h, RED)
    elif prop == "document":
        rect(ctx, fx - 0.01 * h, fy - 0.14 * h, 0.12 * h, 0.16 * h, WHITE)
        for k in range(3):
            line(ctx, [(fx + 0.01 * h, fy - 0.1 * h + k * 0.035 * h), (fx + 0.09 * h, fy - 0.1 * h + k * 0.035 * h)], RULE, 2)
    elif prop == "keys":
        disc(ctx, fx + 0.03 * h, fy + 0.02 * h, 0.022 * h, GOLD)
        rect(ctx, fx + 0.03 * h, fy + 0.012 * h, 0.07 * h, 0.014 * h, GOLD)
    elif prop == "tablet":
        rect(ctx, fx - 0.01 * h, fy - 0.12 * h, 0.12 * h, 0.15 * h, INK, radius=0.01 * h)
    elif prop == "magnifier":
        line(ctx, [(fx, fy), (fx + 0.05 * h, fy - 0.07 * h)], DARK, 0.018 * h)
        ctx.new_path()
        ctx.arc(fx + 0.075 * h, fy - 0.11 * h, 0.04 * h, 0, 2 * math.pi)
        set_color(ctx, SKY, 0.8)
        ctx.fill_preserve()
        set_color(ctx, DARK)
        ctx.set_line_width(0.012 * h)
        ctx.stroke()

    # head: skin disc, nose, eye, hair
    disc(ctx, 0, head_cy, r, skin)
    poly(ctx, [(r * 0.85, head_cy - r * 0.15), (r * 1.25, head_cy + r * 0.2), (r * 0.8, head_cy + r * 0.25)], skin)
    disc(ctx, r * 0.45, head_cy - r * 0.1, r * 0.09, DARK)
    ctx.new_path()
    if hardhat:
        ctx.arc(0, head_cy - r * 0.15, r * 1.05, math.pi, 2 * math.pi)
        ctx.close_path()
        set_color(ctx, GOLD)
        ctx.fill()
        rect(ctx, -r * 1.2, head_cy - r * 0.2, r * 2.6, r * 0.22, mix(GOLD, DARK, 0.2), radius=r * 0.1)
    elif hair_style == "bun":
        ctx.arc(0, head_cy, r * 1.02, math.pi * 0.95, math.pi * 1.95)
        ctx.close_path()
        set_color(ctx, hair)
        ctx.fill()
        disc(ctx, -r * 0.95, head_cy - r * 0.55, r * 0.42, hair)
    else:
        ctx.arc(0, head_cy, r * 1.02, math.pi * 0.9, math.pi * 1.9)
        ctx.line_to(-r * 0.2, head_cy - r * 0.2)
        ctx.line_to(-r * 1.0, head_cy + r * 0.25)
        ctx.close_path()
        set_color(ctx, hair)
        ctx.fill()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(alpha)
    ctx.restore()


# ---------------------------------------------------------------- architecture
def window_grid(ctx, x, y, w, h, cols, rows, color, gap=0.35):
    """Fine window rhythm drawn as small flat bars (the facade texture)."""
    cw, rh = w / cols, h / rows
    for r in range(rows):
        for c in range(cols):
            rect(ctx, x + c * cw + cw * gap / 2, y + r * rh + rh * 0.18, cw * (1 - gap), rh * 0.62, color)

def facade(ctx, x, base, w, h, color, style="grid", p=1.0, dim=0.0):
    """Flat building. style: grid (modern block) | colonial (arcade + balconies) | market (arched hall).
    p grows it from the ground; dim fades it toward the quiet grey (a 'weak' street)."""
    if p <= 0:
        return
    body = mix(color, RULE, dim)
    dark = mix(body, INK, 0.28)
    light = mix(body, WHITE, 0.45)
    top = base - h
    with grow(ctx, x + w / 2, base, p):
        rect(ctx, x, top, w, h, body)
        if style == "grid":
            rect(ctx, x - 4, top, w + 8, h * 0.05, dark)
            window_grid(ctx, x + w * 0.08, top + h * 0.1, w * 0.84, h * 0.7, max(3, int(w / 34)), max(4, int(h / 46)), light)
            rect(ctx, x + w * 0.4, base - h * 0.14, w * 0.2, h * 0.14, dark)
        elif style == "colonial":
            rect(ctx, x - w * 0.03, top - h * 0.05, w * 1.06, h * 0.06, dark)
            poly(ctx, [(x + w * 0.35, top - h * 0.05), (x + w * 0.5, top - h * 0.15), (x + w * 0.65, top - h * 0.05)], dark)
            bay = w / 3
            for i in range(3):
                wx = x + bay * i + bay * 0.28
                rect(ctx, wx, top + h * 0.12, bay * 0.44, h * 0.26, light)
                rect(ctx, wx - bay * 0.08, top + h * 0.38, bay * 0.6, h * 0.025, dark)
                ax, aw, ah = x + bay * i + bay * 0.18, bay * 0.64, h * 0.36
                ctx.new_path()
                ctx.move_to(ax, base)
                ctx.line_to(ax, base - ah + aw / 2)
                ctx.arc(ax + aw / 2, base - ah + aw / 2, aw / 2, math.pi, 2 * math.pi)
                ctx.line_to(ax + aw, base)
                ctx.close_path()
                set_color(ctx, dark if i == 1 else light)
                ctx.fill()
        elif style == "market":
            rect(ctx, x - 6, top, w + 12, h * 0.08, dark)
            for i in range(4):
                ax, aw = x + w * (0.06 + i * 0.235), w * 0.19
                ctx.new_path()
                ctx.move_to(ax, base - h * 0.08)
                ctx.line_to(ax, base - h * 0.55 + aw / 2)
                ctx.arc(ax + aw / 2, base - h * 0.55 + aw / 2, aw / 2, math.pi, 2 * math.pi)
                ctx.line_to(ax + aw, base - h * 0.08)
                ctx.close_path()
                set_color(ctx, light)
                ctx.fill()
            window_grid(ctx, x + w * 0.08, top + h * 0.12, w * 0.84, h * 0.2, 8, 1, light)

def storefront(ctx, x, base, w, h, color, awning=CORAL, p=1.0, sign=None):
    if p <= 0:
        return
    top = base - h
    dark = mix(color, INK, 0.28)
    with grow(ctx, x + w / 2, base, p):
        rect(ctx, x, top, w, h, color)
        rect(ctx, x + w * 0.08, top + h * 0.08, w * 0.84, h * 0.16, WHITE)
        # striped awning (diagonal stripes, flat)
        ay, ah = top + h * 0.3, h * 0.12
        rect(ctx, x - w * 0.03, ay, w * 1.06, ah, awning)
        ctx.save()
        ctx.rectangle(x - w * 0.03, ay, w * 1.06, ah)
        ctx.clip()
        for k in range(-2, 14):
            sx = x + k * w * 0.1
            poly(ctx, [(sx, ay + ah), (sx + w * 0.04, ay + ah), (sx + w * 0.04 + ah, ay), (sx + ah, ay)], WHITE, 0.55)
        ctx.restore()
        rect(ctx, x + w * 0.08, top + h * 0.52, w * 0.5, h * 0.34, SKY)
        rect(ctx, x + w * 0.66, top + h * 0.5, w * 0.24, h * 0.5, dark)
        if sign:
            text(ctx, sign, x + w / 2, top + h * 0.2, SANS_SEMI, h * 0.075, INK, "center", tracking=h * 0.008, label=None)

def crane(ctx, x, base, h, p=1.0, hook=0.5, color=INK):
    """Tower crane in hairlines (like the fine instruments in the reference spreads)."""
    m = h * 0.035
    top = base - h
    pm, pj, pt = clamp(p * 2.2), clamp(p * 2.2 - 1.0), clamp(p * 2.2 - 1.6)
    for dx in (-m, m):
        line(ctx, partial_polyline([(x + dx, base), (x + dx, top)], pm), color, 2.2)
    zig = [(x + (m if i % 2 else -m), base - h * i / 12) for i in range(13)]
    line(ctx, partial_polyline(zig, pm), color, 1.4)
    line(ctx, partial_polyline([(x - h * 0.24, top), (x + h * 0.72, top)], pj), color, 2.2)
    line(ctx, partial_polyline([(x - h * 0.24, top + h * 0.035), (x + h * 0.72, top + h * 0.035)], pj), color, 1.4)
    line(ctx, partial_polyline([(x - h * 0.24, top), (x, top - h * 0.14), (x + h * 0.72, top)], pt), color, 1.4)
    if pj >= 1:
        rect(ctx, x - h * 0.23, top + h * 0.035, h * 0.09, h * 0.08, RED)
    if pt >= 1:
        hx, hy = x + h * 0.5, top + h * 0.12 + h * 0.4 * hook
        line(ctx, [(hx, top + h * 0.035), (hx, hy)], color, 1.4)
        rect(ctx, hx - h * 0.07, hy, h * 0.14, h * 0.07, GOLD)

def scaffold(ctx, x, base, w, h, p=1.0):
    levels = 4
    for i in range(levels + 1):
        yy = base - h * i / levels
        line(ctx, partial_polyline([(x, yy), (x + w, yy)], clamp(p * 2 - i * 0.2)), INK, 2)
    for j in range(4):
        xx = x + w * j / 3
        line(ctx, partial_polyline([(xx, base), (xx, base - h)], clamp(p * 1.6 - j * 0.1)), INK, 2)
    for i in range(levels):
        for j in range(3):
            if (i + j) % 2 == 0:
                a = (x + w * j / 3, base - h * i / levels)
                b = (x + w * (j + 1) / 3, base - h * (i + 1) / levels)
                line(ctx, partial_polyline([a, b], clamp(p * 2 - 1 - i * 0.1)), INK, 1.2)

def tree(ctx, x, base, h, color=GREEN):
    rect(ctx, x - h * 0.04, base - h * 0.4, h * 0.08, h * 0.4, mix(color, DARK, 0.4))
    disc(ctx, x, base - h * 0.62, h * 0.3, color)

def lamp(ctx, x, base, h):
    line(ctx, [(x, base), (x, base - h)], DARK, 2.4)
    disc(ctx, x, base - h, h * 0.07, GOLD)


# ---------------------------------------------------------------- documents & icons
def document(ctx, x, y, w, h, lines=5, p=1.0, rotate=0.0, fill=WHITE):
    if p <= 0:
        return
    ctx.save()
    ctx.translate(x + w / 2, y + h / 2)
    ctx.rotate(rotate)
    ctx.translate(-w / 2, -h / 2)
    fold = w * 0.2
    poly(ctx, [(0, 0), (w - fold, 0), (w, fold), (w, h), (0, h)], fill, p)
    poly(ctx, [(w - fold, 0), (w, fold), (w - fold, fold)], RULE, p)
    for i in range(lines):
        lw = w * (0.55 if i % 3 == 2 else 0.72) * clamp(p * 1.5 - i * 0.1)
        rect(ctx, w * 0.13, h * 0.24 + i * h * 0.12, lw, h * 0.03, RULE)
    ctx.restore()

def stamp(ctx, cx, cy, r, p, label="QUALIFIED", fill=GREEN):
    """Approval stamp that lands with a small overshoot."""
    if p <= 0:
        return
    s = lerp(1.6, 1.0, ease_back(clamp(p / 0.6), 1.2))
    a = clamp(p / 0.25)
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(-0.16)
    ctx.scale(s, s)
    disc(ctx, 0, 0, r, fill, a)
    ctx.new_path()
    ctx.arc(0, 0, r * 0.8, 0, 2 * math.pi)
    set_color(ctx, WHITE, 0.6 * a)
    ctx.set_line_width(2)
    ctx.stroke()
    check_mark(ctx, 0, -r * 0.16, r * 0.6, clamp((p - 0.4) / 0.4))
    text(ctx, label, 0, r * 0.5, SANS_SEMI, r * 0.19, WHITE, "center", alpha=a, tracking=r * 0.02, label=None)
    ctx.restore()

def calendar(ctx, x, y, w, h, crossed=0.0, head=CORAL):
    rect(ctx, x, y, w, h, WHITE)
    rect(ctx, x, y, w, h * 0.24, head)
    for i in range(3):
        for j in range(4):
            cx, cy = x + w * (0.13 + j * 0.2), y + h * (0.36 + i * 0.2)
            n = i * 4 + j
            rect(ctx, cx, cy, w * 0.14, h * 0.12, CORAL if n < crossed * 12 else RULE)
    for dx in (0.28, 0.72):
        line(ctx, [(x + w * dx, y - h * 0.08), (x + w * dx, y + h * 0.1)], DARK, 4)

def utility_pole(ctx, x, base, h, p=1.0, sway=0.0):
    line(ctx, partial_polyline([(x, base), (x, base - h)], clamp(p * 2)), DARK, 4)
    line(ctx, partial_polyline([(x - h * 0.22, base - h * 0.88), (x + h * 0.22, base - h * 0.88)], clamp(p * 2 - 0.6)), DARK, 3.4)
    for dx in (-0.18, 0.0, 0.18):
        if p > 0.6:
            sx, sy = x + h * dx, base - h * 0.88
            ex, ey = x + h * 0.95, base - h * (0.62 + dx * 0.2)
            pts = [(sx + (ex - sx) * k / 12, sy + (ey - sy) * k / 12 + math.sin(math.pi * k / 12) * h * (0.08 + sway * 0.03))
                   for k in range(13)]
            line(ctx, partial_polyline(pts, clamp((p - 0.6) / 0.4)), INK, 1.4)
        disc(ctx, x + h * dx, base - h * 0.9, h * 0.024, GOLD)

def aurora_mark(ctx, cx, cy, size, reverse=False):
    """The locked Aurora mark (DS-AUR-005 §2): twelve heritage-spectrum ticks on a faint ring.
    Drawn from the 72-unit master: ring r28, ticks from r22 to r30, stroke 5.5, round caps."""
    k = size / 72.0
    ctx.save()
    ctx.translate(cx, cy)
    ctx.new_path()
    ctx.arc(0, 0, 28 * k, 0, 2 * math.pi)
    set_color(ctx, LOGO_CREAM if reverse else LOGO_INK, 0.18 if reverse else 0.14)
    ctx.set_line_width(max(1.0, 1 * k))
    ctx.stroke()
    for i, color in enumerate(HERITAGE):
        angle = math.radians(i * 30)
        s, c = math.sin(angle), -math.cos(angle)
        line(ctx, [(s * 22 * k, c * 22 * k), (s * 30 * k, c * 30 * k)], color, 5.5 * k)
    ctx.restore()

def wordmark(ctx, x, y, size, reverse=False, alpha=1.0, align="left", mark=True):
    """Aurora lockup: mark + 'aur·o·ra' in Fraunces 300 (opsz 144, SOFT 20), italic amber 'o'.
    y is the text baseline; proportions follow the reference lockup (mark 104 : wordmark 62, gap 22)."""
    ink = LOGO_CREAM if reverse else LOGO_INK
    amber = AMBER_LT if reverse else AMBER_DK
    mark_size = size * 104 / 62 if mark else 0
    gap = size * 22 / 62 if mark else 0
    parts = [("aur", "AuroraWordmark", ink), ("o", "AuroraWordmarkItal", amber), ("ra", "AuroraWordmark", ink)]
    word_w = sum(text_width(ctx, s, face, size) for s, face, _ in parts)
    total = mark_size + gap + word_w
    if align == "center":
        x -= total / 2
    ctx.save()
    ctx.push_group()
    if mark:
        aurora_mark(ctx, x + mark_size / 2, y - size * 0.3, mark_size, reverse)
    cursor = x + mark_size + gap
    for s, face, color in parts:
        cursor += text(ctx, s, cursor, y, face, size, color, label="wordmark")
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(alpha)
    ctx.restore()
    return total


# ---------------------------------------------------------------- block map
class CityPlan:
    """Abstract street grid. Blocks inside the defined perimeter fill orange; the rest stay quiet grey.
    White gaps between blocks read as streets, exactly like the district maps in the reference."""
    def __init__(self, x, y, w, h, cols=8, rows=6, gap=7,
                 perimeter=((1, 1), (6, 1), (6, 2), (7, 2), (7, 5), (3, 5), (3, 4), (1, 4))):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.cols, self.rows, self.gap = cols, rows, gap
        self.bw = (w - (cols - 1) * gap) / cols
        self.bh = (h - (rows - 1) * gap) / rows
        self.perimeter = [self.node(c, r) for c, r in perimeter]

    def node(self, c, r):
        return (self.x + c * (self.bw + self.gap) - self.gap / 2, self.y + r * (self.bh + self.gap) - self.gap / 2)

    def block_rect(self, c, r):
        return (self.x + c * (self.bw + self.gap), self.y + r * (self.bh + self.gap), self.bw, self.bh)

    def block_center(self, c, r):
        bx, by, bw, bh = self.block_rect(c, r)
        return bx + bw / 2, by + bh / 2

    def inside(self, c, r):
        px, py = self.block_center(c, r)
        poly_, hit = self.perimeter, False
        for i in range(len(poly_)):
            (x1, y1), (x2, y2) = poly_[i], poly_[(i + 1) % len(poly_)]
            if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
                hit = not hit
        return hit

    def draw(self, ctx, t_grid=1.0, t_fill=1.0, zone=ORANGE, quiet=RULE, highlight=None, t_outline=0.0):
        blocks = [(c, r) for r in range(self.rows) for c in range(self.cols)]
        for i, (c, r) in enumerate(blocks):
            bp = clamp(t_grid * 1.8 - (c + r) / (self.cols + self.rows) * 0.8)
            if bp <= 0:
                continue
            bx, by, bw, bh = self.block_rect(c, r)
            color = quiet
            if self.inside(c, r):
                fp = ease_out(clamp(t_fill * 1.8 - (c + r) / (self.cols + self.rows) * 0.8))
                color = mix(quiet, zone, fp)
            if highlight and (c, r) in highlight:
                hc, hp = highlight[(c, r)]
                color = mix(color, hc, ease_out(clamp(hp)))
            with pop(ctx, bx + bw / 2, by + bh / 2, bp, 1.1):
                rect(ctx, bx, by, bw, bh, color)
        if t_outline > 0:  # optional coral trace of the perimeter
            line(ctx, partial_polyline(self.perimeter, t_outline, closed=True), CORAL, 2.4, dash=[10, 7])
