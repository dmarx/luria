# How to reference remote knowledge

Use a remote when the local record depends on identities owned elsewhere.

A remote reference is a prefix, a delimiter and a uid: the prefix names the remote, the uid is whatever that remote's identifiers look like ([ADR-024](../../record/decisions.d/ADR-024.md)). Luria reads remotes as public URLs over HTTPS, with deliberately no credential path, so what CI resolves is what any reader can follow ([ADR-016](../../record/decisions.d/ADR-016.md)).

## Another Luria record

Declare a remote prefix for the foreign record:

```yaml
remotes:
  LU:
    name: luria
    repo: dmarx/luria
    ref: main
```

Local citations can then compose the remote prefix with the foreign scheme/code — `LU-ADR-013` — rather than pretending the object is local. `luria link --fix` links each one to the URL the remote constructs.

## Arbitrary identifier namespace

For identifiers such as arXiv IDs or issue keys, give the remote a `uid` pattern and a `url` template over its capture groups:

```yaml
remotes:
  ARXIV:
    uid: '(\d{4})[.:](\d{4,5})'
    url: https://arxiv.org/abs/{1}.{2}
```

A citation written as a code, `ARXIV-2301.00001`, is then a checked reference: `luria link --fix` links it to the constructed URL. Hand-written URLs are not rewritten. A link whose text is a remote code but whose target is not the constructed URL is reported under `hand-written-urls`, and `url-ok:` acknowledges a deliberate one. See the [configuration reference](../configuration.md) for the rest of a remote's keys.

## Refresh/check remote knowledge

```console
$ luria remotes
```

lists every foreign code the record cites, per remote, with the URL it resolves to and the evidence behind it. The flags:

- `luria remotes --refresh` discovers each GitHub remote's actual filenames into `remotes.lock.json` and re-observes pinned content,
- `luria remotes --check` HEAD-probes every cited URL and reports what a reader would find — it needs the network, and it is a report, never a failure,
- `luria remotes --pin [CODE]` endorses remote content by hash (below),
- `luria remotes --resolve [CODE]` records what each identifier's title actually is, for remotes that declare how to ask, so the lint can report a document whose `arxiv:` field names a different paper (`source-mismatch`).

`remotes.lock.json` is committed, so CI and offline checkouts resolve identically. The lint only reads it; in CI the `--resolve` write runs where merges serialize, not on every branch ([ADR-112](../../record/decisions.d/ADR-112.md), and see [CI](ci.md#remote-verification)). [`luria remotes`](../cli.md#luria-remotes) has the full behavior.

## Choose a network policy

`lint.network` in `luria.yaml` says how far `luria lint` may go:

```yaml
lint:
  network: never
```

- `auto` (the default) — opportunistic: ask about identifiers the lockfile has no answer for, and report them as unchecked (`source-unchecked`) when the network is not there,
- `never` — no network; answer only from the lockfile,
- `require` — required network verification: an identifier nothing could verify fails the lint without naming `source-unchecked` in `fail_on`.

Document the policy in CI so a green build has a clear meaning.

## Pin content when identity alone is not enough

When your claim depends on the actual content of a foreign source rather than merely its continued existence, pin it ([ADR-066](../../record/decisions.d/ADR-066.md)). For a remote code:

```console
$ luria remotes --pin LU-ADR-001
LU-ADR-001: pinned at sha256:08973b257786…
wrote remotes.lock.json
```

For an arbitrary URL, register it with a `pin:` directive where it is cited, then run a bare `luria remotes --pin`:

```markdown
<!-- pin: https://spec.example/v1.html — the spec this implements -->
We follow [the spec](https://spec.example/v1.html).
```

A later upstream content change then becomes a local finding: once `luria remotes --refresh` re-observes the content, `luria lint` reports it under `remote-drift`. Review the change and run `luria remotes --pin CODE` again to re-endorse it; a bare `--pin` never re-endorses drifted content. [Comment directives](../directives.md) covers `pin:`.

That extends truth maintenance beyond repository boundaries.
