# World bible

A story bible, and the shape that produced two additions to the machinery.

**A plural reference.** A scene `follows` several scenes, so the reference is
many-valued and every one of them is resolved.

**A field that is none of the three kinds that existed.** `worlds` is not a
reference (its values are not codes), not a tag (scenes carry topical tags
too), and not a status — it is a scheme-local **controlled vocabulary**, closed,
with a default that is an effective value rather than a rewrite. A scene naming
a world not in `worlds.yaml` fails the lint, and each world gets a page listing
its scenes.

The default matters: absent means `B`, so `B`'s page lists the scenes that
never mention it, which is what makes the default an actual value instead of a
gap.

The configuration is `luria.toml`, commented throughout; the scenes are under
`record/scenes.d/` with `tags.yaml` and `worlds.yaml` beside them. The generated
views: [the scene index](docs/scenes/README.md) and [the front
door](docs/README.md).

```
LURIA_ROOT=$PWD luria index
LURIA_ROOT=$PWD luria lint
```
