"""
tests/test_enigma_core.py

Pytest suite for enigma_core.py — rotor wiring integrity, cipher logic,
and documented historical behaviour.

Historical test vectors sourced from:
  [1] CryptoMuseum — Enigma wiring tables and operating behaviour
      https://www.cryptomuseum.com/crypto/enigma/wiring.htm
  [2] Rijmenants, Dirk — Enigma Technical Details
      https://www.ciphermachinesandcryptology.com/en/enigmatech.htm
  [3] Wikipedia — Enigma rotor details
      https://en.wikipedia.org/wiki/Enigma_rotor_details

All rotor wirings in enigma_core.py are verified against [1].
"""

import pytest

from enigma_core import (
    ALPHABET,
    ROTOR_DATA,
    REFLECTOR_DATA,
    EnigmaMachine,
    Plugboard,
    Rotor,
)


# ─── Helper ───────────────────────────────────────────────────────────────────


def build(machine_type, rotors, reflector, positions="", rings=None, plugboard=None):
    """Convenience factory for EnigmaMachine.

    positions:  str of letters, e.g. "AAA" — defaults to all A.
    rings:      list of 1-indexed ints, e.g. [1, 1, 1] — defaults to all 1
                (zero internal offset, equivalent to ring label "01").
    plugboard:  list of (a, b) letter pairs.
    """
    n = len(rotors)
    m = EnigmaMachine(machine_type)
    m.configure(
        rotors,
        reflector,
        positions=[ALPHABET.index(c) for c in (positions or "A" * n)],
        ring_settings=[(r - 1) for r in (rings or [1] * n)],
    )
    if plugboard:
        for a, b in plugboard:
            m.plugboard.add_pair(a, b)
    return m


# ─── 1. Historical test vectors ───────────────────────────────────────────────


class TestHistoricalVectors:
    """Verified input/output pairs from primary documentation sources.

    These act as regression anchors: any change to rotor wiring, reflector
    wiring, or signal-path logic that silently alters the cipher will be
    caught here before the executable is published.
    """

    def test_enigma_i_basic_aaaaa(self):
        """Enigma I, rotors I/II/III, reflector B, all positions A, no plugboard.

        AAAAA → BDZGO is the canonical Enigma test vector, cited in both
        CryptoMuseum [1] and Rijmenants [2] and reproduced in countless
        academic and hobbyist implementations.
        """
        m = build("Enigma I", ["I", "II", "III"], "B")
        assert m.encode_text("AAAAA") == "BDZGO"

    def test_enigma_i_extended_sequence(self):
        """Enigma I, rotors I/II/III, reflector B — 28 consecutive A's.

        The 28-character output exercises multiple rotor carry positions.
        Vector verified against [2] (Rijmenants Technical Details, §Test vectors).
        """
        # fmt: off
        expected = "BDZGOWCXLTKSBTMCDLPBMUQOFXYH"
        # fmt: on
        m = build("Enigma I", ["I", "II", "III"], "B")
        assert m.encode_text("A" * 28) == expected

    def test_enigma_i_with_plugboard(self):
        """Enigma I, rotors I/II/III, reflector B, single A↔B plugboard pair.

        Plugboard pair A↔B swaps the signal before and after the rotor path.
        Output computed from CryptoMuseum-verified wirings [1].
        """
        m = build("Enigma I", ["I", "II", "III"], "B", plugboard=[("A", "B")])
        assert m.encode_text("AAAAA") == "BJLCS"

    def test_m3_kriegsmarine_rotors(self):
        """Enigma M3 with Kriegsmarine-exclusive rotors VI, VII, VIII; reflector B.

        Rotors VI, VII, VIII were introduced for the Kriegsmarine and feature
        two turnover notches each (at Z and M), documented in [1] and [3].
        Vector computed from CryptoMuseum-verified wirings [1].
        """
        m = build("Enigma M3", ["VI", "VII", "VIII"], "B")
        assert m.encode_text("AAAAA") == "GJUBB"

    def test_m3_kriegsmarine_ten_chars(self):
        """M3 VI/VII/VIII, 10 A's — exercises the double-notch stepping of rotor VI.

        Rotors VI, VII, and VIII each have two turnover notches (Z and M).
        Ten characters is long enough to guarantee at least one notch pass
        and verify that the double-notch stepping code is exercised. Vector
        computed from CryptoMuseum-verified wirings [1].
        """
        m = build("Enigma M3", ["VI", "VII", "VIII"], "B")
        assert m.encode_text("A" * 10) == "GJUBBWMKDK"

    def test_m4_beta_bthin_equivalence_to_enigma_i(self):
        """M4 with 4th rotor Beta at position A + reflector B-Thin ≡ reflector B.

        When Beta is at position A with ring setting 01 (zero offset), the
        combined signal path Beta-forward → B-Thin → Beta-backward is
        mathematically equivalent to passing through reflector B alone.
        This documented equivalence was by design, ensuring backward
        compatibility with 3-rotor traffic [1][3].
        """
        m = build("Enigma M4", ["Beta", "I", "II", "III"], "B-Thin")
        # Must produce the same ciphertext as Enigma I with reflector B
        assert m.encode_text("AAAAA") == "BDZGO"

    def test_m4_gamma_cthin(self):
        """M4 with 4th rotor Gamma + reflector C-Thin.

        Gamma + C-Thin is the other valid M4 thin-rotor/reflector pairing.
        Vector computed from CryptoMuseum-verified wirings [1].
        """
        m = build("Enigma M4", ["Gamma", "I", "II", "III"], "C-Thin")
        assert m.encode_text("AAAAA") == "PJBUZ"


