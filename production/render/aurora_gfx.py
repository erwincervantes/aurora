"""Aurora editorial illustration toolkit (pycairo).

Brand constants, easing, text with bounds QC, progressive line drawing, and the
geometric illustration components shared by the YouTube film, the Short, and the thumbnail.
"""
import math
import cairo

# ---------------------------------------------------------------- brand system
def hex_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))

NAVY = hex_rgb("#1A2236")        # ink: text and outlines
CREAM = hex_rgb("#F7F2E8")       # paper background
# Illustration panels: saturated mid-tones from Salvadoran colonial facades. Validated as a set
# (lightness band, chroma, CVD separation >= 10 dE) and each carries navy text at >= 4.7:1.
TEAL = hex_rgb("#2E9E8A")
TERRACOTTA = hex_rgb("#E5634F")
OCHRE = hex_rgb("#E2A41C")
COBALT = hex_rgb("#5E93E0")
PAPER = hex_rgb("#ECE3D3")       # secondary surface one step darker than cream (flat, no gradient)

FONT_HEAD = "AuroraFrauncesSemi"   # Fraunces 600, opsz 72, SOFT 0, WONK 0 (static instance)
FONT_HEAD_REG = "AuroraFrauncesReg"  # Fraunces 400
FONT_BODY = "AuroraGeistReg"       # Geist 400
FONT_BODY_MED = "AuroraGeistMed"   # Geist 500
FONT_BODY_SEMI = "AuroraGeistSemi" # Geist 600

LINE = 3.0  # standard outline weight at 1080p: thin, precise, still survives YouTube compression


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
    """Collects device-space text boxes each frame so we can flag clipping and caption collisions."""
    width = 1920
    height = 1080
    safe_margin = 40
    caption_zone = None     # (x0, y0, x1, y1) reserved for captions
    boxes = []

    @classmethod
    def reset(cls):
        cls.boxes = []

    @classmethod
    def register(cls, ctx, x0, y0, x1, y1, label, is_caption=False):
        cx0, cy0, cx1, cy1 = ctx.clip_extents()  # only the visible (unclipped) part of the text counts
        x0, y0, x1, y1 = max(x0, cx0), max(y0, cy0), min(x1, cx1), min(y1, cy1)
        if x1 <= x0 or y1 <= y0:
            return
        corners = [ctx.user_to_device(x, y) for x, y in ((x0, y0), (x1, y0), (x0, y1), (x1, y1))]
        xs = [c[0] for c in corners]
        ys = [c[1] for c in corners]
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


# ---------------------------------------------------------------- color / primitives
def set_color(ctx, color, alpha=1.0):
    ctx.set_source_rgba(color[0], color[1], color[2], alpha)

def rounded_rect(ctx, x, y, w, h, r):
    r = max(0.0, min(r, w / 2, h / 2))
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()

def path_length(ctx):
    total, last, start = 0.0, None, None
    for kind, points in ctx.copy_path_flat():
        if kind == cairo.PATH_MOVE_TO:
            last = start = points
        elif kind == cairo.PATH_LINE_TO:
            total += math.dist(last, points)
            last = points
        elif kind == cairo.PATH_CLOSE_PATH and last and start:
            total += math.dist(last, start)
            last = start
    return total

class Shape:
    """One drawable element: a path builder plus optional fill; outlines draw progressively."""
    def __init__(self, build, fill=None, stroke=True, line_width=None, fill_alpha=1.0, stroke_color=None):
        self.build = build
        self.fill = fill
        self.stroke = stroke
        self.line_width = line_width
        self.fill_alpha = fill_alpha
        self.stroke_color = stroke_color

