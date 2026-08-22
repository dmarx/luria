from __future__ import annotations
import datetime as dt
import re
import sys
from . import adr_index as builder
from . import adr_pending, badges, ci, doc_refs, journal, link_targets, narrow_titles, ref_status, remotes, statuses
from .config import current
STATUS_RE = re.compile('^(Active|Proposed|Deferred|Superseded|Rejected)( — \\S(?:.|\\n)*\\S)?$')
INDEX_EXEMPT = {'README.md'}

def check_docs_index(errors: list[str]) -> None:
    cfg = current()
    index = cfg.docs / 'README.md'
    if not index.exists():
        return
    text = index.read_text()
    exempt = {s.dir for s in cfg.schemes.values()} | {s.view for s in cfg.schemes.values() if s.render == 'index'} | {s.tag_dir for s in cfg.schemes.values() if s.render == 'index'} | {j.dir for j in cfg.journals.values()} | {j.output for j in cfg.journals.values()} | {cfg.reports}
    pages = sorted(cfg.docs.glob('*.md'))
    for sub in sorted((p for p in cfg.docs.iterdir() if p.is_dir())):
        if sub not in exempt:
            pages += sorted(sub.glob('*.md'))
    for page in pages:
        rel = page.relative_to(cfg.docs)
        if str(rel) in INDEX_EXEMPT:
            continue
        if f'({rel})' not in text:
            errors.append(f'{cfg.rel(index)}: missing index entry for {rel}')

def check_frontmatter(errors: list[str]) -> None:
    cfg = current()
    for scheme in cfg.schemes.values():
        for path in [*scheme.documents().values(), *scheme.temp_documents().values()]:
            rel = cfg.rel(path)
            meta, body = builder.parse_frontmatter(path.read_text())
            if not meta:
                errors.append(f'{rel}: no YAML frontmatter (see _template.md)')
                continue
            check_title(errors, rel, meta, body)
            status = str(meta.get('status', '')).strip()
            if not status:
                errors.append(f'{rel}: no `status:` in frontmatter')
            elif not STATUS_RE.match(status):
                errors.append(f"{rel}: nonstandard status {status!r} (want: Active|Proposed|Deferred|Superseded|Rejected, optional ' — note')")
            elif statuses.undeclared(scheme, status):
                errors.append(f"{rel}: status {status.split(' — ')[0]!r} is not one the {scheme.prefix} scheme declares (see {cfg.rel(scheme.statuses_yaml)})")
            if not (meta.get('tags') or []):
                errors.append(f'{rel}: no `tags:` in frontmatter (see ADR-003)')
            for field in scheme.requires:
                if not meta.get(field):
                    errors.append(f'{rel}: no `{field}:` in frontmatter — the {scheme.prefix} scheme requires it (luria.toml)')

def check_title(errors: list[str], rel: str, meta: dict, body: str) -> None:
    title = str(meta.get('title') or '').strip()
    if not title:
        errors.append(f'{rel}: no `title:` in frontmatter (see ADR-013)')
        return
    first = next((ln for ln in body.splitlines() if ln.startswith('#')), '')
    heading = builder.TITLE_RE.sub('', first).strip()
    if heading and heading != title:
        errors.append(f'{rel}: `title:` and the body heading disagree — {title!r} vs {heading!r}')

def check_status_vocabulary(errors: list[str]) -> None:
    for scheme in current().schemes.values():
        errors.extend(statuses.problems(scheme))

def check_tag_groups(errors: list[str]) -> None:
    cfg = current()
    for scheme in cfg.schemes.values():
        if not scheme.tag_groups:
            continue
        for path in [*scheme.documents().values(), *scheme.temp_documents().values()]:
            meta, _ = builder.parse_frontmatter(path.read_text())
            if not meta:
                continue
            rel = cfg.rel(path)
            tags = {str(t) for t in meta.get('tags') or []}
            for group in scheme.tag_groups:
                present = sorted(tags & group.tags)
                shown = ', '.join(sorted(group.tags))
                if group.require == 'exactly-one' and len(present) != 1:
                    errors.append(f"{rel}: `{group.name}` wants exactly one of {shown} — has {', '.join(present) or 'none'}")
                elif group.require == 'at-most-one' and len(present) > 1:
                    errors.append(f"{rel}: `{group.name}` wants at most one of {shown} — has {', '.join(present)}")
                if present and (clash := sorted(tags & group.excluded_by)):
                    errors.append(f"{rel}: {', '.join(clash)} excludes `{group.name}`, but the document also has {', '.join(present)}")

