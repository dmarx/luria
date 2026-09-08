"""Where a project keeps its record, and what its references look like.

Everything else in Luria is generic; this module is the one place that knows a
particular project. It reads `luria.toml` from the project root:

    [luria]
    issue_url = "https://github.com/owner/repo/issues/{n}"

    [luria.paths]
    docs = "docs"
    decisions = "record/decisions.d"
    design_principles = "docs/design-principles.md"

    [luria.fragments]
    "record/changelog.d" = "CHANGELOG.md"   # collected into…

    [luria.journals.devlog]
    dir = "record/devlog.d"             # …whereas a journal's entries persist
    output = "docs/devlog"

    [luria.code]
    globs = ["src/**/*.py", "*.md"]

    [luria.schemes.ADR]
    dir = "record/decisions.d"          # ground truth, filed by hand
    output = "docs/decisions"           # the browsable view, generated

The layout this describes is the read/write boundary (ADR-021): everything a
contributor *files* lives under `record/`, every view a reader *browses* lives
under `docs/`. A scheme whose `output` is unset keeps the old collocated shape
— view beside sources — so a project that arrived before the split never has
to move anything.

Every key has a default, so a project with the conventional layout needs a
`luria.toml` containing only `issue_url` — and Luria still runs without one, on
defaults alone, which is what makes `luria init` able to bootstrap.

Two merge rules, split by what a table *is* (ADR-047). A settings table —
`paths`, `code`, `lint`, `site` — merges per key: setting `docs` does not
clear `reports`. A **family** table — `schemes`, `fragments`, `journals`,
`remotes` — is replaced whole the moment the project declares it: the entries
are named by the project, so a family you write is yours entirely, and the
shipped `ADR` scheme is simply absent from a project that declares schemes
without it. Before this split, families merged too, which produced the two
limits that could only be documented, never obeyed: the default scheme could
not be removed, and a key it set (`output = "docs/decisions"`) could not be
unset by omission — only overridden.

The alternative was arguments threaded through every entry point. That works
until the second caller forgets one and the linter and the fixer disagree about
which files they cover — the exact class of bug ADR-002 exists to prevent. One
config object, resolved once from disk.
"""

from __future__ import annotations

import os
import re
import tomllib
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

CONFIG_NAME = "luria.toml"

DEFAULTS: dict = {
    "issue_url": "",
    "paths": {
        "docs": "docs",
        "decisions": "record/decisions.d",
        "design_principles": "docs/design-principles.md",
        # Committed with the other views rather than left in a build dir, so a
        # README badge has somewhere real to point (#35).
        "reports": "docs/reports",
    },
    "fragments": {
        "record/changelog.d": "CHANGELOG.md",
    },
    "code": {
        "globs": [],
        # Dated records: true about the day they were written, forever. Scanning
        # them for stale references produces permanent, unactionable noise. A
        # journal is one too, and is covered without being listed here — see
        # `Config.is_historical`.
        "historical": ["CHANGELOG.md"],
    },
    "schemes": {
        "ADR": {"dir": "record/decisions.d", "output": "docs/decisions",
                "active": "Active", "render": "index"},
    },
    # Sequences rendered from a relation the schemes already declare
    # (ADR-011 in the consumer record, #171). Empty for a project that
    # declares no relation worth walking, which is every project today.
    "chains": {},
    # Other projects whose records this one cites, keyed by a short prefix. A
    # reference then composes: `LU-ADR-013` is that remote's decision 13
    # (ADR-016).
    "remotes": {},
    # Dated entries that persist and render into books (ADR-020). Unlike a
    # scheme, a journal entry has no number — its identity is when it was
    # written — and unlike a fragment directory, its sources are never consumed.
    "journals": {
        "devlog": {
            "dir": "record/devlog.d",
            "output": "docs/devlog",
            "granularity": "month",
            "title": "Development log",
        },
    },
    "stale_days": 90,
    # The enforcement dial (ADR-035): warning classes named here fail the
    # lint instead of printing. Empty is the default posture — reported,
    # not enforced — and the acknowledgement directives keep working under
    # promotion, because only unacknowledged rows ever reach a class.
    "lint": {
        "fail_on": [],
        # This project's own concrete nouns, for the `narrow-titles` class.
        # Luria ships NONE: the whole point of the check is that the words are
        # yours, and a shipped list would be some other project's vocabulary
        # wearing the authority of a default. Empty means the class never
        # fires, which is the right behaviour for a project that has not
        # thought about it (ADR-035's warn-first posture, one step further).
        "narrow_terms": [],
        # May `luria lint` reach the network to check what an identifier
        # actually is? "auto" fetches only what the lockfile has no answer
        # for — usually the one citation a contribution just added — and
        # falls back to reporting it unchecked when the network is not
        # there. "never" is the hermetic build, answering only from the
        # lockfile. "require" makes an unreachable remote a finding, which
        # is what CI wants: a green build then means the references were
        # verified rather than merely remembered.
        "network": "auto",
    },
    # Whole records nested inside this one (ADR-077, ADR-078). Empty for the
    # ordinary project, which contains no others.
    "include_records": [],
    # The published site (ADR-042). Every key is derivable from `issue_url`
    # for a GitHub project, so the conventional case needs no `[luria.site]`
    # table at all — a default nobody has to read the docs to get.
    "site": {
        # Whether this record is published on the web at all. True because
        # every key below derives for a GitHub project and publishing is the
        # conventional case; `publish = false` is for a record that lives
        # only in its repository, and is how such a project turns off the
        # finding that its README names no site (DP-10).
        "publish": True,
        "title": "",
        "base_url": "",
        "source_url": "",
        "exclude": [],
        # Branding. All optional: unset means the generator's own look.
        "icon": "",
        "logo": "",
        "logo_dark": "",
        "theme": {},
    },
}

# `https://github.com/owner/repo/issues/{n}` → ("owner", "repo"). The one
# fact the site defaults are derived from, so a GitHub project that already
# configured issue links gets a title, a Pages URL and a source base free.
GITHUB_ISSUE_RE = re.compile(
    r"https?://github\.com/([^/]+)/([^/]+)/issues\b")


def find_root(start: Path | None = None) -> Path:
    """The project root: nearest ancestor with a `luria.toml`, else with a
    `.git`, else the starting directory. Env var `LURIA_ROOT` wins, which is
    what lets the tests run against fixture trees."""
    if env := os.environ.get("LURIA_ROOT"):
        return Path(env).resolve()
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / CONFIG_NAME).exists():
            return candidate
    for candidate in (here, *here.parents):
        if (candidate / ".git").exists():
            return candidate
    return here


def _merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


# unresolved-ok-block: ADR-tmp47fje — ADR-049's example of the shape, not a document
# A temporary code's tail: a literal `tmp` sentinel plus five base-36
# characters — `ADR-tmp47fje`. The alphabetic start keeps the numeric and
# temporary patterns disjoint by construction, and the spelled-out sentinel
# does two more jobs (ADR-049): a reader who has never met the convention still
# sees "provisional" at every citation site, and the prose pattern stops
# false-matching six-letter English after a prefix — `[a-z][a-z0-9]{5}`, the
# first shape, read "the ADR-review process" as a temporary reference.
TEMP_TAIL = r"tmp[a-z0-9]{5}"
_TEMP_TAIL_RE = re.compile(rf"^{TEMP_TAIL}$")


def is_temp_tail(tail: str) -> bool:
    """Whether a code's tail is a temporary one — the ONE place that decides.

    Every other spelling of this question composes `TEMP_TAIL` with a prefix to
    match a code or a filename. A caller holding only the tail asks here rather
    than inventing a cheaper test: `not tail.isdigit()` looks equivalent and
    is not, because it answers "this is not a number" — which a malformed tail
    also satisfies."""
    return bool(_TEMP_TAIL_RE.match(tail))


@dataclass(frozen=True)
class TagGroup:
    """A set of a scheme's tags that combine under a rule.

    `tags.yaml` declares what a tag *means*; this declares which of them may
    appear together, because some vocabularies are axes rather than piles. An
    argument is sound or overreaching or invalid — exactly one — and saying so
    in prose leaves it to be checked by nobody, which is how a rule becomes a
    comment.

    Opt-in per scheme: a scheme declaring no group is unconstrained, which is
    every scheme that exists today."""

    name: str
    tags: frozenset[str]
    # "any" (the default — the group is a label, not an axis), "at-most-one",
    # or "exactly-one".
    require: str = "any"
    # Tags that forbid this whole group. `sound` excluding the failure modes
    # is the motivating case: naming how an argument fails contradicts saying
    # it does not.
    excluded_by: frozenset[str] = frozenset()
    # True when membership came from the vocabulary's `primary_for` keys
    # rather than an inline list. Carried so a reader of the generated record
    # page can tell which file to edit.
    derived: bool = False


REQUIRE_RULES = ("any", "at-most-one", "exactly-one")