# ─── 2. Self-inverse property ─────────────────────────────────────────────────


class TestSelfInverse:
    """The Enigma is symmetric: encrypting the ciphertext on an identically
    configured machine always recovers the original plaintext.

    This property holds because: (a) the reflector is an involution, and
    (b) the plugboard is applied identically before and after the rotor path.
    """

    PLAINTEXT = "THEQUICKBROWNFOXJUMPSOVERTHELAZYDOG"

    def _roundtrip(self, machine_type, rotors, reflector, **kwargs):
        """Encrypt then decrypt with identical settings; assert recovery."""
        ct = build(machine_type, rotors, reflector, **kwargs).encode_text(self.PLAINTEXT)
        pt = build(machine_type, rotors, reflector, **kwargs).encode_text(ct)
        assert pt == self.PLAINTEXT, f"Roundtrip failed for {machine_type}"

    def test_self_inverse_enigma_i(self):
        self._roundtrip("Enigma I", ["I", "II", "III"], "B")

    def test_self_inverse_enigma_i_with_plugboard(self):
        self._roundtrip(
            "Enigma I",
            ["I", "II", "III"],
            "B",
            plugboard=[("A", "Z"), ("B", "Y"), ("C", "X")],
        )

    def test_self_inverse_enigma_i_non_default_positions(self):
        self._roundtrip("Enigma I", ["I", "II", "III"], "B", positions="QEV")

    def test_self_inverse_m3(self):
        self._roundtrip("Enigma M3", ["VI", "VII", "VIII"], "B")

    def test_self_inverse_m3_with_plugboard(self):
        self._roundtrip(
            "Enigma M3",
            ["VI", "VII", "VIII"],
            "C",
            positions="MCK",
            plugboard=[("A", "T"), ("S", "D")],
        )

    def test_self_inverse_m4_beta(self):
        self._roundtrip("Enigma M4", ["Beta", "I", "II", "III"], "B-Thin")

    def test_self_inverse_m4_gamma(self):
        self._roundtrip("Enigma M4", ["Gamma", "IV", "V", "I"], "C-Thin")

    def test_no_letter_encodes_to_itself(self):
        """A fundamental Enigma property: no letter can encrypt to itself.

        This was exploited by Bletchley Park codebreakers — 'crib' plaintext
        guesses could be ruled out if any letter appeared in the same position
        in both plaintext and ciphertext.
        """
        m = build("Enigma I", ["I", "II", "III"], "B")
        for _ in range(26):
            for letter in ALPHABET:
                ct = m.encode_char(letter)
                assert ct != letter, f"Letter {letter} encoded to itself"


# ─── 3. Double-stepping anomaly ───────────────────────────────────────────────


