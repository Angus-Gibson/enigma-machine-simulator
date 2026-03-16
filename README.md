# Enigma Machine Simulator

A fully functional, visually authentic recreation of the German Enigma cipher machine, built with Python and Pygame. Supports all three Wehrmacht/Kriegsmarine variants with accurate rotor wirings, the double-stepping anomaly, plugboard, ring settings, and period-correct aesthetics rendered from real texture assets.

---

## Historical Background

The Enigma machine was an electro-mechanical cipher device used extensively by Nazi Germany during the Second World War. Originally developed commercially in the early 1920s, it was adopted by the German military in the late 1920s and became the backbone of German encrypted communications — used by the Army (*Wehrmacht*), Air Force (*Luftwaffe*), and Navy (*Kriegsmarine*) throughout the war.

The machine works by passing an electrical signal through a series of rotating substitution wheels (rotors), a fixed reflector, and a plugboard, producing a scrambled output letter for each key pressed. Crucially, the rotors advance with each keypress, meaning the substitution changes constantly — the same letter typed twice in a row produces two different cipher letters. The machine is also symmetric: if you encrypt a message, you can decrypt it by typing the ciphertext on an identically configured machine.

The Enigma's apparent security led German commanders to rely on it even for highly sensitive communications. Breaking it became one of the most consequential intellectual achievements of the war. Polish mathematicians — Marian Rejewski, Jerzy Różycki, and Henryk Zygalski — first cracked an early Enigma variant in 1932 using mathematical analysis and reconstructed rotors. They shared their methods with British and French intelligence in July 1939, weeks before the German invasion of Poland. At Bletchley Park, teams led by Alan Turing and Gordon Welchman built on this work to develop the Bombe, an electromechanical device that could systematically search for Enigma settings. Allied codebreakers, working with captured machines and codebooks, eventually read German traffic regularly — intelligence known as ULTRA, considered by many historians to have shortened the war by two years or more.

The four-rotor M4 variant, introduced by the Kriegsmarine in February 1942, was specifically designed to defeat Bombe attacks by adding a fourth rotor, and initially blinded Allied codebreakers to U-boat communications for nearly ten months — the longest Enigma blackout of the war.

---

## Machine Types

| Model | Service | Rotors | Notes |
|-------|---------|--------|-------|
| **Enigma I** | Wehrmacht / Luftwaffe | 3 (from I–V) | Standard Army/Air Force model, 1930s–1945 |
| **Enigma M3** | Kriegsmarine | 3 (from I–VIII) | Naval variant; Rotors VI–VIII have two turnover notches |
| **Enigma M4** | Kriegsmarine U-Boats | 4 (Beta/Gamma + I–VIII) | 4th thin rotor never steps; requires B-Thin or C-Thin reflector |

### Rotors
Each rotor implements a fixed letter substitution and advances the rotor to its left when it passes its turnover notch. Rotors VI, VII, and VIII (Kriegsmarine) have *two* notches and step twice per revolution. The fourth rotor on the M4 (Beta or Gamma) is fixed — it never steps — and combines with a paired thin reflector to replicate the three-rotor enigma's reflector behaviour at a higher security level.

### Double-Stepping Anomaly
The middle rotor of a three-rotor machine has a mechanical quirk: it steps on the same keystroke that causes the left rotor to step, meaning it takes two consecutive steps in a row. This is faithfully reproduced in the simulator.

---

## Installation

**Requirements:** Python 3.10+ and a working audio output (or PulseAudio on WSL2).