def draw_shapes(ctx, shapes, line_p=1.0, fill_p=1.0, line_width=LINE, color=NAVY):
    """Fill (fading in with fill_p) then stroke outlines sequentially up to line_p of their total length."""
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    if fill_p > 0:
        for shape in shapes:
            if shape.fill is not None:
                ctx.new_path()
                shape.build(ctx)
                set_color(ctx, shape.fill, shape.fill_alpha * clamp(fill_p))
                ctx.fill()
    if line_p <= 0:
        ctx.new_path()
        return
    lengths = []
    for shape in shapes:
        if shape.stroke:
            ctx.new_path()
            shape.build(ctx)
            lengths.append((shape, path_length(ctx)))
    budget = sum(length for _, length in lengths) * clamp(line_p)
    for shape, length in lengths:
        if budget <= 0:
            break
        ctx.new_path()
        shape.build(ctx)
        ctx.set_line_width(shape.line_width or line_width)
        set_color(ctx, shape.stroke_color or color)
        if budget < length:
            ctx.set_dash([budget, length + 20])
        ctx.stroke()
        ctx.set_dash([])
        budget -= length
    ctx.new_path()

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

def stroke_polyline(ctx, points, color=NAVY, width=LINE, dash=None, alpha=1.0):
    if len(points) < 2:
        return
    ctx.new_path()
    ctx.move_to(*points[0])
    for p in points[1:]:
        ctx.line_to(*p)
    ctx.set_line_width(width)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    set_color(ctx, color, alpha)
    if dash:
        ctx.set_dash(dash)
    ctx.stroke()
    ctx.set_dash([])

def check_mark(ctx, cx, cy, size, p=1.0, color=NAVY, width=None):
    points = [(cx - size * 0.42, cy + size * 0.02), (cx - size * 0.12, cy + size * 0.32), (cx + size * 0.45, cy - size * 0.33)]
    stroke_polyline(ctx, partial_polyline(points, p), color, width or max(3, size * 0.16))

def cross_mark(ctx, cx, cy, size, p=1.0, color=NAVY, width=None):
    s = size * 0.36
    w = width or max(3, size * 0.15)
    stroke_polyline(ctx, partial_polyline([(cx - s, cy - s), (cx + s, cy + s)], clamp(p * 2)), color, w)
    stroke_polyline(ctx, partial_polyline([(cx + s, cy - s), (cx - s, cy + s)], clamp(p * 2 - 1)), color, w)

def badge(ctx, cx, cy, r, fill, p=1.0, mark="check"):
    """Circle badge that pops in, then draws its mark."""
    scale = ease_back(prog(p, 0, 0.5))
    if scale <= 0:
        return
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(scale, scale)
    ctx.arc(0, 0, r, 0, 2 * math.pi)
    set_color(ctx, fill)
    ctx.fill_preserve()
    set_color(ctx, NAVY)
    ctx.set_line_width(LINE)
    ctx.stroke()
    mp = prog(p, 0.45, 0.55)
    if mark == "check":
        check_mark(ctx, 0, 0, r * 1.1, mp)
    elif mark == "cross":
        cross_mark(ctx, 0, 0, r * 1.1, mp)
    elif mark == "question":
        if mp > 0:
            text(ctx, "?", 0, r * 0.36, FONT_HEAD, r * 1.15, NAVY, align="center", alpha=mp, label=None)
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

def text(ctx, s, x, y, face, size, color=NAVY, align="left", alpha=1.0, tracking=0.0, label="text", is_caption=False):
    """Draw one line with baseline at y. Returns the drawn width."""
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

def text_block(ctx, s, x, y, face, size, color=NAVY, max_width=800, leading=1.18, align="left", alpha=1.0, p=None, stagger=0.12):
    """Wrapped paragraph; optional p (0..1+) animates each line rising in. Returns bottom baseline y."""
    lines = wrap(ctx, s, face, size, max_width)
    for i, line in enumerate(lines):
        line_alpha, dy = alpha, 0.0
        if p is not None:
            lp = ease_out(clamp((p - i * stagger) / 0.6))
            line_alpha, dy = alpha * lp, (1 - lp) * size * 0.35
        if line_alpha > 0:
            text(ctx, line, x, y + i * size * leading + dy, face, size, color, align, line_alpha)
    return y + (len(lines) - 1) * size * leading

def rise(ctx, t, start, duration=0.55):
    """(alpha, dy) for a reveal that rises into place and then stays perfectly still."""
    p = ease_out(prog(t, start, duration))
    return p, (1 - p) * 18

