"""agent-wiki command line.

  wiki init [DIR] [--lang en|zh|ja|es|fr|de] [--name NAME]   create a new wiki
  wiki build                                                rebuild the index (normally automatic)
  wiki search TERM [TERM...] [--type T] [--project P] [--lang L] [--limit N] [--json]
  wiki list [TYPE] [--project P] [--json]
  wiki show ID [--json]
  wiki add lesson|project|playbook "Title" [--project P] [--tags a,b] [--id ID] [--slug name] [--lang L]
  wiki check                                                front matter, links, secret scan (exit 1 on problems)
  wiki lint [--write]                                       weekly health check (orphans, stale, duplicates...)
  wiki stats [--json]
  wiki sql "SELECT ..."                                     read-only SQL over the index
  wiki export-sql OUT.sql                                   dump the index as SQL (e.g. for Cloudflare D1)
  wiki mcp stdio | http [--port 8790] | token add NAME read|write | token list | token revoke NAME

Global options: --root DIR (or AGENT_WIKI_ROOT). Output language: AGENT_WIKI_LANG or the wiki's `language`.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

from . import __version__, core
from .i18n import LANGUAGES, set_lang, t

FLAGS = {"--json", "--write"}


def parse(argv: list[str]) -> tuple[list[str], dict]:
    pos, opts = [], {}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in FLAGS:
            opts[a[2:]] = True
        elif a.startswith("--") and i + 1 < len(argv):
            opts[a[2:]] = argv[i + 1]
            i += 1
        else:
            pos.append(a)
        i += 1
    return pos, opts


def out_json(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def fail(key: str, code: int = 2, **kw) -> None:
    print(t(key, **kw), file=sys.stderr)
    sys.exit(code)


def wiki_error(e: core.WikiError) -> None:
    msg = str(e)
    if msg.startswith("exists:"):
        fail("exists", path=msg.split(":", 1)[1])
    if msg in ("no_root", "need_id", "sql_readonly"):
        fail(msg)
    print(msg, file=sys.stderr)
    sys.exit(2)


def cmd_init(pos, opts):
    path = Path(pos[0] if pos else ".").resolve()
    lang = opts.get("lang", "en")
    if lang not in LANGUAGES:
        lang = "en"
    set_lang(lang)
    if core.init_wiki(path, lang, opts.get("name")):
        print(t("init_done", path=path, lang=lang))
    else:
        print(t("init_exists", path=path))


def cmd_build(w, pos, opts):
    _, info = core.build(w)
    counts = ", ".join(f"{k} {v}" for k, v in info["counts"].items()) or "0"
    tok = ", ".join(f"{k}={v or '-'}" for k, v in info["tokenizers"].items())
    print(t("built", counts=counts, tok=tok))


def cmd_search(w, pos, opts):
    if not pos:
        fail("usage_search")
    res = core.search(w, pos, opts.get("type", ""), opts.get("project", ""), opts.get("lang", ""),
                      int(opts.get("limit", 20)))
    if opts.get("json"):
        return out_json(res)
    if not res:
        print(t("no_results"))
        return
    for r in res:
        extra = f" · {r['lang']}" if r["lang"] else ""
        print(f"[{r['type']}] {r['id']} · {r['title']}{extra}\n    {r['path']}\n    {r['snippet']}")


def cmd_list(w, pos, opts):
    typ = pos[0] if pos else ""
    if typ and typ not in w.types:
        fail("list_bad_type", types=", ".join(w.types))
    rows = core.list_docs(w, typ, opts.get("project", ""))
    if opts.get("json"):
        return out_json(rows)
    for r in rows:
        print(f"[{r['type']}] {r['id']} · {r['title']}" + (f" · {r['status']}" if r["status"] else "")
              + (f" · {r['updated']}" if r["updated"] else ""))


def cmd_show(w, pos, opts):
    if not pos:
        fail("usage_show")
    d = core.get_doc(w, pos[0])
    if not d:
        fail("not_found", code=1)
    if opts.get("json"):
        return out_json(d)
    dash = lambda v: v or "-"  # noqa: E731
    print(f"# {d['title']}\n" + t("show_meta", type=d["type"], status=dash(d["status"]), project=dash(d["project"]),
                                  tags=dash(d["tags"]), updated=dash(d["updated"]), lang=dash(d["lang"])))
    print(f"{t('file')} {d['path']}\n")
    print(d["body"])
    if d["backlinks"]:
        print("\n" + t("backlinks") + ", ".join(d["backlinks"]))


def cmd_add(w, pos, opts):
    kinds = [k for k in ("lesson", "project", "playbook") if k in w.cfg["sections"].values()]
    if len(pos) < 2 or pos[0] not in kinds:
        fail("usage_add", kinds="|".join(kinds))
    p = core.add_doc(w, pos[0], pos[1], opts.get("project", ""), opts.get("tags", ""), opts.get("id", ""),
                     opts.get("slug", ""), opts.get("lang", ""))
    core_id = core.parse_frontmatter(p.read_text(encoding="utf-8"))[0].get("id", p.stem)
    print(t("added", path=w.rel(p), id=core_id))


def cmd_check(w, pos, opts):
    problems, warns, n = core.check(w)
    for key, kw in problems:
        print("✗ " + t(key, **kw))
    for key, kw in warns:
        print("! " + t(key, **kw))
    print(t("chk_done", docs=n, problems=len(problems), warns=len(warns)))
    if problems:
        sys.exit(1)


def lint_report(w, r) -> str:
    out = [f"# {t('lint_title', date=r['today'].isoformat())}", "",
           t("lint_summary", docs=len(r["docs"]), orphans=len(r["orphans"]), stale=len(r["stale"]),
             dups=len(r["dups"]), noout=len(r["no_out"]), supers=len(r["supers"])), "", t("lint_howto"), ""]

    def sec(key, rows):
        out.extend([f"## {t(key)} ({len(rows)})", ""] + (rows or ["- " + t("none")]) + [""])

    sec("lint_orphans", [f"- `{d['id']}` {d['title']} — {d['path']}" for d in r["orphans"]])
    sec("lint_stale", [f"- `{d['id']}` {t('lint_days', n=age)} — {d['title']}" for age, d in r["stale"]])
    sec("lint_dups", [f"- `{a['id']}` ↔ `{b['id']}` ({s:.2f}) {a['title']} / {b['title']}" for s, a, b in r["dups"]])
    sec("lint_noout", [f"- `{d['id']}` {d['title']}" for d in r["no_out"]])
    sec("lint_supers", [f"- `{d['id']}` {t('lint_line', n=n)}: {line}" for d, n, line in r["supers"]])
    return "\n".join(out) + "\n"


def cmd_lint(w, pos, opts):
    r = core.lint(w)
    text = lint_report(w, r)
    if opts.get("write"):
        f = w.inbox / f"lint-{r['today'].isoformat()}.md"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8")
        print(t("written", path=w.rel(f)))
        print(text.splitlines()[2])
    else:
        print(text)


def cmd_stats(w, pos, opts):
    s = core.stats(w)
    if opts.get("json"):
        return out_json(s)
    fmt = lambda d: ", ".join(f"{k} {v}" for k, v in d.items()) or "-"  # noqa: E731
    print(f"{s['name']}")
    print(t("stats_docs") + fmt(s["by_type"]))
    print(t("stats_langs") + fmt(s["by_lang"]))
    print(t("stats_projects") + fmt(s["by_project"]))
    print(t("stats_recent"))
    for r in s["recent"]:
        print(f"  {r['updated']} · {r['type']} · {r['id']} · {r['title']}")


def cmd_sql(w, pos, opts):
    if not pos:
        fail("sql_readonly")
    cols, rows = core.run_sql(w, " ".join(pos))
    print("\t".join(cols))
    for r in rows:
        print("\t".join("" if v is None else str(v) for v in r))


def cmd_export(w, pos, opts):
    if not pos:
        print("Usage: wiki export-sql OUT.sql", file=sys.stderr)
        sys.exit(2)
    Path(pos[0]).write_text(core.export_sql(w), encoding="utf-8")
    print(t("written", path=pos[0]))


def cmd_mcp(w, pos, opts):
    from . import mcp_server
    mcp_server.main(w, pos, opts)


COMMANDS = {"build": cmd_build, "search": cmd_search, "list": cmd_list, "show": cmd_show, "add": cmd_add,
            "check": cmd_check, "lint": cmd_lint, "stats": cmd_stats, "sql": cmd_sql, "export-sql": cmd_export,
            "mcp": cmd_mcp}


def main(argv: list[str] | None = None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)
    root = None
    if "--root" in argv:  # global option, allowed before or after the command
        i = argv.index("--root")
        root = argv[i + 1] if i + 1 < len(argv) else None
        del argv[i:i + 2]
    set_lang(None)
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return
    if argv[0] in ("-V", "--version", "version"):
        print(f"agent-wiki {__version__}")
        return
    cmd, rest = argv[0], argv[1:]
    pos, opts = parse(rest)
    if cmd == "init":
        return cmd_init(pos, opts)
    fn = COMMANDS.get(cmd)
    if not fn:
        fail("unknown_cmd", cmd=cmd)
    try:
        w = core.open_wiki(root)
        set_lang(w.cfg.get("language"))
        fn(w, pos, opts)
    except core.WikiError as e:
        wiki_error(e)
    except BrokenPipeError:
        pass


if __name__ == "__main__":
    main()