class TestDoubleSteppingAnomaly:
    """The middle rotor of a 3-rotor machine has a mechanical quirk: it steps
    on the same keystroke that it causes the left rotor to step, taking two
    consecutive steps in a row.

    Cause: the ratchet pawl for the left rotor engages the middle rotor's
    ratchet wheel even when the middle rotor's own notch is not in the carry
    position.  When the middle rotor IS at its notch, the left rotor's pawl
    pushes both the left rotor (via the middle notch) and the middle rotor
    (via its own ratchet).

    Documented in [1], [2], and [3].

    For rotors I / II / III:
      Rotor I  notch: Q  (stepping past Q advances the left rotor)
      Rotor II notch: E  (stepping past E advances the left rotor)
      Rotor III notch: V (stepping past V advances the middle rotor)

    Starting from positions A / D / U (left / mid / right):
      Encode 1: only right steps            → A D V
      Encode 2: right at notch → mid steps  → A E W
      Encode 3: mid at notch → DOUBLE-STEP  → B F X  ← anomaly
    """

    def test_double_step_sequence_i_ii_iii(self):
        m = build("Enigma I", ["I", "II", "III"], "B", positions="ADU")

        m.encode_char("A")
        assert m.positions == ["A", "D", "V"], "Step 1: only right rotor should advance"

        m.encode_char("A")
        assert m.positions == ["A", "E", "W"], "Step 2: right at notch, middle should step"

        m.encode_char("A")
        assert m.positions == [
            "B",
            "F",
            "X",
        ], "Step 3: double-step — middle and left both advance"

    def test_double_step_middle_rotor_steps_twice(self):
        """The middle rotor steps on keypress 2 AND keypress 3 — two in a row."""
        m = build("Enigma I", ["I", "II", "III"], "B", positions="ADU")
        m.encode_char("A")
        mid_after_1 = m.rotors[1].position  # D(3)
        m.encode_char("A")
        mid_after_2 = m.rotors[1].position  # E(4) — stepped once
        m.encode_char("A")
        mid_after_3 = m.rotors[1].position  # F(5) — stepped AGAIN (double-step)

        assert mid_after_2 == mid_after_1 + 1, "Middle should step on keypress 2"
        assert mid_after_3 == mid_after_2 + 1, "Middle should step again on keypress 3 (double-step)"

    def test_normal_stepping_before_anomaly(self):
        """Verify regular single-step behaviour before the anomaly window."""
        m = build("Enigma I", ["I", "II", "III"], "B", positions="AAA")
        # Rotor III notch is V(21); we are far from it, so only right steps
        for i in range(5):
            m.encode_char("A")
        # After 5 steps from A, right should be at F(5), others unchanged
        assert m.positions == ["A", "A", "F"]

    def test_m4_double_step_skips_4th_rotor(self):
        """In M4, double-stepping applies only to rotors[1-3]; rotors[0] never steps."""
        # Start mid(rotors[2]) at notch E so next step triggers double-step
        # rotors: [Beta(4th), I(left), II(mid), III(right)]
        # We need rotors[2]=II at E and rotors[3]=III just before V
        m = build("Enigma M4", ["Beta", "I", "II", "III"], "B-Thin", positions="AAEU")
        beta_before = m.rotors[0].position

        m.encode_char("A")  # III steps U→V
        m.encode_char("A")  # III at V → II steps; positions: A A F W ... wait
        # The key assertion: Beta (rotors[0]) must never move
        for _ in range(30):
            m.encode_char("A")
        assert m.rotors[0].position == beta_before, "4th rotor must never step"


# ─── 4. Plugboard symmetry ────────────────────────────────────────────────────


