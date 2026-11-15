import datetime as dt
import json
import shutil
from pathlib import Path

import pytest

from agent_wiki import cli, core, mcp_server
from agent_wiki.i18n import M, LANGUAGES, set_lang

DEMO = Path(__file__).resolve().parent.parent / "examples" / "demo-wiki"


@pytest.fixture(autouse=True)
def english():
    set_lang("en")
    yield
    set_lang("en")


@pytest.fixture()
def wiki(tmp_path, monkeypatch):
    root = tmp_path / "wiki"
    shutil.copytree(DEMO, root, ignore=shutil.ignore_patterns(".cache"))
    monkeypatch.setenv("AGENT_WIKI_STATE", str(tmp_path / "state"))
    monkeypatch.delenv("AGENT_WIKI_LANG", raising=False)
    return core.open_wiki(root)


def ids(results):
    return [r["id"] for r in results]


# ---------- search across languages ----------
@pytest.mark.parametrize("term, expected", [
    ("自动续费", "L-0003"),          # Chinese, 4 chars (trigram)
    ("迁移", "L-0003"),              # Chinese, 2 chars (LIKE fallback), title hit ranks first
    ("予約確認", "L-0004"),          # Japanese
    ("precio", "L-0002"),            # Spanish, prefix of "precios"
    ("deployer", "deploy-website"),  # French "Déployer" without the accent
    ("DÉPLOYER", "deploy-website"),  # case and accent insensitive
    ("Mitglieder", "datenbank-backup"),
    ("flare", "website"),            # substring inside "Cloudflare"
])
def test_search_multilingual(wiki, term, expected):
    res = core.search(wiki, [term])
    assert expected in ids(res)
    if term == "迁移":
        assert ids(res)[0] == "L-0003"


def test_search_and_terms(wiki):
    assert ids(core.search(wiki, ["DNS", "deploy"])) == ["L-0001"]
    assert core.search(wiki, ["DNS", "预约"]) == []


def test_search_filters(wiki):
    assert set(ids(core.search(wiki, ["deploy"], type="playbook"))) == {"deploy-website"}
    assert all(r["lang"] == "zh" for r in core.search(wiki, ["Stripe"], lang="zh"))
    assert "L-0003" in ids(core.search(wiki, ["Stripe"], project="booking-app"))


def test_snippet_marks_term(wiki):
    r = core.search(wiki, ["precios"])[0]
    assert "[precios]" in r["snippet"]


def test_index_rebuilds_when_file_changes(wiki):
    core.build(wiki)
    f = wiki.root / "lessons" / "L-0001-check-dns-before-deploy.md"
    f.write_text(f.read_text(encoding="utf-8") + "\nzebracrossing\n", encoding="utf-8")
    import os, time
    future = time.time() + 5
    os.utime(f, (future, future))
    assert ids(core.search(wiki, ["zebracrossing"])) == ["L-0001"]


# ---------- docs, links ----------
def test_get_doc_and_backlinks(wiki):
    d = core.get_doc(wiki, "L-0001")
    assert d["lang"] == "en" and "website" in d["backlinks"] and "deploy-website" in d["backlinks"]
    assert core.get_doc(wiki, "nope") is None


def test_list_and_stats(wiki):
    assert {r["id"] for r in core.list_docs(wiki, "lesson")} == {"L-0001", "L-0002", "L-0003", "L-0004"}
    s = core.stats(wiki)
    assert s["by_type"]["lesson"] == 4 and set(s["by_lang"]) >= {"en", "zh", "ja", "es", "fr", "de"}


def test_sql_is_read_only(wiki):
    cols, rows = core.run_sql(wiki, "select count(*) as n from docs")
    assert cols == ["n"] and rows[0][0] == 9
    for bad in ["delete from docs", "select 1; delete from docs", "drop table docs", "attach database 'x' as y"]:
        with pytest.raises(core.WikiError):
            core.run_sql(wiki, bad)


# ---------- check ----------
def test_check_clean(wiki):
    problems, warns, n = core.check(wiki)
    assert problems == [] and warns == [] and n == 9


def test_check_finds_problems(wiki):
    key = "sk-" + "A" * 30
    (wiki.root / "lessons" / "L-0009-bad.md").write_text(
        f"---\nid: L-0001\ntype: playbook\ntitle: Bad\nupdated: 11/11/2026\n---\n\nkey {key} see [[missing]]\n",
        encoding="utf-8")
    problems, warns, _ = core.check(wiki)
    kinds = {k for k, _ in problems}
    assert {"chk_missing", "chk_type", "chk_dup", "chk_date", "chk_secret"} <= kinds
    assert any(kw.get("ref") == "missing" for _, kw in warns)


