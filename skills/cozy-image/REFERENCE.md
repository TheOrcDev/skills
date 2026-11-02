# Cozy image reference

## Setup

The skill needs the Studio MCP tools in your agent. Choose the one that matches where the user's Studio runs.

### Hosted Studio

Create one agent token per agent, so each one can be revoked on its own. Run this in the cozy-studio checkout; [docs/HOSTING.md](https://github.com/TheOrcDev/cozy-studio/blob/hosted-mode/docs/HOSTING.md) has the setup.

```bash
bun --env-file=.env.hosted run hosted:admin token create "Claude Code"
```

Register it for every project:

```bash
claude mcp add --scope user --transport http cozy-studio https://<your-studio>/mcp \
  --header "Authorization: Bearer <agent token>"
```

Any other MCP client that supports Streamable HTTP and custom headers can use the same URL and header.

### Local Studio

A cozy-studio checkout already registers the stdio server `cozy-studio-mcp` in its `.mcp.json`. To use it from other folders:

```bash
claude mcp add --scope user cozy-studio-mcp -- bun /absolute/path/to/cozy-studio/scripts/studio-mcp.ts
```

Studio must be running. If its API is not on port 17223, set `COZY_STUDIO_API_URL`.

### Both

In Studio, open Settings → Advanced & maintenance and set **Agent access (MCP)** to **Generate and cancel**. With **Read only**, the default, agents can search but not generate.

| | Hosted | Local |
|---|---|---|
| `publicUrl` | Absolute signed link, valid for 24 hours | `/library/...`; prefix it with `http://127.0.0.1:17223` |
| `studio_import_reference_file` | Not available | Available for **Allowed import folders** |
| Providers | ChatGPT | Every provider set up in Studio |

## `studio_generate` arguments

Unknown keys are rejected.

| Argument | Values | Default |
|---|---|---|
| `requestId` | `batch-` followed by letters, digits and hyphens, 8 to 128 characters in all | Required |
| `prompt` | Up to 32,000 characters | Required |
| `task` | `image_generate`, `image_edit`, `sprite_sheet`, `texture_generate`, `style_preset_card` | The recipe's default |
| `aspectRatio` | `1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, `21:9` | `1:1` |
| `imageSize` | `512px`, `1K`, `2K`, `4K` | `1K` |
| `count` | 1 to 16; each image is its own job | 1 |
| `negativePrompt` | Up to 16,000 characters | None |
| `referenceIds` | Up to 16 catalog image IDs | None |
| `recipeId`, `recipeParams` | From `studio_recipes` | None |
| `providerId` | From `studio_providers` | `chatgpt` |
| `workspaceId` | From `studio_workspaces` | Studio's default workspace |

## Results

- **Batch** (`studio_generate`, `studio_batch`):
  - `id`: the `requestId`.
  - `status`: `queued`, `running`, `needs_review`, `completed`, `partial`, `failed` or `cancelled`. `partial` means some images finished and others failed or were cancelled.
  - `counts`, and `jobs[]` with each job's `id`, `status` and `error`.
- **Job** (`studio_job`): `{ id, status, error, updatedAt }`. It is small, so use it for polling.
- **Catalog image** (`studio_catalog`):
  - `id`, `publicUrl` and `prompt`.
  - `thumbnailUrl`: a 512 px WebP, for a quick look.
  - `width`, `height`, `mimeType`, `fileSizeBytes`, `jobId`, `batchId` and `createdAt`.
  - Filters: `q`, `batch_id`, `job_id`, `workspace_id` and `recipe_id`; page with `limit` (up to 100) and `offset`.
  - When a link has expired, call `studio_catalog` again for a fresh one.

## Recipes

`studio_recipes` lists every recipe with its parameters, options and defaults. Pass `recipeId` and only the `recipeParams` you want to change; Studio fills in the rest from the defaults.

| Recipe | Use for | Main parameters |
|---|---|---|
| `spritesheet` | A sprite sheet in one image (task `sprite_sheet`) | `grid` (`2x2` to `8x8`, `1x6 Strip`), `style` (`Pixel Art (16-bit)`, `Vector Flat`, ...), `view`, `background` |
| `character` | A character reference sheet | `layout` (`Classic Turnaround`, `Expression Sheet`, ...), `style`, `shot`, `focus`, `hasReference` |
| `remaster` | Restoring or reworking a reference image | `style`, `lighting`, `color`, `fidelity` |
| `camera` | The same subject from a new camera angle, from a reference | `azimuth`, `elevation`, `distance`, `hasReference` |
| `cinematic` | A storyboard grid | `frames`, `rows`, `cols`, `genre`, `tone`, `lighting` |
| `styles` | A look written out field by field, shared across a set | See [A shared look](#a-shared-look) |
| `character-poses`, `character-sprites`, `character-scenes`, `character-variants`, `character-transforms` | Character Lab work from a reference | Read them from `studio_recipes` |

When you pass a reference to `character` or `camera`, set `hasReference: true`. A `spritesheet` with no reference must set both `view` and `style`, because their defaults (`Match Source`, `Preserve Style`) copy a source image. `remaster` always needs a reference.

`animation-sequence` and `sprite-atlas` are multi-step workflows that run from the Studio UI. Don't start them through MCP; hosted Studio doesn't offer them.

Example of a sprite sheet:

```json
{
  "requestId": "batch-slime-walk-2b9e",
  "recipeId": "spritesheet",
  "prompt": "Green slime monster walk cycle, one pose per cell, evenly spaced",
  "recipeParams": { "grid": "4x2", "style": "Pixel Art (16-bit)", "view": "Side Scroll", "background": "Chroma Green" }
}
```

## A shared look

The `styles` recipe sends a look to the provider as structured directives. Write the fields once and pass them unchanged with every image in a set.

`presetId` and `presetName` are required. They are labels only: they are not sent to the provider, and a look you write yourself can use any ID, such as `custom-` followed by a slug.

```json
{
  "recipeId": "styles",
  "recipeParams": {
    "presetId": "custom-storybook-gouache",
    "presetName": "Storybook gouache",
    "aesthetic": "Hand-painted storybook gouache with soft edges",
    "colorTone": "Muted teal and warm ochre, low saturation",
    "lightingShadow": "Soft overcast light, gentle long shadows",
    "textureMaterial": "Visible paper grain and dry-brush strokes",
    "negativePrompt": "photo, 3d render, glossy plastic, text"
  }
}
```

The fields are `aesthetic`, `subjectTreatment`, `colorTone`, `lightingShadow`, `textureMaterial`, `cameraComposition`, `atmosphereMood` and `renderingQuality`.

To restyle a reference without changing its subject, pose or framing, pass it in `referenceIds` and add `"mode": "PRESERVE_REFERENCE"` to `recipeParams`.

### Saved and installed styles

- **User styles.** `studio_user_styles` lists the user's saved styles. Each has `visualDna` and `avoidRules`.
- **Style packs.** `studio_extensions` lists the installed packs (`kind: "style-pack"`). `studio_extension_json` with `{ "extensionId": "<id>", "path": "search.json" }` lists a pack's presets by `id`, `name`, `categoryName` and `tags`.
  - The full preset text is in `runtime.json`, at about 2.5 KB per preset. That is usually more than an MCP client accepts in one tool result.
  - If it's too large, use the preset's `name` and `styleAnchors` as the starting point for your own fields.
- **Mapping into `recipeParams`.** Saved styles (`visualDna`) and pack presets (`style`) use the same snake_case keys:

  | Style key | Parameter |
  |---|---|
  | `aesthetic` | `aesthetic` |
  | `subject_treatment` | `subjectTreatment` |
  | `color_and_tone` | `colorTone` |
  | `lighting_and_shadow` | `lightingShadow` |
  | `texture_and_material` | `textureMaterial` |
  | `camera_and_composition` | `cameraComposition` |
  | `atmosphere_and_mood` | `atmosphereMood` |
  | `rendering_and_quality` | `renderingQuality` |

  Put `avoidRules`, or a preset's `negativePrompt`, in `negativePrompt`. Use the style's `id` as `presetId` and its `name` as `presetName`.

## References

Every reference is a catalog image ID.

- **Earlier results.** Use any `id` from `studio_catalog`.
- **A file, local Studio.** If the file is in one of the **Allowed import folders**, call `studio_import_reference_file` with `{ "requestId": "reference-<slug>-<hex>", "path": "/absolute/path.png" }`. Studio reads the file itself.
- **A file, otherwise.** Call `studio_import_reference` with `{ requestId, name, mimeType, base64, sha256 }`.
  - The bytes pass through your context, so shrink the image first. A 512 px JPEG is around 50 KB, or about 70,000 base64 characters.
  - The tool accepts PNG, JPEG, WebP and GIF up to 8 MiB.
  - `sha256` is the hash of the file itself, not of the base64 text.

  ```bash
  sips -Z 512 -s format jpeg input.png --out /tmp/ref.jpg   # or: magick input.png -resize 512x512 -quality 85 /tmp/ref.jpg
  shasum -a 256 /tmp/ref.jpg | cut -d' ' -f1
  base64 < /tmp/ref.jpg | tr -d '\n'
  ```

Both import tools return `catalogImageId`; put it in `referenceIds`. If an import times out, retry with the same `reference-` ID and the same content and name.

## Errors

| You see | Cause | Do |
|---|---|---|
| `MCP access denied` | Agent access is Off or Read only | Ask the user to set it to Generate and cancel |
| `Invalid tool arguments` with `issues` | A field is wrong or unknown | Fix the listed fields |
| `Unknown recipe. Use studio_recipes.` | Wrong `recipeId` | Check `studio_recipes` |
| `Catalog reference not found` or `is unavailable` | Wrong or deleted reference | Search `studio_catalog` again |
| 409 conflict on `studio_generate` | The same `requestId` was used with different input | Use a new `requestId` |
| The provider is not ready or signed out | The ChatGPT sign-in has expired | The user signs in again in Studio. For hosted Studio, they import their local sign-in again (HOSTING.md, step 5) |
| HTTP 401 from the MCP server | The token is missing, wrong or revoked | The user creates a new token |
| 401 when downloading | The link has expired | Call `studio_catalog` again |
| Connection refused (local) | Studio isn't running | Ask the user to start Studio |
