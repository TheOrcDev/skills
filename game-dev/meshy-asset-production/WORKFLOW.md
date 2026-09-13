# Meshy recipe and receipts

Resolve the active subject's manifest/template first. Original proof references are in `ArtSource/3D/Meshy/<subject>/`; roster references are in `ArtSource/3D/Roster/Meshy/<subject>/`. Their manifests and current plan decisions govern any exceptions.

## Geometry recipe

The recorded unit production baseline is:

| Control | Recorded setting |
|---|---|
| Route | Image to 3D, Multi-view enabled |
| Model | Meshy 7 – Flagship |
| Model type / resolution | High Detail / Standard |
| Ultra / Split / Image Enhancement | Off |
| Texture during geometry | Off when exposed; texture is a child task |
| Smart Topology | Not selected; identity-first geometry |
| Pose | Subject's `meshyPose` and recorded exceptions |
| Visibility | Private; no Community publication |
| Geometry estimate | Historically 20 credits; verify live |

Map `01-front.png` → Main, `02-left.png` → Left, `03-back.png` → Back, `04-right.png` → Right. Verify actual thumbnails, including weapon tips, immediately before Generate. Do not upload `identity-reference.png` or `contact-sheet.png` as a single multi-view image.

Pose is usually A-Pose for the contracted humanoid route and off for Generic/custom creatures. Use the subject record rather than inferring from its appearance. Do not invent a seed, negative-prompt field, PBR switch or polygon slider that the live route does not expose.

## Texture recipe

The normal child task uses Meshy 7 – Flagship, Image Input, the same four views with Multi-view on, Generate PBR Maps on and 2K output. The historical charge is 10 credits; check the current estimate and allowance. Texture resizing to a subject's final 1K/2K budget happens during cleanup.

Inspect Base Color, Metallic, Roughness and Normal channels; some exports pack channels together. Record what the provider actually delivered. A separate Text Input texture pass is a material-correction option only when within the authorized route; preserve its exact prompt. The Devourer used explicit hide, flesh, keratin and bone descriptions to correct a mineral-looking surface. That exception is not the default for every organic subject.

## Preserve each task

Use the existing receipt template/schema and ledger structure; do not start a parallel accounting file. Fill observed values, not placeholders or inferred success:

- Subject, task ID/URL, parent ID for child jobs, UTC timestamps, non-secret account label and private status.
- Every visible setting, each source path/hash and slot, displayed cost, actual consumption and balance before/after.
- Original download paths, sizes/hashes, preview/settings captures, raw audit result, reviewer and candidate decision.
- Pending, failed or rejected states and explicit missing exports/evidence.

Keep original geometry FBX/GLB under `ArtSource/3D/Meshy/Raw/<subject>/<geometry-task-id>/`. Keep linked texture exports and their receipt in that task's child directory following the existing subject convention. Preserve provider ZIPs untouched; extracted members and later repairs are additional artifacts with provenance.

If a download fails, retry the download on the existing task through a supported route. Never regenerate geometry merely to recover an export. An uncertain submission is reconciled before resubmitting. Do not change browser security settings to bypass a blocked download.

## Verification and exit

Audit both available model formats with `tools/3d/audit_model.py` in raw mode; inspect source-material renders using `tools/3d/render_model_previews.py --material-mode source`. Run Blender scripts through Blender, not plain Python. Raw mode may permit missing textures or a high polygon count; record those limitations and require usable UV/material data before textured cleanup.

Check ledger arithmetic against actual task charges and the observed balance; annotate outside credits/adjustments rather than attributing them to this project. Commit only owned receipts/evidence when requested, and append the outcome and any open operator decision to the coordination board.