def chip(ctx, label, x, y, fill, size=24, face=FONT_BODY_MED, pad_x=18, height=None, alpha=1.0, align="left"):
    """Rounded label pill. (x, y) is top-left (or top-center with align='center'). Returns width."""
    height = height or size * 1.9
    width = text_width(ctx, label, face, size) + pad_x * 2
    if align == "center":
        x -= width / 2
    rounded_rect(ctx, x, y, width, height, height / 2)
    set_color(ctx, fill, alpha)
    ctx.fill_preserve()
    set_color(ctx, NAVY, alpha)
    ctx.set_line_width(LINE * 0.8)
    ctx.stroke()
    text(ctx, label, x + pad_x, y + height * 0.5 + size * 0.36, face, size, NAVY, alpha=alpha)
    return width

def kicker(ctx, label, x, y, alpha=1.0, color=NAVY, size=20, align="left"):
    return text(ctx, label.upper(), x, y, FONT_BODY_SEMI, size, color, align=align, alpha=alpha, tracking=size * 0.14)


# ---------------------------------------------------------------- panels
def panel(ctx, x, y, w, h, fill, p=1.0, direction="up", radius=0, outline=True, line_p=None):
    """Flat color panel revealed by a wipe (the SURES-style colored block)."""
    if p <= 0:
        return
    e = ease_in_out(clamp(p))
    ctx.save()
    if direction == "up":
        ctx.rectangle(x - 4, y + h * (1 - e) - 4, w + 8, h * e + 8)
    elif direction == "down":
        ctx.rectangle(x - 4, y - 4, w + 8, h * e + 8)
    elif direction == "right":
        ctx.rectangle(x - 4, y - 4, w * e + 8, h + 8)
    else:
        ctx.rectangle(x + w * (1 - e) - 4, y - 4, w * e + 8, h + 8)
    ctx.clip()
    rounded_rect(ctx, x, y, w, h, radius) if radius else ctx.rectangle(x, y, w, h)
    set_color(ctx, fill)
    ctx.fill()
    ctx.restore()
    if outline:
        lp = clamp((line_p if line_p is not None else p) * 1.0)
        pts = [(x, y + h), (x, y), (x + w, y), (x + w, y + h)]
        if radius:
            draw_shapes(ctx, [Shape(lambda c: rounded_rect(c, x, y, w, h, radius))], lp, 0)
        else:
            stroke_polyline(ctx, partial_polyline(pts, lp, closed=True))

def ground_line(ctx, x0, x1, y, p=1.0):
    stroke_polyline(ctx, partial_polyline([(x0, y), (x1, y)], p))


