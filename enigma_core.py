"""
enigma_core.py
Authentic WWII German Enigma Machine logic.

Rotor wirings verified against:
  - Cryptomuseum.com/crypto/enigma/wiring.htm
  - Wikipedia: Enigma rotor details
  - Enigma Technical Documentation

Signal flow:  keyboard -> plugboard -> rotors (R→L) -> reflector
              -> rotors (L→R) -> plugboard -> lamp
"""

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# Tuple: (wiring_string, turnover_notch_positions)
# Turnover position = the rotor letter that, when *leaving* that position (stepping past it),
# causes the next rotor to step.  'Q' = rotor steps when position advances FROM Q to R.
# fmt: off
ROTOR_DATA = {
    'I':     ('EKMFLGDQVZNTOWYHXUSPAIBRCJ', 'Q'),    # Wehrmacht/Luftwaffe
    'II':    ('AJDKSIRUXBLHWTMCQGZNPYFVOE', 'E'),
    'III':   ('BDFHJLCPRTXVZNYEIWGAKMUSQO', 'V'),
    'IV':    ('ESOVPZJAYQUIRHXLNFTGKDCMWB', 'J'),
    'V':     ('VZBRGITYUPSDNHLXAWMJQOFECK', 'Z'),
    'VI':    ('JPGVOUMFYQBENHZRDKASXLICTW', 'ZM'),   # Kriegsmarine double-notch
    'VII':   ('NZJHGRCXMYSWBOUFAIVLPEKQDT', 'ZM'),
    'VIII':  ('FKQHTLXOCBJSPDZRAMEWNIUYGV', 'ZM'),
    # M4 4th-position thin rotors — never step, no turnover
    'Beta':  ('LEYJVCNIXWPBQMDRTAKZGFUHOS', ''),
    'Gamma': ('FSOKANUERHMBTIYCWLQPZXVGJD', ''),
}

REFLECTOR_DATA = {
    'A':       'EJMZALYXVBWFCRQUONTSPIKHGD',
    'B':       'YRUHQSLDPXNGOKMIEBFZCWVJAT',
    'C':       'FVPJIAOYEDRZXWGCTKUQSBNMHL',
    'B-Thin':  'ENKQAUYWJICOPBLMDXZVFTHRGS',   # M4 only
    'C-Thin':  'RDOBJNTKVEHMLFCWZAXGYIPSUQ',   # M4 only
}
# fmt: on

MACHINE_CONFIGS = {
    'Enigma I': {
        'num_rotors': 3,
        'available_rotors': ['I', 'II', 'III', 'IV', 'V'],
        'available_reflectors': ['A', 'B', 'C'],
        'fourth_rotors': [],
        'description': 'Wehrmacht / Luftwaffe (1930s)',
    },
    'Enigma M3': {
        'num_rotors': 3,
        'available_rotors': ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII'],
        'available_reflectors': ['B', 'C'],
        'fourth_rotors': [],
        'description': 'Kriegsmarine, 3-Rotor (1934)',
    },
    'Enigma M4': {
        'num_rotors': 4,
        'available_rotors': ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII'],
        'available_reflectors': ['B-Thin', 'C-Thin'],
        'fourth_rotors': ['Beta', 'Gamma'],
        'description': 'Kriegsmarine U-Boot, 4-Rotor (1942)',
    },
}


class Rotor:
    """One Enigma rotor wheel."""

    def __init__(self, name: str):
        self.name = name
        wiring, notches = ROTOR_DATA[name]
        self.wiring = wiring  # Forward mapping string
        self.notches = notches  # Letters at which turnover triggers next rotor
        self.position = 0  # 0–25  (A=0)
        self.ring_setting = 0  # 0–25  (01=0)

        # Pre-compute numeric forward/backward tables
        self._fwd = [ALPHABET.index(c) for c in wiring]
        self._bwd = [0] * 26
        for i, v in enumerate(self._fwd):
            self._bwd[v] = i

    @property
    def display_letter(self) -> str:
        return ALPHABET[self.position]

    @property
    def ring_label(self) -> str:
        return f"{self.ring_setting + 1:02d}"

    def at_notch(self) -> bool:
        """True when this rotor's current position will trigger the next rotor to step."""
        return ALPHABET[self.position] in self.notches

    def step(self):
        self.position = (self.position + 1) % 26

    def forward(self, signal: int) -> int:
        """Encipher signal passing right-to-left (entry side)."""
        idx = (signal + self.position - self.ring_setting) % 26
        out = self._fwd[idx]
        return (out - self.position + self.ring_setting) % 26

    def backward(self, signal: int) -> int:
        """Encipher signal passing left-to-right (return side)."""
        idx = (signal + self.position - self.ring_setting) % 26
        out = self._bwd[idx]
        return (out - self.position + self.ring_setting) % 26


