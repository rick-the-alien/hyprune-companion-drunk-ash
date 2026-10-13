# Drunk Ash · a Hyprune companion

**Drunk Ash** is a companion character for [Hyprune](https://hyprune.com), the explorable,
world-driven desktop for Hyprland. Pick him as your companion and he follows you through every
world: a slightly unsteady fellow in a purple hoodie who keeps a couple of metres behind you,
catches up at a run when you get ahead, and has a few things to say when you talk to him (E).

| | |
| --- | --- |
| Package id | `io.github.rick-the-alien.drunk-ash` (an object library) |
| Object | `drunk-ash`: a character with a companion block |
| Version | 0.1.0 |
| Needs | Hyprune core with IPC 0.25 and object format 0.10 (companions) |
| Licence | [CC-BY-4.0](LICENSE): credit "Drunk Ash by Rick" ([ATTRIBUTION](package/ATTRIBUTION.md)) |
| Size | about 2.4 MB: 8,000 triangles, KTX2 textures at 1024 px, meshopt geometry |

## Install

From the community registry (once listed), in the Director (Browse) or with the CLI:

```sh
hyprune library add io.github.rick-the-alien.drunk-ash
```

Straight from this repository's releases, without the registry:

```sh
hyprune library add github:rick-the-alien/hyprune-companion-drunk-ash@v0.1.0
```

Then choose him in Settings → Companion, or `hyprune` IPC `companion.set` with the ref
`library/io.github.rick-the-alien.drunk-ash@0.1.0/drunk-ash`.

## What he does

- Follows 2 m behind and beside you, walking his own drunk walk; runs to catch up; turns up out of
  sight after warps and world switches (with a wave when you spot him).
- Idles with three idle loops of his own; turns to face you when you look at him.
- **E**: Talk (one line at a time), Stay or Follow. Carry him (Super+drag) and set him down on a
  drawn route and he walks it until you call him back with Follow.
- Never stands between you and a screen, never blocks a doorway, never pushes you.

## Repository layout

| Path | What |
| --- | --- |
| `package/` | The package exactly as it ships: `library.json`, `LICENSE`, `ATTRIBUTION.md`, `objects/drunk-ash/` (`object.json`, `object.glb`, `thumbnail.png`). |
| `release/` | Release notes and the registry card image (`thumb-1.png`), published as release assets. |
| `tools/release.py` | Builds the release assets (MIT). |
| `.github/workflows/release.yml` | On a `v*` tag: checks the package, builds the assets and creates the GitHub Release (MIT). |

The package holds the normalised character, not the author's raw export.

## Releasing

Publishing is a tag plus a release (RFC-0015): the tag is the version.

1. Set the same `version` in `package/library.json` and `package/objects/drunk-ash/object.json`,
   and commit.
2. `git tag v<version> && git push origin v<version>`.
3. The workflow checks the package with the Hyprune SDK, builds
   `io.github.rick-the-alien.drunk-ash-<version>.tar.zst`, its `.sha256` and its
   `.release.json`, creates the release, and prints the community registry entry in the job
   summary.

Published tags and assets are never moved or replaced; a fix is a new version. Enable the
repository's immutable releases setting where available.

To build the same assets locally (byte for byte: the archive is reproducible and compressed by
the pinned `zstandard` wheel):

```sh
python3 -m venv .venv && .venv/bin/pip install -r tools/requirements.txt
.venv/bin/python tools/release.py --tag v0.1.0
sha256sum dist/*.tar.zst
```

## Repository settings

Name `hyprune-companion-drunk-ash` (the `<owner>/hyprune-<kind>-<name>` convention) with the
GitHub topics `hyprune` and `hyprune-companion`.

## Licence

The package content (model, textures, rig, animations, thumbnail) is © Rick, licensed
[CC-BY-4.0](LICENSE). The release tooling (`tools/`, `.github/`) is MIT ([LICENSE-tools](LICENSE-tools)).