# ---------------------------------------------------------------- figures
def person(ctx, x, feet_y, h, shirt, walk=0.0, facing=1, arms="down", hardhat=False, apron=False,
           prop=None, alpha=1.0, hair=NAVY, seated=False):
    """Geometric editorial figure. walk is a phase in radians; arms: down|hold|point|wave|present."""
    ctx.save()
    ctx.push_group()
    ctx.translate(x, feet_y)
    ctx.scale(facing, 1)
    r = 0.095 * h
    head_y = -h + r
    torso_top = head_y + r + 0.035 * h
    torso_h = 0.36 * h
    hip_y = torso_top + torso_h
    leg_w = 0.075 * h
    swing = math.sin(walk) * 0.38

    # legs (navy trousers)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    set_color(ctx, NAVY)
    ctx.set_line_width(leg_w)
    if seated:
        for dx in (-0.05 * h, 0.05 * h):
            ctx.move_to(dx, hip_y - 0.02 * h)
            ctx.line_to(dx + 0.22 * h, hip_y - 0.02 * h)
            ctx.line_to(dx + 0.22 * h, 0)
            ctx.stroke()
    else:
        leg_len = -hip_y - leg_w * 0.4
        for sign in (1, -1):
            angle = swing * sign
            ctx.move_to(sign * 0.04 * h, hip_y)
            ctx.line_to(sign * 0.04 * h + math.sin(angle) * leg_len, hip_y + math.cos(angle) * leg_len)
            ctx.stroke()

    # torso: trapezoid with rounded shoulders
    top_w, bot_w = 0.27 * h, 0.22 * h
    def torso(c):
        c.new_sub_path()
        c.move_to(-bot_w / 2, hip_y)
        c.line_to(-top_w / 2, torso_top + 0.05 * h)
        c.curve_to(-top_w / 2, torso_top, -top_w / 2, torso_top, -top_w / 2 + 0.05 * h, torso_top)
        c.line_to(top_w / 2 - 0.05 * h, torso_top)
        c.curve_to(top_w / 2, torso_top, top_w / 2, torso_top, top_w / 2, torso_top + 0.05 * h)
        c.line_to(bot_w / 2, hip_y)
        c.close_path()
    draw_shapes(ctx, [Shape(torso, fill=shirt)], 1, 1, line_width=LINE * 0.9)
    if apron:
        def apron_shape(c):
            c.rectangle(-bot_w * 0.36, torso_top + torso_h * 0.35, bot_w * 0.72, torso_h * 0.75)
        draw_shapes(ctx, [Shape(apron_shape, fill=CREAM)], 1, 1, line_width=LINE * 0.8)

    # arms: outlined limbs (navy stroke under shirt-colored stroke)
    shoulder_y = torso_top + 0.04 * h
    arm_len = 0.33 * h
    # angle from straight-down; positive swings toward the facing direction
    poses = {"down": (-0.12 + swing * 0.6, -0.12 - swing * 0.6), "hold": (1.15, 0.95), "point": (1.5, 0.08),
             "wave": (2.7, 0.08), "present": (1.0, 0.15)}
    front_angle, back_angle = poses.get(arms, poses["down"])
    for sx, angle in ((top_w / 2 - 0.03 * h, front_angle), (-top_w / 2 + 0.03 * h, back_angle)):
        splay = 0.06 * h * (1 if sx > 0 else -1) if arms == "down" else 0.0
        ex = sx + math.sin(angle) * arm_len + splay
        ey = shoulder_y + math.cos(angle) * arm_len
        for width, color in ((0.07 * h + 2 * LINE * 0.8, NAVY), (0.07 * h, shirt)):
            ctx.set_line_width(width)
            set_color(ctx, color)
            ctx.move_to(sx, shoulder_y)
            ctx.line_to(ex, ey)
            ctx.stroke()
    if prop == "folder":
        def folder(c):
            c.rectangle(0.1 * h, torso_top + 0.1 * h, 0.2 * h, 0.15 * h)
        draw_shapes(ctx, [Shape(folder, fill=OCHRE)], 1, 1, line_width=LINE * 0.8)
    elif prop == "tablet":
        def tablet(c):
            rounded_rect(c, 0.08 * h, torso_top + 0.08 * h, 0.16 * h, 0.2 * h, 0.02 * h)
        draw_shapes(ctx, [Shape(tablet, fill=COBALT)], 1, 1, line_width=LINE * 0.8)

    # head + hair cap
    def head(c):
        c.arc(0, head_y, r, 0, 2 * math.pi)
    draw_shapes(ctx, [Shape(head, fill=CREAM)], 1, 1, line_width=LINE * 0.9)
    ctx.new_path()
    if hardhat:
        ctx.arc(0, head_y - r * 0.05, r * 1.08, math.pi, 2 * math.pi)
        ctx.rectangle(-r * 1.3, head_y - r * 0.12, r * 2.6, r * 0.22)
        set_color(ctx, OCHRE)
        ctx.fill_preserve()
        set_color(ctx, NAVY)
        ctx.set_line_width(LINE * 0.8)
        ctx.stroke()
    else:
        ctx.arc(0, head_y, r, math.pi * 1.02, math.pi * 1.98)
        ctx.curve_to(r * 0.9, head_y - r * 0.2, r * 0.2, head_y - r * 0.55, -r * 0.3, head_y - r * 0.3)
        ctx.close_path()
        set_color(ctx, hair)
        ctx.fill()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(alpha)
    ctx.restore()