@dataclass(frozen=True)
class RequiredWhen:
    """A field demanded only while another field says one of these things:

        [luria.schemes.SOTA.fields.promote_when]
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
    on: str
    values: tuple[str, ...]


@dataclass(frozen=True)
class PlainField:
    """A field declared in the `fields` table that carries no vocabulary —
    its type is "any truthy value", the same as a `requires` entry, and what
    it adds is when the requirement applies."""
    field: str
    required: bool = False
    many: bool = False
    required_when: RequiredWhen | None = None


@dataclass(frozen=True)
class FieldGroup:
    """Several fields of which an entry must carry some — a requirement that
    is satisfied by any of them, named for what they have in common:

        [luria.schemes.LIT.field_groups.source]
        fields  = ["arxiv", "doi", "url"]
        require = "at-least-one"          # or "exactly-one", "at-most-one"

    `requires` demands every field it names; a paper that was never posted
    to arXiv but has a DOI, or only a URL, has a source all the same, and
    demanding `arxiv` of it is demanding the wrong thing. The group says
    what is actually required — *a source* — and which fields count as
    one. Opt-in per scheme, like a tag group (ADR-054)."""
    name: str
    fields: tuple[str, ...]
    require: str = "at-least-one"


FIELD_RULES = ("at-least-one", "exactly-one", "at-most-one")


@dataclass(frozen=True)
class Reference:
    """A frontmatter field that holds a code from a named scheme.

        [luria.schemes.SOTA.references]
        source = { scheme = "LIT", required = true }

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
    resolves every element, and each becomes an edge (#141)."""
    field: str
    scheme: str
    required: bool = True
    many: bool = False
    converse: str = ""
    # When the requirement applies, if not always (see `RequiredWhen`).
    required_when: RequiredWhen | None = None


@dataclass(frozen=True)
class Vocabulary:
    """A frontmatter field backed by a scheme-local controlled vocabulary
    (ADR-076):

        [luria.schemes.SCENE.fields.worlds]
        vocabulary = "worlds"     # the values: worlds.yaml beside the records
        many       = true         # a list of values; default false, one value
        default    = ["B"]        # the effective value when the field is absent

    `fields` is the table a field's shape and type are declared in; today
    `vocabulary` is the one type it takes, and `requires` and `references`
    remain the spellings for the other two kinds until they consolidate
    here. The values file is shaped like `tags.yaml`. Closed: a value
    outside the file is a finding. `required` (default false) and `default`
    are exclusive — a field with a default is never absent, so `required`
    would say nothing."""
    # The frontmatter key, and the vocabulary (file stem) it draws from.
    # Usually the same word; `world:` backed by `worlds.yaml` is the other.
    field: str
    name: str
    file: Path
    many: bool = False
    required: bool = False
    # Normalised to a tuple of values whatever the shape declared; None when
    # absence is a meaningful state rather than a spelling of the default.
    default: tuple[str, ...] | None = None
    # When the requirement applies, if not always (see `RequiredWhen`).
    required_when: RequiredWhen | None = None


# The axes every scheme has, with their own files and their own rules.
# `tags` stays: it is OPEN, and a vocabulary is closed by
# construction (ADR-054 deferred even a `closed` flag), and its
# `tag_groups` constrain a *subset of values*, which a vocabulary
# cannot express. `status` needed neither — it is the closed,
# single-valued case the mechanism was built for (#181).
BUILT_IN_AXES = ("tags",)


# Path → ((mtime_ns, size), number). Keyed on the stat rather than reset
# explicitly: a write bumps mtime, so the entry expires on its own.
_NUMBER_CACHE: dict[Path, tuple[tuple[int, int], int | None]] = {}

# `number:` is an integer on a line of its own, so it can be read without a YAML
# parse of the whole document — this runs once per file per lint, and the
# frontmatter of a scaffolded document is mostly comments.
_NUMBER_RE = re.compile(r"^number:[ \t]*(\d+)[ \t]*$", re.M)


def _declared_number(path: Path) -> int | None:
    """The `number:` a document's frontmatter declares, or None.

    Read out of the frontmatter block only: a `number:` in the body is prose
    about identity, not a claim to one — and it does occur there, so the
    block boundary is what makes the field readable without a YAML parse."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 3)
    if end == -1:
        # Unterminated frontmatter is no frontmatter, which is what
        # `parse_frontmatter` decides too — searching on would read the body,
        # and a `number:` in the body is prose about identity, not a claim to one.
        return None
    m = _NUMBER_RE.search(text[4:end + 1])
    return int(m.group(1)) if m else None


@dataclass(frozen=True)
class Scheme:
    """A family of referable documents — `ADR-012`, `RFC-7`, `SPEC-3`.

    Luria ships with one, and knowing that one is not built in is the point:
    the annotation vocabulary says `inactive-ok`, not `adr-ok`, and a code
    carries its prefix, so a second scheme is an entry here (ADR-006)."""
    prefix: str
    dir: Path
    active: str = "Active"
    # The retirement pair, defaults rather than laws (ADR-085). A
    # project whose decisions are `Supplanted` and point at their
    # replacement through `supplanted_by:` says so here, and every check,
    # edge and rendering follows its words. `active` set the precedent long
    # before: which word means in force was already the project's to choose.
    successor: str = "superseded_by"
    retires_on: str = "Superseded"
    # A second spelling this scheme's documents answer to, rendered from each
    # document's own frontmatter (#219):
    #
    #     alias = "LIT-{authors[0]}-{year}-{number}"
    #
    # Recovers an identifier a reader can interpret without a lookup, which
    # is what a record gives up when it adopts sequential codes. Include
    # `{number}` and collisions are impossible by construction; leave it out
    # and the lint reports the two documents that landed on one spelling.
    # Unlike `formerly:`, the fixer leaves a rendered alias alone — the point
    # is to keep it written.
    alias: str = ""
    # How this scheme's generated view is built. "index" is a table of links
    # plus per-tag pages — right when the documents are browsed and read one at
    # a time. "document" concatenates the bodies into one page — right when the
    # set is read as a whole, which is what a principles doc is (ADR-012).
    render: str = "index"
    # Where the generated view lands. For `render = "document"` this is the
    # assembled page itself; for `render = "index"` it is the directory the
    # index and its tag pages render into. Unset means the view renders beside
    # the sources — the collocated shape every project had before the
    # read/write boundary existed (ADR-021), kept so adoption never starts
    # with a move. Omission genuinely unsets it for every scheme, the shipped
    # `ADR` included: a declared `schemes` family replaces the defaults
    # rather than merging into them (ADR-047), so there is nothing left to
    # inherit the key from.
    output: Path | None = None
    # When this scheme's numbers are assigned (ADR-049). "filing" is today's
    # behaviour: `luria new` takes the next free number on the spot — right
    # for a single-writer record, and a distributed claim on a global counter
    # the moment branches are concurrent. "merge" issues a temporary code
    # unresolved-ok: ADR-tmp47fje — ADR-049's example of the shape
    # instead (`ADR-tmp47fje`, visibly provisional and never a number), and
    # `luria concretize` — run wherever merges serialize — assigns the real
    # numbers in merge order and records each temporary code as a permanent
    # `aka:` alias.
    allocate: str = "filing"
    # Whether a title in this scheme must avoid `[luria.lint] narrow_terms`.
    # False everywhere by default, including for the shipped ADR scheme: a
    # decision is *about* something specific and naming it is correct. A
    # scheme whose documents claim to transfer — principles, values — is where
    # this earns its keep.
    titles_generalize: bool = False
    # Frontmatter fields this scheme demands beyond the standard set. What
    # makes a CROSS-SCHEME move safe to automate (ADR-040): `luria migrate`
    # moves the file, and the document then fails lint until a human supplies
    # what the target scheme's template would have prompted for. The machinery
    # relocates a document; only a person can vouch that it belongs.
    requires: tuple[str, ...] = ()
    # Which of this scheme's tags may appear together (see `TagGroup`). Empty
    # for every scheme that does not declare `[luria.schemes.X.tag_groups]`,
    # which is the unconstrained behaviour every project has today.
    tag_groups: tuple[TagGroup, ...] = ()
    # Where this scheme's tag vocabulary lives. Unset means the collocated
    # `tags.yaml` beside the sources, which is where it has always been. Set,
    # two schemes can name ONE file and share a vocabulary instead of keeping
    # a copy each (ADR-060).
    tags_file: Path | None = None
    # Several fields of which an entry must carry some (see `FieldGroup`):
    # `[luria.schemes.X.field_groups.NAME]`. What `requires` cannot say —
    # that any of these satisfies the need, and the need has a name.
    field_groups: tuple[FieldGroup, ...] = ()
    # Frontmatter fields that hold a code from another scheme, by field name:
    # `source = { scheme = "LIT", required = true, many = false }`. `requires`
    # says a field is present; this says what it means, and whether it holds
    # one code or a list of them.
    references: tuple[Reference, ...] = ()
    # Frontmatter fields backed by a controlled vocabulary (see
    # `Vocabulary`): `[luria.schemes.X.fields.NAME]` with `vocabulary =
    # "V"`, values in `V.yaml` beside the records. The third instance of
    # what `statuses.yaml` and `tags.yaml` already are.
    vocabularies: tuple[Vocabulary, ...] = ()
    # Fields declared in the same table with no vocabulary: any truthy value,
    # carrying when the requirement applies (`PlainField`, #170).
    plain_fields: tuple[PlainField, ...] = ()
    # Fields computed from another field rather than written (`derive.Derived`,
    # #216). Resolved onto a document's frontmatter wherever one is read, so a
    # derived field is an ordinary field to everything downstream — and a
    # written one is a finding, because it has a source and this is not it.
    derived: tuple = ()
    # Why this scheme's records all sharing one status is deliberate rather
    # than a dead enforcement mechanism (#104). The `inert-status` check is the
    # one judgment call in luria with no acknowledgement — every other has an
    # `inactive-ok:`-style comment carrying a reason, and this finding is about
    # a *scheme*, so it has no site to comment at. Setting this is that
    # acknowledgement: the row stops being a finding and the reason renders in
    # its place, so a reader still sees that nobody is being judged and why.
    # A reason is mandatory for the same purpose it is mandatory in a
    # directive — silence that carries no argument is indistinguishable from
    # an oversight.
    uniform_ok: str | None = None
    # The share of records at one status above which the field stops carrying
    # information. 1.0 — the default — is the original rule: report only when
    # EVERY record agrees, on the argument that a corpus whose claims all
    # survive is legitimate and one retirement proves a judgement is being
    # made. That argument holds for a young or genuinely stable scheme and
    # fails for a large one: a registry at 133/144 `Active` has a 92% prior
    # before you read a status, and eleven exceptions are enough to silence
    # the check permanently while a quarter of its entries go unexamined.
    # Lowering this asks the sharper question — is the vocabulary *exercised*
    # — and is opt-in because the answer is a matter of what a scheme is for.
    uniform_share: float = 1.0

    @property
    def view(self) -> Path:
        """The directory an index-rendered scheme's view lives in."""
        return self.output or self.dir

    @property
    def index_path(self) -> Path:
        return self.view / "README.md"

    @property
    def tag_dir(self) -> Path:
        return self.view / "tags"

    def vocab_dir(self, name: str) -> Path:
        """Where a vocabulary's per-value pages render, beside the tag pages."""
        return self.view / name

    # The stub and the tag metadata are *authored*, so they live with the
    # sources — the view directory holds only what the generator wrote, which
    # is what lets the lint call anything else in it an error (ADR-021).
    @property
    def stub(self) -> Path:
        return self.dir / "README.stub"

    @property
    def tags_yaml(self) -> Path:
        return self.tags_file or self.dir / "tags.yaml"

    @property
    def statuses_yaml(self) -> Path:
        """What this scheme's statuses mean. Optional; absent leaves the
        closed vocabulary open to all five and renders no legend."""
        return self.dir / "statuses.yaml"

    @property
    def pattern(self):
        return re.compile(rf"\b{self.prefix}[- ](?P<num>\d{{1,4}})\b")

    # Kept as a class attribute because every regex here composes it with a
    # prefix; the definition and the predicate both live at module level.
    TEMP_TAIL = TEMP_TAIL

    @property
    def temp_pattern(self):
        return re.compile(rf"\b{self.prefix}-(?P<tail>{self.TEMP_TAIL})\b")

    def temp_of(self, path: Path) -> str | None:
        """The temporary tail a filename carries, or None if it isn't one."""
        m = re.fullmatch(rf"{self.prefix}-({self.TEMP_TAIL})\.md", path.name)
        return m.group(1) if m else None

    def temp_documents(self) -> dict[str, Path]:
        """Tail → path for every temporary document awaiting concretization."""
        found: dict[str, Path] = {}
        for path in sorted(self.dir.glob("*.md")):
            tail = self.temp_of(path)
            if tail is not None:
                found[tail] = path
        return found

    def code(self, number: str | int) -> str:
        return f"{self.prefix}-{int(number):03d}"

    def filename(self, number: str | int) -> str:
        """`ADR-013.md` — the file is named for the code and nothing else.

        The title lives in the frontmatter, where a correction costs an edit
        rather than a rename plus every link that pointed at the old name
        (ADR-013)."""
        return f"{self.code(number)}.md"

    def number_of(self, path: Path) -> int | None:
        """This document's identity: its `number:`, or the one its filename carries.

        The frontmatter wins, because that is where identity lives (#219).
        The filename is the fallback and the witness — a record written
        before `number:` existed still reads, and `luria repair` populates the
        field from the path it already asserts, which is how a project
        migrates without anyone typing a number.

        Cached on (mtime, size) rather than reset by hand: every writer of a
        document bumps its mtime, so the cache invalidates itself and no
        caller has to remember. Reading the field costs a parse, and this is
        the hot path — `documents()` runs on every lint, index and link
        pass."""
        try:
            st = path.stat()
        except OSError:
            return self.number_in_name(path)
        key = (st.st_mtime_ns, st.st_size)
        hit = _NUMBER_CACHE.get(path)
        if hit is not None and hit[0] == key:
            return hit[1]
        held = _declared_number(path)
        found = held if held is not None else self.number_in_name(path)
        _NUMBER_CACHE[path] = (key, found)
        return found

    def number_in_name(self, path: Path) -> int | None:
        """The document number a filename carries, or None if it isn't one.

        Deliberately tolerant of a trailing slug: `adr-010-some-title.md` is
        what most projects arrive with, and refusing to read them would make
        adoption a rename-everything-first proposition. Luria *writes* the short
        form and *reads* both."""
        m = re.fullmatch(rf"{self.prefix}-0*(\d+)(?:-[^/]*)?\.md", path.name,
                         re.IGNORECASE)
        return int(m.group(1)) if m else None

    def documents(self) -> dict[int, Path]:
        """Number → path for every document in this scheme, ascending.

        The one place a scheme directory is read. Five copies of this glob had
        accumulated, each with its own regex — the drift DP-4 names, harmless
        only for as long as the filename shape never changed."""
        found: dict[int, Path] = {}
        for path in sorted(self.dir.glob("*.md")):
            if self.temp_of(path) is not None:
                continue
            number = self.number_of(path)
            if number is not None:
                found.setdefault(number, path)
        return dict(sorted(found.items()))


# The shipped URI templates, per name and per construction shape. GitHub's
# blob/raw pairing lives HERE, as data — not as a regex that parses a rendered
# URL back apart. A different forge is a different pair of templates in a
# remote's `uris` table; teaching Luria a new forge builtin would be one more
# entry, and both are the same kind of thing.
_BLOB = "https://github.com/{repo}/blob/{ref}"
_RAW = "https://raw.githubusercontent.com/{repo}/{ref}"
_DEFAULT_URIS: dict[str, dict[str, str]] = {
    "read": {"document": _BLOB + "/{document}#{anchor}",
             "file": _BLOB + "/{dir}/{filename}"},
    "bytes": {"document": _RAW + "/{document}",
              "file": _RAW + "/{dir}/{filename}"},
}


def _fold_uris(spec: dict, where: str) -> dict[str, str]:
    """A table's `uris` plus its sugar spellings, as one dict.

    `url` and `pin_url` ARE `uris.read` and `uris.bytes` — the short names
    for the two relations Luria itself consumes. Folded at load so exactly
    one structure answers at render time (DP-4); setting both spellings to
    different values is a config error rather than a silent winner."""
    declared = {str(k): str(v) for k, v in (spec.get("uris") or {}).items()}
    for sugar, uri_name in (("url", "read"), ("pin_url", "bytes")):
        value = spec.get(sugar, "")
        if not value:
            continue
        if declared.get(uri_name, value) != value:
            raise ValueError(
                f"luria.toml: {where} sets both `{sugar}` and "
                f"`uris.{uri_name}` — they are one setting; keep either")
        declared[uri_name] = value
    return declared


@dataclass(frozen=True)
class RemoteScheme:
    """How one of a remote's code families constructs (ADR-023).

    A remote is not one directory of files — it is a project, and different
    schemes in it have different shapes. Each entry names one construction:

        [luria.remotes.SG.schemes.ADR]
        dir = "docs/decisions"                 # file per code

        [luria.remotes.SG.schemes.DP]
        document = "docs/design-principles.md" # sections of one file…
        anchor = "dp-{number}"                 # …at Luria's stable anchors

    `anchor` defaults to the prefix lowercased plus the number — `dp-18` —
    which is the anchor shape Luria's own document render emits, so a remote
    on current conventions needs only the `document` line. A `url` template
    overrides both, and a `uris` table names further relations for this
    family alone — both with the full template vocabulary (see `Remote`)."""
    prefix: str
    dir: str = ""
    document: str = ""
    anchor: str = ""
    url: str = ""
    # Where this scheme's *stable bytes* live, for content pins — same
    # substitutions as `url`. Declared, not derived: only the project can vouch
    # that a URL serves content rather than a page around it (#135).
    pin_url: str = ""
    # Content-pin every cited reference in this scheme (#135): `luria remotes
    # --pin` endorses them all, and `luria lint` reports any cited code the
    # lockfile has not endorsed yet — the endorsement is of the code family
    # as a body of knowledge, not of one citation at a time.
    pin: bool = False
    # Named URI templates for this code family — `[….schemes.Y.uris]`. The
    # general form of `url` and `pin_url`, which are its `read` and `bytes`
    # entries; populated at load with the sugar folded in (`_fold_uris`).
    uris: dict[str, str] = field(default_factory=dict)

    def anchor_for(self, number: int) -> str:
        template = self.anchor or f"{self.prefix.lower()}-{{number}}"
        return template.format(number=number, prefix=self.prefix)


@dataclass(frozen=True)
class Remote:
    """Another project's record, cited from this one.

    A reference to it composes the remote's prefix with the foreign scheme's
    own code — `LU-ADR-013` — so the namespace is explicit at the point of use
    and nothing has to guess which project an unprefixed code meant (ADR-016).

        [luria.remotes.LU]
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

        [luria.remotes.ARXIV]
        uid = "(\\d{4})[.:](\\d{4,5})"
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

        [luria.remotes.LU.uris]
        bytes   = "https://gitlab.example/{repo}/-/raw/{ref}/{dir}/{filename}"
        history = "https://github.com/{repo}/commits/{ref}/{dir}/{filename}"

    GitHub's blob/raw pair is simply the shipped default pair of `read` and
    `bytes` templates for a remote with a `repo` — a different forge is a
    different pair of lines, not a different subsystem."""
    prefix: str
    repo: str = ""
    # Where the remote's *issues* live. Defaults to the GitHub convention for
    # a remote with a `repo`, and stays empty for one reached by a `url`
    # template alone — an arXiv identifier or a ticket key has no tracker, and
    # guessing one would put the silent wrongness of #194 in a new place.
    issue_url: str = ""
    ref: str = "main"
    dir: str = "record/decisions.d"
    name: str = ""
    url: str = ""
    # The delimiter between the prefix and the rest of the reference. "-" is
    # the convention; a project whose uids themselves contain hyphens can move
    # it out of the way.
    delim: str = "-"
    # A regex for the reference's tail. Unset means the Luria shape — a scheme
    # code like `ADR-032`, normalised and constructed through the machinery
    # below. Set, the tail is an opaque identifier: matched exactly, never
    # normalised, constructed only through the `url` template.
    uid: str = ""
    # Where this remote's stable bytes live, for content pins (#135) — same
    # substitutions as `url`. `url` is where a *reader* lands; this is what a
    # pin *hashes*, and they differ whenever the reader's page is a rendering
    # (an arXiv abstract, a ticket view) whose markup churns under identical
    # content. Declared rather than derived, because only the project can
    # vouch that a URL is content-stable; unset, only a GitHub file
    # construction can be pinned.
    pin_url: str = ""
    # How to read a title out of what `uris.title` serves: a regex whose first
    # group is the title. Declared rather than derived, for the same reason
    # `pin_url` is — only the project can vouch that a URL serves metadata in
    # a shape worth trusting, and guessing per host would be magic that fails
    # silently when a provider changes its response. The two recipes that
    # matter are in the documentation; both are one line.
    title_re: str = ""
    # Content-pin every cited reference to this remote (#135). Set here it
    # covers the whole namespace; set on one of the remote's schemes, just
    # that code family. Registration in config rather than per code, because
    # the judgement is per source: a record this project leans on is endorsed
    # as a body of knowledge, and one `luria remotes --pin` keeps the hashes
    # current while `luria lint` reports what is cited but not yet endorsed.
    pin: bool = False
    # Named URI templates — `[luria.remotes.X.uris]`. A code relates to a SET
    # of URIs through one template vocabulary, and this table is where a
    # relation beyond the shipped two gets its name; `url` and `pin_url` are
    # sugar for its `read` and `bytes` entries, folded in at load.
    uris: dict[str, str] = field(default_factory=dict)
    schemes: dict[str, RemoteScheme] = field(default_factory=dict)

    @property
    def label(self) -> str:
        return self.name or self.repo or self.prefix

    def canon(self, tail: str) -> str:
        """The tail's one spelling. `ADR-32` and `ADR-032` name one document
        in a scheme-shaped remote; a uid is already exact and stays put."""
        if self.uid:
            return tail
        prefix, number = tail.rsplit("-", 1)
        return f"{prefix.upper()}-{int(number):03d}"

    def base(self, dir: str | None = None) -> str:
        """A directory in the remote, as a URL."""
        return (f"https://github.com/{self.repo}/blob/{self.ref}/"
                f"{self.dir if dir is None else dir}").rstrip("/")

    def scheme_for(self, code: str) -> RemoteScheme | None:
        return self.schemes.get(code.rsplit("-", 1)[0].upper())

    def link(self, code: str, filename: str | None = "") -> str:
        """The reader's URL for a foreign code — the `read` URI."""
        return self.uri("read", code, filename)

    def uri(self, name: str, code: str, filename: str | None = "") -> str:
        """Render the named URI for a code — the one place a code becomes a
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
        (ADR-024)."""
        if self.uid:
            return self._format(self.uris.get(name, ""), code)
        scheme = self.scheme_for(code)
        if name == "read":
            if scheme is not None and scheme.uris.get("read"):
                template = scheme.uris["read"]
            elif scheme is not None and scheme.document and self.repo:
                template = _DEFAULT_URIS["read"]["document"]
            elif scheme is not None and scheme.dir and self.repo:
                template = _DEFAULT_URIS["read"]["file"]
            elif self.uris.get("read"):
                template = self.uris["read"]
            elif self.repo:
                template = _DEFAULT_URIS["read"]["file"]
            else:
                return ""
        else:
            template = (scheme.uris.get(name, "") if scheme else "") \
                or self.uris.get(name, "") \
                or _DEFAULT_URIS.get(name, {}).get(self._construction(scheme), "")
        return self._render(template, code, scheme, filename) if template else ""

    def _construction(self, scheme: RemoteScheme | None) -> str:
        """How `read` constructs when no template governs it: "document",
        "file", or "" when a template (or nothing) answers instead. The only
        shapes whose other-name defaults are derivable rather than guessed."""
        if scheme is not None and scheme.uris.get("read"):
            return ""
        if scheme is not None and scheme.document and self.repo:
            return "document"
        if scheme is not None and scheme.dir and self.repo:
            return "file"
        if self.uris.get("read"):
            return ""
        return "file" if self.repo else ""

    def _render(self, template: str, code: str, scheme: RemoteScheme | None,
                filename: str | None) -> str:
        """One template, one vocabulary. A variable the remote cannot supply
        is simply absent, and a template that references it renders ""."""
        prefix, number = code.rsplit("-", 1)
        values: dict = {"code": code, "number": int(number), "prefix": prefix,
                        "ref": self.ref,
                        "dir": (scheme.dir if scheme is not None and scheme.dir
                                else self.dir)}
        if self.repo:
            values["repo"] = self.repo
        if scheme is not None and scheme.document:
            values["document"] = scheme.document
            values["anchor"] = scheme.anchor_for(int(number))
        if filename is not None:
            values["filename"] = filename or f"{code}.md"
        try:
            return template.format(**values)
        except (KeyError, IndexError):
            return ""

    def _format(self, template: str, code: str) -> str:
        """A uid template, fed the whole tail as {0}/{uid} and its capture
        groups by position (ADR-024)."""
        if not template:
            return ""
        m = re.fullmatch(self.uid, code)
        groups = m.groups() if m else ()
        return template.format(code, *groups, uid=code, prefix=self.prefix)

    def auto_pin(self, code: str) -> bool:
        """Whether config declares this code's content pinned (#135).

        `pin = true` on the remote covers its whole namespace; on one of its
        schemes, that code family. Declared per source rather than per
        citation, because that is where the judgement lives: a record this
        project leans on is endorsed as a body of knowledge."""
        if self.pin:
            return True
        scheme = None if self.uid else self.scheme_for(code)
        return bool(scheme and scheme.pin)


@dataclass(frozen=True)
class Fragment:
    """One fragment directory: where its pieces assemble to, and in what shape.

        [luria.fragments]
        "record/changelog.d" = "CHANGELOG.md"       # the append style
        [luria.fragments."record/changelog.d"]      # or, spelled as a table:
        file  = "CHANGELOG.md"
        style = "changelog"

    `append` is the narrative shape: bodies oldest-first, inserted before the
    marker, so the marker stays at the end and the log reads top-down.
    `changelog` is the release shape: each collection is one dated batch,
    inserted right after the marker so the newest batch reads first, fragments
    newest-first within it. The shape is configuration because the fragment
    convention is the contract, not the collector (ADR-028) — the same
    directory-of-fragments serves either reading order."""
    target: Path
    style: str = "append"


def primary_tags(prefix: str, tags_path: Path) -> frozenset[str]:
    """Terms this scheme may carry as a primary, from the vocabulary itself.

    A tag says which schemes it is a primary for, where the tag is defined:

        training-optimization:
          label: Training optimization
          primary_for: [LIT, SOTA]

    Without this a shared vocabulary has to be restated as a `tags` list per
    group, which is the same set of strings written a third and fourth time —
    and the copies drift, because nothing relates them. Measured on the record
    that motivated this: seven terms across four places, and the blurbs for
    the same tag already disagreed between two of them (ADR-060)."""
    if not tags_path.exists():
        return frozenset()
    try:
        import yaml
        declared = yaml.safe_load(tags_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return frozenset()
    found = set()
    for tag, meta in declared.items():
        for named in (meta or {}).get("primary_for", ()) or ():
            if str(named).upper() == prefix.upper():
                found.add(str(tag))
    return frozenset(found)


def _tag_groups(prefix: str, raw: dict,
                tags_path: Path | None = None) -> tuple[TagGroup, ...]:
    """Read a scheme's `[luria.schemes.X.tag_groups]` tables.

    Validated here rather than at lint time: a misspelled rule is a config
    error, and a config error that surfaces as "no violations" is the quiet
    failure this whole feature exists to remove.

    A group that lists no `tags` derives its membership from the vocabulary's
    `primary_for` keys. That is still validated eagerly — an empty derivation
    is the same "constrains nothing" error as an empty list, and finding it at
    load keeps the promise above."""
    groups = []
    for name, spec in raw.items():
        rule = str(spec.get("require", "any"))
        if rule not in REQUIRE_RULES:
            raise ValueError(
                f"luria.toml: schemes.{prefix}.tag_groups.{name} has "
                f"require = {rule!r}; expected one of {list(REQUIRE_RULES)}")
        tags = frozenset(str(x) for x in spec.get("tags", ()))
        derived = False
        if not tags and tags_path is not None:
            tags = primary_tags(prefix, tags_path)
            derived = bool(tags)
        if not tags:
            raise ValueError(
                f"luria.toml: schemes.{prefix}.tag_groups.{name} lists no "
                f"tags and no tag in {tags_path} names {prefix} in its "
                f"`primary_for`, so it constrains nothing"
                if tags_path is not None else
                f"luria.toml: schemes.{prefix}.tag_groups.{name} lists no "
                f"tags, so it constrains nothing")
        groups.append(TagGroup(
            name=name, tags=tags, require=rule, derived=derived,
            excluded_by=frozenset(str(x) for x in spec.get("excluded_by", ()))))
    return tuple(groups)


def _field_groups(prefix: str, raw: dict) -> tuple[FieldGroup, ...]:
    """Read a scheme's `[luria.schemes.X.field_groups]` tables. Validated at
    load like a tag group: a group naming no fields, or a rule that is not
    one, would surface as "no violations"."""
    groups = []
    for name, spec in raw.items():
        rule = str(spec.get("require", "at-least-one"))
        if rule not in FIELD_RULES:
            raise ValueError(
                f"luria.toml: schemes.{prefix}.field_groups.{name} has "
                f"require = {rule!r}; expected one of {list(FIELD_RULES)}")
        fields = tuple(str(f) for f in spec.get("fields", ()))
        if not fields:
            raise ValueError(
                f"luria.toml: schemes.{prefix}.field_groups.{name} lists no "
                f"fields, so it constrains nothing")
        groups.append(FieldGroup(name=str(name), fields=fields, require=rule))
    return tuple(groups)


def _checked_converses(prefix: str, refs: tuple) -> tuple:
    """Refuse a converse declaration that cannot mean what it says.

    A relation's converse is the relation read backwards: if A `extends` B
    then B is `extended_by` A. Declaring the pair is what lets the fixer
    complete one side from the other, and symmetry is simply the case where
    a relation is its own converse.

    Four things have to hold, and each of them fails silently otherwise —
    a pair that never completes looks exactly like a record with nothing
    missing (DP-15)."""
    by_name = {r.field: r for r in refs}
    for ref in refs:
        if not ref.converse:
            continue
        where = f"luria.toml: schemes.{prefix}.references.{ref.field}.converse"
        other = by_name.get(ref.converse)
        if other is None:
            raise ValueError(
                f"{where}: {ref.converse!r} is not a reference {prefix} "
                f"declares — a converse names the field holding the same "
                f"relation read backwards, and it has to exist to be written "
                f"into (declared: {', '.join(sorted(by_name)) or 'none'})")
        if other.scheme != ref.scheme:
            raise ValueError(
                f"{where}: {ref.field!r} holds {ref.scheme} codes and "
                f"{ref.converse!r} holds {other.scheme} codes — the same "
                f"relation read backwards points at the same scheme")
        if other.converse != ref.field:
            raise ValueError(
                f"{where}: {ref.converse!r} does not name {ref.field!r} back "
                f"— a converse is mutual, and half a pair completes in one "
                f"direction only "
                f"(saw: {ref.converse}.converse = {other.converse or 'unset'!r})")
        for side in (ref, other):
            if not side.many:
                raise ValueError(
                    f"{where}: {side.field!r} needs `many = true` — either "
                    f"side of a pair is written into, and several documents "
                    f"can stand in one relation to the same one")
    return refs


def _references(prefix: str, raw: dict) -> tuple[Reference, ...]:
    """Read a scheme's `[luria.schemes.X.references]` table."""
    found = []
    for field, spec in raw.items():
        if not isinstance(spec, dict) or not spec.get("scheme"):
            raise ValueError(
                f"luria.toml: schemes.{prefix}.references.{field} needs a "
                f"`scheme` — it names which scheme's codes the field holds")
        where = f"luria.toml: schemes.{prefix}.references.{field}"
        required = bool(spec.get("required", True))
        found.append(Reference(field=str(field),
                               scheme=str(spec["scheme"]).upper(),
                               required=required,
                               many=bool(spec.get("many", False)),
                               converse=str(spec.get("converse", "")),
                               required_when=_required_when(where, spec,
                                                            required)))
    return tuple(_checked_converses(prefix, tuple(found)))


def _required_when(where: str, spec: dict, required: bool) -> RequiredWhen | None:
    """`required_when = { status = ["Proposed"] }` — one field, one set of
    values. Validated eagerly, for the reason every other declaration is: a
    condition that can never hold, or one whose meaning the reader has to
    guess, surfaces as "no violations"."""
    raw = spec.get("required_when")
    if raw is None:
        return None
    if not isinstance(raw, dict) or not raw:
        raise ValueError(f"{where}: `required_when` is a table naming one "
                         f"field and the values that make this one required "
                         f"— `{{ status = [\"Proposed\"] }}`")
    if len(raw) > 1:
        raise ValueError(
            f"{where}: `required_when` names one field, not "
            f"{', '.join(sorted(raw))} — two conditions would need an `and` "
            f"or an `or` this config does not have")
    if required:
        raise ValueError(f"{where}: the field is already always required, so "
                         f"`required_when` says nothing — drop one of them")
    on, values = next(iter(raw.items()))
    values = tuple(str(v) for v in
                   (values if isinstance(values, list) else [values]))
    if not values:
        raise ValueError(f"{where}: `required_when.{on}` lists no values, so "
                         f"the condition can never hold and the field is "
                         f"never required")
    return RequiredWhen(on=str(on), values=values)


def _fields(prefix: str, raw: dict, scheme_dir: Path, root: Path,
            references: tuple, scaffolding: bool = False) -> tuple:
    """Read a scheme's `[luria.schemes.X.fields]` tables, as
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
    violations", which is the quiet failure a declaration exists to remove."""
    from .derive import parse as parse_derivation
    from .vocabularies import declared
    found = []
    plain: list[PlainField] = []
    rules = []
    taken = {r.field for r in references}
    for field, spec in raw.items():
        where = f"luria.toml: schemes.{prefix}.fields.{field}"
        if field in BUILT_IN_AXES:
            raise ValueError(f"{where}: `{field}` is built in — `tags` is "
                             f"open, and a vocabulary is closed")
        if field in taken:
            raise ValueError(f"{where}: `{field}` is also declared under "
                             f"`references`; a field has one declaration")
        rule = None
        if spec.get("derive") is not None:
            rule = parse_derivation(where, str(field), spec["derive"])
            if spec.get("many"):
                raise ValueError(
                    f"{where}: `derive = \"{rule.spec}\"` reads one value off "
                    f"a list, so the field holds one — drop `many`")
            if spec.get("required"):
                raise ValueError(
                    f"{where}: a derived field is present exactly when "
                    f"the fields it reads are, so `required` here would "
                    f"name the wrong line as the fix — require "
                    f"{', '.join(f'`{n}`' for n in rule.sources)} instead")
            if spec.get("default") is not None:
                raise ValueError(
                    f"{where}: `default` and `derive` are two answers to "
                    f"where the value comes from — keep one")
            rules.append(rule)
        name = spec.get("vocabulary")
        if not name:
            required = bool(spec.get("required", False))
            when = _required_when(where, spec, required)
            if when is None and not required and rule is None:
                raise ValueError(f"{where}: declares no type — `vocabulary = "
                                 f"\"NAME\"` types the field, `derive` says "
                                 f"where its value comes from, `required_when` "
                                 f"says when it applies, and a table with "
                                 f"none of them constrains nothing")
            plain.append(PlainField(field=str(field), required=required,
                                    many=bool(spec.get("many", False)),
                                    required_when=when))
            continue
        name = str(name)
        file = scheme_dir / f"{name}.yaml"
        values = declared(file)
        if not values and not (scaffolding and not file.exists()):
            # Absent is not the same as empty when a scaffold is being
            # planned: `luria init` reads the config to decide what to
            # write, and the vocabulary file is one of the things it is
            # about to write. Every other caller keeps ADR-076's eager rule.
            raise ValueError(
                f"{where}: {file.relative_to(root)} declares no values, so "
                f"the field constrains nothing")
        many = bool(spec.get("many", False))
        required = bool(spec.get("required", False))
        default = spec.get("default")
        defaults = None
        if default is not None:
            if required:
                raise ValueError(
                    f"{where}: a field with a default is never absent, so "
                    f"`required` says nothing — drop one of them")
            if many and not isinstance(default, list):
                raise ValueError(f"{where}: `many = true`, so `default` must "
                                 f"be a list")
            if not many and isinstance(default, list):
                raise ValueError(f"{where}: `default` must be one value, since "
                                 f"the field holds one (`many = true` for a "
                                 f"list)")
            defaults = tuple(str(v) for v in
                             (default if isinstance(default, list) else [default]))
            if bad := [d for d in defaults if d not in values]:
                raise ValueError(
                    f"{where}: default {', '.join(bad)} is not in "
                    f"{file.relative_to(root)} (values: {', '.join(values)})")
        found.append(Vocabulary(field=str(field), name=name, file=file,
                                many=many, required=required,
                                default=defaults,
                                required_when=_required_when(where, spec,
                                                             required)))
    return tuple(found), tuple(plain), tuple(rules)


def _fragment(spec) -> Fragment:
    if isinstance(spec, dict):
        return Fragment(Path(spec.get("file") or spec.get("target") or ""),
                        spec.get("style", "append"))
    return Fragment(Path(spec))


@dataclass(frozen=True)
class Chain:
    """A relation walked transitively and rendered as sequences (#171).

        [luria.chains.lineage]
        scheme   = "LIT"                    # whose documents are the nodes
        relation = "extends"                # the spine: A extends B, B first
        sibling  = "compared_against"        # optional: rivals off the spine
        output   = "docs/lineage.md"         # one page, a section per line
        title    = "Lines of work"

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
    like current (DP-15)."""
    name: str
    scheme: str
    # The spine, always a tuple — one relation is the common case and reads
    # as `relation = "extends"`, which is why the key stays singular: it
    # names the concept, not the count. `facet_by` takes either shape too.
    relation: tuple[str, ...]
    output: Path
    sibling: str = ""
    title: str = ""
    # A second field to show beside each step's status (#173). A record can
    # carry an axis the status cannot express — how far the *field* has
    # converged, as against what the record itself asserts — and without this
    # the page renders an agreed trunk and a disputed branch identically,
    # which is the one distinction a line of work exists to show.
    #
    # The facets a step is classified along, in render order — `status`
    # included, and named rather than assumed.
    #
    # Named for what the fields ARE rather than for what the renderer does
    # with them. They are independent axes of one document — ADR-076 calls
    # `status` and `tags` exactly that, and already writes a page per
    # vocabulary value, which is faceted browsing. A chain shows one
    # document's values along each.
    #
    # It was `annotate` first, meaning "the OTHER field" beside a hardcoded
    # status: a verb whose object was the thing it sat next to. When the
    # list became the whole content there was nothing left to annotate, and
    # the word outlived what it described.
    facet_by: tuple[str, ...] = ("status",)
    # The field a step in this chain asserts it shares with its neighbours
    # (#214). Unset means the chain asserts nothing about any field, which is
    # the default because most relations do not: `source:` joins a practice to
    # its paper across two vocabularies that were separated on purpose, and a
    # check assuming otherwise fires on every cross-domain citation a record
    # was designed to allow.
    invariant: str = ""


@dataclass(frozen=True)
class Journal:
    """Dated entries that persist, rendered into books (ADR-020).

        [luria.journals.devlog]
        dir         = "devlog.d"        # entries, partitioned yyyy/mm/dd/
        output      = "docs/devlog"     # a directory of books plus an index
        granularity = "month"           # year | month | day
        title       = "Development log"
        blurb       = "…"               # optional prose for the index

    The difference from a fragment directory is that nothing is consumed: an
    entry was true when written and stays true, so the view is *generated* from
    sources that persist rather than collected from sources that are deleted."""
    name: str
    dir: Path
    output: Path
    granularity: str = "month"
    title: str = "Journal"
    blurb: str = ""
    _root: Path = Path(".")

    @property
    def rel_dir(self) -> str:
        try:
            return str(self.dir.relative_to(self._root))
        except ValueError:
            return self.dir.name


@dataclass(frozen=True)
class Site:
    """How the record publishes as a browsable site (ADR-042).

        [luria.site]
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

        [luria.site.theme.light]
        light = "#f4f1e8"                      # any of Quartz's colour names

    `logo_dark` is only needed when the artwork can't invert itself. A logo
    whose SVG exposes a `--luria-ink` custom property — the convention this
    project's own kit uses — is re-inked to the theme automatically, and one
    that doesn't is used as it is in both modes."""
    title: str
    base_url: str
    source_url: str
    exclude: tuple[str, ...] = ()
    # Whether this record is published. `base_url` derives for every GitHub
    # project whether or not anyone deploys, so it cannot answer the question
    # on its own; this can, and it defaults to the conventional case.
    publish: bool = True
    icon: Path | None = None
    logo: Path | None = None
    logo_dark: Path | None = None
    theme: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Config:
    root: Path
    issue_url: str
    docs: Path
    decisions: Path
    design_principles: Path
    reports: Path
    fragments: dict[str, Fragment]      # fragment dir name → how it assembles
    code_globs: tuple[str, ...]
    historical: frozenset[Path]
    schemes: dict[str, Scheme]
    remotes: dict[str, Remote]
    journals: dict[str, Journal]
    chains: dict[str, Chain]
    stale_days: int
    fail_on: tuple[str, ...]            # warning classes promoted to failures
    narrow_terms: tuple[str, ...]       # this project's nouns (narrow-titles)
    network: str                        # "auto" | "never" | "require"
    # Whole records nested inside this one — directory globs, each match
    # holding its own `luria.toml` (ADR-077, relocated by ADR-078).
    #
    # This lived under `[luria.site]` for as long as publishing was the only
    # thing that needed it. It isn't a site fact: it says this project contains
    # other projects, which is what `luria index` needs in order to regenerate
    # their views and what `--check` needs in order to notice a stale one. A
    # key that `index` has to reach into the site table to read is DP-16's
    # awkwardness — a distinction the layout had stopped expressing.
    include_records: tuple[str, ...] = ()
    site: Site = None  # type: ignore[assignment]
    _raw: dict = field(default_factory=dict, repr=False)

    def nested_records(self) -> list[Path]:
        """Directories matched by `include_records` that are really records.

        One authoritative answer, because three callers need it and they must
        agree: `luria index` regenerates these, `luria index --check` compares
        them, and `luria site` mounts them. Two implementations of "which
        directories are nested records" would drift into a state where a record
        is published but never regenerated (DP-4).

        A match without a `luria.toml` is skipped rather than failed —
        `examples/*` is the natural way to write "every example", and a stray
        directory beside them should not break a build. A *pattern* matching
        nothing is an error, raised by the callers, because an include that
        silently covers no record is a section of the project quietly not
        maintained (DP-1, DP-15)."""
        out = []
        for pattern in self.include_records:
            for path in sorted(self.root.glob(pattern)):
                if path.is_dir() and (path / CONFIG_NAME).exists():
                    out.append(path)
        return out

    def unmatched_record_patterns(self) -> list[str]:
        """Patterns in `include_records` that name no record at all."""
        import fnmatch
        found = {p.relative_to(self.root).as_posix() for p in self.nested_records()}
        return [pat for pat in self.include_records
                if not any(fnmatch.fnmatch(rel, pat) for rel in found)]

    def _index_scheme(self):
        return next((s for s in self.schemes.values() if s.render == "index"),
                    None)

    @property
    def index(self) -> Path:
        s = self._index_scheme()
        return s.index_path if s else self.decisions / "README.md"

    @property
    def stub(self) -> Path:
        s = self._index_scheme()
        return s.stub if s else self.decisions / "README.stub"

    @property
    def tags_yaml(self) -> Path:
        s = self._index_scheme()
        return s.tags_yaml if s else self.decisions / "tags.yaml"

    @property
    def tag_dir(self) -> Path:
        s = self._index_scheme()
        return s.tag_dir if s else self.decisions / "tags"

    @property
    def config_doc(self) -> Path:
        """Where the generated configuration reference lands."""
        return self.docs / "configuration.md"

    @property
    def record_doc(self) -> Path:
        """Where the generated description of *this* project's record lands.

        Distinct from `config_doc` because they answer different questions and
        only one of them is about this repository: the reference is the schema
        (identical wherever Luria is installed), this page is the shape a
        particular project gave it."""
        return self.docs / "record.md"

    @property
    def owns_schema(self) -> bool:
        """True in the tree that *contains* the dataclasses the configuration
        reference is a projection of.

        The reference is generated rather than written so it cannot drift from
        `config.py` — an argument that only holds where `config.py` is a file
        the reader can open. Rendered into an adopting project it is a
        vendored copy of somebody else's schema, carrying a stamp that tells
        the reader to go edit a file they do not have, and going stale on
        their next upgrade with nothing in their repository responsible for
        it. So the page renders where its source lives, which is here (and in
        a project that vendored the package rather than installing it — for
        which the same argument holds, and the same file is present)."""
        return (self.root / "luria" / "config.py").resolve() \
            == Path(__file__).resolve()

    @property
    def remotes_lock(self) -> Path:
        """Discovered code→filename maps for the remotes, checked in.

        A lockfile rather than a live lookup: CI and an offline checkout have
        to resolve a foreign reference the same way a laptop with network does,
        and a private remote can only be read from a local clone anyway."""
        return self.root / "remotes.lock.json"

    def is_generated(self, path: Path) -> bool:
        """A view the generator owns. Rewriting one is pointless — the next
        build undoes it — so the reference fixer skips them.

        The status reports count too (#35): they *list* retired and dangling
        codes, so scanning them would report the report — every flagged code
        would gain a citation site inside the page that flags it, and the
        view could never converge."""
        if path.parent == self.reports:
            return True
        # The configuration reference (`luria index` renders it from this
        # module's own dataclasses). Generated for the usual reason — a
        # hand-written copy of a schema drifts — and flagged here for a second
        # one: the page is *made* of example codes, and `doc_refs.doc_files`
        # filters on this method, so the bare-reference lint and the fixer
        # both leave it alone.
        if path == self.config_doc:
            return True
        # The record description, generated from this config for the same two
        # reasons: a hand-written "how our record works" drifts, and the page
        # is made of example codes.
        if path == self.record_doc:
            return True
        # A chain page (#171). Generated for the usual reason, and excluded
        # here for a sharper one: its whole job is to show a line *including*
        # its retired steps, so scanning it would report every superseded
        # document in every chain as an unacknowledged citation — at a site
        # the reader must not edit, in a file the next build overwrites.
        if any(path == c.output for c in self.chains.values()):
            return True
        for s in self.schemes.values():
            if s.render == "index" and (path == s.index_path
                                        or path.parent == s.tag_dir):
                return True
            # A vocabulary's per-value pages, which render beside the tag
            # pages and are as generated as they are. Missing here for as long
            # as vocabularies have existed, and invisible until a *retired*
            # document became a vocabulary member: the reference report scans
            # what this method does not exclude, so it found a citation of a
            # superseded document inside a page nobody can annotate — an
            # `inactive-ok:` written there is erased by the next build. Worse,
            # the page is written in the same pass that renders the report, so
            # the report saw the *previous* run's copy and `luria index` stopped
            # converging.
            if s.render == "index" and any(path.parent == s.vocab_dir(v.name)
                                           for v in s.vocabularies):
                return True
            if s.output == path:
                return True
        return any(path.parent == j.output for j in self.journals.values())

    def is_template(self, path: Path) -> bool:
        """A scheme's `_template.md` — a form, not a document.

        Luria reads it to scaffold new entries, so its example codes are
        illustrative by definition: a placeholder resolves to nothing, and a
        realistic example is a real document that may not be in force. Both
        were reported against the template itself on the record that
        motivated this, which is a finding about a form nobody filed
        (ADR-061).

        Exempt from the CODE machinery only. A template's relative link
        targets are still checked, because a broken path there is copied into
        every document made from it."""
        return path.name == "_template.md" and any(
            path.parent == scheme.dir for scheme in self.schemes.values())

    def is_historical(self, path: Path) -> bool:
        """A dated record: true about the day it was written, and never
        updated to stay true. Scanning one for stale references produces
        permanent, unactionable rows, so the status report skips it.

        Three shapes qualify: a file listed in `[luria.code] historical`, an
        uncollected fragment (it is about to *become* one), and anything in a
        journal — its entries and the books they render into alike. The last
        one is why this is a method rather than the set-membership test it used
        to be: a journal's entries are nested, so `path.parent` is not the
        journal directory."""
        if path in self.historical:
            return True
        if path.parent in {self.root / d for d in self.fragments}:
            return True
        return any(j.dir in path.parents or j.output in path.parents
                   for j in self.journals.values())

    def link_base(self, path: Path) -> Path:
        """The directory a link written in `path` resolves against.

        Not always `path.parent`. A fragment is *assembled into* a file that
        lives somewhere else, so a link relative to the fragment's own directory
        breaks the moment it is collected (ADR-005). Two kinds of fragment
        qualify — a changelog/devlog fragment, and a document-rendered scheme's
        source, which is the same relationship wearing a different name."""
        for name, fragment in self.fragments.items():
            if path.parent == self.root / name:
                return (self.root / fragment.target).parent
        for scheme in self.schemes.values():
            if scheme.render == "document" and scheme.output \
                    and path.parent == scheme.dir:
                return scheme.output.parent
            # An index scheme's stub is authored beside the sources but IS the
            # view's prose, so its links resolve from where the index renders.
            # The documents themselves resolve from where they sit — they are
            # read in place, arrived at by link (ADR-021).
            if scheme.render == "index" and path == scheme.stub:
                return scheme.view
        for journal in self.journals.values():
            if journal.dir in path.parents:
                return journal.output
        return path.parent

    def rel(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.root))
        except ValueError:
            return str(path)


# The tables whose entries a project names, as opposed to the settings tables
# whose keys Luria names. The distinction decides the merge rule (ADR-047).
FAMILIES = ("schemes", "fragments", "journals", "remotes", "chains")


def load(root: Path | None = None, text: str | None = None,
         scaffolding: bool = False) -> Config:
    """The config at `root`, or parsed from `text` when given.

    `text` exists for `luria init --config`: the scaffold has to be planned
    from a config that is not on disk yet (and, under `--dry-run`, never will
    be), so the parser is reachable without a write."""
    root = root or find_root()
    raw = DEFAULTS
    config_file = root / CONFIG_NAME
    if text is None and config_file.exists():
        text = config_file.read_text(encoding="utf-8")
    if text is not None:
        parsed = tomllib.loads(text)
        parsed = parsed.get("luria", parsed)
        raw = _merge(DEFAULTS, parsed)
        # A declared family replaces the default one rather than merging into
        # it (ADR-047): its entries are named by the project, and "you get the
        # ones you wrote" is the only reading under which a family can shrink.
        for family in FAMILIES:
            if family in parsed:
                raw[family] = parsed[family]

    paths = raw["paths"]
    return Config(
        root=root,
        issue_url=raw.get("issue_url", ""),
        docs=root / paths["docs"],
        decisions=root / paths["decisions"],
        design_principles=root / paths["design_principles"],
        reports=root / paths["reports"],
        fragments={k: _fragment(v) for k, v in raw["fragments"].items()},
        code_globs=tuple(raw["code"]["globs"]),
        historical=frozenset(root / p for p in raw["code"]["historical"]),
        schemes=(schemes := _schemes(raw["schemes"], root, scaffolding)),
        remotes={
            prefix.upper(): Remote(
                prefix.upper(),
                repo=spec.get("repo", ""),
                issue_url=spec.get("issue_url", ""),
                ref=spec.get("ref", "main"),
                dir=spec.get("dir", "record/decisions.d"),
                name=spec.get("name", ""),
                url=spec.get("url", ""),
                delim=spec.get("delim", "-"),
                uid=spec.get("uid", ""),
                pin_url=spec.get("pin_url", ""),
                title_re=spec.get("title_re", ""),
                pin=bool(spec.get("pin", False)),
                uris=_fold_uris(spec, f"remotes.{prefix.upper()}"),
                schemes={
                    s.upper(): RemoteScheme(
                        s.upper(),
                        dir=sub.get("dir", ""),
                        document=sub.get("document", ""),
                        anchor=sub.get("anchor", ""),
                        url=sub.get("url", ""),
                        pin_url=sub.get("pin_url", ""),
                        pin=bool(sub.get("pin", False)),
                        uris=_fold_uris(
                            sub, f"remotes.{prefix.upper()}.schemes.{s.upper()}"),
                    )
                    for s, sub in spec.get("schemes", {}).items()
                },
            )
            for prefix, spec in raw.get("remotes", {}).items()
        },
        journals={
            name: Journal(
                name,
                dir=root / spec["dir"],
                output=root / spec["output"],
                granularity=spec.get("granularity", "month"),
                title=spec.get("title", name.title()),
                blurb=spec.get("blurb", ""),
                _root=root,
            )
            for name, spec in raw.get("journals", {}).items()
        },
        chains=_chains(raw.get("chains", {}), schemes, root),
        stale_days=int(raw.get("stale_days", 90)),
        fail_on=tuple(raw["lint"]["fail_on"]),
        narrow_terms=tuple(raw["lint"].get("narrow_terms", [])),
        network=str(raw["lint"].get("network", "auto")),
        include_records=tuple(raw.get("include_records", ())),
        site=_site(raw, root),
        _raw=raw,
    )


def _chains(raw: dict, schemes: dict, root: Path) -> dict[str, Chain]:
    """Every declared chain, checked against the schemes it walks.

    Validated here for the reason every other declaration is: a chain over a
    scheme nothing declares, or over a field that is not a reference, renders
    an empty page — and an empty page is indistinguishable from a correct
    one (DP-15)."""
    out = {}
    for name, spec in raw.items():
        where = f"luria.toml: chains.{name}"
        prefix = str(spec.get("scheme", "")).upper()
        if prefix not in schemes:
            raise ValueError(f"{where}: scheme {prefix!r} is not declared "
                             f"(have: {', '.join(sorted(schemes))})")
        declared = {r.field for r in schemes[prefix].references}
        raw_facets = spec.get("facet_by", ("status",))
        facet_by = tuple(str(f) for f in (
            [raw_facets] if isinstance(raw_facets, str) else raw_facets))
        # `status` is nameable because it is a declared vocabulary since
        # #181, arriving through `vocabularies` like any other field. Only
        # `tags` is still an axis the code assumes.
        known = ({v.field for v in schemes[prefix].vocabularies}
                 | {f.field for f in schemes[prefix].plain_fields}
                 | set(schemes[prefix].requires) | declared
                 | {"tags", "status"})
        for field in facet_by:
            if field not in known:
                raise ValueError(
                    f"{where}: `facet_by` names {field!r}, which {prefix} "
                    f"does not declare, so every step would render it blank "
                    f"(nameable: {', '.join(sorted(known))})")
        raw_spine = spec.get("relation", "")
        spine = tuple(str(f) for f in (
            [raw_spine] if isinstance(raw_spine, str) else raw_spine))
        for key, fields in (("relation", spine),
                            ("sibling", (str(spec.get("sibling", "")),))):
            for field in fields:
                if key == "sibling" and not field:
                    continue
                if field not in declared:
                    raise ValueError(
                        f"{where}: `{key}` names {field!r}, which is not a "
                        f"reference {prefix} declares — a chain over a field "
                        f"nothing types walks no edges and renders an empty "
                        f"page (declared: "
                        f"{', '.join(sorted(declared)) or 'none'})")
        if not spec.get("output"):
            raise ValueError(f"{where}: needs an `output` — the page the "
                             f"sequences render to")
        invariant = str(spec.get("invariant", ""))
        if invariant and invariant not in known:
            raise ValueError(
                f"{where}: `invariant` names {invariant!r}, which {prefix} "
                f"does not declare — a chain asserting a shared value in a "
                f"field nothing holds reports every line and means nothing "
                f"(nameable: {', '.join(sorted(known))})")
        out[name] = Chain(name=name, scheme=prefix,
                          relation=spine,
                          sibling=str(spec.get("sibling", "")),
                          output=root / str(spec["output"]),
                          facet_by=facet_by,
                          invariant=invariant,
                          title=str(spec.get("title", "")) or name.title())
    return out


# The two axes every scheme has, whatever else it declares.
BUILT_IN_CONDITION_FIELDS = ("status", "tags")


def _check_conditions(prefix: str, scheme) -> None:
    """Every `required_when` on a scheme, against what that scheme can
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
    that ground would forbid the ordinary case."""
    from .statuses import vocabulary as status_words
    from .vocabularies import declared as declared_values

    nameable = {*BUILT_IN_CONDITION_FIELDS, *scheme.requires,
                *(r.field for r in scheme.references),
                *(v.field for v in scheme.vocabularies),
                *(f.field for f in scheme.plain_fields)}
    vocab_of = {v.field: v for v in scheme.vocabularies}

    for field, when in _conditions(scheme):
        where = f"luria.toml: schemes.{prefix}.fields.{field}.required_when"
        if when.on not in nameable:
            raise ValueError(
                f"{where}: `{when.on}` is not a field {prefix} declares, so "
                f"the condition can never hold and `{field}` is never "
                f"required (nameable: {', '.join(sorted(nameable))})")
        allowed: tuple[str, ...] | None = None
        if when.on == "status":
            allowed = status_words(scheme)
        elif when.on in vocab_of:
            allowed = tuple(declared_values(vocab_of[when.on].file))
        if allowed is None:
            continue
        if bad := [v for v in when.values if v not in allowed]:
            raise ValueError(
                f"{where}: {', '.join(repr(v) for v in bad)} is not a value "
                f"`{when.on}` takes, so the condition can never hold and "
                f"`{field}` is never required "
                f"(values: {', '.join(allowed)})")


def _check_derivations(prefix: str, scheme) -> None:
    """Every `derive` against the scheme that declares it (#216).

    Two things the shape check cannot know on its own: whether the source is a
    field this scheme can hold, and whether it holds a *list*. Both are eager
    for the usual reason — a derivation off a field nothing carries resolves to
    nothing on every document, which reads exactly like a record with no
    findings.

    List-valued is the harder rule and the one worth stating: `first:` of a
    single value is that value, so a derivation off a scalar is a rename
    wearing a derivation's clothes, and renames belong in the frontmatter."""
    from .derive import lone_field
    plural = {"tags", *(v.field for v in scheme.vocabularies if v.many),
              *(r.field for r in scheme.references if r.many),
              *(f.field for f in scheme.plain_fields if f.many)}
    nameable = {*BUILT_IN_CONDITION_FIELDS, "number", *scheme.requires,
                *(r.field for r in scheme.references),
                *(v.field for v in scheme.vocabularies),
                *(f.field for f in scheme.plain_fields)}
    for rule in scheme.derived:
        where = f"luria.toml: schemes.{prefix}.fields.{rule.field}.derive"
        for name in rule.sources:
            if name not in nameable:
                raise ValueError(
                    f"{where}: `{name}` is not a field {prefix} declares, so "
                    f"`{rule.field}` resolves to nothing on every document "
                    f"(nameable: {', '.join(sorted(nameable))})")
        # The scalar-rename rule, narrowed to where it still bites. A template
        # that builds something — `"LIT-{first_author}-{number}"` — reads
        # single-valued fields legitimately. A template that is *only* a
        # single-valued field copies it under a second name, which is the
        # rename this refused before templates existed.
        if lone_field(rule.template) and rule.sources[0] not in plural:
            raise ValueError(
                f"{where}: `{rule.template}` is just `{rule.sources[0]}` under "
                f"another name — a template that reads one single-valued field "
                f"and nothing else renames a field rather than deriving one")


def _alias_template(prefix: str, raw) -> str:
    """A scheme's `alias` template, validated for shape where it is read.

    Two things are checkable without any document: that the template renders
    at all, and that it starts with this scheme's prefix. The prefix matters
    because every reference scanner in luria finds a code by its prefix
    first — a spelling that does not carry one is unreachable however well it
    resolves, which is the quiet kind of failure eager validation exists to
    prevent (#219)."""
    template = str(raw or "").strip()
    if not template:
        return ""
    where = f"luria.toml: schemes.{prefix}.alias"
    try:
        template.format_map(_Probe())
    except (ValueError, IndexError) as exc:
        raise ValueError(f"{where}: {template!r} is not a template "
                         f"`str.format` can render ({exc})") from exc
    if not template.startswith(f"{prefix}-"):
        raise ValueError(
            f"{where}: {template!r} does not start with '{prefix}-', so no "
            f"reference scanner would find it — a spelling luria cannot see "
            f"resolves for nobody")
    return template


class _Probe(dict):
    """Answers to any name, so a template's *shape* can be checked without a
    document. Indexing and attribute access have to work too, since
    `{authors[0]}` and `{date.year}` are ordinary template spellings."""

    def __missing__(self, key):
        return self

    def __getitem__(self, key):
        return self

    def __getattr__(self, name):
        return self

    def __format__(self, spec):
        return ""


def _conditions(scheme):
    """Every (field name, condition) this scheme declares, across the tables
    a condition can be written in."""
    for group in (scheme.references, scheme.vocabularies, scheme.plain_fields):
        for entry in group:
            if entry.required_when is not None:
                yield entry.field, entry.required_when


def _schemes(raw: dict, root: Path,
             scaffolding: bool = False) -> dict[str, Scheme]:
    """Every declared scheme, with the cross-scheme checks that need them all.

    A reference naming a scheme that does not exist is a config error, and it
    can only be caught once the whole family is known — so it happens here
    rather than in `_references`, which sees one table at a time."""
    schemes = {}
    for prefix, spec in raw.items():
        tags_file = root / spec["tags"] if spec.get("tags") else None
        tags_path = tags_file or root / spec["dir"] / "tags.yaml"
        schemes[prefix] = Scheme(
            prefix=prefix,
            dir=root / spec["dir"],
            active=spec.get("active", "Active"),
            successor=str(spec.get("successor", "superseded_by")),
            retires_on=str(spec.get("retires_on", "Superseded")),
            render=spec.get("render", "index"),
            output=root / spec["output"] if spec.get("output") else None,
            allocate=spec.get("allocate", "filing"),
            alias=_alias_template(prefix, spec.get("alias", "")),
            titles_generalize=bool(spec.get("titles_generalize", False)),
            requires=tuple(spec.get("requires", ())),
            tag_groups=_tag_groups(prefix, spec.get("tag_groups", {}),
                                   tags_path),
            tags_file=tags_file,
            references=(refs := _references(prefix, spec.get("references", {}))),
            **dict(zip(("vocabularies", "plain_fields", "derived"),
                       _fields(prefix, spec.get("fields", {}),
                               root / spec["dir"], root, refs,
                               scaffolding))),
            field_groups=_field_groups(prefix, spec.get("field_groups", {})),
            uniform_ok=(spec.get("uniform_ok") or None),
            uniform_share=float(spec.get("uniform_share", 1.0)),
        )
    for prefix, scheme in schemes.items():
        _check_conditions(prefix, scheme)
        _check_derivations(prefix, scheme)
        for ref in scheme.references:
            if ref.scheme not in schemes:
                raise ValueError(
                    f"luria.toml: schemes.{prefix}.references.{ref.field} "
                    f"names scheme {ref.scheme!r}, which is not declared "
                    f"(have: {', '.join(sorted(schemes))})")
    return schemes


def _site(raw: dict, root: Path) -> Site:
    """The site settings, with every unset key derived from `issue_url`.

    A non-GitHub (or absent) issue URL derives nothing: the title falls back
    to the directory name and the two URLs stay empty, which `luria site`
    reports rather than guessing at."""
    spec = raw.get("site", {})
    m = GITHUB_ISSUE_RE.match(raw.get("issue_url", "") or "")
    owner, repo = m.groups() if m else ("", "")
    return Site(
        title=spec.get("title") or repo or root.name,
        # GitHub Pages' own default for a project site. Quartz wants it
        # without the scheme.
        base_url=spec.get("base_url")
        or (f"{owner.lower()}.github.io/{repo}" if owner else ""),
        # `HEAD` rather than a branch name: one fewer projection to keep in
        # step with whatever the default branch is called (DP-3).
        source_url=spec.get("source_url")
        or (f"https://github.com/{owner}/{repo}/blob/HEAD" if owner else ""),
        exclude=tuple(spec.get("exclude", ())),
        publish=bool(spec.get("publish", True)),
        icon=root / spec["icon"] if spec.get("icon") else None,
        logo=root / spec["logo"] if spec.get("logo") else None,
        logo_dark=root / spec["logo_dark"] if spec.get("logo_dark") else None,
        theme=spec.get("theme", {}) or {},
    )


@lru_cache(maxsize=1)
def current() -> Config:
    """The config for this process. Cached because every module wants it and
    re-reading per call would make the file's mtime a source of skew."""
    return load()


def reset() -> None:
    """Drop the cache — for tests that point `LURIA_ROOT` at a fixture."""
    current.cache_clear()


@contextmanager
def rooted(root: Path):
    """Run a block with `root` as the current project, then put it back.

    `load(root)` already builds any project's config, but that is not enough
    to *operate* on one: the modules underneath — `doc_refs.link_base`,
    `edges.graph`, the renderers — call `current()` for themselves, by design,
    since threading a config through every call site would be its own kind of
    mess. So switching projects means switching the global, and the honest
    thing is to make that a bounded, restoring operation with a name rather
    than have callers set the environment variable and hope.

    Reentrant by construction: the previous value is captured and restored,
    including its absence."""
    before = os.environ.get("LURIA_ROOT")
    os.environ["LURIA_ROOT"] = str(Path(root).resolve())
    reset()
    try:
        yield current()
    finally:
        if before is None:
            os.environ.pop("LURIA_ROOT", None)
        else:
            os.environ["LURIA_ROOT"] = before
        reset()