```bash
# Clone or copy the project folder, then:
cd enigma

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### WSL2 Note
Audio is routed automatically through PulseAudio via WSLg. No extra configuration is needed. If you see audio errors, ensure WSLg is running (`echo $PULSE_SERVER` should return a path).

---

## Running

```bash
cd enigma
.venv/bin/python main.py
```

The window opens at 1440×960 and scales responsively — drag the window corners or maximise it to fill the screen.

---

## Controls

### Physical Keyboard
Type any letter (A–Z) to encode it. The corresponding output letter lights on the lampboard and is appended to the output panel. Press **Backspace** to undo the last character. Press **Escape** to close any open dropdown or dismiss error messages.

### Machine Configuration (before encoding)

| Element | Location | Action |
|---------|----------|--------|
| **Machine type** | Header dropdown (`▼`) | Switch between Enigma I, M3, M4 — resets all settings |
| **Reflector (UKW)** | Top of machine body | Click a button to select A/B/C or B-Thin/C-Thin |
| **4th Rotor** | Machine body (M4 only) | Click Beta or Gamma |
| **Rotor storage box** | Left panel | Click a rotor disc to select it (highlighted in gold) |
| **Rotor slots** | Machine body (slots #1–#3/4) | Click an empty slot to place the selected rotor |
| **Remove rotor** | Red ✕ button on each slot | Returns rotor to the storage box |
| **Starting position** | ▲/▼ arrows beside each window | Step the rotor's starting letter up or down |
| **Ring setting** | ▲/▼ arrows at the bottom of each slot | Adjust the internal ring offset (shown as `01/A`–`26/Z`) |

### Plugboard (Steckerbrett)
Click any two unpaired letters in sequence to connect them with a cable — both buttons turn copper-coloured and a bezier wire is drawn between them. Click a paired letter to disconnect it. Up to 13 pairs can be connected simultaneously. The plugboard adds a final letter swap before and after the rotor path.

### Output Panel
The right-hand notepad shows the current rotor positions, the full input plaintext, and the ciphertext output. Press **CLEAR** to erase both texts.

### Buttons
| Button | Action |
|--------|--------|
| **RESET ALL** | Clears rotors, positions, ring settings, plugboard pairs, and output |
| **RESET POS** | Resets all rotor starting positions to A without clearing other settings |
| **CLEAR** | Erases input and output text only |

---

## Verifying Cipher Correctness

A known test vector for Enigma I with rotors I/II/III, Reflector B, all positions and ring settings at A, no plugboard: typing `AAAAA` should produce `BDZGO`. The simulator passes this test.

Encryption is symmetric: configure two instances identically and the output of one is the input of the other.

---

## Project Structure

```
enigma/
├── main.py            # Pygame GUI (~1400 lines) — all visuals and interaction
├── enigma_core.py     # Pure cipher logic — rotors, reflector, plugboard, machine
├── sound_manager.py   # Audio loading and playback with WSL2 fallback
├── requirements.txt
├── assets/
│   ├── wood.png       # Walnut wood grain texture (ambientCG)
│   ├── metal.png      # Brushed metal texture (ambientCG)
│   └── bakelite.png   # Bakelite surface texture (ambientCG)
└── sounds/
    ├── key_press.mp3  # Typewriter keypress (Freesound — BMacZero, CC0)
    ├── rotor_click.mp3# Mechanical ratchet (Freesound — InMotionAudio, CC0)
    └── place_rotor.mp3# Heavy mechanical thud (Freesound — BMacZero, CC0)
```

---

## Credits

### Texture Assets
Textures sourced from **[ambientCG](https://ambientcg.com)** (formerly Texture Haven), published under the **Creative Commons CC0 1.0 Universal** licence — no attribution required, free for any use.

- `wood.png` — Walnut wood grain
- `metal.png` — Brushed/painted metal surface
- `bakelite.png` — Dark bakelite phenolic resin surface

### Sound Assets
Sounds sourced from **[Freesound.org](https://freesound.org)**, all **CC0 Public Domain**:

- `key_press.mp3` — "typewriter.wav" by BMacZero ([freesound.org/s/160678](https://freesound.org/s/160678))
- `rotor_click.mp3` — "MECHRtch_Ratchet01" by InMotionAudio ([freesound.org/s/689528](https://freesound.org/s/689528))
- `place_rotor.mp3` — "Thud2.wav" by BMacZero ([freesound.org/s/96137](https://freesound.org/s/96137))

### Rotor Wirings
Verified against [CryptoMuseum — Enigma Wiring](https://www.cryptomuseum.com/crypto/enigma/wiring.htm) and the Enigma technical documentation.
