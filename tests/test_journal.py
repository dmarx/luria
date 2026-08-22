import datetime as dt
from pathlib import Path
import pytest
from luria import journal
from luria.config import Journal, current
REPO = Path(__file__).resolve().parents[1]

def jrnl(tmp_path: Path, granularity: str='month') -> Journal:
    return Journal('devlog', dir=tmp_path / 'devlog.d', output=tmp_path / 'docs' / 'devlog', granularity=granularity, title='Development log', _root=tmp_path)

def file_entry(j: Journal, stamp: str, title: str, body: str='Body.', tags: list[str] | None=None) -> Path:
    created = dt.datetime.fromisoformat(stamp)
    path = journal.path_for(j, created)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\ntitle: {title!r}\ncreated: '{created.isoformat()}'\ntags: {tags or []}\n---\n\n{body}\n")
    return path

def test_path_is_derived_from_the_timestamp(tmp_path):
    j = jrnl(tmp_path)
    created = dt.datetime(2026, 8, 3, 21, 19, 26)
    assert journal.path_for(j, created) == j.dir / '2026/08/03/211926.md'

def test_path_and_created_round_trip(tmp_path):
    j = jrnl(tmp_path)
    created = dt.datetime(2026, 1, 9, 4, 5, 6)
    assert journal.created_from_path(journal.path_for(j, created)) == created

@pytest.mark.parametrize('raw,want', [('2026-08-03T21:19:26', dt.datetime(2026, 8, 3, 21, 19, 26)), (dt.datetime(2026, 8, 3, 21, 19, 26), dt.datetime(2026, 8, 3, 21, 19, 26)), (dt.date(2026, 8, 3), dt.datetime(2026, 8, 3)), ('not a date', None), (None, None)])
def test_created_accepts_what_yaml_hands_back(raw, want):
    assert journal.parse_created(raw) == want

def test_new_steps_forward_on_a_collision(tmp_path):
    j = jrnl(tmp_path)
    now = dt.datetime(2026, 8, 3, 21, 19, 26)
    first = journal.new(j, 'One', now)
    second = journal.new(j, 'Two', now)
    assert first.name == '211926.md'
    assert second.name == '211927.md'

def test_new_writes_frontmatter_the_lint_accepts(tmp_path):
    j = jrnl(tmp_path)
    path = journal.new(j, 'A title', dt.datetime(2026, 8, 3, 21, 19, 26))
    entry = journal.read(path)
    assert entry.title == 'A title'
    assert journal.path_for(j, entry.created) == path

def test_entries_sort_by_time_not_by_filesystem_order(tmp_path):
    j = jrnl(tmp_path)
    file_entry(j, '2026-09-01T09:00:00', 'September')
    file_entry(j, '2026-08-03T21:19:26', 'August, later')
    file_entry(j, '2026-08-03T08:00:00', 'August, earlier')
    assert [e.title for e in journal.entries(j)] == ['August, earlier', 'August, later', 'September']

def test_the_template_is_not_an_entry(tmp_path):
    j = jrnl(tmp_path)
    j.dir.mkdir(parents=True)
    (j.dir / '_template.md').write_text("---\ntitle: 'x'\n---\n\nShape.\n")
    file_entry(j, '2026-08-03T21:19:26', 'Real')
    assert [e.title for e in journal.entries(j)] == ['Real']

@pytest.mark.parametrize('granularity,keys', [('day', ['2026-08-03', '2026-08-04']), ('month', ['2026-08']), ('year', ['2026'])])
def test_granularity_decides_the_partition(tmp_path, granularity, keys):
    j = jrnl(tmp_path, granularity)
    file_entry(j, '2026-08-03T21:19:26', 'One')
    file_entry(j, '2026-08-04T03:27:11', 'Two')
    assert sorted(journal.books(j)) == keys

def test_book_lists_its_contents(tmp_path):
    j = jrnl(tmp_path)
    file_entry(j, '2026-08-03T21:19:26', 'The first thing')
    file_entry(j, '2026-08-04T03:27:11', 'The second thing')
    book = journal.render_book(j, '2026-08', journal.books(j)['2026-08'])
    assert '# Development log — August 2026' in book
    assert '- [3 Aug 21:19 — The first thing](#20260803211926)' in book
    assert '- [4 Aug 03:27 — The second thing](#20260804032711)' in book
    for anchor in ('20260803211926', '20260804032711'):
        assert f'<a name="{anchor}"></a>' in book

def test_anchor_is_the_timestamp_not_the_title(tmp_path):
    j = jrnl(tmp_path)
    file_entry(j, '2026-08-03T21:19:26', 'Before')
    before = journal.entries(j)[0].anchor
    file_entry(j, '2026-08-03T21:19:26', 'After — retitled')
    assert journal.entries(j)[0].anchor == before

