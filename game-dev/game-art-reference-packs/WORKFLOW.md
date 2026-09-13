# Reference preparation workflow

Run commands from the actual repository root. Inspect the relevant registry entry, source turnaround record and preparer's CLI before changing inputs. Resolve any missing sparse-checkout paths from Git; do not regenerate art merely because the local checkout omitted it.

## Original proof subjects

For Thorgrim, Gray Rat and Giant Ant under the proof contract:

```sh
python3 tools/prepare_meshy_reference_packs.py --check
```

When the requested source/crop correction is recorded and ready to build:

```sh
python3 tools/prepare_meshy_reference_packs.py
python3 tools/prepare_meshy_reference_packs.py --check
```

The preparer owns its generated `ArtSource/3D/Meshy/manifest.json`, subject packs and templates. Inspect its pinned source/crop configuration before changing it. Raw exports and accepted production assets are separate from regenerated references.

## Remaining roster

Read `ArtSource/3D/Roster/subjects.json` and `ArtSource/3D/References/Turnarounds/roster-generation.json`. Correct the source record and, when necessary, `turnaround.viewCropOverrides` on the subject rather than modifying generated views.

```sh
python3 tools/prepare_roster_reference_packs.py --check
```

To rebuild after an authorized reference change:

```sh
python3 tools/prepare_roster_reference_packs.py
python3 tools/prepare_roster_reference_packs.py --check
```

This command can rebuild multiple subjects. Review the full diff; coordinate any shared registry/preparer changes, and keep unrelated subjects out of the commit. Packs live under `ArtSource/3D/Roster/Meshy/<subject>/`; the manifest is `ArtSource/3D/Roster/manifest.json`.

## Inspect the output

| File | Purpose |
|---|---|
| `views/01-front.png` | Meshy Main View |
| `views/02-left.png` | Meshy Left |
| `views/03-back.png` | Meshy Back |
| `views/04-right.png` | Meshy Right |
| `contact-sheet.png` | Local crop/order review |
| `generation-receipt.template.json` | Template for a later provider task |

Check view direction, framing and missing/fused appendages visually; verify the manifest hashes against the files that will actually be uploaded. Upload only project-owned, approved source material within the repository's rights boundary.

When preparer behavior changes, run its corresponding `tools.tests.test_prepare_meshy_reference_packs` or `tools.tests.test_prepare_roster_reference_packs` unittest module. For a source-only change, the preparer's `--check` plus visual crop inspection is the direct verification.

Report which packs changed and whether operator review is outstanding. Stage only the claimed source, generated reference and lineage paths when a commit is requested; append the slice outcome to the coordination board.
