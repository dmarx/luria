# Python Project Structure

## luria/adr_index.py
```python
def escape_cell(text: str) -> str
    """`text` as one table cell, however many `|` it contains."""

def rebase_links(text: str, prefix: str) -> str
    """
    Rewrite relative link targets in `text` for an output `prefix` away.
    Summaries are authored relative to the scheme's *source* directory — the
    same base as the ADR body they were lifted from — and this index renders
    them into the view directory and again one level down in `tags/<tag>.md`.
    Owning the rendering is what lets a summary carry links at all: without
    this, no single relative target could be correct everywhere (ADR-005).
    The result is **normalized**, because a link that only a webserver's path
    resolver forgives is a link some readers lose: concatenation alone yields
    `../../record/decisions.d/../../docs/design-principles.md`, which GitHub
    collapses and a static-site generator does not (#13).
    """

def _normalize(target: str) -> str
    """
    Collapse `a/../b` in a relative link target, fragment preserved.
    `posixpath` because these are URLs, not filesystem paths — the separator
    is `/` on every platform that renders the view.
    """

def prefix_for(scheme, out_dir: Path) -> str
    """
    The rebase prefix for text authored in `scheme.dir`, rendered into
    `out_dir`. "" when they are the same place — the collocated layout — so
    the old output is byte-identical where nothing moved.
    """

def parse_frontmatter(text: str) -> tuple[[dict, str]]
    """
    Split leading `---` YAML frontmatter from the body. Missing frontmatter
    yields an empty dict so a half-migrated tree still renders — lint reports
    the omission rather than the build crashing on it.
    """

def _load_yaml(text: str)

def read_document(path: Path) -> tuple[[dict, str]]
    """
    This document's frontmatter and body, parsed at most once per revision.
    Every `Adr` construction parsed the file it names, and the schemes are
    loaded once per consumer rather than once per run: a 729-document record
    parsed 16,872 frontmatter blocks on one `luria lint`, about 23 per
    document, and the YAML was 70 of its 95 seconds (#249).
    The returned mapping is copied per caller. `Adr` folds derived fields into
    the dict it is handed, and a shared mapping would let one reading's
    derivation leak into the next — the failure the per-`Adr` resolver in
    `Adr.__init__` exists to avoid (#233), reintroduced one layer down.
    """

def forget_documents() -> None
    """
    Drop the parse cache — for tests that rewrite a fixture faster than the
    filesystem's mtime resolution can distinguish.
    """

class Adr

    def __init__(self, path: Path, scheme)

    @property
    def code(self) -> str

    @property
    def status(self) -> str
        """
        The display form — `Superseded — by [X](…); note` — composed from
        the fields, a successor linked relative to the scheme directory the
        way a hand-written note's link was. `status_value`, `status_note`
        and `superseded_by` are the fields.
        """

    @property
    def superseded_by(self) -> tuple[[str, Ellipsis]]

    @property
    def status_value(self) -> str

    @property
    def status_note(self) -> str

    @property
    def tags(self) -> list[str]
        """
        This document's values on its scheme's axis, or none when the
        scheme declares no axis (ADR-098).
        """

    def cell(self, prefix: str) -> str
        """
        The Summary column: the `summary:` frontmatter, or empty.
        The row used to be one blob — summary when present, else title —
        under a column labelled "Title", a shape kept originally to make the
        migration byte-identical and outlived by its reason: any document
        with a summary showed its summary mislabelled as a title. The title
        now has its own column, so this one is honest about being optional —
        an empty cell is a document whose index row could say more, not a
        rendering fallback papering over the gap.
        A summary may carry relative links, written — like the ADR's body —
        relative to the scheme's source directory. `prefix` rebases them for
        output that renders somewhere else (ADR-005); it is the same prefix
        the row's own ADR link already took.
        """

    @property
    def version(self) -> int
        """
        Which revision of this document's claim you are reading.
        Standard frontmatter for every scheme (ADR-016), not just principles.
        A decision is superseded rather than rewritten, so its version moves
        rarely — but "rarely" is not "never": a decision whose *scope* widens
        without its choice changing is a revision, and that is exactly the case
        a reader needs told apart from a fresh decision.
        """

    @property
    def influenced_by(self) -> list[str]

    def row(self, prefix: str) -> str


def load_adrs() -> list[Adr]
    """
    The ADR scheme's documents. Kept as its own name because the pending
    report is about decisions specifically, not about every scheme.
    """

def load_scheme(scheme) -> list[Adr]
    """
    Every document in the scheme: numbered ascending, then any temporary
    documents (ADR-049) by their `date:` and name — they have no place in the
    sequence yet, so they read after it.
    """

def render_index(adrs: list[Adr], scheme) -> str

def render_document(scheme, docs: list[Adr]) -> str
    """
    Every document's body, in number order, as one page.
    The right shape when the set is read *as a whole* rather than browsed one at
    a time — which is what a principles document is: people cite "DP-3" and then
    read it in the context of its neighbours. The metadata line is what the
    fragment frontmatter buys: a version, so a revised principle says so
    (ADR-012), and the decisions whose experience produced it.
    """

def _link(code: str, base: Path) -> str
    """
    `ADR-004` → a link to that decision, relative to `base`.
    Relative to *where the text renders*, not where the fragment lives — the
    same rule the reference fixer follows for anything assembled elsewhere
    (ADR-005). An unresolvable code yields "", and the caller renders the bare
    code rather than a link to nothing (DP-1: say what you can, don't invent).
    """

def view_dirs(nested: bool) -> list[Path]
    """
    Every directory the generator owns outright. Anything in one of these
    it didn't render is an orphan — a stale tag page, a book from an old
    granularity, or a hand-written file that will read as generated (ADR-021).
    A collocated scheme (no separate `output`) contributes only its tag dir,
    because its view directory also holds the sources.
    """

def orphans(rendered: dict[[Path, str]]) -> list[Path]

def ignored(paths: list[Path]) -> set[Path]
    """
    The subset of `paths` that git is configured to ignore.
    A generated view the project has gitignored is one it has decided not to
    keep — `paths.reports = "build/doc-reports"` behind a CI artifact
    upload is the shape that exists in the wild. The staleness check has
    nothing to compare against there: a fresh clone never has the file, so
    *missing* reads as *stale*, and the remedy the failure prints — regenerate
    and commit the result — is the one thing `.gitignore` forbids. A check
    that cannot be satisfied is not a check; it is a permanently red job that
    teaches people to stop reading it, which is DP-1 wearing a green hat.
    Only `--check` consults this. Writing is unaffected: `luria index` still
    renders an ignored view, because *not committed* is not *not wanted* —
    that report is precisely what the artifact upload publishes.
    One `git check-ignore` for the whole set. Exit 1 means "nothing matched",
    the ordinary answer; anything else (not a repo, no git on PATH) means we
    cannot tell, and not-ignored is the answer that keeps checking.
    """

def _render_scheme(scheme) -> dict[[Path, str]]

def outputs(nested: bool) -> dict[[Path, str]]
    """
    Every generated view, across every scheme — one place, so the lint's
    staleness check covers a new scheme the moment it is configured.
    Rendered wide (ADR-026): each scheme and each journal is an independent
    pure function of the tree, so they run as parallel units. `pmap` returns
    in input order, which is what keeps the merged dict — and therefore the
    staleness diff — deterministic.
    """

class Staleness
    """
    Everything the staleness check has to say about the tree.
    Three kinds, kept apart because each wants a different sentence: a view
    that differs from what the generator would write, a file sitting in a view
    directory the generator never wrote, and a README whose badge counts have
    drifted.
    """

    @property
    def all(self) -> list[Path]

    @property
    def any(self) -> bool


def staleness(rendered: dict[[Path, str]] | None) -> Staleness
    """
    The one answer to "is the committed tree current?", for
    `luria index --check`; `luria lint` reads only its `orphaned` field.
    It used to be computed twice, in two files, from the same three rules —
    which is the arrangement where a fix lands in one of them and the other
    keeps failing. It did: the gitignore exemption below was written in
    `--check` first, and `lint` went on rejecting the same tree. Now the
    lint asks no staleness question at all (ADR-068), and this stays one
    function so the orphan rule cannot fork either.
    A view the project gitignores is excluded from all three kinds. There is
    no committed copy to compare against — see `ignored`.
    """

def run(check: bool) -> None
    """
    Regenerate every view — the decision index and tag pages, the
    principles document, the devlog books, the status reports, the README
    badges — and nothing else: sources are `luria repair`'s. --check exits 1
    if any view is stale instead of writing.
    """

```

## luria/adr_pending.py
```python
class Pending

    def age(self, today: Any) -> int | None

    def is_stale(self, today: Any, stale_days: int) -> bool


def _date(meta: dict) -> Any | None

def pending() -> list[Pending]
    """
    Every undecided document in every scheme, oldest first; undated ones
    last — a document with no `date:` can't be aged, which is itself worth
    seeing.
    Not just decisions. A `Proposed` principle is an open question in exactly
    the same way, and a report that covered one scheme would go quietly blind
    the day a project configured a second (ADR-018).
    """

def table(rows: list[Pending], today: Any, stale_days: int) -> list[str]

def headline(rows: list[Pending], today: Any, stale_days: int) -> str

def run(stale_days: int, as_of: str) -> None
    """
    The pending-documents table on the console. --as-of fixes the clock
    (for tests); --stale-days tightens the overdue marker.
    """

```

## luria/aliases.py
```python
class Alias
    """One spelling, what it resolves to, and which kind it is."""

    @property
    def superseded(self) -> bool
        """
        Whether `luria link --fix` rewrites this away. A past spelling is
        rewritten; a derived one is what the author meant to write.
        """


def canon(code: str) -> str | None
    """`dp-4`, `DP 4` and `DP-004` are one spelling: `DP-004`."""

def render(template: str, meta: dict, scheme, number: int) -> str | None
    """
    One document's alias, or None when the template cannot be filled.
    `str.format` over the document's own frontmatter, plus the three values
    the scheme knows — the same template vocabulary a remote URI renders
    through, fed from a different source. A template naming a field this
    document lacks renders nothing rather than a half-spelling: a partial
    alias would resolve for some documents and not others, silently.
    """

def alias_map(cfg: Config | None) -> dict[[str, Alias]]
    """
    Every spelling → what it resolves to, across every scheme.
    Derived fresh from the documents and cached per config. An entry that
    outlived the frontmatter it came from would be exactly the hand-kept
    ledger ADR-040 rejected — so nothing is stored, only projected.
    The cache is what makes derived aliases affordable: resolution used to
    scan every document on demand, which was fine while the only aliases
    were temporary codes nobody writes on purpose. A spelling people *choose*
    to cite makes that path hot (#219).
    """

def reset() -> None
    """
    Drop the cache — for the migration executor, which edits the very
    frontmatter this map is derived from.
    """

def split(code: str) -> tuple[[str, int]]

def previous(path, scheme, number: int) -> str | None
    """
    The alias this document rendered at the last commit, or None.
    Where the old spelling comes from, and the reason it is not stored: the
    record's history is git's, so the previous frontmatter is already written
    down — recording each rendered alias in the document too would be exactly
    the hand-kept ledger ADR-040 rejected, one copy per revision.
    None whenever git cannot answer: a new file, a detached tree, no
    repository at all. Absence of history is not a change of spelling, and a
    repair that guessed here would write a `formerly:` entry naming a
    spelling that never existed.
    """

```

## luria/anchors.py
```python
def addressable(text: str) -> set[str]
    """
    Every fragment this document can be reached at from anywhere.
    The heading half is `slugs`, which is the same function the generator
    uses to WRITE these links — deliberately, because a check computing the
    anchor a second way would agree with the generator and not with the
    publisher, which is the failure it exists to catch (ADR-100).
    """

def by_name_only(text: str) -> set[str]
    """
    Fragments this document answers to on a real navigation and nowhere
    else.
    """

class Reach
    """
    How a document can be reached: every fragment that resolves, the ones
    that resolve only on a real navigation, and whether it could be read.
    """

class Finding
    """A fragment link whose target anchors it by `name` alone."""

def scan(documents: dict[[Path, str]], generated, base) -> list[Finding]
    """
    Every such link across `documents`, a mapping of path to content.
    Content rather than paths, and this is the whole of what CI taught this
    check. Read from disk, it reports the COMMITTED views — and a branch
    carries the default branch's copies of those and is forbidden to update
    them (ADR-018), so the check failed every pull request that touched an
    anchor and named a repair the author was not allowed to make. Handed the
    render instead, it asks the question that is actually about this source
    tree: will the views this record produces contain a fragment nothing can
    scroll to? `check_view_dirs` has always worked this way, and its
    docstring says why — "a branch carries the default branch's copies and
    has nothing to be stale against".
    `generated` answers "is this path a view?" and `base` answers "where
    does this prose render?" — `Config.is_generated` and `Config.link_base`
    in practice. `base` is not the file's own directory: a
    `render = "document"` scheme's prose is written to resolve from the page
    it assembles into, so `../../docs/values.md` in a source is correct there
    and nonsense from the source's own folder.
    """

def repair(text: str, fragments: set[str]) -> str
    """
    `text` with each named anchor in `fragments` rewritten to an id.
    Only the ones something links to: an unlinked `<a name=>` in prose is a
    person's own business, and rewriting it would be this tool editing a
    document to satisfy a rule nothing is currently breaking.
    """

def documents(rendered: dict[[Path, str]] | None) -> dict[[Path, str]]
    """
    What the anchor check reads: every source, and every view AS THE
    GENERATOR WOULD WRITE IT — never the committed copy.
    The motivating case is a journal index linking into a journal book, and
    both are generated, so sources alone cannot see it. The committed copies
    cannot be used either: on a branch they are the default branch's, which
    this record deliberately does not update there (ADR-018).
    """

def anchors_at(target: Path) -> Reach

def swap(m: Any) -> str

```

## luria/badges.py
```python
def counts() -> tuple[[int, int]]
    """(needs decision, cited-not-in-force). Both across every local scheme."""

def badge(label: str, value: int, target: str) -> str

def report_link(filename: str) -> str
    """
    Where a badge points: the report that explains its number (#35).
    Read from config rather than restated — a default that spells out a
    configured path is a projection, and projections drift
    ([DP-3](../docs/design-principles.md#dp-3)); the predecessor of this
    function proved it, the moment the index moved.
    """

def _inner() -> str
    """The badges themselves, without the markers around them."""

def region() -> str

def rewrite(text: str) -> str
    """
    The README with its badge region refreshed.
    Returns the text unchanged when there is no region — a project that hasn't
    opted in isn't nagged, and `--write` says so rather than silently doing
    nothing (DP-1).
    """

def readme() -> Path

def run(write: bool, check: bool) -> None
    """
    Print the badge markdown; --write rewrites the README region,
    --check exits 1 when it is stale. `luria index` does this in normal use.
    """

```

## luria/chains.py
```python
@dataclass
class Line
    """
    One weakly-connected sequence: an ordered spine, plus the documents
    attached to it only by a cross-link.
    """

    @property
    def members(self) -> list[Adr]


def _codes(doc: Adr, name: str, contract) -> list[str]
    """
    The codes one relation field holds on one document. A shape the
    contract rejects is the lint's finding, not this walk's — reading it as
    empty here keeps one mistake reported in one vocabulary.
    """

def _load(chain) -> tuple[[dict[[str, Adr]], dict[[str, list[str]]], dict[[str, list[str]]]]]
    """
    Every document of the chain's scheme, and its two relations, keyed by
    code and filtered to codes that land — a reference to something outside
    the scheme is the contract's finding, not a node here.
    """

def _components(codes: list[str], neighbours: dict[[str, set[str]]]) -> list[list[str]]
    """
    Maximal weakly-connected groups, in the order their earliest member
    appears — so the page's sections are stable across runs.
    """

def _depths(group: list[str], spine: dict[[str, list[str]]]) -> dict[[str, int]]
    """
    Distance from a root, longest-path so a step never renders above
    something it extends. Bounded by the group's size, which is what keeps a
    cycle from spinning here rather than being reported.
    """

def _order(group: list[str], spine: dict[[str, list[str]]], depth: dict[[str, int]]) -> tuple[[list[str], dict[[str, str]], dict[[str, list[str]]]]]
    """
    The spine in render order: every step immediately after the parent it
    nests under.
    Sorting by `(depth, code)` is not enough, and the way it fails is silent.
    The page carries nesting as indentation, so a step at depth d+1 reads as
    a child of whatever step at depth d preceded it — which, under a plain
    sort, is whichever one happened to sort last. One group with two roots,
    or one step with two parents, and the page asserts a descent nobody
    declared. Found in `anthology-of-the-sota`, where Kimi Linear rendered
    as a descendant of Mamba-3 because Gated DeltaNet has two parents.
    So: choose one parent per step — the deepest, ties broken by code, so a
    step nests under the most specific thing it extends — and emit each
    subtree depth-first from its root. The other parents are real and are
    returned to be named rather than dropped.
    """

def lines_of(chain) -> list[Line]
    """
    Every sequence in one chain, spines ordered oldest first.
    A document is on the spine when it extends something or something
    extends it; one attached only by a cross-link renders alongside. Both
    the page and `walk()` come through here, so the view and the query
    cannot disagree about what a line contains.
    """

def walk() -> list[Line]
    """Every sequence in every declared chain."""

def rows() -> list[str]
    """
    A succession that loops: always wrong, mechanically detectable, and
    not repairable — which of two steps came first is not in the data.
    A relation stated on only one side used to be reported here too. It
    moved to `relations.py`, because it is a fact about the relation and not
    about any chain that happens to walk it: a declared pair is one-sided or
    it is not, whether or not a page renders it.
    """

def _spine(chain) -> str
    """
    The chain's spine relations, as prose — `` `extends:` `` for the
    common case and `` `extends:` and `corrects:` `` for a signed one. One
    implementation, because the cycle finding and the page header name the
    same thing and drifting apart would be a small lie in two voices.
    """

def _reaches(start: str, spine: dict[[str, list[str]]]) -> set[str]
    """
    Every code reachable from one, following the spine. Visited-guarded,
    so a cycle terminates rather than being discovered by recursion depth.
    """

def _link(doc: Adr, chain) -> str
    """
    A target that resolves from where the page renders.
    It points at the *source* document, not at the scheme's view directory:
    an index-rendered scheme puts a README and its tag pages there, never a
    page per document, so `docs/literature/LIT-140.md` resolves to nothing.
    The index's own rows have always linked this way, through `prefix_for`,
    and the first version of this function inventing a second convention was
    caught by the first real corpus it met — no fixture had checked that a
    rendered target exists.
    """

def _annotation(doc: Adr, chain) -> str
    """
    One step's value along each facet the chain names, in that order.
    Read through the compiled contract rather than raw frontmatter, so a
    field with a `default` shows its default rather than a blank — what
    ADR-076 means by an effective value never being absent — and a `status:`
    carrying a qualifying note reads as its word.
    """

def _step(doc: Adr, chain, lead: str) -> str
    """
    One line of the rendered list: the code, the title, and the status
    *value*.
    `Adr.status` is the composed display form — `Superseded — by [X](…);
    note` — and this page wants none of that. The successor is the next
    line, so linking it here says twice what the shape already says; and the
    note is an argument about why the step happened, which is the half this
    view deliberately leaves on the document. Rendering the composed form
    also dragged a link authored in the source's frame onto a page that
    renders somewhere else, which is a thing to rebase rather than a thing
    to want. `status_value` is the field, and the fields are why it is
    there to ask for.
    """

def _render(chain, lines: list[Line]) -> str

def outputs() -> dict
    """
    The rendered pages, for `luria index` to write and `--check` to
    compare — one entry per declared chain, none at all for a project that
    declares none.
    """

def emit(code: str) -> None

```

## luria/ci.py
```python
def running_in_ci(env: dict[[str, str]] | None) -> bool
    """True when any known CI variable is set to something not falsey."""

def regenerate_remedy(command: str) -> str
    """
    "How do I clear this?" — answered for where the reader is standing.
    In a terminal the bare command is the whole answer. In a build the reader
    needs the half that is easy to miss: the output has to be **committed**.
    Both ways of doing that are legitimate — regenerate locally, or let a
    generation job commit and push — and the CI form names both rather than
    steering people away from automating it (ADR-029). What it warns against
    is the specific broken shape: dropping the generator into the checking job
    and committing nothing, which discards the output *and* leaves the check
    comparing the generator against itself.
    """

```

## luria/citation.py
```python
def path() -> Path

def readme() -> Path

def _author(entry: dict) -> str
    """
    One author, in BibTeX's `Family, Given` order.
    A CFF author is either a person (`family-names`/`given-names`) or an
    entity (`name`). Both are legal and they format differently, so the entity
    form is braced to stop BibTeX splitting a company name into a surname.
    """

def _key(data: dict, authors: list[str]) -> str
    """
    `marx_luria` — the surname and the title, lowercased.
    Stable across releases on purpose: a citation key that moved with the
    version would break every bibliography that had already used it, which is
    the opposite of what a citation is for.
    """

def entry() -> str
    """The BibTeX entry, or "" when there is no readable `CITATION.cff`."""

def _inner() -> str

def region() -> str

def rewrite(text: str) -> str
    """
    The README with its citation region refreshed.
    Unchanged when there is no region — a project that has not opted in is not
    nagged, which is the same bargain the badge region makes.
    """

def run(write: bool, check: bool) -> None
    """Print, write, or check the README's citation region."""

```

## luria/cli.py
```python
def _survivable_console() -> None
    """
    Never let a console encoding turn output into a traceback.
    Every file this package reads and writes is UTF-8 by construction, but the
    *console* belongs to the platform: a Windows terminal at cp1252 cannot
    encode the arrow in `luria init → path`, and the default behaviour is to
    raise rather than to degrade. That turned a scaffold into a stack trace on
    a machine where nothing was wrong (#112).
    The stream keeps its own encoding — writing UTF-8 at a cp1252 console
    would trade a crash for mojibake — and only its error handling changes, so
    a character the console cannot show becomes `?` and the line still reads.
    Set `PYTHONUTF8=1` for full fidelity.
    """

def main() -> int

```

## luria/collect.py
```python
def is_stub(body: str) -> bool
    """True when a fragment carries no prose — only comments and whitespace."""

def find_marker(text: str) -> str | None

def collect(view_text: str, bodies: list[str], style: str, date: str) -> str
    """
    Assemble `bodies` (oldest first) into `view_text` at the insert marker,
    in the declared `style` (ADR-028).
    Pure — the CLI does the I/O. Raises if the marker is missing rather than
    guessing where the entries belong: silently appending to the wrong place in
    a long narrative is worse than failing (DP-1). A batch of only stubs
    changes nothing — in the changelog style that is what keeps an empty
    `## <date>` heading from accumulating per quiet collection.
    """

def _added_at(path: Path) -> tuple[[int, str]]
    """
    Sort key: commit time the fragment was added, then filename.
    Uncommitted fragments get a sentinel that sorts last — locally, the entry
    you just wrote is the newest thing in the batch.
    """

def fragment_paths(fragment_dir: Path) -> list[Path]

def collect_dir(name: str, fragment) -> int
    """Collect one fragment directory into its view. Returns the count."""

def run(dir: str, commit: bool) -> None
    """
    Assemble fragment directories into their views — all of them, or just
    --dir. --commit stages and commits the result (CI mode).
    """

```

## luria/comment_carry.py
```python
def _bare(line: str) -> str
    """
    The line with quoted strings and any trailing comment removed.
    Only used for counting brackets, so the replacement need not be valid
    TOML — it needs the same bracket balance outside strings.
    """

def _path(name: str) -> tuple[[str, Ellipsis]]
    """A dotted table name as a path, with the `luria` root dropped."""

def blocks(text: str) -> list[tuple[[tuple[[str, Ellipsis]], str]]]
    """
    (path, comment text) for every comment block, in document order.
    The text is the comment lines with their `#` and one following space
    stripped, joined by newlines — the shape ruamel wants to write it back.
    A block before the first table has the empty path: it is the document's
    own header rather than any key's.
    """

def rejoin(text: str) -> str
    """
    Restore the bare `#` lines a paragraph break inside a block becomes.
    ruamel writes an empty comment line as an empty *line*, which is not a
    comment: it detaches the prose below it from the key it documents, and in
    a long config that is the exact confusion the carry exists to prevent.
    A blank line between two comments at the same indentation was a `#`.
    """

def yaml_blocks(text: str) -> tuple[[str, list[tuple[[str, str]]]]]
    """
    A vocabulary file's own prose: (its header, [(key, comment), ...]).
    A vocabulary file is written at column 0 because it is its own file.
    Inlined under `vocabularies:` its keys are two levels in, and ruamel
    emits a carried comment at the column it was stored with — so every
    block lands flush left inside an indented mapping, documenting nothing
    a reader can see. Recovering them as text lets the caller attach them
    the same way every other block is attached, which is the one place that
    knows the indent.
    Only top-level keys are looked at: a vocabulary is a flat mapping of
    name to entry, and prose inside an entry is about a value, not a place.
    """

```

## luria/concretize.py
```python
def pending() -> list[tuple[[object, str, Path]]]
    """
    (scheme, tail, path) for every temporary document, in the order their
    numbers should be assigned: scheme by config order, then commit time.
    """

def _record_alias(text: str, old_code: str) -> str
    """
    `old_code` appended to the document's `formerly:` frontmatter — created
    after `status:` when the field doesn't exist yet, extended in place when
    it does. Runs after the tree-wide rewrite, so the alias is the only place
    the temporary code still appears.
    """

def _rewrite_files(renames: list[tuple[[str, str]]]) -> int
    """
    Every occurrence of each old code, in every file the record scans —
    history included, per ADR-040's second commitment: a spelling left behind
    in a journal is not preserved, it is a second name for the same document
    that grep and readers must both know. The collected changelog and the
    journal entries ride in `doc_files`; generated views are absent from it
    and the caller regenerates them.
    """

def run(check: bool) -> None
    """
    Concretize every temporary code — or, with --check, exit 1 naming the
    ones that exist (the trunk guard: a temp code on main means this command
    didn't run where merges serialize).
    """

```

## luria/config.py
```python
def find_root(start: Path | None) -> Path
    """
    The project root: nearest ancestor with a `luria.yaml`, else with a
    `.git`, else the starting directory. Env var `LURIA_ROOT` wins, which is
    what lets the tests run against fixture trees.
    """

def _merge(base: dict, override: dict) -> dict
    """
    `base` with `override` folded into it, nested tables merging.
    `OmegaConf.merge` is the function, and the reason to route through it
    rather than hand-roll the recursion is that the schema below then applies
    to the result: a key the schema types as a string and the config gives a
    list is a load-time error naming the key, instead of a `TypeError` three
    modules away in whatever first reads it (ADR-098).
    """

def in_fixture_namespace(prefix: str) -> bool
    """Whether a scheme prefix falls in the reserved fixture namespace."""

def is_temp_tail(tail: str) -> bool
    """
    Whether a code's tail is a temporary one — the ONE place that decides.
    Every other spelling of this question composes `TEMP_TAIL` with a prefix to
    match a code or a filename. A caller holding only the tail asks here rather
    than inventing a cheaper test: `not tail.isdigit()` looks equivalent and
    is not, because it answers "this is not a number" — which a malformed tail
    also satisfies.
    """

class TagGroup
    """
    A set of a scheme's tags that combine under a rule.
    `tags.yaml` declares what a tag *means*; this declares which of them may
    appear together, because some vocabularies are axes rather than piles. An
    argument is sound or overreaching or invalid — exactly one — and saying so
    in prose leaves it to be checked by nobody, which is how a rule becomes a
    comment.
    Opt-in per scheme: a scheme declaring no group is unconstrained, which is
    every scheme that exists today.
    """

class RequiredWhen
    """
    A field demanded only while another field says one of these things:
        schemes:
          SOTA:
            fields:
              promote_when: {}
        required_when = { status = ["Proposed", "Deferred"] }
    `requires` says a field must always be there, which is right for identity
    — a title, a source. It is wrong for a field that is *about* a state: a
    practice at a provisional status should say what would settle it, and one
    already in force has nothing to be waiting for. Demanding the field of
    everything makes most documents carry a key with nothing to put in it,
    and demanding it of nothing is what a project has today (#170).
    One field against a set of literal values, and no more than that. Not
    negation, not conjunction, not an expression: a config that can state
    arbitrary predicates is a config nobody reads at a glance, and the whole
    value of this one is that a reader sees the rule in the line.
    Pure data. Deciding whether it holds of a document needs the field's
    *effective* value — a status carrying a note is still that status, a
    vocabulary field with a default is never absent — and only the compiled
    contract knows how to resolve that. `Contract.demands` does it, which
    also keeps this module from reaching up into ones that depend on it.
    """

class PlainField
    """
    A field declared in the `fields` table that carries no vocabulary —
    its type is "any truthy value", the same as a `requires` entry, and what
    it adds is when the requirement applies.
    """

class FieldGroup
    """
    Several fields of which an entry must carry some — a requirement that
    is satisfied by any of them, named for what they have in common:
        schemes:
          LIT:
            field_groups:
              source: {}
        fields  = ["arxiv", "doi", "url"]
        require = "at-least-one"          # or "exactly-one", "at-most-one"
    `requires` demands every field it names; a paper that was never posted
    to arXiv but has a DOI, or only a URL, has a source all the same, and
    demanding `arxiv` of it is demanding the wrong thing. The group says
    what is actually required — *a source* — and which fields count as
    one. Opt-in per scheme, like a tag group (ADR-054).
    """

class Reference
    """
    A frontmatter field that holds a code from a named scheme.
        schemes:
          SOTA:
            references:
              source:
                scheme: LIT
                required: true
    `requires = ["source"]` already says the field must be there. What it
    cannot say is what the field MEANS, and the gap is wider than it looks: a
    required field is satisfied by any truthy value, so a practice citing a
    decision as its evidence passes, and so does one citing the string "a
    paper I read once". The rule the project was relying on — every practice
    names the paper behind it — was enforced only in the sense that the field
    was not blank.
    Declaring the relationship instead makes four checks out of one: present,
    shaped like a code, belonging to that scheme, resolving to a document
    (ADR-060).
    `converse` names the field holding the same relation read backwards —
    `extends` and `extended_by`, or `compared_against` naming itself, which
    is what symmetry *is*. Declaring it is what licenses `luria link --fix`
    to write one side from the other, and what makes a one-sided pair a
    finding; a relation with no declared converse is left entirely alone,
    because its reverse edge would be a guess (#178).
    `many` says the field holds a list of codes rather than one. Without it
    a list was stringified and its first code checked, the rest ignored —
    structured input coerced to prose and half-read, with no finding. A
    scalar field given a list is now a finding; a plural field checks and
    resolves every element, and each becomes an edge (#141).
    """

class Vocabulary
    """
    A frontmatter field backed by a scheme-local controlled vocabulary
    (ADR-076):
        schemes:
          SCENE:
            fields:
              worlds:
                vocabulary: worlds
                many: true
        default    = ["B"]        # the effective value when the field is absent
    `fields` is the table a field's shape and type are declared in; today
    `vocabulary` is the one type it takes, and `requires` and `references`
    remain the spellings for the other two kinds until they consolidate
    here. The values file is shaped like `tags.yaml`. Closed: a value
    outside the file is a finding. `required` (default false) and `default`
    are exclusive — a field with a default is never absent, so `required`
    would say nothing.
    """

def forget_documents() -> None
    """
    Drop the directory listings — for a writer that outruns mtime
    resolution, and for tests that rewrite a fixture faster than the
    filesystem can distinguish.
    """

def _declared_number(path: Path) -> int | None
    """
    The `number:` a document's frontmatter declares, or None.
    Read out of the frontmatter block only: a `number:` in the body is prose
    about identity, not a claim to one — and it does occur there, so the
    block boundary is what makes the field readable without a YAML parse.
    """

@lru_cache(...)
def _code_pattern(prefix: str) -> Any

@lru_cache(...)
def _temp_pattern(prefix: str, tail: str) -> Any

class Scheme
    """
    A family of referable documents — `ADR-012`, `RFC-7`, `SPEC-3`.
    Luria ships with one, and knowing that one is not built in is the point:
    the annotation vocabulary says `inactive-ok`, not `adr-ok`, and a code
    carries its prefix, so a second scheme is an entry here (ADR-006).
    """

    @property
    def view(self) -> Path
        """The directory an index-rendered scheme's view lives in."""

    @property
    def index_path(self) -> Path

    @property
    def grouped_fields(self) -> tuple[[str, Ellipsis]]
        """
        Every field whose values a view groups by, axis first.
        The declared vocabularies, plus the axis when it declares none — a
        scheme may head its index with a field it has not enumerated, which
        is the ordinary starting point and what `luria init` scaffolds. One
        definition, because three places need the same answer: which
        directories the generator owns, which are exempt from the docs
        index, and which paths are generated (ADR-098).
        """

    @property
    def tag_dir(self) -> Path
        """
        Where the axis's per-value pages render. `<view>/<axis>/`, so a
        scheme whose axis is `tags` keeps the path it has always had.
        """

    def vocab_dir(self, field: str) -> Path
        """
        Where a grouped field's per-value pages render — the axis's among
        them, since it is a declared field like any other (ADR-098).
        Keyed on the FIELD, not on the vocabulary's name: a name is a config
        detail and a published path is not, so sharing a vocabulary between
        two schemes — or renaming one — must not move anybody's pages
        (ADR-098). Two schemes naming one vocabulary still render their
        own pages, under their own views.
        """

    @property
    def stub(self) -> Path

    @property
    def axis_field(self)
        """The `Vocabulary` behind `axis`, or None when there is no axis."""

    @property
    def tags_vocab(self) -> str
        """The NAME of the vocabulary behind the axis, for a finding to cite."""

    @property
    def tags(self) -> dict[[str, dict]]
        """This scheme's axis vocabulary, by value."""

    @property
    def statuses(self) -> dict[[str, dict]]
        """This scheme's status vocabulary, by value."""

    @property
    def pattern(self)

    @property
    def temp_pattern(self)

    def temp_of(self, path: Path) -> str | None
        """The temporary tail a filename carries, or None if it isn't one."""

    def temp_documents(self) -> dict[[str, Path]]
        """Tail → path for every temporary document awaiting concretization."""

    def _listing(self) -> tuple[[dict[[int, Path]], dict[[str, Path]]]]
        """
        (numbered, temporary) for this scheme's directory, read once.
        Both questions are answered from one walk, because they were two
        walks of the same directory and neither was cached.
        """

    def code(self, number: str | int) -> str

    def filename(self, number: str | int) -> str
        """
        `ADR-013.md` — the file is named for the code and nothing else.
        The title lives in the frontmatter, where a correction costs an edit
        rather than a rename plus every link that pointed at the old name
        (ADR-013).
        """

    def number_of(self, path: Path) -> int | None
        """
        This document's identity: its `number:`, or the one its filename carries.
        The frontmatter wins, because that is where identity lives (#219).
        The filename is the fallback and the witness — a record written
        before `number:` existed still reads, and `luria repair` populates the
        field from the path it already asserts, which is how a project
        migrates without anyone typing a number.
        Cached on (mtime, size) rather than reset by hand: every writer of a
        document bumps its mtime, so the cache invalidates itself and no
        caller has to remember. Reading the field costs a parse, and this is
        the hot path — `documents()` runs on every lint, index and link
        pass.
        """

    def number_in_name(self, path: Path) -> int | None
        """
        The document number a filename carries, or None if it isn't one.
        Deliberately tolerant of a trailing slug: `adr-010-some-title.md` is
        what most projects arrive with, and refusing to read them would make
        adoption a rename-everything-first proposition. Luria *writes* the short
        form and *reads* both.
        """

    def documents(self) -> dict[[int, Path]]
        """
        Number → path for every document in this scheme, ascending.
        The one place a scheme directory is read. Five copies of this glob had
        accumulated, each with its own regex — the drift DP-4 names, harmless
        only for as long as the filename shape never changed.
        """


def _fold_uris(spec: dict, where: str) -> dict[[str, str]]
    """
    A table's `uris` plus its sugar spellings, as one dict.
    `url` and `pin_url` ARE `uris.read` and `uris.bytes` — the short names
    for the two relations Luria itself consumes. Folded at load so exactly
    one structure answers at render time (DP-4); setting both spellings to
    different values is a config error rather than a silent winner.
    """

class RemoteScheme
    """
    How one of a remote's code families constructs (ADR-023).
    A remote is not one directory of files — it is a project, and different
    schemes in it have different shapes. Each entry names one construction:
        `remotes.SG.schemes.ADR`
        dir = "docs/decisions"                 # file per code
        `remotes.SG.schemes.DP`
        document = "docs/design-principles.md" # sections of one file…
        anchor = "dp-{number}"                 # …at Luria's stable anchors
    `anchor` defaults to the prefix lowercased plus the number — `dp-18` —
    which is the anchor shape Luria's own document render emits, so a remote
    on current conventions needs only the `document` line. A `url` template
    overrides both, and a `uris` table names further relations for this
    family alone — both with the full template vocabulary (see `Remote`).
    """

    def anchor_for(self, number: int) -> str


class Remote
    """
    Another project's record, cited from this one.
    A reference to it composes the remote's prefix with the foreign scheme's
    own code — `LU-ADR-013` — so the namespace is explicit at the point of use
    and nothing has to guess which project an unprefixed code meant (ADR-016).
        `remotes.LU`
        name = "luria"
        repo = "dmarx/luria"             # GitHub owner/name
        ref  = "main"                    # branch or tag the links point at
        dir  = "record/decisions.d"      # where its decisions live
        url  = "https://…/{code}.md"     # optional: overrides construction
    Everything but `repo` (or `url`) has a default, because the defaults are
    Luria's own conventions — a remote that uses them needs one line. A code
    family with a different shape gets a `schemes` entry (`RemoteScheme`),
    which wins over these remote-level settings for its own prefix.
    A remote need not hold a Luria-shaped record at all (ADR-024). Give it a
    `uid` pattern and its references are the prefix, the delimiter and
    whatever the pattern matches — an arxiv id, a ticket key — constructed
    through the `url` template, which can index the uid's capture groups by
    position:
        `remotes.ARXIV`
        uid = "(\d{4})[.:](\d{4,5})"
        url = "https://arxiv.org/abs/{1}.{2}"   # {0} or {uid} is the whole tail
    A `pin_url` template names where the remote's *stable bytes* live, which
    is what lets `luria remotes --pin` endorse content that has no GitHub
    file behind it (#135) — arXiv's e-print archive is the paper where its
    abstract page is a rendering:
        pin_url = "https://arxiv.org/e-print/{1}.{2}"
    Both are the short names of a general table: a code relates to a SET of
    named URIs, each through a template over one vocabulary — {code},
    {number}, {prefix}, {repo}, {ref}, {dir}, {document}, {anchor}, and
    {filename}, which the discovered lockfile map fills. `url` is
    `uris.read`, `pin_url` is `uris.bytes`, and a relation Luria does not
    ship yet is one more name:
        `remotes.LU.uris`
        bytes   = "https://gitlab.example/{repo}/-/raw/{ref}/{dir}/{filename}"
        history = "https://github.com/{repo}/commits/{ref}/{dir}/{filename}"
    GitHub's blob/raw pair is simply the shipped default pair of `read` and
    `bytes` templates for a remote with a `repo` — a different forge is a
    different pair of lines, not a different subsystem.
    """

    @property
    def label(self) -> str

    def canon(self, tail: str) -> str
        """
        The tail's one spelling. `ADR-32` and `ADR-032` name one document
        in a scheme-shaped remote; a uid is already exact and stays put.
        """

    def base(self, dir: str | None) -> str
        """A directory in the remote, as a URL."""

    def scheme_for(self, code: str) -> RemoteScheme | None

    def link(self, code: str, filename: str | None) -> str
        """The reader's URL for a foreign code — the `read` URI."""

    def uri(self, name: str, code: str, filename: str | None) -> str
        """
        Render the named URI for a code — the one place a code becomes a
        URL, whatever the relation's name.
        A code relates to a SET of URIs, not one: `read` is where a reader
        lands, `bytes` is what a content pin hashes (#135), and a project may
        declare further names ahead of a consumer. Every name renders through
        one template vocabulary — {code}, {number}, {prefix}, {repo}, {ref},
        {dir}, {document}, {anchor}, {filename} — so a new relation is a
        template, never a subsystem.
        Precedence for `read` is ADR-023's: the scheme's template, then the
        scheme's shape (a `document`'s anchored page, a `dir`'s file), then
        the remote's template, then the remote-level file construction. For
        every other name a declaration beats a derivation at either level
        (ADR-066), and a derived default exists only where `read` itself
        resolves by construction — a remote whose documents live behind a
        `url` template has told us nothing about where its bytes live, and a
        guessed raw URL would be a claim nobody made. A chosen template that
        cannot fill its variables renders "" rather than falling through:
        silent fallback would hide a misspelled variable behind a working
        convention (DP-1).
        `filename` carries the discovered-map contract (ADR-016): "" means
        never discovered (the code-only convention fills {filename}), a name
        means discovered, None means the map is authoritative and silent —
        {filename} is then unavailable, so any construction needing it
        renders "".
        A uid remote has exactly one rung per name — its own template, fed
        the whole tail as {0}/{uid} and its capture groups by position
        (ADR-024).
        """

    def _construction(self, scheme: RemoteScheme | None) -> str
        """
        How `read` constructs when no template governs it: "document",
        "file", or "" when a template (or nothing) answers instead. The only
        shapes whose other-name defaults are derivable rather than guessed.
        """

    def _render(self, template: str, code: str, scheme: RemoteScheme | None, filename: str | None) -> str
        """
        One template, one vocabulary. A variable the remote cannot supply
        is simply absent, and a template that references it renders "".
        """

    def _format(self, template: str, code: str) -> str
        """
        A uid template, fed the whole tail as {0}/{uid} and its capture
        groups by position (ADR-024).
        """

    def auto_pin(self, code: str) -> bool
        """
        Whether config declares this code's content pinned (#135).
        `pin = true` on the remote covers its whole namespace; on one of its
        schemes, that code family. Declared per source rather than per
        citation, because that is where the judgement lives: a record this
        project leans on is endorsed as a body of knowledge.
        """


class Fragment
    """
    One fragment directory: where its pieces assemble to, and in what shape.
        fragments:
          record/changelog.d: CHANGELOG.md         # the append style
          record/changelog.d:                      # or, spelled as a mapping:
            file: CHANGELOG.md
            style: changelog
    `append` is the narrative shape: bodies oldest-first, inserted before the
    marker, so the marker stays at the end and the log reads top-down.
    `changelog` is the release shape: each collection is one dated batch,
    inserted right after the marker so the newest batch reads first, fragments
    newest-first within it. The shape is configuration because the fragment
    convention is the contract, not the collector (ADR-028) — the same
    directory-of-fragments serves either reading order.
    """

def primary_tags(prefix: str, values: dict) -> frozenset[str]
    """
    Terms this scheme may carry as a primary, from the vocabulary itself.
    A tag says which schemes it is a primary for, where the tag is defined:
        training-optimization:
          label: Training optimization
          primary_for: [LIT, SOTA]
    Without this a shared vocabulary has to be restated as a `tags` list per
    group, which is the same set of strings written a third and fourth time —
    and the copies drift, because nothing relates them. Measured on the record
    that motivated this: seven terms across four places, and the blurbs for
    the same tag already disagreed between two of them (ADR-060).
    """

def _tag_groups(prefix: str, field: str, raw: dict, tag_values: dict | None) -> tuple[[TagGroup, Ellipsis]]
    """
    Read one field's `groups:` tables.
    Validated here rather than at lint time: a misspelled rule is a config
    error, and a config error that surfaces as "no violations" is the quiet
    failure this whole feature exists to remove.
    A group that lists no `tags` derives its membership from the vocabulary's
    `primary_for` keys. That is still validated eagerly — an empty derivation
    is the same "constrains nothing" error as an empty list, and finding it at
    load keeps the promise above.
    """

def _field_groups(prefix: str, raw: dict) -> tuple[[FieldGroup, Ellipsis]]
    """
    Read a scheme's `schemes.X.field_groups` tables. Validated at
    load like a tag group: a group naming no fields, or a rule that is not
    one, would surface as "no violations".
    """

def _checked_converses(prefix: str, refs: tuple, schemes: dict) -> tuple
    """
    Refuse a converse declaration that cannot mean what it says.
    A relation's converse is the relation read backwards: if A `extends` B
    then B is `extended_by` A. Declaring the pair is what lets the fixer
    complete one side from the other, and symmetry is simply the case where
    a relation is its own converse.
    **The converse lives on the scheme whose codes the field holds**, which
    is the declaring scheme itself only when the relation does not cross one.
    `SOTA.introduced_by` holds `LIT` codes, so its converse `introduces` is a
    field on `LIT` holding `SOTA` codes — and until ADR-097 that could
    not be declared at all, so a crossing relation was sayable from one end
    and unreachable from the other (#253).
    Four things have to hold, and each of them fails silently otherwise —
    a pair that never completes looks exactly like a record with nothing
    missing (DP-15).
    """

def _cite(prefix: str, spec: dict) -> str
    """
    Read and check `schemes.X.cite`.
    Unset resolves to what the scheme already does, so the key is inert until
    a project sets it.
    Two refusals rather than one, because they are different mistakes. An
    unknown word is a typo; an EXPLICIT `cite = "view"` on an index scheme is
    a request that cannot be honoured — there is no assembled document to
    anchor into — and quietly resolving to the page anyway would answer a
    question the project did not ask (DP-1).
    """

def _references(prefix: str, raw: dict) -> tuple[[Reference, Ellipsis]]
    """Read a scheme's `schemes.X.references` table."""

def _required_when(where: str, spec: dict, required: bool) -> RequiredWhen | None
    """
    `required_when = { status = ["Proposed"] }` — one field, one set of
    values. Validated eagerly, for the reason every other declaration is: a
    condition that can never hold, or one whose meaning the reader has to
    guess, surfaces as "no violations".
    """

def _fields(prefix: str, raw: dict, scheme_dir: Path, root: Path, references: tuple, scaffolding: bool, vocabularies: dict | None) -> tuple
    """
    Read a scheme's `schemes.X.fields` tables, as
    `(vocabularies, plain fields, derivations)`.
    One table for a field's shape and type. `vocabulary` is the one *type* it
    takes; `required_when` is a rule about when the field applies and needs no
    type, so a table declaring only that is a plain field — any truthy value,
    like a `requires` entry, demanded only under its condition (#170). A table
    declaring neither is an error rather than a field that constrains nothing,
    and a field also named in `references` is two declarations of one thing.
    `derive` says where the value comes from rather than what shape it is, so
    it is a declaration in its own right and composes with `vocabulary` — the
    pairing that gets "the first tag is a real topic" out of the vocabulary
    check already written, with no second check to keep in step (#216).
    Validated here, eagerly, for the reason tag groups are: a declared axis
    with no values, or a default no value matches, would surface as "no
    violations", which is the quiet failure a declaration exists to remove.
    """

def _fragment(spec) -> Fragment

class Chain
    """
    A relation walked transitively and rendered as sequences (#171).
        chains:
          lineage:
            scheme: LIT
            relation: extends
            sibling: compared_against
            output: docs/lineage.md
            title: Lines of work
    `relation` takes one field or several — `["extends", "corrects"]` — and
    several are walked as one spine (#211). That is not a convenience: a
    record can carry succession with a sign, where "builds on the parent" and
    "exists because the parent is broken" are both steps in one line and one
    relation renders them identically. Two relations state the difference
    where a per-entry attribute would have to qualify a reference, which is
    the shape the consumer record's own ADR-011 refuses. The sign is which
    field the code sits in.
    `edges.py` already reads a reference field as a typed relation, and the
    site already renders each page's neighbours. What no view answered is
    *what sequence is this document a step in* — and that is the question the
    documents themselves were answering, one prose paragraph each, until two
    of them went stale on the same fact and had to be corrected in two
    places.
    Both fields must be declared references on the scheme; a chain over a
    field nothing declares would render nothing, and nothing looks exactly
    like current (DP-15).
    """

class Journal
    """
    Dated entries that persist, rendered into books (ADR-020).
        `journals.devlog`
        dir         = "devlog.d"        # entries, partitioned yyyy/mm/dd/
        output      = "docs/devlog"     # a directory of books plus an index
        granularity = "month"           # year | month | day
        title       = "Development log"
        blurb       = "…"               # optional prose for the index
    The difference from a fragment directory is that nothing is consumed: an
    entry was true when written and stays true, so the view is *generated* from
    sources that persist rather than collected from sources that are deleted.
    """

    @property
    def rel_dir(self) -> str


class Site
    """
    How the record publishes as a browsable site (ADR-042).
        `site`
        title      = "Luria"
        base_url   = "dmarx.github.io/luria"
        source_url = "https://github.com/dmarx/luria/blob/HEAD"
        exclude    = ["template/**"]
    Only `exclude` is genuinely per-project: the rest default off `issue_url`,
    because a project that told Luria where its issues live has already told
    it which GitHub repository it is (DP-3 — derive the projection).
    `source_url` is where a link lands when its target is a repository file
    the site does not publish: a workflow, a template, the licence. Empty
    means "leave those links alone", and `luria site` says how many it left.
    The branding keys are the project's own artwork, cited by path:
        icon      = "assets/brand/icon.svg"    # favicon, any square image
        logo      = "assets/brand/lockup.svg"  # shown in place of the title
        logo_dark = "assets/brand/lockup-inverted.svg"   # optional
        `site.theme.light`
        light = "#f4f1e8"                      # any of Quartz's colour names
    `logo_dark` is only needed when the artwork can't invert itself. A logo
    whose SVG exposes a `--luria-ink` custom property — the convention this
    project's own kit uses — is re-inked to the theme automatically, and one
    that doesn't is used as it is in both modes.
    """

class Config

    def nested_records(self) -> list[Path]
        """
        Directories matched by `include_records` that are really records.
        One authoritative answer, because three callers need it and they must
        agree: `luria index` regenerates these, `luria index --check` compares
        them, and `luria site` mounts them. Two implementations of "which
        directories are nested records" would drift into a state where a record
        is published but never regenerated (DP-4).
        A match without a `luria.yaml` is skipped rather than failed —
        `examples/*` is the natural way to write "every example", and a stray
        directory beside them should not break a build. A *pattern* matching
        nothing is an error, raised by the callers, because an include that
        silently covers no record is a section of the project quietly not
        maintained (DP-1, DP-15).
        """

    def unmatched_record_patterns(self) -> list[str]
        """Patterns in `include_records` that name no record at all."""

    def _index_scheme(self)

    @property
    def index(self) -> Path

    @property
    def stub(self) -> Path

    @property
    def tags(self) -> dict[[str, dict]]
        """The index scheme's tag vocabulary."""

    @property
    def tag_dir(self) -> Path

    @property
    def config_doc(self) -> Path
        """Where the generated configuration reference lands."""

    @property
    def record_doc(self) -> Path
        """
        Where the generated description of *this* project's record lands.
        Distinct from `config_doc` because they answer different questions and
        only one of them is about this repository: the reference is the schema
        (identical wherever Luria is installed), this page is the shape a
        particular project gave it.
        """

    @property
    def owns_schema(self) -> bool
        """
        True in the tree that *contains* the dataclasses the configuration
        reference is a projection of.
        The reference is generated rather than written so it cannot drift from
        `config.py` — an argument that only holds where `config.py` is a file
        the reader can open. Rendered into an adopting project it is a
        vendored copy of somebody else's schema, carrying a stamp that tells
        the reader to go edit a file they do not have, and going stale on
        their next upgrade with nothing in their repository responsible for
        it. So the page renders where its source lives, which is here (and in
        a project that vendored the package rather than installing it — for
        which the same argument holds, and the same file is present).
        """

    @property
    def remotes_lock(self) -> Path
        """
        Discovered code→filename maps for the remotes, checked in.
        A lockfile rather than a live lookup: CI and an offline checkout have
        to resolve a foreign reference the same way a laptop with network does,
        and a private remote can only be read from a local clone anyway.
        """

    def is_generated(self, path: Path) -> bool
        """
        A view the generator owns. Rewriting one is pointless — the next
        build undoes it — so the reference fixer skips them.
        The status reports count too (#35): they *list* retired and dangling
        codes, so scanning them would report the report — every flagged code
        would gain a citation site inside the page that flags it, and the
        view could never converge.
        """

    def is_template(self, path: Path) -> bool
        """
        A scheme's `_template.md` — a form, not a document.
        Luria reads it to scaffold new entries, so its example codes are
        illustrative by definition: a placeholder resolves to nothing, and a
        realistic example is a real document that may not be in force. Both
        were reported against the template itself on the record that
        motivated this, which is a finding about a form nobody filed
        (ADR-061).
        Exempt from the CODE machinery only. A template's relative link
        targets are still checked, because a broken path there is copied into
        every document made from it.
        """

    def is_historical(self, path: Path) -> bool
        """
        A dated record: true about the day it was written, and never
        updated to stay true. Scanning one for stale references produces
        permanent, unactionable rows, so the status report skips it.
        Three shapes qualify: a file listed in `code.historical`, an
        uncollected fragment (it is about to *become* one), and anything in a
        journal — its entries and the books they render into alike. The last
        one is why this is a method rather than the set-membership test it used
        to be: a journal's entries are nested, so `path.parent` is not the
        journal directory.
        """

    def link_base(self, path: Path) -> Path
        """
        The directory a link written in `path` resolves against.
        Not always `path.parent`. A fragment is *assembled into* a file that
        lives somewhere else, so a link relative to the fragment's own directory
        breaks the moment it is collected (ADR-005). Two kinds of fragment
        qualify — a changelog/devlog fragment, and a document-rendered scheme's
        source, which is the same relationship wearing a different name.
        """

    def rel(self, path: Path) -> str


def load(root: Path | None, text: str | None, scaffolding: bool) -> Config
    """
    The config at `root`, or parsed from `text` when given.
    `text` exists for `luria init --config`: the scaffold has to be planned
    from a config that is not on disk yet (and, under `--dry-run`, never will
    be), so the parser is reachable without a write.
    """

def _chains(raw: dict, schemes: dict, root: Path) -> dict[[str, Chain]]
    """
    Every declared chain, checked against the schemes it walks.
    Validated here for the reason every other declaration is: a chain over a
    scheme nothing declares, or over a field that is not a reference, renders
    an empty page — and an empty page is indistinguishable from a correct
    one (DP-15).
    """

def _check_conditions(prefix: str, scheme) -> None
    """
    Every `required_when` on a scheme, against what that scheme can
    actually say — checked once the whole scheme is assembled, because a
    condition may name a field declared in a different table.
    Shape validation alone was not enough, and the module's own reason for
    validating eagerly is why: a condition that can never hold "surfaces as
    no violations". `{ staus = ["Proposed"] }` and `{ status = ["proposed"] }`
    are the two likeliest authoring mistakes, and both used to be accepted,
    never hold, and leave the field silently never required — the exact
    outcome the declaration exists to remove (review of #172).
    Values are checked only where a closed set exists: the status vocabulary,
    and a field the scheme backs with one. A free-text field
    (`stage = ["blocked"]`) has nothing to check against, and refusing on
    that ground would forbid the ordinary case.
    """

def _check_derivations(prefix: str, scheme, schemes) -> None
    """
    Every `derive` against the scheme that declares it (#216).
    Two things the shape check cannot know on its own: whether the source is a
    field this scheme can hold, and whether it holds a *list*. Both are eager
    for the usual reason — a derivation off a field nothing carries resolves to
    nothing on every document, which reads exactly like a record with no
    findings.
    List-valued is the harder rule and the one worth stating: `first:` of a
    single value is that value, so a derivation off a scalar is a rename
    wearing a derivation's clothes, and renames belong in the frontmatter.
    """

def _check_target_fields(where: str, rule, ref, schemes) -> None
    """
    A followed template against the scheme it actually renders against.
    Takes the schemes being built rather than reading `current()`: this runs
    *during* load, and asking the loader for the config it is still assembling
    recurses until the stack ends.
    Skipped when the target is a scheme this project does not declare — a
    remote, or a prefix configured elsewhere — because there is nothing local
    to check the names against and refusing would forbid a legitimate shape.
    """

def _alias_template(prefix: str, raw) -> str
    """
    A scheme's `alias` template, validated for shape where it is read.
    Two things are checkable without any document: that the template renders
    at all, and that it starts with this scheme's prefix. The prefix matters
    because every reference scanner in luria finds a code by its prefix
    first — a spelling that does not carry one is unreachable however well it
    resolves, which is the quiet kind of failure eager validation exists to
    prevent (#219).
    """

class _Probe(dict)
    """
    Answers to any name, so a template's *shape* can be checked without a
    document. Indexing and attribute access have to work too, since
    `{authors[0]}` and `{date.year}` are ordinary template spellings.
    """

    def __missing__(self, key)

    def __getitem__(self, key)

    def __getattr__(self, name)

    def __format__(self, spec)


def _conditions(scheme)
    """
    Every (field name, condition) this scheme declares, across the tables
    a condition can be written in.
    """

def _schemes(raw: dict, root: Path, scaffolding: bool, vocabularies: dict | None) -> dict[[str, Scheme]]
    """
    Every declared scheme, with the cross-scheme checks that need them all.
    A reference naming a scheme that does not exist is a config error, and it
    can only be caught once the whole family is known — so it happens here
    rather than in `_references`, which sees one table at a time.
    """

def _site(raw: dict, root: Path) -> Site
    """
    The site settings, with every unset key derived from `issue_url`.
    A non-GitHub (or absent) issue URL derives nothing: the title falls back
    to the directory name and the two URLs stay empty, which `luria site`
    reports rather than guessing at.
    """

@lru_cache(...)
def current() -> Config
    """
    The config for this process. Cached because every module wants it and
    re-reading per call would make the file's mtime a source of skew.
    """

def reset() -> None
    """Drop the cache — for tests that point `LURIA_ROOT` at a fixture."""

@contextmanager
def rooted(root: Path)
    """
    Run a block with `root` as the current project, then put it back.
    `load(root)` already builds any project's config, but that is not enough
    to *operate* on one: the modules underneath — `doc_refs.link_base`,
    `edges.graph`, the renderers — call `current()` for themselves, by design,
    since threading a config through every call site would be its own kind of
    mess. So switching projects means switching the global, and the honest
    thing is to make that a bounded, restoring operation with a name rather
    than have callers set the environment variable and hope.
    Reentrant by construction: the previous value is captured and restored,
    including its absence.
    """

```

## luria/config_doc.py
```python
def fence(text: str, lang: str) -> str
    """Indented example blocks in a docstring → fenced code blocks."""

def rows(cls: type) -> list[tuple[[str, str, str]]]
    """
    (key, type, default) for every public field of a config dataclass.
    The whole point of the module: this reads the schema rather than a list,
    so a field added to `Site` cannot be silently missing from the reference.
    The default shown is the *dataclass's* — the answer to "what do I get if I
    omit this key?", which is the question a reference is asked. What the
    shipped `luria.yaml` happens to set for its own ADR scheme is a different
    question, and answering it here would tell a project adding a second
    scheme that `output` defaults to `docs/decisions`, which is false.
    """

def _render_default(value) -> str

def table(cls: type) -> str

def plain_table(keys: list[tuple[[str, str]]], defaults: dict) -> str

def render() -> str

def outputs(out_dir: Path | None) -> dict[[Path, str]]
    """
    The reference, keyed by where it lands — the unit `luria index`
    renders, so a stale page fails the same check as every other view.
    """

def retire() -> list[Path]
    """
    Remove a configuration reference this project no longer generates.
    Until ADR-059 the page rendered into every adopting project, so an upgrade
    leaves one behind: a vendored copy of Luria's schema, already a release out
    of date, with nothing in the repository responsible for keeping it true.
    Left alone it is worse than absent, because it reads as current.
    Deleting a file in somebody else's repository wants a reason better than
    "we stopped writing it", so the guard is the generator's own marker: its
    presence is proof Luria wrote this file, and its absence means the path is
    the project's own prose and is left exactly where it is.
    """

def write(out_dir: Path | None) -> list[Path]

def swap(m: Any) -> str

```

## luria/contract.py
```python
class Field
    """
    One frontmatter field an entry must (or may) carry, and what it holds.
    `reference` is a scheme prefix when the field names a document, `None`
    when any truthy value satisfies it — the gap between the two is the one
    ADR-060 measured. `because` is every declaration that contributed, so a
    finding can say why rather than only what.
    """

class Contract
    """What one scheme demands of each of its entries."""

    def derivation(self, name: str)
        """
        The rule computing `name`, or None when it is written (#216).
        Read by everything that must tell a computed field from a written one:
        the scaffold, which has no flag to offer for one, and the record page,
        which says where the value comes from rather than what shape it is.
        """

    def demands(self, field: Field, meta: dict) -> bool
        """
        Whether this document must carry the field. Consulted everywhere
        `required` used to be read directly, so a conditional requirement
        cannot be honoured by one check and ignored by the next — which is
        the failure mode this module was written to end.
        A method on the contract rather than on the field, because deciding
        whether a condition holds needs the *effective* value of the field it
        names, and only the compiled contract knows how to resolve that.
        """

    def reading(self, name: str, meta: dict) -> list
        """
        What a field is read as on one document — the same resolution the
        checks and the record page use, so a condition sees the value the
        rest of the machinery sees.
        Three cases, and the first two are why this cannot read raw
        frontmatter. A `status:` carrying a qualifying note is still that
        status and the note is its own field (ADR-072), so
        `Proposed — pending a replication` reads as `Proposed`. A vocabulary
        field with a `default` is never absent (ADR-076), so a document that
        omits it reads as the default — and reading raw made a condition on
        such a field never hold, for precisely the documents it was written
        about. Everything else is what the document says: a list reads as its
        elements, and an absent field reads as nothing, which is "the
        condition does not hold" rather than an error (the missing-field
        finding is the document check's, not this one's).
        """

    @property
    def empty(self) -> bool
        """
        True for every scheme that declares nothing — which is every
        scheme that predates the three tables, and the shipped ADR scheme.
        """


def built_in(scheme) -> tuple[[Field, Ellipsis]]
    """
    The fields a scheme gets without asking — today, the one naming what
    replaced a retired document.
    A **default**, not a law (ADR-085). The field's name and the status
    that demands it come from the scheme (`successor` and `retires_on`,
    themselves defaulting to `superseded_by` and `Superseded`), and a scheme
    declaring the field in its own `references` table replaces this outright
    — `for_scheme` merges these last, with `setdefault`.
    `active` set that precedent long ago: which word means *in force* was
    always the project's to choose. What generic code needs is the role, not
    the word.
    """

def for_scheme(scheme) -> Contract
    """
    Everything `luria.yaml` declares this scheme demands of an entry.
    Fields keep declaration order — `requires` first, then the references
    that did not merge into one — so findings read in the order the config
    was written.
    """

def _cite(because: tuple[[str, Ellipsis]]) -> str
    """
    `(luria.yaml: schemes.SOTA.requires, schemes.SOTA.references.source)`
    — every declaration behind an obligation, grouped by the file it is in,
    so a reader is sent to the key and not just the file.
    """

def field_group_because(contract: Contract, group: FieldGroup) -> str

def group_because(contract: Contract, group: TagGroup) -> str
    """
    Where a tag group was declared — and, when its membership is derived,
    where the members come from.
    """

def _condition(field: Field, meta: dict | None) -> str
    """
    Why a conditional requirement fired, in the document's own words:
    the field that decided and the value it held. A finding that recites only
    the rule leaves the reader to work out which of their fields turned it
    on.
    """

def explain(contract: Contract, field: Field, meta: dict | None) -> str
    """
    Why a field is demanded, in the words the finding has always used,
    plus the key that said so.
    The provenance is read out of the obligation rather than spelled here,
    so the day one comes from somewhere other than `luria.yaml` the finding
    says so without this function learning about it.
    """

def describe(contract: Contract) -> list[str]
    """
    The whole contract, one line per obligation, each naming where it was
    declared — the same words a finding cites, from the same place (DP-4).
    What `docs/record.md` prints under "what an entry must carry".
    """

def reference_code(value: str) -> str | None
    """
    The code a reference field holds: a scheme code, or a remote one.
    Remotes are read first, through the one reader of their anatomy. A uid
    remote's tail is opaque — `ARXIV-2110.08058`, `DOI:10.1145/3600006` —
    and the scheme-shaped pattern, tried alone, read `ARXIV-2110` out of
    the first and nothing out of the second, so a `superseded_by:` naming a
    paper failed as "names no scheme or remote" while the same code in
    prose resolved. Any truthy value was never the contract; a remote code
    always was (`_any_scheme_violations`).
    """

def resolvable(prefix: str) -> set[str]
    """
    Every code a reference into `prefix` may name: the numbered documents
    and the temporary ones awaiting concretization (ADR-049).
    """

def values_of(field: Field, raw) -> list | None
    """
    The values a reference field holds, one per element, or None when
    the shape contradicts the declaration.
    A plural field takes a list or a single value (a list of one, which is
    unambiguous). A scalar field given a list is None: the tool would have
    to guess which element was meant, and guessing is what stringifying
    the list and reading its first code used to do, silently.
    """

def effective_values(field: Field, raw) -> list | None
    """
    What a field is read as: its written values, or the default when it
    is absent. The source is never touched — a default is a convention the
    config states, not a fact the tree does (ADR-076).
    """

def local_scheme(code: str) -> str | None
    """
    The configured scheme a code belongs to, or None for a remote code
    or a prefix nothing declares.
    """

def is_remote(code: str) -> bool

def _any_scheme_violations(contract: Contract, field: Field, rel: str, raw, known: dict[[str, set[str]]], meta: dict | None) -> list[str]
    """
    A built-in reference into any scheme: one code or a list, each a
    code that resolves in the scheme it names, or a remote code — and
    present at all when the contract demands it.
    """

def violations(contract: Contract, rel: str, meta: dict, known: dict[[str, set[str]]], resolve) -> list[str]
    """
    One document against its scheme's contract, one line per breach.
    `known` maps a target prefix to its resolvable codes; the caller loads
    each once per run rather than once per document. `resolve` is how a
    `from` derivation reads the document it follows (#233), and for the same
    reason belongs to the run: one shared reader, not one per document.
    A derived field (#216) is read off the document before anything else runs,
    so every check below sees one field whether it was computed or written —
    with one exception, taken first: writing a derived field down is itself
    the finding.
    """

def _vocabulary_violations(contract: Contract, field: Field, rel: str, raw, meta: dict | None) -> list[str]
    """
    A vocabulary field against its declaration: the shape, the presence,
    and every value against the closed set — naming the file, since that is
    where a missing value gets added.
    """

```

## luria/derive.py
```python
class Follow
    """
    Which referenced document a derivation reads: `source[0]`, `paper`.
    `index` is None for a scalar reference and an integer for one element of
    a plural one. There is no "every element" spelling: a field holds one
    value, so collecting across a list would need somewhere to put the
    others.
    """

    def __str__(self) -> str

    def code(self, meta: dict) -> str | None
        """The code this document points at, or None when it points nowhere."""


class Derived
    """
    One derivation: `field` is what it defines, `template` how, and
    `follow` which document — None for this one (#216), a reference to
    render against for another (#233).
    """

    @property
    def spec(self) -> str
        """The declaration as written, for messages that name it."""

    @property
    def sources(self) -> tuple[[str, Ellipsis]]
        """The frontmatter fields this template reads, for the eager check."""


def names_in(template: str) -> tuple[[str, Ellipsis]]
    """
    The field names a template reads, without the indexing or the format
    spec — `"LIT-{authors[0]}-{published:.4}"` names `authors` and
    `published`. What the eager check needs in order to say whether a scheme
    can hold them.
    """

def lone_field(template: str) -> bool
    """
    Whether the template is exactly one replacement field and nothing else.
    That is the case where the value survives as itself rather than as its
    rendering, which is what keeps a derived field comparable to the
    vocabulary it is checked against.
    """

def render(template: str, values: dict)
    """
    A template against one document's values, or None when it cannot fill.
    None rather than a partial rendering: a half-filled spelling would
    resolve for some documents and not others, with nothing saying which.
    """

def parse_follow(where: str, raw) -> Follow
    """
    A `from = "source[0]"` declaration, or a ValueError naming the fault.
    Shape only. Whether the name is a reference the scheme declares, and
    whether it holds one value or several, needs the whole scheme.
    """

def parse(where: str, field: str, raw, follow) -> Derived
    """
    One `derive = "{template}"` declaration, or a ValueError naming what
    was wrong with it. Shape only — whether the names are fields the scheme
    can hold needs the whole scheme, so that is checked there.
    `follow` is the parsed `from`, when the template renders against a
    referenced document rather than this one (#233).
    """

class _Probe(dict)
    """
    Answers to any name, so a template's shape can be checked without a
    document — indexing and attributes included, since `{authors[0]}` and
    `{date.year}` are ordinary spellings.
    """

    def __missing__(self, key)

    def __getitem__(self, key)

    def __getattr__(self, name)

    def __format__(self, spec)


def value(meta: dict, rule: Derived, resolve)
    """
    The derived value for one document, or None when the template cannot
    be filled.
    Absence is not an error here. A document with no `tags:` has no primary
    topic to compute, and saying so is the tags field's job — reporting it
    twice would name the wrong line as the fix. The same holds across a
    reference: pointing at nothing, at a code that resolves to nothing, or at
    a document that does not carry the field all derive nothing, because each
    already has a check whose finding names the right line.
    Without `from`, only the document's own frontmatter is in scope, and that
    is enough for `{number}` too, now that identity is a field a document
    carries rather than a filename it is parsed out of (ADR-087) — a
    capability this step inherits rather than adds.
    With `from`, `resolve` maps a code to that document's *written*
    frontmatter. A caller that cannot resolve (none was supplied) derives
    nothing rather than guessing.
    """

def written(meta: dict, rules) -> list[str]
    """
    The derived fields this document wrote for itself — the finding, since
    a derived field has one source and frontmatter is not it.
    """

def applied(meta: dict, rules, resolve) -> dict
    """
    `meta` with every derivation resolved onto it.
    A copy: the caller's dict is what the document says, and several checks
    still need to tell the two apart.
    `resolve` is what a `from` derivation reads the other document through;
    every rule sees the document's *written* frontmatter, never a partially
    derived one, so the order rules are applied in cannot matter.
    """

```

## luria/directives.py
```python
def _split_expiry(args: tuple[[str, Ellipsis]]) -> tuple[[tuple[[str, Ellipsis]], 'dt.date | None', str | None]]
    """
    Pull `until <YYYY-MM-DD>` out of a directive's arguments.
    An expiry is a modifier on the directive, not one of the things it names,
    so it leaves the argument list — otherwise every consumer that validates
    arguments would report `until` as an unknown one.
    An ISO date and nothing else. A duration ("two weeks") would need an anchor
    the file does not carry, and `2026-10-01` is the anchor written down.
    """

class Directive

    def covers(self, line: int) -> bool

    def expired(self, as_of: Any) -> bool
        """
        `until 2026-10-01` is good ON the 1st — a date somebody wrote as the
        last day they meant it to hold, not the first day it stops.
        """


def _fence_line_spans(text: str) -> list[tuple[[int, int]]]
    """1-based (first, last) line numbers of each fenced code block."""

def _docstring_line_spans(text: str) -> list[tuple[[int, int]]]
    """
    1-based (first, last) line numbers of each docstring in a Python source.
    Module, class and function docstrings only — a string used as a value is
    not one, and annotating it is not what anyone means. Unparseable source
    yields nothing rather than raising: a directive scope is not the place to
    discover a syntax error.
    """

def forget_scans() -> None
    """Drop the scan caches — for tests that count how often a scan runs."""

def blocks(text: str, path: Path | None) -> list[tuple[[int, int]]]
    """Blank-line-delimited runs of lines, 1-based inclusive — see `_blocks`."""

def comment_fragments(path: Path, text: str) -> list[tuple[[int, int, str]]]
    """Every real comment in `path` — see `_comment_fragments`."""

def _blocks(text: str, path: Path | None) -> list[tuple[[int, int]]]
    """
    Blank-line-delimited runs of lines, 1-based inclusive.
    A fenced block is atomic — a blank line inside a code sample doesn't end
    the paragraph — and so is a **Python docstring**, for the same reason and
    on the same principle (#222). A docstring is one syntactic unit however
    many paragraphs it holds, so a `-block` directive written above a
    definition governs the whole of what that definition says, not just its
    first paragraph. Without it the only annotation that reaches a citation in
    a docstring's third paragraph is `-file`, which is far too blunt for the
    case: an ordinary sentence of prose that happens to name a code.
    """

def _comment_fragments(path: Path, text: str) -> list[tuple[[int, int, str]]]
    """(line, char offset, comment body) for every real comment in `path`."""

def _with_inner_markers(fragments: list[tuple[[int, int, str]]]) -> list[tuple[[int, int, str]]]
    """
    Each comment, plus what follows any further marker on its first line.
    A grammar reads `// note  // dir: x` as one comment, which is true, and
    would leave the appended directive un-opened and so unread. The marker
    scan splits there and the split is a spelling people use, so a grammar's
    precision is applied to *finding* comments and not to re-litigating what
    counts as the start of one. Only the first line: in a block comment a
    marker further down is at a line this fragment cannot name.
    """

def _frontmatter_comments(text: str) -> list[tuple[[int, int, str]]]
    """
    YAML comments in a markdown file's frontmatter, as comment fragments.
    A reference field is a citation site — `superseded_by:` naming a retired
    document is reported at its line like any sentence would be — but the
    only comment the markdown scan read was an HTML one, and frontmatter
    is YAML. The directive that could answer the finding in place had no
    place to stand, and the file-scoped one was the only spelling left. The
    frontmatter has its own comment syntax; this reads it, so a line-scoped
    directive works there the way it does in a `.py` file:
        # inactive-ok: ADR-012 — the successor was itself later retired
        superseded_by: ADR-012
    """

def _line_offsets(text: str) -> list[int]

def find(path: Path, text: str, names: set[str] | None, as_of: Any | None) -> list[Directive]
    """
    Every LIVE directive in `path`, with the lines each one governs resolved.
    An expired one (`until <date>`, #58) is simply absent: the linter behaves
    as if it were never written, which is what an expiry is for. Dropping it
    here rather than at each consumer is what makes that uniform — `find` is
    the one place directives are read, so nothing downstream has to know the
    feature exists. `find_expired` is how they stay reportable.
    """

def _parse(path: Path, text: str, names: set[str] | None) -> list[Directive]
    """Every directive in `path`, expired or not — one parser, two views."""

def find_expired(path: Path, text: str, names: set[str] | None, as_of: Any | None) -> list[Directive]
    """
    The directives `find` dropped because their date has passed.
    Inert is not the same as invisible. A check that starts failing again with
    no word about the acknowledgement sitting right above it is a puzzle rather
    than a report, so the expiry is worth naming where the failure appears.
    """

def _governed(scope: str, line: int, spans: list[tuple[[int, int]]], path: Path, text: str) -> frozenset[int]

def _entry_below(text: str, line: int) -> set[int]
    """
    The lines "the next line" means: one, in prose — but in frontmatter a
    field is an entry, and a `superseded_by:` written as a list carries its
    code on the line after its key. A comment above the key that reached
    only the key would excuse nothing, and `luria repair` writes exactly
    that list shape. So inside the frontmatter the line below extends over
    the entry's continuation lines: indented ones, and `- ` items.
    """

def _directive_only(text: str, span: tuple[[int, int]], path: Path) -> bool
    """
    True when a block is nothing but directives — which is what makes it an
    introduction to the block below rather than a block of its own.
    """

def shaped_spans(text: str, names: set[str]) -> list[tuple[[int, int]]]
    """Char spans of every directive-shaped run naming one of `names`."""

def problems(directive: Directive, valid_args: set[str] | None) -> str | None
    """A directive that can't do anything is worth saying so about."""

def in_fence(line: int) -> bool

```

## luria/doc_refs.py
```python
def remote_issue_re() -> Any | None

class Ref

    def describe(self) -> str


def _frontmatter_span(text: str) -> tuple[[int, int]] | None

def prose_spans(text: str) -> list[tuple[[int, int]]]
    """Every prose value in the frontmatter, in document order."""

def in_prose(spans: list[tuple[[int, int]]], pos: int) -> bool

def _fence_spans(text: str) -> list[tuple[[int, int]]]
    """Spans covered by fenced code blocks, including their fence lines."""

def _code_span_spans(text: str) -> list[tuple[[int, int]]]
    """
    Inline code spans, paired *within a paragraph*.
    Pairing backticks across the whole document is what a first pass did, and it
    is wrong: one unbalanced backtick — inside a fenced block, or a stray one in
    7,000 lines of devlog — inverts which side of every later backtick is code,
    and `` `#123` `` gets linked inside its own code span. Fenced blocks are cut
    out first (they are masked separately anyway) and each remaining paragraph
    pairs independently, so a desync can't outlive one paragraph. A code span
    can't contain a blank line, so nothing legitimate is lost.
    """

def html_block_spans(text: str) -> list[tuple[[int, int]]]
    """
    Character spans of raw-HTML blocks — a block-tag line through the next
    blank line. Code fences win, so a fenced `<div>` isn't one.
    """

def code_spans(text: str) -> list[tuple[[int, int]]]
    """
    Fenced blocks and inline code spans — where markdown shows an example
    rather than states one. Callers that need to read HTML comments (which
    `masked` hides) mask with this instead.
    """

def in_html_block(pos: int, spans: list[tuple[[int, int]]]) -> bool

def unlinted(path: Path, text: str) -> bool
    """
    True when `path` opts out of reference checking wholesale:
        <!-- unlinted-file: — why this page is exempt -->
    Covers the bare-reference lint, wikilink handling and the
    reference-status scan. Everything else — frontmatter, titles, journal
    checks — still applies; this exempts the *references*, not the document.
    """

def link_base(path: Path) -> Path
    """Back-compat shim: the rule lives on the config (`Config.link_base`)."""

def unexempt_spans(text: str, path: Path) -> list[tuple[[int, int]]]
    """
    Character spans an `unexempt:` directive puts back under the linter.
    Code is exempt because code is quoted, not asserted — but a snippet in the
    docs can be quasi-prose, citing decisions the reader should be able to
    follow. `<!-- unexempt: codeblock -->` above a fence says so for that block.
    The caveat is inherent, not a bug: markdown inside a fence renders
    literally, so the link the linter then demands shows as `[ADR-157](…)` in
    the sample. That is the trade the directive exists to let an author make.
    """

def directive_problems(path: Path, text: str) -> list[str]
    """Directives that silently do nothing — worse than no directive."""

def masked(text: str, path: Path) -> list[bool]
    """One flag per character: True where a reference must be ignored."""

def find_refs(text: str, path: Path) -> list[Ref]
    """All unlinked references in `text`, in source order."""

def _line_index(text: str)

class Wikilink

def wikilink_target(inner: str, source: Path) -> str | None
    """
    What `[[inner]]` links to, cited from `source`. Tries, in order: a
    foreign code in any registered shape (ADR-016, ADR-024), a local scheme
    code, and an issue number. The brackets are the cue, so the low-`#N`
    ambiguity rule never applies here.
    """

def wikilinks(text: str, source: Path) -> list[Wikilink]
    """
    Every `[[…]]` in prose, resolved where possible. Quoted regions are
    specimens, comments are instructions, and frontmatter is data — except
    the summary, which is prose here as everywhere (ADR-005).
    """

def expand_wikilinks(text: str, source: Path) -> tuple[[str, int]]
    """
    Rewrite every resolvable wikilink as a markdown link (an `<a href>`
    inside a raw-HTML block, where markdown wouldn't render). Unresolvable
    ones are left in place for the lint to name.
    """

def adr_paths() -> dict[[int, Path]]
    """
    The ADR scheme's documents — {} when the project has no ADR scheme,
    which is a legal record shape now that a declared `schemes` family
    replaces the defaults (ADR-047). Kept as a named helper because the two
    entry points precompute it for the common case.
    """

def dp_anchors() -> dict[[int, str]]
    """
    Principle number → the anchor a link to it should use.
    An explicit `<a name="dp-13"></a>` wins over the heading's own slug, because
    a principle is a living document: reword one and every heading-derived link
    to it stops resolving, silently. The generator emits explicit anchors
    (ADR-012), but a project whose principles are still one hand-written file
    has only headings, and those still work.
    """

def _anchor_number(scheme, anchor: str) -> int | None
    """
    Which of `scheme`'s documents an anchor in its assembled view names.
    The inverse of the two spellings the anchor can have: the constructed
    `prefix-N`, and — for the principles document — whatever `dp_anchors`
    discovered there, which may be a heading slug from a project that writes
    its principles by hand.
    """

def retarget_view_citations(text: str, source: Path) -> tuple[[str, int]]
    """
    Rewrite links that point INTO a document-rendered scheme's assembled
    view at the cited document's own page, for a scheme whose `cite` is
    "page". Returns the new text and how many links moved.
    Flipping `cite` changes what a citation resolves to, which is enough for
    every reference written from then on. It is not enough for the record you
    already have: those citations are plain markdown links, and the linkifier
    spells BARE references — it has no reason to look at a link that is
    already written. On this project that was 330 links across 81 pages, so a
    switch that only governed future links would have fixed nothing a reader
    could see.
    Deliberately narrow. The link TEXT is untouched, because it is the
    author's sentence rather than a field. A link with no fragment is left
    alone: pointing at the whole assembled document is a real thing to do. An
    anchor that names no document is left alone too — rewriting it would swap
    a dead fragment for a dead FILE, which is worse and hides it from the
    lint.
    """

def _relative(target: Path, base: Path) -> str

def is_ambiguous_issue(ref: Ref, text: str, anchors: dict[[int, str]]) -> bool
    """
    A `#N` small enough to be a principle number (or an ADR's third open
    question, or story 2) and with no cue saying otherwise. Left alone — a
    confidently wrong link is worse than a number the reader has to look up.
    """

def legacy_spellings() -> list[str]
    """
    Every citation still written in a concretized code's old spelling —
    `path:line CODE → CODE-NOW` — across the docs and the configured code
    globs (ADR-040's rung-1 warning class, `legacy-spellings`).
    Raw text on purpose, where the reference scanner masks: a legacy
    spelling inside an existing link's *label* is exactly the case the
    rewrite missed, and one in a code span is a quotation that the
    concretizer's own sweep would have modernized had it been in-tree at the
    time. Alias-gating is the precision: a temp-shaped string that resolves
    to no document is not a legacy spelling, it is either a live temp code
    (the branch's normal state) or prose noise, and neither belongs here.
    The in-tree steady state is an empty list — the sweep is full — so a
    row here means an in-flight branch merged after a concretization pass,
    and `luria link --fix` upgrades it.
    """

def alias_number(scheme, tail: str) -> int | None
    """
    The number a document answers to under another spelling — a temporary
    code it used to be (ADR-049), a `formerly:` entry from a migration, or a
    spelling its scheme renders from frontmatter (#219).
    Read from `aliases.alias_map`, which caches per config. It used to scan
    every document on demand, and the docstring's reason was sound while the
    only aliases were temporary codes nobody writes on purpose: the path was
    rare. A spelling people *choose* to cite is not rare, so the scan became
    the wrong shape the moment derived aliases existed.
    """

def _temp_target(scheme, tail: str, source: Path, base: Path) -> str | None
    """
    Where a temporary code points, cited from `source` (ADR-049).
    A live temporary document wins: file link for an index scheme, a
    tail-keyed anchor in the assembled page for a document scheme. A tail
    with no live document may be a `formerly:` alias of a concretized
    document, which then resolves exactly as its number would — so a temp
    code cited somewhere the concretizer's rewrite cannot reach (a PR
    thread, a commit message, another repository, a branch cut before
    concretization) never goes dead, only stale in spelling. In-tree the
    sweep is full, history included (ADR-040), so an alias hit from a local
    file usually means an in-flight branch awaiting its next `--fix`.
    """

def resolve(ref: Ref, source: Path, adrs: dict[[int, Path]], anchors: dict[[int, str]], text: str | None) -> str | None
    """
    The link target for `ref` as cited from `source`, or None when the
    reference can't be resolved (an ADR number with no file), would be a
    self-link (an ADR citing itself, a principle citing itself), or is an
    ambiguous low `#N` (needs `text` to judge).
    """

def _absorb_brackets(text: str, ref: Ref) -> tuple[[int, int]]
    """
    `[ADR-919]` — a shortcut reference link with no definition, so it renders
    as literal brackets. Swallow them rather than nesting a link inside, which
    would render as `[ADR-919]` with the text linked.
    """

def _frontmatter_survives(old: str, new: str) -> bool
    """
    True when rewriting the summary only *added links* — the YAML still
    parses, every other key is untouched, and stripping the new links yields the
    original summary back.
    A prose value can be a quoted scalar, a folded block, or a plain multi-line
    scalar, and only the last of those has characters a link could disturb.
    Rather than enumerate which styles are safe, the rewrite is checked. The
    check lives here, not in the fixer, because the linter calls it too: a
    reference the fixer would decline to write must not be one the linter
    demands.
    """

def rewritable_refs(text: str, source: Path, adrs: dict[[int, Path]], anchors: dict[[int, str]]) -> list[Ref]
    """
    The references `linkify` will actually turn into links — what the linter
    reports, so the two can never disagree.
    """

def linkify(text: str, source: Path, adrs: dict[[int, Path]] | None, anchors: dict[[int, str]] | None) -> tuple[[str, int]]
    """
    Rewrite every resolvable bare reference in `text` as a link.
    Returns the new text and the number of rewrites.
    """

def _label(ref: Ref) -> str
    """
    What the written link says. The matched text, with one exception: a
    spelling the document *used* to have is a legacy spelling, and the fixer
    upgrades it to the canonical code (ADR-040) rather than engraving the old
    name into a fresh link.
    A **derived** alias is the opposite case and keeps its text (#219). It is
    not a stale spelling but a current one, rendered from the document's own
    frontmatter, and recovering an identifier a reader can interpret is the
    whole point of having it — canonicalizing it here would erase that on the
    first `luria link --fix`, silently, which is the failure this branch
    exists to avoid.
    """

def _apply(text: str, refs: list[Ref], source: Path, adrs: dict[[int, Path]], anchors: dict[[int, str]]) -> str

def doc_files() -> list[Path]
    """
    Every file the reference rules apply to.
    `*.stub` counts. A stub is the one hand-written part of a generated view,
    and its prose lands in a page the lint then skips *because* it is
    generated — so a bare reference written there was invisible to both checks
    at once. `link_base` already knows where a stub renders (ADR-016).
    """

def fenced(pos: int) -> bool

def cover(start: int, end: int) -> None

def take(kind: str, num: int, start: int, end: int, prefix: str) -> bool

def line_of(pos: int) -> int

```

## luria/edges.py
```python
class Edge

def _lands(field, code: str) -> bool
    """
    Whether a code is a node this graph has: a local document of the
    declared scheme, or of any scheme for a built-in reference. A remote
    code is a citation the remote machinery verifies, never an edge.
    """

def outbound(doc: Adr) -> list[Edge]
    """Every typed edge this document is the source of."""

class Graph

    def outbound(self, code: str) -> list[Edge]

    def inbound(self, code: str) -> list[Edge]
        """The backlinks: every typed edge that lands on `code`."""


def graph() -> Graph
    """Every typed edge in the record, read once."""

def code_of(path: Path) -> str | None
    """Which node a scheme document's file is, or None for anything else."""

```

## luria/field_edit.py
```python
def add_to_field(text: str, name: str, code: str) -> str
    """
    Add one code to a list-valued frontmatter field, creating the field
    when it is absent and widening a scalar rather than replacing it.
    A `many` field accepts one code written as a scalar (a list of one), so
    the scalar case is real and overwriting it would silently delete a
    relation — the quiet kind of loss this module exists to end.
    """

def drop_from_field(text: str, name: str, code: str) -> str
    """
    Take one code out of a list-valued frontmatter field, removing the
    field itself when that was its last entry.
    A field left standing with nothing under it is not a relation held by
    nobody — it is invalid frontmatter, and the next reader gets a parse
    error instead of the tidy record the deletion was meant to leave.
    """

```

## luria/frontmatter_shape.py
```python
def frontmatter_raw(text: str) -> str | None
    """
    The YAML block between the opening and closing `---` fences, or None
    when the document has no well-formed frontmatter. Kept as raw text so a
    check can see what PyYAML silently rewrites.
    """

def check(errors: list[str], rel: str, text: str) -> None
    """Reject HTML comments and duplicate mapping keys in YAML frontmatter."""

```

## luria/init.py
```python
def _template_dir() -> Path
    """
    The scaffold's location, which depends on how Luria arrived.
    Installed from a wheel, the template ships inside the package
    (`luria/template/`, ADR-027); in a checkout it sits at the repository
    top level, where a visitor browses it (ADR-021). Packaged wins when both
    exist, because an installed Luria should scaffold what it shipped.
    """

def _origin_url(into: Path) -> str
    """
    The `origin` remote, or "" — for any reason at all.
    Not being in a repository is the ordinary case for `luria init`, and so is
    having no origin yet. Neither is a problem worth a message, let alone a
    failure: the key this feeds is optional.
    """

def infer_issue_url(into: Path) -> str
    """
    `https://github.com/owner/repo/issues/{n}` from the origin remote.
    Empty when there is no remote, or when its host is not one whose issue
    path this knows. Guessing at an unknown forge would put a broken link on
    every entry that names an issue, which is a worse default than the empty
    string it replaces.
    """

def _slug(prefix: str) -> str
    """
    `RFC` → `rfcs`, the directory name a prefix implies.
    Mechanical on purpose. The shipped schemes are named for what they hold
    (`decisions.d`, `principles.d`) rather than for their codes, and a project
    that wants that can edit one line — but guessing at it here would mean
    guessing at what an RFC *is*, which this package has no opinion about.
    """

def _spec(item: str, kinds: tuple, default: str, what: str) -> tuple
    """
    `NAME` or `NAME:kind`, validated at the point of typing.
    Eagerly, and with the vocabulary in the message: a scaffold is run once,
    usually by somebody meeting these words for the first time, so a silent
    fallback would be discovered much later and by reading generated output.
    `default` is passed rather than taken as the first of `kinds`, which is
    the shape this had until a test caught it defaulting a journal to `year`.
    The listing order is for the error message and the default is a fact about
    the dataclass; tying them together made the second follow the first.
    """

def _scheme_entry(prefix: str, render: str) -> tuple[[dict, str]]
    """One scheme's table and the comment that introduces it."""

def _journal_entry(name: str, granularity: str) -> tuple[[dict, str]]
    """One journal's table and the comment that introduces it."""

def shorthand_tables(text: str, schemes: str, journals: str) -> str
    """
    The template's config, plus one table per shorthand entry.
    Additive by design. The template already declares ADR and DP, so adding
    a third scheme keeps all three — which is what "mostly the defaults" has
    to mean, given that a declared family replaces the shipped one whole
    (ADR-047). Removing a default is deleting its table, which is an edit to
    a file the user can now see.
    Added to the document rather than to the end of the text: YAML nests by
    indentation, so an indented block appended to a file joins whichever
    top-level key happens to be last — silently, and wrongly. The round trip
    is ruamel's, so the template's comments survive it (ADR-098).
    """

def _read(rel: str) -> str

def _toml_text(into: Path, config_arg: str | None, issue_url: str, schemes: str, journals: str) -> str
    """The config the scaffold is planned from, resolved in priority order."""

def template_config(into: Path, issue_url: str, schemes: str, journals: str) -> str
    """
    The shipped template's config, with the issue URL filled in and the
    shorthand expanded.
    Shared by `luria init` and `luria config`, which differ only in what they
    do with the result — scaffold from it, or hand it over to be edited.
    """

def _scheme_files(scheme: Scheme) -> dict[[Path, str]]
    """
    What one scheme's directory starts with.
    ADR and a document-rendered DP get the shipped rich content — the
    decision doctrine and the seed principles are what this package has to
    say, and they are prefix-specific on purpose. Everything else gets the
    neutral shapes above, titled after itself.
    """

def _statuses_yaml(scheme) -> str
    """
    The scheme's vocabulary as a file it owns.
    Written from `statuses.DEFAULT_STATUSES` so the scaffold and the fallback
    cannot drift into two lists — the duplicated projection DP-3 names.
    """

def _views(cfg: Config) -> str
    """
    The docs index's bullet list — one line per view this record renders,
    derived from the config so the list and the record cannot disagree about
    what exists (the docs-index lint would catch it, but a scaffold that
    starts red teaches the wrong first lesson).
    """

def plan(into: Path, config_arg: str | None, issue_url: str, schemes: str, journals: str) -> list[tuple[[Path, str]]]
    """(destination, content) for everything the scaffold would write."""

def write(into: Path, issue_url: str, dry_run: bool, config: str | None, schemes: str, journals: str) -> tuple[[int, int, list[Path]]]

def config_run(into: str, issue_url: str, schemes: str, journals: str, stdout: bool) -> None
    """
    Write a starting `luria.yaml` from the shorthand, and stop there.
    The same file `luria init` would have written, without the scaffold. It
    exists because the shorthand covers the two things projects usually vary
    and nothing else: a project that also wants a different directory, a
    narrowed status vocabulary or a tag group has to edit the config, and
    doing that *after* a scaffold means moving directories the first run
    already created.
        luria config --schemes "RFC,SPEC:document"   # write it
        $EDITOR luria.yaml                           # change what you like
        luria init                                   # scaffold that shape
    Refuses to overwrite, like everything else here. `--stdout` prints instead
    of writing, for a look before committing to one.
    """

def run(into: str, issue_url: str, dry_run: bool, config: str, schemes: str, journals: str) -> None
    """
    Scaffold the record a config declares (default: the detected root's
    own config, or the shipped template's). Never overwrites; --config PATH
    installs that file as luria.yaml and scaffolds its shape; --dry-run lists
    what would be written; --issue-url makes issue numbers linkable.
    --schemes and --journals extend the shipped template for a project that
    wants the defaults plus a little: `--schemes "RFC,SPEC:document"`,
    `--journals "incidents:day"`. Each entry becomes an ordinary commented
    table in the luria.yaml this writes, so the shorthand is something you
    type once rather than a format anything reads back.
    """

```

## luria/invariants.py
```python
class Unbound
    """One finding: the documents, and what each holds in the field."""

    @property
    def codes(self) -> tuple[[str, Ellipsis]]


def held(doc: Adr, field: str) -> set[str]
    """
    The values a document holds in `field`, as a set.
    A scalar is a set of one, which is what lets equality and intersection be
    the same test — `status: Active` on both sides intersects to `{"Active"}`
    exactly when the two are equal.
    """

def _neighbours(chain: Chain) -> dict[[str, set[str]]]
    """
    Every undirected edge the chain walks — spine and cross-link alike.
    Read through `relations.edges`, which unions a relation with its declared
    converse, so a one-sided declaration is walked before the fixer has
    written the other half. A finding that waited for `luria link --fix` would
    be a finding about tidiness rather than about the record.
    """

def _walk(chain: Chain) -> tuple[[dict[[str, Adr]], dict[[str, set[str]]]]]

def edges(chain: Chain) -> list[Unbound]
    """Pairs in a declared relation that share no value in the field."""

def paths(chain: Chain) -> list[Unbound]
    """
    Components whose members hold no value in common.
    A one-member component is not a finding: a document alone in the graph
    asserts nothing about anything, so there is no invariance to express.
    """

def findings() -> tuple[[list[Unbound], list[Unbound]]]
    """
    Every chain that declares an invariant, as (edges, paths).
    Chains without one contribute nothing, silently — the check is opt-in
    because most relations assert no shared field, and a record that has not
    said which one it means should read the same as a record with no
    relations at all.
    """

```

## luria/journal.py
```python
def parse_created(raw) -> Any | None
    """
    `created:` as a datetime. YAML may hand back a date, a datetime or a
    string depending on quoting, so all three are accepted rather than making
    the author remember which one the parser prefers.
    """

def path_for(journal: Journal, created: Any) -> Path

def created_from_path(path: Path) -> Any | None

class Entry

    @property
    def anchor(self) -> str
        """
        Keyed to the timestamp, not the title — a title can be corrected,
        and a heading-derived anchor would break every link to it silently.
        """


def read(path: Path) -> Entry | None

def entries(journal: Journal) -> list[Entry]
    """
    Every filed entry, oldest first. Sorted by the timestamp, so the order
    is a property of the record rather than of how the branches landed.
    """

def populate_created(journal: Journal) -> list[Path]
    """
    Write a missing `created:` into entries whose path already says it (#33).
    The path is derived from `created:` (ADR-020), so when the field is empty
    the path is the one witness left — populating from it writes down what the
    tree already asserts rather than inventing anything. An entry whose field
    and path *disagree* is left alone: two witnesses in conflict is a
    judgement for a human, not a mechanical fix.
    Runs from `luria repair`, which the generation job commits onto the
    branch that filed the entry (ADR-068).
    """

def book_key(journal: Journal, created: Any) -> str

def books(journal: Journal) -> dict[[str, list[Entry]]]

def _sections(journal: Journal, filed: list[Entry]) -> list[str]
    """
    Each entry's section of a book, in order, without the contents list.
    Split out because the contents list has to link headings that this text
    defines — and a heading's anchor depends on every heading before it, the
    entry bodies' own included (ADR-100).
    """

def entry_anchors(journal: Journal, filed: list[Entry]) -> dict[[str, str]]
    """
    `{entry.anchor: the heading's slug}` for one book.
    The slug, not the id: a reader copies the link the *page* offers — the
    one on the heading — and a contents list pointing somewhere else is two
    addresses for one entry, which is what sent somebody looking for a bug
    that was not there. Both resolve; only one is what the page shows.
    Computed over the whole book in document order, because that is what a
    slug depends on. Which is also why this is here rather than in the
    caller: the answer needs the entry bodies, not just the titles.
    """

def _heading_text(journal: Journal, filed: list[Entry]) -> str
    """The book's own headings, before the first entry."""

def render_book(journal: Journal, key: str, filed: list[Entry]) -> str

def render_index(journal: Journal, grouped: dict[[str, list[Entry]]]) -> str
    """
    The journal's front page: the current book's contents inline, then the
    shelf. Hot on top, cold below — without this, the newest writing sits
    behind two clicks and the whole journal reads as an archive (ADR-021).
    """

def outputs_for(journal: Journal) -> dict[[Path, str]]
    """
    One journal's books plus its index — the unit the parallel renderer
    runs (ADR-026). A configured-but-unused journal renders nothing: the
    default config names one, so emitting an empty index would put a
    `docs/devlog/` into every project that never files an entry.
    """

def outputs() -> dict[[Path, str]]
    """
    Every book, plus each journal's index. One place, so the staleness
    check covers a journal the moment it is configured.
    """

def new(journal: Journal, title: str, now: Any) -> Path
    """
    Create an entry, stepping a second forward on collision.
    Not a probability argument — the filesystem already knows. A same-second
    collision is possible when a tool files several at once, and "unlikely" is
    a worse guarantee than "checked" when checking is a `path.exists()`.
    """

def run(journal: str) -> None
    """
    What is filed, and which books it renders to (a status listing —
    `luria new` files entries).
    """

```

## luria/link_refs.py
```python
def linkify_files(paths: list[Path], fix: bool) -> tuple[[int, list[Path]]]
    """
    Count the references PATHS would gain as links; --fix writes them.
    Returns the count and the files written (none without --fix).
    """

def fix_anchors(fix: bool) -> int
    """
    Rewrite every `<a name=>` something links to into an `<a id=>`.
    Whole-record rather than per-path, because it edits the file holding the
    ANCHOR: the link is spelled correctly and the thing it names cannot be
    found, so narrowing to the paths on the command line would repair the
    half of a pair the defect is not in (ADR-099).
    Which file that is cannot be read off the link's target. A stub is the
    authored part of a generated page, so a `<a name=>` written in one is
    reported against the VIEW it renders into — and the view is not the
    thing to edit, since the next build overwrites it. So this repairs every
    authored document carrying a reported fragment. Loose, and safe to be:
    `repair` only touches anchors some link actually named, and turning
    `name` into `id` is an improvement in any file it lands in.
    Returns the number of files changed — or that would change.
    """

def run() -> None
    """
    Rewrite bare references as links and complete declared relations —
    every doc, or just PATHS. Reports what would change; --fix writes it.
    --links-only skips the relation completion.
    Completion is whole-record: it reads every document of a scheme to know
    what is missing, so PATHS narrows the linking only.
    """

```

## luria/link_targets.py
```python
def _local_path(target: str) -> str | None
    """
    The on-disk path a link target names, or None when it names something
    else. The fragment and query are dropped: a heading that does not exist is
    a different (and much noisier) check than a file that does not.
    """

def broken(files: list[Path] | None) -> tuple[[list[str], list[str]]]
    """
    Relative link targets that resolve to nothing, and the `target-ok:`
    directives that no longer acknowledge anything.
    Deliberate cases exist — a link into a build output that is generated but
    not committed, a path a downstream consumer creates — so each one is either
    acknowledged or reported, never silent and never an error (ADR-035).
    """

```

## luria/lint.py
```python
def check_docs_index(errors: list[str]) -> None

def check_frontmatter(errors: list[str]) -> None

def check_form_text(errors: list[str]) -> None
    """
    A prose field still saying what the scheme's `_template.md` says is
    the form's text, not the document's — a summary that reads "one-paragraph
    description of the decision" in the index. Write it, or drop the key.
    """

def check_title(errors: list[str], rel: str, meta: dict, body: str) -> None
    """
    `title:` is the source of truth, and the body's H1 repeats it.
    Two copies of one string is the drifting projection DP-3 names, and the
    filename no longer carries a third (ADR-013). The H1 can't simply be
    dropped — someone reading the file on its own needs a heading — so this is
    rung 2: keep the copy, guard the property that they agree.
    """

def check_status_vocabulary(errors: list[str]) -> None
    """
    A `statuses.yaml` key outside ADR-003's five words.
    Narrowing the vocabulary per scheme is the point; extending it is not, and
    a file naming `Accepted` would render a legend and silence nothing — it
    would look like it was working, which is the worst way for a config file to
    be wrong.
    """

def check_reserved_prefix(errors: list[str]) -> None
    """
    A scheme declared in the reserved fixture namespace (ADR-093).
    Always wrong and always mechanically fixable, which is why it is an error
    and not a report: the namespace exists so that a project's test suite can
    spell codes nobody claims, and a project that claims one has quietly taken
    that guarantee away from itself — its own fixture codes start resolving,
    and the failure looks exactly like success until a real document lands on
    the number.
    The check reads the config, not the record, so it fires at declaration
    time, before the first document makes the prefix expensive to change.
    """

def check_contracts(errors: list[str]) -> None
    """
    Each scheme's contract, enforced — what it `requires`, what its
    `references` hold, which of its grouped values combine (ADR-040, ADR-060,
    ADR-054). Compiled once per scheme and checked in one pass over its
    documents (#141), where there used to be one pass per table.
    Opt-in, all of it: a scheme declaring none of the three compiles to an
    empty contract and this is silent for it, which is every record that
    predates the tables. A breach is a hard error, not a status class — a
    malformed entry is a defect in the document, and declaring the table
    was the opt-in (ADR-054).
    """

def check_numbers(errors: list[str]) -> None
    """
    A document's `number:` and its filename have to agree (#219).
    The same check `check_journals` makes about `created:` and an entry's
    path, for the same reason: identity lives in the frontmatter, the name on
    disk is a projection of it, and a projection that disagrees with its
    source means every reader picks a different one. Here the stakes are
    concrete — `documents()` reads the field, while a link target is written
    from the code, so a disagreement resolves references to a filename that
    is not there.
    A violation rather than a report, and not repaired automatically: which
    of the two is right is a question only the author can answer, and
    renaming on a guess would move a document's identity. An *absent* `number:`
    is the repairable case, and `luria repair` handles it from the path.
    """

def check_alias_collisions(errors: list[str]) -> None
    """
    Two documents rendering one alias (#219).
    A violation rather than a report, because a spelling that resolves to two
    documents makes every citation through it ambiguous — worse than a stale
    reference, which at least points somewhere definite.
    Not auto-disambiguated. An automatic suffix is order-dependent and would
    silently renumber when a third document arrives; the fix is the template,
    and including `{number}` in it makes collisions impossible by
    construction, since the number is what `luria concretize` guarantees
    unique.
    """

def check_journals(errors: list[str]) -> None
    """
    A journal entry's path is derived from its `created:` timestamp, and the
    two have to agree — otherwise the ordering the whole scheme rests on says
    one thing and the frontmatter says another (ADR-020). Also: an entry needs
    a title, because the title is what the book's contents list shows.
    """

def check_version_history(errors: list[str]) -> None
    """
    `version:` and `history:` have to agree.
    Correcting a document in place is only honest because the correction is
    visible ([ADR-019](../record/decisions.d/ADR-019.md)), and nothing was checking
    that the visible part exists. A bumped version with no history entry is a
    silent revision wearing a version number.
    """

def check_view_dirs(errors: list[str]) -> None
    """
    A view directory holds only generated files (ADR-021), so a
    hand-written file inside one is a violation — computed against what the
    generator would write, in memory, so the check reads sources and writes
    nothing.
    Staleness — a committed view that differs from the generator's output —
    is not checked here. It is a property of the default branch, where the
    views are committed, and `luria index --check` in the generation job
    answers it there (ADR-068); a branch carries the default branch's copies
    and has nothing to be stale against. For the same reason a file in a view
    directory that says it was generated is left alone: it is a view the
    generator no longer writes, which `luria index` deletes and `--check`
    reports, not something a person wrote.
    """

def workflow_temp_code_lines() -> list[str]
    """
    A temporary code (ADR-049) cited from a workflow file, one line per
    site. `luria concretize` rewrites the code with everything else when the
    decision is numbered, and the workflow's own token cannot push a change
    under `.github/workflows/` — so on that token the generation job's
    commit is refused whole. A job pushing with a token that has workflow
    write has no such problem, which is why this is a warning class and not
    a violation: the project says which token it runs on by naming
    `workflow-temp-codes` in `fail_on`, or not.
    """

def check_wikilinks(errors: list[str]) -> None
    """
    A wikilink is the author asserting "this is a reference" (ADR-025), so
    both failure modes are violations, with different remedies: a resolvable
    one just hasn't been fixed yet, and an unresolvable one is a request the
    machinery cannot honour — which must be said, not skipped (DP-1).
    """

def check_anchors(errors: list[str]) -> None
    """
    A fragment link that does not reach what it names.
    Two shapes. `<a name=>` alone is addressable in the repository and on
    GitHub, where a fragment is a real navigation, and not on the site the
    record publishes to, whose router scrolls with `getElementById` — so the
    link works everywhere a contributor checks and fails where readers use
    it (ADR-099). Nothing at all is the plainer case, and it became
    checkable only once luria owned a slugger of its own: a heading's anchor
    is the publisher's, and a check that guessed at it would report links
    that work (ADR-100).
    Read against the RENDER, not the committed tree — see
    `anchors.documents`.
    """

def cite_target_lines() -> list[str]
    """
    `cite = "page"` in a record whose pages are not published.
    The two halves of ADR-094 have to travel together. `cite = "page"` sends
    a citation of DP-003 to that principle's own page rather than to an
    anchor in the assembled view — which is right, and is the durable
    address, because a page's path does not move when somebody rewords a
    heading. It is also only an address if the page exists: a site that
    excludes the scheme's sources does the one thing it can and sends the
    reader to the repository. ADR-094 measured that when `publishable()`
    still withheld them — links redirected off-site went from 10 to 195.
    `publishable()` no longer withholds them by derivation, so this is now
    reachable only on purpose, through `site.exclude`. On purpose is exactly
    when it needs saying: the config asks for durable citations and the
    publishing rules withhold the thing they resolve to, and every citation
    silently becomes a link out of the site.
    A warning rather than an error. A record may publish nowhere, or publish
    a subset deliberately, and this cannot tell which — but it can say that
    the two settings disagree (ADR-035).
    """

def check_bare_refs(errors: list[str]) -> None
    """
    A reference the reader can't follow is a reference they have to grep for.
    Document codes, design principles and issue numbers are hyperlinks in prose
    — everywhere the same rules the fixer uses say they can be (ADR-005).
    """

def unlinked_site() -> list[str]
    """
    A record that publishes a site whose README never names it.
    `luria site` has always known where the record lands — `base_url` derives
    from `issue_url` — and nothing wrote it where a reader of the repository
    front page would look. An absence that reads exactly like a success is
    the case DP-15 exists for, and this is the signal.
    Satisfied by the URL appearing anywhere in the README, prose link
    included: the finding is "your front page does not point at the site you
    publish", not "you must use our marker".
    Scoped by `site.publish`, which defaults true: `base_url` derives
    for every GitHub project whether or not one is deployed, so a record that
    lives only in its repository says `publish = false` and the guard goes
    quiet — a guard opts out rather than being argued with (DP-10).
    """

def spent_upgrades() -> list[str]
    """
    Upgrades this record has already run.
    A one-shot upgrade is temporary by construction, and the thing that
    makes it *stay* temporary is being asked about. Once every record has
    run one it is dead code that still has to be read, tested and
    explained — so a record that no longer needs it says so, the way
    `stale-directives` reports a directive that no longer suppresses
    anything. One user's record saying it is not proof every record has,
    which is why the row says "once every record has" rather than "now".
    """

def status_sections() -> list[tuple[[str, str, list[str]]]]
    """
    Every status finding, as (class, headline, detail lines) — computed
    once, so the warning path and the `fail_on` path cannot disagree.
    """

def expired_directives(as_of: Any | None) -> list[str]
    """
    Acknowledgements whose `until <date>` has passed (#58).
    They have already stopped suppressing anything — `directives.find` drops
    them — so this is not the enforcement, it is the explanation. Without it a
    check simply starts failing again with the acknowledgement still sitting
    above it, and the author has to work out that the date is why.
    Reported apart from "no longer apply", because they are different facts. A
    stale acknowledgement means the subject moved under it: the document went
    Active, the reference was deleted. An expired one did its job and ran out
    of the time its author gave it, which is the outcome `until` was written to
    produce.
    """

def report_warnings(errors: list[str]) -> None
    """
    Status findings: warnings by default, failures on request (ADR-035).
    Citing a retired document is often correct — a `Rejected` decision exists
    to be pointed at — so by default every class here is reported and none
    fails the build. A project that wants a class *enforced* names it in
    `lint.fail_on`, and its unacknowledged rows become violations;
    the acknowledgement directives keep working either way.
    """

def run() -> None
    """Check the record; exits 1 with one line per violation."""

def scan_one(path) -> list[str]

```

## luria/migrate.py
```python
class Pair

    @property
    def old_parts(self) -> tuple[[str, int]]
        """
        Prefix and number. The old side is always numeric: a document that
        never had a number has nothing to migrate away from.
        """

    @property
    def new_parts(self) -> tuple[[str, str]]
        """
        Prefix and the LITERAL new tail — `004`, or `tmp47fje`.
        A string either way. The two spellings do not share a type: one is a
        number carrying a padding convention, the other is an opaque identity
        (ADR-049). An earlier `int | str` union pushed the ambiguity out to
        every call site, which then had to test the type to learn which it
        had — and the padding branch and the provisional branch are not the
        same question.
        """

    @property
    def new_is_provisional(self) -> bool
        """A temporary code, awaiting `luria concretize`."""

    @property
    def new_anchor_tail(self) -> str
        """
        How the tail is spelled inside an anchor: `#gp-4`, `#gp-tmp47fje`.
        Anchors never pad — the generator emits the bare number — so a
        numeric tail normalizes through `int` and a provisional one passes
        through untouched.
        """


@dataclass
class Plan

def _spec_path(ref: str) -> Path
    """The spec file `ref` names: a path, a filename, or a leading number."""

def _plan_rename(plan: Plan, op: dict) -> None

def _plan_move(plan: Plan, op: dict) -> None

def build_plan(spec: dict, title: str) -> Plan

def _tracked_files() -> list[Path]

def sweep_text(text: str, plan: Plan, paths: bool, source: Path) -> tuple[[str, int]]
    """
    Every mapped spelling in one text, rewritten. Masks only what the
    mapping doesn't own: composed remote codes (another project's namespace)
    that the spec didn't explicitly claim via `remotes = [...]`, URLs for
    the path pairs (a foreign repo can host a file by the same name), and
    every `formerly:` block.
    """

def rename_key_at(text: str, path: tuple[[str, Ellipsis]], old: str, new: str) -> str
    """
    Rename one mapping key, and only where it sits under `path`.
    Round-tripped rather than swept: `remotes.ARXIV` and `schemes.ARXIV` are
    the same six characters in the text and two different places in the
    document, and only a parser tells them apart. The round trip is
    ruamel's, so the comments a person wrote in their config survive a
    migration that was asked to rename a key (ADR-098).
    """

def config_paths_pass(text: str, plan: Plan) -> str
    """
    Path pairs in a config file, section-aware: a remote's `document:`
    line spells *that project's* path, which only moves if the spec claimed
    the remote via `remotes = [...]`. Everything outside unclaimed remote
    sections — the scheme's `output`, the `paths` values, comments —
    follows the rename.
    Which lines are whose comes from the parser rather than from counting
    indentation, because the enclosing mapping is what decides whose path a
    line spells and the parser is the thing that knows it. The rewrite is
    still textual: a rename reaches into comments and into the middle of
    string values, and neither is a node to reassign (ADR-098).
    """

def _stamp_formerly(path: Path, old_code: str) -> None
    """
    Append `old_code` to the document's `formerly:` list, creating it
    after the opening `---` when absent. Appending, never replacing: a
    document moved twice carries both pasts.
    """

def _git(args: list[str]) -> str

def apply(plan: Plan) -> tuple[[int, int]]
    """
    Execute the plan against the working tree. Returns (files swept,
    rewrites). Everything here is a working-tree edit — committing is the
    caller's (or `--commit`'s) move, so the diff can be read first.
    """

def describe(plan: Plan) -> list[str]

def _blame_ignore(sha: str, title: str) -> None

def run(spec: str, dry_run: bool, commit: bool) -> None
    """
    Execute the migration SPEC (a file in record/migrations.d/, named by
    path, filename or leading number). --dry-run prints the plan; --commit
    commits the result and appends it to .git-blame-ignore-revs.
    """

def masked_spans(text: str, mask_urls: bool) -> list[tuple[[int, int]]]

def swap(text: str, pattern: str, repl, mask_urls: bool) -> str

def swap_pair(text: str, pair: Pair) -> str

def unlink_relocated(text: str) -> str
    """
    Any link AT a moved document's old address loses its target.
    Matched on the ADDRESS, not the label: a citation may be worded
    (`[design-principles #17](../design-principles.md#dp-17)`) rather than
    spelled as the code, and those are exactly the ones a code-shaped
    pattern walks past — leaving a live link to a document that moved.
    The whole citation — label included — becomes the NEW CODE, bare, and
    the fixer links it. Keeping the old label was the first attempt and it
    undid itself: `[design-principles #17](…#dp-17)` stripped to
    `design-principles #17`, whose bare `#17` the resolver reads as a
    design-principle reference and re-linked straight back to the anchor
    that had just been vacated. A stale label is not worth preserving at
    the cost of resurrecting the address it names.
    """

def respell_relocated(text: str) -> str
    """
    A citation WORDED rather than spelled — `design-principles #17` in
    a code comment — names a moved document as surely as `DP-017` does,
    and both the code swap and the address swap walk straight past it: it
    contains no code, and (unlinked) it points at no address.
    The recognizer is the one the fixer already uses, so the two can't
    disagree about what counts as a reference — `find_refs` is what turns
    `design-principles #17` into a link in the first place. Only
    *relocated* documents are respelled, and only the prose spellings: a
    citation that already spells the code belongs to `swap_pair`, which
    knows how to mirror padding.
    """

def guarded(m: Any) -> str

def code_repl(m: Any) -> str

```

## luria/narrow_titles.py
```python
def _pattern(terms: tuple[[str, Ellipsis]]) -> Any | None
    """
    One alternation over the vocabulary, plural-tolerant.
    Built per call rather than cached: the vocabulary is config, and config
    resets. A stale pattern would be the hand-kept projection this project
    exists to argue against.
    """

def _acknowledged(path, text: str) -> set[str]
    """Terms this document says it is using in another sense."""

def rows() -> list[str]
    """One line per narrow title, ready for the warning report."""

```

## luria/new.py
```python
def kinds() -> dict[[str, tuple[[str, object]]]]
    """
    Every place the record takes a new entry, keyed by the name `luria
    new` accepts. Derived from config, so the help text and the dispatch
    can't disagree about what this project scaffolds.
    """

def default_kind() -> str | None
    """
    The journal, when there is exactly one — `luria new` with no argument
    files a devlog entry, the commonest scaffold by far.
    """

def _sub_line(text: str, field: str, value, many: bool) -> str
    """
    Replace a single-line frontmatter field, or a block one (`>-` /
    list) through its indented continuation lines. A field the form does not
    scaffold is appended rather than dropped — substitution on no match used
    to lose the value and report success.
    `value` may arrive as a tuple: Fire reads `--tags record,mechanism` as
    a Python literal, and that is the spelling the help text invites.
    `many` is the contract's word for the field's shape (#169). Without it
    a comma-separated value became the single string `'LIT-1, LIT-2'` — a
    list stringified and half-read, which is the finding #141 added, written
    by the tool that scaffolds the document.
    """

def _drop_field(text: str, field: str) -> str
    """
    Remove a frontmatter field and its continuation lines — the block
    `_sub_line` would have replaced — leaving the comment above it.
    """

def _append_field(text: str, block: str) -> str
    """
    Add a field at the end of the frontmatter, where a reader looks for
    what the form did not prompt for.
    """

def plural_fields(scheme) -> frozenset[str]
    """
    The fields this scheme's contract declares hold a list. Read from the
    contract rather than named here, so the scaffold and the lint cannot
    disagree about a field's shape — which is the whole of #169.
    """

def declared_fields(scheme) -> tuple[[str, Ellipsis]]
    """
    Every field a scheme names, for `luria new` to accept as a flag and
    to refuse anything else by. The kinds are the config (ADR-036); so are
    the flags.
    A derived field is not among them (#216): its value comes off another
    field, so a flag for it would scaffold a line the lint rejects on the
    document's first read — the scaffold offering a guaranteed violation.
    """

def _mint_tail(scheme) -> str
    """
    A fresh temporary tail (ADR-049): the `tmp` sentinel plus five base-36
    characters — `tmp47fje` — so the code can never be read as a number AND
    reads as provisional to someone who has never met the convention. Random
    rather than derived, because the whole point is an identity that needs no
    coordination — checked against the tails already on disk, which is the
    only collision this process can see and the only one likely enough to
    matter (the space is 36⁵ per scheme).
    """

def new_scheme_doc(scheme, fields: dict[[str, str]]) -> Path

def write_number(text: str, number: int) -> str
    """
    Put `number: N` at the top of a document's frontmatter.
    First line, above the scaffold's comments: identity is the one field a
    reader should not have to hunt for, and `luria repair` writes it into
    existing documents at the same place, so a migrated record and a fresh
    one read alike. Text surgery rather than a YAML round-trip, for the
    reason `field_edit` gives — rewriting through a parser reflows the
    comments a scaffolded document is mostly made of.
    """

def new_fragment(dir_name: str, name: str | None) -> Path
    """
    A fragment named for its filing moment, like a journal entry.
    It used to be named for the git branch — one fragment per contribution,
    addressed by where the contribution lived. That identity broke the first
    time a branch was restarted from the default branch after a squash merge:
    the same branch name filed a second contribution, `luria new changelog`
    reopened the *merged* fragment, and two PRs' entries muddled into one
    batch (#76). A timestamp is the identity the devlog already uses, and it
    cannot collide; flat rather than `yyyy/mm/dd/` nested, because the
    collector and the lint glob a fragment directory one level deep. Two
    fragments from one contribution is fine — they collect into the same
    dated batch. `--name` remains the explicit override, and an existing
    named fragment is reopened rather than duplicated.
    """

def new_migration(fields: dict[[str, str]], name: str | None) -> Path
    """
    The next spec in record/migrations.d/ — numbered like a document,
    because execution order is information (a move can depend on a rename).
    """

def new_entry(kind: str | None, fields: dict[[str, str]], name: str | None) -> Path

def run(kind: str, title: str, status: str, summary: str, tags: str, name: str) -> None
    """
    Scaffold an entry and print its path. KIND defaults to the journal;
    the other kinds come from luria.yaml (scheme prefixes, fragment dirs).
    Field flags are optional — content belongs to your editor.
    Beyond the four universal flags, a scheme's own declared fields are
    accepted by name — `--source LIT-134,LIT-140` where the SOTA scheme
    declares `source` — and written in the shape the contract declares
    (#169). An undeclared flag is refused rather than written, because a key
    the scheme has no opinion about, scaffolded by a script, is exactly the
    kind of thing nothing downstream would ever report.
    """

```

## luria/parallel.py
```python
def jobs() -> int
    """
    How wide to run. `LURIA_JOBS` wins; 0/unset means the default width.
    A fixed default rather than `os.cpu_count()`, because the workloads are
    I/O-bound — the right width tracks latency overlap, not cores.
    """

def pmap(fn: Callable[[Any, R]], items: Iterable[T]) -> list[R]
    """
    `list(map(fn, items))`, run on a thread pool, results in input order.
    Exceptions propagate exactly as they would serially — the first failing
    item raises when its result is collected — so a caller's error handling
    is the same either way.
    """

```

## luria/pins.py
```python
def stable_url(remote: Remote, code: str) -> str
    """
    The URL whose bytes ARE the document — the code's `bytes` URI.
    One rendering call: `remotes.construct` supplies the lockfile's word on
    {filename}, `Remote.uri` applies the precedence (a declared template at
    either level, then the default derived from the same shape `read`
    constructs by — GitHub's raw scheme as a shipped template, not a regex
    over a rendered URL). "" means no source vouches for stable bytes: a
    rendered page's markup churns under identical content, so a hash of it
    would drift on its own schedule and the pin would cry wolf (ADR-016).
    A source-specific case — another forge, a service's canonical bytes
    endpoint — is a `uris.bytes` template in config, or one more entry in
    `config._DEFAULT_URIS`; everything downstream consumes only the URL.
    """

def content_hash(body: bytes) -> str
    """
    `sha256:<hex>` — prefixed so a future algorithm change is visible in
    the lockfile rather than silently comparing across algorithms.
    """

def state() -> dict[[str, dict[[str, dict[[str, str]]]]]]
    """
    The committed content pins: {prefix: {code: {endorsed, seen}}} (#135).
    `endorsed` is the hash of the content a human vouched for; `seen` is what
    upstream served at the last `--refresh`. The two disagreeing is the whole
    signal, and it lives in the lockfile so `luria lint` can read it offline.
    """

def url_state() -> dict[[str, dict[[str, str]]]]
    """
    The committed URL pins: {url: {endorsed, seen}} — the same two-hash
    bargain for content that is not a foreign code at all.
    """

def _copy(pinned: dict) -> dict

def flagged_urls(files) -> tuple[[set[str], list[str]]]
    """
    URLs a `pin:` directive marks for endorsement, and the directives that
    mark nothing.
        <!-- pin: https://spec.test/v1.html — the spec this implements -->
        We follow [the spec](https://spec.test/v1.html).
    Not every load-bearing citation is a foreign code: a spec, a blog post,
    a dataset card. The flag lives where the URL is cited — same scopes as
    every directive — and it IS the pin's registration: `luria remotes
    --pin` endorses what is flagged, and removing the flag is how a pin is
    retired (the next bare `--pin` prunes it). A pin that fires too often
    costs one deleted comment, and the URL goes back to being an ordinary,
    unwatched link.
    The directive's own comment is blanked before checking what it governs —
    otherwise every flag would satisfy itself with the URL in its own text,
    and a flag whose citation was deleted could never report itself stale.
    """

def flag_problems() -> list[str]
    """
    `pin:` directives that register nothing — the lint's stale-directives
    section reads these, same bargain as every other directive (DP-1).
    """

def endorse(requested: tuple[[str, Ellipsis]]) -> None
    """
    Endorse remote content: fetch each document, store its hash (#135).
    With arguments — codes or flagged URLs — endorse exactly those, which is
    also the ONLY way a drifted pin is endorsed again. With none, sync the
    lockfile to what is registered: every cited code the config declares
    pinned (`pin = true` on a remote or one of its schemes), every existing
    pin that is still cited, and every `pin:`-flagged URL — and drop pins
    nothing cites or flags any more, so the committed state keeps describing
    the record that exists. A bare run never moves an `endorsed` hash that
    upstream has drifted from: it records the observation and names the
    explicit command, because a scheduled sweep must not quietly launder the
    findings the lint was about to raise.
    """

def _endorse_one(label: str, url: str, into: dict, key: str, explicit: bool) -> None
    """
    Fetch one document's stable bytes and record the endorsement.
    A change since the last endorsement is endorsed only by an explicit act:
    a bulk run records it as `seen` — the same observation `--refresh` makes
    — and says which command endorses it, so drift always crosses a human's
    desk before the record vouches for it again.
    """

def refresh_seen() -> list[str]
    """
    Re-fetch every pinned document and record what upstream serves now in
    `seen` — never touching `endorsed`, which only `--pin` moves. Returns the
    codes that drifted; the committed diff is what lets `luria lint` warn
    offline (#135).
    """

def _observe(label: str, url: str, entry: dict, drifted: list[str]) -> None
    """One fetch into one pin's `seen` hash."""

def migrate_endorsements(moves: list[tuple[[str, str, str]]], claimed: list[str]) -> tuple[[int, list[str]]]
    """
    Carry pinned endorsements through a migration (ADR-040, #135).
    A rename moves a document's ADDRESS and leaves its content standing, and
    the endorsement is of the content — so for each claimed mirrored remote,
    a pin is re-keyed from the old tail to the new one with both hashes
    intact, rather than dropped and re-fetched. The distinction is not
    cosmetic: prune-and-re-endorse would silently vouch for whatever is
    upstream at that moment, laundering any drift a human had not reviewed.
    The claimed remote's discovered filename map is dropped instead of
    re-keyed: its keys AND its values spell the old world, an authoritative
    map with the wrong keys turns every new-spelled reference into "absent
    from the remote", and discovery (`luria remotes --refresh`) is the only
    authority that can rebuild it — absence honestly means "code-only
    convention until then". When upstream's own rename lands, the pinned
    documents' bytes will have changed too (their citations were swept), and
    that surfaces as ordinary drift for review — exactly the crossing of a
    human's desk the two-hash design exists to force.
    Returns (pins re-keyed, remote prefixes whose filename maps dropped).
    """

def drift_lines() -> list[str]
    """
    Every pin out of step with the record — from the committed lockfile
    alone, so the lint that reads this stays a check that passes on a train.
    The network work happened earlier: `--pin` recorded the endorsement,
    `--refresh` recorded what upstream serves, and this compares.
    """

```

## luria/readme.py
```python
def markers(name: str) -> tuple[[str, str]]
    """The opening and closing comments delimiting the `name` region."""

def _region_re(name: str) -> Any

def has(text: str, name: str) -> bool

def rewrite(text: str, name: str, body: str) -> str
    """
    `text` with the `name` region's contents replaced by `body`, or `text`
    unchanged where the region is absent.
    """

def path() -> Path

```

## luria/record_doc.py
```python
def _rel(cfg, path: Path | None, dir: bool) -> str
    """
    A path as the reader will type it: relative to the project root, with
    a trailing slash when it names a directory.
    `dir` is passed by the caller rather than read off the disk. A first draft
    asked `Path.is_dir()`, which made the page a function of the filesystem
    and therefore not idempotent: a directory `luria index` creates on its own
    run answers differently before and after, so the page rendered one way,
    was written, and then compared unequal to itself. `luria index && luria
    lint` on a fresh `luria init` caught it — the config always knew which
    kind each path was, and this now asks the config.
    """

def _table(header: list[str], rows: list[list[str]]) -> str

def schemes_section(cfg) -> str
    """One row per referable document family — the thing a code names."""

def contracts_section(cfg) -> str
    """
    What each scheme demands of an entry beyond the standard fields —
    the compiled contract `luria lint` checks (#141), one line per
    obligation, each naming the key that declared it. Rendered from the
    same description a finding cites, so the page and the lint cannot
    disagree about what a scheme asks for.
    """

def journals_section(cfg) -> str
    """
    Dated entries that persist. Unlike a fragment directory, nothing
    consumes them — the books are a view over sources that stay.
    """

def fragments_section(cfg) -> str
    """
    Many small files assembled into one document, and then consumed —
    which is what makes a fragment directory conflict-free per contribution
    and a journal permanent.
    """

def remotes_section(cfg) -> str
    """Another project's codes, citable from this one by a prefixed code."""

def filing_section(cfg) -> str
    """
    What to type. Derived from `new.kinds()`, the same mapping the CLI
    dispatches on, so the command in this table is the command that works.
    """

def _flatten(prefix: str, value, depth: int) -> list[tuple[[str, object]]]
    """
    `{"site": {"theme": {...}}}` as `site.theme`, and no deeper.
    `depth` stops at a settings table's own keys, which is where a *decision*
    lives. A theme is one choice with twenty-four colours in it; flattening all
    the way turns one changed setting into twenty-four rows and buries the
    other five.
    """

def _value(v) -> str
    """
    A configured value as a reader would recognize it — a scalar as itself,
    a list spelled out, a nested table by the count that makes it one.
    """

def settings_section(cfg) -> str
    """
    The settings this project moved off Luria's defaults, and nothing else.
    A diff, not a dump: a reader looking at a full key table cannot tell which
    rows were decided and which merely happened. Family tables are excluded —
    they *are* the sections above, and are replaced whole rather than merged
    (ADR-047), so "differs from the default" is not a meaningful question to
    ask of one.
    """

def render() -> str

def outputs(out_dir: Path | None) -> dict[[Path, str]]
    """
    The page, keyed by where it lands — the unit `luria index` renders, so
    a stale page fails the same check as every other view.
    """

def write(out_dir: Path | None) -> list[Path]

```

## luria/ref_status.py
```python
def _blank(text: str, spans: list[tuple[[int, int]]]) -> str

def _rel(path: Path) -> str
    """Repo-relative when it can be; absolute otherwise (test fixtures)."""

class Doc
    """A referable document: its code, its status, and whether that's in force."""

def _load_scheme(scheme) -> dict[[str, Doc]]
    """
    Every document in one scheme's directory, with its status.
    Frontmatter-with-a-`status:` is the only contract a scheme has to meet, so
    a second scheme is a directory and a prefix — not a code change (ADR-006).
    Merge-allocated documents (ADR-049) are loaded alongside the numbered
    ones. Reading the directory by number skipped them, and a document the
    checker holds no record of reads as a code that names nothing — so a
    `Proposed` decision could be cited as settled and nothing said so until
    `luria concretize` gave it a number, on `main`, in a file nobody had
    touched (#203). Its status was in its frontmatter the whole time.
    """

def schemes() -> dict

def load_docs() -> dict[[str, Doc]]

def _codes(spec: str) -> tuple[[set[str], str]]
    """
    The document codes an annotation names, and the text with them removed.
    Composed codes come out first and whole: a remote's `DP-004` is that
    remote's principle, and reading the tail out of the middle of the composed
    code would have the validator check the wrong project (ADR-016).
    """

def _exists(code: str, known: set[str]) -> bool
    """
    Whether a code names something. A composed one asks the remote —
    parsed by the remote's own delimiter and tail shape, not by assuming a
    hyphen (ADR-024).
    """

class Annotation

    def __str__(self) -> str

    @property
    def scope(self) -> str

    def covers(self, line: int) -> bool


def annotations(path: Path, text: str, known: set[str], directive: str) -> list[Annotation]
    """
    Every annotation of one kind in `path`, malformed ones included — they
    are reported rather than dropped, because an annotation that silently does
    nothing is worse than no annotation.
    The two kinds share every rule but one, and it is inverted: `inactive-ok`
    must name a document that exists (else it excuses nothing), while
    `unresolved-ok` must name one that doesn't (else there is nothing to
    excuse). Same check, opposite sign.
    """

class Citation

    def __str__(self) -> str


@dataclass
class Scan

    def used(self, ann: Annotation) -> bool


def scanned_files() -> list[Path]
    """Current-guidance docs + code. Order is stable so the report is."""

def forget_scan() -> None
    """
    Drop the corpus scan — for a writer that outruns mtime resolution, and
    for tests that count how often the corpus is scanned.
    """

def _fingerprint() -> tuple

def scan(files: list[Path] | None, docs: dict[[str, Doc]] | None) -> Scan
    """
    Every citation and every annotation — see `_scan`.
    The no-argument call, which asks about the whole record, is served from a
    cache keyed on the corpus's stat fingerprint. A call that names its own
    `files` or `docs` is asking about a corpus the fingerprint does not
    describe, so it is computed every time.
    The returned `Scan` is shared between callers and must be treated as
    read-only.
    """

def _scan(files: list[Path] | None, docs: dict[[str, Doc]] | None) -> Scan
    """
    Every citation and every annotation, with each citation pointing at the
    annotation that excuses it (if any).
    Deliberately unmasked, unlike the link lint: a reference in a code comment
    or inside a fenced block is still a claim about why the code is the way it
    is, which is the thing being checked.
    """

def _spread(sites: list[Citation], limit: int) -> list[Citation]
    """
    Up to `limit` sites, one file at a time before repeating a file — a
    single file's five consecutive lines say much less than five files do.
    """

def flagged(result: Scan | None, docs: dict[[str, Doc]] | None)
    """
    (Doc, unexcused sites, excused count) for retired documents that are
    still cited without an acknowledgement — most-cited first.
    """

def dangling(result: Scan | None, docs: dict[[str, Doc]] | None) -> list[tuple[[str, list[Citation], int]]]
    """
    (code, unexcused sites, excused count) for codes that name no document
    here — most-cited first.
    Three things look identical from here and read very differently: a typo, a
    number carried in from another project, and a fixture code in a test. Only
    a human can tell them apart, which is why this is a report and not an error
    (ADR-035) — and why `unresolved-ok` exists to retire the ones that are
    deliberate.
    """

def dangling_lines(result: Scan | None, docs: dict[[str, Doc]] | None) -> list[str]

def acknowledged_count(result: Scan | None, docs: dict[[str, Doc]] | None) -> int
    """
    How many references to retired documents an annotation excused. Printed
    every run: a suppression nobody counts is a suppression nobody notices.
    """

def dangling_acknowledged_count(result: Scan | None, docs: dict[[str, Doc]] | None) -> int
    """
    The same count for `unresolved-ok`. Both are printed on a clean run, so
    "nothing to report" can never mean "everything was silenced".
    """

def stale_annotations(result: Scan | None, docs: dict[[str, Doc]] | None) -> list[str]
    """
    Annotations that no longer excuse anything — the document went Active,
    the reference moved, or the annotation is malformed. A suppression that
    rots silently is the thing acknowledgements are supposed to prevent.
    """

def summary_lines(result: Scan | None, docs: dict[[str, Doc]] | None) -> list[str]
    """
    One line per flagged document — what `luria lint` prints. Every count
    is real; the sites are what's elided, and `luria reports` has them.
    """

def warnings(sites: int, result: Scan | None, docs: dict[[str, Doc]] | None) -> list[str]
    """The summary, plus where to look."""

def run(all: bool) -> None
    """The reference-status report on the console; --all lists every site."""

```

## luria/referents.py
```python
@dataclass
class Lookup
    """Code → that document's written frontmatter, read at most once each."""

    def __call__(self, code: str) -> dict
        """
        The frontmatter for `code`, or `{}` when it names no document.
        `{}` rather than an exception: a code that resolves to nothing is
        already the reference check's finding, and raising here would report
        one fault twice — on the line that cites it and on the line that
        derives from it.
        """


def _read(code: str) -> dict
    """
    Through `read_document`, not around it (DP-4).
    This opened and parsed the file itself, which made it a second reader of
    a document — and a second reader does not take the bargain that makes the
    cache safe. `read_document` expires an entry when the file's mtime moves,
    so `field_edit` and `repair` can write mid-run and read back; a reader
    outside that cannot be dropped by `forget_documents()` and can see a
    different revision than every other caller in the same run.
    Not a speedup: measured on two records, routing this through the cache
    costs and saves nothing detectable. The cost that mattered was a
    directory glob, not a parse.
    """

def path_of(code: str) -> Path | None
    """
    The file a local code names, or None — a remote, an unknown scheme, or
    a number no document carries.
    Temporary codes resolve too (ADR-049): a merge-allocated document is a
    real document that has not been numbered yet, and a derivation off one
    should not go blank until the merge that numbers it.
    """

```

## luria/relations.py
```python
class Repair
    """
    One edit that makes a declared pair agree: add `code` to `path`'s
    `field`, or remove it. Which of the two depends on what *changed* — see
    `_intents`.
    """

def pairs() -> list[tuple[[str, str, str, str]]]
    """
    Every declared converse, as (scheme, field, converse field, converse
    scheme).
    The fourth element is where a relation's far side lives, and it is the
    declaring scheme only when the relation does not cross one:
    `SOTA.introduced_by` holds `LIT` codes, so its converse `introduces` is a
    field on `LIT` (#253).
    Both directions appear, so a caller iterating this sees each edge from
    the side that declares it. A self-converse relation appears once.
    """

def _codes(doc: Adr, name: str, contract) -> list[str]
    """
    The codes one relation field holds. A shape the contract rejects is
    the lint's finding, not this reading's.
    """

def _documents(prefix: str) -> dict[[str, Adr]]
    """Every document of one scheme, by code."""

def _reads(owner: str, field: str, target: dict[[str, Adr]]) -> dict[[str, set[str]]]
    """
    What each document of `owner` declares in `field`, filtered to codes
    that land in `target` — the scheme whose codes the field holds.
    Filtering against the *target* rather than the owner is what makes this
    work when the relation crosses: a reference outside the scheme it names
    is the contract's finding, not an edge here, and which scheme that is
    depends on the field.
    """

def _held(prefix: str, field: str, back: str, far: str) -> tuple[[dict[[str, Adr]], dict[[str, Adr]], dict[[str, dict[[str, set[str]]]]]]]
    """
    Both sides of one pair: the near documents, the far documents, and
    what each side declares. For a relation that does not cross, the two
    document sets are the same object and this is the old behaviour.
    """

def edges(prefix: str, field: str) -> dict[[str, set[str]]]
    """
    One relation as declared from *either* side: what each document holds
    in `field`, plus what other documents name it in the converse.
    The union is why a one-sided declaration still reads correctly before
    anyone runs the fixer. Completion makes the two agree on disk; this makes
    them agree in every reading meanwhile. A field with no declared converse
    is simply itself.
    """

def converse_of(prefix: str, field: str) -> str
    """The field holding `field` read backwards, or "" if none is declared."""

def converse_scheme_of(prefix: str, field: str) -> str
    """
    Which scheme that converse field lives on — `prefix` itself unless the
    relation crosses.
    """

def _contradictions(field: str, back: str, held: dict) -> set[tuple[[str, str]]]
    """
    Pairs already standing in both directions of one relation.
    Two shapes, and only for a directed pair — for a symmetric relation both
    documents holding the fact is the *completed* state, not a clash. A
    document naming another in both `field` and its converse says that other
    is at once before and after it; two documents each naming the other in
    `field` say the same thing from opposite ends. Either way nothing is
    missing: two incompatible things are present.
    """

def _at_head(prefix: str, fields: set[str]) -> dict[[str, str]] | None
    """
    The committed text of every document of this scheme that declared one
    of these fields at HEAD, keyed by path relative to the root.
    `None` means there is no baseline to compare against — no repository, or
    no commit yet. Narrowed with `git grep` because the answer only depends
    on documents that declared a relation, which is a handful of a corpus.
    """

def _side_at_head(prefix: str, field: str) -> dict[[str, list[str]]] | None
    """What each of one scheme's documents declared in one field at HEAD."""

def _committed(prefix: str, field: str, back: str, far: str) -> tuple[[set, set]] | None
    """
    The two edge sets as HEAD held them: declared forward, and declared
    from the converse side. `None` when there is no baseline.
    Each side is read out of its own scheme's directory, which is the same
    directory twice unless the relation crosses.
    """

def _listed(value) -> list[str]
    """
    Codes from a raw frontmatter value, list or scalar. Deliberately not
    contract-resolved: HEAD's config is not necessarily this one's, and all
    that is wanted here is what the text said.
    """

def _now(field: str, back: str, held: dict) -> tuple[[set, set]]
    """The same two edge sets as the working tree holds them."""

def _intents(prefix: str, field: str, back: str, far: str, docs: dict, far_docs: dict, held: dict) -> tuple[[list[Repair], list[tuple[[str, str]]]]]
    """
    What to do about every edge either side declares, and the conflicts.
    The rule is about *change*, not about state. A one-sided edge means one
    of two opposite things — somebody wrote it and the other side has not
    caught up, or somebody deleted it and the other side is stale — and the
    working tree holds neither answer. What changed since the last commit
    does.
    Added on either side wins by being written to both. Removed on either
    side wins by being taken from both. Added on one side while removed on
    the other is two deliberate edits that contradict: reported, never
    resolved, because writing either loses the other.
    An edge nothing has touched falls through to adding, which is what a
    corpus predating the fixer needs. That reading can be wrong — a deletion
    committed before the fixer ran looks like nothing changed — but it is
    self-correcting: delete it once more and the deletion *is* a change.
    """

def _mutual(field: str, back: str, held: dict, edge: tuple[[str, str]]) -> bool
    """
    Whether this clash is the relation asserted in both directions, as
    opposed to one side withdrawn while the other was asserted.
    """

def _applied(meta: dict, entries: list[Repair]) -> dict
    """`meta` as it would read after these repairs, without touching disk."""

def _contract_for(path: Path)
    """
    The contract of whichever scheme owns this document. A repair can now
    land in either of a pair's two schemes, so the contract that judges it is
    a property of the file, not of the relation.
    """

def _blocked(prefix: str, docs: dict, repairs: list[Repair]) -> tuple[[list[Repair], list[tuple[[Repair, str]]]]]
    """
    Split repairs into the ones that are safe to write and the ones that
    would break the document they land in.
    The fixer edits frontmatter, and frontmatter is what the contract judges,
    so an edit can move a document from satisfying its scheme to violating
    it — a back-reference added into a field group that allows only one of
    two fields, or a stale one removed out of a field the status requires.
    Neither is the author's mistake and neither should be made silently.
    Only *new* violations block. A document already in breach somewhere else
    still gets its back-references, or one unrelated mistake would freeze
    every relation it stands in.
    """

def _all_repairs() -> tuple[[list[Repair], list[tuple[[Repair, str]]]]]
    """Every edit the declared pairs need, and every one held back."""

def completions() -> list[Repair]
    """
    Every edit a declared pair needs and the contract permits, ordered so
    a run is reproducible. Empty when every pair already agrees.
    """

def rows() -> list[str]
    """
    A declared pair the two documents do not agree on, said in the
    record's own paths and naming what the fixer will do about it.
    """

def complete(fix: bool) -> list[Repair]
    """
    Make every declared pair agree; report the edits without `fix`.
    Grouped per file so a document needing several is written once.
    """

def relation_spans(path, text: str) -> list[tuple[[int, int]]]
    """
    Where a document declares its place in a line, as character spans.
    Not a citation site. `extends:` names the step this work builds on, and
    that step being retired is what a line *looks like* — a successor's
    predecessor is superseded by construction. Reporting it would hand back
    one "cites a retired document" finding per retired step in every chain,
    at the field whose entire job is to name it, and the only way to quiet
    them would be an acknowledgement comment per edge. `compared_against:`
    goes the same way: a comparison against a design that has since been
    retired stayed true when the design was retired.
    The codes are still checked — that a reference resolves, and resolves in
    the declared scheme, is the contract's business and unaffected. What is
    suppressed is only the reading of these fields as *citations*, the way a
    `formerly:` entry and a code inside a URL already are.
    Both halves of a declared pair, not just the one a chain names: the
    converse states the same fact from the far end, so exempting one and
    reporting the other would hand back a finding for every edge the fixer
    completes.
    """

```

## luria/remotes.py
```python
def tail_re(remote: Remote) -> str

def remote_pattern(remote: Remote) -> Any

class RemoteRef
    """One foreign reference found in text, already canonical."""

    @property
    def prefix(self) -> str

    @property
    def composed(self) -> str


def references(text: str) -> list[RemoteRef]
    """
    Every configured remote's references in `text`, in source order.
    Scanned per remote rather than by one combined regex, because each remote
    brings its own delimiter and tail shape. Longer prefixes scan first and
    claim their spans, so `SGX-…` is never read as `SG` plus a strange tail.
    """

def parse_code(text: str) -> tuple[[Remote, str]] | None
    """
    `SG-DP-18` → (the SG remote, "DP-018"); None when no remote matches the
    whole string. The one reader of a composed code's anatomy — annotation
    arguments, link labels and report keys all come through here, so the
    delimiter is spelled in exactly one place (DP-4).
    """

def normalise(code: str) -> str
    """
    A scheme code with and without leading zeros is one document — one lock
    key. Only scheme-shaped tails come here; a uid is exact already.
    """

def _read_lockfile() -> dict

def lock() -> dict[[str, dict[[str, str]]]]

def write_lock(found: dict[[str, dict[[str, str]]]] | None, pinned: dict[[str, dict[[str, dict[[str, str]]]]]] | None, urls: dict[[str, dict[[str, str]]]] | None, titles: dict[[str, dict[[str, str]]]] | None) -> Path
    """
    Write the lockfile, replacing only the sections given — a refresh must
    not lose the pins, nor a pin the discovered filenames.
    """

def construct(remote: Remote, code: str, name: str) -> str
    """
    The named URI for one foreign code, with the lockfile's word on
    {filename}.
    `Remote.uri` renders templates; this supplies the one variable only the
    lockfile knows. **Discovery, once done, is authoritative** (ADR-016): a
    map read from the remote whose keys omit this code means the code names
    no file there — {filename} is then unavailable, any construction that
    needs it renders "", and guessing anyway once produced a confident link
    to a file that has never existed. No map at all is the different claim
    "never discovered", and the code-only convention (ADR-013) fills
    {filename} instead. A template that never mentions {filename} — a `url`,
    a document anchor — is untouched by any of it, which is the old rule
    "the lockfile's authority covers exactly what discovery can see: files"
    falling out of variable availability rather than being control flow.
    """

def link(remote: Remote, code: str) -> str
    """The reader's URL for one foreign code — its `read` URI."""

def issue_link(remote_prefix: str, number: int) -> str
    """
    The URL for one of a remote's issues, or `""` when it has no tracker.
    `LU-#193` means luria's issue 193. Before this it meant nothing: the
    prefix was inert prose and the number resolved through the *citing*
    project's `issue_url`, producing a well-formed link to a different
    project's issue of the same number (#194). Nothing could catch it — the
    target resolved, so the link checker was satisfied.
    Empty for a remote with no `repo` and no explicit `issue_url`. A remote
    reached by a `url` template — an arXiv identifier, a ticket key — has no
    issue tracker, and inventing one would move the same silent wrongness
    somewhere new rather than remove it.
    """

def resolve(remote_prefix: str, code: str) -> str

def hand_links(files: list[Path] | None) -> tuple[[list[str], list[str]]]
    """
    Links whose label is a composed foreign code but whose target is not
    the URL Luria would construct — with the `url-ok:` annotations that
    acknowledge the deliberate ones.
    Construction has real limits: a remote's principles may be sections of one
    document, which no filename convention can address, so a hand-written URL
    is sometimes the only correct citation. It is also a hand-maintained
    projection ([DP-3](../docs/design-principles.md#dp-3)) frozen at writing
    time — if the remote later adopts a convention or the lockfile learns the
    real filename, nothing updates it. So each one is either acknowledged or
    reported (ADR-035): never an error, never silent.
    Returns (flagged, stale): unacknowledged hand links, and `url-ok`
    directives that no longer acknowledge anything.
    """

def _same_code(arg: str, code: str) -> bool

def _from_names(names: list[str]) -> dict[[str, str]]
    """
    Filenames → {code: filename}. The same permissive rule
    `Scheme.number_of` uses, so a remote on either naming convention reads.
    """

def _upstream_dir(text: str, fallback: str) -> str
    """
    The remote's own `luria.yaml` is the authority on where its documents
    live. Reading it rather than guessing is the whole point of a config file
    existing — and when there isn't one, the configured value stands.
    """

def _fetch_bytes(url: str) -> tuple[[bytes, str]]
    """
    (body, why-not). Public HTTPS only — there is no credential path here,
    deliberately: a discovery that needs a secret is a discovery CI can't
    reproduce, and the answer for an unreadable remote is a `url` template.
    """

def _fetch(url: str) -> tuple[[str, str]]

def discover(remote: Remote) -> tuple[[dict[[str, str]] | None, str]]
    """
    ({code: filename}, how) for one remote. `how` names the source, or the
    reason there wasn't one — a discovery that silently finds nothing is
    indistinguishable from a remote with no documents (DP-1).
    None and {} are different claims, and the difference is the lockfile's
    whole authority: {} means the directory was read and holds no documents,
    which is a finding; None means the remote could not be read at all, and
    writing an empty map for it would flip every one of its references to
    "absent from the remote" (the exact false alarm `readable()` exists to
    prevent).
    """

class Probe

    @property
    def ok(self) -> bool


def cited() -> dict[[str, set[str]]]
    """Every foreign code this project actually cites, by remote prefix."""

def _head(url: str) -> tuple[[bool, str]]
    """(reached, why-not). A HEAD, because the body is never wanted."""

def readable(remote: Remote) -> tuple[[bool, str]]
    """
    Whether this remote can be read at all, anonymously.
    Probed once per remote, and it is what keeps the check honest. A private
    repository answers 404 to every anonymous request, so probing documents
    without asking this first reports a shelf of perfectly good links as
    broken — a guard that cries wolf, which is a guard nobody reads
    (ADR-016).
    """

def probe(remote: Remote, code: str, visible: bool) -> Probe
    """
    One document. `visible` is `readable()`'s verdict for the remote, so a
    private repo yields "unverifiable" rather than a false "404".
    """

def run(refresh: bool, check: bool, pin: bool | str | tuple, resolve: bool | str | tuple) -> None
    """
    How each configured remote's cited references resolve. --refresh
    discovers code→filename maps into the lockfile and re-observes pinned
    content; --check HEADs every construction (needs network — a report,
    never a failure); --pin endorses remote content by hash, so `luria lint`
    can report when a cited document changes upstream (#135); --resolve
    records what each identifier's title actually is, so the lint can report
    a document whose `arxiv:` names a different paper (#166).
    """

```

## luria/repair.py
```python
def apply() -> list[Path]
    """Every mechanical source repair, written: the files that changed."""

def populate_numbers(scheme) -> list[Path]
    """
    Write `number:` into every document of `scheme` that lacks one, from the
    number its filename already carries.
    A temporary document is skipped: it has no number yet by design, and
    `luria concretize` writes the field at the moment it assigns one
    (ADR-049). Idempotent, like every repair here — a second run finds the
    field present and does nothing.
    """

def retire_aliases(scheme) -> list[Path]
    """
    Move a document's superseded alias into `formerly:`.
    The alias at the last commit against the alias now: they differ exactly
    when the field the template reads was edited, and the old spelling is
    then live in citations that nothing else would ever fix. Idempotent — a
    second run finds the entry already recorded.
    Nothing happens without a template, and nothing happens for a spelling
    already recorded, so a record that never edits a source field never sees
    this repair at all.
    """

def run() -> None
    """
    Write every mechanical source repair: link bare references, populate
    `created:` from a journal entry's path, move a note out of `status:`
    into `status_note:` and `superseded_by:`, retire a stale configuration
    reference. Prints what changed; a second run changes nothing. Returns
    nothing — Fire would print a return value, and a list of paths is not
    the summary a caller wants.
    """

```

## luria/reports.py
```python
def _link(target: Path, base: Path) -> str

def _n(count: int, noun: str, plural: str) -> str
    """
    `1 document`, `3 documents` — counted prose, not `document(s)`.
    The console warnings keep the parenthetical style (they are terse by
    trade); a report is a page someone reads, and `(s)` makes every count a
    small puzzle.
    """

def _site(c, base: Path) -> str
    """
    A citation site as a clickable list item — the label keeps the line
    number, the link lands on the file.
    """

def reference_status(base: Path | None) -> str

def _pending_table(rows, base: Path) -> list[str]
    """
    One table of undecided documents. Shared by the flat rendering and the
    per-scheme one, so the columns cannot drift apart between them.
    """

def _pending_by_scheme(rows) -> list[tuple[[str, list]]]
    """
    `(prefix, rows)` for each scheme that has an undecided document, in the
    order `luria.yaml` declares the schemes (#230).
    Declaration order rather than alphabetical, for the reason `tags.yaml`
    orders topics: which family a reader meets first is the project's
    statement about itself, not something to sort.
    A prefix `pending()` returned that no scheme declares still gets a group
    — the collector is the authority on what is undecided, and a renderer
    that silently dropped rows would be the worse failure.
    """

def pending_decisions(base: Path | None) -> str

def unbound_lineage(base: Path | None) -> str
    """Relations that assert a shared property no field names (#214)."""

def outputs(out_dir: Path | None) -> dict[[Path, str]]
    """
    Every report, keyed by where it lands — the unit `luria index`
    renders, so a stale report fails the same staleness check as every other
    view (#35).
    """

def write(out_dir: Path | None) -> list[Path]

def run(out: str) -> None
    """
    Write the status reports — to the configured dir, or --out elsewhere
    (e.g. a CI artifact staging dir).
    """

```

## luria/site.py
```python
@dataclass
class Report
    """
    What one staging run did, in the shape the CLI prints and a test
    asserts on. Counted rather than merely logged: a link that could not be
    placed is the number worth watching, and a silent staging run would hide
    exactly the reference the site is meant to make followable (DP-1).
    """

    def lines(self) -> list[str]


def colors(site: Site) -> str
    """
    Quartz's `colors:` block, with `site.theme` merged over the
    generator's defaults.
    An unknown colour name is refused by name rather than dropped: a palette
    key silently ignored is a project wondering why its brand didn't take
    (DP-1).
    """

def _reinked(svg: str, ink: str) -> str
    """
    The artwork, forced to one ink colour.
    Only for a logo that declares `--luria-ink`. An inline `style` on the root
    element outranks the stylesheet rules inside the file, including the
    `prefers-color-scheme` one — which is the point: the site's theme is a
    toggle, and the operating system's preference is not it.
    """

def _svg_size(svg: str) -> tuple[[float, float]]
    """
    The artwork's aspect, from its viewBox — 4:1 if it hasn't got one, so
    a logo without one still renders rather than collapsing to nothing.
    """

def _excluded(rel: str, site: Site) -> bool

def document_source(path: Path, cfg) -> bool
    """
    Whether `path` is one code of a scheme that renders into ONE document.
    A design principle is the case: `record/principles.d/DP-004.md` assembles
    into `docs/design-principles.md`, so its links are spelled for `docs/` and
    `link_base` reports it as a source rendered elsewhere — which is why it
    went unpublished.
    Not every source that answers that description. A changelog or devlog
    fragment has no code, no title of its own and no identity apart from the
    view it lands in; there is nothing to give a page TO. This is the shape
    where the fragment IS a document — numbered, titled, statused, cited by
    code — that happens to be rendered as a section of one.
    """

def publishable(cfg, skip: Path | None) -> list[Path]
    """
    Every markdown file the site publishes, in a stable order.
    The derived rule is the second clause: a file whose links resolve against
    some *other* directory is a source rendered into a view, and the view is
    already here. Excluding it is not tidiness — its links are spelled for
    where its prose lands, so publishing it in place would break every one.
    `document_source` is the exception, and it is an exception to the
    CONSEQUENCE rather than to the rule: those links really are spelled for
    somewhere else, and `stage` re-spells them on the way out (`_rebase`). It
    earns that because a cited document with no page of its own is the one
    thing this record's own linter cannot say out loud.
    `skip` is the staging directory when it sits inside the project — the
    default `build/site` does. Without it the second run publishes the first
    run's output, and the site grows a copy of itself per build.
    """

def destination(path: Path, cfg) -> Path
    """
    Where `path` lands in the vault, relative to `content/`.
    Only the root README moves: Quartz serves `index.md` as the landing page,
    and a record whose front door is its README should not need a second copy
    of it to have one.
    """

def _alias(path: Path, cfg) -> str | None
    """
    The bare code a scheme document should also answer to — `/ADR-025`.
    This is the one place Obsidian's convention and Luria's meet. A wikilink
    here is a *code*, resolved through the scheme config; in a vault it is a
    *filename*, resolved by basename. For a file-per-code scheme those agree,
    and an alias makes the short URL agree too.
    """

def _inbound_labels(scheme) -> tuple[[dict[[str, str]], tuple[[str, Ellipsis]]]]

def _repeats_an_outbound(edge, held: set[tuple[[str, str]]]) -> bool
    """
    Whether an inbound edge says what this page's own frontmatter already
    said, through the converse field.
    The backlinks exist for the direction the site would otherwise lose. A
    declared converse removes that loss by storing the fact on both
    documents, so rendering the backlink too prints one fact twice under two
    labels — once humanised from the field, once as the raw field name.
    inactive-ok: ADR-084 — the decision this behaviour follows from; it is
    Proposed because nobody has marked it Active, not because it is unsettled
    Read from what the page actually holds rather than from the declaration
    alone: a one-sided relation is a lint finding, and a record mid-repair
    should still see the edge it has.
    """

def _edge_bits(outbound, inbound, scheme, known) -> list[tuple[[str, list[str]]]]
    """
    The typed edges as record-line fragments, wikilinks and all.
    Supersession and influence already read from the page's own frontmatter
    (the status note, `influenced_by:`), so outbound only adds the declared
    reference fields — the one direction the site otherwise loses, since
    frontmatter renders as nothing.
    """

def _scheme_of(source: Path)
    """
    The index-rendered scheme whose directory holds this document, if
    any. Where the successor field's name comes from.
    """

def _vocabulary_bits(meta: dict, source: Path) -> list[str]
    """
    A vocabulary field's *written* values, each linked to its page. The
    default is deliberately not shown: a reader is never shown a field the
    file does not have (ADR-076); the record page says what absence
    means.
    """

def readme_region() -> str
    """
    The README's link to where this record is published, or `""` when no
    URL can be derived.
    A link rather than a shields badge, deliberately. A badge carries a number
    that moves and is worth the round-trip; a base URL is a constant luria
    already knows, and rendering it as a remote image would cost a reader a
    request to display text this repository could have written itself — the
    same argument `badges.py` makes for baking its counts in.
    The prose around it stays the project's: the region holds the one fact
    that is derived, and anything a project wants to say about its site goes
    outside the markers where no rewrite will touch it.
    """

def titles() -> dict[[str, str]]
    """
    `{code: title}` for every referable document in the record.
    Read through `ref_status`, which already loads exactly this — one reader
    for "what documents are there and what are they called" rather than a
    second that could disagree (DP-4).
    """

def _plain(title: str) -> str
    """
    A title as data, with what the surfaces it lands in would read as
    syntax escaped.
    Two hazards, both real rather than hypothetical. `|` ends a table cell.
    And `[[` opens a wikilink the expander then tries to resolve — this
    project's own ADR-025 is titled ``Wikilinks: `[[CODE]]` is a typed
    reference``, and splicing it unescaped asked the resolver for a document
    called `CODE` on every page citing it.
    Markdown renders `\[` as `[`, so the escape costs the reader nothing.
    """

def _named(code: str, known: dict[[str, str]]) -> str
    """
    A code as a wikilink, followed by the document's title.
    A code alone asks the reader to already know the record: `LIT-141` says
    nothing about what it is, and the whole point of a backlink is to be
    followed by someone who does not yet know where it goes. The title is what
    makes the line answerable without opening anything.
    Unknown codes render bare rather than guessing — a remote code, or one the
    lint is already reporting as resolving to nothing.
    """

def _table(rows: list[tuple[[str, list[str]]]]) -> str
    """
    The record's facts as a two-column table.
    They were one line of `**Label** value` separated by center dots, which
    reads acceptably at three facts and not at eleven: `LIT-140` runs to a
    paragraph of bolded fragments a reader has to parse before they can scan.
    A table gives every fact the same shape and puts the labels in a column,
    which is what makes it scannable rather than merely shorter.
    Header-less on purpose — `| | |` — because "Field" and "Value" name
    nothing a reader did not already know from the rows.
    A field with several values gets a real bulleted list inside its cell —
    `<ul>`, because a markdown table cell cannot hold a block-level list and
    Quartz passes raw HTML through (verified against v4.5.2: the markdown
    links inside the items are still parsed, and `CrawlLinks` still resolves
    them). One value renders plain: a one-item bullet is a bullet about
    nothing.
    The center dot is gone from both levels. It was separating peers inside a
    cell, which it did adequately, but a title after each code makes the items
    long enough that a line each is the only thing that reads.
    """

def record_line(meta: dict, source: Path, outbound, inbound, known: dict[[str, str]] | None) -> str
    """
    The frontmatter facts, rendered where a reader (and a graph) can see
    them: status, when it was filed, the issue, what influenced it, and the
    typed edges in and out of it.
    Composed with wikilinks and handed to the resolver rather than spelled
    here — the fixer owns every target in this record, and a second speller
    would be the drift DP-4 names.
    """

def _insert_after_title(body: str, line: str) -> str
    """
    Put the record line under the document's `# ` heading, or at the top
    when there isn't one. A superseded decision announces itself above the
    fold or not at all.
    """

def split_frontmatter(text: str) -> tuple[[str | None, str]]
    """
    (raw YAML, body). `None` for the YAML when there is no frontmatter —
    a generated view has none, and is copied through untouched.
    """

def _with_alias(front: str, alias: str | None) -> str

def landing_page(text: str, cfg) -> str
    """
    Give the README the name and the second address it needs as `index.md`.
    Two things break in the rename. A site derives a page's title from its
    frontmatter or its first heading, and a README that opens with a centred
    logo has neither — so the front page was titled `index`, after the file we
    renamed it to. And anything still pointing at `README.md` now points at a
    page that isn't there; the alias is what keeps that link answering.
    """

def _rebase(text: str, source: Path, cfg) -> str
    """
    Re-spell a document source's relative links for its own page.
    A design principle's prose is written to be read in the assembled view, so
    its targets resolve against `link_base` — `docs/` — not against the file's
    own directory. `../record/decisions.d/ADR-006.md` is correct there and
    wrong from `record/principles.d/`, which is where the page now lands.
    So the source stays exactly as it is in the repository, where the fixer and
    the lint both expect that spelling, and staging re-points each target on
    the way out. Publishing without this would trade one broken link for
    another, which is the failure it exists to prevent — and the reason it runs
    BEFORE `_retarget`, whose "does this leave the published set" question is
    only answerable once the path means what it says.
    Only relative targets move. A URL, an anchor-only link and a specimen
    inside a code span are all left alone, on the same rule the reference lint
    uses: code is quoted, not asserted.
    """

def _retarget(text: str, source: Path, cfg, published: set[Path], staged_assets: dict[[Path, Path]], report: Report) -> str
    """
    Send every relative link that leaves the published set somewhere real.
    An image is staged so it renders; anything else — a workflow, the scaffold,
    the licence — becomes a link at the repository, because the site is a view
    of the record and those files are the record's subject, not its pages.
    """

def brand(out: Path, cfg, report: Report) -> str
    """
    Stage the project's artwork and return the stylesheet that uses it.
    The icon is copied verbatim and rasterized by `actions/site` with the
    `sharp` the generator already depends on — so a project points at the
    vector master it maintains and nothing derived from it is ever committed
    to drift (DP-3).
    The logo is written twice, once per theme, because a stylesheet can switch
    on Quartz's toggle and an SVG's own media query cannot. Missing artwork is
    named rather than skipped in silence (DP-1).
    """

def stage(out: Path, cfg, nested: bool) -> Report
    """
    Write the vault and its config under `out`. Idempotent: the content
    directory is rebuilt from scratch, so a rename in the record cannot leave
    a stale page behind to be served forever.
    `nested` is what stops a nested record from staging its own — see
    `stage_nested`.
    """

def nested_records(cfg) -> list[Path]
    """
    Delegates to `Config.nested_records` — see there for the rules.
    Kept as a name in this module because the staging code reads better for
    it, and because the answer must be the one `luria index` uses: a record
    this publishes but nothing regenerates is the worst of both (DP-4).
    """

def stage_nested(content: Path, cfg, report: Report) -> None
    """
    Stage each nested record into `content/<its path>/`.
    The reason this exists rather than the parent simply publishing the files:
    a parent config cannot tell a source from a view inside a child. That test
    is `Config.link_base`, and it answers from the *reading* config's schemes —
    so under luria's own config an example's `VALUE-001.md` looks like ordinary
    prose, and `publishable()` would emit both the fragment and the assembled
    view it renders into. Each child is therefore staged by its own config,
    and only the finished `content/` is mounted.
    Two consequences worth stating.
    **The child's views are read, not built.** They are committed and
    regenerated by `luria index` alongside this project's own (ADR-078), so
    staging reads what is on disk — the same contract the parent runs on, where
    the Pages build follows the job that regenerates.
    **The child's own `include_records` is not honoured.** One level is a
    section; two is a maze, and nothing here needs it. Said out loud because
    the recursion would otherwise look like an oversight.
    """

def run(out: str) -> None
    """
    Stage the record as a Quartz vault — `content/` plus `quartz.config.yaml`
    — under OUT, ready for `npx quartz build`.
    """

def order(relation: str) -> tuple[[int, str]]

def cell(values: list[str]) -> str

def fix(match: Any) -> str

def fix(match: Any) -> str

```

## luria/slugs.py
```python
def text_of(heading: str) -> str
    """A heading's plain text: tags removed, the way a parser sees it."""

def slug(heading: str) -> str
    """
    The anchor for one heading, ignoring repeats. Use `Slugger` when a
    whole document's headings are being numbered.
    """

class Slugger
    """
    One document's headings, in order, with repeats disambiguated.
    `github-slugger` appends `-1`, `-2`, … to the SECOND and later
    occurrences of a slug, counting per document. Two entries titled "Notes"
    in one book is not hypothetical — a journal is exactly where it
    happens — and getting the suffix wrong is a link to the wrong entry,
    which is worse than a link to nothing.
    """

    def __init__(self) -> None

    def slug(self, heading: str) -> str


def headings(text: str) -> list[str]
    """
    Every heading's text, in document order, code fences skipped.
    In order because that is what a slug depends on: the second "Notes" in a
    document is `notes-1`, and a heading inside a shell example that got
    counted would shift every suffix after it. One implementation, because
    the generator and the check have to agree about what a heading is or the
    check is checking something else (ADR-100).
    """

def anchors_for(text: str) -> dict[[str, str]]
    """`{heading text: its slug}` for one document, in order."""

```

## luria/sources.py
```python
def normalize(title: str) -> str

class Identifier

    @property
    def key(self) -> str


def _field_line(text: str, field: str) -> int

def identifiers() -> list[Identifier]
    """
    Every document field that holds a remote identifier, with the title the
    document claims for it.
    """

def _title_url(remote, uid: str) -> str
    """
    The metadata URL for one identifier, or "" when the remote has not
    declared one. `uris.title` renders over the same vocabulary as `read`,
    with the uid's capture groups by position.
    """

def forget_refusals() -> None
    """
    Clear the per-run circuit breaker. For tests, and for a caller that
    runs more than one pass in one process.
    """

class Fetched

    @property
    def known(self) -> bool


def _retry_after(error) -> float | None
    """Seconds a 429/503 asked us to wait, when it said."""

def _once(url: str, pattern: str) -> Fetched

def _fetch(url: str, pattern: str) -> Fetched
    """
    Ask once, and wait only when the host said how long to wait.
    A 404 is an answer. A 429 is not an answer, and the previous version
    treated "not an answer" as "ask again soon" — three attempts, 3s then 6s.
    Under a sustained rate limit that is 9 seconds per identifier to arrive at
    the same `throttled` it already had after the first, and the caller pays it
    once per identifier (#250).
    `Retry-After` is different: a host that says when to come back has told us
    the request that will succeed, so a short one is honoured. A long one is
    not slept through — a build that blocks for two minutes on a metadata
    courtesy API is worse than a build that reports what it could not check.
    """

def ask(ident: 'Identifier') -> Fetched | None
    """
    Ask upstream what one identifier is, or None when the remote has not
    declared how to ask. The single place a socket is opened.
    A remote that has already refused during this run is not asked again: the
    breaker is here rather than in `resolve` so that every caller inherits it,
    including the lint's per-identifier check, where a sustained throttle
    otherwise costs a round trip for each unknown citation.
    """

def _queue(only: tuple[[str, Ellipsis]], known: dict) -> list['Identifier']
    """
    The identifiers to ask about, unsettled ones first.
    An identifier the lockfile has no entry for is one no run has ever
    settled — a new citation, or one a throttle cut a previous run off
    before. Asking those first is what makes an interrupted run make
    progress: the old order was the record's own, so a throttle partway
    through meant the same tail went unresolved run after run.
    Within each group the order is shuffled, so one identifier that always
    errors cannot sit at the head of the queue forever and spend the window
    on itself. That is also why the seed is not fixed.
    """

def resolve(only: tuple[[str, Ellipsis]]) -> list[str]
    """
    Fetch every identifier's title and record it in the lockfile.
    Returns one line per identifier that could not be settled. A `throttled`
    or `unreachable` answer is NOT written: an entry that says nothing is
    read later as agreement, so the absence has to stay an absence and be
    reported here instead.
    Three things make this survive a rate limit rather than be defeated by
    one (#250). Unsettled identifiers are asked first, so an interrupted run
    keeps the answers nobody had. What it learned is checkpointed as it goes,
    so a run that is throttled — or killed — keeps them. And a remote that
    refuses ends there: the courtesy pause between requests is the floor on
    this command's cost, and paying it 200 more times against a host that is
    saying no is how an eleven-minute command became one nobody ran.
    """

def state() -> dict[[str, dict[[str, str]]]]
    """What the committed lockfile says each identifier resolves to."""

def mismatch_lines() -> tuple[[list[str], list[str], list[str]]]
    """
    Identifiers that disagree with upstream, identifiers nothing has
    checked, and `source-ok:` directives that no longer acknowledge anything.
    The lockfile is a **cache with an endorsement in it**, not the boundary of
    what may be known. An identifier it has no answer for is the interesting
    case, not the exempt one: a citation is never more likely to be wrong than
    in the minutes after it is typed, and the first version of this check
    passed exactly then, because nothing had resolved it yet.
    So under `lint.network = "auto"` the lint asks about what it does
    not already know — normally the one citation a contribution added — and
    falls back to reporting it unchecked when it cannot. "never" answers only
    from the lockfile, for a hermetic build. "require" makes not being able to
    ask a finding, so a green CI run means the references were verified rather
    than remembered.
    """

```

## luria/statuses.py
```python
class Status
    """
    A status: one word from the closed vocabulary, the successor a
    superseded document names, and an optional prose note. Three fields,
    three types:
        status: Superseded
        superseded_by: FX-ADR-032
        status_note: the capital never burned after all
    The word is data, checked against the vocabulary. `superseded_by` is a
    reference — structure, checked and resolved like any declared
    reference, and the typed edge (ADR-071). The note is prose — a
    prose key like `summary:` (ADR-051): rendered, linked by the fixer,
    scanned for citations, for whatever the field cannot say. They used to
    share one scalar, `Superseded — by X`, split in six places with three
    spellings of one regex; that form is still read, reported by the lint,
    and moved by `luria repair`.
    """

    @property
    def display(self) -> str


def display(status: Status, link) -> str
    """
    `Superseded — by X; note`: the reading a status has always had,
    composed from the fields. `link` renders a successor's code the way
    the surface it lands on wants — a relative link in the index, a
    wikilink on the site — and bare codes are the default.
    """

def parse(raw) -> Status
    """The combined scalar — `Superseded — by ADR-035` — read apart."""

def successor_field(scheme) -> str
    """
    The field a retiring document names its replacement in. The scheme's
    where one is given, the default otherwise — this module is called from
    places that have no scheme in hand, and defaulting is the whole point.
    """

def of(meta: dict, scheme) -> Status
    """
    A document's status from its frontmatter, whichever form it wrote.
    `status_note:` wins when present; a note still riding in `status:` is
    read too, so nothing breaks between the field arriving and the file
    being moved. `scheme` says what the successor field is called; without
    one the default name is read, which is what every project not renaming
    it uses.
    """

def normalised(meta: dict) -> dict
    """
    `meta` with `status:` read apart into the three-field form.
    The legacy scalar `Superseded — by X; note` puts a qualifier inside the
    value, so the raw frontmatter is not the vocabulary value — which is
    what made `status` look like it needed a bespoke checker. Splitting it
    here, once, at the boundary where frontmatter is read for checking,
    means every generic consumer downstream sees a bare word and needs no
    idea that this field is different (#181).
    The combined form is still reported, by the check whose finding names
    the repair. This only stops it being reported twice.
    """

def combined(meta: dict) -> bool
    """True when `status:` still carries the note — the form to move."""

def set_status(text: str, value: str, note: str, superseded_by, scheme) -> str
    """
    The file text with its status written in the three-field form.
    The one writer of the fields, so the shape has one spelling: the
    migration's tombstone and the index's repair both come through here.
    Existing `status_note:` and `superseded_by:` blocks are replaced, never
    duplicated.
    """

def successor_in(note: str) -> str | None
    """
    The code an old-form `by CODE …` note opens with, or None.
    Read the way prose is read everywhere else — links unwrapped, then the
    scheme-driven finder (ADR-046). This is the repair's reader only: the
    relation itself lives in `superseded_by:`, and nothing infers it from
    prose at check time.
    """

def repair(text: str) -> str | None
    """
    A document's text brought to the three-field form, or None when it
    is there already: a note riding in `status:` moves to `status_note:`,
    and a Superseded document whose old-form note opens with `by CODE` gets
    `superseded_by:` — the note dropped when it said only that, kept
    verbatim when it said more. Reads the values through YAML rather than
    by eye, so a quoted multi-line note comes through intact.
    """

def split(text: str) -> str | None
    """
    Kept as the name the split was introduced under; `repair` is the
    whole operation.
    """

def populate(scheme) -> list
    """
    Bring every document to the three-field form — a source repair
    `luria repair` runs, like `created:` from a journal entry's path
    (ADR-031): the file already states the facts, and the tree is made to
    say so in the fields that carry them.
    """

def declared(scheme) -> dict[[str, dict]]
    """
    `{status: {label, blurb}}` as the scheme declares it, or `{}`.
    An empty mapping means "declares nothing", which is the default and leaves
    every check below inert — an unconfigured project must not be told it has a
    problem, and must not be told it is clean either.
    """

def vocabulary(scheme) -> tuple[[str, Ellipsis]]
    """
    The words this scheme's documents may use: its own if it declares
    any, the default five otherwise.
    Distinct from `declared()`, which stays "what the file says" — the legend
    renders only for a project that asked for one, and a default nobody wrote
    is not something to publish as though they had.
    """

def problems(scheme) -> list[str]
    """
    The one thing a declared vocabulary cannot leave out.
    The words are the project's now, but `active` is how every check decides
    what is in force — it is the role the whole citation apparatus rests on.
    A vocabulary omitting it means nothing is ever in force, which silences
    the retired-citation check completely while looking like a working
    configuration. That is the failure this guard exists for; inventing a
    word is not.
    """

def undeclared(scheme, status: str) -> bool
    """
    True when nothing is checking this scheme's status word.
    Not "the word is wrong" — that is the vocabulary's finding, raised with
    every other controlled field once the scheme declares one. This is the
    case a vocabulary cannot raise: its own absence. A scheme declaring no
    `status` field has no values, so every word passes and the check looks
    clean because it is not there (DP-15).
    Requiring the declaration is #181's second half; it breaks every record
    that predates it, so it ships with the command that writes one.
    """

def legend(scheme) -> str
    """
    The declared statuses as a markdown table, or `''` when none are.
    Rendered above the index table rather than behind a stub placeholder, so
    that adopting the file is enough to make the meaning visible. A legend
    nobody added a placeholder for is a legend nobody reads, which is the
    failure this exists to fix.
    """

def _observed(scheme) -> list[str]
    """Every record's status value in the scheme, trailing notes stripped."""

def spread(found: list[str]) -> str
    """
    `8 Proposed, 2 Superseded, 1 Deferred` — the tail behind a modal status.
    The finding is about a distribution, so the row has to show one. "Every
    record is Active" is a fact a reader can act on; "133/144 at Active" alone
    invites the reply that eleven exceptions exist, and naming them answers it
    in advance.
    """

def uniform(scheme) -> tuple[[str, int, int]] | None
    """
    `(modal status, its count, the total)` when the status field has
    stopped carrying information.
    A status field where every record agrees is indistinguishable from no
    status field, and the difference matters because other machinery reads it:
    `active` decides what counts as retired, and `retired-citations` fires off
    that. A scheme in this state has an enforcement mechanism that cannot fire,
    and the build is green *because* nothing is being judged (#104).
    "Every record" was the original test, on the argument that a corpus whose
    claims all survive is legitimate and so a single retirement proves the
    judgement is live. `uniform_share` is the dial that argument needs at
    scale: a scheme at 133/144 `Active` reads as a tracked attribute and
    behaves as a constant, and the eleven exceptions that silence the check
    are no evidence that the other 133 were ever examined. The default is
    1.0 — exactly the original rule — because lowering it is a claim about
    what a scheme is for, and that belongs to the project.
    `None` below the floor, for a scheme rendered as one document (a
    design-principles page where everything is in force is the expected state,
    not a smell), when the scheme declares a vocabulary of exactly one status,
    which is a project saying so on purpose, and when the scheme sets
    `uniform_ok` — the acknowledgement this finding lacked. See
    `acknowledged_rows` for where that reason surfaces instead.
    """

def uniform_rows() -> list[str]
    """One line per scheme whose status field carries no information."""

def acknowledged_rows() -> list[str]
    """
    One line per scheme whose uniformity a human has vouched for.
    The counterpart to `uniform_rows`. An acknowledged scheme is still
    uniform — nothing there is being judged, and the citation checks still
    cannot fire — so the fact does not stop being true when someone explains
    it. It stops being a *finding* and becomes a note, which is the same
    bargain `inactive-ok:` strikes at a citation site: the reason is
    mandatory, and it renders where the finding would have.
    """

```

## luria/syntax.py
```python
def available() -> bool
    """Whether a grammar backend is installed and switched on."""

class _Node(NamedTuple)
    """A node, as plain data. Nothing native survives past `_nodes`."""

    @property
    def size(self) -> int

    @property
    def end_line(self) -> int
        """
        The 1-based last line this node occupies.
        A node ending at column 0 has consumed the newline of the line before
        it and occupies nothing on the row tree-sitter reports.
        """


def _nodes(tree) -> list[_Node]
    """
    Every node in `tree`, converted to plain data in one pass.
    Read with a cursor and copied immediately, so that no live node outlives
    this function. That is the boundary the rest of the module is written
    against: a node is a view into memory the bindings own, a failure there is
    a segfault rather than an exception, and a segfault has no traceback and
    surfaces in whatever allocates next. Copying out is cheap — a lint reads
    every node exactly once — and it means only this function has to be right
    about lifetimes.
    """

def _parse(path: Path, text: str) -> list[_Node] | None
    """Every node in `path`, as plain data — or None for no opinion."""

def comments(path: Path, text: str) -> list[tuple[[int, int, str]]] | None
    """
    (line, character offset, body) for every comment, or None for no opinion.
    The shape matches `directives.comment_fragments`, which is the caller.
    """

def grow(path: Path, text: str, block: tuple[[int, int]], after: int) -> tuple[[int, int]]
    """
    `block`, extended to the syntactic unit it introduces.
    `after` is the line the directive itself sits on: the unit is what the
    directive *introduces*, so the search starts below it, and a directive
    that already stands above its block (`after` before it) starts at the
    block's own first line.
    The unit is the smallest named node with children that begins at that
    first line of content and holds the whole block. Smallest, because a
    top-level comment's next sibling is often the whole document, which would
    quietly turn `-block` into `-file`. Holding the whole block, because a
    node that stops inside it is part of the block, not the block. With
    children, because a leaf is a token: `f` in `f() {` and `int` in
    `int f(void)` both start in the right place and neither is a block.
    Returns `block` unchanged when there is no grammar, no such node, or
    nothing to add. It never returns a narrower span than it was given.
    """

def _first_content(lines: list[str], first: int, last: int) -> tuple[[int, int]] | None
    """
    The 0-based (row, column) where the block's content starts.
    Column, not just row: a node has to *begin* there to be the block's unit,
    and in an indented file the line's first non-space character is where that
    is.
    """

```

## luria/templates.py
```python
def _line_of(text: str, field: str) -> int
    """Where the field is written, so the finding is clickable."""

def rows() -> list[str]
    """One line per template that contradicts its scheme's contract."""

def _squash(value) -> str

def placeholders(scheme) -> dict[[str, str]]
    """
    What the scheme's form says in each prose field, whitespace squashed —
    the words a filed document must not still be saying. Empty when the
    scheme has no form.
    """

def form_text(scheme, meta: dict) -> list[str]
    """
    The prose keys of one document that still carry the form's own
    words. A template's `summary:` describes what a summary is for, so a
    document repeating it verbatim has not written one; the decision index
    then prints the instruction where the decision should be — which is how
    two Proposed decisions reached the published site saying "One-paragraph
    description of the decision". Always wrong, and the mechanical fix is to
    drop the key: an absent summary falls back to the title.
    """

```

## luria/upgrade.py
```python
class Upgrade
    """One version boundary, and what has to be true before it is deleted."""

def _statuses_yaml() -> str

def _schemes(raw: dict) -> dict[[str, dict]]

def _plan(root: Path) -> tuple[[list[tuple[[Path, str]]], list[str], list[str]]]
    """(files to write, config lines to append, notes) — nothing written."""

def _declared(text: str, prefixes: list[str], values: dict) -> str
    """
    `text` with `status` wired up for each scheme, and the vocabulary it
    names declared once.
    Written into the document rather than onto the end of it. YAML nests by
    indentation, so an appended `schemes.VP.statuses: x` is a key literally
    called "schemes.VP.statuses", and an appended indented block joins
    whichever top-level key happens to be last — both of them silent. The
    round trip is ruamel's, so the comments a project wrote in its own
    config come through it (ADR-098).
    """

def _prose(text: str, name: str, into: list[tuple[[tuple[[str, Ellipsis]], str]]]) -> str
    """
    Take a vocabulary file's comments off it, recording where each goes.
    Returns the text with nothing but values left, so what ruamel loads has
    no comment carrying a column from a file it is no longer in.
    """

def _moved(path: tuple[[str, Ellipsis]]) -> tuple[[str, Ellipsis]]

def _carry(doc, blocks: list[tuple[[tuple[[str, Ellipsis]], str]]]) -> list[str]
    """
    Write each block above the key it documented. Returns the prose that
    had nowhere to land, so the caller can print it rather than eat it.
    """

def convert_config(root: Path) -> tuple[[str, list[str], list[Path]]]
    """
    One `luria.yaml` from a TOML config and the vocabulary files beside
    each scheme's records: (the YAML, what it folded, what nothing reads now,
    what prose had nowhere to land).
    **Parsed with `tomllib` and written with `yaml`, never moved as bytes.**
    `uid = "(\d{4})[.:](\d{4,5})"` does not survive a copy — the two
    formats escape differently — so every value is re-encoded by a writer that
    knows its own rules. That is the only version of this that is safe, and
    the reason a regex in a `uid` is the thing to check afterwards.
    A vocabulary two schemes hold identical copies of becomes ONE entry they
    both name, which is the whole point of the boundary (ADR-098).
    **Comments are carried, because they are not values.** The re-encoding
    argument above is about escaping, and a comment has none: it is prose
    attached to a place, and `comment_carry` recovers the place. What a
    project wrote to explain its own config is the part of the config a
    reader needs most, and the first version of this dropped all of it.
    """

def _run_yaml(where: Path, dry_run: bool) -> None
    """
    The boundary crossing. Leaves the TOML on disk: deleting what you just
    converted, before anyone has read the result, is not a migration anybody
    should trust.
    """

def run(name: str) -> None
    """
    Write what a new version requires into a record that predates it.
    NAME is the upgrade to run; with none, the available ones are listed
    with what each is waiting on before it can be deleted.
    """

```

## luria/vocabularies.py
```python
def declared(values: dict | None) -> dict[[str, dict]]
    """
    `{value: {label, blurb}}` in declaration order, or `{}` when a scheme
    names no vocabulary.
    Takes the values rather than a path since ADR-098: a vocabulary is
    declared once under `vocabularies:` and referenced by name, so there is no
    longer a file per scheme to read — which is what let two schemes sharing
    one vocabulary drift apart in ten of thirteen entries.
    """

def label_of(meta: dict | None, value: str) -> str
    """
    What a view calls this value: its `label`, else the value itself.
    One fallback, because there were three — `tag.title()` in the tag pages,
    `""` in the status legend, and the raw value here — so a scheme declaring
    no `label` rendered an empty legend column but a title-cased tag heading
    (ADR-098).
    """

def _label(meta: dict, value: str) -> str

def _fields(scheme)
    """
    Every field whose values a view groups by: the scheme's declared
    vocabularies, and its axis even when the axis declares no vocabulary.
    `Scheme.grouped_fields` is the one answer — the same one the generator
    uses to decide which directories it owns (ADR-098).
    """

def _listing(scheme, docs) -> list[tuple[[str, object, object, dict[[str, list]]]]]
    """
    Per grouped field: (name, declaration or None, compiled field,
    {value: [docs]}) — the documents under each value by their *effective*
    values, so an entry with the field absent sits under the default.
    The values come in one order for every field: declared ones as the
    vocabulary declares them, then — for an OPEN field only — any value a
    document actually uses, alphabetically. Using a new value must never
    require a config change, which is the whole of what `tags` being open
    always meant; a closed field's unknown value is a finding instead, and
    giving it a page would be publishing the mistake.
    A field naming no vocabulary is open the same way, and for a plainer
    reason: there is no closed set for a value to fall outside of.
    """

def _noun(scheme) -> str

def _meta_of(vocab) -> dict[[str, dict]]

def index_blocks(scheme, docs) -> str
    """
    The `{categories}` block on a scheme's index: one block per grouped
    field, the axis first.
    Two shapes, and the scheme's own `axis:` chooses between them rather
    than the code knowing which field is special. The axis is the browsing
    surface, so its values list the documents under them; every other field
    is a row of chips with counts, because the value's own page already
    holds the table (ADR-098). One walk, one label rule, one blurb
    rule, one ordering rule — where there were two of each, and they had
    drifted.
    """

def pages(scheme, docs) -> dict[[Path, str]]
    """
    A page per value, at `<view>/<field>/<value>.md` — the axis's pages
    among them, on the same template.
    They were two templates: the axis's said "ADRs tagged `x`" and
    sentence-cased the blurb, every other field's named the field and
    rendered `**Label** — blurb`. Same directory, same table, same footer,
    two spellings of the heading and two of the blurb (ADR-098).
    """

```

## luria/yaml_edit.py
```python
def _rt() -> YAML

def load(text: str) -> Any

def dump(data: Any) -> str

def at(data: Any, path: tuple[[str, Ellipsis]]) -> Any | None
    """The mapping at `path`, or None if the document has no such place."""

def ensure(data: Any, path: tuple[[str, Ellipsis]]) -> Any
    """The mapping at `path`, creating the empty ones on the way."""

def merge_into(data: Any, extra: dict, path: tuple[[str, Ellipsis]]) -> Any
    """
    Fold `extra` into the document at `path`, keeping what is there.
    A deep merge rather than an assignment: setting `schemes` to a new mapping
    would silently drop every scheme the file already declared.
    """

def rename_key(data: Any, path: tuple[[str, Ellipsis]], old: str, new: str) -> bool
    """
    Rename one key of the mapping at `path`, in place, keeping its order.
    In place because order is content in a config a person reads, and because
    the comments attached to the key belong to it rather than to its position.
    Returns whether anything was renamed.
    """

def set_block(parent: Any, key: str, value: Any, before: str, indent: int) -> None
    """
    Add `key: value` to `parent`, with `before` as the comment above it.
    The comment goes through ruamel rather than into the text, so it lands
    above the key wherever the key lands — which is the whole difference
    between a generated block and a generated block in the right place.
    """

def keys(data: Any, path: tuple[[str, Ellipsis]]) -> Iterator[tuple[[tuple[[str, Ellipsis]], int, int]]]
    """
    (path, line, column) for every mapping key, in document order.
    Zero-based, as ruamel records them.
    """

def span(data: Any, path: tuple[[str, Ellipsis]]) -> tuple[[int, int | None]] | None
    """
    The half-open line range the entry at `path` occupies, or None.
    From its own line to the line the next entry at or outside its
    indentation starts on; `None` for the end means the end of the document.
    Line numbers rather than a subtree because the callers that need this
    are rewriting the *text* and need to know which lines are whose.
    """

def _deep(into: Any, more: dict) -> None

```

## tests/_config.py
```python
def _deep(into: dict, extra: dict) -> dict

def merged() -> str
    """One YAML document from several fragments, later parts winning."""

```

## tests/_scheme.py
```python
def decision(root: Path, number: int, status: str, title: str, summary: str, superseded_by) -> Path
    """
    File a decision where the *current* config's ADR scheme reads them.
    Derived rather than hardcoded, because the conventional location moved
    once already (`docs/decisions` → `record/decisions.d`, ADR-021) and a
    fixture that spells the path writes documents the scheme can't see —
    every test downstream then passes on an empty corpus.
    """

```

## tests/conftest.py
```python
def _repo_root(monkeypatch)
    """Pin the config to this repo unless a test overrides it."""

def project(tmp_path, monkeypatch)
    """A minimal but complete record, for tests that need a controlled tree."""

```

## tests/test_adr_index.py
```python
def test_relative_targets_are_rebased()

def test_absolute_and_anchor_targets_are_left_alone()
    """
    A URL, a root-relative path and a same-page anchor mean the same thing
    from any directory — rewriting them would break them.
    """

def test_no_prefix_is_a_no_op()
    """
    README.md renders from the ADRs' own directory, so its rows are the
    unmodified text — that's what kept the ADR-004 migration byte-identical.
    """

def test_row_rebases_summary_and_status_together(tmp_path, monkeypatch)
    """
    The row's own link was always rebased; the summary and the status note
    are prose rendered into the same row and need the same treatment. Four
    supersession links 404'd on the tag pages until this held.
    """

def test_every_generated_relative_link_resolves()
    """
    The property the rebasing exists for, checked against the real corpus.
    Covers every render — scheme views and journal books both go through
    `outputs()`.
    Code spans are skipped for the same reason the hyperlink lint skips them:
    a link inside backticks is a *quotation* of a link, and the devlog quotes
    several broken ones on purpose.
    A target resolves if it is on disk or is itself a view this render
    writes: a branch carries no regenerated views (ADR-068), so the
    book a new entry opens exists only in `outputs()` until `main` commits
    it.
    """

def value(root: Path, number: int, title: str, body: str) -> Path

def vp_scheme(root: Path) -> Scheme

def render(root: Path) -> str

def test_document_demotes_the_heading_and_renumbers(project)

def test_document_emits_a_stable_anchor(project)
    """
    Keyed to the number, not the wording — a principle is a living document
    and its heading moves (ADR-012).
    """

def test_document_strips_the_frontmatter(project)

def test_metadata_line_carries_version_and_origin(project)

def test_a_retired_principle_says_so(project)
    """
    `Active` is the silent default; anything else is stated, because a
    principle nobody believes any more is exactly what a reader needs told.
    """

def test_influenced_by_renders_as_a_followable_backlink(project)
    """
    Relative to where the text *renders* — `docs/`, not the fragment's own
    directory — which is the trap that caught two links in the first eight.
    Under the record layout the decision sources are a tree away (ADR-021),
    and the relpath is derived so this asserts the rule, not the location.
    """

def test_an_unresolvable_backlink_stays_a_bare_code(project)
    """DP-1: say what can be said, rather than linking to nothing."""

def test_outputs_covers_every_scheme(project, monkeypatch)
    """
    One `luria index`, every scheme — so the staleness check picks up a new
    scheme the moment it is configured, with no second command to remember.
    """

def test_filename_is_the_code(project)

def test_a_legacy_slug_filename_is_still_read(project)
    """
    Most projects arrive with `adr-010-some-title.md`, and refusing to read
    them would make adoption a rename-everything-first proposition. Luria
    writes the short form and reads both.
    """

def test_a_readme_is_not_a_document(project)
    """
    `README.md`, `README.stub`, `_template.md` and `tags.yaml` share the
    directory with the sources — the scheme's own filename rule is what tells
    them apart, and it is the only such rule in the package.
    """

def test_title_frontmatter_wins_over_the_heading(project)

def test_the_heading_is_the_fallback(project)
    """
    A project mid-adoption has decisions with no `title:` yet, and a blank
    index cell would be worse than a heading-derived one.
    """

def test_prefix_for_collocated_scheme_is_empty()
    """
    Unset `output` is the old layout — view beside sources — and its
    rendering must stay byte-identical, or every pre-record project's index
    goes stale on upgrade.
    """

def test_split_scheme_rows_link_into_the_source_tree(project, monkeypatch)
    """
    An index rendered away from its sources reaches back with a relative
    prefix — the row's own link, the summary's links and the status note all
    take the same one.
    """

def test_stub_lives_with_the_sources_and_renders_in_the_view(project)
    """
    The stub is authored, so it sits on the write side; the view directory
    holds only what the generator wrote (ADR-021).
    """

def test_orphans_reports_strays_in_every_view_dir(project)

def test_a_collocated_view_dir_is_not_policed(project)
    """
    With no separate `output` the scheme's directory holds the sources —
    calling every ADR an orphan would fail the entire pre-record layout.
    """

def test_a_pipe_in_a_summary_stays_one_cell(tmp_path, monkeypatch)
    """
    A literal `|` in a summary is a cell delimiter to the table parser: the
    row grows extra columns and the summary's tail lands in the status column
    (#14 — ADR-003's status vocabulary listing put 'Proposed' there). The
    renderer escapes, because a summary is prose and escaping is table syntax.
    """

def test_a_hand_escaped_pipe_is_not_double_escaped(tmp_path, monkeypatch)
    """
    An author who worked around #14 by writing `\|` in the source must not
    get `\\|` — a stray backslash and a broken row again. The escape
    normalises both spellings to one.
    """

def test_title_and_summary_are_separate_columns(tmp_path, monkeypatch)
    """
    The middle column used to be one blob — summary when present, else
    title — under a header that said "Title", so any document with a summary
    showed its summary mislabelled. Title now has its own column, and the
    summary cell is honestly empty when there is none, rather than a
    fallback papering over the gap.
    """

def _rfc_project(tmp_path, monkeypatch)
    """
    A project whose only index scheme is RFC, so the tag page has to name
    something other than this package's own vocabulary.
    """

def _axis_page(root, scheme, value: str) -> str

def test_an_axis_page_names_its_own_scheme_not_decisions(tmp_path, monkeypatch)
    """
    A project's RFC tag page should not be titled after this package's
    decisions — the same rule DEFAULT_STUB already states for the index.
    Rendered by `vocabularies.pages` since ADR-098: the axis's pages go
    through the same template as every other field's, into the same kind of
    directory, and `render_tag_page` was the second copy of it.
    """

def test_an_axis_page_blurb_keeps_its_casing(tmp_path, monkeypatch)
    """
    The old renderer sentence-cased the blurb with a hand-rolled
    `raw[:1].upper()`, because `str.capitalize()` lowercases everything
    after the first character and silently destroyed a blurb running to
    more than one sentence. The one template prints it as written.
    """

```

## tests/test_adr_pending.py
```python
def row(number, status, title, date, cites, unacknowledged)

def test_only_open_statuses_are_pending(project)
    """
    `Proposed` and `Deferred` are the two "not decided" states. `Rejected`
    and `Superseded` are decisions — they belong to the reference report.
    """

def test_oldest_first_and_undated_last()

def test_age_and_staleness()

def test_undated_decision_is_reported_not_dropped()
    """
    A decision with no `date:` can't be aged — which is itself a finding, so
    it is listed with `?` rather than quietly skipped.
    """

def test_headline_counts_are_real()

def test_empty_corpus_says_so()

def test_citation_counts_come_from_the_reference_scan(project)
    """
    The second axis: an old proposal nothing cites is a stalled idea; one the
    codebase cites everywhere is a decision already made in code.
    """

def test_headline_reconciles_with_the_reference_report(project)
    """
    Side by side the two counts read as an off-by-one. They are not: the
    reference report lists only decisions with an *unacknowledged* citation.
    """

def test_report_never_fails_the_build()

def test_every_scheme_is_covered(project)
    """
    A `Proposed` principle is an open question exactly as a decision is, and
    a report covering one scheme goes blind the day a second is configured
    (ADR-018).
    """

```

## tests/test_alias_inference.py
```python
def write(root: Path, rel: str, text: str) -> Path

def project(tmp_path, monkeypatch, alias: str) -> Path

def note(root: Path, number: int) -> Path

def scheme()

def test_the_alias_renders_from_the_document(tmp_path, monkeypatch)

def test_a_template_naming_a_missing_field_renders_nothing(tmp_path, monkeypatch)
    """
    Half a spelling would resolve for some documents and not others, with
    nothing saying which — so a template that cannot be filled yields none.
    """

def test_no_template_means_no_derived_aliases(tmp_path, monkeypatch)

def test_correcting_the_source_moves_the_alias(tmp_path, monkeypatch)
    """
    Recomputed, therefore always true — and therefore the old spelling
    stops resolving, which is why `formerly:` has to catch it.
    """

def test_a_superseded_spelling_kept_in_formerly_still_resolves(tmp_path, monkeypatch)

def test_a_real_code_outranks_another_document_s_nickname(tmp_path, monkeypatch)
    """
    A document's own name wins: an alias that happens to spell a code
    must never shadow the document that code belongs to.
    """

def test_an_alias_resolves_like_the_code(tmp_path, monkeypatch)

def test_a_shape_that_resolves_to_nothing_is_not_a_reference(tmp_path, monkeypatch)
    """
    The precision rule: the map decides, not the pattern. Otherwise a
    widened tail would start matching prose.
    """

def test_the_fixer_leaves_a_derived_alias_written(tmp_path, monkeypatch)
    """
    The whole point. Canonicalizing here would erase the readable
    identifier on the first `luria link --fix`.
    """

def test_the_fixer_still_upgrades_a_past_spelling(tmp_path, monkeypatch)
    """
    The opposite instruction, over the same map — which is why an entry
    carries its kind rather than the caller guessing from shape.
    """

def test_two_documents_on_one_spelling_is_a_violation(tmp_path, monkeypatch)

def test_the_number_makes_collisions_impossible(tmp_path, monkeypatch)

def test_a_template_without_the_prefix_is_refused(tmp_path, monkeypatch)
    """
    Every scanner finds a code by its prefix first, so a spelling without
    one is unreachable however well it resolves.
    """

def test_an_unrenderable_template_is_refused(tmp_path, monkeypatch)

def _git(root)

def committed_project(tmp_path, monkeypatch)

def test_a_changed_source_field_retires_the_old_spelling(tmp_path, monkeypatch)
    """
    The old spelling comes from git rather than a stored ledger: the
    previous frontmatter is already written down, so recording each rendered
    alias in the document too would be a copy per revision.
    """

def test_the_retirement_is_idempotent(tmp_path, monkeypatch)

def test_an_unchanged_alias_retires_nothing(tmp_path, monkeypatch)

def test_a_document_with_no_history_retires_nothing(tmp_path, monkeypatch)
    """
    Absence of history is not a change of spelling. A repair that guessed
    here would write a `formerly:` naming something that never existed.
    """

def test_no_template_means_no_retirement(tmp_path, monkeypatch)

```

## tests/test_anchors.py
```python
def attrs(html: str) -> list[str]

def test_a_journal_book_anchors_its_entries_by_id(project, monkeypatch)
    """
    55 links in one book of this project's own devlog, every one of them
    landing at the top of the page on the published site.
    """

def test_an_assembled_documents_anchors_are_ids(project, monkeypatch)
    """
    The same fix on the other emitter: a `render = "document"` scheme
    gives each source an anchor in the page it assembles into, and a citation
    with `cite = "view"` points at it.
    """

def test_an_anchor_reachable_only_by_name_is_a_finding(project, monkeypatch)
    """
    A hand-written `<a name=>` in prose somebody links to. The generator
    cannot be the only thing that knows this rule, or the next hand-written
    anchor puts the bug back.
    """

def test_an_anchor_that_is_an_id_is_silent(project, monkeypatch)

def test_a_fragment_naming_a_heading_is_silent(project, monkeypatch)
    """
    A heading gets an `id` from every renderer there is. Only an explicit
    anchor can be addressable in one place and not another.
    """

def test_the_fixer_rewrites_the_anchor_it_named(project, monkeypatch)
    """
    `--fix` repairs the TARGET, because that is where the defect is: the
    link is spelled correctly and the thing it names cannot be found.
    """

def test_a_stale_committed_view_is_not_a_finding(project, monkeypatch)
    """
    The regression CI found. A branch carries the DEFAULT branch's copies
    of every view and deliberately does not update them (ADR-018), so a
    check that read them failed every pull request touching an anchor and
    named a repair the author was not allowed to make. The question is about
    this source tree: what will the views it renders contain?
    """

def test_an_anchor_that_reaches_a_view_through_a_stub_is_a_finding(project, monkeypatch)
    """
    A stub is the hand-written part of a generated page, so an anchor
    written there lands in a view the same way the generator's does — and is
    the one case where a person, not the generator, owns the repair. The
    finding names the stub, which is the file they can edit.
    """

def _extend(root: Path, extra: dict) -> None

def _journal_project(root: Path, monkeypatch) -> Path

def _document_project(root: Path, monkeypatch) -> Path

def _linked_pair(root: Path, monkeypatch, anchor: str, frag: str) -> Path

def test_a_fragment_that_names_no_heading_and_no_id_is_a_finding(project, monkeypatch)

def test_a_reworded_heading_is_what_this_catches(project, monkeypatch)
    """
    The fragility the slug switch buys, made loud. A contents list links
    the heading; somebody rewords the heading; the link goes nowhere and
    nothing else in the record would have said so.
    """

def test_a_fragment_naming_a_heading_that_is_there_is_silent(project, monkeypatch)

def test_a_link_into_a_file_this_record_does_not_own_is_not_a_finding(project, monkeypatch)
    """Reporting every one of those would bury the ones that are ours."""

def test_a_books_contents_links_the_heading_not_the_timestamp(project, monkeypatch)
    """
    Both addresses resolve. Only one is the one the page hands a reader —
    Quartz puts its ¶ anchor and its own sidebar TOC on the heading — and a
    contents list pointing somewhere else is two addresses for one entry.
    """

def test_the_journal_index_links_the_same_anchor_as_the_book(project, monkeypatch)

def test_an_entry_body_heading_shifts_the_slugs_after_it(project, monkeypatch)
    """
    Why the slug is computed over the whole book rather than off the
    titles: a heading inside one entry's body consumes a slug, and a later
    entry with the same title is `-1`, not the bare one.
    """

```

## tests/test_axis.py
```python
def project(tmp_path, monkeypatch, scheme_keys: str) -> Path

def test_an_open_vocabulary_accepts_a_value_it_does_not_declare()
    """
    The reason `tags` could not be a vocabulary before. A project
    declares the values it has an opinion about — order, label, blurb — and
    reaching for a new one stays an edit to a document.
    """

def test_an_undeclared_value_on_an_open_field_is_not_a_finding(tmp_path, monkeypatch)

def test_the_same_value_on_a_closed_field_is_a_finding(tmp_path, monkeypatch)
    """
    Closed is still the default and still checked — `closed: false` opens
    one field, not the mechanism.
    """

def test_a_scheme_may_head_its_index_with_a_field_that_is_not_tags(tmp_path, monkeypatch)
    """
    The payoff. A world-bible's axis is `worlds`, and nothing in the code
    has an opinion about which word that is: the pages land under the
    field's own name, and the index groups by it.
    """

def test_a_scheme_with_no_axis_renders_no_categories(tmp_path, monkeypatch)
    """
    And is not told it is missing any. A scheme that declares no taxonomy
    has none — which the old code could not express, because every scheme
    had `tags` whether it wanted one or not.
    """

def test_an_axis_must_name_a_field_the_scheme_declares(tmp_path, monkeypatch)
    """
    Eagerly, like every other declaration: an axis pointing at nothing
    renders an empty categories block, and an empty one is indistinguishable
    from a correct one.
    """

def test_a_scheme_level_tags_key_says_where_the_vocabulary_goes(tmp_path, monkeypatch)

def test_a_scheme_level_tag_groups_key_says_where_the_groups_go(tmp_path, monkeypatch)
    """
    A group constrains a subset of ONE field's values, so it is declared
    under that field — which is also what lets a scheme group two different
    fields, where `schemes.X.tag_groups` could only ever mean `tags`.
    """

def test_a_group_names_the_field_it_constrains(tmp_path, monkeypatch)

def test_a_group_reads_its_own_field_not_a_key_called_tags(tmp_path, monkeypatch)
    """
    The bug this shape removes: the check read `meta["tags"]` whatever
    the group was about, so a group on any other field saw nothing and
    passed every document.
    """

def test_the_axis_heads_the_index_whatever_order_the_fields_are_in(tmp_path, monkeypatch)
    """
    `fields:` is written in whatever order reads best, which is not an
    answer about which taxonomy comes first.
    """

def test_both_kinds_of_page_come_off_one_template(tmp_path, monkeypatch)
    """
    The axis's page and another field's differ in the field they name and
    nothing else — where they used to differ in the heading, the blurb, and
    which module wrote them.
    """

def test_an_open_fields_undeclared_value_gets_a_row_and_a_page(tmp_path, monkeypatch)
    """
    It always did on the axis and never did anywhere else, because the two
    renderers answered this differently. One walk, one answer — and `closed`
    is what decides it.
    """

def test_a_closed_fields_unknown_value_gets_neither(tmp_path, monkeypatch)
    """
    Publishing a page for it would be publishing the mistake — the lint
    is already reporting the value.
    """

def test_a_declared_value_nobody_uses_still_has_a_row_and_a_page(tmp_path, monkeypatch)
    """
    The vocabulary says the value exists, and `(0)` is the useful thing to
    know about it. The row carries no colon, because there is no list of
    documents to introduce.
    """

def test_grouped_fields_is_the_one_answer(tmp_path, monkeypatch)
    """
    Three places need it — which directories the generator owns, which
    are exempt from the docs index, and which paths are generated — and a
    fourth disagreeing with them is how a page becomes an orphan.
    """

```

## tests/test_badges.py
```python
def principle(root: Path, number: int, status: str, title: str) -> Path

def with_schemes(project) -> None

def test_a_settled_record_counts_zero(project)

def test_proposed_and_deferred_both_need_a_decision(project)
    """
    Two statuses, one question: "we haven't decided" and "we decided not to
    decide yet" are both open (ADR-003).
    """

def test_every_scheme_is_counted(project)
    """
    "All reachable schemes" is the point: a `Proposed` principle is an open
    question exactly as a decision is.
    """

def test_a_retired_document_counts_only_while_cited(project)
    """
    The number is *cited* but retired. A superseded decision nothing points
    at is history, not a problem.
    """

def test_an_acknowledged_citation_does_not_count(project)
    """
    Citing a retired decision is often right, and the whole point of the
    acknowledgement is that the considered ones stop being noise (ADR-035).
    """

def test_zero_is_green_and_nonzero_is_amber(project)
    """
    Neither number is a failure, so neither goes red — "look at this", not
    "you broke it".
    """

def test_rewrite_replaces_only_the_region(project)

def test_a_project_without_a_region_is_left_alone(project)
    """
    Not everyone wants badges, and a tool that edits a README nobody asked
    it to edit is a tool people stop running.
    """

def test_rewriting_twice_changes_nothing(project)
    """
    Idempotence is what makes the staleness check meaningful — otherwise
    every run would report the previous run's output as stale.
    """

```

## tests/test_chains.py
```python
def write(root: Path, rel: str, text: str) -> Path

def project(tmp_path, monkeypatch, extra: str) -> Path

def note(root: Path, number: int, title: str) -> Path

def test_a_line_is_ordered_oldest_first(tmp_path, monkeypatch)

def test_a_document_in_no_relation_is_in_no_chain(tmp_path, monkeypatch)

def test_two_lines_are_two_chains(tmp_path, monkeypatch)

def test_a_branch_keeps_both_successors(tmp_path, monkeypatch)
    """A line is a DAG, not a list: two papers can replace the same one."""

def test_a_sibling_joins_the_chain_without_joining_the_spine(tmp_path, monkeypatch)
    """A rival that extends nothing is still part of the story."""

def test_a_chain_of_siblings_alone_still_renders(tmp_path, monkeypatch)
    """
    Two papers that only compare themselves to each other are a
    comparison, which is the fact the field exists to record.
    """

def test_a_cycle_is_a_finding(tmp_path, monkeypatch)

def test_a_cycle_does_not_crash_the_walk(tmp_path, monkeypatch)
    """A finding is not an excuse to render nothing (DP-15)."""

def test_a_one_sided_relation_is_not_this_check_s_business(tmp_path, monkeypatch)
    """
    It moved to `relations.py` (#178). A declared pair is one-sided or it
    is not, whether or not a chain walks it — so the finding belongs to the
    relation, and `broken-chains` keeps only what is about the sequence.
    """

def test_a_two_sided_comparison_is_clean(tmp_path, monkeypatch)

def test_succession_is_not_expected_to_be_symmetric(tmp_path, monkeypatch)

def test_no_sibling_relation_declared_means_no_symmetry_finding(tmp_path, monkeypatch)

def test_the_page_is_generated_and_stamped(tmp_path, monkeypatch)

def test_the_page_shows_status_so_a_retired_step_reads_as_one(tmp_path, monkeypatch)

def test_every_rendered_target_resolves(tmp_path, monkeypatch)
    """
    The first version linked into the scheme's *view* directory, which for
    an index-rendered scheme holds a README and tag pages and never a page
    per document — so every link on the page resolved to nothing, and no
    fixture noticed until a real corpus did.
    """

def test_a_project_declaring_no_chains_renders_nothing(tmp_path, monkeypatch)

def test_an_undeclared_relation_is_a_config_error(tmp_path, monkeypatch)
    """
    A chain over a field the scheme does not declare a reference would
    render nothing, and nothing is indistinguishable from current (DP-15).
    """

def test_a_chain_over_an_undeclared_scheme_is_a_config_error(tmp_path, monkeypatch)

def test_the_class_is_promotable_and_wired(tmp_path, monkeypatch)

def test_the_page_is_part_of_the_generated_views(tmp_path, monkeypatch)
    """
    `luria index --check` has to compare it, or a stale chain page ships
    looking current.
    """

def test_only_the_status_value_is_rendered(tmp_path, monkeypatch)
    """
    `status`, `superseded_by` and `status_note` are three fields, and the
    composed display form is one reading of them. This page wants the value:
    the successor is the next line, and the note is the argument this view
    leaves on the document. Rendering the composed form also dragged a link
    authored in the source's frame onto a page that renders elsewhere.
    """

def test_the_page_is_not_a_citing_site(tmp_path, monkeypatch)
    """
    A chain's job is to show the line *including* its retired steps, so
    scanning it would report every superseded document in every chain — at a
    site the reader must not edit, in a file the next build overwrites.
    """

def test_a_relation_naming_a_retired_step_is_not_a_citation(tmp_path, monkeypatch)
    """
    A successor's predecessor is superseded by construction. Reading
    `extends:` as a citation hands back one finding per retired step in every
    chain, at the field whose whole job is to name it.
    """

def test_prose_naming_a_retired_step_is_still_a_citation(tmp_path, monkeypatch)
    """
    Only the field is exempt. A paragraph pointing at a retired document
    is the finding this record adopted the check to get.
    """

def _showing(tmp_path, monkeypatch)

def _note(root, number, title)

def test_a_step_shows_each_named_field(tmp_path, monkeypatch)

def test_the_default_is_shown_like_any_other_value(tmp_path, monkeypatch)
    """
    ADR-076: a field with a default is never absent, so a step that says
    nothing still has a value, and hiding it would make the page disagree
    with the record.
    """

def test_nothing_declared_renders_status_alone(tmp_path, monkeypatch)

def test_showing_a_field_the_scheme_does_not_declare_is_a_config_error(tmp_path, monkeypatch)
    """
    Same reason a chain over an undeclared relation is: it would render
    nothing, and nothing looks exactly like correct (DP-15).
    """

def test_facet_by_names_every_axis_including_status(tmp_path, monkeypatch)
    """
    `status` has no privileged place on this page.
    It rendered implicitly before, with `facet_by` naming "the other one" —
    which made the chain the last thing still treating `status` as a
    built-in axis after #181 made it a declared vocabulary like any other.
    The chain names what it shows; `status` is in that list or it is not.
    """

def test_facet_by_defaults_to_status_alone(tmp_path, monkeypatch)
    """So a chain that says nothing renders what it always rendered."""

def test_a_scalar_facet_by_still_reads(tmp_path, monkeypatch)
    """One field is a list of one, written the shorter way."""

def test_a_facet_naming_nothing_is_refused(tmp_path, monkeypatch)

def test_two_roots_in_one_group_each_keep_their_own_child(tmp_path, monkeypatch)
    """
    Two roots join one group through a shared descendant. The page
    indents by depth, so if the order is not anchored to each node's parent
    a child lands under whichever root happened to sort last — asserting a
    descent nobody declared.
    """

def test_a_child_follows_its_parent_not_its_parent_s_sibling(tmp_path, monkeypatch)
    """
    The shape that broke the anthology's Mamba line: two siblings at one
    depth, and the child of the *first* rendered under the second.
    """

def test_a_second_parent_is_named_rather_than_dropped(tmp_path, monkeypatch)
    """
    A node renders under one parent. The other edge is true and must not
    vanish from the page just because the layout is a tree.
    """

def test_a_spine_of_two_relations_is_one_line(tmp_path, monkeypatch)

def test_a_second_spine_relation_nests_like_the_first(tmp_path, monkeypatch)

def test_a_scalar_relation_still_reads(tmp_path, monkeypatch)

def test_the_header_names_every_spine_relation(tmp_path, monkeypatch)

def test_a_spine_relation_the_scheme_does_not_declare_is_refused(tmp_path, monkeypatch)

def test_a_cycle_across_two_spine_relations_is_a_finding(tmp_path, monkeypatch)

```

## tests/test_ci.py
```python
def _no_ambient_ci(monkeypatch)
    """
    The suite itself runs in CI, so every var must be cleared per-test or
    these assertions read the runner's environment instead of the fixture's —
    a test that passes locally and inverts on GitHub Actions.
    """

def test_a_bare_shell_is_not_ci()

def test_any_known_variable_is_enough(monkeypatch, var)
    """
    Every vendor gets its own name, so dropping the generic `CI` doesn't
    silently take the advice with it.
    """

def test_a_runner_saying_not_a_build_is_believed(monkeypatch, value)
    """Some runners export CI=false to mean exactly that."""

def test_a_terminal_gets_the_bare_command()
    """
    In a working copy the command *is* the whole answer; padding it with CI
    advice would train people to skim the one message that matters.
    """

def test_ci_is_offered_both_ways_to_commit(monkeypatch)
    """
    The remedy must not steer people away from automating regeneration —
    that was this decision's rejected first draft, and it outlaws generation
    jobs. Both legitimate routes get named (ADR-029).
    """

def test_ci_warns_against_the_shape_that_commits_nothing(monkeypatch)
    """
    The broken shape is specifically 'generator in the checking job on the
    default branch, output committed by nobody' — not 'a generator ran in
    CI', and not a branch, which carries no view of its own (ADR-068).
    """

def test_the_remedy_never_forbids_generating_in_ci(monkeypatch)
    """
    A guard on the correction, since the wrong version reads perfectly well
    and would sail through review a second time.
    """

def test_the_remedy_names_the_command_it_was_given(monkeypatch)

def test_the_staleness_check_carries_the_ci_remedy(monkeypatch, project, capsys)
    """
    The integration that matters: this is the exact string an adopter reads
    in a build log when the index goes stale, and the reason they reached for
    the wrong fix. `luria index --check` is where it is read now — the lint
    asks no staleness question (ADR-068).
    """

def test_bare_badges_says_it_only_printed(capsys, monkeypatch, project)
    """
    Bare `python -m luria.badges` exits 0 having written nothing. Printing
    the markdown is legitimate; looking like a write is not (DP-1). The
    `luria badges` command itself is retired (ADR-030), so only the module
    entry point can reach this.
    """

```

## tests/test_citation.py
```python
def cited(project)

def test_a_person_renders_family_then_given(cited)

def test_an_entity_author_is_braced(cited)
    """
    BibTeX splits an unbraced name on the last space, which turns a lab
    into a surname.
    """

def test_several_authors_join_with_and(cited)

def test_the_key_is_the_surname_and_the_first_title_word(cited)
    """
    A slice of the title produced `luriaprojectmemoryk`, which is a key
    nobody would type twice.
    """

def test_the_key_does_not_move_with_the_version(cited)
    """
    A key that changed per release would break every bibliography that had
    already used it.
    """

def test_a_release_date_becomes_the_year(cited)

def test_the_repository_wins_over_a_docs_url(cited)
    """One `url` in BibTeX, and for software it is where the source is."""

def test_no_cff_renders_nothing(project)

def test_unreadable_yaml_renders_nothing_rather_than_half(cited)

def test_the_region_says_so_when_there_is_no_source(project)

def test_rewrite_fills_the_region(cited)

def test_a_readme_without_a_region_is_left_alone(cited)
    """
    A project that has not opted in is not nagged — the same bargain the
    badge region makes.
    """

def test_a_stale_region_is_reported(cited)

def test_a_fresh_region_is_not(cited)

def build(cff, readme)

```

## tests/test_cite_targets.py
```python
def _document_record(root: Path, extra: dict | None) -> Path

def test_a_published_record_is_silent(project)

def test_excluding_the_sources_is_a_finding(project)
    """
    The config asks for durable citations and the publishing rules
    withhold the thing they resolve to.
    """

def test_citing_the_view_instead_is_silent(project)
    """
    `cite = "view"` resolves to an anchor luria emits into the assembled
    page, which is published whether or not the sources are.
    """

def test_a_record_that_publishes_nothing_is_silent(project)
    """
    Nothing resolves anywhere, so the two settings do not disagree —
    there is only one of them.
    """

def test_the_class_can_be_enforced(project)
    """
    A warning by default: a record may publish a subset deliberately and
    this cannot tell. Naming it in `fail_on` makes it fatal (ADR-035).
    """

```

## tests/test_cli.py
```python
def test_every_command_is_registered()

def _luria() -> Any

def test_an_unknown_command_refuses_with_the_list()

def test_help_derives_from_the_functions()

def test_a_failing_gate_exits_nonzero(tmp_path, monkeypatch)
    """
    `luria lint` as a CI gate: SystemExit must survive Fire — Fire prints
    return values, so an exit code can never be a return value.
    """

```

## tests/test_collect.py
```python
def test_append_lands_before_the_marker_oldest_first()

def test_changelog_batch_lands_after_the_marker_newest_first()

def test_changelog_batches_stack_newest_first()

def test_a_stub_only_batch_emits_no_date_heading()
    """
    The failure this prevents was documented as a caveat under scriv: a
    collection round of only no-user-facing-changes stubs left a bare date
    heading behind, which somebody then had to revert by hand.
    """

def test_stubs_are_dropped_from_a_mixed_batch()

def test_changelog_style_with_marker_at_eof_keeps_a_final_newline()

```

## tests/test_concretize.py
```python
def merge_project(tmp_path, monkeypatch)
    """
    A record whose ADR scheme allocates at merge, with two temporary
    documents that cite each other — one bare, one wikilinked.
    """

def lint_errors() -> list[str]

def test_prose_that_merely_resembles_a_code_is_not_a_reference(merge_project)
    """
    The sentinel is also a false-positive guard: the first temp shape
    (any six alphanumerics starting with a letter) read "the ADR-review
    process" as a temporary reference, because `review` is six letters.
    """

def test_a_minted_code_can_never_be_read_as_a_number(merge_project)

def test_temp_documents_are_first_class_on_the_branch(merge_project)
    """
    Indexed, linted, and their citations demanded and linkable — the whole
    point is that a branch can write against the document it just filed.
    """

def test_concretize_assigns_renames_rewrites_and_aliases(merge_project)

def test_an_aliased_code_resolves_forever(merge_project)
    """
    The citation the rewriter can't reach — a PR thread, a commit message
    — must keep resolving after concretization: an old name, never a dead
    one.
    """

def test_check_guards_the_trunk(merge_project)
    """
    A temporary code on main is always wrong and mechanically fixable, so
    it fails — ADR-035's bar for a failing check.
    """

def test_concretize_rewrites_history_too(merge_project)
    """
    The sweep is full — journals included (ADR-040's second commitment,
    adopted by ADR-049 on review): "temporary" is relative to the record, so
    wherever the tree can be rewritten to the canonical ID, it is. After a
    run exactly one spelling of each code exists in the tree; git guards
    what was actually written, and the alias serves the citations that live
    outside the tree.
    """

def test_filing_allocation_is_untouched(project)
    """
    The default dial: a scheme without `allocate = "merge"` still numbers
    at creation, exactly as before.
    """

def test_a_legacy_spelling_is_reported_and_upgraded(merge_project)
    """
    An in-flight branch merges after a concretization pass, still citing
    the old temporary name. The warning names it with its remedy, and the
    fixer upgrades the *spelling* to the canonical code rather than
    engraving the old name into a fresh link.
    """

def test_a_live_temp_code_is_not_a_legacy_spelling(merge_project)
    """
    Before concretization, temporary codes are the branch's normal state —
    the warning is for spellings a sweep has already retired.
    """

def test_the_warning_is_promotable(merge_project, monkeypatch)
    """`legacy-spellings` rides the ADR-035 ladder like every other class."""

```

## tests/test_config.py
```python
def load_text(tmp_path, text)

def test_a_declared_family_replaces_the_default(tmp_path)

def test_an_undeclared_family_keeps_the_default(tmp_path)

def test_a_declared_scheme_key_is_unset_by_omission(tmp_path)
    """
    The sharp edge the old rule had: `output` inherited `docs/decisions`
    from the default ADR entry, so the documented way to keep an existing
    layout silently relocated the index.
    """

def test_settings_tables_still_merge_per_key(tmp_path)
    """
    `paths` is Luria's vocabulary, not the project's — setting one key must
    not clear the others, or every partial override becomes a broken config.
    """

def test_declaring_journals_does_not_touch_schemes(tmp_path)
    """Replacement is per family: each table is judged on its own presence."""

```

## tests/test_config_consumers.py
```python
def _consumers() -> dict[[str, list[str]]]
    """Each `Site` field → the modules that read it off a `site` receiver."""

def test_every_site_setting_is_read_by_something()

def test_the_check_can_tell_a_read_field_from_an_unread_one()
    """
    The positive control. `_consumers()` returning "everything is fine"
    because its pattern matches nothing is the failure mode that would make
    the test above worthless, so prove the instrument moves: a field that is
    genuinely read is found, and an invented one is not.
    """

```

## tests/test_config_doc.py
```python
def test_renders_a_page_with_every_section()

def test_every_public_field_of_every_config_dataclass_has_a_row(cls)
    """
    The guarantee, stated once per schema class.
    Not "the fields I listed appear" — *every* field, read from the class at
    render time. Add one to `Site` and this test starts covering it with no
    edit here, which is the same mechanism that puts it on the page.
    """

def test_a_new_field_appears_without_touching_the_renderer()
    """
    The load-bearing claim, fired directly.
    `rows()` reads `dataclasses.fields()`, so a class it has never seen
    renders anyway. If this ever fails, the module has grown a hand-maintained
    list and the whole design is void.
    """

def test_private_fields_are_not_documented()
    """`_root` and `_raw` are plumbing, not keys anyone writes."""

def test_union_types_do_not_break_the_table()
    """
    `Path | None` carries markdown's own column separator.
    Unescaped, the row silently becomes four columns and every row under it
    shifts — the kind of break that renders as a slightly wrong table rather
    than an error.
    """

def test_keys_luria_fills_itself_are_not_labelled_required()
    """
    A prefix comes from the table's name; a site title derives from
    `issue_url`. Calling either "required" sends a reader looking for a key
    to write that does not exist.
    """

def test_defaults_are_the_schema_not_this_repos_config()
    """
    `output` is unset for a scheme you add, whatever this repo sets for its
    own ADRs. Reading the shipped `luria.yaml` here would document a default
    that does not exist.
    """

def test_indented_examples_become_fenced_blocks()

def test_page_is_registered_as_generated()
    """
    Which is what keeps the bare-reference lint off a page made of example
    codes, and keeps `luria link --fix` from rewriting them.
    """

def test_renders_into_the_index_alongside_every_other_view()

def test_outputs_can_be_redirected(tmp_path)

def test_render_is_deterministic()
    """
    A committed view checked for staleness must be a pure function of the
    schema — nothing clock-dependent, or it goes stale at midnight.
    """

def test_states_what_is_not_configurable()
    """A reference that lists only dials reads as though everything is one."""

def test_this_repo_owns_the_schema()
    """
    The positive case has to be asserted somewhere, or the gate could be
    stuck closed and every other test here would still pass.
    """

def test_an_adopting_project_does_not_own_the_schema(project)
    """
    A project that installed the package has no `luria/config.py` of its
    own, so the reference would be a vendored copy of somebody else's file —
    already a release out of date, with nothing in their repository
    responsible for it.
    """

def test_the_reference_is_not_a_view_in_an_adopting_project(project)

def test_the_record_description_is_a_view_in_both(project)
    """
    The other half of the split: the page that *is* about their project
    renders everywhere, including here.
    """

def test_retire_removes_a_reference_luria_wrote(project)
    """
    The upgrade path. Before ADR-059 the page rendered into every adopting
    project, so a bump leaves one behind that nothing will ever update.
    """

def test_retire_leaves_a_page_the_project_wrote_itself(project)
    """
    Deleting a file in somebody else's repository wants a better reason
    than "we stopped writing it". The generator's marker is the proof, and
    prose that happens to share the name is not ours to remove.
    """

def test_retire_never_touches_the_reference_where_it_belongs()
    """
    Here, the page is the deliverable — a cleanup that removed it would be
    a generator deleting its own output.
    """

```

## tests/test_contract.py
```python
def write(root: Path, rel: str, text: str) -> Path

def doc(root: Path, rel: str) -> Path

def project(tmp_path, monkeypatch, sota_extra: str | dict) -> Path

def sota() -> Any

def declared(c: Any) -> list
    """The scheme's own fields — every scheme also carries the built-ins."""

def test_a_scheme_declaring_nothing_has_an_empty_contract(tmp_path, monkeypatch)

def test_requires_compiles_to_a_required_untyped_field(tmp_path, monkeypatch)

def test_a_reference_compiles_to_a_typed_field(tmp_path, monkeypatch)

def test_an_optional_reference_is_typed_but_not_required(tmp_path, monkeypatch)

def test_a_field_in_both_tables_is_one_obligation(tmp_path, monkeypatch)
    """
    ADR-060 noted that a field in both `requires` and `references` was
    checked twice and reported twice. Composition is intersection: required
    and required is required, and the reference supplies the type. One
    obligation, carrying both declarations as its provenance.
    """

def test_every_obligation_says_where_it_was_declared(tmp_path, monkeypatch)

def test_one_pass_reports_fields_and_groups_together(tmp_path, monkeypatch)

def test_a_doubly_declared_missing_field_is_reported_once(tmp_path, monkeypatch)

def test_a_satisfied_contract_is_silent(tmp_path, monkeypatch)

def test_the_shipped_record_is_clean_through_the_contract()
    """
    This record declares one thing now — its status vocabulary (#181) —
    and nothing else, so the pass still finds nothing to report on it.
    `empty` stopped being true here when `status:` became a field a scheme
    declares rather than one the code assumes, and again when `tags:` did
    (ADR-098). That is the change working twice: the record page lists
    both vocabularies and cites where each is declared, where before it said
    "nothing beyond the standard fields" and neither was readable from the
    record at all.
    """

def test_a_finding_names_the_key_that_declared_the_obligation(tmp_path, monkeypatch)
    """
    Not just the file: the key. When a second authoring surface exists,
    "luria.yaml" alone would send the reader to the wrong table.
    """

def test_a_merged_obligation_names_both_keys(tmp_path, monkeypatch)

def test_a_group_finding_names_its_key_and_derived_membership(tmp_path, monkeypatch)

def test_describe_is_one_renderer_for_the_whole_contract(tmp_path, monkeypatch)
    """
    What the record page prints and what a finding cites are the same
    words from the same place, so they cannot drift apart (DP-4).
    """

def test_describe_of_an_empty_contract_is_empty(tmp_path, monkeypatch)

def scenes(tmp_path, monkeypatch, many: bool | None, required: bool | None) -> Path

def scene(root: Path, extra: str) -> Path

def findings() -> list[str]
    """
    Contract findings for the document under test. The two supporting
    scenes declare no `follows` of their own and are not what is being
    asked about.
    """

def test_a_reference_declares_whether_it_holds_one_code_or_many(tmp_path, monkeypatch)

def test_the_default_is_one(tmp_path, monkeypatch)

def test_a_list_where_one_code_was_declared_is_a_finding(tmp_path, monkeypatch)
    """
    The reported defect: a list was stringified, its first code checked
    and the rest ignored, silently. Structured input coerced to prose and
    half-read is worse than no support at all.
    """

def test_every_element_of_a_plural_reference_is_checked(tmp_path, monkeypatch)

def test_a_plural_reference_that_resolves_is_silent(tmp_path, monkeypatch)

def test_a_required_plural_reference_may_not_be_empty(tmp_path, monkeypatch)

def test_an_optional_plural_reference_may_be_empty_or_absent(tmp_path, monkeypatch)

def test_a_single_code_in_a_plural_field_is_a_list_of_one(tmp_path, monkeypatch)
    """
    Unambiguous, so accepted: one value is fully interpreted. The
    asymmetry with the scalar case is deliberate — a list in a scalar field
    leaves the tool guessing which element was meant.
    """

def test_describe_says_one_or_many(tmp_path, monkeypatch)

def papers(tmp_path, monkeypatch, group: dict | None) -> Path

def paper(root: Path, extra: str) -> Path

def lit_findings() -> list[str]

def test_a_field_group_is_read_with_its_rule(tmp_path, monkeypatch)

def test_at_least_one_of_the_fields_satisfies_the_group(tmp_path, monkeypatch)
    """
    A paper never posted to arXiv still has a DOI, or failing that a URL:
    the requirement is *a source*, and several fields can be one.
    """

def test_none_of_the_fields_is_a_finding_that_names_them_all(tmp_path, monkeypatch)

def test_an_empty_field_does_not_count(tmp_path, monkeypatch)

def test_exactly_one_and_at_most_one_are_rules_too(tmp_path, monkeypatch)

def test_a_group_with_no_fields_or_a_bad_rule_is_a_config_error(tmp_path, monkeypatch)

def test_describe_lists_the_group_with_its_provenance(tmp_path, monkeypatch)

def test_a_remote_code_is_read_whole(tmp_path, monkeypatch)
    """
    A uid remote's tail is opaque, so the scheme-shaped pattern read
    `ARXIV-2110` out of the first and nothing out of the second.
    """

def test_a_scheme_code_is_still_read_without_any_remote(tmp_path, monkeypatch)

def test_superseded_by_may_name_remote_documents(tmp_path, monkeypatch)
    """
    The docstring always said "or a remote code"; the reader truncated it
    before the check could see it, so a paper superseded by a paper failed
    as "names no scheme or remote".
    """

def test_an_undeclared_prefix_in_superseded_by_is_still_a_finding(tmp_path, monkeypatch)

```

## tests/test_derive.py
```python
def write(root: Path, rel: str, text: str) -> Path

def project(tmp_path, monkeypatch, extra: str, topics: str) -> Path

def note(root: Path, number: int, tags: list[str]) -> Path

def scheme()

def findings(root: Path, path: Path) -> list[str]

def test_the_first_value_becomes_the_field(tmp_path, monkeypatch)

def test_order_is_the_whole_statement(tmp_path, monkeypatch)
    """
    The same two tags the other way round are a different primary. This is
    the cost the feature accepts, so it is pinned rather than implied.
    """

def test_an_explicit_index_reads_further_in(tmp_path, monkeypatch)

def test_an_empty_source_derives_nothing(tmp_path, monkeypatch)
    """
    Absence rather than a blank: a document with no tags has no primary
    topic, and inventing one would be a value nobody wrote.
    """

def test_the_document_on_disk_is_untouched(tmp_path, monkeypatch)
    """
    A derived value lives in the reading, never in the file — the property
    that makes folding it into `meta` safe.
    """

def test_writing_a_derived_field_is_a_finding(tmp_path, monkeypatch)

def test_a_written_value_that_agrees_is_still_a_finding(tmp_path, monkeypatch)
    """
    Agreeing today is not the property that matters. Two copies of one fact
    are free to diverge tomorrow, and nothing would notice.
    """

def test_the_scaffold_offers_no_flag_for_one(tmp_path, monkeypatch)

def test_the_derived_value_is_checked_against_its_vocabulary(tmp_path, monkeypatch)
    """
    "The first tag must be a real topic" costs no new check — the
    vocabulary machinery already written does it once the field exists.
    """

def test_a_secondary_tag_outside_the_vocabulary_is_fine(tmp_path, monkeypatch)
    """
    Only the first position is constrained. `tags` stays open, which is
    what lets a private tag ride along behind a real topic.
    """

def test_a_chain_can_assert_the_derived_field(tmp_path, monkeypatch)
    """
    The point of the exercise: `invariant` reads a derived field like any
    other, so a relation can assert the primary rather than any tag.
    """

def test_sharing_a_secondary_binds_tags_but_not_the_primary(tmp_path, monkeypatch)
    """
    The two readings the pair makes available, on one record: `tags` is
    satisfied by any shared value, `primary_topic` only by the first.
    """

def test_the_record_page_says_where_the_value_comes_from(tmp_path, monkeypatch)

def test_a_derivation_that_could_never_resolve_is_refused(tmp_path, monkeypatch, spec, message)

def test_a_second_answer_about_the_value_is_refused(tmp_path, monkeypatch, extra, message)

def test_a_derivation_needs_no_vocabulary_to_be_a_field(tmp_path, monkeypatch)
    """
    `derive` types a field on its own. Without this the bare case would be
    resolved onto documents but described nowhere, which is a field the record
    page cannot tell a reader about.
    """

def test_a_lone_field_keeps_the_value_s_type(tmp_path, monkeypatch)
    """
    `{versions[0]}` is the number, not "3". What keeps a derived value
    comparable to the vocabulary member a check matches it against, and to
    the value another document's list is intersected with.
    """

def test_a_template_that_builds_something_is_a_string(tmp_path, monkeypatch)
    """
    The other half of the rule: literal text around a field means the
    author was writing a string, so they get one.
    """

def test_a_lone_scalar_field_is_still_refused_as_a_rename(tmp_path, monkeypatch)
    """
    The pre-template rule, narrowed to where it still bites: `{year}`
    under a second name copies a field rather than deriving one. A template
    that *builds* from scalars is fine — this is only the bare case.
    """

def test_derive_and_alias_render_through_one_vocabulary(tmp_path, monkeypatch)
    """
    The point of the step: the same spelling means the same thing whether
    it names a field or an alias.
    """

def test_a_template_reading_nothing_is_refused(tmp_path, monkeypatch)
    """
    A constant is a default, not a derivation — and `default` is the
    spelling that already means that.
    """

```

## tests/test_derive_reference.py
```python
def write(root: Path, rel: str, text: str) -> Path

def project(tmp_path, monkeypatch, extra: str) -> Path

def paper(root: Path, number: int, published: str | None, extra: str) -> Path

def practice(root: Path, number: int) -> Path

def sota()

def meta_of(path: Path) -> dict

def findings(path: Path) -> list[str]

def test_an_indexed_reference_supplies_the_value(tmp_path, monkeypatch)

def test_the_index_picks_which_reference(tmp_path, monkeypatch)
    """
    A practice with several sources takes its primary's date, and which
    one that is is the list's order — the property the whole feature rests on.
    """

def test_a_scalar_reference_needs_no_index(tmp_path, monkeypatch)

def test_the_referenced_document_is_untouched(tmp_path, monkeypatch)

def test_no_reference_derives_nothing(tmp_path, monkeypatch)

def test_an_index_past_the_end_derives_nothing(tmp_path, monkeypatch)

def test_a_dangling_reference_derives_nothing(tmp_path, monkeypatch)
    """
    The code resolves to no document. That is the reference check's
    finding to report, not this one's — deriving nothing keeps one fault to
    one line.
    """

def test_a_target_without_the_field_derives_nothing(tmp_path, monkeypatch)

def test_it_reads_written_frontmatter_not_the_target_s_own_derivation(tmp_path, monkeypatch)
    """
    One hop. The target's `published` here is itself derived, and this
    resolves to nothing rather than chaining — which is what makes a cycle
    impossible by construction rather than by detection.
    """

def test_writing_it_down_is_still_a_finding(tmp_path, monkeypatch)

def test_a_written_value_that_disagrees_is_the_motivating_defect(tmp_path, monkeypatch)
    """
    The anthology's eight stale dates, in one test: the practice says one
    thing, the paper it cites says another, and before this the record had no
    way to notice.
    """

def test_from_must_name_a_reference_this_scheme_holds(tmp_path, monkeypatch)

def test_a_plural_reference_needs_an_index(tmp_path, monkeypatch)

def test_a_scalar_reference_refuses_an_index(tmp_path, monkeypatch)

def test_the_template_is_checked_against_the_target_scheme(tmp_path, monkeypatch)
    """
    `{nonesuch}` is not a field LIT can hold, so this would resolve to
    nothing on every document — the quiet failure eager validation exists for.
    """

def test_reading_the_same_name_is_not_self_derivation(tmp_path, monkeypatch)
    """
    `published` from `published` is a cycle within one document and a
    perfectly ordinary read across two. The rule has to know the difference.
    """

def test_a_lone_field_across_a_reference_is_not_a_rename(tmp_path, monkeypatch)
    """
    Within a document `"{x}"` copies a field under a second name and is
    refused. Across a reference it is the entire point.
    """

def test_many_on_a_followed_derivation_names_the_derive_line(tmp_path, monkeypatch)
    """
    The refusal quotes the literal `derive =` value. `spec` also names the
    followed reference, which was written on its own line — quoting it here
    would print backticks inside a quoted string.
    """

def test_from_alone_renders_nothing(tmp_path, monkeypatch)

def test_a_malformed_from_says_so(tmp_path, monkeypatch)

```

## tests/test_directive_cache.py
```python
def test_a_second_scan_of_the_same_text_does_not_retokenize(monkeypatch)

def test_a_second_blocks_call_does_not_rewalk_the_ast(monkeypatch)

def test_a_rewrite_is_never_read_stale()
    """
    The property that makes keying on content safe: `field_edit` and
    `repair` rewrite files mid-run, and the new text is simply a different
    key rather than a stale entry waiting to be invalidated.
    """

def test_the_same_text_at_two_paths_is_not_confused()
    """
    A comment in Markdown and a comment in Python are not the same scan,
    so the path belongs in the key even when the bytes match.
    """

def test_a_caller_cannot_scribble_on_the_next_readers_result()
    """
    Both return lists, and a caller that mutates one would otherwise be
    editing what every later reading of that file sees.
    """

def test_unparseable_python_still_scans_through_the_cache()
    """The crude fallback is part of what gets cached, not a path around it."""

def test_directives_still_resolve_the_lines_they_govern()
    """
    The cache sits under `_parse`, so the thing it speeds up must be
    unchanged: a `-block` directive above a definition still governs the
    whole docstring it introduces (#222).
    """

```

## tests/test_directive_ttl.py
```python
def _md(tmp_path: Path, body: str) -> tuple[[Path, str]]

def _one(tmp_path: Path, body: str, as_of: Any | None)

def test_a_directive_without_an_expiry_never_expires(tmp_path)

def test_an_unexpired_directive_still_governs_and_knows_its_date(tmp_path)

def test_the_last_day_is_included(tmp_path)
    """`until 2026-09-12` reads as "good until the 12th", not "dead on it"."""

def test_an_expired_directive_is_not_returned_at_all(tmp_path)
    """
    "Behaves as if the annotation isn't even there" — and the way to be sure
    of that everywhere is to drop it at `find`, the one place they are read.
    """

def test_expiry_is_uniform_across_directive_names(tmp_path)
    """
    Not a feature of `inactive-ok`. `find` parses the shape, so every
    directive gets this the same way — which is the promise the syntax makes.
    """

def test_scope_still_works_with_an_expiry(tmp_path)

def test_expired_directives_are_findable_for_reporting(tmp_path)
    """
    Dropping them from `find` makes them inert; it must not make them
    invisible. A check that starts failing again with no word about the
    acknowledgement sitting right above it is a puzzle, not a report.
    """

def test_nothing_expired_is_an_empty_list_not_a_surprise(tmp_path)

def test_find_and_find_expired_partition_the_file(tmp_path)

def test_an_unparseable_date_keeps_the_directive_live_and_reports_it(tmp_path)
    """
    Fail-safe, and loud. Dropping the suppression on a typo would break a
    build for a reason the message would not explain; keeping it and reporting
    the typo says what to fix without breaking anything.
    """

def test_until_with_no_date_is_reported(tmp_path)

def test_a_well_formed_expiry_is_not_a_problem(tmp_path)

def test_a_malformed_expiry_does_not_eat_the_codes(tmp_path)
    """
    The report is about the date. The codes it names are still the codes it
    names, so whatever the directive was excusing stays excused.
    """

def test_the_report_names_the_file_the_directive_and_the_date(tmp_path, monkeypatch)

def test_a_live_directive_is_not_reported(tmp_path, monkeypatch)

```

## tests/test_directives.py
```python
def find(text, path, names)

def test_parses_name_args_and_reason()
    """
    The codes here are a made-up scheme on purpose: the parser knows nothing
    about ADRs, and real codes in fixtures would show up in `luria reports`.
    """

def test_directive_must_open_its_comment()
    """
    `# noqa` convention. Matching mid-comment means prose *about* the syntax
    invokes it — comments in the scanner explaining these rules did exactly
    that before this held.
    """

def test_examples_are_not_directives()
    """
    A fenced example in markdown and a docstring example in Python are not
    comments. Documenting the syntax must not activate it.
    """

def test_reads_code_comments()

def test_second_comment_on_a_line_is_seen()

def test_names_filter()

def test_line_scope_is_its_line_and_the_next()

def test_block_scope_is_the_paragraph()

def test_file_scope_is_everything()

def test_no_directive_has_its_own_default_scope()
    """
    The suffix decides, uniformly. A per-directive default is one more thing
    to remember, and it made the bare form reach across a blank line for one
    directive and not another.
    """

def test_a_bare_directive_does_not_reach_across_a_blank_line()
    """
    The rule that was tried and removed: a standalone bare directive silently
    governing the block below it. Convenient for one example, unpredictable
    everywhere else — `-block` says it out loud instead.
    """

def test_a_standalone_block_directive_governs_the_block_it_introduces()
    """
    A directive alone between blank lines has no content block of its own, so
    the block it means is the next one. That is the reading of "block", not an
    exception to it.
    """

def test_two_directives_in_one_standalone_block_both_reach()

def test_a_bare_directive_flush_against_a_fence_reaches_it()
    """
    No blank line, so line scope covers the fence's opening line — and
    unexempting any line of a fence unexempts that fence.
    """

def test_a_fence_is_one_block_even_with_blank_lines()

def test_blocks_are_blank_line_delimited()

def test_missing_argument_is_a_problem()

def test_unknown_argument_is_a_problem()

def test_valid_directive_has_no_problem()

def test_shaped_spans_match_examples_too()
    """
    A code named in directive syntax is being governed, not cited — whether
    the directive is live or an illustration of one.
    """

def test_a_yaml_comment_in_frontmatter_is_a_comment()
    """
    A reference field is a citation site, and the frontmatter is YAML —
    so the comment that answers a finding there is a `#` one, line-scoped
    like everywhere else: its own line and the field below it.
    """

def test_a_directive_shaped_heading_in_the_body_does_not_fire()
    """
    `#` opens a heading outside the frontmatter. The scan never leaves the
    frontmatter, so prose *about* the syntax stays prose.
    """

def test_no_frontmatter_means_no_yaml_comments()

def test_frontmatter_and_html_comments_are_both_read_in_order()

def test_in_frontmatter_the_line_below_is_the_whole_entry()
    """
    `luria repair` writes `superseded_by:` as a list, so the code sits on
    the line after the key; a directive above the key has to reach it.
    """

def test_in_prose_the_line_below_is_still_one_line()

def test_a_block_directive_above_a_def_reaches_its_whole_docstring(tmp_path)
    """
    The case that motivated this: a citation in a docstring's *third*
    paragraph. Before, only `-file` reached it — far too blunt for one
    sentence of prose that happens to name a code.
    """

def test_a_docstring_is_atomic_the_way_a_fence_is(tmp_path)
    """
    The principle it rests on, already in the rules for fenced code: a
    blank line inside one syntactic unit does not end the paragraph.
    """

def test_a_directive_written_inside_a_docstring_still_does_not_fire(tmp_path)
    """
    Unchanged, and load-bearing: a docstring is not a comment, so prose
    that looks like a directive is prose.
    """

def test_unparseable_python_yields_no_docstring_spans(tmp_path)
    """A directive's scope is not where a syntax error should surface."""

@needs_grammar
def test_block_reaches_past_a_blank_line_inside_one_unit(tmp_path, name, src)
    """
    The docstring case was never about docstrings. Every language has a
    construct that holds a blank line, and the run-of-non-blank-lines rule is
    wrong in all of them the same way.
    """

@needs_grammar
def test_a_block_does_not_grow_into_the_next_entry(tmp_path)
    """
    Growth stops at the unit the directive introduces. A top-level comment's
    next sibling is the whole YAML document; taking that would make `-block`
    mean `-file` in every workflow file in the repository.
    """

@needs_grammar
def test_a_directive_inside_a_string_is_not_a_comment(tmp_path)
    """What the marker scan cannot do, and says so in its own comment."""

@needs_grammar
def test_a_directive_appended_after_other_comment_text_still_reads(tmp_path)
    """
    A grammar reads `// note  // dir: x` as one comment, which is true and
    would drop the directive. The spelling predates the grammar and keeps
    working: precision is applied to finding comments, not to redefining where
    one starts.
    """

@needs_grammar
def test_growth_never_narrows_what_a_block_already_covered(tmp_path)
    """
    The rule is a union. A file that lints today cannot start failing
    because a grammar has a tidier opinion about its blocks.
    """

```

## tests/test_doc_refs.py
```python
def kinds(text)
    """
    (what matched, which number). A scheme reference reports its prefix
    rather than the bare kind — `ADR` is not special to the finder any more
    (ADR-006), so "adr" here means "the ADR scheme matched".
    """

def test_finds_each_kind()

def test_design_principle_wins_over_issue()
    """
    `design-principles #13` is principle 13, not issue 13 — the DP pattern
    has to claim the `#13` before the issue pattern sees it.
    """

def test_bare_principle_is_a_principle()
    """
    The docs say "principle #4" as often as "design principle #4"; read as an
    issue it links to a real but unrelated issue 4.
    """

def test_principle_run_carries_the_label()
    """
    "principles #17 and #18" — the label governs the run, so the sibling is
    principle 18, not issue 18.
    """

def test_bold_marker_is_not_stolen_from_the_run()
    """
    The `**` closing "**Design principles #17 and #18**" belongs to the bold
    that opened before the label — swallowing it into the last link's text
    leaves the emphasis unbalanced.
    """

def test_spaced_adr_and_bold()

def test_hex_colour_is_not_an_issue()

def test_heading_hash_is_not_an_issue()

def test_low_numbers_need_a_cue_to_be_issues()
    """
    A `#N` small enough to be a principle number is also how the docs number
    open questions, stories and gotchas. With a cue it's an issue; without one
    it is left alone rather than linked to a real but unrelated issue.
    """

def test_code_is_ignored()

def test_stray_backtick_does_not_poison_the_rest_of_the_file()
    """
    Pairing backticks document-wide lets one unbalanced tick invert which
    side of every later tick counts as code: `#123` got linked inside its own
    code span, and 809 real references were skipped as "code" in the same file.
    Pairing is per paragraph, so a desync can't outlive one.
    """

def test_unexempt_puts_a_code_block_back_under_the_lint(tmp_path)
    """
    Code is exempt because code is quoted, not asserted — but a snippet in
    the docs can be quasi-prose citing decisions the reader should follow.
    """

def test_unexempt_needs_block_scope_across_a_blank_line()
    """
    The bare form is line-scoped like every other directive, so a blank line
    between it and the fence means it governs nothing. `-block` says so.
    """

def test_unexempt_is_off_by_default(tmp_path)

def test_unexempt_reports_an_unknown_region()

def test_existing_links_are_ignored()

def test_defined_shortcut_reference_is_already_a_link()

def test_undefined_shortcut_reference_is_bare()

def test_frontmatter_data_is_exempt_but_the_summary_is_not()
    """
    `status:`/`issue:` are data the generator reads by value; a link there
    would be a link in a data field. The summary is prose that the generator
    renders as markdown — and rebases per output — so it carries links.
    """

def test_summary_rewrite_is_verified_against_the_yaml()
    """
    The rewrite is checked, not assumed safe: it must still parse, leave
    every other key alone, and reduce back to the original summary when the
    links are stripped.
    """

def test_unsurvivable_summary_rewrite_is_dropped_by_both_sides()
    """
    If a rewrite would change the YAML's meaning, the fixer declines it —
    and `rewritable_refs` (what lint reports) declines it identically.
    """

def test_html_attributes_and_anchors_are_ignored()

def test_urls_and_comments_are_ignored()

def test_linkify_uses_repo_conventions()

def test_linkify_is_idempotent()

def test_html_block_gets_an_html_anchor()
    """
    Markdown isn't parsed inside a raw HTML block, so `[#551](…)` there would
    render as literal brackets — the README gallery is exactly this shape.
    """

def test_undefined_shortcut_brackets_are_absorbed()

def test_self_reference_is_not_linked()

def test_fragment_links_resolve_from_the_collected_file()
    """
    A changelog fragment is assembled into /CHANGELOG.md — links must be
    written for where the text lands, not for where the fragment sits.
    """

def test_journal_entry_links_resolve_from_its_book()
    """
    A journal entry is nested (`.../2026/08/03/`) and renders into the
    journal's output directory, so its links resolve from *there* however deep
    the entry is (ADR-020).
    """

def test_design_principle_links_to_its_own_page()
    """
    This record sets `cite = "page"`, so a principle is cited at the file it
    publishes as rather than at an anchor in the assembled document. The other
    setting is covered in tests/test_scheme_cite.py; here the point is which
    one THIS record chose.
    """

def test_the_assembled_document_cites_a_principle_at_its_page_too()
    """
    No special case for citing from inside the view: under `cite = "page"`
    the view is not the target, so there is no self-link to avoid.
    """

def test_explicit_anchor_beats_the_heading_slug(project)
    """
    A principle is a living document, so its heading moves. The generator
    emits `<a name="dp-N">` for exactly that reason (ADR-012), and a link has to
    prefer it — otherwise rewording a principle silently breaks every link to
    it, which is the fail-stale polarity DP-3 rules out.
    """

def test_heading_slug_is_the_fallback(project)
    """
    A project whose principles are still one hand-written file has no
    explicit anchors, and its links must still resolve — the fallback is what
    keeps the convention adoptable before `luria index` has ever run.
    """

def test_repo_docs_have_no_bare_references()
    """
    The invariant `make lint-docs` enforces, asserted directly so a failure
    names the file and line.
    """

def test_fixer_links_a_uid_remote_reference(tmp_path, monkeypatch)
    """
    A bare `ARXIV-2403.05530` becomes a link through the uid template —
    the reference machinery is shape-agnostic end to end (ADR-024).
    """

```

## tests/test_doc_reports.py
```python
def test_writes_every_report(tmp_path)

def test_generated_stamp_says_not_to_edit(tmp_path)

def test_reference_report_links_every_site(project)
    """
    The console summary caps at five sites per document; the report is
    where the rest lives, so it must not cap — and each site is a link to the
    citing file (#35).
    """

def test_reference_report_links_the_flagged_document(project)

def test_reference_report_counts_match_the_scan()

def test_the_report_never_calls_a_proposed_document_retired(project)
    """
    The clarification #63 asked for: a Proposed document was listed under
    a page titled "Retired documents", and Proposed is the opposite of
    retired — it hasn't been in force yet. The umbrella is "not in force",
    and the section says which side of that a status falls on.
    """

def test_pending_report_links_every_row_to_its_decision(project)

def test_pending_report_states_age_as_a_date(project)
    """
    "Open since 2026-01-01" is a fact about the record; "N days" is a fact
    about today, and a committed view can't carry one (#35).
    """

def test_the_two_reports_explain_why_their_counts_differ()
    """
    The bug that prompted the reports: one said 8 and the other 9, with
    nothing explaining that they measure different things.
    """

def test_outputs_land_in_the_configured_reports_dir()

def test_reports_are_deterministic()

def _git(root)

def test_a_gitignored_report_dir_is_not_stale(tmp_path, monkeypatch)
    """
    `luria index --check` must not fail over a view the project ignores.
    A project can point `[luria.paths] reports` at a build directory and
    publish the result as a CI artifact instead of committing it — which is
    the shape downstream had. A fresh clone then never has the file, so
    *missing* read as *stale*, and the remedy the failure printed ("regenerate
    and commit the result") is the one thing `.gitignore` forbids: the docs
    job went red on every commit and stayed there.
    """

def test_a_tracked_report_dir_still_gates(tmp_path, monkeypatch)
    """
    The exemption is `.gitignore`, not the reports directory.
    A project that commits its reports — which is this repo's own layout —
    must keep failing on a stale one, or the fix would have turned a real
    check off for everybody to unstick one project.
    """

def test_index_check_is_the_one_staleness_verdict(tmp_path, monkeypatch)
    """
    One rule set, one command. There used to be two.
    `luria index --check` and `luria lint` both decided what "stale" means,
    from the same three rules written twice; the gitignore exemption above
    went into the first one and `lint` went on rejecting the identical tree.
    They shared `staleness()` after that, and now the lint asks no staleness
    question at all (ADR-068): the view-directory check reads only the
    orphan rule. This pins `--check`'s verdict on both sides of the
    exemption, and that the lint has nothing to say about a stale view.
    """

def verdicts() -> tuple[[bool, list[str]]]

```

## tests/test_document_cache.py
```python
def _doc(path: Path, title: str, body: str) -> Path

def test_second_read_does_not_reparse(tmp_path, monkeypatch)

def test_a_rewrite_invalidates_it(tmp_path)
    """
    The property the whole cache rests on: a writer bumps the mtime, so no
    caller has to remember to drop anything.
    """

def test_callers_cannot_scribble_on_each_others_metadata(tmp_path)
    """
    `Adr` folds derived fields into the mapping it is handed. A shared dict
    would let one reading's derivation leak into the next — the failure the
    per-`Adr` resolver exists to avoid (#233), reintroduced one layer down.
    """

def test_body_survives_the_round_trip(tmp_path)

def test_a_document_with_no_frontmatter_still_reads(tmp_path)

def test_resolving_a_code_twice_does_not_reparse(tmp_path, monkeypatch)

def test_a_rewrite_is_still_seen_through_the_referent_path(tmp_path, monkeypatch)
    """
    The cache is only safe because `repair` writes documents mid-run and
    reads them back. Going through it must not break that.
    """

def test_a_code_naming_nothing_still_answers_empty(tmp_path, monkeypatch)
    """
    `{}` rather than an exception: a code resolving to nothing is already
    the reference check's finding, and raising here would report it twice.
    """

def test_an_unreadable_document_still_answers_empty(tmp_path, monkeypatch)

```

## tests/test_documents_cache.py
```python
def _doc(path: Path, number: int) -> Path

def scheme_dir(tmp_path, monkeypatch)
    """The ADR scheme of a real config, and the directory it reads."""

def _scheme(pair)

def test_a_second_call_does_not_reglob(scheme_dir, monkeypatch)

def test_temp_documents_shares_the_same_glob(scheme_dir, monkeypatch)
    """Both read the same directory listing; one walk answers both."""

def test_a_new_document_is_seen(scheme_dir)

def test_a_removed_document_is_seen(scheme_dir)

def test_a_rename_is_seen(scheme_dir)
    """`luria concretize` renames a temporary document into its number."""

def test_forget_clears_it(scheme_dir)
    """The escape hatch, for a writer that outruns mtime resolution."""

```

## tests/test_edges.py
```python
def write(root: Path, rel: str, text: str) -> Path

def doc(root: Path, rel: str) -> Path

def adr(path: Path) -> Adr

def test_the_superseded_by_field_is_an_edge(project)

def test_the_field_may_name_several_successors(project)

def test_a_note_alone_is_not_an_edge(project)
    """
    Two drafts inferred the successor from a `by CODE` note and were
    corrected on review: the field is structure, checked and resolved; a
    sentence the tool happens to recognise is not. The old shape is read
    once more by `luria index`, as the repair that fills the field.
    """

def test_a_note_beside_the_field_is_prose_not_a_second_edge(project)

def test_a_code_in_any_other_status_note_is_not_an_edge(project)
    """
    A Rejected note may cite what defeated it, a Deferred one what parked
    it. The note is prose: those are citations the scanner finds, not
    relations the graph invents.
    """

def test_a_foreign_successor_is_not_an_edge(project)
    """
    A remote's namespace is theirs (ADR-016); the graph has no node for
    it, so there is nothing for the edge to land on.
    """

def test_influenced_by_is_an_edge(project)

def two_schemes(tmp_path, monkeypatch) -> Path

def test_a_declared_reference_field_is_an_edge_named_for_the_field(tmp_path, monkeypatch)

def test_a_linked_reference_field_still_reads(tmp_path, monkeypatch)

def test_a_reference_that_is_not_a_code_is_no_edge(tmp_path, monkeypatch)
    """The lint reports it (ADR-060); the graph does not invent a node."""

def test_inbound_edges_are_the_backlinks(project)

def test_the_shipped_record_has_its_three_successions()
    """
    Fired on a real case: the three superseded decisions in this record
    each name a successor, and the graph reads every one.
    """

def test_the_record_line_names_what_a_decision_supersedes()

def test_the_record_line_names_what_a_decision_influenced()

def test_the_record_line_carries_a_declared_reference_both_ways(tmp_path, monkeypatch)

def test_a_staged_page_carries_its_inbound_edges(project)

def scenes(tmp_path, monkeypatch, many: bool) -> Path

def test_a_plural_reference_is_one_edge_per_code(tmp_path, monkeypatch)
    """
    The reported defect's other half: the edge derivation stringified
    the list too, and emitted one edge for two codes.
    """

def test_a_list_in_a_scalar_reference_yields_no_edge(tmp_path, monkeypatch)
    """
    The lint reports the shape; the graph does not guess which element
    was meant.
    """

def converse_schemes(tmp_path, monkeypatch) -> Path
    """
    Two schemes where the practice line declares its converse, which is
    what puts the same fact in both documents' frontmatter.
    """

def test_a_stored_converse_is_not_also_rendered_as_a_backlink(tmp_path, monkeypatch)
    """
    `extends:` and `extended_by:` hold ONE fact, written on both sides
    because the converse is declared. The inbound rendering exists for the
    direction the site would otherwise lose; when the converse is stored
    here, nothing is lost, and printing it twice under two labels — once
    humanised, once as a raw field name — is the same fact wearing two
    coats.
    """

def test_a_backlink_with_no_stored_converse_still_renders(tmp_path, monkeypatch)
    """
    The suppression is about a fact already on the page, not about
    backlinks. `source:` declares no converse, so the citing practice is
    the only place this note's page can learn it is cited.
    """

def test_an_unwritten_converse_still_renders_as_a_backlink(tmp_path, monkeypatch)
    """
    A one-sided relation is a lint finding, not a reason for the page to
    go quiet: suppress the backlink only where the converse is actually
    stored, so a record mid-repair still shows the edge it has.
    """

```

## tests/test_encoding.py
```python
def bare_io_calls(path: Path) -> list[str]
    """`x.read_text()` / `x.write_text(...)` with no `encoding=`."""

def test_no_file_io_in_the_package_depends_on_the_locale()
    """
    The structural half. `Path.read_text()` with no encoding uses whatever
    the platform prefers, which is cp1252 on a default Windows install and
    ASCII under `LC_ALL=C` — so the default is a portability bug wherever the
    record contains an em dash, and this record's prose is full of them.
    """

def test_a_generated_view_is_utf_8_whatever_the_console_is(tmp_path)
    """
    The behavioural half, run the way the bug arrived: a full scaffold and
    build under an ASCII locale, in a subprocess, because the interpreter
    settles its encodings at startup and no fixture can undo that.
    """

def test_the_console_degrades_rather_than_raising(tmp_path)
    """
    `luria init` prints an arrow. Under a console that cannot encode one
    the line still has to arrive, because the alternative is a traceback in
    place of a scaffold.
    """

def run()

```

## tests/test_examples.py
```python
def example(tmp_path, monkeypatch)
    """
    Build one example into a temp tree and point the config at it.
    Copied rather than run in place: generating into the repository would
    leave committed views nobody regenerates, which is the exact failure the
    examples argue against.
    """

def lint_errors() -> list[str]
    """
    `luria lint`'s failures, as a list rather than an exit code.
    Every check `lint.run()` runs, in its order. Naming a subset here would
    make these tests pass on records the real command rejects — which is the
    same drift the examples exist to catch, one level up.
    """

def assert_published(report, name: str) -> None
    """
    A staging run that published something, and placed all of it.
    Both halves, in order. A vault with no pages places nothing by definition,
    so `unplaced == []` from an empty run reads exactly like a clean one — the
    assertion has to prove it measured before it is allowed to conclude.
    """

def test_every_example_lints_clean(example, name)
    """The headline claim: these are configurations that work."""

def test_every_example_render_is_stable(example, name)
    """
    A second `luria index` changes nothing — the views are a pure function
    of the sources, which is what makes staleness detectable at all.
    """

def test_two_schemes_render_in_their_two_shapes(example)
    """
    `render = "index"` browses; `render = "document"` reads whole. Neither
    is a special case, and neither is about decisions.
    """

def test_a_view_can_render_beside_its_sources(example)
    """
    Adoption never has to begin by moving files.
    Note what the example has to write to get this: `output` equal to `dir`,
    not `output` omitted. Omitting it works for a scheme you invent, and does
    *not* work for `ADR` — see the limit pinned at the bottom of this file.
    """

def test_three_journals_at_three_granularities(example)
    """`journals` is a family, not a fixed devlog."""

def test_uid_remotes_link_things_that_are_not_records(example)
    """
    The capability that has nothing to do with decision records: a regex
    and a URL template make arXiv ids, ticket keys and CVEs first-class,
    linted references.
    """

def test_a_uid_remote_can_move_its_delimiter(example)
    """
    Ticket keys contain the default delimiter themselves, so `JIRA:PLAT-88`
    has to be spellable. Without `delim`, the prefix and the key are
    indistinguishable.
    """

def test_two_schemes_can_disagree_about_the_same_work(example)
    """
    The modeling case for splitting a scheme: a paper and a practice drawn
    from it are separate claims, so each needs its own status. One scheme
    means one status field, and then they cannot differ.
    """

def test_a_practice_names_the_paper_behind_it(example)
    """
    A declared reference is what makes "every practice cites a paper" a
    check rather than a sentence in CONTRIBUTING — and a *typed* one, so a
    practice citing a decision, or a sentence, fails too (ADR-060). The
    example carried `requires = ["source"]` until #141's dogfooding pass
    measured the gap. A paper's own source is a field group: any of
    `arxiv`, `doi` or `url` satisfies it, because a report never posted to
    arXiv is a paper all the same.
    """

def test_exactly_one_primary_category_is_enforced(example)
    """
    The rule every tagged corpus states in prose and then drifts away
    from. Eight lines of config, and the lint holds it.
    """

def test_active_selects_a_status_the_vocabulary_holds(example)
    """
    `active` picks the in-force state *from* the vocabulary — it does not
    invent one.
    The five are a default now rather than a law, so a project may name its
    own words in `statuses.yaml`. What it may not do is point `active` at a
    word the vocabulary does not hold: no document could ever be in force,
    which silences the citation checks while looking configured. Documented
    in `examples/README.md`; pinned here so it cannot quietly stop.
    """

def test_a_declared_family_replaces_the_defaults(example)
    """
    A project that declares schemes gets exactly the schemes it declared.
    These used to be two pinned *limits*: the shipped ADR scheme could not be
    removed, and omitting its `output` inherited `docs/decisions` instead of
    unsetting it — both because families merged over `DEFAULTS`. ADR-047
    changed the rule: a declared family replaces the default one. The pins
    fired when the rule changed, which is what they were for; these are their
    inversions.
    """

def test_an_undeclared_family_keeps_the_defaults(example)
    """
    The other half of the replacement rule: a family you never mention is
    still the shipped one. `many-journals` declares only journals, so its
    scheme family is untouched and the default ADR scheme survives.
    """

def test_omitting_output_collocates_a_declared_scheme(example)
    """
    Declaring `[luria.schemes.ADR] dir = "decisions"` with no `output`
    now genuinely unsets it — nothing is left for the key to inherit from —
    so the view renders beside the sources, as the `collocated` example's
    config reads.
    """

def test_a_configured_scheme_is_linted_like_any_other(example)
    """
    The promise ADR-006 made, at the layer that was missing it.
    `find_refs` used to know three hardcoded patterns — ADR, the `#` spelling
    of DP, and issues. A project that configured `RFC` got indexes, tag pages
    and `luria new rfc`, and no reference checking at all: `RFC-7` in prose was
    neither linked nor reported. Rendering was general; the linter was not.
    """

def test_cross_scheme_references_resolve_to_each_shape(example)
    """
    An index-rendered scheme resolves to the document's own file; a
    document-rendered one to an anchor in the assembled page. Both from the
    right base, which is where the text *renders*, not where it lives.
    """

def test_the_dp_code_spelling_is_found_not_only_the_prose_one(example)
    """
    `CLAUDE.md` and the scaffolded template both tell contributors to write
    the bare code and let the fixer spell the target. For `DP-6` that was
    false: `DP_RE` matched only `design principles #6`, so a bare `DP-6` was
    neither linked nor reported — the worst of the three behaviours.
    """

def test_a_document_never_links_to_itself(example)
    """
    A fragment is a different file from the page it assembles into, so the
    `target == source` test that protects an index-rendered scheme does not
    fire here. Without an explicit guard a principle's own `# DP-001:` heading
    becomes a link, and the title check then fails on a heading that no longer
    matches its frontmatter — which is exactly what happened first.
    """

def test_a_scene_with_no_worlds_sits_in_the_default_trajectory(example)
    """
    The convention the world-building record could not state: absent
    means B. Read as B by the index; never written into the scene.
    """

def test_a_world_the_file_does_not_name_is_a_finding(example)

def test_a_plural_follows_is_checked_element_by_element(example)

def test_a_paper_with_only_a_url_has_a_source(example)
    """
    The report that was never posted to arXiv: `requires = ["arxiv"]`
    would have failed it; the `source` group takes its `url:`.
    """

def test_precedence_is_an_edge_the_lint_follows(example)
    """
    A record whose documents govern each other.
    The constitution example's distinguishing claim: which rule wins is a
    declared, resolved reference rather than an adjective. Every other corpus
    of instructions expresses precedence by escalating emphasis — IMPORTANT,
    then CRITICAL, then capitals — which inflates until it no longer sorts
    anything.
    """

def test_a_required_reference_makes_an_ungrounded_rule_a_finding(example)
    """
    `grounds` is a typed reference, not `requires`.
    Same rule the knowledge-base example states about citations: `requires` is
    satisfied by any truthy value, so a practice grounded in "because it reads
    better" would pass. Only a typed reference can say the value must name a
    VALUE — and both rule-shaped schemes declare it, so no rule in this record
    stands on its own authority.
    """

def test_a_document_may_be_superseded_across_schemes(example)
    """
    A PRACTICE retired by a BOUNDARY.
    Worth pinning because it is not obvious that it should work: `superseded_by`
    resolves across schemes, so the record can say "the rule was replaced by a
    limit" rather than forcing the successor into the predecessor's family — and
    the generated index renders the successor's link from the other scheme's
    view directory.
    """

def test_every_example_stages_its_own_site(example, tmp_path, name)
    """
    Each example is a whole record, so each publishes as its own site.
    The root `luria.yaml` excludes `examples/**` from *this project's* site,
    and that reads like the examples cannot be published. It is the opposite
    claim: they are excluded because each is a separate record, and the parent
    config cannot stage a child's. `Config.link_base` is the reason — the
    parent has no VALUE, SCENE or LIT scheme, so an example's document-scheme
    sources come back with `link_base == path.parent` and `publishable()`
    cannot tell a source from a view. It would publish both, and half of the
    views it published would be whatever a contributor's working tree happened
    to hold, since none of them is committed.
    Pointing `LURIA_ROOT` at the example instead is all it takes. Asserted per
    example rather than described once, because the interesting number is
    what staging counts. `luria lint` checks that a relative target exists *on
    disk*; it has no opinion about whether the file it names is ever published.
    Constitution's four VALUE citations pointed at `../values.d/VALUE-00N.md` —
    present, lint-clean, and never a page, because a document scheme renders
    its sources into one assembled view. Staging is the only check that reads
    them as links a reader would try to follow.
    """

def test_every_active_document_accounts_for_something_in_the_source(example)
    """
    `constitution/` carries the document it decomposes, so the decomposition
    can be checked rather than believed.
    The claim a record like this makes is that each of its documents accounts
    for part of the source. Nothing enforced that until the source was in the
    repository, and it is not the sort of thing a schema can express: the
    reference the lint follows runs `PRACTICE → VALUE`, not `PRACTICE →
    the text it was drawn from`. Asserted here instead, in the direction that
    can actually go wrong — a document nobody derived, invented because it
    sounded like a principle.
    Retired documents are exempt and that is the point of the exemption: a
    superseded practice is history, and history is not required to still
    explain the current source.
    """

def test_every_section_of_the_source_says_what_accounts_for_it(example)
    """
    The other direction, which is the one that actually goes wrong.
    `test_every_active_document_accounts_for_something_in_the_source` catches a
    document nobody derived. The likelier change by far is the opposite — the
    constitution gains a paragraph and nobody writes anything — and until this
    existed, nothing caught it: appending a whole new section to the source and
    writing no document left the suite green.
    A `Decomposed as` block is required after every section, and a block saying
    *nothing yet* satisfies it. That is the point rather than a loophole: the
    three runtime-fact sections are accounted for by nothing deliberately, and
    an explicit "nothing, and nothing should" is a different statement from an
    absent one — which is the whole of [[DP-015]] applied to a document.
    """

def build(name: str) -> Path

```

## tests/test_frontmatter_shape.py
```python
def errors_for(project) -> list[str]

def test_html_comment_in_frontmatter_is_reported(project)
    """PyYAML accepts `<!-- ... -->` as a mapping key; Quartz does not."""

def test_hash_comment_in_frontmatter_is_clean(project)
    """The intended spelling after #163: a YAML `#` comment is not a key."""

def test_duplicate_frontmatter_key_is_reported(project)
    """PyYAML keeps the last value; a strict loader rejects the file."""

def test_indented_html_comment_in_folded_scalar_is_clean(project)
    """An indented `<!--` is content, not a mapping key."""

```

## tests/test_init.py
```python
def test_existing_files_are_kept_verbatim(tmp_path, capsys)

def test_a_kept_claude_md_gets_the_map_pointer(tmp_path, capsys)
    """
    The file isn't touched — the recommendation goes to stdout, where
    permission isn't needed.
    """

def repoint(tmp_path, monkeypatch)

def test_a_fresh_default_init_lints_clean(tmp_path, monkeypatch, capsys)
    """
    The three documented commands, run as documented. This exact loop
    caught two template defects the day it was first automated — a bare
    LU-ADR-048 and a bare DP-1, both invisible until scheme-driven reference
    detection existed — so it stays as the guard for that whole class.
    """

def test_init_config_scaffolds_the_declared_shape(tmp_path, monkeypatch)
    """
    `--config` installs the file and scaffolds what it declares — and
    nothing else: no decision directory for a project that declared no
    decision scheme.
    """

def test_init_config_refuses_a_project_that_already_has_one(tmp_path)
    """
    Scaffolding one config's shape while a different config governs the
    record would build directories the project's own machinery doesn't know
    about — an error, not a skip.
    """

def test_init_scaffolds_from_the_projects_own_config(tmp_path)
    """
    A project that already has a `luria.yaml` gets that config's shape,
    not the template's. This was the old wart: init used to copy the fixed
    tree regardless, scaffolding decision directories for a record whose
    config declared none.
    """

def test_generic_template_matches_new_entrys_contract(tmp_path, monkeypatch)
    """
    The `{PREFIX}-NNN` placeholder is `luria new`'s substitution target
    (ADR-036); a scaffolded template that misspelled it would copy the
    placeholder into every real document.
    """

def test_generated_stub_placeholders_are_single_braced(tmp_path)
    """
    A scaffolded stub is substituted by `str.replace`, not `str.format`, so
    `{{categories}}` is not an escape — it is a literal brace wrapped around
    the placeholder, and the index generator renders the pair verbatim.
    The hand-shipped decisions stub uses single braces and was always right;
    this pins the generated ones to the same spelling.
    """

def test_init_writes_the_status_vocabulary(tmp_path, monkeypatch)
    """
    The binding constraint on turning built-ins into defaults.
    `template-drift` and `inert-status` both came from a capability that was
    live but invisible: nobody used it because nothing showed it. A default
    inherited from code is that trap again — the project cannot read what it
    is getting, so it never occurs to anyone that it is theirs to change. So
    `luria init` writes the vocabulary down.
    """

def test_the_written_vocabulary_is_the_one_in_force(tmp_path, monkeypatch)
    """Written, not decorative: editing the file changes what lints."""

```

## tests/test_init_shorthand.py
```python
def scaffold(root)

def test_a_bare_prefix_gets_the_conventional_paths(tmp_path)

def test_a_document_scheme_outputs_one_page(tmp_path)

def test_the_shipped_schemes_survive(tmp_path)
    """
    "Mostly the defaults" has to mean additive. A declared family replaces
    the shipped one whole (ADR-047), so the template's own tables staying in
    the file is what keeps ADR and DP alive alongside the new one.
    """

def test_several_at_once(tmp_path)

def test_a_journal_defaults_to_monthly(tmp_path)

def test_a_plural_prefix_is_not_doubled(tmp_path)

def test_the_prefix_is_upcased(tmp_path)

def test_the_new_scheme_is_scaffolded_like_any_other(tmp_path)

def test_the_config_it_writes_is_ordinary_toml(tmp_path)
    """
    No shorthand survives into the file — the whole design. A reader of
    this config sees what every other project's config looks like.
    """

def test_an_unknown_render_names_the_vocabulary(tmp_path)

def test_an_unknown_granularity_names_the_vocabulary(tmp_path)

def test_redeclaring_a_shipped_scheme_is_refused(tmp_path)
    """
    Silently merging would be worse: the template's ADR table carries the
    decision doctrine, and a second one would either duplicate or shadow it.
    """

def test_shorthand_against_an_existing_config_is_refused(tmp_path)
    """
    The shorthand extends the shipped template. Where a config already
    exists the shape is somebody's decision, and appending to it from a flag
    would edit a file the project owns.
    """

def test_an_empty_entry_is_ignored_not_guessed_at(tmp_path)

def repo(root, origin)

def test_the_remote_shapes_all_parse(tmp_path, remote, expected)
    """
    scp-like, https, and ssh:// — the three ways the same remote is
    written, and `https` matches a bare hostname under the scp-like branch,
    so the ordering of that alternation is load-bearing.
    """

def test_an_unknown_shape_infers_nothing(tmp_path, remote)
    """
    A wrong issue URL is worse than an empty one: it renders a link on
    every entry carrying an issue, and each one 404s.
    """

def test_no_remote_and_no_repository_are_both_quiet(tmp_path)

def test_the_inferred_url_reaches_the_config(tmp_path)

def test_it_cascades_into_the_site_settings(tmp_path)
    """
    The reason this is worth inferring rather than prompting for: one
    value, four settings.
    """

def test_an_explicit_url_wins(tmp_path)

def test_it_writes_the_config_and_nothing_else(tmp_path)

def test_the_file_is_what_init_would_have_written(tmp_path, monkeypatch)
    """
    One builder behind both commands. If they drift, a project that edits
    the config and then inits gets a shape neither of them described.
    """

def test_editing_it_then_initing_scaffolds_the_edit(tmp_path, monkeypatch)
    """
    The flow this exists for: rename a directory before anything is
    created, rather than moving it afterwards.
    """

def test_it_refuses_to_overwrite(tmp_path)

def test_stdout_prints_without_writing(tmp_path, capsys)

def test_stdout_works_over_an_existing_config(tmp_path, capsys)
    """
    Looking is not writing, so the refusal above does not apply — this is
    how you see what the shorthand would have produced.
    """

def test_it_infers_the_issue_url_too(tmp_path)

```

## tests/test_invariants.py
```python
def write(root: Path, rel: str, text: str) -> Path

def project(tmp_path, monkeypatch, extra: str) -> Path

def note(root: Path, number: int, tags: list[str]) -> Path

def chain()

def test_a_relation_sharing_no_value_is_a_finding(tmp_path, monkeypatch)

def test_a_relation_sharing_a_value_is_not(tmp_path, monkeypatch)

def test_the_shared_value_need_not_be_the_only_one(tmp_path, monkeypatch)
    """
    Overlapping membership is the feature. A document legitimately in two
    areas must not be a finding merely for being in two.
    """

def test_a_document_in_no_relation_is_never_a_finding(tmp_path, monkeypatch)

def test_the_cross_link_is_walked_too(tmp_path, monkeypatch)
    """
    `compared_against` asserts two things are rivals for one job, which is
    as much a claim of commonality as succession is.
    """

def test_a_one_sided_declaration_is_walked_before_the_fixer_runs(tmp_path, monkeypatch)
    """`extended_by` on one side, nothing written back yet — still an edge."""

def test_a_line_can_be_unbound_while_every_step_is_bound(tmp_path, monkeypatch)
    """
    The case that makes this a second finding rather than the first one
    with a knob: A∩B = {x}, B∩C = {y}, A∩B∩C = empty.
    """

def test_a_line_sharing_one_value_throughout_is_not_a_finding(tmp_path, monkeypatch)

def test_every_edge_finding_sits_inside_a_path_finding(tmp_path, monkeypatch)
    """
    The containment that justifies reporting both: edges are a strict
    subset, so the sharp case is never lost among the diffuse ones.
    """

def test_a_single_valued_field_is_compared_by_equality(tmp_path, monkeypatch)
    """
    Equality and intersection are the same test once a scalar reads as a
    set of one, which is why the config needs no operator.
    """

def test_a_field_absent_on_one_end_shares_nothing(tmp_path, monkeypatch)

def test_a_chain_declaring_no_invariant_reports_nothing(tmp_path, monkeypatch)
    """
    The default that keeps the check from firing on relations which never
    asserted a shared field — the reason it is opt-in at all.
    """

def test_an_invariant_naming_an_undeclared_field_is_refused(tmp_path, monkeypatch)
    """
    Eagerly, like every other declaration: a field nothing holds would
    report every line and mean nothing.
    """

def test_the_report_names_both_findings(tmp_path, monkeypatch)

def test_the_report_says_so_when_nothing_is_declared(tmp_path, monkeypatch)

def test_the_report_is_a_configured_output(tmp_path, monkeypatch)

```

## tests/test_journal.py
```python
def jrnl(tmp_path: Path, granularity: str) -> Journal

def file_entry(j: Journal, stamp: str, title: str, body: str, tags: list[str] | None) -> Path

def test_path_is_derived_from_the_timestamp(tmp_path)

def test_path_and_created_round_trip(tmp_path)

def test_created_accepts_what_yaml_hands_back(raw, want)
    """
    Quoting decides whether the YAML parser returns a string, a date or a
    datetime. Making the author remember which one is a trap, not a rule.
    """

def test_new_steps_forward_on_a_collision(tmp_path)
    """Not a probability argument — the filesystem already knows."""

def test_new_writes_frontmatter_the_lint_accepts(tmp_path)

def test_entries_sort_by_time_not_by_filesystem_order(tmp_path)
    """
    The point of the scheme: what the log says happened first is a property
    of the record, not of the order the branches landed.
    """

def test_the_template_is_not_an_entry(tmp_path)

def test_granularity_decides_the_partition(tmp_path, granularity, keys)
    """
    The right book size depends on how fast a project writes, which is a
    measurement rather than a constant.
    """

def test_book_lists_its_contents(tmp_path)

def test_anchor_is_the_timestamp_not_the_title(tmp_path)
    """
    A title can be corrected. A heading-derived anchor would break every
    link to it silently, which is the failure polarity DP-3 rules out.
    """

def test_tags_are_shown_when_present(tmp_path)

def test_index_lists_books_newest_first(tmp_path)

def test_a_single_book_reads_as_one(tmp_path)

def test_this_repos_journal_is_filed_correctly()
    """The record Luria keeps of itself is the first consumer (ADR-009)."""

def test_entries_are_never_consumed()
    """
    A journal's sources persist — that is the whole difference from a
    collected view (ADR-012), and it is what makes staleness computable.
    """

def test_an_unused_journal_renders_nothing(tmp_path, monkeypatch)
    """
    The default config names a devlog. A project that never files an entry
    should not grow an empty `docs/devlog/`.
    """

def test_index_inlines_the_current_book(tmp_path)
    """
    Hot on top: the newest book's contents render on the journal's front
    page, newest entry first, so the current writing is one click from the
    entrypoint instead of two (ADR-021).
    """

def test_populate_created_fills_a_missing_field(tmp_path)

def test_populate_created_refills_an_empty_field(tmp_path)

def test_populate_created_respects_a_filed_value(tmp_path)
    """
    A field that *disagrees* with the path is two witnesses in conflict —
    a judgement for the lint to demand, never a mechanical overwrite.
    """

def test_populate_created_skips_a_path_that_implies_nothing(tmp_path)

def test_populate_created_writes_frontmatter_where_there_is_none(tmp_path)

```

## tests/test_link_targets.py
```python
def _project(root: Path, monkeypatch) -> None
    """
    A project with an index scheme and a journal, which is the layout that
    separates the two frames: a record document is read where it sits, a
    journal entry is assembled into `docs/log/`.
    """

def _note(root: Path, number: int, body: str) -> Path

def _entry(root: Path, body: str) -> Path

def test_a_target_that_resolves_is_silent(tmp_path, monkeypatch)

def test_a_target_that_resolves_to_nothing_is_reported(tmp_path, monkeypatch)

def test_a_journal_entry_resolves_from_where_it_renders(tmp_path, monkeypatch)
    """
    The whole point. `record/log.d/2026/01/01/` is five directories deep and
    renders into `docs/log/`, so the target that works is the one written for
    the view — and the arithmetic that looks right beside the source is wrong.
    Both assertions matter. Accepting the view-relative form is not evidence on
    its own: a check that resolved from the source directory would also have to
    reject it, and a check that resolved from *neither* would reject both.
    """

def test_urls_anchors_and_absolute_paths_are_not_checked(tmp_path, monkeypatch)
    """
    None of these name a file in this repo, so none of them can be dead
    here. A check that reported them would be unusable in prose that cites the
    web, which is most prose.
    """

def test_a_pattern_is_not_a_path(tmp_path, monkeypatch)
    """
    A URL template and a uid regex are link-shaped by accident. Both appear
    in config examples in this repo's own record, which is how they were
    found: `uid = "(\d{4})[.:](\d{4,5})"` reads as a link to `(\d{4,5})`.
    """

def test_an_example_in_code_is_not_a_citation(tmp_path, monkeypatch)
    """
    Same rule the reference checks use: markdown showing a link is not
    writing one.
    """

def test_a_fragment_does_not_hide_a_missing_file(tmp_path, monkeypatch)
    """
    `#section` is not checked, but the file it hangs off still is —
    otherwise appending an anchor would silence any dead link.
    """

def test_a_percent_encoded_target_resolves_to_the_real_name(tmp_path, monkeypatch)
    """
    A filename with a space is written `a%20note.md` in markdown and stored
    with the space on disk. Comparing the encoded form would report every one
    of them.
    """

def test_a_deliberate_target_is_acknowledged_not_deleted(tmp_path, monkeypatch)
    """
    The escape hatch, and it is per-target: acknowledging one placeholder
    must not silence the dead link three lines down.
    """

def test_a_directive_that_acknowledges_nothing_is_reported(tmp_path, monkeypatch)
    """
    A directive that silently does nothing is worse than no directive: it
    reads as considered when the consideration has expired.
    """

def test_the_class_is_failable(tmp_path, monkeypatch)
    """
    Emitted classes must be nameable in `fail_on` — the dial and the
    reporter read the same vocabulary.
    """

def test_a_clean_project_does_not_emit_the_class(tmp_path, monkeypatch)

```

## tests/test_lint.py
```python
def _listed(raw: str) -> list[str]
    """
    `'"a", "b"'` -> `["a", "b"]`.
    The fixtures built a TOML array by interpolating its innards. A YAML config
    takes the list itself, so the parsing that used to happen in the config
    parser happens here.
    """

def errors_for(project) -> list[str]

def test_agreeing_title_and_heading_pass(project)

def test_a_drifted_heading_is_reported(project)
    """The failure this exists for: the title is corrected in one copy only."""

def test_a_missing_title_is_reported(project)

def test_a_body_with_no_heading_is_not_a_disagreement(project)
    """
    Absence isn't drift. A fragment whose body opens with prose has nothing
    to contradict the frontmatter, and demanding a heading is a different rule
    from the one this check enforces.
    """

def test_the_check_covers_every_scheme(project)
    """
    Not just decisions — a principle's title drifts the same way, and more
    often, because principles are expected to be reworded (ADR-012).
    """

def journal_project(project) -> Path

def entry(root: Path, at: str, created: str | None, title: str) -> Path
    """
    `at` is where the file goes; `created` is what it claims — the two are
    separate arguments precisely so a test can disagree with itself.
    """

def journal_errors(project) -> list[str]

def test_an_entry_at_its_own_timestamp_passes(project)

def test_a_moved_entry_is_reported(project)
    """
    The failure this exists for: the ordering the scheme rests on says one
    thing and the frontmatter says another.
    """

def test_an_entry_with_no_created_is_reported(project)
    """
    When the path implies the timestamp, the error names the remedy —
    `luria repair` populates the field from it (#33).
    """

def test_an_entry_no_witness_can_date_is_reported_as_such(project)
    """
    A path that implies nothing leaves no witness to populate from, so the
    error asks the author instead of promising a remedy that won't come.
    """

def test_an_untitled_entry_is_reported(project)
    """
    The title is what the book's contents list shows, so it isn't optional
    the way `tags:` is.
    """

def test_the_template_is_exempt(project)

def version_errors(project) -> list[str]

def versioned(project, version: int, history: str) -> Path

def test_version_one_needs_no_history(project)

def test_a_bumped_version_with_no_history_is_reported(project)
    """
    A silent revision wearing a version number — which is the thing
    ADR-019 permits corrections *because* it rules out.
    """

def test_history_that_agrees_passes(project)

def test_history_that_lags_the_version_is_reported(project)

def generated_errors(project) -> list[str]

def test_a_hand_written_file_in_a_view_dir_is_a_violation(project)
    """
    The payoff of the read/write boundary: "don't hand-edit" is a checkable
    property, and its failure polarity points the right way — the stray file
    fails the build rather than quietly surviving beside the views.
    """

def test_a_stale_view_is_not_the_lint_s_question(project)
    """
    A branch carries the default branch's views, and files entries they do
    not show; that is not staleness the branch can fix, and `luria lint` runs
    there as it is. `luria index --check` asks the question on the default
    branch (ADR-068).
    """

def test_a_view_the_generator_no_longer_writes_is_not_a_stray(project)
    """
    A leftover that says it was generated is a stale view, not a
    hand-written one: main's copy of a tag page for a tag the branch
    dropped, say. `luria index` deletes it where views are committed.
    """

def dial_project(project, fail_on: str, mute: str) -> None
    """
    A project with a retired decision cited from a docs page, and the
    dials set to `fail_on` and `mute` (TOML list bodies, e.g.
    '"retired-citations"').
    """

def dial_errors(capsys) -> tuple[[list[str], str]]

def test_the_default_posture_is_warn_only(project, capsys)
    """
    Nothing configured, nothing fails — every argument for warn-first
    survives as the argument for warn-by-default (ADR-035).
    """

def test_a_promoted_class_fails_instead_of_printing(project, capsys)

def test_every_emitted_class_is_nameable_in_the_dial(project, capsys)
    """
    A class the linter can emit must be one the dial accepts.
    `legacy-spellings` was reported by `status_sections` but missing from
    FAILABLE, so a project asking to enforce it was told the class did not
    exist — the dial rejecting a notch it was already printing (DP-1). The
    assertion is over the whole vocabulary, not the one that bit.
    """

def test_an_acknowledged_row_never_fails(project, capsys)
    """
    The dial changes the consequence, not the accounting — `inactive-ok:`
    is the escape hatch under enforcement too.
    """

def test_a_wrong_notch_is_an_error(project, capsys)
    """
    A dial set to a notch that doesn't exist must not silently enforce
    nothing (DP-1).
    """

def test_pending_documents_can_be_promoted(project, capsys)

def workflow_project(project, text: str, fail_on: str) -> None

def test_a_temporary_code_in_a_workflow_is_a_warning_class(project, capsys)
    """
    On the workflow's own token the generation job's push would be
    refused: `luria concretize` rewrites the code with everything else, and
    that token may not modify `.github/workflows/`. A job pushing with
    workflow write has no such problem — so a warning class, on the dial.
    """

def test_a_project_on_the_workflow_token_fails_on_it(project, capsys)

def test_a_numbered_code_in_a_workflow_is_fine(project)

def formed_project(project, template_summary: str) -> None

def form_text_errors() -> list[str]

def test_a_summary_still_saying_what_the_form_says_is_reported(project)
    """
    Two Proposed decisions reached the published index saying
    "One-paragraph description of the decision" — the template's own
    instruction, filed as if it were the summary.
    """

def test_a_summary_of_the_document_s_own_passes(project)

def test_a_scheme_with_no_form_has_nothing_to_compare(project)

def test_a_muted_class_is_not_reported(project, capsys)
    """
    `mute` removes a class from the report entirely.
    Distinct from `fail_on`, which changes a finding's consequence. A project
    that has decided a whole check is not useful to it has nowhere to put an
    acknowledgement — the directives carry a reason at a *site*, and this
    kind of finding has none.
    """

def test_muting_one_class_leaves_the_others(project, capsys)
    """A mute is per-class, not a global off switch."""

def test_mute_rejects_a_class_that_does_not_exist(project, capsys)
    """
    Same rule as `fail_on`: a dial set to a notch that does not exist must
    say so rather than silently suppress nothing (DP-1).
    """

def test_a_class_cannot_be_both_enforced_and_hidden(project, capsys)
    """
    Not a precedence question. Guessing which the project meant would make
    one of the two settings a lie, so it is a configuration error.
    """

def test_enforcement_still_wins_over_a_conflicting_mute(project, capsys)
    """
    The conflict is reported AND the class still fails — a misconfigured
    mute must not be able to hide a check the same file asked to enforce.
    """

def test_acknowledged_uniformity_is_mutable(project, capsys)
    """
    It is not failable — a project cannot promote its own acknowledgement
    to a failure — but it is exactly the standing note a project may not want
    repeated on every run, so the two vocabularies are not the same list.
    """

```

## tests/test_migrations.py
```python
def _record_project(tmp_path, monkeypatch)
    """A project whose FXM-004 used to be FXL-4 — the post-migration shape."""

def test_the_alias_map_derives_from_formerly(tmp_path, monkeypatch)

def _git(root)

def _premigration_project(tmp_path, monkeypatch)
    """
    A project the day before its FXL scheme becomes FXM — documents,
    citations in three frames, a fixture number, and two remotes: SG is
    another project (its namespace survives), LU mirrors this one (its
    composed codes follow the rename).
    """

def _locked_project(tmp_path, monkeypatch)
    """
    The pre-migration project plus a committed lockfile: pins and
    filename maps for both the mirrored LU remote and the foreign SG one.
    """

def test_endorsements_travel_with_a_claimed_rename(tmp_path, monkeypatch)
    """
    The endorsement is of CONTENT, which a rename does not change — so
    the mirrored LU pin is re-keyed with both hashes intact (drift state
    included: prune-and-re-endorse would have laundered the unreviewed
    `seen`). The foreign SG entries survive byte-for-byte: the lockfile is
    never swept as text, which is what protects `"FXL-004"` under `"SG"`
    from a mask that cannot see nested keys as another project's
    namespace (#135).
    """

def test_dry_run_plans_the_pin_move_and_keeps_the_lockfile(tmp_path, monkeypatch, capsys)

def test_dry_run_prints_the_plan_and_changes_nothing(tmp_path, monkeypatch, capsys)

def test_rename_scheme_end_to_end(tmp_path, monkeypatch, capsys)

def test_a_rename_mirrors_each_citation_s_padding(tmp_path, monkeypatch)
    """
    `FXL-004` stays padded, `FXL-4` stays bare, and the anchor stays bare.
    The tail is one string with two spellings in play at once — the padded
    filename form and the bare prose form — so a rewrite has to answer
    "padded?" per citation rather than once per pair. Pinned because the
    provisional-tail work touched exactly this branch.
    """

def test_move_doc_lands_provisional_then_concretizes(tmp_path, monkeypatch)
    """
    A move arrives under a TEMPORARY code and is numbered afterwards.
    "The next free number" is no more a fact inside a migration than it is on
    a branch: every operation plans against the tree as it is now. So the move
    mints a temp code (ADR-049) and the concretizer — which runs where merges
    serialize — assigns the real one. The document ends up carrying BOTH
    aliases: the code it migrated from, and the temporary code it wore in
    between.
    """

def test_two_moves_into_one_scheme_do_not_collide(tmp_path, monkeypatch)
    """
    Two moves into one scheme, in one spec, must not claim one identity.
    With numbers they did: both read the same highest number and the second
    `git mv` overwrote the first — a document destroyed, and the dry-run
    printed two lines saying so in plain sight. Temporary codes make the
    collision structurally impossible rather than arithmetically avoided.
    """

def test_move_doc_supersede_copies_and_tombstones(tmp_path, monkeypatch)
    """
    Supersede copies rather than moves, and rewrites nothing.
    The tombstone names the provisional code; the concretizer rewrites it to
    the assigned number along with every other occurrence, so the status line
    ends up pointing at the real one without the migration having to know it.
    """

def test_new_migration_scaffolds_a_numbered_spec(tmp_path, monkeypatch)

def test_the_sweep_honors_unlinted_file(tmp_path, monkeypatch, capsys)
    """
    A file that declares its references quotes (`unlinted-file`, #37) is
    a page of specimens — the sweep leaves every spelling in it alone.
    """

def test_provisional_is_decided_in_one_place(tmp_path, monkeypatch)
    """
    `Pair.new_is_provisional` must ask the canonical predicate.
    The cheap version — `not tail.isdigit()` — looks equivalent and answers a
    different question: "this is not a number", which a malformed tail also
    satisfies. Pinned by asserting the two disagree exactly where they should.
    """

def test_a_same_render_move_keeps_its_links_untouched(tmp_path, monkeypatch)
    """
    The unlink pass must fire ONLY when the shape actually changes.
    Two index-rendered schemes address a document the same way, so a move
    between them is a pure spelling swap — dropping and rebuilding those links
    would be churn, and would quietly relink bare references the author left
    bare on purpose elsewhere in the file.
    """

def test_a_worded_citation_of_a_moved_document_is_rebuilt(tmp_path, monkeypatch)
    """
    A citation labelled in prose, not spelled as the code, still follows.
    `[design-principles #17](../design-principles.md#fxl-17)` is a live link to
    an anchor the move just vacated, and a code-shaped pattern walks straight
    past it. Worse, stripping it to its LABEL resurrects the problem: the bare
    `#17` left behind is itself a design-principle reference, which the fixer
    re-links to the address that was just vacated. The whole citation has to
    become the new code.
    """

def _worded_move_project(tmp_path, monkeypatch)
    """
    The premigration project plus a SOURCE FILE that cites FXL-4 two ways —
    by code and in prose — and a spec that moves FXL-4 into an index-rendered
    scheme.
    """

def test_the_relink_pass_stops_where_the_hyperlink_lint_stops(tmp_path, monkeypatch)
    """
    Rebuilding links must not reach files the linter never checks.
    The sweep walks every tracked file, because "does this text spell a code
    that moved?" is a question a `.py` comment answers as truthfully as a
    document does. Linking is a different question — code is quoted, not
    asserted, so a source file is exempt from the hyperlink lint — and running
    the fixer wider than the linter checks turned one two-document move into a
    469-file diff of markdown links inside Python comments.
    """

def test_a_worded_citation_in_code_follows_the_move(tmp_path, monkeypatch)
    """
    A prose-spelled citation names the document as surely as the code does.
    `design-principles #4` in a comment carries no code for the code swap to
    catch and, unlinked, no address for the address swap to catch. It is
    recognized by the same scanner that would have turned it into a link in a
    document, so the sweep can respell it — and must, or the move leaves a
    citation pointing at a document that is no longer there.
    """

def test_a_formerly_stamp_is_not_a_dangling_citation(tmp_path, monkeypatch)
    """
    The alias a move writes must not be reported as a broken reference.
    `formerly: FXL-004` names a code that resolves to no document *because the
    alias exists* — that is what the stamp is for. Counting it made every
    migration hand back one fresh "resolves to no document" warning per moved
    document, pointing at the files the migration had just written.
    """

```

## tests/test_narrow_titles.py
```python
def _listed(raw: str) -> list[str]
    """
    `'"a", "b"'` -> `["a", "b"]`.
    The fixtures built a TOML array by interpolating its innards. A YAML config
    takes the list itself, so the parsing that used to happen in the config
    parser happens here.
    """

def _project(root: Path, monkeypatch, terms: str, generalize: bool) -> None
    """
    A project with a VP scheme rendering to a document, and the dial set.
    `VP` rather than `DP`: a fixture that borrows a real sequence's prefix is
    the hazard the fixture-code rule exists for, and this repo's own principles
    are the corpus a narrow-title check would otherwise read.
    """

def _value(root: Path, number: int, title: str, body: str) -> Path

def test_no_vocabulary_means_no_check(tmp_path, monkeypatch)
    """
    The default posture: luria ships no nouns, so nothing fires.
    A project that has not thought about this must not be told it has a
    problem — and must not be told it is clean either. The class is absent.
    """

def test_a_scheme_that_does_not_claim_to_transfer_is_untouched(tmp_path, monkeypatch)
    """A decision is ABOUT something specific; naming it is correct."""

def test_a_local_noun_in_a_transferable_title_is_reported(tmp_path, monkeypatch)

def test_the_match_is_plural_tolerant_and_case_insensitive(tmp_path, monkeypatch)

def test_a_substring_is_not_a_match(tmp_path, monkeypatch)
    """
    `node` must not fire on "anode" — the alternation is word-bounded.
    The word has to genuinely CONTAIN the term, or the test passes whatever
    the pattern does. A first draft used "nodded", which does not contain
    "node" at all, and so held even with the boundaries removed.
    """

def test_another_sense_is_acknowledged_not_removed(tmp_path, monkeypatch)
    """
    The vocabulary keeps working elsewhere; this USE is the exception.
    Shrinking the vocabulary to silence one document is how the check stops
    protecting every other document.
    """

def test_the_class_is_failable(tmp_path, monkeypatch)
    """
    Emitted classes must be nameable in `fail_on` — the dial and the
    reporter read the same vocabulary.
    """

```

## tests/test_new.py
```python
def test_the_default_kind_is_the_journal(project)

def test_a_scheme_gets_the_next_free_number(project)

def test_the_template_is_copied_with_the_code_filled_in(project)

def test_named_fields_are_optional_but_honoured(project)

def test_a_fragment_takes_the_given_name(project)

def test_an_unnamed_fragment_is_stamped_like_a_journal_entry(project)
    """
    The default identity is the filing moment (ADR-036 v2). It used to be
    the git branch, which collided the first time a branch was restarted
    after a squash merge and refiled: `luria new changelog` reopened the
    MERGED fragment and muddled two PRs into one batch.
    """

def test_an_unknown_kind_names_what_this_project_scaffolds(project)

def test_a_comma_separated_tags_flag_survives_fire(project)
    """
    `luria new adr --tags record,mechanism` reaches `run` as a tuple:
    Fire reads a comma-separated argument as a Python literal. The
    scaffolder took `.split(",")` on it and crashed, so the one spelling
    the help text invites was the one that failed.
    """

def _plural_project(project, many: bool)

def test_a_plural_reference_flag_is_written_as_a_list(project)

def test_one_code_for_a_plural_reference_is_still_a_list(project)

def test_a_scalar_reference_flag_stays_scalar(project)

def test_a_field_absent_from_the_template_is_added_not_dropped(project)
    """
    `_sub_line` substitutes; a field the form does not scaffold matched
    nothing and the value vanished with the command reporting success.
    """

def test_an_undeclared_flag_is_refused_by_name(project)
    """
    Silently accepting an unknown field would write a key the scheme has
    no opinion about into every document a script files.
    """

def test_a_declared_flag_reaches_the_document_through_run(project, capsys)

def test_an_unfilled_summary_is_dropped_not_copied_from_the_form(project)
    """
    The form's `summary:` explains what a summary is for. A document
    scaffolded without one used to carry that explanation as its summary,
    and two Proposed decisions reached the published index saying it. The
    key goes; the comment above it stays as the instruction.
    """

```

## tests/test_number.py
```python
def write(root: Path, rel: str, text: str) -> Path

def project(tmp_path, monkeypatch, allocate: str) -> Path

def doc(root: Path, name: str) -> Path

def scheme()

def test_the_field_wins_over_the_filename(tmp_path, monkeypatch)

def test_the_filename_answers_when_the_field_is_absent(tmp_path, monkeypatch)
    """
    A record written before `number:` existed still reads — which is what
    makes the field introducible without a migration anyone has to run.
    """

def test_a_number_in_the_body_is_prose_not_a_claim(tmp_path, monkeypatch)
    """
    Not hypothetical: a line wrap in a real note put `number:` at column
        zero mid-sentence ("...here mainly for the 10%
    number: the record's
        optimizer practices..."). The frontmatter boundary is what keeps prose
        from claiming an identity.
    """

def test_a_temporary_document_has_no_number_yet(tmp_path, monkeypatch)
    """
    By design: a merge-allocated document holds no claim on the sequence
    until `luria concretize` assigns one (ADR-049).
    """

def test_the_cache_expires_when_the_file_changes(tmp_path, monkeypatch)
    """
    Keyed on the stat rather than reset by hand, so a writer that forgets
    to invalidate cannot serve a stale identity.
    """

def test_a_disagreement_is_a_finding(tmp_path, monkeypatch)

def test_agreement_is_silent(tmp_path, monkeypatch)

def test_an_absent_field_is_not_a_disagreement(tmp_path, monkeypatch)
    """
    It is the repairable case, and reporting it here would name a finding
    whose remedy is a different command.
    """

def test_repair_populates_the_field_from_the_path(tmp_path, monkeypatch)

def test_repair_is_idempotent(tmp_path, monkeypatch)

def test_repair_leaves_a_temporary_document_alone(tmp_path, monkeypatch)

def test_repair_never_invents_a_number(tmp_path, monkeypatch)
    """A file whose name carries no number has no witness to repair from."""

def test_new_writes_the_field(tmp_path, monkeypatch)

def test_new_leaves_it_out_for_a_merge_allocated_scheme(tmp_path, monkeypatch)

def test_write_number_replaces_rather_than_duplicates(tmp_path, monkeypatch)

def test_write_number_leaves_a_document_with_no_frontmatter_alone(tmp_path)

def test_concretize_writes_the_field_when_it_assigns_the_number(tmp_path, monkeypatch)
    """The one moment a merge-allocated document acquires a number at all."""

def test_unterminated_frontmatter_declares_nothing(tmp_path, monkeypatch)
    """
    `parse_frontmatter` treats an unclosed block as no frontmatter; reading
    identity has to agree, or the two disagree about what a document says.
    """

def test_an_indented_number_is_inside_another_field(tmp_path, monkeypatch)
    """
    A block scalar's continuation lines are indented, so the column-zero
    anchor is what keeps prose out of the identity.
    """

```

## tests/test_one_reader.py
```python
def test_no_module_opens_a_document_for_itself()

def _inside_read_document(text: str, at: int) -> bool
    """The fallback inside `read_document` itself, for a path it cannot stat."""

def test_two_consumers_parse_each_document_once(tmp_path, monkeypatch)
    """
    The behaviour the shape is for: a second pass over the same corpus
    costs no parses, whichever consumer asks.
    """

```

## tests/test_parallel.py
```python
def test_results_keep_input_order()

def test_exceptions_propagate_like_map()

def test_jobs_env_forces_serial(monkeypatch)
    """
    `LURIA_JOBS=1` is the escape hatch: straight tracebacks, honest
    profiles, and a concurrency suspicion ruled in or out without an edit.
    """

def test_jobs_env_garbage_falls_back_to_default(monkeypatch)

def test_empty_input_is_fine()

def test_outputs_identical_at_any_width(monkeypatch)
    """
    The determinism the staleness check rests on: the rendered views are
    byte-identical serial and wide.
    """

def boom(x)

```

## tests/test_pins.py
```python
def cite(project, text: str) -> None

def pinfile(project) -> dict

def serve(monkeypatch, body: bytes) -> None

def test_raw_url_rebases_the_blob_construction(project)
    """
    The pinned bytes must be the document, not GitHub's page around it —
    the page's markup churns under identical content.
    """

def test_raw_url_drops_a_document_anchor(project)
    """
    A fragment selects nothing server-side; the endorsement covers the
    document the anchor lands in.
    """

def test_a_url_template_has_no_stable_bytes_to_pin(project)
    """
    An arXiv abstract or a Jira ticket is a rendered page — hashing it
    would drift on its own schedule, and the pin would cry wolf.
    """

def test_a_declared_pin_url_makes_a_uid_remote_pinnable(project)
    """
    `url` is where a reader lands; `pin_url` is what a pin hashes. The
    declaration takes the same substitutions, so arXiv's immutable e-print
    stands behind the abstract page a reader sees.
    """

def test_a_declared_pin_url_wins_over_the_github_rebase(project)
    """
    The project's declaration is the strongest evidence there is — a
    remote that mirrors its record somewhere stabler than the repo can say
    so, and the construction steps aside.
    """

def test_a_scheme_level_pin_url_scopes_the_declaration(project)

def test_pin_stores_the_endorsed_hash(project, monkeypatch)

def test_pin_survives_a_refresh_and_vice_versa(project, monkeypatch)
    """
    One lockfile, two writers — a refresh must not lose the pins, nor a
    pin the discovered filenames.
    """

def test_refresh_moves_seen_and_never_endorsed(project, monkeypatch)
    """
    `endorsed` is a human's claim; only `--pin` may move it. The refresh
    records the observation, and the committed diff carries the drift.
    """

def test_an_unreachable_document_keeps_its_last_observation(project, monkeypatch)
    """
    Unreachable is not changed — inventing a new `seen` on a network error
    would report drift that never happened.
    """

def test_drift_is_read_offline_from_the_lockfile(project)
    """
    The whole point of committing both hashes: `luria lint` compares them
    without opening a socket, like every other check.
    """

def test_an_agreeing_pin_is_silent(project)

def test_a_pin_nothing_cites_is_reported(project)
    """
    A pin that outlived its citation is the lockfile's version of a stale
    directive — committed state that no longer governs anything.
    """

def test_bare_pin_syncs_to_the_declared_remote_and_prunes_the_rest(project, monkeypatch)
    """
    `pin = true` on a remote registers its whole namespace: a bare
    `--pin` endorses every cited code, and drops pins nothing cites.
    """

def test_bare_pin_leaves_unregistered_citations_alone(project, monkeypatch)
    """
    No config flag, no directive, no existing entry — nothing registers a
    pin, so a bare sweep must not invent one.
    """

def test_an_existing_pin_is_its_own_registration(project, monkeypatch)
    """
    An explicit `--pin CODE` once made the entry; a bare sweep keeps
    re-observing it while it is cited, declaration or none.
    """

def test_a_scheme_level_declaration_scopes_the_registration(project, monkeypatch)
    """`pin = true` on one scheme covers that code family and no other."""

def test_a_declared_citation_never_endorsed_is_reported(project)
    """
    The scheme-level counterpart of a flagged, unendorsed URL: the config
    says pinned, the lockfile says nothing, and silence would make the
    declaration decorative (DP-1).
    """

def test_a_declared_but_unpinnable_citation_names_the_remedy(project)
    """
    `pin = true` on a remote with no stable-bytes construction cannot be
    honoured — the row says so and names `pin_url`, instead of demanding a
    `--pin` that would refuse.
    """

def test_a_bare_sweep_never_launders_drift(project, monkeypatch, capsys)
    """
    The whole point of the two hashes is that drift crosses a human's
    desk. A scheduled bare `--pin` records the observation; only the
    explicit command endorses the change.
    """

def test_re_endorsing_clears_the_drift(project, monkeypatch)
    """
    The issue's loop closed: review the change, run the CLI, and the
    lockfile again says a human vouched for what is there (#135).
    """

def test_remote_drift_can_be_promoted_to_a_failure(project, monkeypatch, capsys)
    """
    The dial works for this class like any other (ADR-035): named in
    `fail_on`, the drifted pins fail the build instead of printing.
    """

def test_a_pin_flag_registers_a_cited_url(project)
    """
    Not every load-bearing citation is a foreign code — the flag lives
    where the URL is cited, same scopes as every directive.
    """

def test_a_flag_does_not_satisfy_itself(project)
    """
    The URL inside the directive's own comment must not count as the
    citation it governs — otherwise a flag whose link was deleted could
    never report itself stale.
    """

def test_a_flag_naming_a_code_is_redirected(project)
    """
    A foreign code needs no flag — `--pin CODE` already covers it — and a
    directive that looks armed while doing nothing is the quiet failure the
    problems report exists for (DP-1).
    """

def test_bare_pin_endorses_flagged_urls_and_prunes_unflagged(project, monkeypatch)

def test_an_unflagged_url_is_refused(project, monkeypatch, capsys)
    """
    The flag is the registration: a pin the prose doesn't carry would be
    invisible exactly where it governs.
    """

def test_url_drift_is_reported_and_re_endorsing_clears_it(project, monkeypatch)

def test_a_flag_never_endorsed_is_reported(project)
    """
    A flag that registered a pin nobody fetched is armed-looking and doing
    nothing — said, not silent (DP-1).
    """

def test_removing_the_flag_retires_the_pin(project)
    """
    The issue's escape hatch: a pin that fires too often costs one deleted
    comment, and the URL goes back to being an ordinary, unwatched link.
    """

def test_stale_flags_reach_the_lint(project)

```

## tests/test_prose_frontmatter.py
```python
def _project(root: Path, monkeypatch) -> None

def test_a_bare_reference_in_origin_is_rewritten(tmp_path, monkeypatch)

def test_a_data_field_is_still_data(tmp_path, monkeypatch)
    """
    `issue:` is read by value and never rendered — a link there is a link
    inside a data field, so the fixer must leave it alone.
    """

```

## tests/test_readme_site.py
```python
def at(project, toml: str) -> Path

def test_the_region_carries_the_derived_url(project)

def test_a_project_that_derives_no_url_renders_nothing(project)
    """
    A non-GitHub issue URL derives no base_url, and inventing one would be
    a link to a page that does not exist.
    """

def test_rewrite_replaces_only_the_named_region(project)

def test_a_readme_without_the_region_is_left_alone(project)

def test_rewriting_twice_changes_nothing(project)

def test_the_two_regions_do_not_collide(project)
    """
    `luria:badges` and `luria:site` are separate markers so a project can
    take one without the other, and so neither region's meaning has to widen
    to hold the other's content.
    """

def test_a_record_that_publishes_and_does_not_link_is_reported(project)

def test_a_hand_written_link_satisfies_it(project)
    """
    The finding is 'your README does not point at the site you publish',
    not 'you must use our marker'. A project that wrote the link in its own
    prose has already done the thing.
    """

def test_a_record_that_does_not_publish_is_not_reported(project)
    """
    `base_url` derives for every GitHub project whether or not anyone
    deploys, so it cannot scope this on its own. A record that lives only in
    its repository says so, and the guard goes quiet — a guard opts out
    rather than being argued with (DP-10).
    """

def test_a_record_with_no_readme_is_not_reported(project)

def test_lurias_own_readme_links_its_site()
    """
    Fired on the real corpus, not only a fixture: the repository this
    ships from publishes a site and must say so on its front page.
    """

```

## tests/test_record_doc.py
```python
def unusual(tmp_path, monkeypatch)
    """A project whose record shares no vocabulary with Luria's own."""

def test_names_every_scheme_the_project_declared(unusual)

def test_names_every_journal_including_the_second(unusual)

def test_names_the_fragment_directory_and_its_target(unusual)

def test_names_each_remote_by_the_prefix_a_citation_carries(unusual)

def test_filing_table_offers_exactly_what_the_cli_dispatches_on(unusual)
    """
    The commands are the CLI's own mapping, so the table cannot advertise
    a kind `luria new` would reject — the drift this page exists to not have.
    """

def test_a_new_family_appears_without_touching_the_renderer(unusual)
    """The load-bearing claim, fired directly rather than inferred."""

def test_settings_table_shows_what_changed_and_not_what_did_not(unusual)

def test_a_nested_table_is_one_row_not_one_row_per_colour(project)
    """
    A theme is one choice with two dozen colours in it. Flattened all the
    way it buries every other row, which is how a diff stops being readable.
    """

def test_family_tables_stay_out_of_the_settings_diff(unusual)
    """
    They are the sections above, and a declared family is replaced whole
    rather than merged — "differs from the default" is not a question that
    means anything about one.
    """

def test_the_page_is_the_same_after_the_generator_has_run(unusual)
    """
    Idempotence, and it has bitten once: a first draft asked the
    filesystem whether each path was a directory, so a directory `luria index`
    created on its own run flipped a trailing slash — the page rendered, was
    written, and then compared unequal to itself. `luria index && luria lint`
    on a fresh `luria init` is where it surfaced.
    """

def test_the_page_lands_where_the_docs_surface_is(unusual)

def test_the_fixer_leaves_it_alone(unusual)
    """
    It is made of example codes — `RFC-001` names nothing. Rewriting them
    into links would report the page to itself on the next lint.
    """

def test_the_page_says_when_no_scheme_demands_more_than_the_standard_fields(unusual)

def test_the_page_lists_each_obligation_with_where_it_was_declared(unusual)

```

## tests/test_ref_status.py
```python
def scan(project, body, name, retired, active)
    """A project with one retired and one Active decision, plus `body`."""

def codes(docs)

def test_finds_citations_with_line_numbers(project)

def test_repeated_reference_on_one_line_is_one_site(project)
    """Two mentions in a sentence are one place to go look."""

def test_a_document_does_not_cite_itself(project)
    """Every decision's own title names it; that is not a reference to follow."""

def test_only_retired_documents_are_flagged(project)

def test_historical_records_are_out_of_scope()
    """
    A dated record is true about the day it was written, forever. Scanning
    it produces permanent, unactionable rows.
    """

def test_journals_are_out_of_scope_entries_and_books_alike()
    """
    A journal is a dated record too (ADR-020), and its entries are *nested*
    — which is why the check is `is_historical` rather than a membership test
    on `path.parent`.
    """

def test_configured_code_globs_are_in_scope()

def test_line_annotation_excuses_its_own_line(project)

def test_line_annotation_excuses_the_line_below(project)
    """So it can be written above the sentence it excuses."""

def test_a_bare_annotation_does_not_reach_across_a_blank_line(project)
    """
    The suffix is the only thing that decides scope
    ([ADR-008](../record/decisions.d/ADR-008.md)).
    """

def test_a_standalone_block_annotation_governs_what_it_introduces(project)

def test_block_annotation_covers_its_paragraph(project)

def test_file_annotation_covers_the_whole_document(project)

def test_annotation_works_in_a_code_comment(project)

def test_annotation_only_excuses_the_codes_it_names(project)

def test_bare_numbers_are_rejected(project)
    """
    The vocabulary has to survive a second reference scheme, so a code
    carries its prefix ([ADR-006](../record/decisions.d/ADR-006.md)).
    """

def test_mixed_bare_number_is_rejected(project)

def test_unknown_code_is_reported(project)

def test_annotation_for_an_active_document_is_stale(project)

def test_annotation_with_no_matching_reference_is_stale(project)

def test_summary_names_the_acknowledged_count(project)
    """Suppression is never silent — the line says how many it hid."""

def test_summary_counts_every_site_even_when_they_are_not_listed(project)
    """
    The console caps at five sites per document; the count never caps, so
    the report can't read as "covered everything" when it elided most of it.
    """

def test_spread_prefers_distinct_files(tmp_path)

def test_report_never_fails_the_build()
    """
    It is a warning. `luria lint` must not start failing on a citation that
    may be correct.
    """

def test_a_second_scheme_needs_no_code_change(project)
    """
    A prefix and a directory, per
    [ADR-006](../record/decisions.d/ADR-006.md).
    """

def test_the_vocabulary_is_scheme_agnostic()
    """
    `inactive-ok`, not `adr-ok` — the annotation names a prefixed code, so a
    second scheme is config rather than a fork.
    """

def test_a_code_naming_no_document_is_reported(project)
    """
    It used to be dropped: the fixer can't link it, so the lint said
    nothing — and that silence hid ten stale numbers from another project.
    """

def test_a_resolvable_code_is_not_dangling(project)

def test_unresolved_ok_retires_one(project)

def test_unresolved_ok_is_scoped_like_every_other_directive(project)
    """
    No per-directive defaults: the suffix decides, and a blank line between
    the annotation and what it governs needs `-block`.
    """

def test_unresolved_ok_naming_a_real_document_is_malformed(project)
    """
    The inverted check. `inactive-ok` is wrong when it names a code that
    doesn't resolve; this one is wrong when it names a code that does — so an
    annotation that stops applying is reported either way.
    """

def test_a_code_inside_a_url_is_not_a_citation(project)
    """
    Linking out to another project's decision is the *correct* way to name
    a foreign document, and the URL contains its code. Counting that as a local
    reference would report every such link as dangling — which is exactly what
    broke the `luria init` template's own scaffolded lint.
    """

def test_a_directive_naming_a_code_is_not_citing_it(project)
    """
    True of a live annotation and of an example of one alike — otherwise
    documenting the syntax inflates the report, and an annotation excuses
    itself and can never go stale.
    """

def test_a_frontmatter_field_is_a_site_that_a_yaml_comment_can_excuse(project)
    """
    `superseded_by:` naming a document that was itself later retired is
    reported at its line like a sentence would be. Before the frontmatter's
    own comments were read, the only spelling that reached it was the
    file-scoped one — broader than the finding.
    """

def test_a_frontmatter_site_without_a_comment_is_still_reported(project)

def temp_decision(root: Path, tail: str, status: str, title: str) -> Path
    """A merge-allocated document, before `luria concretize` numbers it."""

def test_a_temp_coded_document_is_loaded_with_its_status(project)
    """
    It was not, and the file carried a status the whole time.
    `Scheme.documents()` keys by number and skips a file it cannot get one
    from, so a merge-allocated document never reached `load_docs()` and the
    status checker held no record of it — not "no status", no document.
    """

def test_a_temp_code_is_a_citation_site(project)
    """
    The other half. `CODE_RE` required digits, so the citing text was not
    a site either — both blind spots had to hold, and both did.
    """

def test_citing_a_proposed_temp_document_is_reported(project)
    """
    The finding the anthology only saw after its merge concretized the
    codes, on `main`, in a file nobody was editing.
    """

def test_an_acknowledgement_covers_a_temp_code(project)
    """
    Whatever the checker can report, a directive has to be able to
    excuse — otherwise the finding is one nobody can clear.
    """

def test_an_active_temp_document_is_not_flagged(project)
    """Being temporary is not being retired."""

```

## tests/test_relations.py
```python
def write(root: Path, rel: str, text: str) -> Path

def project(tmp_path, monkeypatch, extra: str) -> Path

def note(root: Path, number: int, title: str) -> Path

def test_a_converse_must_name_a_declared_reference(tmp_path, monkeypatch)

def test_a_converse_must_be_mutual(tmp_path, monkeypatch)
    """
    The converse of the converse is the relation. A half-declaration
    leaves one direction completing and the other not.
    """

def test_a_converse_must_point_at_the_same_scheme(tmp_path, monkeypatch)

def test_both_sides_of_a_pair_hold_a_list(tmp_path, monkeypatch)
    """Completion writes into either side, and N documents can extend one."""

def test_a_relation_is_its_own_converse_when_it_says_so(tmp_path, monkeypatch)

def test_a_directed_relation_completes_into_its_converse(tmp_path, monkeypatch)
    """
    The correction. `extends` is directed and is completed anyway —
    into `extended_by`, where the fact is true.
    """

def test_completion_runs_in_both_directions(tmp_path, monkeypatch)
    """Declaring the converse is as good as declaring the relation."""

def test_a_relation_with_no_converse_is_never_completed(tmp_path, monkeypatch)
    """
    The user's condition: absent a declared duality, inventing the
    reverse edge is a guess, so nothing is written and nothing is reported.
    """

def test_a_symmetric_relation_completes_into_itself(tmp_path, monkeypatch)
    """Self-converse is symmetry — the same rule, not a second one."""

def test_a_relation_is_never_mirrored_into_its_own_field(tmp_path, monkeypatch)
    """The constraint that survives: A extends B does not make B extend A."""

def test_writing_the_back_reference_clears_the_finding(tmp_path, monkeypatch)

def test_completing_is_idempotent(tmp_path, monkeypatch)

def test_without_fix_nothing_is_written(tmp_path, monkeypatch)

def test_a_scalar_field_becomes_a_list_rather_than_losing_a_value(tmp_path, monkeypatch)
    """
    `many` accepts one code written as a scalar. Appending must keep the
    value that was there — the failure would be silent and delete a relation.
    """

def test_a_contradiction_across_the_pair_is_not_completable(tmp_path, monkeypatch)
    """
    `extends: B` and `extended_by: B` on one document says B is both
    older and newer. There is no side to write; a person has to choose.
    """

def test_the_finding_names_the_field_it_would_write(tmp_path, monkeypatch)

def test_link_fix_completes_by_default(tmp_path, monkeypatch)

def test_links_only_reproduces_the_old_behaviour(tmp_path, monkeypatch)

def test_the_class_is_promotable_and_wired(tmp_path, monkeypatch)

def commit(root: Path, message: str) -> None

def edit(root: Path, number: int, old: str, new: str) -> None

def test_a_side_added_since_the_last_commit_is_propagated(tmp_path, monkeypatch)

def test_a_side_removed_since_the_last_commit_prunes_the_other(tmp_path, monkeypatch)
    """
    The bug this exists to fix. The author deletes the relation from the
    document that declared it; the back-reference must go, not come back.
    """

def test_pruning_is_idempotent(tmp_path, monkeypatch)

def test_a_pruned_field_that_empties_is_removed_entirely(tmp_path, monkeypatch)
    """
    A bare `extended_by:` with nothing under it is not valid frontmatter
    for a reference field, and reads as a relation nobody can name.
    """

def test_a_pruned_field_keeps_its_other_codes(tmp_path, monkeypatch)

def test_removing_both_sides_needs_no_repair(tmp_path, monkeypatch)

def test_one_side_added_while_the_other_was_removed_is_a_conflict(tmp_path, monkeypatch)
    """
    Both edits are deliberate and they contradict. Writing either loses
    one of them, so the fixer reports and touches nothing.
    """

def test_an_unchanged_one_sided_pair_still_completes(tmp_path, monkeypatch)
    """
    The migration path: a record that predates the fixer has one-sided
    pairs at HEAD too, and nothing has changed. Adding is the safe reading —
    a deletion the author repeats becomes a change, and prunes.
    """

def test_a_document_git_has_never_seen_reads_as_added(tmp_path, monkeypatch)

def test_without_git_everything_reads_as_added(tmp_path, monkeypatch)
    """
    No repository, no baseline — the fixer keeps its old behaviour rather
    than refusing to work.
    """

def test_a_symmetric_relation_prunes_too(tmp_path, monkeypatch)

def test_the_finding_says_which_way_the_fixer_will_go(tmp_path, monkeypatch)

def test_a_converse_field_is_not_a_citation_site(tmp_path, monkeypatch)
    """
    `extends:` is exempt because a predecessor being retired is what a
    line looks like. `extended_by:` says the same fact from the far end, so
    exempting one and not the other would report every completed edge.
    """

def grouped(tmp_path, monkeypatch) -> Path

def test_a_repair_that_would_break_a_document_is_not_applied(tmp_path, monkeypatch)

def test_a_blocked_repair_says_which_rule_stopped_it(tmp_path, monkeypatch)

def test_a_repair_that_breaks_nothing_is_still_applied(tmp_path, monkeypatch)
    """The guard must not stop the ordinary case."""

def test_a_document_already_in_violation_is_not_held_hostage(tmp_path, monkeypatch)
    """
    Only *new* violations block. A document that already breaches its
    contract elsewhere still gets its back-reference, or one pre-existing
    mistake would freeze every relation the document is in.
    """

```

## tests/test_relations_crossing.py
```python
def _project(tmp_path, monkeypatch, extra: str | dict) -> Path

def _lit(root: Path, n: int, body: str) -> None

def _sota(root: Path, n: int, body: str) -> None

def test_a_crossing_pair_can_be_declared(tmp_path, monkeypatch)

def test_the_converse_must_point_back_at_the_declaring_scheme(tmp_path, monkeypatch)
    """
    A field on the far scheme with the right NAME is not the converse if it
    points somewhere else. Here `LIT` holds a self-consistent pair of its own,
    so the only defect left is that `SOTA.introduced_by` names a converse that
    does not point back at `SOTA`.
    """

def test_the_converse_must_exist_on_the_far_scheme(tmp_path, monkeypatch)
    """
    It is looked up on the scheme whose codes the field holds — which is
    the message a reader needs, since the obvious guess is the near one.
    """

def test_it_still_has_to_be_mutual(tmp_path, monkeypatch)
    """Half a pair completes in one direction only, crossing or not."""

def test_the_far_side_is_written_on_the_other_scheme(tmp_path, monkeypatch)
    """The whole point: state it once, on whichever end knows it."""

def test_it_completes_from_the_far_end_too(tmp_path, monkeypatch)

def test_an_agreeing_crossing_pair_needs_nothing(tmp_path, monkeypatch)

def test_a_code_that_lands_in_no_document_is_not_an_edge(tmp_path, monkeypatch)
    """
    A dangling reference is the contract's finding, not a repair here —
    and which scheme it has to land in depends on the field.
    """

def test_edges_reads_a_crossing_relation_from_either_side(tmp_path, monkeypatch)
    """Before anyone runs the fixer, both readings already agree."""

def test_the_one_sided_pair_is_reported(tmp_path, monkeypatch)

def test_same_scheme_pairs_are_unaffected(tmp_path, monkeypatch)
    """The generalization has to leave the existing case alone."""

```

## tests/test_remotes.py
```python
def with_remote(project, extra: str | dict) -> Path

def lockfile(project, entries: dict[[str, str]]) -> None

def test_code_only_convention_is_the_default(project)
    """
    Right whenever the remote follows ADR-013, and it is Luria's own
    convention — so a remote that uses it needs one config line.
    """

def test_a_discovered_filename_wins(project)
    """
    The only rung that can resolve a slug-named remote — no template can
    turn a number into `adr-032-changelog-ci-collection.md`.
    """

def test_discovery_is_authoritative_once_done(project)
    """
    A code absent from a lockfile that was read *from the remote* names no
    document there. Guessing a filename anyway is how `DP-004` produced a
    confident link to a file that has never existed.
    """

def test_no_lockfile_means_fall_back_rather_than_refuse(project)
    """
    Never refreshed is not the same claim as "not there" — a project that
    has not run discovery still gets working links for a conventional remote.
    """

def test_an_explicit_template_overrides_everything(project)

def test_an_unregistered_prefix_is_not_a_namespace(project)
    """
    `MY-ADR-004` in prose must stay prose. The pattern is built from the
    registry precisely so unregistered text is never claimed.
    """

def test_the_finder_claims_the_whole_composed_span(project)
    """`UP-ADR-032` must not also be read as a local `ADR-032`."""

def test_a_local_code_still_reads_as_local(project)

def test_the_fixer_writes_a_url_not_a_relative_path(project)
    """
    A different repository, so no `link_base` applies and the same target is
    right from every file.
    """

def test_an_unresolvable_foreign_code_is_not_linked(project)
    """
    The lint never demands a rewrite the fixer wouldn't make, so a code the
    remote doesn't have stays bare — and is reported instead.
    """

def test_the_citation_scan_does_not_read_a_local_code_out_of_it(project)
    """
    `UP-ADR-012` must not count as a citation of *this* project's ADR-012 —
    which would keep a local retired decision looking cited forever.
    """

def test_an_unresolvable_foreign_code_is_reported(project)
    """
    Blanking the composed span must not make it invisible — a foreign code
    that names nothing is still a reference nobody can follow (ADR-014).
    """

def test_the_annotation_validator_reads_the_composed_code(project)
    """
    `unresolved-ok: UP-ADR-012` must be checked against the *remote*. Reading
    `ADR-012` out of the middle asks the wrong project, and the annotation is
    then reported as stale for a reason that isn't true.
    """

def test_discovery_reads_both_filename_conventions(tmp_path)
    """
    A remote that predates ADR-013 has slugs; one that follows it doesn't.
    Both have to read, or adoption means renaming somebody else's repo.
    """

def test_the_remotes_own_config_says_where_its_documents_live()
    """
    Fetched from the remote and parsed, rather than guessed — which is the
    whole point of a config file existing.
    """

def test_an_unparseable_upstream_config_leaves_the_default_standing()
    """
    A remote may have a `luria.yaml` this version can't read. Falling back
    is right; crashing on someone else's file is not.
    """

def test_discovery_says_why_it_found_nothing(project)
    """
    A discovery that silently returns nothing is indistinguishable from a
    remote with no documents (DP-1) — and it returns None, not {}, because an
    unreadable remote and an empty directory are different claims.
    """

def test_failed_discovery_never_writes_an_authoritative_empty_map(project, monkeypatch, capsys)
    """
    Surfaced by pinning against this repo's own remotes: a private remote's
    failed discovery wrote `{}` to the lockfile, and an empty map is
    *authoritative* — every one of its references then resolved to "absent
    from the remote". Failure must leave the remote off the lockfile (or keep
    the map it had), so it stays on the code-only convention.
    """

def hand(project, body: str, name: str)

def test_hand_written_url_is_reported(project)
    """
    A hand URL is sometimes the only correct citation — and it is frozen at
    writing time, so it is reported until acknowledged, never silently kept.
    """

def test_constructed_url_is_not_reported(project)

def test_url_ok_acknowledges_the_link(project)

def test_url_ok_matches_unpadded_codes(project)
    """
    `UP-ADR-32` and `UP-ADR-032` are one document — the annotation should
    not care which spelling either side used.
    """

def test_unused_url_ok_is_stale(project)
    """A directive that silently does nothing is worse than no directive."""

def test_url_ok_on_a_constructed_link_is_stale(project)
    """
    The inverted validity check, same as `unresolved-ok`: acknowledging a
    link that matches the construction excuses nothing.
    """

def test_a_quoted_hand_link_is_a_specimen_not_a_citation(project)

def test_document_scheme_constructs_a_file_anchor(project)
    """
    A document-rendered scheme's documents are sections, not files — the
    construction is the assembled page plus an anchor.
    """

def test_anchor_defaults_to_the_stable_anchor_shape(project)
    """
    The prefix lowercased plus the number, unpadded — the shape Luria's
    own document render emits, so a remote on current conventions needs only
    the `document` line.
    """

def test_anchor_template_is_configurable(project)

def test_scheme_dir_scopes_the_file_convention(project)
    """
    Different code families in one namespace construct into different
    places; the remote-level `dir` keeps serving the rest.
    """

def test_scheme_url_template_wins(project)

def test_lockfile_authority_does_not_cover_document_schemes(project)
    """
    The lockfile maps *files*, which is all discovery can see. A section of
    a document never appears in a directory listing, so its absence from the
    lockfile is not evidence — the anchor construction must survive it.
    """

def test_url_ok_retires_when_the_construction_catches_up(project)
    """
    The loop ADR-022 promised: configure the scheme, delete the hand URL,
    and a leftover acknowledgement reports itself stale.
    """

def test_uid_remote_constructs_through_the_template(project)

def test_uid_capture_groups_index_the_template_by_position(project)
    """
    {1}, {2}… are the uid pattern's capture groups; {0}/{uid} is the whole
    tail — so one template can restructure the identifier.
    """

def test_uid_is_exact_never_normalised(project)
    """
    `ADR-32` and `ADR-032` are one document; `2403.05530` is itself. A uid
    must survive canonicalisation untouched — zero-padding an arxiv id would
    quietly cite a different paper.
    """

def test_the_delimiter_is_configurable(project)

def test_unconfigured_prefixes_do_not_match(project)
    """
    The pattern is built from config: `FAKE-1234.5678` must not be read as
    a namespace just because it is shaped like one.
    """

def test_uid_remote_without_a_template_constructs_nothing(project)
    """
    One rung only — with no template there is nothing to guess with, and
    "" is what makes ref-status report the citation as dangling (DP-1).
    """

def test_lockfile_never_vetoes_a_uid_remote(project)

def test_scheme_shaped_references_still_scan_beside_uid_remotes(project)

def test_url_ok_covers_uid_remotes_too(project)
    """
    A hand URL for a uid code is the same acknowledged state — the check
    and the directive are shape-agnostic because both go through the remote's
    own parser.
    """

def test_fixture_prefix_resolves_to_the_convention_note()
    """
    Dogfood, corpus-dependent: this repo registers `FX` (#38) so a fixture
    code is resolvable by construction — it points at the note that explains
    it, and can never collide with the real sequence.
    """

def test_uris_read_is_url_by_its_long_name(project)

def test_agreeing_spellings_are_allowed(project)

def test_conflicting_spellings_are_a_config_error(project)
    """
    `url` IS `uris.read` — two values for one setting must fail loudly,
    not crown a silent winner.
    """

def test_a_custom_bytes_template_uses_the_discovered_filename(project)
    """
    A GitLab-style raw scheme is a template, not a builtin — and
    {filename} feeds ANY template, carrying the lockfile's authority with
    it: the map's silence vetoes a custom construction exactly as it vetoes
    the shipped one.
    """

def test_any_name_renders_and_an_undeclared_one_is_empty(project)
    """
    `read` and `bytes` are the shipped names, not the vocabulary's edge —
    a new relation is a template waiting for a consumer, never a subsystem.
    """

def test_an_unfillable_template_renders_nothing_rather_than_guessing(project)
    """
    A chosen template that cannot fill a variable renders "" instead of
    falling back to the convention — a misspelled variable stays visible as
    a dangling reference rather than hiding behind a working guess (DP-1).
    """

def test_a_read_template_implies_no_bytes(project)
    """
    The retired regex rebased ANY rendered URL that happened to be
    blob-shaped. Bytes now come from declarations and construction shapes
    only — a remote whose read is a template has said nothing about where
    its bytes live, and a guessed raw URL would be a claim nobody made.
    """

def test_uid_remotes_render_named_uris_through_their_groups(project)

def test_scheme_level_uris_scope_to_the_family(project)

def test_a_remote_issue_links_to_the_remote_tracker(project)
    """
    `UP-#7` means upstream's issue 7.
    Before this, the `UP-` was inert prose and the `#7` resolved through the
    *citing* project's `issue_url` — a well-formed link to a completely
    different project's issue 7, which in a mature tracker exists and is about
    something else. Nothing could catch it: the target resolves, so
    `broken-targets` was satisfied.
    """

def test_an_explicit_issue_url_wins(project)
    """
    A forge that is not GitHub is a line of config, not a subsystem —
    the same bargain the `uris` table already makes for documents.
    """

def test_a_remote_with_no_repo_has_no_tracker(project)
    """
    `ARXIV-#5` names nothing. A remote reached by a `url` template has no
    issues, and guessing one would be the same silent wrongness in a new
    place — so it resolves to nothing and the caller reports it.
    """

def test_the_prefix_claims_the_whole_span(project)
    """
    The bug was one of scanning, not only of construction: the local issue
    pattern read `#7` out of the middle of `UP-#7`. The remote reference has
    to claim its span first, exactly as `UP-ADR-013` already does.
    """

def test_a_bare_issue_still_links_locally(project)
    """The narrow fix stays narrow: an unprefixed `#7` is this project's."""

def test_a_remote_issue_is_written_as_a_link(project)

```

## tests/test_repair.py
```python
def test_repair_populates_a_missing_created(project)

def test_repair_links_a_bare_reference(project)

def test_repair_is_idempotent(project)
    """The job that pushes a repair runs again on what it pushed."""

def test_repair_clears_what_the_lint_reported(project)
    """The lint names `luria repair` as the remedy; the remedy has to work."""

def test_index_writes_no_source(project)
    """
    `luria index` is views only: a source it used to repair is left as
    filed, for `luria repair` and the commit point that belongs to.
    """

```

## tests/test_reports_by_scheme.py
```python
def write(root: Path, rel: str, text: str) -> Path

def project(tmp_path, monkeypatch, schemes) -> Path
    """A record with one or two schemes, declared in the order given."""

def doc(root: Path, prefix: str, number: int, status: str, date: str) -> Path

def test_two_schemes_render_as_separate_sections(tmp_path, monkeypatch)

def test_a_row_sits_under_its_own_scheme(tmp_path, monkeypatch)

def test_section_order_follows_the_config_not_the_alphabet(tmp_path, monkeypatch)
    """
    `pending()` walks `current().schemes`, which is declaration order. A
    project decides which of its families a reader meets first, the same way
    `tags.yaml` decides the order of topics.
    """

def test_a_scheme_with_nothing_pending_gets_no_section(tmp_path, monkeypatch)
    """
    Three declared schemes, two with an open question. The third is not an
    empty heading — a section per declared scheme would report absence as a
    row of nothing.
    """

def test_one_scheme_stays_flat(tmp_path, monkeypatch)
    """
    A single-scheme record gains nothing from a heading naming the only
    family it has, and luria's own record is one of those.
    """

def test_rows_stay_oldest_first_within_a_section(tmp_path, monkeypatch)

def test_the_headline_still_counts_every_scheme(tmp_path, monkeypatch)
    """
    The total is what the badge publishes, and it is a fact about the
    record rather than about any one family.
    """

def test_the_badge_count_is_unchanged_by_the_grouping(tmp_path, monkeypatch)

def test_every_code_is_still_a_link(tmp_path, monkeypatch)
    """
    The reader arrived from a badge, not a grep prompt — the report's own
    standing rule.
    """

```

## tests/test_required_when.py
```python
def write(root: Path, rel: str, text: str) -> Path

def project(tmp_path, monkeypatch, sota_extra: str) -> Path

def check(status: str, extra: str) -> list[str]

def test_a_provisional_document_must_carry_the_field(tmp_path, monkeypatch)

def test_an_active_document_need_not(tmp_path, monkeypatch)
    """Nothing is waiting, so there is nothing to state."""

def test_a_provisional_document_that_carries_it_is_clean(tmp_path, monkeypatch)

def test_every_listed_value_triggers_it(tmp_path, monkeypatch)

def test_the_finding_names_the_value_that_triggered_it(tmp_path, monkeypatch)
    """
    A conditional requirement that reports only the rule leaves the reader
    to work out which of their fields turned it on.
    """

def test_the_finding_cites_the_declaration(tmp_path, monkeypatch)

def test_a_status_note_does_not_defeat_the_condition(tmp_path, monkeypatch)
    """
    `Proposed — pending a replication` is the one status vocabulary's
    spelling for a qualified status (ADR-003); matching the raw string would
    read it as a different status and quietly exempt the document.
    """

def test_it_composes_with_a_reference_declaration(tmp_path, monkeypatch)
    """
    `required_when` is a property of a field, so it applies to a typed one
    the same way.
    """

def test_unconditional_and_conditional_together_is_a_config_error(tmp_path, monkeypatch)
    """
    `required = true` already demands it always; the condition would say
    nothing, which is the quiet failure a declaration exists to remove.
    """

def test_two_conditions_is_a_config_error(tmp_path, monkeypatch)
    """
    One field against a set of values. Two keys would need an `and`/`or`
    nobody has written down, and a config that guesses is worse than one
    that refuses.
    """

def test_an_empty_value_list_is_a_config_error(tmp_path, monkeypatch)
    """A condition that can never be true is a requirement that never fires."""

def test_a_field_table_declaring_nothing_is_still_an_error(tmp_path, monkeypatch)

def test_the_contract_describes_the_condition(tmp_path, monkeypatch)
    """
    `docs/record.md` prints what an entry must carry; a requirement that
    only exists at some statuses has to say so, or the generated page is a
    lie about the scheme.
    """

def test_the_scheme_is_not_empty_for_a_condition_alone(tmp_path, monkeypatch)
    """
    `Contract.empty` decides whether a scheme has a contract worth
    printing; a scheme whose only declaration is a conditional one has.
    """

def test_a_misspelled_condition_field_is_refused(tmp_path, monkeypatch)

def test_the_refusal_names_what_the_scheme_could_have_meant(tmp_path, monkeypatch)

def test_a_miscased_status_value_is_refused(tmp_path, monkeypatch)
    """`proposed` is not a status, and a condition naming it never holds."""

def test_a_status_outside_what_the_scheme_declares_is_refused(tmp_path, monkeypatch)
    """
    A scheme narrowing its status vocabulary narrows what a condition on
    `status` can name too.
    """

def test_a_condition_on_tags_is_accepted(tmp_path, monkeypatch)
    """
    `tags` is nameable because the scheme declares it — which is the whole
    of what `tags` being an axis means since ADR-098.
    """

def test_a_condition_on_a_declared_reference_is_accepted(tmp_path, monkeypatch)

def test_a_condition_on_a_free_text_field_leaves_its_values_alone(tmp_path, monkeypatch)
    """
    A field with no vocabulary has no set to check against, and refusing
    on that ground would forbid the ordinary case.
    """

def test_a_value_outside_a_vocabulary_field_is_refused(tmp_path, monkeypatch)

def test_a_value_inside_a_vocabulary_field_is_accepted(tmp_path, monkeypatch)

def test_a_vocabulary_default_makes_the_condition_hold(tmp_path, monkeypatch)
    """
    ADR-076: a field with a default is never absent. Reading raw
    frontmatter made the condition never hold for precisely the documents it
    was written about.
    """

def test_a_list_valued_condition_field_matches_any_element(tmp_path, monkeypatch)

def test_a_missing_condition_field_does_not_hold(tmp_path, monkeypatch)
    """
    Absent is "the condition is not met", not an error: the document
    check has its own finding for a missing required field.
    """

def _superseded(root: Path, extra: str) -> dict

def test_a_superseded_document_must_name_its_successor(tmp_path, monkeypatch)

def test_a_superseded_document_that_names_one_is_clean(tmp_path, monkeypatch)

def test_an_active_document_need_not_name_a_successor(tmp_path, monkeypatch)

def test_the_built_in_condition_stays_out_of_the_per_scheme_contract(tmp_path, monkeypatch)
    """
    `describe()` lists what a scheme declares *beyond* the standard
    fields, and the record page says so in its own sentence. Rendering the
    built-in there would make every scheme look as though it declared a
    contract, and would contradict the "nothing beyond the standard fields"
    line the same page prints.
    """

def test_the_record_page_states_the_built_in_condition_once(tmp_path, monkeypatch)
    """
    It is a real rule and a reader should meet it — stated with the
    standard fields, where it belongs, rather than repeated under every
    scheme as though each had declared it.
    """

def test_a_scheme_declaring_nothing_is_still_empty(tmp_path, monkeypatch)
    """
    The built-in carrying a condition must not make every scheme look as
    though it declared a contract.
    """

def run(status)

def run(tags)

```

## tests/test_reserved_prefix.py
```python
def project(tmp_path, monkeypatch, prefix: str) -> Path

def errors_for(tmp_path, monkeypatch, prefix: str) -> list[str]

def test_an_ordinary_prefix_is_fine(tmp_path, monkeypatch)

def test_the_fixture_prefix_itself_is_refused(tmp_path, monkeypatch)

def test_the_bare_namespace_is_refused(tmp_path, monkeypatch)
    """
    `FX` is the remote prefix (ADR-034); a scheme of the same name would
    make every composed `FX-ADR-032` ambiguous as well.
    """

def test_any_other_name_in_the_namespace_is_refused(tmp_path, monkeypatch)
    """
    A migration fixture needs two prefixes at once, so the reservation is a
    namespace rather than one name — and a namespace has to hold at its edges
    or the second prefix is invisible only by luck.
    """

def test_a_prefix_that_merely_starts_with_f_is_fine(tmp_path, monkeypatch)

def test_a_prefix_containing_fx_elsewhere_is_fine(tmp_path, monkeypatch)
    """The reservation is a leading namespace, not a substring search."""

def test_the_finding_names_the_remedy(tmp_path, monkeypatch)
    """
    A scheme that already has documents is renamed by `rename_scheme`
    (ADR-040), not by hand — the finding has to say so, because the obvious
    reading of "pick another prefix" is to edit the config and orphan the
    filenames.
    """

def test_the_check_is_wired_into_the_run(tmp_path, monkeypatch)

```

## tests/test_scan_cache.py
```python
def _doc(root: Path, number: int, body: str) -> Path

def test_a_second_scan_of_an_unchanged_corpus_is_not_redone(project, monkeypatch)

def test_a_rewrite_is_seen(project)
    """
    The property the whole cache rests on. `repair` and `migrate` rewrite
    documents mid-run and read them back; a cache that missed that would hand
    back the record as it was before the repair.
    """

def test_a_new_document_is_seen(project)
    """
    The fingerprint covers the *set*, not just each file's stamp, so a
    document appearing is a different corpus.
    """

def test_a_deleted_document_is_seen(project)

def test_a_call_with_arguments_is_not_served_from_the_cache(project, monkeypatch)
    """
    `files=` and `docs=` describe a corpus the fingerprint does not, so
    those calls run every time rather than colliding with the shared entry.
    """

def test_the_shared_scan_still_matches_its_own_annotations(project)
    """
    `Scan.used` compares annotations by identity, so handing the same
    object to every caller has to keep that relationship intact — it is the
    one thing sharing could plausibly break.
    """

```

## tests/test_scheme_cite.py
```python
def _project(root: Path, monkeypatch, cite: str | None, render: str) -> None
    """
    A principles-shaped project: sources in `record/principles.d`, assembled
    into `docs/design-principles.md`.
    """

def _principle(root: Path, number: int, title: str) -> Path

def _view(root: Path) -> Path
    """
    The assembled document, carrying the explicit anchors the generator
    emits — so an anchor target is available to be chosen, and a test that
    prefers the page is choosing rather than falling back.
    """

def _ref(text: str, source: Path)

def _prose_target(text: str, source: Path) -> str | None

def test_a_document_scheme_defaults_to_its_view(tmp_path, monkeypatch)
    """
    The key is inert until set. A project upgrading into this version finds
    its citations spelled exactly as before.
    """

def test_an_index_scheme_defaults_to_the_page(tmp_path, monkeypatch)
    """
    Not a choice — an index scheme assembles no view, so the document's own
    file is its only address. Recorded as `cite` all the same, so the field
    always says where a citation goes rather than sometimes meaning nothing.
    """

def test_a_citation_resolves_to_the_cited_documents_own_page(tmp_path, monkeypatch)

def test_the_anchor_is_not_used_even_though_one_exists(tmp_path, monkeypatch)
    """
    The instrument check: the view carries `<a name="dp-2">`, and
    `dp_anchors` finds it. Preferring the page is a decision, not an absence.
    """

def test_a_document_citing_itself_still_resolves_to_nothing(tmp_path, monkeypatch)

def test_a_code_with_no_document_resolves_to_nothing(tmp_path, monkeypatch)
    """
    Under `view` this returned an anchor into the assembled page whether or
    not the principle existed. A page target cannot: there is no file.
    """

def test_cite_view_restores_the_anchor(tmp_path, monkeypatch)

def test_cite_view_from_inside_the_view_is_a_bare_fragment(tmp_path, monkeypatch)

def test_an_unknown_cite_value_is_refused_by_name(tmp_path, monkeypatch)

def test_cite_view_on_an_index_scheme_is_refused(tmp_path, monkeypatch)
    """
    An index-rendered scheme assembles no document, so there is no view to
    anchor into. Saying so beats silently resolving to the page anyway — the
    project asked for something that does not exist here (DP-1).
    """

def test_cite_page_on_an_index_scheme_is_accepted(tmp_path, monkeypatch)
    """
    Redundant but true — it describes what an index scheme already does, so
    refusing it would be pedantry rather than a caught mistake.
    """

def test_an_already_written_anchor_link_is_retargeted_at_the_page(tmp_path, monkeypatch)

def test_the_link_text_is_left_exactly_as_written(tmp_path, monkeypatch)
    """
    The label is the author's sentence, not a field. Retargeting is about
    where the link goes.
    """

def test_a_bare_fragment_inside_the_view_is_retargeted_too(tmp_path, monkeypatch)

def test_it_is_idempotent(tmp_path, monkeypatch)

def test_a_scheme_that_cites_its_view_is_left_alone(tmp_path, monkeypatch)

def test_a_link_to_the_view_itself_is_not_a_citation(tmp_path, monkeypatch)
    """
    No fragment means the author is pointing at the whole document, which is
    a real thing to link to and not a principle citation.
    """

def test_an_anchor_naming_no_document_is_left_alone(tmp_path, monkeypatch)
    """
    Rewriting it would point at a file that does not exist — worse than the
    dead fragment it already is, and it hides the problem from the lint.
    """

def test_a_specimen_in_a_code_span_is_not_rewritten(tmp_path, monkeypatch)

```

## tests/test_scheme_patterns.py
```python
def _scheme(prefix: str) -> Scheme

def test_the_same_prefix_compiles_once(monkeypatch)

def test_two_prefixes_do_not_share_a_pattern()
    """
    The cache is keyed on the prefix, so a second scheme must not be
    handed the first one's regex — that would make every code read as ADR.
    """

def test_the_code_pattern_still_reads_what_it_read_before()
    """Behaviour is the contract; the cache is an implementation detail."""

def test_the_temp_pattern_still_reads_what_it_read_before()

def test_the_temp_pattern_is_cached_per_prefix(monkeypatch)

def test_a_scheme_overriding_the_tail_gets_its_own_temp_pattern()
    """
    `TEMP_TAIL` is a class attribute, so it belongs in the key rather than
    being assumed constant — a subclass that narrows it must not be handed
    the base spelling's regex.
    """

def test_the_cache_does_not_need_a_scheme_to_be_hashable()
    """
    `Scheme` is frozen but NOT hashable — it carries dict fields, so
    `hash()` raises `TypeError`. That is why the cache keys on the prefix
    string and not on the scheme: an `lru_cache` over the instance would have
    been a bug the moment it was called.
    """

class Narrow(Scheme)

```

## tests/test_scheme_requires.py
```python
def _project(root: Path, monkeypatch, requires: str) -> Path

def test_no_requires_demands_nothing(tmp_path, monkeypatch)
    """The default: a scheme asks for the standard fields and no more."""

def test_a_required_field_is_demanded_by_name(tmp_path, monkeypatch)

def test_supplying_the_field_clears_it(tmp_path, monkeypatch)

def test_an_empty_value_does_not_satisfy_it(tmp_path, monkeypatch)
    """
    A present-but-empty key is the shape a scaffold leaves behind, and it
    vouches for nothing — the whole point is a human filling it in.
    """

```

## tests/test_scheme_shape.py
```python
def write(root: Path, rel: str, text: str) -> Path

def doc(root: Path, rel: str) -> Path

def two_schemes(tmp_path, monkeypatch)
    """Two schemes sharing one vocabulary file, as the motivating record has."""

def test_two_schemes_can_share_one_vocabulary(two_schemes)
    """
    The duplication this removes: the shared terms were previously written
    once per scheme in tags.yaml and again per scheme in the config — and a
    shared FILE was the half-measure, since two schemes could point at one and
    simply did not (ADR-098).
    """

def test_group_membership_comes_from_the_vocabulary(two_schemes)
    """
    `primary_for` is what lets the group list no tags at all — and lets one
    file give two schemes DIFFERENT primaries, which an inline list can only
    do by repeating the shared part.
    """

def test_a_derived_group_is_enforced_like_any_other(two_schemes)

def test_a_tag_the_scheme_cannot_carry_is_not_in_its_group(two_schemes)
    """
    `generative` is a LIT primary only, so a practice carrying it has no
    primary at all — which is what the record wanted and could previously say
    only by writing the other list out.
    """

def test_an_inline_list_still_wins(tmp_path, monkeypatch)
    """
    Derivation is the fallback, not a replacement: a group that lists tags
    means those tags, whatever the vocabulary says.
    """

def test_a_group_that_derives_nothing_is_a_config_error(tmp_path, monkeypatch)
    """
    The eager-validation promise: a group constraining nothing must not
    surface as "no violations".
    """

def test_a_declared_reference_must_be_present(two_schemes)

def test_a_reference_must_be_a_code(two_schemes)
    """
    The gap `requires` left: a required field is satisfied by any truthy
    value, so an arbitrary sentence passed.
    """

def test_a_reference_must_belong_to_the_named_scheme(two_schemes)
    """
    The other half of the gap: a practice citing a decision as its
    evidence passed silently.
    """

def test_a_reference_must_resolve(two_schemes)

def test_a_good_reference_is_silent(two_schemes)

def test_a_linked_reference_still_reads(two_schemes)
    """
    Reference fields are data and stay bare, but a hand-edited file can
    carry a link; refusing that would be a lint nobody could satisfy twice.
    """

def test_an_optional_reference_may_be_absent(two_schemes)

def test_referencing_an_undeclared_scheme_is_a_config_error(two_schemes)

def build(toml_extra: str)

```

## tests/test_site.py
```python
def test_publishes_the_decisions_and_the_generated_views()

def test_never_publishes_a_fragment()
    """
    A fragment writes links for the page it lands in, has no code, no title
    of its own and no identity apart from the view — staging it in place would
    break every one of those links and duplicate the view besides.
    """

def test_publishes_a_document_schemes_sources_as_pages_too()
    """
    A design principle is not a fragment. It is numbered, titled, statused,
    versioned and cited by code — every property a decision has except an
    address — so it gets one. The assembled view is still published; both, like
    a decision and its index.
    """

def test_a_published_page_is_one_whose_links_resolve_where_it_lands()
    """
    The invariant, restated for the exception. It used to read
    `link_base(path) == path.parent`, which is the same claim while every
    source rendered elsewhere stayed unpublished. A document-scheme source
    breaks that equality on purpose — its links are spelled for the view — and
    earns it by being REBASED at stage time. Everything else still has to
    resolve where it sits.
    """

def test_a_staged_principle_has_its_links_rebased_onto_its_own_page()
    """
    The source spells `../record/decisions.d/ADR-006.md`, which is correct
    from `docs/` and wrong from `record/principles.d/`. Publishing it without
    re-spelling would trade one broken link for another.
    """

def test_rebasing_leaves_a_specimen_in_a_code_span_alone()

def test_a_principle_answers_to_its_bare_code_like_a_decision()

def test_excludes_are_honoured()

def test_readme_becomes_the_landing_page()

def test_site_defaults_derive_from_the_issue_url()

def test_site_defaults_stay_empty_without_a_github_issue_url(project)
    """
    No guessing: a project Luria cannot identify gets empty URLs, which
    `luria site` reports rather than inventing a domain for (DP-1).
    """

def test_record_line_carries_status_date_and_lineage()

def test_record_line_reads_every_issue_in_the_field()
    """
    `issue: '#21, #23'` is a shape this record actually uses, so the
    separator is read out of the field rather than assumed.
    """

def test_record_line_is_empty_without_frontmatter_facts()

def test_version_appears_only_when_it_is_not_one()

def test_staged_decision_gets_its_code_as_an_alias(tmp_path)

def test_staging_is_idempotent_and_drops_removed_pages(tmp_path)

def test_a_staging_directory_inside_the_project_is_not_republished(project)
    """
    The default `--out build/site` sits in the tree Luria scans. Without
    the skip, the second run publishes the first run's output.
    """

def _quartz_config(root) -> dict
    """The generated config, parsed. YAML since Quartz 5 (ADR-101)."""

def _plugin(config: dict, name: str) -> dict

def test_config_is_written_with_the_project_title(tmp_path)

def test_links_out_of_the_site_go_to_the_repository(tmp_path)

def test_a_quoted_path_is_never_retargeted(tmp_path)
    """
    Code is a specimen, not a claim (ADR-008). Rewriting a path inside a
    fence would edit the example the prose is teaching.
    """

def test_pages_land_at_their_repository_paths(tmp_path)
    """
    Preserved paths are what let the record's own relative links keep
    resolving — the whole reason no second link resolver exists here.
    """

def test_index_normalizes_rebased_targets(target, expected)
    """
    The bug the site build found (#13): concatenation alone leaves
    `a/../b`, which GitHub forgives and a static site generator does not.
    """

def test_an_unresolvable_influence_is_counted_not_swallowed(project)
    """
    `influenced_by` is frontmatter — data, which the prose scanner never
    reads — so an unexpandable code there has no other place to be seen.
    """

def test_a_superseded_decision_says_so_on_its_page(project)
    """
    Status lives in frontmatter, which renders as nothing — so on a site a
    retired decision reads as current unless the staging says otherwise.
    """

def test_an_html_image_is_staged_beside_its_page(tmp_path)
    """
    `<img src>` is how a README centres a banner — markdown isn't parsed
    inside an HTML block — and an unrecognised shape is worse than a wrong
    one: it is neither staged, nor redirected, nor counted (#70).
    """

def test_the_landing_page_is_named_and_still_answers_to_README(tmp_path)

def test_the_graph_sits_above_the_article_not_in_the_sidebar(tmp_path)
    """
    Quartz's sidebars stack below the content under 1200px, so a graph in
    the right rail is at the bottom of the page on most windows (#71).
    One key since Quartz 5, where it was a generated `quartz.layout.ts` — the
    whole reason luria wrote TSX at all (ADR-101).
    """

def test_the_action_copies_everything_the_staging_writes(tmp_path)
    """
    The pair that has to move together. `stage` gained a second generated
    file and the action did not copy it — a whole layout silently reverting
    to Quartz's default is exactly the drift DP-3 says to guard as a
    property, not as a list somebody remembers to extend.
    It matches `cp` commands rather than mentions. The first version of this
    test asked whether the name appeared anywhere in the action, which a
    directory called `static` satisfies from any of the three other lines
    that say `quartz/static/` — a guard that passes for a reason unrelated to
    what it checks is not a guard.
    """

def test_the_palette_merges_over_the_generators_defaults()
    """A project names the colours it cares about; the rest stay Quartz's."""

def test_an_unknown_colour_name_is_refused_by_name()
    """
    Silently dropping a key is a project wondering why its brand didn't
    take (DP-1).
    """

def test_the_icon_is_staged_as_the_vector_master(tmp_path)
    """
    Not rasterized here and not committed anywhere: `actions/site` renders
    it with the generator's own `sharp`, so nothing derived from the artwork
    exists in the repository to drift (DP-3).
    """

def test_the_logo_is_baked_once_per_theme(tmp_path)

def test_artwork_that_cannot_be_re_inked_is_left_alone()

def test_missing_artwork_is_named_not_skipped(project)

def test_a_project_with_no_artwork_still_gets_a_stylesheet(project)

def parent(tmp_path, monkeypatch, include: dict | None) -> Path

def child(root: Path, name: str) -> Path
    """
    A complete little record inside `root`, carrying a scheme the parent
    has never heard of — which is the condition the mount exists for.
    """

def test_a_nested_record_is_staged_by_its_own_config(tmp_path, monkeypatch)
    """
    The whole point, and the reason a merge would not do.
    `publishable()` tells a source from a view with
    `link_base(path) != path.parent`, and `link_base` answers from the
    *reading* config's schemes. The parent has no NOTE scheme, so under the
    parent's config `NOTE-001.md` reads as ordinary prose.
    This used to prove that by the source's ABSENCE, which stopped working the
    day a document scheme's sources became pages: the child publishes it now,
    on purpose. The discriminator is the code ALIAS. Only a config that knows
    the NOTE scheme can give `NOTE-001.md` a `/NOTE-001` address; the parent,
    reading it as prose, would publish the same file with no alias at all. So
    the alias is exactly the thing that is present when the child staged it and
    missing when the parent did.
    """

def test_a_nested_record_gets_its_own_landing_page(tmp_path, monkeypatch)
    """
    The child's README becomes the section's index, titled from the child's
    own `site.title`. Without it a link to the section lands on nothing — the
    examples had no root README and mounted as a directory with no front
    page.
    """

def test_include_records_implies_exclusion_from_the_parent_pass(tmp_path, monkeypatch)
    """
    Without this the merge reintroduces what the mount solves.
    Asserted against the parent's file list rather than the staged vault,
    because from the vault the two failures are indistinguishable: a child file
    published by the parent and one mounted by the child both land under
    `sub/alpha/`.
    """

def test_a_pattern_matching_no_record_is_an_error(tmp_path, monkeypatch)
    """
    A silently empty include is a section of the site that does not exist,
    and nothing else would report it (DP-1). A directory that is not a record
    is a different case and stays a quiet skip — `sub/*` is the natural way to
    write "every one of these", and a stray directory beside them should not
    break a publish.
    """

def test_staging_a_child_leaves_the_parent_config_current(tmp_path, monkeypatch)
    """
    `rooted()` restores what it swapped. A leaked `LURIA_ROOT` would make
    every later call in the process read the child's record instead.
    """

def test_a_nested_record_is_regenerated_by_the_parents_index(tmp_path, monkeypatch)
    """
    `luria index` at the root writes a nested record's views too (ADR-078).
    This is the half that makes committing them safe. A committed view is only
    as good as the thing that regenerates it, and before this the parent's
    index did not know the child existed — so the views were gitignored, and
    the examples were the one place in this repository where a view could not
    be browsed at all.
    """

def test_an_orphan_in_a_nested_view_directory_is_an_orphan(tmp_path, monkeypatch)
    """
    `view_dirs` reaches into nested records for the same reason `outputs`
    does: a stale page left in a child's view directory reads as generated,
    and the parent is the only thing running the check.
    An index-render scheme, because only those own a view *directory* — a
    document scheme owns one file, and a stray beside it is somebody's prose,
    not an orphan.
    """

def test_a_title_that_looks_like_syntax_is_escaped()
    """
    A title is data spliced into a markdown table cell that is then
    wikilink-expanded, so anything in it that reads as syntax has to be
    escaped. This project's ADR-025 is titled ``Wikilinks: `[[CODE]]` is a
    typed reference``, and two decisions cite it through `influenced_by:` —
    unescaped, every one of their pages asked the resolver for a document
    called `CODE`.
    """

def test_staging_leaves_no_unresolved_wikilink()
    """
    The whole record, not a fixture: the escaping above was found by this
    assertion failing on two real pages, and it is what keeps it found.
    """

```

## tests/test_slugs.py
```python
def test_the_ordinary_case()

def test_punctuation_goes_and_the_word_characters_stay()

def test_an_underscore_survives()
    """
    `\w` includes it, so `github-slugger` keeps it. My first version
    stripped `_` as a markdown emphasis marker and produced `failon`, which
    is a link to nothing.
    """

def test_removed_punctuation_leaves_its_spaces_behind()
    """
    The order is remove-then-replace, and each space becomes one hyphen
    rather than each RUN of them. An em-dash between two spaces therefore
    leaves a double hyphen — which my first version collapsed.
    """

def test_repeats_are_numbered_from_the_second()

def test_a_repeat_that_collides_with_a_numbered_one_moves_on()
    """
    `github-slugger` keeps incrementing until the result is unused, so a
    document containing "Notes", "Notes" and "Notes 1" cannot end up with two
    headings answering to `notes-1`.
    """

def test_headings_come_out_in_document_order()

def test_a_heading_inside_a_fence_is_not_one()
    """
    It would consume a slug and shift the suffix of every heading after
    it, which is a link to the wrong entry rather than to none.
    """

def test_a_longer_fence_closes_a_shorter_one_and_not_the_reverse()

def test_anchors_for_maps_each_heading_to_its_own_slug()

```

## tests/test_sources.py
```python
def _project(project, extra: str, network: str) -> None

def _note(project, number: int, title: str, arxiv: str, directive: str) -> None

def _resolved(project, entries: dict[[str, str]]) -> None

def test_an_identifier_naming_a_different_paper_is_reported(project)
    """
    The whole point. `2305.10755` is a real arXiv paper and a valid
    identifier; it is simply not the PaLM 2 technical report, and no check
    that stops at "does this resolve" can say so.
    """

def test_an_agreeing_identifier_is_silent(project)

def test_wrapping_case_and_punctuation_do_not_count_as_disagreement(project)
    """
    A recorded title keeps its own capitalisation and line breaks. Only the
    words decide, or the check would fire on every document that was typed by
    a human rather than pasted.
    """

def test_a_truncated_title_is_a_disagreement(project)
    """
    The tempting case to forgive, and it is not forgiven. Dropping a
    subtitle is usually harmless and sometimes not: one record read "Neural
    Networks are Surprisingly Modular" for a paper about *Pruned* networks,
    which is a weaker claim wearing a stronger title. The directive is how a
    deliberate trim is recorded, so the judgement lands on a person.
    """

def test_an_escaped_title_is_not_a_mismatch(project)
    """
    Found by running the check on a real corpus: arXiv's Atom feed returns
    "Better &amp; Faster", and comparing that against what a person typed
    reported a mismatch on the escaping. A false positive is how a check gets
    switched off, so entities are unescaped at the fetch.
    """

def test_html_entities_are_unescaped_at_the_fetch(project, monkeypatch)
    """
    The fix belongs at the fetch, not at the comparison: the lockfile
    should record what the title IS, so a reader of the diff sees a title
    rather than markup.
    """

class _FakeResponse

    def __init__(self, body)

    def read(self)

    def __enter__(self)

    def __exit__(self)


def test_a_source_ok_directive_acknowledges_it(project)
    """
    A nickname the project prefers is legitimate and common — 22 of the 53
    were this class. Without an acknowledgement the check is noisy enough to
    be switched off.
    """

def test_a_source_ok_that_excuses_nothing_is_reported(project)
    """
    Same bargain every other directive strikes: an acknowledgement cannot
    outlive what it excused, or the record fills with permissions nobody can
    audit.
    """

def test_a_hermetic_build_answers_only_from_the_lockfile(project)
    """
    `network = "never"` is the train, and the deliberately hermetic CI. It
    reports what the lockfile knows and stays quiet about the rest.
    """

def test_an_unchecked_identifier_is_reported_when_asking_failed(project, monkeypatch)
    """
    The hole the first version shipped with. A citation is never more
    likely to be wrong than in the minutes after it is typed, and back then
    the check passed exactly then — nothing had resolved it yet, and no entry
    read as agreement.
    """

def test_the_lint_asks_about_what_the_lockfile_cannot_answer(project, monkeypatch)
    """
    Under "auto" the lockfile is a cache, not the boundary of what may be
    known — so a freshly typed wrong citation is caught on the run that adds
    it, without anyone remembering a command.
    """

def test_what_the_lint_learns_is_written_back(project, monkeypatch)
    """
    So the next run answers offline, and the diff shows a reviewer what
    upstream said and when.
    """

def test_an_identifier_upstream_does_not_have_is_its_own_finding(project)
    """
    404 is an answer, and a different one from "I could not ask". Recorded
    in the lockfile as such so it is not re-fetched forever.
    """

def test_a_404_is_an_answer_and_a_429_is_not(project)
    """
    The distinction the first version lacked: it retried everything and
    reported every failure alike, so a throttled batch wrote nothing and read
    afterwards as agreement.
    """

def test_the_lint_carries_the_class(project)

def test_the_title_url_indexes_the_uid_capture_groups(project)
    """
    `uris.title` renders over the same vocabulary as `url`, so a remote
    whose metadata API wants the identifier restructured needs one line, not a
    second subsystem.
    """

def test_a_remote_with_no_title_uri_is_skipped(project)
    """
    Most remotes are records, not metadata APIs. Declaring nothing means
    the check has no opinion, rather than an opinion it cannot support.
    """

```

## tests/test_sources_throttle.py
```python
def _project(project, network: str) -> None

def _note(project, number: int, arxiv: str) -> None

def _throttle(retry_after: str | None)

def _opener(responses, calls)

def test_a_throttle_without_retry_after_is_not_retried(project, monkeypatch)
    """
    One request, not three. The retries changed the outcome in none of the
    cases that motivated them — a rate limit is a property of the window.
    """

def test_a_short_retry_after_is_honoured_once(project, monkeypatch)
    """
    A host that says when to come back has named the request that will
    succeed, so a short wait is the request it asked for.
    """

def test_a_long_retry_after_is_reported_not_slept_through(project, monkeypatch)
    """
    A build that blocks two minutes on a metadata courtesy API is worse
    than one that reports what it could not check.
    """

def test_the_wait_a_host_asked_for_is_carried_as_a_value(project)
    """It was parsed and then spent only on the message string."""

def test_one_refusal_ends_the_remote_for_the_run(project, monkeypatch)
    """The second throttled identifier tells us nothing the first did not."""

def test_the_breaker_does_not_leak_between_runs(project, monkeypatch)

def test_unsettled_identifiers_are_asked_first(project)
    """
    The old order was the record's own, so a throttle partway through left
    the same tail unresolved run after run.
    """

def test_the_queue_is_shuffled_so_one_bad_identifier_cannot_head_block(project)
    """
    Deliberately not seeded: an identifier that always errors must not sit
    at the head of the queue every run and spend the window on itself.
    """

def test_what_a_throttled_run_learned_is_kept(project, monkeypatch)
    """A run that dies in the middle used to write nothing at all."""

def fake(url, timeout)

class _Body

    def __init__(self, text)

    def read(self)

    def __enter__(self)

    def __exit__(self)


def fake(url, timeout)

```

## tests/test_statuses.py
```python
def _project(root: Path, monkeypatch, uniform_share: float | None, active: str | None, successor: str | None, retires_on: str | None) -> None

def _value(root: Path, number: int, status: str, superseded_by: str | None) -> Path

def _wire(root: Path, values: dict | None) -> None
    """
    Point `status:` at the named vocabulary, and declare it.
    The values used to be a `statuses.yaml` beside the records; since
    ADR-098 they are in the config under a name, so wiring the field and
    declaring the words are one edit rather than two files.
    """

def _declare(root: Path, text: str) -> None
    """
    Write the vocabulary AND wire it.
    The file alone declares nothing since `status:` became an ordinary
    controlled field (#181): `statuses.yaml` is the values, the `fields`
    table is the wiring — the split ADR-076 draws for every vocabulary.
    """

def _scheme()

def test_declaring_nothing_checks_nothing(tmp_path, monkeypatch)
    """
    The posture a record predating the declaration is in, said plainly.
    It used to be silent in both directions — no legend, and no complaint,
    because the five were enforced from the code. With the words the
    project's, silence in the second direction would mean an unchecked
    field looking exactly like a clean one (DP-15), so it says so.
    """

def test_a_declared_vocabulary_is_the_vocabulary(tmp_path, monkeypatch)
    """
    It replaces rather than narrows — there is no longer a list in the
    code for it to be a subset of.
    """

def test_a_trailing_note_does_not_defeat_the_check(tmp_path, monkeypatch)
    """
    A `status_note:` qualifies the word rather than being part of it, and
    the check reads the word alone.
    """

def test_a_scheme_may_name_its_own_words(tmp_path, monkeypatch)
    """
    The five were a law and are now a default (#183). A project whose
    decisions are `Accepted` and `Withdrawn` says so, and the checks follow
    its words rather than telling it those words do not exist.
    """

def test_a_vocabulary_without_the_in_force_word_is_a_config_error(tmp_path, monkeypatch)
    """
    The invariant that replaces "the vocabulary is closed". `active` is
    how every check decides what is in force, so a vocabulary that omits it
    means nothing is ever in force — silently, and catastrophically for the
    citation checks.
    """

def test_an_active_word_outside_the_default_is_a_config_error_too(tmp_path, monkeypatch)
    """
    The same invariant when the project declares nothing. `active` naming
    a word the default vocabulary does not contain means no document can
    ever be in force — reported once, at the configuration, rather than as
    one finding per document.
    """

def test_a_word_outside_the_declared_vocabulary_is_still_reported(tmp_path, monkeypatch)
    """
    Replacing the list does not mean abandoning the check — it means the
    check reads the project's list.
    """

def test_a_scheme_declaring_no_vocabulary_checks_no_word(tmp_path, monkeypatch)
    """
    The honest consequence of `status:` becoming an ordinary controlled
    field: with no declaration there are no values, so nothing constrains
    the word — and the finding says exactly that rather than pretending a
    default is in force. Requiring the declaration is the next step.
    """

def test_the_meaning_reaches_the_generated_index(tmp_path, monkeypatch)
    """
    The point of the feature. A template comment is read once, by whoever
    mints a record; the index is read by everyone else, and until now its
    status column was five bare words with no way to learn what they meant
    here.
    """

def test_undeclared_means_nothing_is_checking_it(tmp_path, monkeypatch)
    """
    `undeclared` no longer means "the word is wrong" — that is the
    vocabulary's finding now. It means nothing is checking the word at all,
    which is the one thing a vocabulary cannot report about itself.
    """

def _values(root: Path, n: int, status: str) -> None

def test_a_uniform_status_field_is_reported(tmp_path, monkeypatch)
    """
    The finding: nothing here has ever been judged.
    Worth catching because `active` is what `retired-citations` reads. A scheme
    where nothing is ever retired has an enforcement mechanism that cannot
    fire, and its green build says only that no one has looked.
    """

def test_one_dissenting_record_clears_it(tmp_path, monkeypatch)
    """
    The distinction is live as soon as anything varies. This is not a rule
    about proportion — a corpus whose claims all survive is legitimate — so a
    single retirement is enough to say a judgment is being made.
    """

def test_one_dissenter_still_clears_it_at_the_default_share(tmp_path, monkeypatch)
    """
    `uniform_share` defaults to 1.0, which IS the original rule. A project
    that never sets it sees exactly the behaviour it saw before, so turning
    the dial into a dial cannot start reporting on anyone.
    """

def test_a_lowered_share_reports_a_near_constant_field(tmp_path, monkeypatch)
    """
    The case the default cannot see. Eleven records in force and one
    retired is 92% — a status a reader can predict without looking, and a
    vocabulary whose other values are decorative. A project that says so with
    `uniform_share` gets told.
    """

def test_a_genuinely_mixed_scheme_passes_a_lowered_share(tmp_path, monkeypatch)
    """
    The check still has to be silent on a scheme that exercises its
    vocabulary, or lowering the share would just be a tax on large schemes.
    """

def test_the_row_names_the_tail_it_is_reporting_against(tmp_path, monkeypatch)
    """
    A distributional finding has to show a distribution. "133/144 at
    Active" invites the reply that exceptions exist; naming them answers it
    in the row.
    """

def test_a_trailing_note_does_not_look_like_variety(tmp_path, monkeypatch)
    """
    `Superseded — by X` and `Superseded — by Y` are one status wearing two
    strings. Comparing whole values would call that variety and clear a scheme
    that has none.
    """

def test_a_young_scheme_is_not_reported(tmp_path, monkeypatch)
    """
    Below the floor, uniformity is evidence of nothing. Three records all in
    force is a scheme someone started last week.
    """

def test_a_scheme_declaring_one_status_has_said_so_on_purpose(tmp_path, monkeypatch)
    """
    The interesting interaction with #102. A project that declares exactly
    one status has answered this question already, and reporting it would be
    telling it off for doing the configuration right.
    """

def test_a_document_rendered_scheme_is_exempt(tmp_path, monkeypatch)
    """
    A design-principles page where every principle is in force is the
    expected state, not a smell — principles are superseded by revision, and
    `version:` carries that.
    """

def test_the_class_is_failable(tmp_path, monkeypatch)

def _uniform_project(root: Path, monkeypatch, ack: str | None) -> None

def test_uniform_fires_without_the_acknowledgement(tmp_path, monkeypatch)

def test_uniform_ok_moves_the_row_from_finding_to_note(tmp_path, monkeypatch)

def test_acknowledgement_lapses_when_the_scheme_stops_being_uniform(tmp_path, monkeypatch)

def test_a_project_cannot_promote_its_own_acknowledgement_to_a_failure()

def test_a_status_parses_into_its_word_and_its_note()
    """
    One scalar, two concepts (ADR-003): the word is data, the note is
    prose. Split in six places before this existed.
    """

def test_a_document_exposes_both(project)

def test_of_reads_the_two_field_form(project)

def test_of_still_reads_the_combined_form_and_says_so(project)

def test_split_moves_the_note_out_of_status(project)

def test_split_carries_a_quoted_multi_line_note_intact(project)
    """ADR-015's shape: a quoted scalar that runs onto a second line."""

def test_set_status_replaces_an_existing_note_rather_than_duplicating(project)

def test_a_note_riding_in_status_is_a_finding_that_names_the_repair(tmp_path, monkeypatch)

def test_repair_moves_the_note_and_the_finding_clears(tmp_path, monkeypatch)
    """
    The repair is the one `luria repair` already runs for `created:`
    (ADR-031): the file states both facts, and is made to say so in two.
    """

def test_a_code_in_the_note_is_a_citation_the_fixer_links(project)
    """
    The note is prose (ADR-051): a bare code there is what `luria link
    --fix` writes, and what the lint demands until it does.
    """

def test_the_repair_keeps_a_note_that_says_more_than_the_code(project)
    """
    ADR-015's shape: the successor goes to the field, and the rest of the
    sentence stays as prose, verbatim — the repair never rewrites what an
    author wrote beyond the shape the machinery itself used to write.
    """

def test_superseded_without_a_successor_is_a_finding(tmp_path, monkeypatch)
    """
    ADR-071's rule, now stated as a `required_when` on the built-in field
    rather than a hand-written branch — so it is checked with every other
    obligation, in `check_contracts`, and carries the same wording and
    provenance as any declared one (#170, review of #172).
    """

def test_the_supersession_rule_is_no_longer_a_branch_in_frontmatter(tmp_path, monkeypatch)
    """One implementation (DP-4): the check moved, it did not get copied."""

def test_a_successor_that_resolves_to_nothing_is_a_finding(tmp_path, monkeypatch)

def test_display_composes_the_successor_and_the_note(project)

def test_a_scheme_names_its_own_successor_field(tmp_path, monkeypatch)

def test_the_renamed_field_carries_the_successor_rule(tmp_path, monkeypatch)
    """
    ADR-071 follows the words: a retiring document must still name what
    replaced it, in whatever field the project calls it.
    """

def test_the_renamed_field_is_read_as_the_successor(tmp_path, monkeypatch)

def test_the_renamed_field_draws_the_succession_edge(tmp_path, monkeypatch)

def test_declaring_the_field_yourself_replaces_the_default(tmp_path, monkeypatch)
    """
    The point of calling it a default: a scheme that declares the field in
    its own `references` table owns it outright, and the default adds
    nothing beside it.
    """

def test_status_may_be_declared_as_a_vocabulary(tmp_path, monkeypatch)

def test_the_declared_vocabulary_checks_the_word(tmp_path, monkeypatch)

def test_one_bad_word_is_one_finding(tmp_path, monkeypatch)
    """
    The whole point. Before this, the bespoke check and the generic one
    both fired: two findings for one value.
    """

def test_a_status_carrying_a_note_is_one_finding_too(tmp_path, monkeypatch)
    """
    The obstacle that decided the shape. `status: Deferred — until the
    audit` means the raw value is not the vocabulary value, so a naive
    vocabulary check reports the whole string as an unknown word — beside
    the existing "carries a note" finding, which is the actionable one.
    Normalising the frontmatter at the read boundary means the generic
    checker needs no idea that `status` is special.
    """

def test_a_scheme_without_a_status_vocabulary_fails_the_lint(tmp_path, monkeypatch)
    """
    The break. A record predating the declaration has an unchecked
    `status:` — every word passes, and the absence looks exactly like a
    clean check (DP-15). It is a violation, and the finding names the
    command that fixes it.
    """

def test_the_upgrade_satisfies_the_requirement(tmp_path, monkeypatch)
    """
    The fix ships with the break, and is the whole remedy: after it, the
    record lints clean without anyone hand-editing config.
    """

def test_the_upgrade_does_not_load_the_config_it_repairs(tmp_path, monkeypatch)
    """
    It has to run against a record the new version refuses to load, or it
    is unrunnable in exactly the situation it exists for.
    """

def test_a_spent_upgrade_says_it_can_be_deleted(tmp_path, monkeypatch)
    """
    The marker. An upgrade that has nothing left to do anywhere is dead
    code that still has to be read and tested, so the lint raises the
    question rather than waiting for someone to remember it — the posture
    `stale-directives` already takes.
    """

def test_a_scheme_level_statuses_key_says_where_the_vocabulary_goes(tmp_path, monkeypatch)
    """
    `status` is a field, so `fields.status.vocabulary` names its
    vocabulary and nothing else does.
    A second `schemes.X.statuses:` beside it was not merely redundant: it
    could disagree with the field, and the two readers disagreed with it.
    `statuses.declared` read the scheme key while `statuses.undeclared` read
    the field, so a scheme could render a status legend and be reported as
    having no status check at all. The key is refused rather than ignored —
    silently dropping the vocabulary somebody named is the same failure one
    step later.
    """

def test_active_stays_a_scheme_level_word(tmp_path, monkeypatch)
    """
    What is privileged about `status` is not its vocabulary but `active:`
    — WHICH word means in force, the role the whole citation apparatus rests
    on. That names a word, not a vocabulary, so it stays where it is.
    """

```

## tests/test_syntax.py
```python
def test_one_comment_rule_covers_every_language(name, src)
    """
    `"comment" in node.type` is the whole of luria's per-language knowledge.
    Seven grammars spell the node `comment` and Rust spells it `line_comment`;
    nothing here enumerates either.
    """

def test_a_hash_inside_a_string_is_not_a_comment()
    """
    The crude marker scan cannot tell these apart, and says so in its own
    comment. A grammar can, in every language at once.
    """

def test_a_real_comment_beside_a_string_still_reads()
    """The point is precision, not silence."""

def test_offsets_are_character_offsets_not_byte_offsets()
    """
    Every other scanner in luria hands out character offsets, and a
    directive's span is compared against them.
    """

def test_an_unparseable_file_yields_nothing_rather_than_guessing()
    """
    A grammar that cannot parse the file has no opinion worth acting on, and
    the caller falls back to the scan that at least sees the text.
    """

def test_a_suffix_no_grammar_claims_is_not_an_error()

def test_growth_reaches_past_a_blank_line_inside_one_syntactic_unit()
    """
    The case this exists for: the blank-line run stops at line 3, and the
    citation is on line 5. The definition is one node, so the block is too.
    """

def test_growth_never_shrinks_a_block()
    """
    The rule is a union with the blank-line block, so a directive that works
    today cannot stop working because a grammar disagrees.
    """

def test_growth_takes_the_smallest_unit_that_holds_the_block()
    """
    A top-level YAML comment's next sibling is the whole document, which
    would make `-block` mean `-file`. The smallest node that starts where the
    block's content starts and still holds the block is the `jobs:` entry.
    """

def test_growth_stops_at_the_entry_it_introduces()
    """
    Same file, one line later: `after:` is a sibling entry, not part of the
    block, and nothing grows into it.
    """

def test_growth_is_the_same_rule_in_every_language(name, src, block, want)

def test_growth_declines_on_an_unparseable_file()

def test_the_extra_can_be_turned_off_without_uninstalling_it(monkeypatch)
    """
    A grammar that misreads a file is a bug someone needs a way around
    tonight, not after a release.
    """

def test_every_file_in_this_repository_scans_without_crashing()
    """
    Not a formality. Two lifetime bugs in this module took a real file to
    reproduce and killed the process rather than raising, which no other test
    here can see: a `try` catches an exception, not a segfault. Scanning the
    tree is the only check that runs the grammars over the shapes people
    actually write.
    """

```

## tests/test_tag_groups.py
```python
def project(tmp_path: Path, monkeypatch) -> Path

def errors_for(tmp_path, monkeypatch) -> list[str]

def test_exactly_one_is_satisfied(tmp_path, monkeypatch)

def test_exactly_one_rejects_none(tmp_path, monkeypatch)
    """
    The defect this feature was built for: an argument carrying only a
    failure mode and no strength.
    """

def test_exactly_one_rejects_two(tmp_path, monkeypatch)

def test_excluded_by_catches_a_contradiction(tmp_path, monkeypatch)
    """Naming how an argument fails contradicts saying it does not."""

def test_excluded_by_is_silent_when_the_group_is_absent(tmp_path, monkeypatch)

def test_at_most_one_allows_zero(tmp_path, monkeypatch)

def test_a_scheme_with_no_groups_is_unconstrained(tmp_path, monkeypatch)
    """
    Every record that predates this feature.
    The whole field goes, not just its `groups`: a scheme that says nothing
    about its tags declares no tags field, and then has no axis either
    (ADR-098).
    """

def test_an_unknown_rule_is_a_config_error(tmp_path, monkeypatch)
    """
    Caught at parse time. A misspelled rule that surfaced as 'no
    violations' would be the quiet failure this feature exists to remove.
    """

def test_a_group_with_no_tags_is_a_config_error(tmp_path, monkeypatch)

```

## tests/test_template_exemption.py
```python
def test_a_scheme_template_is_recognised(project)

def test_an_ordinary_document_is_not_a_template(project)

def test_a_template_is_left_out_of_the_reference_scan(project)
    """The whole point: an example code in a form is not a citation."""

def test_a_non_template_in_the_same_directory_is_still_scanned(project)

```

## tests/test_templates.py
```python
def write(root: Path, rel: str, text: str) -> Path

def project(tmp_path, monkeypatch, sota_extra: str) -> Path

def template(root: Path, scheme_dir: str) -> Path

def test_a_scalar_scaffold_for_a_plural_field_is_a_finding(tmp_path, monkeypatch)
    """
    The anthology case: `many = true` was decided, the form kept saying
    one, and 140 of 144 practices were filed single-sourced.
    """

def test_a_list_scaffold_for_a_plural_field_is_clean(tmp_path, monkeypatch)

def test_a_scalar_scaffold_for_a_scalar_field_is_clean(tmp_path, monkeypatch)

def test_a_list_scaffold_for_a_scalar_field_is_a_finding(tmp_path, monkeypatch)
    """
    The mirror image, and the one #141 made a finding on documents: a list
    in a scalar field was stringified and half-read.
    """

def test_a_required_field_missing_from_the_form_is_a_finding(tmp_path, monkeypatch)

def test_an_optional_field_missing_from_the_form_is_clean(tmp_path, monkeypatch)
    """
    A form prompts for what is required; an optional field is the
    author's to add, and demanding it in the template would make every
    document carry an empty key.
    """

def test_an_optional_field_present_in_the_wrong_shape_is_still_a_finding(tmp_path, monkeypatch)
    """
    Absent is the author's choice; present-and-wrong is copied into every
    document.
    """

def test_a_field_the_contract_does_not_know_is_clean(tmp_path, monkeypatch)
    """Templates carry optional fields and comments, and should."""

def test_placeholder_values_are_never_checked(tmp_path, monkeypatch)
    """`LIT-000` resolves to nothing and that is the point of a form."""

def test_a_scheme_with_no_template_is_clean(tmp_path, monkeypatch)
    """Every scheme predating templates, and every scheme that wants none."""

def test_a_template_with_no_frontmatter_is_clean(tmp_path, monkeypatch)
    """
    Reported by the docs checks already; not this check's finding to
    duplicate.
    """

def test_the_finding_cites_the_declaration(tmp_path, monkeypatch)
    """
    DP-4: a finding says where the obligation was declared, so the reader
    is sent to the key and not just told the rule.
    """

def test_a_commented_out_field_does_not_count_as_scaffolded(tmp_path, monkeypatch)
    """A form that explains a field in a comment has not prompted for it."""

def test_this_repos_own_templates_agree_with_its_contracts()
    """
    Fired on the real record, which is the only place it can be wrong in
    a way a fixture cannot show.
    """

def test_the_class_is_promotable_and_wired(tmp_path, monkeypatch)
    """
    A class reported by `status_sections` but absent from FAILABLE tells a
    project asking to enforce it that the class does not exist (test_lint's
    `legacy-spellings` regression, kept from recurring).
    """

def test_a_form_that_agrees_reports_nothing(tmp_path, monkeypatch)

def test_a_conditionally_required_field_is_demanded_at_the_forms_own_status(tmp_path, monkeypatch)
    """
    The form scaffolds `status: Proposed`, and a proposed entry in this
    scheme must say what would settle it — so the form has to prompt for it
    (#170 meeting #169).
    """

def test_it_is_not_demanded_when_the_form_starts_elsewhere(tmp_path, monkeypatch)

```

## tests/test_unlinted.py
```python
def page(project: Path, body: str, opted_out: bool) -> Path

def test_unlinted_file_yields_no_rewritable_refs(project)

def test_unlinted_file_keeps_wikilinks_quiet(project)

def test_unlinted_file_is_skipped_by_the_scan_and_counted(project)
    """
    The visibility bargain: the file's citations vanish from the scan, and
    the file itself appears in the count — an exemption nobody sees is how a
    report stops being a complete account (ADR-035).
    """

def test_report_lists_the_opted_out_files(project)

def test_narrow_unlinted_governs_nothing_and_says_so(project)

```

## tests/test_upgrade_yaml.py
```python
def _record(root: Path) -> None

def test_it_writes_the_yaml_config(tmp_path, monkeypatch)

def test_a_regex_survives_the_format_change(tmp_path, monkeypatch)
    """
    The hazard the whole converter exists for. TOML and YAML escape
    differently, so the bytes cannot simply move — and a `uid` that stops
    matching fails at reference-resolution time, a long way from here.
    """

def test_the_config_it_writes_actually_loads(tmp_path, monkeypatch)
    """End to end rather than by inspection: the point is a record that runs."""

def test_two_schemes_holding_the_same_words_end_up_naming_one_vocabulary(tmp_path, monkeypatch)
    """
    The defect that motivated the boundary: a vocabulary two schemes share
    had to be two files, and in the corpus that prompted this, ten of thirteen
    entries had drifted apart.
    inactive-ok: ADR-098 — Proposed, named as the decision this upgrade
    carries a record across.
    """

def test_words_that_differ_stay_two_vocabularies(tmp_path, monkeypatch)
    """
    It collapses copies, never opinions: two schemes whose words disagree
    are two vocabularies, and merging them would be the converter deciding
    something the record never said.
    """

def test_a_folded_vocabulary_is_wired_to_the_status_field(tmp_path, monkeypatch)
    """
    The TOML fixture declares no `fields.status` — and neither did the
    records this converter exists for, because the declaration is #181's
    second half and they predate it.
    `schemes.X.statuses` does not exist on the far side of the boundary, so
    a `statuses.yaml` folded into the central table has to reach the field
    that reads it. Carrying the words across and leaving nothing pointing at
    them would be a conversion that loses the vocabulary while reporting
    success.
    """

def test_it_leaves_the_toml_and_the_vocabulary_files_alone(tmp_path)
    """
    Deleting what you just converted, before anyone has read the result,
    is not a migration anybody should trust — it prints the `git rm` instead.
    """

def test_dry_run_writes_nothing(tmp_path)

def test_a_record_already_across_says_so(tmp_path, capsys)

def test_another_upgrade_refuses_until_this_one_has_run(tmp_path)
    """
    `statuses` reads the config by its new name, so on a record still on
    TOML it would report "nothing to upgrade" — true, and useless.
    """

def test_it_is_listed_with_what_it_waits_on(capsys)

def _commented(root: Path) -> None

def test_a_comment_on_a_table_survives(tmp_path)

def test_a_comment_on_a_key_survives(tmp_path)

def test_a_carried_comment_lands_above_the_key_it_documented(tmp_path)

def test_a_comment_in_a_vocabulary_file_survives(tmp_path)

def test_the_config_still_loads_with_comments_carried(tmp_path, monkeypatch)
    """Carried prose is a comment, not a value: the result still parses."""

def test_a_comment_whose_key_moved_is_reported_not_dropped(tmp_path, capsys)
    """
    `tags`, `statuses` and `tag_groups` do not exist on the far side —
    they split into a vocabulary and a field. A comment on one has no key to
    land above, so the upgrade has to say so rather than eat it.
    """

def test_a_dotted_key_is_a_path_not_a_name(tmp_path, capsys)
    """
    `uris.title = "..."` nests exactly as a table would. Read as one key
    named "uris.title" the comment above it lands nowhere, which is how the
    real config's one stranded block was found.
    """

def test_a_paragraph_break_stays_inside_the_block(tmp_path)
    """
    ruamel writes an empty comment line as an empty line, which is not a
    comment — it detaches the prose below from the key it documents.
    """

def test_a_vocabulary_file_header_lands_at_the_vocabulary_s_indent(tmp_path)
    """
    A vocabulary file's prose is written at column 0 because the file is
    its own document. Inlined under `vocabularies:` it is two levels in, and
    ruamel emits a carried comment at the column it was stored with — so the
    header ends up flush left inside an indented block, which is legal YAML
    and reads as though it belongs to nothing.
    """

def test_prose_inside_a_vocabulary_lands_above_its_entry(tmp_path)
    """
    The per-entry comments are the high-value ones — which decision added
    this topic, and why. At column 0 inside an indented mapping they document
    nothing a reader can see.
    """

def _comment_lines(text: str) -> list[str]

def test_every_comment_line_survives_the_crossing(tmp_path, capsys)
    """
    The property the examples above are instances of. Run against the real
    477-line config this carries 369 of 369 lines; here it holds over every
    shape a TOML config and a vocabulary file can put a comment in.
    """

def test_no_comment_line_is_carried_twice(tmp_path)
    """
    Presence is not enough: `yaml_set_comment_before_after_key` APPENDS to
    whatever a key already carries, so a caller that joins the blocks itself
    writes the first one twice. Counting is what catches that, and the
    presence property above cannot.
    """

```

## tests/test_vocabularies.py
```python
def write(root: Path, rel: str, text: str) -> Path

def scene(root: Path, n: int, extra: str) -> Path

def world(tmp_path, monkeypatch, table: dict | None, vocab: str | None, name: str, field: str | None, extra: dict | None) -> Path

def field()
    """The vocabulary field under test — not the tag axis beside it."""

def test_a_declared_vocabulary_is_read_with_its_values(tmp_path, monkeypatch)

def test_the_defaults_are_one_optional_value_and_no_default(tmp_path, monkeypatch)

def test_a_vocabulary_with_no_file_is_a_config_error(tmp_path, monkeypatch)
    """
    Eager, like a tag group that constrains nothing: a declared axis with
    no values would surface as 'no violations', which is the quiet failure.
    """

def test_a_default_outside_the_vocabulary_is_a_config_error(tmp_path, monkeypatch)

def test_a_default_takes_the_fields_shape(tmp_path, monkeypatch)

def test_required_and_default_together_is_a_config_error(tmp_path, monkeypatch)
    """
    A field with a default is never absent, so `required` says nothing —
    and a key that says nothing reads as though it did.
    """

def test_the_axis_is_a_declared_field_like_any_other(tmp_path, monkeypatch)
    """
    `tags` used to be refused here — it was an axis the code assumed, and
    the mechanism carved it out (ADR-054's deferred `closed` flag was the
    reason). It is a field now: backed by a vocabulary, OPEN, and named by
    the scheme as its axis (ADR-098).
    """

def test_a_field_entry_declares_its_type(tmp_path, monkeypatch)
    """
    `fields` is the table a field's shape and type live in; `vocabulary`
    is the one type it takes today, and an entry naming none is an error
    rather than a field that constrains nothing.
    """

def test_a_field_has_one_declaration(tmp_path, monkeypatch)

def test_the_field_and_its_vocabulary_may_be_named_differently(tmp_path, monkeypatch)
    """
    `world:` in the frontmatter, drawn from the `worlds` vocabulary: the
    field is the author's word, the vocabulary is the shared one's.
    **Pages render under the FIELD's name**, and the finding and the record
    line use it too. They used to render under the vocabulary's, which made a
    config detail into a published path — so sharing a vocabulary between two
    schemes, or renaming one, moved pages and orphaned the old directory.
    inactive-ok: ADR-098 — Proposed, named as the decision that moved
    this path; the citation is to the reasoning.
    """

def test_describe_names_the_values_the_default_and_both_files(tmp_path, monkeypatch)

def findings() -> list[str]

def test_a_value_outside_the_vocabulary_is_a_finding(tmp_path, monkeypatch)

def test_a_list_where_one_value_was_declared_is_a_finding(tmp_path, monkeypatch)

def test_an_absent_field_with_a_default_is_not_a_finding(tmp_path, monkeypatch)

def test_a_required_vocabulary_field_may_not_be_absent(tmp_path, monkeypatch)

def test_effective_values_apply_the_default_without_touching_the_source(tmp_path, monkeypatch)

def rendered(root: Path) -> dict[[Path, str]]

def test_the_index_renders_a_page_per_value_beside_the_tag_pages(tmp_path, monkeypatch)

def test_an_absent_field_lists_the_entry_under_the_default(tmp_path, monkeypatch)

def test_the_index_links_every_value_and_says_which_is_the_default(tmp_path, monkeypatch)

def test_value_pages_are_generated_views_nobody_has_to_link(tmp_path, monkeypatch)
    """
    Owned by the generator like the tag pages: a stale one is an orphan,
    and the docs index is not asked to list them one by one.
    """

def test_a_value_page_is_generated_by_the_reference_machinery_too(tmp_path, monkeypatch)
    """
    `is_generated` has to agree with `view_dirs`, and for a long time it
    did not.
    Two definitions of "the generator owns this file" existed side by side.
    `view_dirs()` listed the vocabulary directory, so the orphan lint and the
    docs index both knew — the test above. `Config.is_generated` did not, so
    the *reference* machinery treated the same page as hand-written prose:
    `doc_refs.doc_files()` filters on it, and `ref_status.scanned_files()`
    filters on that.
    Three things followed, in rising order of damage. `luria link --fix` would
    rewrite a page the next build overwrites. A citation inside one could not
    be excused, because an `inactive-ok:` comment written into a generated file
    is erased. And `luria index` stopped converging: the reports render in the
    same parallel pass as the vocabulary pages, so the report read the
    *previous* run's copy of a page it should never have opened, and a second
    index produced a different report than the first.
    Only a *retired* document made it visible — one whose citation the report
    would flag — so it was present from the day vocabularies shipped and found
    about 26 hours later, by an example that happened to retire one.
    """

def test_indexing_twice_leaves_the_reports_unchanged(tmp_path, monkeypatch)
    """
    The convergence this bug actually broke, asserted end to end.
    A `Superseded` scene is still a member of its world, so the world page
    cites a retired document. While that page was scannable the reference
    report gained a finding on the second run that the first had not seen —
    `luria index` was not idempotent, and idempotence is the whole basis of
    the staleness check.
    The positive control is the first assertion: a run that renders no report
    would satisfy "unchanged" trivially.
    """

def test_the_record_line_shows_the_written_values_not_the_default(tmp_path, monkeypatch)

def test_a_status_backed_by_a_vocabulary_is_named_once(tmp_path, monkeypatch)
    """
    `status:` became an ordinary declared vocabulary (#181), and the
    record line renders it twice for it: once through `statuses.display`,
    which is the only path that can say `Superseded — by X`, and again
    through the generic vocabulary loop that now sees it like any other.
    One field, one bit.
    """

def test_a_superseded_status_still_reads_its_successor(tmp_path, monkeypatch)
    """
    The reason the dedicated path wins over the generic one: the generic
    loop renders the bare word, and only `statuses.display` composes the
    successor the status note carries.
    """

```

## tests/test_wikilinks.py
```python
def project_with(project, extra: str)

def expand(project, text, name)

def test_local_code_expands(project)

def test_label_becomes_the_link_text(project)

def test_document_scheme_code_expands_to_an_anchor(project)
    """
    `[[VP-3]]` — a shape the prose scanner never takes (it needs a `#`),
    which is half the point of typing the brackets.
    """

def test_remote_code_expands_to_a_url(project)

def test_uid_remote_expands_through_its_template(project)

def test_a_low_issue_number_needs_no_cue_inside_brackets(project)
    """
    Bare `#10` in prose is ambiguous and left alone; `[[#10]]` is the
    author saying it is an issue — the brackets are the cue.
    """

def test_quoted_wikilinks_are_specimens(project)

def test_unresolvable_wikilinks_stay_put(project)

def test_expansion_is_idempotent(project)

def test_the_inner_code_is_not_also_a_bare_reference(project)
    """
    One wikilink, one demand. Without masking, `[[ADR-004]]` would be
    reported twice — as a wikilink and as the bare code inside it.
    """

def wikilink_errors(project) -> list[str]

def test_a_resolvable_wikilink_names_the_fixer(project)

def test_an_unresolvable_wikilink_is_its_own_error(project)
    """
    The one place the lint demands something `--fix` cannot do — by design:
    the author asserted a reference, so a silent skip would be a silent
    refusal (DP-1).
    """

```

## tests/test_yaml_edit.py
```python
def _loaded(text: str) -> dict

def test_a_block_lands_in_the_mapping_it_was_addressed_to()

def test_an_edit_keeps_the_comments_the_file_came_with()

def test_a_new_block_carries_its_own_comment_above_it()

def test_merging_a_family_keeps_the_families_already_there()

def test_a_rename_reaches_only_the_mapping_it_names()

def test_a_renamed_key_stays_where_its_author_put_it()

def test_renaming_what_is_not_there_changes_nothing()

def test_at_reports_absence_rather_than_inventing_it()

def test_span_is_the_lines_the_block_occupies()

def test_a_regex_survives_the_round_trip()

def test_the_shipped_template_is_already_in_the_shape_this_emits()

```
