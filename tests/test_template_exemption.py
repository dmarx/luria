# unresolved-ok-file: ADR-999 — an illustrative code inside a fixture's
# template body, which is the very thing this module says is not a citation
"""A scheme's `_template.md` is a form, not a document.

It exists to be copied, so its example codes are illustrative by definition —
a placeholder resolves to nothing, and a realistic example is a real document
that may not be in force. Both were reported against the template itself on
the record that motivated this, which is a finding about a form nobody filed.

Exempt from the CODE machinery only. Link targets are still checked, because
a broken path in a template is copied into every document made from it.
"""

from luria import config, ref_status
from tests._scheme import decision


def test_a_scheme_template_is_recognised(project):
    scheme = config.current().schemes["ADR"]
    scheme.dir.mkdir(parents=True, exist_ok=True)
    template = scheme.dir / "_template.md"
    template.write_text("---\nstatus: Proposed\n---\n\n# ADR-NNN: A form\n")
    assert config.current().is_template(template)


def test_an_ordinary_document_is_not_a_template(project):
    path = decision(project, 1, "Active")
    assert not config.current().is_template(path)


def test_a_template_is_left_out_of_the_reference_scan(project):
    """The whole point: an example code in a form is not a citation."""
    scheme = config.current().schemes["ADR"]
    decision(project, 1, "Rejected", title="A retired decision")
    template = scheme.dir / "_template.md"
    template.write_text(
        "---\nstatus: Proposed\n---\n\n"
        "# ADR-NNN: A form\n\nSupersede with ADR-001, and see ADR-999.\n")

    scanned = ref_status.scanned_files()
    assert template not in scanned, "the template is not a citing site"


def test_a_non_template_in_the_same_directory_is_still_scanned(project):
    decision(project, 1, "Active")
    scanned = ref_status.scanned_files()
    scheme = config.current().schemes["ADR"]
    assert scheme.dir / "ADR-001.md" in scanned