def check_journals(errors: list[str]) -> None:
    cfg = current()
    for name, jrnl in cfg.journals.items():
        for path in sorted(jrnl.dir.rglob('*.md')):
            if path.name == '_template.md':
                continue
            rel = cfg.rel(path)
            meta, _ = builder.parse_frontmatter(path.read_text())
            created = journal.parse_created(meta.get('created'))
            if created is None:
                if journal.created_from_path(path) is not None:
                    errors.append(f'{rel}: no `created:` timestamp — `luria index` populates it from the path')
                else:
                    errors.append(f"{rel}: no `created:` timestamp, and the path doesn't imply one (see _template.md)")
                continue
            want = journal.path_for(jrnl, created)
            if path != want:
                errors.append(f'{rel}: `created:` says it belongs at {cfg.rel(want)} — run `luria new` to file entries, or move it')
            if not str(meta.get('title') or '').strip():
                errors.append(f"{rel}: no `title:` — it is what the {name} book's contents list shows")

def check_version_history(errors: list[str]) -> None:
    cfg = current()
    for scheme in cfg.schemes.values():
        for path in scheme.documents().values():
            meta, _ = builder.parse_frontmatter(path.read_text())
            version = int(meta.get('version', 1) or 1)
            history = meta.get('history') or []
            rel = cfg.rel(path)
            if version > 1 and (not history):
                errors.append(f'{rel}: version {version} with no `history:` — a correction is only honest if it says what changed (see ADR-019)')
            elif history:
                last = history[-1].get('version') if isinstance(history[-1], dict) else None
                if last != version:
                    errors.append(f'{rel}: `history:` ends at version {last!r} but the document says {version}')

def check_generated_index(errors: list[str]) -> None:
    cfg = current()
    report = builder.staleness()
    remedy = ci.regenerate_remedy()
    for path in report.stale:
        errors.append(f'{cfg.rel(path)}: stale — {remedy}')
    for path in report.orphaned:
        errors.append(f'{cfg.rel(path)}: not something the generator wrote — a view directory holds only generated files (ADR-021); {remedy}, or file the content as a source')
    if report.badges:
        errors.append(f'{cfg.rel(report.badges)}: badge counts are stale — {remedy}')

def check_wikilinks(errors: list[str]) -> None:
    cfg = current()
    for path in doc_refs.doc_files():
        text = path.read_text()
        for w in doc_refs.wikilinks(text, path):
            rel = cfg.rel(path)
            if w.target is None:
                errors.append(f'{rel}:{w.line}: [[{w.inner}]] resolves to nothing this project can link — a typo, an unregistered prefix, or a self-link')
            else:
                errors.append(f'{rel}:{w.line}: [[{w.inner}]] is not yet a link — run `luria link --fix`')

def check_bare_refs(errors: list[str]) -> None:
    cfg = current()
    adrs, anchors = (doc_refs.adr_paths(), doc_refs.dp_anchors())

    def scan_one(path) -> list[str]:
        text = path.read_text()
        return [f'{cfg.rel(path)}:{ref.line}: {ref.describe()} is not a link — run `luria link --fix`' for ref in doc_refs.rewritable_refs(text, path, adrs, anchors)]
    from .parallel import pmap
    for found in pmap(scan_one, doc_refs.doc_files()):
        errors.extend(found)
FAILABLE = ('retired-citations', 'unresolved-codes', 'hand-written-urls', 'broken-targets', 'inert-status', 'legacy-spellings', 'narrow-titles', 'stale-directives', 'pending-documents', 'unlinted-files')