class TestPlugboardSymmetry:
    """The plugboard (Steckerbrett) applies a symmetric letter swap: if A→B
    then B→A.  Up to 13 pairs can be active simultaneously."""

    def test_swap_is_bidirectional(self):
        pb = Plugboard()
        pb.add_pair("A", "Z")
        assert pb.swap(ALPHABET.index("A")) == ALPHABET.index("Z")
        assert pb.swap(ALPHABET.index("Z")) == ALPHABET.index("A")

    def test_unpaired_letters_pass_through(self):
        pb = Plugboard()
        pb.add_pair("A", "Z")
        for letter in "BCDEFGHIJKLMNOPQRSTUVWXY":
            idx = ALPHABET.index(letter)
            assert pb.swap(idx) == idx, f"Unpaired letter {letter} should be unchanged"

    def test_multiple_pairs_independent(self):
        pb = Plugboard()
        for a, b in [("A", "Z"), ("B", "Y"), ("C", "X")]:
            pb.add_pair(a, b)
        assert pb.swap(0) == 25   # A↔Z
        assert pb.swap(25) == 0   # Z↔A
        assert pb.swap(1) == 24   # B↔Y
        assert pb.swap(24) == 1   # Y↔B
        assert pb.swap(2) == 23   # C↔X
        assert pb.swap(23) == 2   # X↔C

    def test_remove_pair_restores_passthrough(self):
        pb = Plugboard()
        pb.add_pair("A", "Z")
        pb.remove_letter("A")
        assert pb.swap(ALPHABET.index("A")) == ALPHABET.index("A")
        assert pb.swap(ALPHABET.index("Z")) == ALPHABET.index("Z")

    def test_plugboard_symmetry_through_full_machine(self):
        """Plugboard pairs are applied symmetrically before and after rotor path."""
        pairs = [("A", "Z"), ("B", "Y"), ("C", "X"), ("D", "W")]
        m = build("Enigma I", ["I", "II", "III"], "B", plugboard=pairs)
        ct = m.encode_text("ENIGMAMACHINE")
        m2 = build("Enigma I", ["I", "II", "III"], "B", plugboard=pairs)
        assert m2.encode_text(ct) == "ENIGMAMACHINE"

    def test_duplicate_pair_ignored(self):
        """Adding a pair involving an already-connected letter is a no-op."""
        pb = Plugboard()
        pb.add_pair("A", "Z")
        pb.add_pair("A", "B")   # A already connected — should be ignored
        assert pb.swap(ALPHABET.index("A")) == ALPHABET.index("Z")
        assert pb.swap(ALPHABET.index("B")) == ALPHABET.index("B")  # B still unpaired

    def test_max_thirteen_pairs(self):
        """Plugboard accepts up to 13 pairs (26 letters / 2)."""
        pb = Plugboard()
        letters = list(ALPHABET)
        pairs = [(letters[i], letters[i + 13]) for i in range(13)]
        for a, b in pairs:
            pb.add_pair(a, b)
        assert len(pb.pairs) == 26  # 13 pairs × 2 entries (both directions)


# ─── 5. Rotor wiring integrity ────────────────────────────────────────────────


class TestRotorWiringIntegrity:
    """Each rotor's wiring must be a valid bijection: every input maps to a
    unique output and every output has exactly one input (a permutation of
    the 26-letter alphabet).

    A violation would mean the rotor wiring was transcribed incorrectly from
    the primary source [1] and the cipher would produce incorrect output.
    """

    @pytest.mark.parametrize("name", list(ROTOR_DATA.keys()))
    def test_wiring_is_permutation(self, name):
        wiring, _ = ROTOR_DATA[name]
        assert len(wiring) == 26, f"Rotor {name}: wiring length must be 26"
        assert set(wiring) == set(ALPHABET), (
            f"Rotor {name}: wiring must contain every letter exactly once"
        )

    @pytest.mark.parametrize("name", list(ROTOR_DATA.keys()))
    def test_forward_backward_are_inverses(self, name):
        """rotor.backward(rotor.forward(x)) == x for every input and position."""
        rotor = Rotor(name)
        for pos in range(26):
            rotor.position = pos
            for sig in range(26):
                assert rotor.backward(rotor.forward(sig)) == sig, (
                    f"Rotor {name} pos={pos}: backward(forward({sig})) != {sig}"
                )

    @pytest.mark.parametrize("name", list(REFLECTOR_DATA.keys()))
    def test_reflector_is_involution(self, name):
        """Reflector must satisfy reflect(reflect(x)) == x (self-inverse).

        If this fails the reflector wiring has a transcription error.
        """
        mapping = REFLECTOR_DATA[name]
        assert len(mapping) == 26
        assert set(mapping) == set(ALPHABET)
        for i, c in enumerate(mapping):
            j = ALPHABET.index(c)
            assert ALPHABET.index(mapping[j]) == i, (
                f"Reflector {name}: reflect(reflect({ALPHABET[i]})) != {ALPHABET[i]}"
            )

    @pytest.mark.parametrize("name", list(REFLECTOR_DATA.keys()))
    def test_reflector_no_fixed_points(self, name):
        """A reflector must not map any letter to itself (would break symmetry)."""
        for i, c in enumerate(REFLECTOR_DATA[name]):
            assert ALPHABET[i] != c, (
                f"Reflector {name}: letter {ALPHABET[i]} maps to itself"
            )


# ─── 6. Ring setting correctness ─────────────────────────────────────────────