def test_tags_are_shown_when_present(tmp_path):
    j = jrnl(tmp_path)
    file_entry(j, '2026-08-03T21:19:26', 'Tagged', tags=['lint', 'record'])
    book = journal.render_book(j, '2026-08', journal.books(j)['2026-08'])
    assert '*2026-08-03 21:19:26 · lint · record*' in book

def test_index_lists_books_newest_first(tmp_path):
    j = jrnl(tmp_path)
    file_entry(j, '2026-07-01T09:00:00', 'July')
    file_entry(j, '2026-08-03T21:19:26', 'August')
    index = journal.render_index(j, journal.books(j))
    assert index.index('[2026-08]') < index.index('[2026-07]')
    assert '2 entries across 2 books' in index

def test_a_single_book_reads_as_one(tmp_path):
    j = jrnl(tmp_path)
    file_entry(j, '2026-08-03T21:19:26', 'Only')
    assert '1 entry across 1 book,' in journal.render_index(j, journal.books(j))

def test_this_repos_journal_is_filed_correctly():
    cfg = current()
    assert cfg.journals, 'this repo configures a devlog journal'
    for j in cfg.journals.values():
        filed = journal.entries(j)
        assert filed
        for entry in filed:
            assert journal.path_for(j, entry.created) == entry.path
            assert entry.title

def test_entries_are_never_consumed():
    cfg = current()
    j = next(iter(cfg.journals.values()))
    before = {p for p in j.dir.rglob('*.md')}
    journal.outputs()
    assert {p for p in j.dir.rglob('*.md')} == before

def test_an_unused_journal_renders_nothing(tmp_path, monkeypatch):
    (tmp_path / 'luria.toml').write_text('[luria]\nissue_url = ""\n')
    monkeypatch.setenv('LURIA_ROOT', str(tmp_path))
    from luria import config as config_mod
    config_mod.reset()
    assert current().journals
    assert journal.outputs() == {}
    config_mod.reset()

def test_index_inlines_the_current_book(tmp_path):
    j = jrnl(tmp_path)
    file_entry(j, '2026-07-01T09:00:00', 'Old month')
    file_entry(j, '2026-08-03T21:19:26', 'Recent')
    file_entry(j, '2026-08-04T03:27:11', 'Newest')
    index = journal.render_index(j, journal.books(j))
    assert '## Currently — [August 2026](2026-08.md)' in index
    assert '- [4 Aug 03:27 — Newest](2026-08.md#20260804032711)' in index
    assert index.index('Newest') < index.index('Recent')
    assert 'Old month' not in index and '[2026-07](2026-07.md)' in index

def test_populate_created_fills_a_missing_field(tmp_path):
    j = jrnl(tmp_path)
    path = j.dir / '2026/08/03/211926.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\ntitle: 'Hand-filed'\ntags: []\n---\n\nBody.\n")
    assert journal.populate_created(j) == [path]
    assert "created: '2026-08-03T21:19:26'" in path.read_text()
    assert journal.read(path).title == 'Hand-filed', 'the rest is untouched'
    assert journal.populate_created(j) == [], 'populating twice is a no-op'

def test_populate_created_refills_an_empty_field(tmp_path):
    j = jrnl(tmp_path)
    path = j.dir / '2026/08/03/211926.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\ntitle: 'Hand-filed'\ncreated:\ntags: []\n---\n\nBody.\n")
    assert journal.populate_created(j) == [path]
    text = path.read_text()
    assert "created: '2026-08-03T21:19:26'" in text
    assert text.count('created:') == 1, 'refilled, not duplicated'

def test_populate_created_respects_a_filed_value(tmp_path):
    j = jrnl(tmp_path)
    path = j.dir / '2026/08/03/211926.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    original = "---\ntitle: 'Moved?'\ncreated: '2026-08-04T03:27:11'\ntags: []\n---\n\nBody.\n"
    path.write_text(original)
    assert journal.populate_created(j) == []
    assert path.read_text() == original

def test_populate_created_skips_a_path_that_implies_nothing(tmp_path):
    j = jrnl(tmp_path)
    path = j.dir / 'notes.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    original = "---\ntitle: 'Loose notes'\n---\n\nBody.\n"
    path.write_text(original)
    assert journal.populate_created(j) == []
    assert path.read_text() == original

def test_populate_created_writes_frontmatter_where_there_is_none(tmp_path):
    j = jrnl(tmp_path)
    path = j.dir / '2026/08/03/211926.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('Just a body, filed by hand.\n')
    assert journal.populate_created(j) == [path]
    entry = journal.read(path)
    assert entry.created == dt.datetime(2026, 8, 3, 21, 19, 26)
    assert entry.body == 'Just a body, filed by hand.'
