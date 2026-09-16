#!/usr/bin/env python3
"""Run author|package -> export -> review (-> reel) for one subject into a versioned work directory.

  python3 pipeline.py --contract <rig-contract.json> --version 1 [--stage all|author|package|export|review|reel]
                      [--source <model>] [--work <dir>] [--render all|keys|none] [--package-args "..."]

Layout: <work>/<subjectId>/v<N>/candidate/{<Folder>_Actions.blend, receipt.json, exports/}
        <work>/<subjectId>/v<N>/evidence/{review.json, frames/, preview/}
Default work dir: ./rig-it-work beside the contract. A version directory is never overwritten.

Environment: RIG_IT_BLENDER (Blender 4.5 binary), RIG_IT_PILLOW_PYTHON (a python with Pillow, for reel.py).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import contract as contract_module  # noqa: E402

BLENDER = Path(os.environ.get('RIG_IT_BLENDER', '/Applications/Blender.app/Contents/MacOS/Blender'))
CODEX_PILLOW = '/Users/orcdev/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'


def pillow_python() -> str:
    explicit = os.environ.get('RIG_IT_PILLOW_PYTHON')
    if explicit:
        return explicit
    for candidate in (sys.executable, CODEX_PILLOW):
        if candidate and Path(candidate).exists():
            probe = subprocess.run([candidate, '-c', 'import PIL'], capture_output=True)
            if probe.returncode == 0:
                return candidate
    raise SystemExit('reel.py needs a Python with Pillow; set RIG_IT_PILLOW_PYTHON or pip install pillow')


def blender(script: str, *args: str) -> str:
    if not BLENDER.exists():
        raise SystemExit(f'Blender not found at {BLENDER}; set RIG_IT_BLENDER')
    command = [str(BLENDER), '--background', '--factory-startup', '--python-exit-code', '1',
               '--python', str(HERE / script), '--', *args]
    print('+ ' + ' '.join(shlex.quote(c) for c in command), file=sys.stderr)
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        sys.stderr.write(result.stdout[-6000:])
        sys.stderr.write(result.stderr[-6000:])
        raise SystemExit(f'{script} failed ({result.returncode})')
    lines = [line for line in result.stdout.splitlines() if line.startswith('{')]
    return lines[-1] if lines else ''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract', required=True, type=Path)
    parser.add_argument('--version', type=int, required=True)
    parser.add_argument('--source', type=Path, help='override the contract source model (an Actions .blend, a raw export dir for package, or a multi-take FBX)')
    parser.add_argument('--work', type=Path, help='work directory (default: rig-it-work beside the contract)')
    parser.add_argument('--render', default='all', choices=['all', 'keys', 'none'])
    parser.add_argument('--view', default='three-quarter', choices=['three-quarter', 'front', 'side'])
    parser.add_argument('--skip-reel', action='store_true')
    parser.add_argument('--stage', default='all', choices=['all', 'author', 'package', 'export', 'review', 'reel'])
    parser.add_argument('--package-args', default='', help='extra arguments passed through to package_biped.py (quoted string)')
    parser.add_argument('--author-args', default='', help='extra arguments passed through to author_clips.py (quoted string)')
    args = parser.parse_args()
    row = contract_module.load(args.contract)
    subject = row['subjectId']
    source = args.source or (Path(row['source']['model']) if row['source'].get('model') else None)
    work = args.work or (args.contract.resolve().parent / 'rig-it-work')
    version_dir = work / subject / f'v{args.version}'
    candidate = version_dir / 'candidate'
    evidence = version_dir / 'evidence'
    blend = candidate / f"{row['folder']}_Actions.blend"
    receipt = candidate / 'receipt.json'
    exports = candidate / 'exports'
    stages = ['author' if row['family'] != 'mixamo-biped' else 'package', 'export', 'review', 'reel'] if args.stage == 'all' else [args.stage]
    if stages[0] in ('author', 'package') and version_dir.exists():
        raise SystemExit(f'{version_dir} exists; bump --version instead of overwriting an iteration')
    if 'author' in stages:
        if source is None:
            raise SystemExit('author needs a source model (contract source.model or --source)')
        print(blender('author_clips.py', '--contract', str(args.contract), '--source', str(source), '--output', str(candidate),
                      *shlex.split(args.author_args)))
    if 'package' in stages:
        if source is None:
            raise SystemExit('package needs --source <raw provider export dir>')
        print(blender('package_biped.py', '--contract', str(args.contract), '--raw', str(source), '--output', str(candidate),
                      *shlex.split(args.package_args)))
    if 'export' in stages:
        export_input = blend if blend.exists() else source
        if export_input is None or not Path(export_input).exists():
            raise SystemExit(f'export needs {blend} or a --source multi-take FBX')
        extra = ['--receipt', str(receipt)] if receipt.exists() else []
        print(blender('export_fbx.py', '--contract', str(args.contract), '--input', str(export_input), '--output', str(exports), *extra))
    if 'review' in stages:
        extra = ['--receipt', str(receipt)] if receipt.exists() else []
        print(blender('review_clips.py', '--contract', str(args.contract), '--exports', str(exports),
                      '--output', str(evidence), '--render', args.render, '--view', args.view, *extra))
    if 'reel' in stages and not args.skip_reel:
        if args.render != 'all' and args.stage == 'all':
            print(json.dumps({'reel': 'skipped: needs --render all'}))
        else:
            command = [pillow_python(), str(HERE / 'reel.py'), '--frames', str(evidence / 'frames'),
                       '--manifest', str(exports / 'animation-manifest.json'), '--output', str(evidence / 'preview')]
            subprocess.run(command, check=True)
    summary = {'subject': subject, 'candidate': str(candidate), 'evidence': str(evidence)}
    if receipt.exists():
        summary['receiptSha256'] = hashlib.sha256(receipt.read_bytes()).hexdigest()
    review = evidence / 'review.json'
    if review.exists():
        report = json.loads(review.read_text())
        summary['gateFailures'] = report.get('gateFailures')
        summary['technicalPass'] = report.get('technicalPass')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