# ---------------------------------------------------------------- architecture
def historic_facade(ctx, x, base_y, w, h, body=OCHRE, line_p=1.0, fill_p=1.0, window_fill=COBALT, shutters=0.0):
    """Colonial two-storey facade with ground-floor arcade: the Historic Center's building type."""
    top = base_y - h
    arcade_h = h * 0.42
    shapes = []
    shapes.append(Shape(lambda c: c.rectangle(x, top, w, h), fill=body))
    shapes.append(Shape(lambda c: c.rectangle(x - w * 0.03, top - h * 0.05, w * 1.06, h * 0.05), fill=CREAM))
    def pediment(c):
        c.move_to(x + w * 0.36, top - h * 0.05)
        c.line_to(x + w * 0.5, top - h * 0.16)
        c.line_to(x + w * 0.64, top - h * 0.05)
        c.close_path()
    shapes.append(Shape(pediment, fill=CREAM))
    shapes.append(Shape(lambda c: (c.move_to(x, base_y - arcade_h), c.line_to(x + w, base_y - arcade_h))))
    bay_w = w / 3
    for i in range(3):
        ax = x + bay_w * i + bay_w * 0.16
        aw = bay_w * 0.68
        ah = arcade_h * 0.8
        def arch(c, ax=ax, aw=aw, ah=ah):
            c.move_to(ax, base_y)
            c.line_to(ax, base_y - ah + aw / 2)
            c.arc(ax + aw / 2, base_y - ah + aw / 2, aw / 2, math.pi, 2 * math.pi)
            c.line_to(ax + aw, base_y)
        shapes.append(Shape(arch, fill=NAVY if i == 1 else CREAM))
        wx = x + bay_w * i + bay_w * 0.26
        ww = bay_w * 0.48
        wy = top + h * 0.12
        wh = h * 0.3
        fill = NAVY if shutters > (i + 1) / 3.5 else window_fill
        shapes.append(Shape(lambda c, wx=wx, wy=wy, ww=ww, wh=wh: c.rectangle(wx, wy, ww, wh), fill=fill))
        def rail(c, wx=wx, wy=wy, ww=ww, wh=wh):
            c.move_to(wx - ww * 0.12, wy + wh + h * 0.02)
            c.line_to(wx + ww * 1.12, wy + wh + h * 0.02)
        shapes.append(Shape(rail))
    draw_shapes(ctx, shapes, line_p, fill_p)

def storefront(ctx, x, base_y, w, h, body=TEAL, awning=TERRACOTTA, line_p=1.0, fill_p=1.0, sign=None):
    top = base_y - h
    shapes = [Shape(lambda c: c.rectangle(x, top, w, h), fill=body),
              Shape(lambda c: c.rectangle(x + w * 0.06, top + h * 0.08, w * 0.88, h * 0.16), fill=CREAM)]
    stripes = 5
    for i in range(stripes):
        sx = x + w * 0.02 + i * w * 0.96 / stripes
        sw = w * 0.96 / stripes
        def stripe(c, sx=sx, sw=sw):
            c.move_to(sx, top + h * 0.3)
            c.line_to(sx + sw, top + h * 0.3)
            c.line_to(sx + sw, top + h * 0.4)
            c.arc(sx + sw / 2, top + h * 0.4, sw / 2, 0, math.pi)
            c.close_path()
        shapes.append(Shape(stripe, fill=awning if i % 2 == 0 else CREAM))
    shapes.append(Shape(lambda c: c.rectangle(x + w * 0.08, top + h * 0.52, w * 0.5, h * 0.36), fill=COBALT))
    shapes.append(Shape(lambda c: c.rectangle(x + w * 0.66, top + h * 0.5, w * 0.24, h * 0.5), fill=NAVY))
    draw_shapes(ctx, shapes, line_p, fill_p)
    if sign and fill_p > 0.5:
        text(ctx, sign, x + w / 2, top + h * 0.2, FONT_BODY_SEMI, h * 0.075, NAVY, "center", alpha=prog(fill_p, 0.5, 0.5), tracking=h * 0.01)

def office_block(ctx, x, base_y, w, h, body=COBALT, line_p=1.0, fill_p=1.0):
    top = base_y - h
    shapes = [Shape(lambda c: c.rectangle(x, top, w, h), fill=body)]
    cols, rows = 3, 5
    for r in range(rows):
        for col in range(cols):
            wx = x + w * 0.14 + col * w * 0.26
            wy = top + h * 0.08 + r * h * 0.16
            shapes.append(Shape(lambda c, wx=wx, wy=wy: c.rectangle(wx, wy, w * 0.16, h * 0.09), fill=CREAM))
    draw_shapes(ctx, shapes, line_p, fill_p)

