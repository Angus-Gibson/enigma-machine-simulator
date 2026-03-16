#!/usr/bin/env python3
"""
main.py  —  Enigma Machine Simulator
Photo-realistic aesthetics: real texture assets, feldgrau military steel,
period-correct hardware detail, responsive fullscreen scaling.
"""

import sys
import math
import pathlib
import textwrap
import webbrowser
import pygame
import pygame.gfxdraw

from enigma_core import ALPHABET, MACHINE_CONFIGS, ROTOR_DATA, EnigmaMachine
from sound_manager import SoundManager


def resource_path(relative: str) -> pathlib.Path:
    """Return absolute path to a bundled resource.

    When running as a PyInstaller onefile executable, temporary files are
    extracted to sys._MEIPASS at runtime.  When running from source the
    path is resolved relative to this file as normal.
    """
    base = pathlib.Path(getattr(sys, '_MEIPASS', pathlib.Path(__file__).parent))
    return base / relative


# ─── Window / layout ──────────────────────────────────────────────────────────
# fmt: off
SW, SH         = 1440, 960
HEADER_H       = 55
BOX_W          = 218
RIGHT_X        = 1082
PANEL_W        = SW - RIGHT_X
MACHINE_X      = BOX_W
MACHINE_W      = RIGHT_X - BOX_W
MACHINE_TOP    = HEADER_H
MACHINE_BOTTOM = 505
PLUG_Y         = MACHINE_BOTTOM
PLUG_H         = 128
LAMP_Y         = PLUG_Y + PLUG_H
LAMP_H         = 150
KEY_Y          = LAMP_Y + LAMP_H
KEY_H          = SH - KEY_Y

KB_ROWS = [list('QWERTZUIO'), list('ASDFGHJK'), list('PYXCVBNML')]
KB_ALL  = [c for row in KB_ROWS for c in row]
ASSETS  = resource_path('assets')

WATERMARK_URL  = 'https://github.com/Angus-Gibson'
WATERMARK_TEXT = 'github.com/Angus-Gibson'

# Keys and modifiers accepted by the Enigma keyboard.
# Using event.key (physical scancode) rather than event.unicode so that
# Shift, Caps Lock, AltGr, etc. cannot smuggle a letter through the check.
_ALPHA_KEYS = frozenset(range(pygame.K_a, pygame.K_z + 1))
_MOD_MASK   = pygame.KMOD_SHIFT | pygame.KMOD_CTRL | pygame.KMOD_ALT | pygame.KMOD_META
# fmt: on

# ─── Period-correct palette ───────────────────────────────────────────────────
# fmt: off
C = {
    'bg':           (10, 11,  8),

    'wood_base':    (40, 21,  7),
    'wood_mid':     (64, 36, 13),
    'wood_light':   (90, 54, 21),
    'wood_dark':    (26, 12,  3),
    'wood_brass':   (140, 108, 44),

    'fg_base':      (60, 65, 54),
    'fg_dark':      (40, 43, 34),
    'fg_mid':       (52, 56, 46),
    'fg_light':     (80, 86, 72),
    'fg_hi':        (106, 113, 96),
    'fg_shadow':    (26, 28, 22),

    'steel_dk':     (30, 32, 34),
    'steel_md':     (52, 55, 60),
    'steel_lt':     (104, 110, 120),
    'steel_hi':     (150, 156, 168),

    'brass_dk':     (104, 78, 28),
    'brass_md':     (146, 116, 46),
    'brass_lt':     (184, 150, 68),
    'brass_hi':     (214, 182, 100),

    'bak_base':     (27, 20, 13),
    'bak_rim':      (42, 32, 22),
    'bak_hi':       (60, 46, 30),
    'bak_letter':   (220, 210, 185),
    'bak_down':     (18, 13,  9),

    'win_bg':       (50, 26,  5),
    'win_glow':     (92, 52, 10),
    'win_letter':   (255, 208, 72),
    'win_adj':      (140, 88, 28),
    'win_bezel':    (14, 11,  5),
    'win_edge_hi':  (80, 62, 32),

    'lamp_ring':    (108, 84, 32),
    'lamp_socket':  (60, 44, 16),
    'lamp_cold':    (20, 14,  5),
    'lamp_warm':    (255, 176, 36),
    'lamp_bright':  (255, 224, 115),
    'lamp_white':   (255, 251, 225),
    'lamp_bloom':   (255, 150, 16),

    'plug_bg':      (44, 48, 40),
    'plug_btn':     (52, 56, 46),
    'plug_sel':     (174, 140, 50),
    'plug_paired':  (160, 96, 33),
    'plug_wire':    (204, 134, 42),

    'text_lt':      (190, 182, 165),
    'text_gold':    (192, 162, 74),
    'text_brass':   (172, 140, 58),
    'text_dk':      (20, 17, 13),
    'text_dim':     (96, 87, 70),

    'danger':       (160, 34, 34),
    'success':      (44, 140, 48),
    'notch':        (210, 40, 40),
    'highlight':    (210, 182, 52),
    'ivory':        (224, 214, 184),

    'slot_empty':   (28, 30, 26),
    'slot_filled':  (44, 47, 40),
    'slot_edge':    (68, 73, 62),
    'arrow_btn':    (54, 58, 49),

    'paper':        (220, 210, 176),
    'paper_line':   (170, 160, 130),

    'msgbox_bg':    (36, 40, 32),
    'msgbox_edge':  (143, 114, 46),

    'metal_lt':     (104, 110, 120),
    'metal_hi':     (150, 156, 168),
    'gold':         (184, 154, 62),
    'gold_lt':      (214, 182, 96),
}
# fmt: on

# ─── Key / lamp geometry ──────────────────────────────────────────────────────
# fmt: off
KEY_W, KEY_H_PX = 58, 46
KEY_GAP_H       = 7
KEY_GAP_V       = 8
KEY_R_VIS       = 20
LAMP_RADIUS     = 21
LAMP_GAP_H      = 8
# fmt: on


