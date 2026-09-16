#!/usr/bin/env python3
"""Assemble labeled three-second preview sections (30 fps) from reviewed frames.

  python3 reel.py --frames <evidence>/frames --manifest <exports>/animation-manifest.json --output <evidence>/preview

Loops play without their duplicated endpoint; one-shots play once and hold the
final frame; Death never resets inside its section. Longer one-shots also get a
complete uncut clip. Requires Pillow and FFmpeg. Subject and folder come from the manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont

FFMPEG = shutil.which('ffmpeg') or '/opt/homebrew/bin/ffmpeg'
FFPROBE = shutil.which('ffprobe') or '/opt/homebrew/bin/ffprobe'
DESCRIPTIONS = {
    'Idle': 'Breathing / looking / secondary motion',
    'Locomotion': 'Travel over a visible floor at nominal speed',
    'BasicAttack': 'Anticipation / strike / recovery',
    'Cast': 'Ability telegraph / release / recovery',
    'Hit': 'Recoil / recover',
    'Death': 'Loss of support / settle / hold',
}


def font(size: int):
    for candidate in ('/System/Library/Fonts/Supplemental/Arial.ttf', '/System/Library/Fonts/Helvetica.ttc',
                      '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def duration(path: Path) -> float:
    return float(subprocess.check_output([FFPROBE, '-v', 'error', '-show_entries', 'format=duration',
                                          '-of', 'default=noprint_wrappers=1:nokey=1', str(path)]))


def validate_frames(root: Path, manifest: dict, clips: list[str] | None = None) -> dict:
    """Fail before encoding if key-only or interrupted renders could look complete."""
    if manifest.get('fps') != 30 or not manifest.get('clips'):
        raise ValueError('Expected a nonempty 30 fps manifest')
    result = {}
    dimensions = None
    for entry in manifest['clips']:
        name = entry['name']
        if clips is not None and name not in clips:
            continue
        if not name or Path(name).name != name or name in result:
            raise ValueError('Invalid or duplicate clip name')
        first, last = entry['frameRange']
        if type(first) is not int or type(last) is not int or first < 0 or last <= first:
            raise ValueError(f'Invalid frame range for {name}')
        expected = [root / name / f'frame-{i:03}.png' for i in range(first, last + 1)]
        actual = sorted((root / name).glob('frame-*.png')) if (root / name).is_dir() else []
        if set(actual) != set(expected):
            raise ValueError(f'Incomplete or extra frames for {name}: expected {len(expected)}, got {len(actual)} '
                             '(render the review with --render all)')
        for path in expected:
            with Image.open(path) as frame:
                size = frame.size
                if dimensions is None:
                    dimensions = size
                if size != dimensions:
                    raise ValueError(f'Mixed frame dimensions: {path}')
                frame.verify()
        result[name] = expected
    if not result:
        raise ValueError('No clips selected')
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frames', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seconds', type=float, default=3.0)
    parser.add_argument('--clip', action='append', help='only these clips (default: every manifest clip)')
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    validated = validate_frames(args.frames, manifest, args.clip)
    args.output.mkdir(parents=True, exist_ok=True)
    title_font, small = font(28), font(16)
    sample = next(iter(validated.values()))[0]
    width, height = Image.open(sample).size
    clips = []
    order = []
    with tempfile.TemporaryDirectory(prefix='rig-it-reel-') as temporary:
        for entry in manifest['clips']:
            name = entry['name']
            if name not in validated:
                continue
            frames = validated[name]
            count = len(frames)
            loop = entry['loop']
            label = Image.new('RGBA', (width, 92), (10, 12, 15, 235))
            draw = ImageDraw.Draw(label)
            draw.text((22, 10), f"{manifest['subject']}  ·  {name}", font=title_font, fill='white')
            extra = f"  |  {entry['durationSeconds']:.2f}s native" + ('  |  loop' if loop else '  |  one-shot, holds')
            if entry.get('nominalSpeedBodyHeightsPerSecond'):
                extra += f"  |  {entry['nominalSpeedBodyHeightsPerSecond']:.2f} body heights/s"
            draw.text((22, 50), DESCRIPTIONS.get(name, name) + extra, font=small, fill=(180, 186, 193))
            label_path = Path(temporary) / f'{name}.png'
            label.save(label_path)
            total = int(round(args.seconds * 30))
            if loop:
                motion = f'loop=loop=-1:size={count - 1}:start=0,setpts=N/(30*TB)'
            else:
                motion = f'tpad=stop_mode=clone:stop_duration={args.seconds}'
            first_index = int(frames[0].stem.split('-')[1])
            output = args.output / f'{name}.mp4'
            subprocess.run([FFMPEG, '-y', '-hide_banner', '-loglevel', 'error', '-framerate', '30',
                            '-start_number', str(first_index), '-i', str(args.frames / name / 'frame-%03d.png'),
                            '-loop', '1', '-framerate', '30', '-i', str(label_path),
                            '-filter_complex', f'[0:v]{motion}[m];[m][1:v]overlay=0:0:shortest=1,format=yuv420p',
                            '-frames:v', str(total), '-c:v', 'libx264', '-crf', '18', '-movflags', '+faststart', str(output)],
                           check=True)
            clips.append(output)
            order.append(name)
            if not loop and entry['durationSeconds'] > args.seconds:
                full = args.output / f'{name}_full.mp4'
                subprocess.run([FFMPEG, '-y', '-hide_banner', '-loglevel', 'error', '-framerate', '30',
                                '-start_number', str(first_index), '-i', str(args.frames / name / 'frame-%03d.png'),
                                '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(full)],
                               check=True)
        reel = args.output / f"{manifest['folder']}_Actions.mp4"
        command = [FFMPEG, '-y', '-hide_banner', '-loglevel', 'error']
        for clip in clips:
            command += ['-i', str(clip)]
        command += ['-filter_complex', ''.join(f'[{i}:v]' for i in range(len(clips))) + f'concat=n={len(clips)}:v=1:a=0[v]',
                    '-map', '[v]', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(reel)]
        subprocess.run(command, check=True)
    durations = {p.name: duration(p) for p in [*clips, reel]}
    for clip in clips:
        assert abs(durations[clip.name] - args.seconds) < 0.002, (clip.name, durations[clip.name])
    assert abs(durations[reel.name] - args.seconds * len(clips)) < 0.002 * len(clips)
    payload = {'subject': manifest['subject'], 'fps': 30, 'sectionSeconds': args.seconds, 'durations': durations,
               'order': order, 'reel': reel.name,
               'sha256': hashlib.sha256(reel.read_bytes()).hexdigest(),
               'productionSha256': manifest['production']['sha256'],
               'source': 'Frames rendered from freshly reimported per-action FBX exports; not gameplay footage',
               'oneShots': 'Play once then hold the final frame; Death does not reset within its section'}
    (args.output / 'preview.json').write_text(json.dumps(payload, indent=2) + '\n')
    print(json.dumps({'reel': str(reel), 'durations': durations}))


if __name__ == '__main__':
    main()