def status_sections() -> list[tuple[str, str, list[str]]]:
    docs = ref_status.load_docs()
    result = ref_status.scan(docs=docs)
    sections: list[tuple[str, str, list[str]]] = []
    lines = ref_status.summary_lines(result, docs)
    if lines:
        sections.append(('retired-citations', f'{len(lines)} warning(s) — retired documents cited unacknowledged from current docs/code (`luria reports` for the sites, `inactive-ok:` to acknowledge one)', lines))
    loose = ref_status.dangling_lines(result, docs)
    if loose:
        sections.append(('unresolved-codes', f'{len(loose)} code(s) resolve to no document (`luria reports` for the sites, `unresolved-ok:` for the deliberate ones)', loose))
    if result.unlinted:
        sections.append(('unlinted-files', f'{len(result.unlinted)} file(s) opt out of reference checking (`unlinted-file:` — listed in the reference report)', [str(current().rel(p)) for p in sorted(result.unlinted)]))
    hand, stale_urls = remotes.hand_links()
    if hand:
        sections.append(('hand-written-urls', f'{len(hand)} link(s) hand-written where a URL would be constructed (`url-ok:` acknowledges a deliberate one)', hand))
    dead, stale_targets = link_targets.broken()
    if dead:
        sections.append(('broken-targets', f'{len(dead)} relative link target(s) resolve to nothing from where the prose renders (`luria link --fix` spells code targets; `target-ok:` acknowledges a deliberate one)', dead))
    uniform = statuses.uniform_rows()
    if uniform:
        sections.append(('inert-status', f'{len(uniform)} scheme(s) file every record at one status, so nothing there can ever be retired and the citation checks cannot fire', uniform))
    legacy = doc_refs.legacy_spellings()
    if legacy:
        sections.append(('legacy-spellings', f"{len(legacy)} citation(s) in a concretized code's old spelling (`luria link --fix` upgrades them)", legacy))
    narrow = narrow_titles.rows()
    if narrow:
        sections.append(('narrow-titles', f'{len(narrow)} title(s) name a project noun in a scheme whose documents claim to transfer (`broad-ok:` acknowledges another sense)', narrow))
    stale = ref_status.stale_annotations(result, docs) + stale_urls + stale_targets
    for path in doc_refs.doc_files():
        stale += doc_refs.directive_problems(path, path.read_text())
    if stale:
        sections.append(('stale-directives', f'{len(stale)} directive(s) no longer apply', sorted(stale)))
    rows = adr_pending.pending()
    if rows:
        sections.append(('pending-documents', adr_pending.headline(rows, dt.date.today(), current().stale_days) + ' (`luria reports` for the table)', []))
    return sections

def report_warnings(errors: list[str]) -> None:
    fail = set(current().fail_on)
    for name in sorted(fail - set(FAILABLE)):
        errors.append(f"luria.toml: `fail_on` names {name!r}, which is no warning class (known: {', '.join(FAILABLE)})")
    for name, headline, lines in status_sections():
        if name in fail:
            errors.append(f'{headline} — failing: `fail_on` names {name!r} in luria.toml')
            errors.extend(lines)
        else:
            print(f'luria: {headline}', file=sys.stderr)
            for line in lines:
                print(f'  {line}', file=sys.stderr)

def run() -> None:
    errors: list[str] = []
    check_docs_index(errors)
    check_frontmatter(errors)
    check_status_vocabulary(errors)
    check_tag_groups(errors)
    check_generated_index(errors)
    check_journals(errors)
    check_version_history(errors)
    check_bare_refs(errors)
    check_wikilinks(errors)
    report_warnings(errors)
    if errors:
        print(f'luria: {len(errors)} violation(s)', file=sys.stderr)
        for e in errors:
            print(f'  {e}', file=sys.stderr)
        raise SystemExit(1)
    print('luria: docs lint clean')
if __name__ == '__main__':
    import fire
    fire.Fire(run)