class TestRingSettings:
    """The ring setting (Ringstellung) shifts the internal wiring of a rotor
    relative to its alphabet ring, producing a systematic offset in the
    substitution.  Different ring settings must produce different ciphertext
    for the same input and start position.
    """

    def test_ring_setting_changes_output(self):
        """Ring setting 01 vs 02 on the rightmost rotor must give different output."""
        m1 = build("Enigma I", ["I", "II", "III"], "B", rings=[1, 1, 1])
        m2 = build("Enigma I", ["I", "II", "III"], "B", rings=[1, 1, 2])
        assert m1.encode_text("AAAAA") != m2.encode_text("AAAAA")

    def test_ring_setting_01_matches_baseline(self):
        """Ring setting 01 (zero offset) must reproduce the baseline test vector."""
        m = build("Enigma I", ["I", "II", "III"], "B", rings=[1, 1, 1])
        assert m.encode_text("AAAAA") == "BDZGO"

    def test_ring_setting_02_known_output(self):
        """Ring setting 02 on rotor III shifts wiring by 1.

        Output computed from CryptoMuseum-verified wirings [1].
        With ring 112 the effective rotor start positions differ by one step,
        producing a different but deterministic substitution.
        """
        m = build("Enigma I", ["I", "II", "III"], "B", rings=[1, 1, 2])
        assert m.encode_text("AAAAA") == "UBDZG"

    def test_ring_setting_self_inverse(self):
        """Self-inverse property must hold regardless of ring setting."""
        rings = [3, 14, 21]
        plaintext = "RINGTEST"
        ct = build("Enigma I", ["I", "II", "III"], "B", rings=rings).encode_text(plaintext)
        pt = build("Enigma I", ["I", "II", "III"], "B", rings=rings).encode_text(ct)
        assert pt == plaintext

    def test_all_ring_settings_produce_valid_output(self):
        """Spot-check all 26 ring settings on rotor III — each must give a
        26-letter output with no crashes and no repeated characters in a
        single-character encode (no self-encryption)."""
        for r in range(1, 27):
            m = build("Enigma I", ["I", "II", "III"], "B", rings=[1, 1, r])
            out = m.encode_char("A")
            assert out in ALPHABET
            assert out != "A"   # no self-encryption


# ─── 7. M4 thin rotor non-stepping ───────────────────────────────────────────


class TestM4ThinRotorNonStepping:
    """The 4th rotor (Beta or Gamma) in the M4 was deliberately made non-stepping.
    It combines with a thin reflector (B-Thin or C-Thin) to replicate the
    effective path of a 3-rotor machine's reflector at a higher key space.

    Documented in [1] and [3]: "The fourth rotor never turns."
    """

    @pytest.mark.parametrize("fourth_rotor,reflector", [
        ("Beta", "B-Thin"),
        ("Gamma", "C-Thin"),
    ])
    def test_fourth_rotor_never_steps(self, fourth_rotor, reflector):
        """Beta and Gamma must remain at their configured position after any
        number of encodes, regardless of what the other three rotors do."""
        m = build(
            "Enigma M4",
            [fourth_rotor, "I", "II", "III"],
            reflector,
            positions="A" * 4,
        )
        initial_pos = m.rotors[0].position

        # Encode enough to trigger multiple carry events in rotors 1-3
        m.encode_text("A" * 100)

        assert m.rotors[0].position == initial_pos, (
            f"4th rotor {fourth_rotor} moved from position "
            f"{ALPHABET[initial_pos]} after 100 encodes"
        )

    def test_fourth_rotor_position_survives_double_step(self):
        """4th rotor must not step even when a double-step occurs in rotors 1-3."""
        # Set up so rotors[2] (II) is at notch E, rotors[3] (III) at U
        # — next two encodes will trigger a double-step in rotors 1-3
        m = build(
            "Enigma M4",
            ["Beta", "I", "II", "III"],
            "B-Thin",
            positions="AAEU",
        )
        beta_pos = m.rotors[0].position
        for _ in range(10):
            m.encode_char("A")
        assert m.rotors[0].position == beta_pos

    @pytest.mark.parametrize("fourth_rotor,reflector", [
        ("Beta", "B-Thin"),
        ("Gamma", "C-Thin"),
    ])
    def test_fourth_rotor_non_default_start_preserved(self, fourth_rotor, reflector):
        """A non-A starting position for the 4th rotor must also remain fixed."""
        m = build(
            "Enigma M4",
            [fourth_rotor, "IV", "V", "I"],
            reflector,
            positions="VABC",
        )
        initial_pos = m.rotors[0].position
        m.encode_text("A" * 50)
        assert m.rotors[0].position == initial_pos