def _kb_positions() -> dict[str, tuple[int, int]]:
    pos = {}
    for ri, row in enumerate(KB_ROWS):
        row_w = len(row) * KEY_W + (len(row) - 1) * KEY_GAP_H
        rx = (RIGHT_X - row_w) // 2
        ry = ri * (KEY_H_PX + KEY_GAP_V)
        for ci, letter in enumerate(row):
            pos[letter] = (rx + ci * (KEY_W + KEY_GAP_H) + KEY_W // 2, ry + KEY_H_PX // 2)
    return pos


_KB_POS = _kb_positions()


# ─── Texture helpers ──────────────────────────────────────────────────────────


def tex_region(tex: pygame.Surface, w: int, h: int, ox: int = 0, oy: int = 0) -> pygame.Surface:
    """Sample a w×h region from tex at offset (ox, oy), tiling if needed."""
    out = pygame.Surface((w, h))
    tw, th = tex.get_size()
    for ty in range(-(oy % th), h, th):
        for tx in range(-(ox % tw), w, tw):
            out.blit(tex, (tx, ty))
    return out


def tint_surf(surf: pygame.Surface, color: tuple, alpha: int = 110) -> pygame.Surface:
    """Blend a colour tint over surf, returns a new converted surface."""
    out = surf.copy().convert()
    ov = pygame.Surface(out.get_size())
    ov.fill(color)
    ov.set_alpha(alpha)
    out.blit(ov, (0, 0))
    return out


def apply_directional_light(surf: pygame.Surface, strength: int = 40) -> pygame.Surface:
    """Simulate top-left warm light: brighten top/left edges, darken bottom/right."""
    w, h = surf.get_size()
    ov = pygame.Surface((w, h), pygame.SRCALPHA)
    s = min(strength, min(w, h))
    for i in range(s):
        t = 1.0 - i / s
        pygame.draw.line(ov, (255, 240, 200, int(38 * t)), (0, i), (w, i))
        pygame.draw.line(ov, (255, 240, 200, int(20 * t)), (i, 0), (i, h))
    half = max(1, s // 2)
    for i in range(half):
        t = 1.0 - i / half
        pygame.draw.line(ov, (0, 0, 0, int(34 * t)), (0, h - 1 - i), (w, h - 1 - i))
        pygame.draw.line(ov, (0, 0, 0, int(18 * t)), (w - 1 - i, 0), (w - 1 - i, h))
    surf.blit(ov, (0, 0))
    return surf


def add_section_shadow(surf: pygame.Surface, y: int, w: int, depth: int = 12):
    """Inset drop shadow at y — physically separates panel sections."""
    sh = pygame.Surface((w, depth), pygame.SRCALPHA)
    for i in range(depth):
        a = int(160 * (1.0 - i / depth) ** 1.4)
        pygame.draw.line(sh, (0, 0, 0, a), (0, i), (w, i))
    surf.blit(sh, (0, y))


# ─── Drawing helpers ──────────────────────────────────────────────────────────


def draw_rounded_rect(surf, colour, rect, radius, border=0, border_colour=None):
    pygame.draw.rect(surf, colour, rect, border_radius=radius)
    if border and border_colour:
        pygame.draw.rect(surf, border_colour, rect, border, border_radius=radius)


def draw_text(surf, text, font, colour, cx, cy, anchor='center'):
    img = font.render(text, True, colour)
    r = img.get_rect()
    if anchor == 'center':
        r.center = (cx, cy)
    elif anchor == 'midleft':
        r.midleft = (cx, cy)
    elif anchor == 'midright':
        r.midright = (cx, cy)
    surf.blit(img, r)
    return r


def draw_bezier_wire(surf, p0, p1, colour, width=2):
    steps = 44
    ctrl_y = min(p0[1], p1[1]) - abs(p1[1] - p0[1]) * 0.5 - 24
    pts = []
    for i in range(steps + 1):
        t = i / steps
        x = (
            (1 - t) ** 3 * p0[0]
            + 3 * (1 - t) ** 2 * t * p0[0]
            + 3 * (1 - t) * t**2 * p1[0]
            + t**3 * p1[0]
        )
        y = (
            (1 - t) ** 3 * p0[1]
            + 3 * (1 - t) ** 2 * t * ctrl_y
            + 3 * (1 - t) * t**2 * ctrl_y
            + t**3 * p1[1]
        )
        pts.append((int(x), int(y)))
    if len(pts) >= 2:
        pygame.draw.lines(surf, colour, False, pts, width)


def bevel_rect(surf, rect, light, shadow, width=2):
    """3-D raised-panel bevel."""
    x, y, w, h = rect
    for i in range(width):
        pygame.draw.line(surf, light, (x + i, y + i), (x + w - 2 - i, y + i))
        pygame.draw.line(surf, light, (x + i, y + i), (x + i, y + h - 2 - i))
        pygame.draw.line(surf, shadow, (x + i, y + h - 1 - i), (x + w - 1 - i, y + h - 1 - i))
        pygame.draw.line(surf, shadow, (x + w - 1 - i, y + i), (x + w - 1 - i, y + h - 1 - i))


def draw_rivet(surf, cx, cy, r=4):
    pygame.draw.circle(surf, (0, 0, 0), (cx + 1, cy + 1), r)
    pygame.draw.circle(surf, C['steel_md'], (cx, cy), r)
    pygame.draw.circle(surf, C['steel_hi'], (cx, cy), r, 1)
    if r > 3:
        pygame.draw.circle(surf, (200, 206, 218), (cx - 1, cy - 1), max(1, r // 3))


def draw_screw(surf, cx, cy, r=5):
    """Brass machine screw head with cross slot — intricate period hardware detail."""
    pygame.draw.circle(surf, (0, 0, 0), (cx + 1, cy + 1), r)
    pygame.draw.circle(surf, C['brass_md'], (cx, cy), r)
    pygame.draw.circle(surf, C['brass_lt'], (cx, cy), r, 1)
    pygame.draw.line(surf, C['brass_dk'], (cx - r + 2, cy), (cx + r - 2, cy), 1)
    pygame.draw.line(surf, C['brass_dk'], (cx, cy - r + 2), (cx, cy + r - 2), 1)
    pygame.draw.circle(surf, C['brass_hi'], (cx - r // 3, cy - r // 3), max(1, r // 3))


# ─── Pre-computed surface builders ────────────────────────────────────────────


def build_lamp_glow_surf(r: int) -> pygame.Surface:
    """Soft warm halo around a lit bulb — tight bloom, does not flood neighbours."""
    size = r + 20
    surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
    cx = cy = size
    for dr, alpha in [(18, 8), (13, 18), (9, 34), (5, 55), (2, 72)]:
        pygame.draw.circle(surf, (*C['lamp_bloom'], alpha), (cx, cy), r + dr)
    return surf


def build_key_surf(bak_tex: pygame.Surface, r: int, pressed: bool) -> pygame.Surface:
    """Round bakelite key cap using real texture, with 3-D convex highlight."""
    size = r * 2 + 24
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = cy = size // 2
    off = 5 if pressed else 0

    if not pressed:
        # Layered drop shadow beneath key
        for si in range(9, 0, -1):
            a = int(115 * si / 9)
            pygame.draw.circle(s, (0, 0, 0, a), (cx + si // 2 + 2, cy + si // 2 + 7), r + si // 2)

    # Socket mount — dark recess in panel
    pygame.draw.circle(s, (8, 5, 3), (cx, cy + 4), r + 7)

    # Crop circular region from bakelite texture
    tw, th = bak_tex.get_size()
    crop = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    crop.blit(bak_tex, (0, 0), (tw // 2 - r, th // 2 - r, r * 2, r * 2))

    # Darken significantly — aged black bakelite
    dk = pygame.Surface((r * 2, r * 2))
    dk.fill((0, 0, 0))
    dk.set_alpha(90 if not pressed else 145)
    crop.blit(dk, (0, 0))

    # Mask to circle
    mask = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    pygame.draw.circle(mask, (255, 255, 255, 255), (r, r), r)
    crop.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    s.blit(crop, (cx - r, cy + off - r))

    # Rim
    pygame.draw.circle(s, C['bak_rim'], (cx, cy + off), r, 2)

    if not pressed:
        # Convex top-left highlight arc — simulates spherical surface in light
        hl = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        hcx, hcy = r - r // 3, r - r // 3
        for hr in range(r * 3 // 4, 0, -4):
            a = max(0, int(62 * (hr / (r * 3 // 4))))
            pygame.draw.circle(hl, (255, 248, 220, a), (hcx, hcy), hr)
        s.blit(hl, (cx - r, cy + off - r))
        # Specular highlight dot
        pygame.draw.circle(s, (238, 228, 208), (cx - r // 3, cy + off - r // 3), 2)
    else:
        # Pressed: shadow falls from top
        dark_half = pygame.Surface((r * 2, r), pygame.SRCALPHA)
        for i in range(r):
            a = int(52 * (1.0 - i / r))
            pygame.draw.line(dark_half, (0, 0, 0, a), (0, i), (r * 2, i))
        s.blit(dark_half, (cx - r, cy + off - r))

    return s


# ─── Application ──────────────────────────────────────────────────────────────


class EnigmaApp:
    def __init__(self):
        pygame.init()
        # RESIZABLE | SCALED: pygame renders at SW×SH, scales to any window size.
        # Mouse events are automatically translated to logical coordinates.
        # Fall back to plain mode if SCALED is unsupported (e.g. headless tests).
        try:
            self.screen = pygame.display.set_mode((SW, SH), pygame.RESIZABLE | pygame.SCALED)
        except pygame.error:
            self.screen = pygame.display.set_mode((SW, SH))
        pygame.display.set_caption("Enigma Machine Simulator")
        self.clock = pygame.time.Clock()
        self.sounds = SoundManager()

        mono = 'Courier New'
        serif = 'Georgia'
        self.f_title = pygame.font.SysFont(serif, 26, bold=True)
        self.f_head = pygame.font.SysFont(serif, 17, bold=True)
        self.f_big = pygame.font.SysFont(mono, 52, bold=True)
        self.f_med = pygame.font.SysFont(mono, 19, bold=True)
        self.f_sm = pygame.font.SysFont(mono, 13)
        self.f_xs = pygame.font.SysFont(mono, 10)
        self.f_key = pygame.font.SysFont(mono, 16, bold=True)
        self.f_lamp = pygame.font.SysFont(mono, 14, bold=True)
        self.f_box = pygame.font.SysFont(mono, 18, bold=True)
        self.f_win = pygame.font.SysFont(mono, 40, bold=True)  # rotor window letter

        self._load_assets()
        self._build_textures()

        self.machine_type = 'Enigma I'
        self._init_machine_state()

        self.selected_box_rotor: str | None = None
        self.plug_first: str | None = None
        self.active_lamp: str | None = None
        self.lamp_timer = 0
        self.active_key: str | None = None
        self.key_timer = 0
        self.backspace_notice_timer = 0
        self.dropdown_open = False
        self.message_box: str | None = None

        self.input_text = ''
        self.output_text = ''
        self.hb: dict[str, pygame.Rect] = {}
        self.running = True
        self._watermark_hover = False

    # ── Asset loading ──────────────────────────────────────────────────────────

    def _load_assets(self):
        """Load PNG texture assets; create tinted variants for different surfaces."""

        def load(name):
            return pygame.image.load(str(ASSETS / name)).convert()

        self._tex_wood = load('wood.png')
        self._tex_metal = load('metal.png')
        self._tex_bakelite = load('bakelite.png')

        # Feldgrau-tinted metal (#4B5320 = 75, 83, 32) — Wehrmacht painted steel
        self._tex_metal_fg = tint_surf(self._tex_metal, (75, 83, 32), 120)
        # Dark-tinted metal — lamp panel, rotor bodies
        self._tex_metal_dk = tint_surf(self._tex_metal, (32, 34, 28), 158)

    def _build_textures(self):
        """Pre-compute all panel surfaces from loaded assets. Called once at startup."""
        box_h = MACHINE_BOTTOM - MACHINE_TOP

        # Rotor storage box — natural wood grain, horizontal flow
        wood = tex_region(self._tex_wood, BOX_W, box_h, ox=0, oy=0)
        apply_directional_light(wood, 50)
        self._wood_surf = wood

        # Main machine chassis — feldgrau painted metal
        chassis = tex_region(self._tex_metal_fg, MACHINE_W, box_h, ox=320, oy=80)
        apply_directional_light(chassis, 38)
        self._chassis_surf = chassis

        # Header bar — darker feldgrau
        hdr = tex_region(self._tex_metal_fg, SW, HEADER_H, ox=0, oy=500)
        dk = pygame.Surface((SW, HEADER_H))
        dk.fill((15, 16, 12))
        dk.set_alpha(155)
        hdr.blit(dk, (0, 0))
        self._header_surf = hdr

        # Plugboard panel — feldgrau, different region for visual variety
        plug = tex_region(self._tex_metal_fg, RIGHT_X, PLUG_H, ox=100, oy=900)
        apply_directional_light(plug, 26)
        self._plug_panel = plug

        # Lampboard — very dark metal, almost black
        lamp = tex_region(self._tex_metal_dk, RIGHT_X, LAMP_H, ox=600, oy=400)
        dk2 = pygame.Surface((RIGHT_X, LAMP_H))
        dk2.fill((3, 2, 1))
        dk2.set_alpha(175)
        lamp.blit(dk2, (0, 0))
        self._lamp_panel = lamp

        # Keyboard panel — dark bakelite texture
        kb = tex_region(self._tex_bakelite, RIGHT_X, KEY_H, ox=200, oy=1200)
        dk3 = pygame.Surface((RIGHT_X, KEY_H))
        dk3.fill((5, 3, 2))
        dk3.set_alpha(162)
        kb.blit(dk3, (0, 0))
        self._kb_panel = kb

        # Right panel (output notepad) background — leave as drawn procedurally
        self._lamp_glow = build_lamp_glow_surf(LAMP_RADIUS)

        # Bakelite key surfaces from texture
        self._key_up = build_key_surf(self._tex_bakelite, KEY_R_VIS, False)
        self._key_down = build_key_surf(self._tex_bakelite, KEY_R_VIS, True)

    # ── State helpers (logic unchanged) ───────────────────────────────────────

    def _init_machine_state(self):
        cfg = MACHINE_CONFIGS[self.machine_type]
        n = cfg['num_rotors']
        self.slots: list[str | None] = [None] * n
        self.slot_pos: list[int] = [0] * n
        self.slot_ring: list[int] = [0] * n
        self.reflector: str = cfg['available_reflectors'][0]
        self.fourth_rotor: str | None = cfg['fourth_rotors'][0] if cfg['fourth_rotors'] else None
        if self.machine_type == 'Enigma M4' and self.fourth_rotor:
            self.slots[0] = self.fourth_rotor
        self.plug_pairs: dict[str, str] = {}

    def _box_rotors(self) -> list[str]:
        cfg = MACHINE_CONFIGS[self.machine_type]
        normal_slots = self.slots[1:] if self.machine_type == 'Enigma M4' else self.slots
        installed = set(s for s in normal_slots if s)
        return [r for r in cfg['available_rotors'] if r not in installed]

    def _is_ready(self) -> bool:
        return all(s is not None for s in self.slots)

    def _build_machine(self) -> EnigmaMachine | None:
        if not self._is_ready():
            return None
        machine = EnigmaMachine(self.machine_type)
        machine.configure(
            list(self.slots),
            self.reflector,
            positions=list(self.slot_pos),
            ring_settings=list(self.slot_ring),
        )
        for a, b in self.plug_pairs.items():
            if ord(a) < ord(b):
                machine.plugboard.add_pair(a, b)
        return machine

    def _encode_key(self, letter: str):
        if not self._is_ready():
            self.message_box = "Please connect the correct number of rotars"
            return
        machine = self._build_machine()
        if machine is None:
            return
        out = machine.encode_char(letter)
        start = 1 if self.machine_type == 'Enigma M4' else 0
        for i in range(start, len(self.slots)):
            self.slot_pos[i] = machine.rotors[i].position
        self.input_text += letter
        self.output_text += out
        self.active_lamp = out
        self.lamp_timer = 45
        self.active_key = letter
        self.key_timer = 12
        self.sounds.play('key_press')
        self.sounds.play('rotor_step')

    # ── Event handling (logic unchanged) ──────────────────────────────────────

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if not self.message_box and not self.dropdown_open:
                    if event.key in _ALPHA_KEYS and not (event.mod & _MOD_MASK):
                        # Bare A-Z only: physical key is alphabetic AND no
                        # modifier (Shift, Ctrl, Alt, Win/Meta) is held.
                        # event.key is the scancode so Caps Lock, AltGr, and
                        # composed unicode values cannot bypass this check.
                        self._encode_key(chr(event.key).upper())
                    elif event.key == pygame.K_BACKSPACE:
                        # Real Enigma operators could not undo a keystroke —
                        # the rotor had already mechanically stepped.  Erasing
                        # the last letter while leaving the rotors advanced
                        # would produce gibberish on decryption.  Show a
                        # period-appropriate notice instead of modifying state.
                        self.backspace_notice_timer = 240  # ~4 s at 60 fps
                    # All other keys are intentionally silent: no sound,
                    # no animation, no state change.
            elif event.type == pygame.MOUSEMOTION:
                over = 'watermark' in self.hb and self.hb['watermark'].collidepoint(event.pos)
                if over != self._watermark_hover:
                    self._watermark_hover = over
                    pygame.mouse.set_cursor(
                        pygame.SYSTEM_CURSOR_HAND if over else pygame.SYSTEM_CURSOR_ARROW
                    )
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(event.pos)

    def _handle_click(self, pos):
        if 'watermark' in self.hb and self.hb['watermark'].collidepoint(pos):
            webbrowser.open(WATERMARK_URL)
            return

        if self.message_box:
            if 'msgbox_ok' in self.hb and self.hb['msgbox_ok'].collidepoint(pos):
                self.message_box = None
                self.sounds.play('rotor_click')
            return

        if self.dropdown_open:
            for mtype in MACHINE_CONFIGS:
                key = f'dd_{mtype}'
                if key in self.hb and self.hb[key].collidepoint(pos):
                    if mtype != self.machine_type:
                        self.machine_type = mtype
                        self._init_machine_state()
                        self.input_text = self.output_text = ''
                        self.selected_box_rotor = self.plug_first = None
                        self.sounds.play('place_rotor')
                    self.dropdown_open = False
                    return
            self.dropdown_open = False
            return

        if 'machine_type_btn' in self.hb and self.hb['machine_type_btn'].collidepoint(pos):
            self.dropdown_open = True
            return
        if 'reset_all' in self.hb and self.hb['reset_all'].collidepoint(pos):
            self._init_machine_state()
            self.input_text = self.output_text = ''
            self.selected_box_rotor = self.plug_first = None
            self.sounds.play('place_rotor')
            return
        if 'reset_pos' in self.hb and self.hb['reset_pos'].collidepoint(pos):
            self.slot_pos = [0] * len(self.slots)
            self.sounds.play('rotor_click')
            return
        if 'clear_output' in self.hb and self.hb['clear_output'].collidepoint(pos):
            self.input_text = self.output_text = ''
            self.sounds.play('rotor_click')
            return

        for ref in MACHINE_CONFIGS[self.machine_type]['available_reflectors']:
            if f'ref_{ref}' in self.hb and self.hb[f'ref_{ref}'].collidepoint(pos):
                self.reflector = ref
                self.sounds.play('rotor_click')
                return

        for fr in MACHINE_CONFIGS[self.machine_type].get('fourth_rotors', []):
            if f'4th_{fr}' in self.hb and self.hb[f'4th_{fr}'].collidepoint(pos):
                self.fourth_rotor = fr
                if self.machine_type == 'Enigma M4':
                    self.slots[0] = fr
                self.sounds.play('rotor_click')
                return

        for r in self._box_rotors():
            if f'box_{r}' in self.hb and self.hb[f'box_{r}'].collidepoint(pos):
                self.selected_box_rotor = None if self.selected_box_rotor == r else r
                self.sounds.play('rotor_click')
                return

        for i in range(len(self.slots)):
            is_m4_fourth = self.machine_type == 'Enigma M4' and i == 0
            sk = f'slot_{i}'
            if sk in self.hb and self.hb[sk].collidepoint(pos):
                if self.slots[i] is None and self.selected_box_rotor and not is_m4_fourth:
                    self.slots[i] = self.selected_box_rotor
                    self.selected_box_rotor = None
                    self.sounds.play('place_rotor')
                    return
            for suffix, action in [
                ('_rm', self._rm_slot),
                ('_pu', self._pos_up),
                ('_pd', self._pos_dn),
                ('_ru', self._ring_up),
                ('_rd', self._ring_dn),
            ]:
                key = f'slot_{i}{suffix}'
                if key in self.hb and self.hb[key].collidepoint(pos):
                    action(i)
                    return

        for letter in ALPHABET:
            if f'plug_{letter}' in self.hb and self.hb[f'plug_{letter}'].collidepoint(pos):
                self._handle_plug_click(letter)
                return
            if f'key_{letter}' in self.hb and self.hb[f'key_{letter}'].collidepoint(pos):
                self._encode_key(letter)
                return

    def _rm_slot(self, i):
        self.slots[i] = None
        self.slot_pos[i] = self.slot_ring[i] = 0
        self.sounds.play('place_rotor')

    def _pos_up(self, i):
        self.slot_pos[i] = (self.slot_pos[i] + 1) % 26
        self.sounds.play('rotor_click')

    def _pos_dn(self, i):
        self.slot_pos[i] = (self.slot_pos[i] - 1) % 26
        self.sounds.play('rotor_click')

    def _ring_up(self, i):
        self.slot_ring[i] = (self.slot_ring[i] + 1) % 26
        self.sounds.play('ring_click')

    def _ring_dn(self, i):
        self.slot_ring[i] = (self.slot_ring[i] - 1) % 26
        self.sounds.play('ring_click')

    def _handle_plug_click(self, letter: str):
        if letter in self.plug_pairs:
            b = self.plug_pairs[letter]
            del self.plug_pairs[letter]
            del self.plug_pairs[b]
            self.sounds.play('rotor_click')
            self.plug_first = None
            return
        if self.plug_first is None:
            self.plug_first = letter
            self.sounds.play('ring_click')
        elif self.plug_first == letter:
            self.plug_first = None
        else:
            a, b = self.plug_first, letter
            if len(self.plug_pairs) // 2 < 13:
                self.plug_pairs[a] = b
                self.plug_pairs[b] = a
                self.sounds.play('rotor_click')
            self.plug_first = None

    # ── Update ────────────────────────────────────────────────────────────────

    def _update(self):
        if self.lamp_timer > 0:
            self.lamp_timer -= 1
            if self.lamp_timer == 0:
                self.active_lamp = None
        if self.key_timer > 0:
            self.key_timer -= 1
            if self.key_timer == 0:
                self.active_key = None
        if self.backspace_notice_timer > 0:
            self.backspace_notice_timer -= 1

    # ── Draw dispatch ─────────────────────────────────────────────────────────

    def _draw(self):
        self.hb = {}
        s = self.screen
        s.fill(C['bg'])
        self._draw_header(s)
        self._draw_rotor_box(s)
        self._draw_machine_body(s)
        # Section depth separators — shadow where panels meet
        add_section_shadow(s, PLUG_Y, RIGHT_X, 14)
        self._draw_plugboard(s)
        add_section_shadow(s, LAMP_Y, RIGHT_X, 12)
        self._draw_lampboard(s)
        add_section_shadow(s, KEY_Y, RIGHT_X, 10)
        self._draw_keyboard(s)
        self._draw_output_panel(s)
        self._draw_backspace_notice(s)
        self._draw_watermark(s)
        if self.dropdown_open:
            self._draw_dropdown(s)
        if self.message_box:
            self._draw_message_box(s)
        pygame.display.flip()

    # ── Header ────────────────────────────────────────────────────────────────

    def _draw_header(self, surf):
        # Real metal texture background
        surf.blit(self._header_surf, (0, 0))

        # Brass bottom edge — double rule
        pygame.draw.line(surf, C['brass_md'], (0, HEADER_H - 3), (SW, HEADER_H - 3), 2)
        pygame.draw.line(surf, C['brass_dk'], (0, HEADER_H - 1), (SW, HEADER_H - 1), 1)
        bevel_rect(surf, (0, 0, SW, HEADER_H), C['fg_hi'], C['fg_shadow'], 2)

        draw_text(
            surf,
            "CHIFFRIERMASCHINE  ENIGMA",
            self.f_title,
            C['brass_lt'],
            22,
            HEADER_H // 2,
            'midleft',
        )

        # Machine-type dropdown button
        mt_text = f"  {self.machine_type}  \u25bc"
        btn_img = self.f_med.render(mt_text, True, C['text_gold'])
        btn_r = btn_img.get_rect(center=(700, HEADER_H // 2))
        btn_rect = btn_r.inflate(20, 10)
        # Button uses metal texture region
        btn_tex = tex_region(self._tex_metal_fg, btn_rect.width, btn_rect.height, ox=700)
        dk = pygame.Surface(btn_tex.get_size())
        dk.fill((10, 11, 8))
        dk.set_alpha(100)
        btn_tex.blit(dk, (0, 0))
        surf.blit(btn_tex, btn_rect.topleft)
        bevel_rect(surf, btn_rect, C['fg_hi'], C['fg_shadow'])
        pygame.draw.rect(surf, C['brass_dk'], btn_rect, 1, border_radius=4)
        surf.blit(btn_img, btn_r)
        self.hb['machine_type_btn'] = btn_rect

        # Reset All
        rr = pygame.Rect(SW - 232, 10, 108, 35)
        pygame.draw.rect(surf, C['danger'], rr, border_radius=5)
        bevel_rect(surf, rr, (200, 60, 60), (100, 20, 20))
        draw_text(surf, "RESET ALL", self.f_sm, C['ivory'], rr.centerx, rr.centery)
        self.hb['reset_all'] = rr

        # Reset Positions
        rpr = pygame.Rect(SW - 118, 10, 108, 35)
        rpr_tex = tex_region(self._tex_metal_fg, rpr.width, rpr.height, ox=900, oy=200)
        dk2 = pygame.Surface(rpr_tex.get_size())
        dk2.fill((10, 11, 8))
        dk2.set_alpha(80)
        rpr_tex.blit(dk2, (0, 0))
        surf.blit(rpr_tex, rpr.topleft)
        bevel_rect(surf, rpr, C['fg_hi'], C['fg_shadow'])
        pygame.draw.rect(surf, C['brass_dk'], rpr, 1, border_radius=4)
        draw_text(surf, "RESET POS", self.f_sm, C['text_gold'], rpr.centerx, rpr.centery)
        self.hb['reset_pos'] = rpr

        # Status indicator — positioned between dropdown and RESET ALL
        ready = self._is_ready()
        ind_col = C['success'] if ready else C['danger']
        ind_txt = "BEREIT" if ready else "NICHT BEREIT"
        ind_x = SW - 348  # gap between dropdown (~850px right edge) and RESET ALL
        pygame.draw.circle(surf, (0, 0, 0), (ind_x + 1, HEADER_H // 2 + 1), 7)
        pygame.draw.circle(surf, ind_col, (ind_x, HEADER_H // 2), 7)
        pygame.draw.circle(surf, (0, 0, 0), (ind_x, HEADER_H // 2), 7, 1)
        draw_text(surf, ind_txt, self.f_xs, ind_col, ind_x + 12, HEADER_H // 2, 'midleft')

        # Corner screws
        for rx, ry in [(10, 9), (SW - 10, 9), (10, HEADER_H - 9), (SW - 10, HEADER_H - 9)]:
            draw_screw(surf, rx, ry, 5)

    # ── Rotor Box ─────────────────────────────────────────────────────────────

    def _draw_rotor_box(self, surf):
        bx, by = 0, MACHINE_TOP
        bw, bh = BOX_W, MACHINE_BOTTOM - MACHINE_TOP

        # Real wood grain texture
        surf.blit(self._wood_surf, (bx, by))

        # Outer brass frame
        pygame.draw.rect(surf, C['brass_dk'], (bx, by, bw, bh), 2)
        bevel_rect(surf, (bx, by, bw, bh), C['wood_light'], C['wood_dark'], 3)

        # Brass corner brackets with screws
        for cx2, cy2 in [
            (bx + 8, by + 8),
            (bx + bw - 8, by + 8),
            (bx + 8, by + bh - 8),
            (bx + bw - 8, by + bh - 8),
        ]:
            pygame.draw.rect(surf, C['brass_dk'], (cx2 - 8, cy2 - 8, 16, 16), border_radius=2)
            bevel_rect(surf, (cx2 - 8, cy2 - 8, 16, 16), C['brass_lt'], C['brass_dk'])
            draw_screw(surf, cx2, cy2, 5)

        # Title plate — embossed brass nameplate
        plate = pygame.Rect(bx + 14, by + 7, bw - 28, 34)
        pygame.draw.rect(surf, C['brass_dk'], plate, border_radius=3)
        bevel_rect(surf, plate, C['brass_lt'], C['brass_dk'])
        # Engraved text: dark shadow + bright text
        draw_text(surf, "ROTOR", self.f_xs, (60, 44, 16), plate.centerx + 1, plate.centery - 4)
        draw_text(surf, "STORAGE", self.f_xs, (60, 44, 16), plate.centerx + 1, plate.centery + 7)
        draw_text(surf, "ROTOR", self.f_xs, C['brass_hi'], plate.centerx, plate.centery - 5)
        draw_text(surf, "STORAGE", self.f_xs, C['brass_hi'], plate.centerx, plate.centery + 6)

        # Rotor discs
        box_rotors = self._box_rotors()
        disc_r = 27
        cols = 3
        pad_x = (bw - cols * (disc_r * 2 + 8)) // 2
        start_y = by + 50

        for idx, rname in enumerate(box_rotors):
            col = idx % cols
            row = idx // cols
            cx2 = pad_x + col * (disc_r * 2 + 10) + disc_r + 4
            cy2 = start_y + row * (disc_r * 2 + 16) + disc_r
            if cy2 + disc_r > by + bh - 24:
                break

            is_sel = self.selected_box_rotor == rname
            rim_col = C['brass_lt'] if is_sel else C['steel_lt']

            # Shadow
            pygame.gfxdraw.filled_ellipse(
                surf, cx2 + 3, cy2 + 4, disc_r, disc_r // 3, (0, 0, 0, 90)
            )

            # Rotor body from dark metal texture
            body_surf = tex_region(
                self._tex_metal_dk, disc_r * 2, disc_r * 2, ox=idx * 80, oy=idx * 60
            )
            if is_sel:
                tint_ov = pygame.Surface(body_surf.get_size())
                tint_ov.fill(C['fg_mid'])
                tint_ov.set_alpha(80)
                body_surf.blit(tint_ov, (0, 0))

            # Mask body to circle
            body_mask = pygame.Surface((disc_r * 2, disc_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(body_mask, (255, 255, 255, 255), (disc_r, disc_r), disc_r)
            body_alpha = body_surf.convert_alpha()
            body_alpha.blit(body_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            surf.blit(body_alpha, (cx2 - disc_r, cy2 - disc_r))

            # Concentric detail rings
            for dr in [disc_r - 5, disc_r - 10]:
                if dr > 0:
                    pygame.draw.circle(surf, C['steel_lt'], (cx2, cy2), dr, 1)

            # Rim
            pygame.draw.circle(surf, rim_col, (cx2, cy2), disc_r, 2)

            # Inner hub with rivet
            pygame.draw.circle(surf, C['brass_md'], (cx2, cy2), 9)
            pygame.draw.circle(surf, C['brass_dk'], (cx2, cy2), 9, 1)
            draw_rivet(surf, cx2, cy2, 3)

            # Engraved label
            f_lbl = self.f_xs if len(rname) > 3 else self.f_sm
            draw_text(surf, rname, f_lbl, (0, 0, 0), cx2 + 1, cy2 + 1)
            draw_text(surf, rname, f_lbl, C['brass_hi'], cx2, cy2)

            if is_sel:
                pygame.draw.circle(surf, C['highlight'], (cx2, cy2), disc_r + 3, 2)

            self.hb[f'box_{rname}'] = pygame.Rect(
                cx2 - disc_r, cy2 - disc_r, disc_r * 2, disc_r * 2
            )

        # Bottom hint
        hint_y = by + bh - 22
        if self.selected_box_rotor:
            draw_text(
                surf,
                f"\u25ba {self.selected_box_rotor} selected",
                self.f_xs,
                C['highlight'],
                bw // 2,
                hint_y - 10,
            )
            draw_text(surf, "click a slot to place", self.f_xs, C['text_dim'], bw // 2, hint_y + 2)
        else:
            draw_text(surf, "click rotor to select", self.f_xs, C['text_dim'], bw // 2, hint_y)

    # ── Machine Body ──────────────────────────────────────────────────────────

    def _draw_machine_body(self, surf):
        bx, by = MACHINE_X, MACHINE_TOP
        bw, bh = MACHINE_W, MACHINE_BOTTOM - MACHINE_TOP

        # Real feldgrau metal texture
        surf.blit(self._chassis_surf, (bx, by))
        pygame.draw.rect(surf, C['fg_dark'], (bx, by, bw, bh), 2)
        bevel_rect(surf, (bx, by, bw, bh), C['fg_hi'], C['fg_shadow'], 3)

        # Corner screws
        for rx, ry in [
            (bx + 10, by + 10),
            (bx + bw - 10, by + 10),
            (bx + 10, by + bh - 10),
            (bx + bw - 10, by + bh - 10),
        ]:
            draw_screw(surf, rx, ry, 5)

        # Mid-edge screws on long sides
        draw_screw(surf, bx + 10, by + bh // 2, 4)
        draw_screw(surf, bx + bw - 10, by + bh // 2, 4)

        # Nameplate — engraved brass
        np_rect = pygame.Rect(bx + bw // 2 - 112, by + 6, 224, 26)
        np_tex = tex_region(self._tex_metal, np_rect.width, np_rect.height, ox=400, oy=700)
        brass_tint = pygame.Surface(np_tex.get_size())
        brass_tint.fill(C['brass_dk'])
        brass_tint.set_alpha(140)
        np_tex.blit(brass_tint, (0, 0))
        surf.blit(np_tex, np_rect.topleft)
        bevel_rect(surf, np_rect, C['brass_lt'], C['brass_dk'])
        pygame.draw.rect(surf, C['brass_md'], np_rect, 1, border_radius=3)
        draw_text(
            surf,
            "CHIFFRIERMASCHINE",
            self.f_xs,
            (60, 44, 16),
            np_rect.centerx + 1,
            np_rect.centery + 1,
        )
        draw_text(
            surf, "CHIFFRIERMASCHINE", self.f_xs, C['brass_hi'], np_rect.centerx, np_rect.centery
        )

        cfg = MACHINE_CONFIGS[self.machine_type]
        ref_x = bx + 16
        ref_y = by + 38

        # ── Reflector selector ─────────────────────────────────────────────
        draw_text(surf, "UKW:", self.f_sm, C['text_gold'], ref_x, ref_y + 9, 'midleft')
        bx2 = ref_x + 44
        for rname in cfg['available_reflectors']:
            sel = rname == self.reflector
            r = pygame.Rect(bx2, ref_y, 68, 22)
            if sel:
                btn_tex = tex_region(self._tex_metal, r.width, r.height, ox=bx2)
                brass_ov = pygame.Surface(btn_tex.get_size())
                brass_ov.fill(C['brass_dk'])
                brass_ov.set_alpha(180)
                btn_tex.blit(brass_ov, (0, 0))
                surf.blit(btn_tex, r.topleft)
                bevel_rect(surf, r, C['brass_lt'], C['brass_dk'])
                draw_text(surf, rname, self.f_sm, C['text_dk'], r.centerx, r.centery)
            else:
                btn_tex2 = tex_region(self._tex_metal_fg, r.width, r.height, ox=bx2)
                dk_ov = pygame.Surface(btn_tex2.get_size())
                dk_ov.fill((8, 9, 7))
                dk_ov.set_alpha(80)
                btn_tex2.blit(dk_ov, (0, 0))
                surf.blit(btn_tex2, r.topleft)
                bevel_rect(surf, r, C['fg_hi'], C['fg_shadow'])
                draw_text(surf, rname, self.f_sm, C['text_lt'], r.centerx, r.centery)
            pygame.draw.rect(surf, C['brass_dk'] if sel else C['fg_shadow'], r, 1, border_radius=3)
            self.hb[f'ref_{rname}'] = r
            bx2 += 76

        # ── 4th rotor (M4 only) ────────────────────────────────────────────
        if self.machine_type == 'Enigma M4':
            f4y = by + 65
            draw_text(surf, "4th Rotor:", self.f_sm, C['text_gold'], ref_x, f4y + 9, 'midleft')
            bx3 = ref_x + 88
            for fr in cfg['fourth_rotors']:
                sel = fr == self.fourth_rotor
                r = pygame.Rect(bx3, f4y, 62, 22)
                bg = C['brass_md'] if sel else C['fg_mid']
                fg2 = C['text_dk'] if sel else C['text_lt']
                pygame.draw.rect(surf, bg, r, border_radius=4)
                bevel_rect(
                    surf,
                    r,
                    C['brass_lt'] if sel else C['fg_hi'],
                    C['brass_dk'] if sel else C['fg_shadow'],
                )
                draw_text(surf, fr, self.f_sm, fg2, r.centerx, r.centery)
                self.hb[f'4th_{fr}'] = r
                bx3 += 70

        # ── Rotor slots ────────────────────────────────────────────────────
        n = cfg['num_rotors']
        area_x = bx + 12
        area_w = bw - 24
        slot_y = by + 96
        slot_h = bh - 108
        slot_w = min(200, (area_w - (n - 1) * 10) // n)
        total_w = n * slot_w + (n - 1) * 10
        start_x = area_x + (area_w - total_w) // 2

        # Inset panel — recessed tray for rotors
        inset = pygame.Rect(start_x - 10, slot_y - 10, total_w + 20, slot_h + 20)
        inset_tex = tex_region(self._tex_metal_dk, inset.width, inset.height, ox=50, oy=200)
        dk_ov2 = pygame.Surface(inset_tex.get_size())
        dk_ov2.fill((2, 2, 1))
        dk_ov2.set_alpha(140)
        inset_tex.blit(dk_ov2, (0, 0))
        surf.blit(inset_tex, inset.topleft)
        pygame.draw.rect(surf, C['fg_dark'], inset, 2, border_radius=6)
        bevel_rect(surf, inset, C['fg_shadow'], C['fg_hi'], 2)

        # Screw at each corner of the inset tray
        for rx, ry in [
            (inset.left + 6, inset.top + 6),
            (inset.right - 6, inset.top + 6),
            (inset.left + 6, inset.bottom - 6),
            (inset.right - 6, inset.bottom - 6),
        ]:
            draw_screw(surf, rx, ry, 4)

        draw_text(
            surf, "\u2190 SLOW", self.f_xs, C['text_dim'], start_x + 4, slot_y - 14, 'midleft'
        )
        draw_text(
            surf,
            "FAST \u2192",
            self.f_xs,
            C['text_dim'],
            start_x + total_w - 4,
            slot_y - 14,
            'midright',
        )

        for i in range(n):
            sx = start_x + i * (slot_w + 10)
            self._draw_rotor_slot(surf, i, sx, slot_y, slot_w, slot_h)

        draw_text(
            surf,
            MACHINE_CONFIGS[self.machine_type]['description'],
            self.f_xs,
            C['text_dim'],
            bx + bw // 2,
            by + bh - 7,
        )

    # ── Rotor slot ────────────────────────────────────────────────────────────

    def _draw_rotor_slot(self, surf, idx, x, y, w, h):
        rotor_name = self.slots[idx] if idx < len(self.slots) else None
        is_m4_fourth = self.machine_type == 'Enigma M4' and idx == 0

        # Housing from dark metal texture
        slot_tex = tex_region(self._tex_metal_dk, w, h, ox=idx * 120, oy=100)
        if not rotor_name:
            # Empty slots are darker
            dk_ov = pygame.Surface(slot_tex.get_size())
            dk_ov.fill((0, 0, 0))
            dk_ov.set_alpha(60)
            slot_tex.blit(dk_ov, (0, 0))
        surf.blit(slot_tex, (x, y))

        edge = (
            C['brass_md']
            if rotor_name
            else (C['highlight'] if self.selected_box_rotor else C['slot_edge'])
        )
        pygame.draw.rect(surf, edge, (x, y, w, h), 2, border_radius=6)
        bevel_rect(surf, (x, y, w, h), C['fg_hi'], C['fg_shadow'])

        label = "4TH" if is_m4_fourth else f"#{idx + 1}"
        draw_text(surf, label, self.f_xs, C['text_dim'], x + w // 2, y + 10)

        if rotor_name is None:
            draw_text(surf, "EMPTY", self.f_sm, C['text_dim'], x + w // 2, y + h // 2 - 8)
            if self.selected_box_rotor:
                draw_text(
                    surf, "[ place here ]", self.f_xs, C['highlight'], x + w // 2, y + h // 2 + 10
                )
            self.hb[f'slot_{idx}'] = pygame.Rect(x, y, w, h)
            return

        # Remove button
        if not is_m4_fourth:
            rm = pygame.Rect(x + w - 22, y + 4, 18, 18)
            pygame.draw.rect(surf, C['danger'], rm, border_radius=4)
            bevel_rect(surf, rm, (200, 60, 60), (100, 20, 20))
            draw_text(surf, "X", self.f_xs, C['ivory'], rm.centerx, rm.centery)
            self.hb[f'slot_{idx}_rm'] = rm

        # Rotor name badge — brass nameplate
        badge = pygame.Rect(x + 4, y + 4, w - 30, 22)
        badge_tex = tex_region(
            self._tex_metal, badge.width, badge.height, ox=200 + idx * 50, oy=600
        )
        brass_ov = pygame.Surface(badge_tex.get_size())
        brass_ov.fill(C['brass_dk'])
        brass_ov.set_alpha(200)
        badge_tex.blit(brass_ov, (0, 0))
        surf.blit(badge_tex, badge.topleft)
        bevel_rect(surf, badge, C['brass_lt'], C['brass_dk'])
        draw_text(
            surf,
            f"Rotor {rotor_name}",
            self.f_xs,
            (60, 44, 16),
            badge.centerx + 1,
            badge.centery + 1,
        )
        draw_text(
            surf, f"Rotor {rotor_name}", self.f_xs, C['brass_hi'], badge.centerx, badge.centery
        )

        # ── Amber backlit position window ──────────────────────────────────
        win_sz = min(68, w - 28)
        win_x = x + w // 2 - win_sz // 2
        win_y = y + 34

        # Outer bezel — deep dark recess
        bz_pad = 6
        bezel_r = pygame.Rect(
            win_x - bz_pad, win_y - bz_pad, win_sz + bz_pad * 2, win_sz + bz_pad * 2
        )
        pygame.draw.rect(surf, C['win_bezel'], bezel_r, border_radius=9)

        # Brass border ring around the window
        pygame.draw.rect(surf, C['brass_md'], bezel_r, 2, border_radius=9)
        bevel_rect(surf, bezel_r, C['brass_lt'], C['brass_dk'], 1)

        # Inner depth rings — aperture effect
        for i in range(3):
            shade = 18 + i * 16
            pygame.draw.rect(
                surf,
                (shade, shade // 2, shade // 7),
                (win_x - (3 - i), win_y - (3 - i), win_sz + (3 - i) * 2, win_sz + (3 - i) * 2),
                1,
                border_radius=6 - i,
            )

        # Amber backlit surface
        pygame.draw.rect(surf, C['win_bg'], (win_x, win_y, win_sz, win_sz), border_radius=4)

        # Vertical glow gradient (bright center, dark edges)
        glow_s = pygame.Surface((win_sz, win_sz), pygame.SRCALPHA)
        for gy in range(win_sz):
            t = math.sin(math.pi * gy / win_sz)
            a = int(72 * t)
            pygame.draw.line(glow_s, (*C['win_glow'], a), (0, gy), (win_sz, gy))
        surf.blit(glow_s, (win_x, win_y))

        # Adjacent letters (prev/next in window)
        letter = ALPHABET[self.slot_pos[idx]]
        prev_l = ALPHABET[(self.slot_pos[idx] - 1) % 26]
        next_l = ALPHABET[(self.slot_pos[idx] + 1) % 26]
        draw_text(surf, prev_l, self.f_xs, C['win_adj'], win_x + win_sz // 2, win_y + 9)
        draw_text(surf, next_l, self.f_xs, C['win_adj'], win_x + win_sz // 2, win_y + win_sz - 9)

        # Main letter — glowing amber
        draw_text(surf, letter, self.f_win, (80, 40, 5), x + w // 2 + 1, win_y + win_sz // 2 + 1)
        draw_text(surf, letter, self.f_win, C['win_letter'], x + w // 2, win_y + win_sz // 2)

        # Inner vignette — adds depth to aperture
        vig_s = pygame.Surface((win_sz, win_sz), pygame.SRCALPHA)
        for ei in range(5):
            a = max(0, 80 - ei * 16)
            pygame.draw.rect(
                vig_s,
                (0, 0, 0, a),
                (ei, ei, win_sz - ei * 2, win_sz - ei * 2),
                1,
                border_radius=max(3 - ei, 0),
            )
        surf.blit(vig_s, (win_x, win_y))

        # Bezel top-left highlight — catches the directional light source
        pygame.draw.line(
            surf,
            C['win_edge_hi'],
            (win_x - bz_pad, win_y - bz_pad),
            (win_x + win_sz + bz_pad, win_y - bz_pad),
        )
        pygame.draw.line(
            surf,
            C['win_edge_hi'],
            (win_x - bz_pad, win_y - bz_pad),
            (win_x - bz_pad, win_y + win_sz + bz_pad),
        )

        # ── Position arrows ────────────────────────────────────────────────
        ar_x = x + w - 18
        ar_cy = win_y + win_sz // 2
        for key_s, dy, lbl in [('_pu', -32, '\u25b2'), ('_pd', 14, '\u25bc')]:
            r = pygame.Rect(ar_x - 14, ar_cy + dy, 24, 22)
            btn_t = tex_region(self._tex_metal_fg, r.width, r.height, ox=ar_x, oy=ar_cy)
            dk_b = pygame.Surface(btn_t.get_size())
            dk_b.fill((5, 5, 4))
            dk_b.set_alpha(60)
            btn_t.blit(dk_b, (0, 0))
            surf.blit(btn_t, r.topleft)
            bevel_rect(surf, r, C['fg_hi'], C['fg_shadow'])
            draw_text(surf, lbl, self.f_xs, C['brass_lt'], r.centerx, r.centery)
            self.hb[f'slot_{idx}{key_s}'] = r

        # ── Ring setting ───────────────────────────────────────────────────
        ring_y = win_y + win_sz + 10
        rlabel = f"Ring: {self.slot_ring[idx] + 1:02d}/{ALPHABET[self.slot_ring[idx]]}"
        draw_text(surf, rlabel, self.f_xs, C['text_gold'], x + w // 2, ring_y + 12)
        for key_s, dy, lbl in [('_ru', 0, '\u25b2'), ('_rd', 20, '\u25bc')]:
            r = pygame.Rect(x + 5, ring_y + dy, 22, 18)
            btn_t2 = tex_region(self._tex_metal_fg, r.width, r.height, ox=x + 5)
            dk_b2 = pygame.Surface(btn_t2.get_size())
            dk_b2.fill((5, 5, 4))
            dk_b2.set_alpha(60)
            btn_t2.blit(dk_b2, (0, 0))
            surf.blit(btn_t2, r.topleft)
            bevel_rect(surf, r, C['fg_hi'], C['fg_shadow'])
            draw_text(surf, lbl, self.f_xs, C['brass_lt'], r.centerx, r.centery)
            self.hb[f'slot_{idx}{key_s}'] = r

        # ── Notch indicator ────────────────────────────────────────────────
        notches = ROTOR_DATA[rotor_name][1]
        if letter in notches:
            nc_x, nc_y = x + w - 10, ring_y + 8
            gl = pygame.Surface((24, 24), pygame.SRCALPHA)
            for gr, ga in [(11, 30), (8, 60), (5, 120)]:
                pygame.draw.circle(gl, (*C['notch'], ga), (12, 12), gr)
            surf.blit(gl, (nc_x - 12, nc_y - 12))
            pygame.draw.circle(surf, C['notch'], (nc_x, nc_y), 4)
            draw_text(surf, "NOTCH", self.f_xs, C['notch'], nc_x - 2, nc_y + 14, 'midright')

    # ── Plugboard ─────────────────────────────────────────────────────────────

    def _draw_plugboard(self, surf):
        surf.blit(self._plug_panel, (0, PLUG_Y))
        pygame.draw.line(surf, C['brass_md'], (0, PLUG_Y), (RIGHT_X, PLUG_Y), 2)
        pygame.draw.line(
            surf, C['brass_dk'], (0, PLUG_Y + PLUG_H - 1), (RIGHT_X, PLUG_Y + PLUG_H - 1), 1
        )
        bevel_rect(surf, (0, PLUG_Y, RIGHT_X, PLUG_H), C['fg_hi'], C['fg_shadow'])

        # Corner screws
        for rx, ry in [
            (8, PLUG_Y + 8),
            (RIGHT_X - 8, PLUG_Y + 8),
            (8, PLUG_Y + PLUG_H - 8),
            (RIGHT_X - 8, PLUG_Y + PLUG_H - 8),
        ]:
            draw_screw(surf, rx, ry, 5)

        draw_text(
            surf,
            "STECKERBRETT  (PLUGBOARD)",
            self.f_head,
            C['text_gold'],
            RIGHT_X // 2,
            PLUG_Y + 11,
        )
        n_pairs = len(self.plug_pairs) // 2
        draw_text(
            surf,
            f"{n_pairs}/13 pairs",
            self.f_xs,
            C['text_dim'],
            RIGHT_X - 60,
            PLUG_Y + 11,
            'midright',
        )

        PK_W, PK_H, PK_GAP, PK_GAP_V = 48, 30, 7, 6

        letter_centres: dict[str, tuple[int, int]] = {}
        for ri, row in enumerate(KB_ROWS):
            row_w = len(row) * PK_W + (len(row) - 1) * PK_GAP
            rx = (RIGHT_X - row_w) // 2
            ry = PLUG_Y + 26 + ri * (PK_H + PK_GAP_V)
            for ci, letter in enumerate(row):
                bx, by = rx + ci * (PK_W + PK_GAP), ry
                cx2, cy2 = bx + PK_W // 2, by + PK_H // 2
                letter_centres[letter] = (cx2, cy2)

                paired = letter in self.plug_pairs
                first_sel = letter == self.plug_first

                r = pygame.Rect(bx, by, PK_W, PK_H)

                # Button surface — bakelite texture for plug keys
                btn_bak = tex_region(self._tex_bakelite, PK_W, PK_H, ox=cx2, oy=cy2)
                if first_sel:
                    # Selected: brass tint
                    br_ov = pygame.Surface(btn_bak.get_size())
                    br_ov.fill(C['brass_md'])
                    br_ov.set_alpha(200)
                    btn_bak.blit(br_ov, (0, 0))
                elif paired:
                    # Paired: warm copper tint
                    co_ov = pygame.Surface(btn_bak.get_size())
                    co_ov.fill(C['plug_paired'])
                    co_ov.set_alpha(200)
                    btn_bak.blit(co_ov, (0, 0))
                else:
                    # Unpaired: just darken the bakelite
                    dk_ov = pygame.Surface(btn_bak.get_size())
                    dk_ov.fill((0, 0, 0))
                    dk_ov.set_alpha(90)
                    btn_bak.blit(dk_ov, (0, 0))

                surf.blit(btn_bak, r.topleft)
                bevel_rect(
                    surf,
                    r,
                    C['brass_lt'] if first_sel else C['fg_hi'],
                    C['brass_dk'] if first_sel else C['fg_shadow'],
                )
                pygame.draw.rect(
                    surf,
                    C['brass_md'] if (first_sel or paired) else C['fg_shadow'],
                    r,
                    1,
                    border_radius=4,
                )

                fg2 = C['text_dk'] if (first_sel or paired) else C['text_lt']
                # Engraved letter
                draw_text(surf, letter, self.f_sm, (0, 0, 0), cx2 + 1, cy2 + 1)
                draw_text(surf, letter, self.f_sm, fg2, cx2, cy2)
                self.hb[f'plug_{letter}'] = r

        # Copper bezier wires — drawn OVER buttons for visibility
        drawn: set = set()
        for a, b in self.plug_pairs.items():
            pair = frozenset([a, b])
            if pair in drawn:
                continue
            drawn.add(pair)
            if a in letter_centres and b in letter_centres:
                p0, p1 = letter_centres[a], letter_centres[b]
                # Shadow wire
                draw_bezier_wire(surf, (p0[0] + 1, p0[1] + 1), (p1[0] + 1, p1[1] + 1), (0, 0, 0), 4)
                # Dark core
                draw_bezier_wire(surf, p0, p1, C['brass_dk'], 4)
                # Bright copper highlight
                draw_bezier_wire(surf, p0, p1, C['plug_wire'], 2)
                # Thin bright center
                hi_col = tuple(min(255, c + 50) for c in C['plug_wire'])
                draw_bezier_wire(surf, p0, p1, hi_col, 1)

    # ── Lampboard ─────────────────────────────────────────────────────────────

    def _draw_lampboard(self, surf):
        surf.blit(self._lamp_panel, (0, LAMP_Y))
        pygame.draw.line(surf, C['brass_md'], (0, LAMP_Y), (RIGHT_X, LAMP_Y), 2)
        pygame.draw.line(
            surf, C['brass_dk'], (0, LAMP_Y + LAMP_H - 1), (RIGHT_X, LAMP_Y + LAMP_H - 1), 1
        )
        bevel_rect(surf, (0, LAMP_Y, RIGHT_X, LAMP_H), C['fg_hi'], C['fg_shadow'])

        # Corner screws
        for rx, ry in [
            (8, LAMP_Y + 8),
            (RIGHT_X - 8, LAMP_Y + 8),
            (8, LAMP_Y + LAMP_H - 8),
            (RIGHT_X - 8, LAMP_Y + LAMP_H - 8),
        ]:
            draw_screw(surf, rx, ry, 5)

        draw_text(surf, "LAMPENFELD", self.f_head, C['text_gold'], RIGHT_X // 2, LAMP_Y + 12)

        r = LAMP_RADIUS

        # Compute positions for all lamps
        lamp_positions: dict[str, tuple[int, int]] = {}
        for ri, row in enumerate(KB_ROWS):
            row_w = len(row) * (r * 2 + LAMP_GAP_H) - LAMP_GAP_H
            rx = (RIGHT_X - row_w) // 2
            row_dv = (LAMP_H - 28 - len(KB_ROWS) * r * 2) // (len(KB_ROWS) + 1)
            cy2 = LAMP_Y + 28 + ri * (r * 2 + row_dv + 4) + r
            for ci, letter in enumerate(row):
                cx2 = rx + ci * (r * 2 + LAMP_GAP_H) + r
                lamp_positions[letter] = (cx2, cy2)

        # Pass 1: draw all cold lamp housings
        for letter, (cx2, cy2) in lamp_positions.items():
            lit = letter == self.active_lamp
            if not lit:
                # Socket shadow
                pygame.draw.circle(surf, C['lamp_socket'], (cx2, cy2 + 2), r + 5)
                # Brass housing ring
                pygame.draw.circle(surf, C['lamp_ring'], (cx2, cy2), r + 5)
                pygame.draw.circle(surf, C['brass_md'], (cx2, cy2), r + 5, 2)
                # Cold dark glass
                pygame.draw.circle(surf, C['lamp_cold'], (cx2, cy2), r)
                pygame.draw.circle(surf, (30, 21, 8), (cx2, cy2), r * 2 // 3)
                # Cold glass reflections (two subtle arcs)
                pygame.draw.circle(surf, (46, 34, 14), (cx2 - r // 4, cy2 - r // 3), 3)
                pygame.draw.circle(surf, (36, 26, 10), (cx2 + r // 5, cy2 - r // 4), 2)
                draw_text(surf, letter, self.f_lamp, (72, 56, 32), cx2, cy2)

        # Pass 2: draw blooms for lit lamps (BLEND_ADD — additively lights cold lamps)
        if self.active_lamp and self.active_lamp in lamp_positions:
            cx2, cy2 = lamp_positions[self.active_lamp]
            gs = self._lamp_glow
            goff = gs.get_width() // 2
            surf.blit(gs, (cx2 - goff, cy2 - goff), special_flags=pygame.BLEND_ADD)

        # Pass 3: draw lit lamp on top
        for letter, (cx2, cy2) in lamp_positions.items():
            if letter == self.active_lamp:
                # Brass housing
                pygame.draw.circle(surf, C['lamp_ring'], (cx2, cy2), r + 5)
                pygame.draw.circle(surf, C['brass_lt'], (cx2, cy2), r + 5, 2)
                # Incandescent layers — warm core to white-hot center
                pygame.draw.circle(surf, C['lamp_warm'], (cx2, cy2), r)
                pygame.draw.circle(surf, C['lamp_bright'], (cx2, cy2), r * 2 // 3)
                pygame.draw.circle(surf, C['lamp_white'], (cx2, cy2), r // 3)
                # Specular flare
                pygame.draw.circle(surf, (255, 255, 255), (cx2 - r // 3, cy2 - r // 3), 2)
                draw_text(surf, letter, self.f_lamp, (55, 25, 5), cx2, cy2)

    # ── Keyboard ──────────────────────────────────────────────────────────────

    def _draw_keyboard(self, surf):
        surf.blit(self._kb_panel, (0, KEY_Y))
        pygame.draw.line(surf, C['brass_md'], (0, KEY_Y), (RIGHT_X, KEY_Y), 2)
        bevel_rect(surf, (0, KEY_Y, RIGHT_X, KEY_H), C['fg_hi'], C['fg_shadow'])

        # Corner screws
        for rx, ry in [
            (8, KEY_Y + 8),
            (RIGHT_X - 8, KEY_Y + 8),
            (8, SH - 8),
            (RIGHT_X - 8, SH - 8),
        ]:
            draw_screw(surf, rx, ry, 5)

        for ri, row in enumerate(KB_ROWS):
            row_w = len(row) * (KEY_W + KEY_GAP_H) - KEY_GAP_H
            rx = (RIGHT_X - row_w) // 2
            ry = KEY_Y + 16 + ri * (KEY_H_PX + KEY_GAP_V)

            for ci, letter in enumerate(row):
                kx = rx + ci * (KEY_W + KEY_GAP_H)
                ky = ry
                cx2 = kx + KEY_W // 2
                cy2 = ky + KEY_H_PX // 2
                pressed = letter == self.active_key

                # Pre-computed bakelite key body from real texture
                ks = self._key_down if pressed else self._key_up
                ksz = ks.get_width() // 2
                surf.blit(ks, (cx2 - ksz, cy2 - ksz))

                # Embossed/engraved letter
                off = 4 if pressed else 0
                if not pressed:
                    # Shadow for engraved depth
                    draw_text(surf, letter, self.f_key, (0, 0, 0), cx2 + 1, cy2 + 2)
                draw_text(
                    surf,
                    letter,
                    self.f_key,
                    (118, 110, 96) if pressed else C['bak_letter'],
                    cx2,
                    cy2 + off,
                )

                self.hb[f'key_{letter}'] = pygame.Rect(kx, ky, KEY_W, KEY_H_PX)

        draw_text(
            surf,
            "Click keys or type to encode  \u2502  Backspace to undo",
            self.f_xs,
            C['text_dim'],
            RIGHT_X // 2,
            KEY_Y + KEY_H - 8,
        )

    # ── Output Panel ──────────────────────────────────────────────────────────

    def _draw_output_panel(self, surf):
        panel = pygame.Rect(RIGHT_X, MACHINE_TOP, PANEL_W, SH - MACHINE_TOP)
        pygame.draw.rect(surf, C['paper'], panel)
        # Left edge — brass separator
        pygame.draw.line(surf, C['brass_md'], (RIGHT_X, HEADER_H), (RIGHT_X, SH), 3)
        pygame.draw.line(surf, C['brass_lt'], (RIGHT_X + 1, HEADER_H), (RIGHT_X + 1, SH), 1)

        # Ruled paper lines
        line_y = MACHINE_TOP + 48
        while line_y < SH - 8:
            pygame.draw.line(surf, C['paper_line'], (RIGHT_X + 8, line_y), (SW - 8, line_y), 1)
            line_y += 18

        # Subtle left margin line (like real paper)
        pygame.draw.line(
            surf, (190, 168, 140), (RIGHT_X + 28, MACHINE_TOP + 48), (RIGHT_X + 28, SH - 8), 1
        )

        draw_text(
            surf, "OUTPUT", self.f_head, C['text_dk'], RIGHT_X + PANEL_W // 2, MACHINE_TOP + 16
        )

        pos_str = "  ".join(ALPHABET[self.slot_pos[i]] for i in range(len(self.slots)))
        draw_text(
            surf,
            f"Positions: {pos_str}",
            self.f_sm,
            C['text_dk'],
            RIGHT_X + 12,
            MACHINE_TOP + 38,
            'midleft',
        )

        pygame.draw.line(
            surf, C['paper_line'], (RIGHT_X + 8, MACHINE_TOP + 50), (SW - 8, MACHINE_TOP + 50), 1
        )

        def wrap_block(label, text, y_start, colour):
            draw_text(surf, label, self.f_sm, C['text_dk'], RIGHT_X + 32, y_start, 'midleft')
            y = y_start + 18
            for line in textwrap.wrap(text if text else "(none)", width=20)[-12:]:
                draw_text(surf, line, self.f_sm, colour, RIGHT_X + 36, y, 'midleft')
                y += 17
                if y > SH - 58:
                    break
            return y

        y = MACHINE_TOP + 60
        y = wrap_block("INPUT:", self.input_text, y, (50, 75, 130))
        y += 4
        pygame.draw.line(surf, C['paper_line'], (RIGHT_X + 8, y), (SW - 8, y), 1)
        y += 6
        wrap_block("OUTPUT:", self.output_text, y, (130, 50, 50))

        draw_text(
            surf,
            f"{len(self.input_text)} chars encoded",
            self.f_xs,
            C['text_dim'],
            RIGHT_X + PANEL_W // 2,
            SH - 50,
        )

        clr = pygame.Rect(RIGHT_X + PANEL_W // 2 - 45, SH - 36, 90, 26)
        pygame.draw.rect(surf, C['danger'], clr, border_radius=5)
        bevel_rect(surf, clr, (200, 60, 60), (100, 20, 20))
        draw_text(surf, "CLEAR", self.f_sm, C['ivory'], clr.centerx, clr.centery)
        self.hb['clear_output'] = clr

    # ── Dropdown ──────────────────────────────────────────────────────────────

    def _draw_dropdown(self, surf):
        items = list(MACHINE_CONFIGS.keys())
        item_h = 40
        dw, dx = 290, 700 - 145
        dy = HEADER_H

        # Background from metal texture
        dd_tex = tex_region(self._tex_metal_fg, dw, len(items) * item_h + 4, ox=dx, oy=200)
        dk_ov = pygame.Surface(dd_tex.get_size())
        dk_ov.fill((12, 13, 10))
        dk_ov.set_alpha(220)
        dd_tex.blit(dk_ov, (0, 0))
        surf.blit(dd_tex, (dx, dy))
        pygame.draw.rect(
            surf, C['brass_md'], (dx, dy, dw, len(items) * item_h + 4), 2, border_radius=5
        )

        for i, mtype in enumerate(items):
            iy = dy + 2 + i * item_h
            ir = pygame.Rect(dx + 2, iy, dw - 4, item_h - 2)
            if mtype == self.machine_type:
                sel_tex = tex_region(self._tex_metal_fg, ir.width, ir.height, ox=dx, oy=iy)
                surf.blit(sel_tex, ir.topleft)
                bevel_rect(surf, ir, C['fg_hi'], C['fg_shadow'])
            draw_text(surf, mtype, self.f_med, C['text_gold'], dx + dw // 2, iy + item_h // 2 - 7)
            draw_text(
                surf,
                MACHINE_CONFIGS[mtype]['description'],
                self.f_xs,
                C['text_dim'],
                dx + dw // 2,
                iy + item_h // 2 + 9,
            )
            self.hb[f'dd_{mtype}'] = ir

    # ── Backspace Notice ──────────────────────────────────────────────────────

    def _draw_backspace_notice(self, surf):
        """Non-modal period-appropriate notice shown when backspace is pressed.

        Real Enigma operators had no undo — the rotor stepped on key contact
        and could not be reversed.  The notice fades out after ~4 seconds and
        never modifies cipher or rotor state.
        """
        if self.backspace_notice_timer <= 0:
            return

        # Fade out over the last 60 frames (~1 s)
        t = self.backspace_notice_timer
        alpha = 255 if t > 60 else int(t / 60 * 255)

        # Position: horizontal strip inside the output panel, vertically centred
        pad = 14
        nw = SW - RIGHT_X - pad * 2
        nh = 52
        nx = RIGHT_X + pad
        ny = (SH - nh) // 2 + 40  # slightly below dead-centre of the panel

        # Background — dark olive, like aged military-issue paper
        bg = pygame.Surface((nw, nh), pygame.SRCALPHA)
        bg.fill((42, 36, 18, alpha))
        surf.blit(bg, (nx, ny))

        # Border — thin, subdued
        border = pygame.Surface((nw, nh), pygame.SRCALPHA)
        pygame.draw.rect(border, (105, 88, 52, alpha), (0, 0, nw, nh), 1)
        surf.blit(border, (nx, ny))

        # Thin rule beneath the first line of text — telegraphic separator
        rule = pygame.Surface((nw - 16, 1), pygame.SRCALPHA)
        rule.fill((105, 88, 52, alpha))
        surf.blit(rule, (nx + 8, ny + 22))

        # Text — warm parchment, monospace at smallest available size
        ink = (214, 190, 132)
        line1 = self.f_xs.render('Enigma operators could not undo keystrokes.', True, ink)
        line2 = self.f_xs.render('Use Reset Position to start over.', True, ink)
        line1.set_alpha(alpha)
        line2.set_alpha(alpha)
        surf.blit(line1, (nx + 8, ny + 8))
        surf.blit(line2, (nx + 8, ny + 28))

    # ── Message Box ───────────────────────────────────────────────────────────

    def _draw_message_box(self, surf):
        bw, bh = 480, 180
        bx = (SW - bw) // 2
        by = (SH - bh) // 2

        dim = pygame.Surface((SW, SH), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 170))
        surf.blit(dim, (0, 0))

        # Box background from metal texture
        box_tex = tex_region(self._tex_metal_fg, bw, bh, ox=bx, oy=by)
        dk_ov = pygame.Surface(box_tex.get_size())
        dk_ov.fill((18, 20, 15))
        dk_ov.set_alpha(200)
        box_tex.blit(dk_ov, (0, 0))
        surf.blit(box_tex, (bx, by))
        pygame.draw.rect(surf, C['msgbox_edge'], (bx, by, bw, bh), 2, border_radius=10)
        bevel_rect(surf, (bx, by, bw, bh), C['fg_hi'], C['fg_shadow'], 2)

        # Corner screws
        for rx, ry in [
            (bx + 10, by + 10),
            (bx + bw - 10, by + 10),
            (bx + 10, by + bh - 10),
            (bx + bw - 10, by + bh - 10),
        ]:
            draw_screw(surf, rx, ry, 4)

        pygame.draw.circle(surf, C['danger'], (bx + 42, by + 52), 18)
        bevel_rect(surf, (bx + 24, by + 34, 36, 36), (200, 60, 60), (100, 20, 20))
        draw_text(surf, "!", self.f_med, C['ivory'], bx + 42, by + 52)

        for i, line in enumerate(textwrap.wrap(self.message_box, width=38)):
            draw_text(surf, line, self.f_sm, C['text_lt'], bx + bw // 2, by + 42 + i * 22)

        ok = pygame.Rect(bx + bw // 2 - 50, by + bh - 48, 100, 32)
        pygame.draw.rect(surf, C['success'], ok, border_radius=6)
        bevel_rect(surf, ok, (60, 190, 65), (30, 100, 35))
        draw_text(surf, "OK", self.f_med, C['ivory'], ok.centerx, ok.centery)
        self.hb['msgbox_ok'] = ok

    # ── Watermark ─────────────────────────────────────────────────────────────

    def _draw_watermark(self, surf):
        """Render a clickable hyperlink in the lower-left corner of the keyboard panel."""
        col = (130, 108, 62) if self._watermark_hover else (72, 60, 34)
        label = self.f_xs.render(WATERMARK_TEXT, True, col)
        x = 10
        y = SH - label.get_height() - 7
        surf.blit(label, (x, y))
        # Underline
        uw = label.get_width()
        uy = y + label.get_height() - 1
        pygame.draw.line(surf, col, (x, uy), (x + uw, uy))
        self.hb['watermark'] = pygame.Rect(x - 2, y - 2, uw + 4, label.get_height() + 5)

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self):
        while self.running:
            self._handle_events()
            self._update()
            self._draw()
            self.clock.tick(60)
        pygame.quit()
        sys.exit(0)


def main():
    app = EnigmaApp()
    app.run()


if __name__ == '__main__':
    main()
