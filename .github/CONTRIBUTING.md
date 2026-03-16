# Contributing to Enigma Machine Simulator

Thank you for your interest in contributing. This document covers everything you need to know to report bugs, suggest features, and submit code changes.

---

## Table of Contents

1. [Running Locally](#running-locally)
2. [Reporting Bugs](#reporting-bugs)
3. [Suggesting Features](#suggesting-features)
4. [Submitting Pull Requests](#submitting-pull-requests)
5. [Code Style Guidelines](#code-style-guidelines)
6. [Historical Accuracy Policy](#historical-accuracy-policy)

---

## Running Locally

**Requirements:** Python 3.10+, a working display, and audio output (or PulseAudio on WSL2).

```bash
git clone https://github.com/Angus-Gibson/enigma-machine-simulator.git
cd enigma-machine-simulator

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
python main.py
```

The window opens at 1440×960 and scales responsively. See the main [README](../README.md) for WSL2 audio notes and a full controls reference.

**Running on Windows without Python:** download the pre-built `EnigmaMachineSimulator-vX.Y.Z.exe` from the [latest release](https://github.com/Angus-Gibson/enigma-machine-simulator/releases/latest).

---

## Reporting Bugs

Before opening an issue, please:

- Check the [existing issues](https://github.com/Angus-Gibson/enigma-machine-simulator/issues) to avoid duplicates.
- Verify the bug is reproducible on the latest commit of `main`.

When opening a bug report, include:

| Field | What to provide |
|---|---|
| **Steps to reproduce** | The exact sequence of actions that triggers the bug |
| **Expected behaviour** | What you expected to happen |
| **Actual behaviour** | What actually happened |
| **Enigma configuration** | Machine type, rotor selection, ring settings, plugboard pairs, starting positions |
| **Environment** | OS, Python version (`python --version`), pygame version (`pip show pygame`) |
| **Screenshot / recording** | Attach one if the bug is visual |

If the bug relates to incorrect cipher output, include:
- The full machine configuration
- Input plaintext and the (incorrect) ciphertext produced
- Expected ciphertext, with the source you used to verify it (e.g. a known test vector or a reference implementation)

---

## Suggesting Features

Feature requests are welcome. Open an issue and:

- Describe the feature and the problem it solves.
- Note whether it touches cipher logic, the GUI, or both.
- If the feature involves a real Enigma variant not currently modelled (e.g. the Railway Enigma or the Swiss K), include at least one primary or secondary source describing that variant's wiring and behaviour. See the [Historical Accuracy Policy](#historical-accuracy-policy) for why this matters.

---

## Submitting Pull Requests

1. **Fork** the repository and create a branch from `main`:
   ```bash
   git checkout -b fix/rotor-double-step
   # or
   git checkout -b feat/enigma-t-variant
   ```

2. **Keep changes focused.** One logical change per pull request. Mixing a bug fix with a refactor makes review harder.

3. **Follow [Conventional Commits](https://www.conventionalcommits.org/)** for your commit messages — the CI pipeline uses them to determine the semantic version bump:

   | Prefix | Effect | Example |
   |---|---|---|
   | `fix:` | Patch bump | `fix: correct turnover notch for rotor VI` |
   | `feat:` | Minor bump | `feat: add ring setting display to output panel` |
   | `feat!:` / `BREAKING CHANGE:` | Major bump | `feat!: replace plugboard API` |
   | `chore:`, `docs:`, `refactor:` | Patch bump (fallback) | `docs: update installation steps` |

4. **Test your changes** before submitting:
   - Manually verify the known test vector: Enigma I, rotors I/II/III, Reflector B, all positions and ring settings at A, no plugboard — typing `AAAAA` should produce `BDZGO`.
   - If you have changed rotor wirings or cipher logic, include the verification result in your PR description.

5. **Open the pull request** against `main`. In the description:
   - Summarise what changed and why.
   - Reference any related issues (`Closes #42`).
   - For cipher/wiring changes, list your cited sources (see below).

6. **CI must pass.** The GitHub Actions workflow lints with Black and Flake8, then builds the Windows executable. A red build blocks merge.

---

## Code Style Guidelines

The CI pipeline enforces style automatically using **Black** and **Flake8**. The lint step runs before the PyInstaller build and a failure blocks merge. Run both locally before pushing:

```bash
pip install black flake8
black --check main.py enigma_core.py sound_manager.py
flake8 main.py enigma_core.py sound_manager.py
```

Or apply black's formatting in-place:

```bash
black main.py enigma_core.py sound_manager.py
```

**Configuration** — both tools are configured to match the project's conventions:

| Tool | Config file | Key settings |
|---|---|---|
| Black | `pyproject.toml` | `line-length = 100`, `skip-string-normalization = true` (single quotes) |
| Flake8 | `.flake8` | `max-line-length = 100`, ignores E221/E271 (column-aligned assignments), E701/E702 (compact guard clauses) |

**Formatted data tables** — the rotor wiring, reflector, colour palette, and sound-file tables use intentional column alignment for readability and are protected with `# fmt: off` / `# fmt: on`. New data tables of the same kind should follow the same pattern.

**General**
- Follow [PEP 8](https://peps.python.org/pep-0008/) for naming and layout.
- Maximum line length: **100 characters**.
- Use descriptive names. Single-letter variables are only acceptable as loop indices or in well-established mathematical notation (e.g. rotor position arithmetic).

**Module responsibilities — keep them separated**

| File | Responsibility |
|---|---|
| `enigma_core.py` | Pure cipher logic only — no pygame imports, no I/O |
| `sound_manager.py` | Audio loading and playback only |
| `main.py` | All pygame GUI, event handling, and rendering |

Do not introduce pygame dependencies into `enigma_core.py`, and do not put cipher logic into `main.py`.

**Comments**
- Comment *why*, not *what*. The double-stepping anomaly implementation and the M4 thin-rotor behaviour are non-obvious — keep those comments.
- Preserve the section separator style (`# ─── Section name ───`) used throughout `main.py`.

**Asset paths**
- Always resolve asset paths through `resource_path()` (defined in `main.py`) or `_resource_path()` (defined in `sound_manager.py`). This ensures paths work both from source and inside the PyInstaller bundle. Never use `__file__` directly or hardcoded absolute paths.

---

## Historical Accuracy Policy

This simulator models real cipher machines. **Changes to rotor wirings, reflector wirings, turnover notch positions, or stepping behaviour must be accompanied by cited primary or secondary sources.** Pull requests that alter cipher logic without citations will not be merged, regardless of how plausible the change looks.

### What counts as an acceptable source

**Primary sources**
- Captured Enigma documentation held by national archives (NARA, TNA, BArch).
- Period German military signals manuals (*Schlüsselanleitung*).

**Authoritative secondary sources**
- [CryptoMuseum — Enigma Wiring](https://www.cryptomuseum.com/crypto/enigma/wiring.htm) — the standard reference used by this project.
- [Dirk Rijmenants' Enigma technical documentation](https://www.ciphermachinesandcryptology.com/en/enigmatech.htm).
- [Wikipedia: Enigma rotor details](https://en.wikipedia.org/wiki/Enigma_rotor_details) — acceptable as a cross-reference, not as a sole source.
- Peer-reviewed academic papers on Enigma cryptanalysis.
- Published books with documented research (e.g. *Seizing the Enigma* by David Kahn, *The Hut Six Story* by Gordon Welchman).

### What is not acceptable
- Undocumented "corrections" based on intuition.
- References to other open-source Enigma implementations without a primary source behind them — implementation bugs can propagate.
- AI-generated wiring tables.

### Verification requirement

Any change to `enigma_core.py` that touches `ROTOR_DATA`, `REFLECTORS`, or the signal-path logic must include in the PR description:

1. The specific value(s) changed and what they were before.
2. The source(s) that support the change, with URLs or publication details.
3. A known test vector confirming the cipher still produces correct output after the change.

The known test vectors currently used as the baseline are documented in the README under *Verifying Cipher Correctness*.

---

*If you are unsure whether a change falls within this policy, open an issue and ask before writing code.*