def test_check_cli_exit_code(wiki, capsys):
    (wiki.root / "lessons" / "x.md").write_text("---\nid: x\n---\n", encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        cli.main(["check", "--root", str(wiki.root)])
    assert e.value.code == 1


# ---------- lint ----------
def test_lint(wiki):
    (wiki.root / "lessons" / "L-0005-lonely.md").write_text(
        "---\nid: L-0005\ntype: lesson\ntitle: Check which account owns the DNS zone before deploy\nstatus: active\n"
        "updated: 2026-01-01\n---\n\nThe old rule is deprecated.\n", encoding="utf-8")
    r = core.lint(wiki, today=dt.date(2026, 11, 15))
    assert "L-0005" in [d["id"] for d in r["orphans"]]
    assert "L-0005" in [d["id"] for d in r["no_out"]]
    assert any({a["id"], b["id"]} == {"L-0001", "L-0005"} for _, a, b in r["dups"])
    assert any(d["id"] == "L-0005" for d, _, _ in r["supers"])
    r2 = core.lint(wiki, today=dt.date(2027, 6, 1))
    assert "website" in [d["id"] for _, d in r2["stale"]]


def test_lint_write(wiki, capsys):
    cli.main(["lint", "--write", "--root", str(wiki.root)])
    files = list((wiki.root / "inbox").glob("lint-*.md"))
    assert len(files) == 1


# ---------- add & templates ----------
@pytest.mark.parametrize("lang, heading", [("en", "## What happened"), ("zh", "## 发生了什么"),
                                           ("ja", "## 何が起きたか"), ("de", "## Was ist passiert")])
def test_add_lesson_in_language(wiki, lang, heading):
    p = core.add_doc(wiki, "lesson", "Ein Test", project="website", tags="a,b", language=lang)
    text = p.read_text(encoding="utf-8")
    assert p.name.startswith("L-0005") and heading in text and f"lang: {lang}" in text
    assert "project: [website]" in text and "tags: [a, b]" in text


def test_add_project_needs_ascii_id(wiki):
    with pytest.raises(core.WikiError):
        core.add_doc(wiki, "project", "新项目")
    p = core.add_doc(wiki, "project", "新项目", id="new-project")
    assert p.name == "new-project.md"


def test_init(tmp_path):
    assert core.init_wiki(tmp_path / "w", "ja")
    cfg = json.loads((tmp_path / "w" / "agent-wiki.json").read_text(encoding="utf-8"))
    assert cfg["language"] == "ja" and (tmp_path / "w" / "lessons").is_dir()
    assert "Write pages in Japanese" in (tmp_path / "w" / "AGENTS.md").read_text(encoding="utf-8")
    assert (tmp_path / "w" / "CLAUDE.md").read_text(encoding="utf-8").strip() == "@AGENTS.md"
    assert not core.init_wiki(tmp_path / "w", "ja")


def test_normalize():
    assert core.normalize("Café STRASSE") == "cafe strasse"
    assert core.slugify("Déployer le site!") == "deployer-le-site"


# ---------- i18n ----------
def test_every_message_has_english_and_valid_placeholders():
    import string
    for key, entry in M.items():
        assert "en" in entry, key
        fields = {f for _, f, _, _ in string.Formatter().parse(entry["en"]) if f}
        for code, text in entry.items():
            assert code in LANGUAGES
            assert {f for _, f, _, _ in string.Formatter().parse(text) if f} == fields, (key, code)


def test_cli_output_language(wiki, capsys, monkeypatch):
    monkeypatch.setenv("AGENT_WIKI_LANG", "zh")
    cli.main(["search", "nothingmatchesthis", "--root", str(wiki.root)])
    assert "没有结果" in capsys.readouterr().out
    monkeypatch.setenv("AGENT_WIKI_LANG", "es")
    cli.main(["search", "nothingmatchesthis", "--root", str(wiki.root)])
    assert "Sin resultados" in capsys.readouterr().out


# ---------- MCP tool functions ----------
def test_mcp_search_fetch(wiki):
    res = json.loads(mcp_server.t_search(wiki, "自动续费"))["results"]
    assert res[0]["id"] == "L-0003" and res[0]["url"].startswith("wiki://")
    doc = json.loads(mcp_server.t_fetch(wiki, "L-0003"))
    assert doc["metadata"]["lang"] == "zh" and "Stripe" not in doc["title"]


def test_mcp_submit_note(wiki):
    msg = mcp_server.t_submit_note(wiki, "Nueva lección", "Contenido de prueba", "lesson", "website", agent="tester")
    files = list((wiki.root / "inbox" / "agents").glob("*.md"))
    assert len(files) == 1 and "submitted_by: tester" in files[0].read_text(encoding="utf-8")
    assert "inbox" in msg


def test_mcp_submit_note_rejects(wiki):
    assert "Rejected" in mcp_server.t_submit_note(wiki, "x", "token: " + "Z" * 20)
    assert "relative" in mcp_server.t_submit_note(wiki, "x", "y", update_path="../etc/passwd")
    assert "relative" in mcp_server.t_submit_note(wiki, "x", "y", update_path="/etc/passwd")
    assert not (wiki.root / "inbox" / "agents").exists()


def test_mcp_sql_rejects_writes(wiki):
    assert "read-only" in mcp_server.t_sql(wiki, "delete from docs")


def test_tokens(wiki, capsys):
    mcp_server.cmd_token(wiki, ["add", "claude", "read"])
    tok = capsys.readouterr().out.strip()
    info, path = mcp_server.authorize(wiki, f"/k/{tok}/mcp", {})
    assert info["role"] == "read" and path == "/mcp"
    info, _ = mcp_server.authorize(wiki, "/mcp", {b"authorization": f"Bearer {tok}".encode()})
    assert info["name"] == "claude"
    assert mcp_server.authorize(wiki, "/mcp", {b"authorization": b"Bearer wrong"})[0] is None
    stored = mcp_server.tokens_file(wiki).read_text()
    assert tok not in stored  # only the hash is stored
    mcp_server.cmd_token(wiki, ["revoke", "claude"])
    assert mcp_server.authorize(wiki, f"/k/{tok}/mcp", {})[0] is None