def crane(ctx, x, base_y, h, line_p=1.0, hook_y=0.5, color=NAVY):
    """Tower crane: lattice mast, jib, counter-jib with weight, apex ties, and a hanging load."""
    m = h * 0.035  # half mast width
    p_mast, p_jib, p_ties = clamp(line_p * 2.2), clamp(line_p * 2.2 - 1.0), clamp(line_p * 2.2 - 1.6)
    top = base_y - h
    for dx in (-m, m):
        stroke_polyline(ctx, partial_polyline([(x + dx, base_y), (x + dx, top)], p_mast), color, LINE)
    zig = [(x + (m if i % 2 else -m), base_y - h * i / 12) for i in range(13)]
    stroke_polyline(ctx, partial_polyline(zig, p_mast), color, LINE * 0.6)
    stroke_polyline(ctx, partial_polyline([(x - h * 0.24, top), (x + h * 0.72, top)], p_jib), color, LINE * 1.2)
    stroke_polyline(ctx, partial_polyline([(x - h * 0.24, top + h * 0.035), (x + h * 0.72, top + h * 0.035)], p_jib), color, LINE * 0.7)
    stroke_polyline(ctx, partial_polyline([(x - h * 0.24, top), (x, top - h * 0.14), (x + h * 0.72, top)], p_ties), color, LINE * 0.7)
    if p_jib >= 1:
        ctx.rectangle(x - h * 0.23, top + h * 0.035, h * 0.09, h * 0.07)
        set_color(ctx, TERRACOTTA)
        ctx.fill_preserve()
        set_color(ctx, NAVY)
        ctx.set_line_width(LINE * 0.8)
        ctx.stroke()
    if p_ties >= 1:
        hx = x + h * 0.5
        hy = top + h * 0.1 + h * 0.45 * hook_y
        stroke_polyline(ctx, [(hx, top + h * 0.035), (hx, hy)], color, LINE * 0.7)
        ctx.rectangle(hx - h * 0.06, hy, h * 0.12, h * 0.07)
        set_color(ctx, OCHRE)
        ctx.fill_preserve()
        set_color(ctx, NAVY)
        ctx.set_line_width(LINE * 0.8)
        ctx.stroke()

def scaffold(ctx, x, base_y, w, h, p=1.0):
    levels = 4
    for i in range(levels + 1):
        yy = base_y - h * i / levels
        stroke_polyline(ctx, partial_polyline([(x, yy), (x + w, yy)], clamp(p * 2 - i * 0.2)), NAVY, LINE * 0.8)
    for j in range(4):
        xx = x + w * j / 3
        stroke_polyline(ctx, partial_polyline([(xx, base_y), (xx, base_y - h)], clamp(p * 1.6 - j * 0.1)), NAVY, LINE * 0.8)
    for i in range(levels):
        for j in range(3):
            if (i + j) % 2 == 0:
                a = (x + w * j / 3, base_y - h * i / levels)
                b = (x + w * (j + 1) / 3, base_y - h * (i + 1) / levels)
                stroke_polyline(ctx, partial_polyline([a, b], clamp(p * 2 - 1 - i * 0.1)), NAVY, LINE * 0.5)


# ---------------------------------------------------------------- documents & icons
def document(ctx, x, y, w, h, fill=CREAM, lines=5, line_p=1.0, fill_p=1.0, rotate=0.0):
    ctx.save()
    ctx.translate(x + w / 2, y + h / 2)
    ctx.rotate(rotate)
    ctx.translate(-w / 2, -h / 2)
    fold = w * 0.18
    def sheet(c):
        c.move_to(0, 0)
        c.line_to(w - fold, 0)
        c.line_to(w, fold)
        c.line_to(w, h)
        c.line_to(0, h)
        c.close_path()
    shapes = [Shape(sheet, fill=fill), Shape(lambda c: (c.move_to(w - fold, 0), c.line_to(w - fold, fold), c.line_to(w, fold)))]
    for i in range(lines):
        ly = h * 0.22 + i * h * 0.12
        lw = w * (0.62 if i % 3 == 2 else 0.74)
        shapes.append(Shape(lambda c, ly=ly, lw=lw: (c.move_to(w * 0.13, ly), c.line_to(w * 0.13 + lw, ly)), line_width=LINE * 0.7))
    draw_shapes(ctx, shapes, line_p, fill_p)
    ctx.restore()

