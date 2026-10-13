# Attribution

**Drunk Ash** by **Rick**, from
[rick-the-alien/hyprune-companion-drunk-ash](https://github.com/rick-the-alien/hyprune-companion-drunk-ash),
licensed under [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) (see `LICENSE`).

This covers everything in this library: the model, skin, textures, rig and animation clips
(`idle`, `idle_alt1`, `idle_alt2`, `walk`, `walk_back`, `run`) of `objects/drunk-ash`, and
its thumbnail. Ash is the author's own original character; the author holds the rights to it
and licenses it here.

Modifications from the author's source export, made with the Hyprune worlds tooling
(`tools/npc-import`, `tools/object-import --adopt`): the rest pose lifted to stand on the
floor (clips unchanged); units, axes and a `root` bone; translation keys kept on the hips with
the travel removed (in-place clips; speeds kept as `extras.speed`), his own sway kept; clips
renamed to the Hyprune character names; weights limited to 4; seam vertices welded, then
decimated to 8,000 triangles;
textures scaled to 1024 px and compressed (KTX2); geometry quantised and meshopt-compressed.
`object.json` (with the companion block) and `thumbnail.png` (a render of the character) are
written by the tooling. The raw export is not part of this repository.
