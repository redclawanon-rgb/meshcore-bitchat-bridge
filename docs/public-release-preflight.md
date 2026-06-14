# Public release preflight (local-only)

Date: 2026-06-14

This is a local release-hygiene artifact for Gate 1 public repository prep. It records readiness, required checks, target details still needed, and stop criteria. Creating or updating this file does **not** authorize creating a public repository, adding a remote, pushing, tagging, publishing a release, opening issues/wiki, or posting publicly.

## Current readiness status

- Local-only MVP docs and no-hardware demo/test coverage are ready for a conservative public-source review.
- The project remains a no-hardware, text-only bridge-frame and adapter-seam demonstration.
- The current branch is `main` and no Git remote is configured locally at the time of this preflight.
- Full stock bitchat compatibility, stock app/BLE interoperability, privacy preservation, Noise coverage, production readiness, and production security are **not claimed**.
- Live serial, BLE, hardware, network, secrets, public repository state, tags/releases, and public posts remain gated behind separate explicit approval.
- A public release target is **not ready to execute** until the target details below are provided and approved.

## Docs inspected for public-release-facing wording

- `README.md`
- `STATUS.md`
- `THREAT_MODEL.md`
- `BITCHAT_SEAM.md`
- `docs/mvp-handoff-index.md`
- `docs/gated-next-loops.md`

Local scan focus:

- Accidental secrets/tokens/credentials/private keys.
- Private endpoints or private filesystem paths.
- Unsupported claims around stock bitchat compatibility/interoperability.
- Unsupported claims around privacy, Noise, production readiness, or production security.

Result: no obvious accidental raw secrets/tokens/credentials/private keys were found in the inspected public-facing docs. The scanned claim-language hits were non-claims, stop criteria, blocker language, or public upstream GitHub links already documented as source-inspection evidence.

## Exact pre-push commands

Run these from the project root before any approved public push/tag/release action:

```bash
git status --short
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
python3 -m unittest discover -s tests -v
```

Optional local doc scan commands before public action:

```bash
python3 - <<'PY'
from pathlib import Path
import re
files = [
    Path('README.md'),
    Path('STATUS.md'),
    Path('THREAT_MODEL.md'),
    Path('BITCHAT_SEAM.md'),
    Path('docs/mvp-handoff-index.md'),
    Path('docs/gated-next-loops.md'),
    Path('docs/public-release-preflight.md'),
]
patterns = {
    'secret/token/private-key marker': re.compile(r'(api[_-]?key|token|secret|password|passwd|bearer|private[_-]?key|BEGIN (RSA|OPENSSH|PRIVATE)|ghp_|github_pat_|xox[baprs]-|AKIA[0-9A-Z]{16}|AIza)', re.I),
    'unsupported-claim review marker': re.compile(r'(stock bitchat|interoperab|compatible|privacy|private|Noise|Nostr|production[- ]ready|production security|secure)', re.I),
    'private-path/endpoint review marker': re.compile(r'(/home/[^\s)`]+|/Users/[^\s)`]+|ssh://|https://[^\s)>]+)', re.I),
}
for file in files:
    text = file.read_text(encoding='utf-8')
    for idx, line in enumerate(text.splitlines(), 1):
        for label, rx in patterns.items():
            if rx.search(line):
                print(f'{file}:{idx}: {label}')
PY
```

Review the scan output by category only; do not paste raw secret values into issues, docs, commits, chats, or public posts if a real secret is ever found.

## Target details still needed before public side effects

Public action must stop until Eric explicitly provides and approves:

- Repository owner/organization.
- Repository name.
- Visibility: public/private/internal at creation time, plus whether/when to switch public.
- License choice and whether to add a tracked `LICENSE` file before publication.
- Default branch name and whether history should be published as-is.
- Remote URL and remote name to configure, if any.
- Whether issues should be enabled.
- Whether discussions should be enabled.
- Whether wiki should be enabled.
- Whether GitHub releases should be enabled.
- Whether to create any tags/releases, and the exact tag/release name/body if yes.
- Whether to publish package artifacts or only source.
- Whether to include an announcement/public post, and approved wording/channel if yes.
- Whether any private local paths, names, or historical commits require cleanup before publishing history.

## Non-claim wording checklist

Before public action, confirm public-facing wording still says or implies:

- This is experimental/local-first MVP work.
- No full stock bitchat app compatibility claim.
- No existing bitchat BLE mesh interoperability claim.
- No private DM support claim.
- No Noise tunnel or E2EE preservation claim.
- No Nostr bridge claim.
- No image/file transfer claim.
- No production readiness/security/privacy claim.
- No real serial/BLE/hardware path is opened by default.
- `tools/bridge_serial.py` is dry-run/no-port-opened by default and real port access requires explicit `--open-real-port` approval.
- The bitchat-side seam is semantic public text only and does not forge stock `BitchatPacket` bytes.
- The MeshCore data type remains a development value (`0xFFFF`), not a registered production namespace.

## Stop criteria

Stop before any public side effect if any of these are true:

- Target owner/repo name/visibility/license/settings are unclear.
- Tests fail.
- `git status --short` shows unexpected changes.
- A scan suggests a possible real secret/token/private key/credential in tracked files.
- Docs imply stock bitchat compatibility, privacy preservation, production readiness, or security beyond lab/local scope.
- A remote, tag, release, issue/wiki/discussion setting, package publish, or public post would be created without explicit approval.
- The action would use live serial, BLE, hardware, network credentials, or private messages without the relevant separate gate being opened.

## Public action performed

Gate 1 source-only publication was approved by Eric and completed after this preflight.

- Repository: <https://github.com/redclawanon-rgb/meshcore-bitchat-bridge>
- Visibility: public
- Default branch: `main`
- Remote: `origin` -> `https://github.com/redclawanon-rgb/meshcore-bitchat-bridge.git`
- License: MIT, tracked in `LICENSE` and detected by GitHub
- Issues: enabled
- Wiki: disabled
- Discussions: disabled
- Tags/releases: none created
- Package artifacts: none published
- Public announcement/post: none made

Future public tags/releases/posts or settings changes remain separate gated actions.
