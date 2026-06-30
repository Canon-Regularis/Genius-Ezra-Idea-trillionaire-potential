# Randomized Image Occlusion

An Anki add-on — *image occlusion, but better.*

Standard image occlusion hides a label at a **fixed** spot on a picture. Over
time you stop recalling the structure and start recalling the **position**: "the
box in the top-left is the aorta." That's spatial memorisation, not knowledge.

This add-on breaks that crutch. On **every review** it places the prompt box at a
**randomised** location and draws a leader-line arrow from the box to the
structure's fixed point. You can't lean on where the box is — you have to follow
the arrow and identify what it actually points at.

> Built as a request for Ezra. 💛

---

## How it works

* You load an image and click each structure to drop a numbered marker, typing a
  label for each. Coordinates are stored **normalized** (fractions of the image),
  so cards render correctly at any size or zoom.
* Each marker becomes one card (via Anki cloze ordinals — one note, many cards),
  exactly like Anki's built-in "hide one, guess one".
* At review time, a small renderer (baked into the card template, so it works on
  AnkiDroid/AnkiMobile **without** the add-on installed):
  1. reads the structures and which one this card tests,
  2. mints a per-review random **seed**, shared front→back via `sessionStorage`
     so the question and answer sides agree on the layout,
  3. places the prompt box at a random in-bounds spot away from the target, and
  4. draws an arrow from the box to the structure (a `?` on the front, the label
     on the back).

Randomisation is **purely presentational** — it never touches scheduling/FSRS.

## Requirements

* Anki **23.10+** (`min_point_version` 231000), Qt6.

## Install (development)

Anki loads add-ons from its `addons21/` folder. Symlink this package in:

```sh
# Windows (PowerShell, as admin)
New-Item -ItemType SymbolicLink `
  -Path "$env:APPDATA\Anki2\addons21\randomized_occlusion" `
  -Target "<repo>\src\randomized_occlusion"

# macOS / Linux
ln -s "<repo>/src/randomized_occlusion" \
  "~/.local/share/Anki2/addons21/randomized_occlusion"
```

Restart Anki, then open **Tools → Randomized Image Occlusion…**.

## Build a distributable add-on

```sh
python build.py    # writes dist/randomized_occlusion.ankiaddon
```

Double-click the `.ankiaddon` to install, or upload it to AnkiWeb.

## Develop & test

```sh
pip install -e ".[dev]"
pytest          # unit tests for the Anki-independent layers
ruff check .
mypy
```

The domain, config, note-type, and factory layers have **no Anki dependency** and
are fully unit tested. Only the thin editor/bootstrap shells require Anki.

## Architecture

The package is layered so that business logic never depends on Anki directly;
adapters ("gateways") invert that dependency, which keeps the core testable.

```text
src/randomized_occlusion/
├── __init__.py          # entry point; runs bootstrap only when aqt is present
├── bootstrap.py         # composition root: wires the menu + install hook
├── resources.py         # locates bundled web assets
├── domain/              # pure value objects: NormalizedPoint, Structure, StructureSet
├── config/              # defaults, ConfigService (+ provider abstraction), RenderConfig
├── notetype/            # NoteTypeSpec, TemplateAssembler, NoteTypeInstaller
├── collection/          # ModelGateway/MediaGateway (+ Anki impls), NoteFactory
├── ops/                 # the single undo-safe CollectionOp that adds notes
├── editor/              # MarkerBridge (pure) + Qt MarkerDialog + EditorLauncher
└── web/
    ├── review/render.js # the review-time renderer (embedded into the template)
    └── editor/          # the image-marking canvas (marker.html/js/css)
```

Design notes:

* **Dependency inversion** — `NoteTypeInstaller` and the ops depend on the
  `ModelGateway`/`MediaGateway` `Protocol`s, not on `col.models`/`col.media`. The
  in-memory fakes used in tests are Liskov-substitutable for the real gateways.
* **Single responsibility** — the note type is described (`spec`), assembled
  (`templates`), and installed (`installer`) by three separate collaborators.
* **One place to mutate** — every database change happens inside one
  `CollectionOp`, so the whole "add a card" action is a single undo step.
