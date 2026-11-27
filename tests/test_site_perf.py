# tests/test_site_perf.py
"""The site build's performance report: what a timed run measures.

`luria.site_perf` reads three things a timed `actions/site` run leaves behind
— a Quartz log stamped line by line, the staged vault and the built output —
and turns them into one JSON document plus a markdown table. Each reader is
tested against the shape the real tool prints, including the coarse rounding
Quartz's own summary lines use, which is why the stamps exist at all.
"""
import io
import json

from luria import site_perf


def test_stamp_prefixes_elapsed_seconds_and_strips_colour():
    ticks = iter([10.0, 10.5, 12.25])
    out = io.StringIO()
    site_perf.stamp(io.StringIO("\x1b[33mone\x1b[39m\ntwo\n"), out,
                    clock=lambda: next(ticks))
    assert out.getvalue() == "[+0.500] one\n[+2.250] two\n"


def test_duration_reads_every_unit_pretty_time_prints():
    assert site_perf.duration("744μs") == 0.000744
    assert site_perf.duration("48ms") == 0.048
    assert site_perf.duration("9s") == 9.0
    assert site_perf.duration("1m") == 60.0
    assert site_perf.duration("1m 3s") == 63.0
    assert site_perf.duration("nonsense") is None


LOG = """\
[+0.100] Found 419 input files from `content` in 48ms
[+0.300] [markdown] content/a.md -> a (12ms)
[+0.400] [markdown] content/big.md -> big (2s)
[+9.000] Parsed 419 Markdown files in 9s
[+9.100] [emit:ComponentResources] index.css
[+10.000] [emit:ContentPage] a.html
[+15.000] [emit:ContentPage] big.html
[+11.000] [emit:CustomOgImages] a-og-image.webp
[+66.000] [emit:CustomOgImages] big-og-image.webp
[+67.000] Emitted 1627 files to `public` in 58s
[+67.100] Done processing 419 files in 1m
"""


def test_parse_log_reads_the_phase_lines_quartz_always_prints():
    got = site_perf.parse_log(LOG.splitlines())
    assert got["phases"]["found"] == {"count": 419, "seconds": 0.048}
    assert got["phases"]["parsed"] == {"count": 419, "seconds": 9.0}
    assert got["phases"]["emitted"] == {"count": 1627, "seconds": 58.0}
    assert got["phases"]["done"] == {"count": 419, "seconds": 60.0}


def test_parse_log_attributes_emit_time_to_emitters_from_the_stamps():
    """Emitters after the first two run concurrently, so a span is when an
    emitter's first and last file appeared, not CPU it alone consumed — the
    report says so. The ordering is what tells you which one held the build."""
    emitters = site_perf.parse_log(LOG.splitlines())["emitters"]
    assert emitters["CustomOgImages"] == {"files": 2, "first": 11.0, "last": 66.0}
    assert emitters["ContentPage"] == {"files": 2, "first": 10.0, "last": 15.0}
    assert list(emitters)[0] == "CustomOgImages"  # slowest-finishing first


def test_parse_log_keeps_the_slowest_markdown_files():
    slow = site_perf.parse_log(LOG.splitlines())["slowest_markdown"]
    assert slow[0] == {"file": "content/big.md", "seconds": 2.0}


def test_parse_log_without_stamps_still_reads_phases():
    got = site_perf.parse_log(["Parsed 3 Markdown files in 2s"])
    assert got["phases"]["parsed"] == {"count": 3, "seconds": 2.0}
    assert got["emitters"] == {}


def test_inventory_groups_bytes_by_kind_and_names_the_heavy_files(tmp_path):
    (tmp_path / "static").mkdir()
    (tmp_path / "static" / "contentIndex.json").write_bytes(b"x" * 300)
    (tmp_path / "a.html").write_bytes(b"x" * 100)
    (tmp_path / "b.html").write_bytes(b"x" * 50)
    (tmp_path / "a-og-image.webp").write_bytes(b"x" * 40)
    (tmp_path / "demo.webp").write_bytes(b"x" * 1000)
    inv = site_perf.inventory(tmp_path, top=2)
    assert inv["files"] == 5
    assert inv["bytes"] == 1490
    assert inv["by_kind"]["html"] == {"files": 2, "bytes": 150}
    # A social card is generated per page; an image the record ships is not.
    assert inv["by_kind"]["og-image"] == {"files": 1, "bytes": 40}
    assert inv["by_kind"]["webp"] == {"files": 1, "bytes": 1000}
    assert inv["content_index_bytes"] == 300
    assert inv["largest"] == [{"path": "demo.webp", "bytes": 1000},
                              {"path": "static/contentIndex.json", "bytes": 300}]


def test_inventory_of_a_missing_directory_is_empty_not_an_error(tmp_path):
    inv = site_perf.inventory(tmp_path / "absent")
    assert inv["files"] == 0 and inv["by_kind"] == {}


def test_report_writes_json_and_a_markdown_summary(tmp_path):
    log = tmp_path / "quartz.log"
    log.write_text(LOG)
    public = tmp_path / "public"
    public.mkdir()
    (public / "a.html").write_text("hi")
    steps = tmp_path / "steps.tsv"
    steps.write_text("luria site\t4.5\nnpm ci\t6.0\nquartz build\t67.1\n")
    out = tmp_path / "perf"
    site_perf.report(log=str(log), public=str(public), staged=str(tmp_path / "none"),
                     steps=str(steps), out=str(out))
    data = json.loads((out / "site-perf.json").read_text())
    assert data["steps"] == {"luria site": 4.5, "npm ci": 6.0, "quartz build": 67.1}
    assert data["quartz"]["phases"]["emitted"]["count"] == 1627
    assert data["output"]["files"] == 1
    md = (out / "site-perf.md").read_text()
    assert "| quartz build | 67.1 |" in md
    assert "CustomOgImages" in md
