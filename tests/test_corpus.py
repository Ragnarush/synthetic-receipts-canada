"""No regression: regenerating the committed sample must give it back byte for byte.

A draw added on a shared path shifts every receipt after it. A new family is not yet in
`corpus/`, so it is skipped until its sample is copied there. Images depend on the installed
font and Pillow; if only images differ on another machine, compare the JSON first.
"""

import filecmp
from pathlib import Path

import pytest

from synthetic_receipts_canada import cli
from synthetic_receipts_canada.families import FAMILIES

CORPUS = Path(__file__).resolve().parent.parent / "corpus"


@pytest.fixture(scope="module")
def regenerated(tmp_path_factory):
    out = tmp_path_factory.mktemp("corpus")
    cli.main(["generate", "--family", "all", "--count", "20", "--seed", "1", "--out", str(out)])
    return out


@pytest.mark.parametrize("family", FAMILIES)
def test_corpus_unchanged(family, regenerated):
    committed = CORPUS / family
    if not committed.is_dir():
        pytest.skip(f"{family} has no committed sample yet")
    names = sorted(p.name for p in committed.iterdir())
    assert names == sorted(p.name for p in (regenerated / family).iterdir())
    json_names = [n for n in names if n.endswith(".json")]
    _, mismatch, errors = filecmp.cmpfiles(committed, regenerated / family, json_names, shallow=False)
    assert not mismatch and not errors, f"ground truth changed: {mismatch + errors}"
    _, mismatch, errors = filecmp.cmpfiles(committed, regenerated / family, names, shallow=False)
    assert not mismatch and not errors, f"images changed (font or Pillow?): {mismatch + errors}"
