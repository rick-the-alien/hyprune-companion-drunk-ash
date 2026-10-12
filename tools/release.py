#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build the release assets of this package from a tagged commit (RFC-0015 package release convention).

    python3 tools/release.py [--tag v0.1.0] [--out dist] [--repo URL] [--checks JSON]

Reads package/ (library.json or world.json at its root) and writes, into --out:

    <id>-<version>.tar.zst          the archive: one root directory named <id>, ustar, sorted
                                    entries, mtime 0, uid/gid 0, modes 0644/0755, zstd level 19
                                    (window log <= 27) from the pinned `zstandard` wheel, so the
                                    bytes are the same on every machine
    <id>-<version>.tar.zst.sha256   `sha256sum` format
    <id>-<version>.release.json     the release record (recordVersion 0.1)
    <id>-<version>.thumb-<n>.png    thumbnails from release/thumb-<n>.png, when present
    registry-entry.json             the community registry entry for this version (not an asset)

It refuses anything the convention forbids: a tag that doesn't name the manifest version, files
outside the data-only allowlist, executable bits or signatures, unsafe names, symlinks, and
the archive limits. The tag defaults to v<version>; the commit is HEAD's (it must be the
tagged commit when --tag names an existing tag).
"""
import argparse, hashlib, io, json, os, pathlib, re, stat, subprocess, sys, tarfile

import zstandard  # pinned in tools/requirements.txt: the wheel bundles its own libzstd

ROOT = pathlib.Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'package'
LIMITS = {  # RFC-0015 archive limits: (archive, expanded, files, single file)
    'library': (256 << 20, 512 << 20, 4000, 32 << 20),
    'world': (512 << 20, 1 << 30, 10000, 128 << 20),
}
DATA = {'.json', '.glb', '.gltf', '.bin', '.png', '.jpg', '.jpeg', '.ktx2', '.svg', '.ogg', '.wav', '.md', '.txt'}
NOTICES = {'LICENSE', 'NOTICE', 'COPYING', 'ATTRIBUTION'}
SIGNATURES = [b'\x7fELF', b'MZ', b'\xfe\xed\xfa\xce', b'\xfe\xed\xfa\xcf', b'\xce\xfa\xed\xfe', b'\xcf\xfa\xed\xfe', b'\xca\xfe\xba\xbe', b'#!', b'\0asm']
SEMVER = re.compile(r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(-[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?$')
SPDX = re.compile(r'^[A-Za-z0-9.+-]+( (AND|OR|WITH) [A-Za-z0-9.+-]+)*$')


def fail(message):
    sys.exit(f'release: {message}')


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def manifest():
    for kind, name in (('library', 'library.json'), ('world', 'world.json')):
        path = PACKAGE / name
        if path.exists():
            return kind, json.loads(path.read_text())
    fail('package/ has no library.json or world.json')


def files():
    """The package tree, checked: relative paths in archive order."""
    out = []
    for path in sorted(PACKAGE.rglob('*')):
        rel = path.relative_to(PACKAGE).as_posix()
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode) or not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
            fail(f'{rel}: only regular files and directories')
        for part in rel.split('/'):
            if part in ('', '.', '..') or any(c in part for c in '\\%?#:') or part.startswith('.'):
                fail(f'{rel}: unsafe or hidden name')
        if stat.S_ISREG(mode):
            stem, ext = os.path.splitext(path.name)
            if ext.lower() not in DATA and path.name not in NOTICES and stem not in NOTICES:
                fail(f'{rel}: not a data file (RFC-0015 data-only allowlist)')
            head = path.open('rb').read(4)
            if any(head.startswith(s) for s in SIGNATURES):
                fail(f'{rel}: starts with an executable or script signature')
        out.append(rel)
    return out


def archive(root, rels):
    """Reproducible ustar stream: sorted, mtime 0, uid/gid 0, no names, 0644/0755."""
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w', format=tarfile.USTAR_FORMAT) as tar:
        entries = [''] + rels
        for rel in entries:
            path = PACKAGE / rel if rel else PACKAGE
            info = tarfile.TarInfo(f'{root}/{rel}'.rstrip('/'))
            info.mtime, info.uid, info.gid, info.uname, info.gname = 0, 0, 0, '', ''
            if path.is_dir():
                info.type, info.mode = tarfile.DIRTYPE, 0o755
                tar.addfile(info)
            else:
                data = path.read_bytes()
                info.size, info.mode = len(data), 0o644
                tar.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def png_size(path):
    data = path.read_bytes()[:24]
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        fail(f'{path.name}: thumbnails are PNG here')
    return int.from_bytes(data[16:20], 'big'), int.from_bytes(data[20:24], 'big')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--tag'); ap.add_argument('--out', default='dist')
    ap.add_argument('--repo', default='https://github.com/rick-the-alien/hyprune-companion-drunk-ash')
    ap.add_argument('--checks', default='{}', help='informative local check results for the record, as JSON')
    a = ap.parse_args()
    kind, m = manifest()
    pid, version, name, licence = m['id'], m['version'], m['name'], m['license']
    tag = a.tag or f'v{version}'
    if not SEMVER.match(version) or '+' in version:
        fail(f'version {version}: SemVer without build metadata')
    if tag != f'v{version}':
        fail(f'tag {tag} does not name the manifest version {version} (a one-package repository tags v<version>)')
    if not SPDX.match(licence):
        fail(f'license {licence!r} is not an SPDX expression')
    commit = git('rev-parse', 'HEAD')
    if git('tag', '--list', tag) and git('rev-list', '-n', '1', tag) != commit:
        fail(f'HEAD is not the commit {tag} points to')
    rels = files()
    regular = [r for r in rels if (PACKAGE / r).is_file()]
    raw = archive(pid, rels)
    big, expanded_limit, file_limit, single = LIMITS[kind]
    expanded = sum((PACKAGE / r).stat().st_size for r in regular)
    if len(regular) > file_limit or expanded > expanded_limit or any((PACKAGE / r).stat().st_size > single for r in regular):
        fail('the package exceeds the RFC-0015 archive limits')
    params = zstandard.ZstdCompressionParameters.from_level(19, window_log=23, threads=0, write_content_size=True)
    packed = zstandard.ZstdCompressor(compression_params=params).compress(raw)
    if len(packed) > big:
        fail('the archive exceeds the RFC-0015 size limit')
    out = (ROOT / a.out) if not os.path.isabs(a.out) else pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    base = f'{pid}-{version}'
    archive_name = f'{base}.tar.zst'
    (out / archive_name).write_bytes(packed)
    digest = hashlib.sha256(packed).hexdigest()
    (out / f'{archive_name}.sha256').write_text(f'{digest}  {archive_name}\n')
    thumbnails = []
    for n in range(1, 5):
        src = ROOT / 'release' / f'thumb-{n}.png'
        if not src.exists():
            break
        if src.stat().st_size > 512 * 1024:
            fail(f'{src.name}: thumbnails are at most 512 KiB')
        w, h = png_size(src)
        if w > 1280 or h > 720:
            fail(f'{src.name}: thumbnails are at most 1280 x 720')
        dst = f'{base}.thumb-{n}.png'
        (out / dst).write_bytes(src.read_bytes())
        thumbnails.append({'name': dst, 'sha256': hashlib.sha256(src.read_bytes()).hexdigest(), 'width': w, 'height': h})
    record = {
        'recordVersion': '0.1',
        'type': kind,
        'id': pid,
        'version': version,
        'formatVersion': m['formatVersion'],
        'name': name,
        'license': licence,
        'archive': {'name': archive_name, 'sha256': digest, 'bytes': len(packed), 'expandedBytes': expanded, 'files': len(regular)},
        'requires': {'libraries': list(m.get('requires', {}).get('libraries', [])) if kind == 'world' else []},
        'thumbnails': thumbnails,
        'source': {'repo': a.repo, 'tag': tag, 'commit': commit},
        'tool': {'name': 'tools/release.py', 'version': '0.1.0'},
        'checks': json.loads(a.checks),
    }
    record_name = f'{base}.release.json'
    record_bytes = (json.dumps(record, indent=2) + '\n').encode()
    (out / record_name).write_bytes(record_bytes)
    owner = a.repo.rstrip('/').split('/')[-2]
    download = f'{a.repo}/releases/download/{tag}'
    entry = {
        'id': pid, 'type': kind, 'name': name, 'summary': m.get('description', name)[:140], 'description': m.get('description', name)[:2000],
        'creator': owner, 'repo': a.repo, 'tags': ['companion', 'character'],
        'versions': [{
            'tag': tag, 'version': version, 'formatVersion': m['formatVersion'], 'published': git('log', '-1', '--format=%cs', commit), 'license': licence,
            'url': f'{download}/{archive_name}', 'sha256': digest, 'bytes': len(packed), 'expandedBytes': expanded, 'files': len(regular),
            'record': {'url': f'{download}/{record_name}', 'sha256': hashlib.sha256(record_bytes).hexdigest()},
            'requires': record['requires'],
            'thumbnails': [{'url': f'{download}/{t["name"]}', 'sha256': t['sha256'], 'width': t['width'], 'height': t['height']} for t in thumbnails],
            'status': 'available'}],
    }
    (out / 'registry-entry.json').write_text(json.dumps(entry, indent=2) + '\n')
    print(f'{archive_name}  {digest}  {len(packed)} bytes, {len(regular)} files, {expanded} expanded')
    print(f'{record_name}  {hashlib.sha256(record_bytes).hexdigest()}')


if __name__ == '__main__':
    main()
