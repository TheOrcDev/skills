# Agent board

This is the shared channel between Claude Code and the operator. The rules are
in `../AGENTS.md`. The request files in `art-source/requests/` are the source of
truth for images; the full list is `../art-source/requests/INDEX.md`, rebuilt by
`bun tools/images/index.ts`.

## Open image requests

Requests that need the operator to look, or that are blocked.

| ID | Title | Status | Operator approval | Plan |
|---|---|---|---|---|

## Open operator decisions

| # | Question | Raised | Needed by |
|---|---|---|---|
| 1 | The image budget for each plan that uses the gateway (Sol on the ChatGPT plan is $0). | {{DATE}} | First gateway request |
| 2 | The ElevenLabs plan tier and credit ceiling. A paid tier (Starter or above) is needed for commercial use. | {{DATE}} | The voice spike |
| 3 | Individual or company as publisher. This sets the ElevenLabs tier needed for music. | {{DATE}} | The voice spike |
| 4 | An Apple Developer account for macOS signing and notarization: yes or no? | {{DATE}} | First public desktop build |
| 5 | Where the browser build is hosted, and whether it carries the full game or a demo part. | {{DATE}} | First deploy |

## Log

Append-only. Newest at the bottom. UTC.

- {{YYYY-MM-DDTHH:MMZ}} **Claude → @Operator:** The project is set up from the
  point-and-click-adventure kit. `tools/test.sh` passes, and the greybox chain passes in the
  macOS app and in Chrome (`docs/qa/001/`). **Next:** plan 002, the look.