def stamp(ctx, cx, cy, r, p, label="QUALIFIED", fill=TEAL):
    """Approval stamp that lands with a small overshoot."""
    if p <= 0:
        return
    s = lerp(1.6, 1.0, ease_back(clamp(p / 0.6), 1.2))
    a = clamp(p / 0.25)
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(-0.16)
    ctx.scale(s, s)
    ctx.arc(0, 0, r, 0, 2 * math.pi)
    set_color(ctx, fill, a)
    ctx.fill_preserve()
    set_color(ctx, NAVY, a)
    ctx.set_line_width(LINE)
    ctx.stroke()
    ctx.arc(0, 0, r * 0.8, 0, 2 * math.pi)
    ctx.set_line_width(LINE * 0.6)
    ctx.stroke()
    check_mark(ctx, 0, -r * 0.18, r * 0.62, clamp((p - 0.4) / 0.4))
    text(ctx, label, 0, r * 0.5, FONT_BODY_SEMI, r * 0.2, NAVY, "center", alpha=a, tracking=r * 0.02, label=None)
    ctx.restore()

def calendar_icon(ctx, x, y, w, h, flip=0.0, fill=TERRACOTTA):
    shapes = [Shape(lambda c: c.rectangle(x, y, w, h), fill=CREAM),
              Shape(lambda c: c.rectangle(x, y, w, h * 0.24), fill=fill)]
    for i in range(3):
        for j in range(4):
            cx = x + w * (0.15 + j * 0.23)
            cy = y + h * (0.38 + i * 0.2)
            shapes.append(Shape(lambda c, cx=cx, cy=cy: c.rectangle(cx, cy, w * 0.12, h * 0.1),
                                fill=NAVY if (i * 4 + j) < flip * 12 else None, line_width=LINE * 0.6))
    draw_shapes(ctx, shapes)
    for dx in (0.28, 0.72):
        stroke_polyline(ctx, [(x + w * dx, y - h * 0.08), (x + w * dx, y + h * 0.08)], NAVY, LINE * 1.2)

def utility_pole(ctx, x, base_y, h, p=1.0, sway=0.0):
    stroke_polyline(ctx, partial_polyline([(x, base_y), (x, base_y - h)], clamp(p * 2)), NAVY, LINE * 1.6)
    stroke_polyline(ctx, partial_polyline([(x - h * 0.22, base_y - h * 0.88), (x + h * 0.22, base_y - h * 0.88)], clamp(p * 2 - 0.6)), NAVY, LINE * 1.3)
    for dx in (-0.18, 0.0, 0.18):
        if p > 0.6:
            sx, sy = x + h * dx, base_y - h * 0.88
            ex, ey = x + h * 0.95, base_y - h * (0.62 + dx * 0.2)
            pts = [(sx + (ex - sx) * k / 12, sy + (ey - sy) * k / 12 + math.sin(math.pi * k / 12) * h * (0.08 + sway * 0.03)) for k in range(13)]
            stroke_polyline(ctx, partial_polyline(pts, clamp((p - 0.6) / 0.4)), NAVY, LINE * 0.6)
    for dx in (-0.18, 0.0, 0.18):
        ctx.arc(x + h * dx, base_y - h * 0.9, h * 0.022, 0, 2 * math.pi)
        set_color(ctx, OCHRE)
        ctx.fill_preserve()
        set_color(ctx, NAVY)
        ctx.set_line_width(LINE * 0.6)
        ctx.stroke()

def aurora_mark(ctx, cx, base_y, r, color_fill=OCHRE, line_color=NAVY, p=1.0):
    """Original wordmark glyph: a rising half-sun over a horizon line (aurora = dawn)."""
    ctx.new_path()
    ctx.arc(cx, base_y, r * ease_out(clamp(p)), math.pi, 2 * math.pi)
    ctx.close_path()
    set_color(ctx, color_fill)
    ctx.fill_preserve()
    set_color(ctx, line_color)
    ctx.set_line_width(max(2, r * 0.12))
    ctx.stroke()
    stroke_polyline(ctx, [(cx - r * 1.35, base_y), (cx + r * 1.35, base_y)], line_color, max(2, r * 0.12))