class Reflector:
    """Enigma reflector (Umkehrwalze)."""

    def __init__(self, name: str):
        self.name = name
        self._map = [ALPHABET.index(c) for c in REFLECTOR_DATA[name]]

    def reflect(self, signal: int) -> int:
        return self._map[signal]


class Plugboard:
    """Enigma plugboard (Steckerbrett).  Up to 13 letter-pair swaps."""

    def __init__(self):
        self.pairs: dict[str, str] = {}
        self._map = list(range(26))

    def add_pair(self, a: str, b: str):
        if a in self.pairs or b in self.pairs:
            return  # Already connected
        ai, bi = ALPHABET.index(a), ALPHABET.index(b)
        self.pairs[a] = b
        self.pairs[b] = a
        self._map[ai] = bi
        self._map[bi] = ai

    def remove_letter(self, a: str):
        if a not in self.pairs:
            return
        b = self.pairs[a]
        del self.pairs[a]
        del self.pairs[b]
        ai, bi = ALPHABET.index(a), ALPHABET.index(b)
        self._map[ai] = ai
        self._map[bi] = bi

    def swap(self, signal: int) -> int:
        return self._map[signal]

    def clear(self):
        self.pairs = {}
        self._map = list(range(26))


class EnigmaMachine:
    """
    The complete Enigma machine.

    rotors list is ordered LEFT → RIGHT  (index 0 = leftmost / slowest).
    For M4:  rotors[0]=4th thin rotor (never steps), rotors[1-3]=normal rotors.
    """

    def __init__(self, machine_type: str = 'Enigma I'):
        self.machine_type = machine_type
        self.config = MACHINE_CONFIGS[machine_type]
        self.rotors: list[Rotor] = []
        self.reflector: Reflector | None = None
        self.plugboard = Plugboard()

    def configure(
        self,
        rotor_names: list[str],
        reflector_name: str,
        positions: list[int] | None = None,
        ring_settings: list[int] | None = None,
    ):
        n = self.config['num_rotors']
        if len(rotor_names) != n:
            raise ValueError(f"{self.machine_type} requires exactly {n} rotors.")

        self.rotors = [Rotor(name) for name in rotor_names]
        self.reflector = Reflector(reflector_name)

        if positions:
            for i, p in enumerate(positions):
                self.rotors[i].position = p % 26
        if ring_settings:
            for i, r in enumerate(ring_settings):
                self.rotors[i].ring_setting = r % 26

    def _step_rotors(self):
        """Advance rotors with authentic double-stepping anomaly."""
        n = len(self.rotors)
        if n == 3:
            mid, right = self.rotors[1], self.rotors[2]
            if mid.at_notch():
                mid.step()
                self.rotors[0].step()
            elif right.at_notch():
                mid.step()
            right.step()
        elif n == 4:
            # rotors[0] is the 4th thin rotor — never steps
            mid, right = self.rotors[2], self.rotors[3]
            if mid.at_notch():
                mid.step()
                self.rotors[1].step()
            elif right.at_notch():
                mid.step()
            right.step()

    def encode_char(self, char: str) -> str:
        """Encode one letter, advancing rotors first."""
        char = char.upper()
        if char not in ALPHABET:
            return char

        self._step_rotors()

        sig = ALPHABET.index(char)
        sig = self.plugboard.swap(sig)

        for rotor in reversed(self.rotors):
            sig = rotor.forward(sig)

        sig = self.reflector.reflect(sig)

        for rotor in self.rotors:
            sig = rotor.backward(sig)

        sig = self.plugboard.swap(sig)
        return ALPHABET[sig]

    def encode_text(self, text: str) -> str:
        return ''.join(self.encode_char(c) for c in text.upper() if c in ALPHABET)

    @property
    def positions(self) -> list[str]:
        return [ALPHABET[r.position] for r in self.rotors]