def wordmark(ctx, x, y, size, color=NAVY, fill=OCHRE, alpha=1.0, align="left"):
    """'Aurora' text wordmark with the dawn glyph. y is the text baseline. Returns total width."""
    r = size * 0.36
    word_w = text_width(ctx, "Aurora", FONT_HEAD, size)
    total = r * 2.7 + size * 0.28 + word_w
    if align == "center":
        x -= total / 2
    ctx.save()
    ctx.push_group()
    aurora_mark(ctx, x + r * 1.35, y - size * 0.08, r, fill, color)
    text(ctx, "Aurora", x + r * 2.7 + size * 0.28, y, FONT_HEAD, size, color, label="wordmark")
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(alpha)
    ctx.restore()
    return total


# ---------------------------------------------------------------- city plan
class CityPlan:
    """Abstract street grid with a defined, irregular perimeter drawn on street centerlines."""
    def __init__(self, x, y, w, h, cols=7, rows=5, gap=18,
                 perimeter=((1, 1), (5, 1), (5, 2), (6, 2), (6, 4), (2, 4), (2, 3), (1, 3))):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.cols, self.rows, self.gap = cols, rows, gap
        self.bw = (w - (cols + 1) * gap) / cols
        self.bh = (h - (rows + 1) * gap) / rows
        self.perimeter = [self.node(c, r) for c, r in perimeter]

    def node(self, c, r):
        return (self.x + self.gap / 2 + c * (self.bw + self.gap), self.y + self.gap / 2 + r * (self.bh + self.gap))

    def block_rect(self, c, r):
        return (self.x + self.gap + c * (self.bw + self.gap), self.y + self.gap + r * (self.bh + self.gap), self.bw, self.bh)

    def block_center(self, c, r):
        bx, by, bw, bh = self.block_rect(c, r)
        return bx + bw / 2, by + bh / 2

    def inside(self, c, r):
        px, py = self.block_center(c, r)
        poly, hit = self.perimeter, False
        for i in range(len(poly)):
            (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
            if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
                hit = not hit
        return hit

    def draw(self, ctx, t_grid=1.0, t_perimeter=1.0, t_fill=1.0, inside_fill=TEAL, highlight=None, dim_outside=False):
        blocks = [(c, r) for r in range(self.rows) for c in range(self.cols)]
        for i, (c, r) in enumerate(blocks):
            bp = clamp(t_grid * 1.6 - i / len(blocks) * 0.6)
            if bp <= 0:
                continue
            bx, by, bw, bh = self.block_rect(c, r)
            fp = 0.0
            if self.inside(c, r):
                order = (c + r) / (self.cols + self.rows)
                fp = clamp(t_fill * 1.8 - order)
            if highlight and (c, r) in highlight:
                fp = highlight[(c, r)][1]
            draw_shapes(ctx, [Shape(lambda cc, bx=bx, by=by, bw=bw, bh=bh: rounded_rect(cc, bx, by, bw, bh, 4), fill=CREAM)], bp, bp, LINE * 0.7)
            if fp > 0:
                ctx.save()
                rounded_rect(ctx, bx, by, bw, bh, 4)
                ctx.clip()
                ctx.rectangle(bx, by + bh * (1 - ease_out(fp)), bw, bh)
                set_color(ctx, highlight[(c, r)][0] if highlight and (c, r) in highlight else inside_fill)
                ctx.fill()
                ctx.restore()
                draw_shapes(ctx, [Shape(lambda cc, bx=bx, by=by, bw=bw, bh=bh: rounded_rect(cc, bx, by, bw, bh, 4))], 1, 0, LINE * 0.7)
        if t_perimeter > 0:
            pts = partial_polyline(self.perimeter, t_perimeter, closed=True)
            stroke_polyline(ctx, pts, NAVY, LINE * 1.4, dash=[14, 9])
