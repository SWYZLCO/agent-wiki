"""Core of agent-wiki: config, parsing, indexing, multilingual search, checks and lint.

Standard library only. Markdown files are the source of truth; the SQLite index is a disposable cache
that is rebuilt automatically whenever a source file is newer than it.
"""
from __future__ import annotations

import datetime as dt
import difflib
import json
import os
import re
import shutil
import sqlite3
import tempfile
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_NAME = "agent-wiki.json"

DEFAULT_CONFIG: dict = {
    "name": "My Wiki",
    "language": "en",
    "sections": {"company": "company", "projects": "project", "lessons": "lesson", "playbooks": "playbook"},
    "extra_sources": [],
    "required": ["id", "type", "title", "status", "updated"],
    "stale_days": {"project": 21, "playbook": 60, "company": 60},
    "lesson_prefix": "L-",
    "project_keywords": {},
    "secret_patterns": [],
    "inbox": "inbox",
    "db": ".cache/wiki.sqlite",
}

SECRET_PATTERNS: list[tuple[str, str]] = [
    (r"sk-[A-Za-z0-9_-]{20,}", "OpenAI-style API key"),
    (r"sk-ant-[A-Za-z0-9_-]{20,}", "Anthropic API key"),
    (r"(?:sk|rk|pk)_(?:live|test)_[A-Za-z0-9]{16,}", "Stripe key"),
    (r"gh[pousr]_[A-Za-z0-9]{30,}", "GitHub token"),
    (r"github_pat_[A-Za-z0-9_]{30,}", "GitHub token"),
    (r"glpat-[A-Za-z0-9_-]{20,}", "GitLab token"),
    (r"xox[abpr]-[A-Za-z0-9-]{10,}", "Slack token"),
    (r"AKIA[0-9A-Z]{16}", "AWS access key"),
    (r"AIza[0-9A-Za-z_-]{35}", "Google API key"),
    (r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}", "JWT"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "private key"),
    (r"(?i)(?:password|passwd|secret|api[_-]?key|token)\s*[:=]\s*['\"]?[^\s'\"`]{8,}", "plaintext credential"),
]

# Lines that announce they are out of date, in several languages (used by lint).
SUPERSEDE_RE = re.compile(
    r"(?i)(\bdeprecated\b|\bsuperseded\b|\bobsolete\b|\boutdated\b|no longer (?:valid|applies|true)"
    r"|已过时|过时了|已作废|作废|不再适用|已取代|被取代|弃用"
    r"|廃止|古い情報|置き換え済み|使用しない"
    r"|obsolet[oa]s?\b|reemplazad[oa]|ya no (?:aplica|es válid)"
    r"|obsolète|remplacée?\b|n'est plus (?:valable|à jour)"
    r"|veraltet|ersetzt durch|nicht mehr gültig)"
)

# Scripts written without spaces between words: matched as substrings (trigram / LIKE).
NO_SPACE_SCRIPT = re.compile(
    r"[฀-๿຀-໿က-႟ក-៿぀-ヿ㐀-䶿"
    r"一-鿿가-힯豈-﫿ｦ-ﾟ]"
)
WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


class WikiError(Exception):
    pass


# ---------- config ----------
@dataclass
class Wiki:
    root: Path
    cfg: dict = field(default_factory=dict)

    @property
    def db_path(self) -> Path:
        return Path(os.environ.get("AGENT_WIKI_DB") or (self.root / self.cfg["db"]))

    @property
    def inbox(self) -> Path:
        return self.root / self.cfg["inbox"]

    @property
    def types(self) -> list[str]:
        out = list(dict.fromkeys(list(self.cfg["sections"].values()) + [s["type"] for s in self.cfg["extra_sources"]]))
        return out

    def secret_patterns(self) -> list[tuple[str, str]]:
        return SECRET_PATTERNS + [tuple(x) for x in self.cfg.get("secret_patterns", [])]

    def rel(self, p: Path) -> str:
        try:
            return p.relative_to(self.root).as_posix()
        except ValueError:
            return str(p)


def load_config(root: Path) -> dict:
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    f = root / CONFIG_NAME
    if f.exists():
        user = json.loads(f.read_text(encoding="utf-8"))
        cfg.update(user)
    return cfg


def find_root(start: str | Path | None = None) -> Path:
    env = os.environ.get("AGENT_WIKI_ROOT")
    if start is None and env:
        start = env
    p = Path(start or Path.cwd()).resolve()
    if start is not None and (p / CONFIG_NAME).exists():
        return p
    for d in [p, *p.parents]:
        if (d / CONFIG_NAME).exists():
            return d
    raise WikiError("no_root")


def open_wiki(root: str | Path | None = None) -> Wiki:
    r = find_root(root)
    return Wiki(r, load_config(r))


def init_wiki(path: Path, language: str = "en", name: str | None = None) -> bool:
    path.mkdir(parents=True, exist_ok=True)
    f = path / CONFIG_NAME
    if f.exists():
        return False
    cfg = {"name": name or path.resolve().name, "language": language,
           "sections": DEFAULT_CONFIG["sections"], "stale_days": DEFAULT_CONFIG["stale_days"]}
    f.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for d in DEFAULT_CONFIG["sections"]:
        (path / d).mkdir(exist_ok=True)
    (path / "inbox").mkdir(exist_ok=True)
    gi = path / ".gitignore"
    if not gi.exists():
        gi.write_text(".cache/\n", encoding="utf-8")
    agents = path / "AGENTS.md"
    if not agents.exists():
        agents.write_text(AGENTS_MD.replace("{{language}}", LANGUAGE_NAMES.get(language, language)), encoding="utf-8")
    claude = path / "CLAUDE.md"
    if not claude.exists():
        claude.write_text("@AGENTS.md\n", encoding="utf-8")  # Claude Code imports AGENTS.md
    return True


LANGUAGE_NAMES = {"en": "English", "zh": "Simplified Chinese", "ja": "Japanese", "es": "Spanish",
                  "fr": "French", "de": "German"}

# Instructions for coding agents (Codex and others read AGENTS.md; Claude Code reads CLAUDE.md, which imports it).
AGENTS_MD = """# Working with this wiki

This folder is an agent-wiki: distilled, linked knowledge that people and agents maintain together.
Markdown files are the source of truth. Never write secret values here, only their names and where they are kept.

## Before you start a task
Search for what is already known, and read the pages you find:

    wiki search <a few keywords>
    wiki show <id>

## After you finish a task that produced a result or a lesson
1. Update the project page in `projects/`, or create one: `wiki add project "Title" --id short-id`
2. Record anything worth remembering as a lesson: `wiki add lesson "Title" --project <id> --tags a,b`
   Fill in what happened, what to do next time, and the evidence (links, commits, files).
3. Turn a procedure you repeated into a playbook: `wiki add playbook "Title" --project <id>`
4. Link related pages with [[id]]. When an answer changes, rewrite the old text to the current answer
   instead of appending "update" notes.
5. Run `wiki check` and fix every problem it reports before committing.

## Conventions
- Write pages in {{language}} unless the user asks otherwise; set `lang:` in the front matter.
- Keep raw material (transcripts, scraped pages, contracts) outside the wiki; link to it.
- Once a week run `wiki lint --write`, read the report in `inbox/`, and fix what it flags.
- Notes from other agents arrive in `inbox/agents/`. Review them, merge what is correct, then delete or archive them.
"""


# ---------- text helpers ----------
def normalize(s: str) -> str:
    """Case- and accent-insensitive form used for substring matching (café → cafe, Straße → strasse)."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.casefold()


def slugify(s: str) -> str:
    s = normalize(s)
    return re.sub(r"[^a-z0-9-]+", "-", s.strip()).strip("-")[:60]


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """A small YAML subset: `key: value` and `key: [a, b]`."""
    text = text.lstrip("﻿")
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        return {}, text
    text = text.replace("\r\n", "\n")
    end = text.find("\n---", 4)
    if end < 0:
        return {}, text
    meta: dict = {}
    for line in text[4:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            meta[k.strip()] = [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
        else:
            meta[k.strip()] = v.strip("'\"")
    return meta, text[end + 4:].lstrip("\n")


def as_list(v) -> list[str]:
    if v is None or v == "":
        return []
    return v if isinstance(v, list) else [x.strip() for x in str(v).split(",") if x.strip()]


def first_heading(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("#"):
            return line.lstrip("# ").strip() or fallback
    return fallback


# ---------- loading ----------
def guess_project(w: Wiki, text: str) -> str:
    t = normalize(text)
    hits: list[str] = []
    for key, pid in w.cfg.get("project_keywords", {}).items():
        if normalize(key) in t and pid not in hits:
            hits.append(pid)
    return ",".join(hits)


def load_docs(w: Wiki) -> list[dict]:
    docs: list[dict] = []
    for sub, typ in w.cfg["sections"].items():
        d = w.root / sub
        if not d.is_dir():
            continue
        for p in sorted(d.rglob("*.md")):
            meta, body = parse_frontmatter(p.read_text(encoding="utf-8"))
            docs.append({
                "id": meta.get("id") or p.stem,
                "type": meta.get("type") or typ,
                "title": meta.get("title") or first_heading(body, p.stem),
                "status": meta.get("status", ""),
                "project": ",".join(as_list(meta.get("project"))),
                "tags": ",".join(as_list(meta.get("tags"))),
                "related": ",".join(as_list(meta.get("related"))),
                "updated": meta.get("updated", ""),
                "lang": meta.get("lang", ""),
                "path": w.rel(p),
                "body": body,
                "_meta": meta,
                "_dir_type": typ,
            })
    for src in w.cfg.get("extra_sources", []):
        d = (w.root / src["dir"]).resolve()
        if not d.is_dir():
            continue
        for p in sorted(d.glob(src.get("glob", "*.md"))):
            text = p.read_text(encoding="utf-8", errors="replace")
            meta, body = parse_frontmatter(text)
            title = meta.get("title") or first_heading(body, p.stem)
            m = DATE.search(p.name)
            docs.append({
                "id": meta.get("id") or f"{src.get('prefix', '')}{p.stem}",
                "type": src["type"], "title": title[:200], "status": meta.get("status", ""),
                "project": ",".join(as_list(meta.get("project"))) or guess_project(w, p.name + " " + title),
                "tags": ",".join(as_list(meta.get("tags"))), "related": ",".join(as_list(meta.get("related"))),
                "updated": meta.get("updated") or (m.group(0) if m else ""), "lang": meta.get("lang", ""),
                "path": w.rel(p), "body": body[: int(src.get("max_chars", 50000))],
                "_meta": meta, "_dir_type": src["type"], "_extra": True,
            })
    return docs


def source_files(w: Wiki) -> list[Path]:
    files = [w.root / CONFIG_NAME, Path(__file__)]
    for sub in w.cfg["sections"]:
        files += list((w.root / sub).rglob("*.md"))
    for src in w.cfg.get("extra_sources", []):
        files += list((w.root / src["dir"]).glob(src.get("glob", "*.md")))
    return files


# ---------- index ----------
SCHEMA = """
CREATE TABLE docs(id TEXT PRIMARY KEY, type TEXT, title TEXT, status TEXT, project TEXT, tags TEXT,
  related TEXT, updated TEXT, lang TEXT, path TEXT, body TEXT, norm TEXT);
CREATE TABLE links(src TEXT, dst TEXT, rel TEXT);
CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);
"""
TOKENIZERS = {
    "words": ["unicode61 remove_diacritics 2", "unicode61"],
    "tri": ["trigram remove_diacritics 1", "trigram"],
}


def _pick_tokenizer(con: sqlite3.Connection, options: list[str]) -> str | None:
    for tok in options:
        try:
            con.execute(f"CREATE VIRTUAL TABLE temp._t USING fts5(x, tokenize='{tok}')")
            con.execute("DROP TABLE temp._t")
            return tok
        except sqlite3.OperationalError:
            continue
    return None


def open_ro(w: Wiki) -> sqlite3.Connection:
    # immutable=1 works on network drives and FUSE mounts that do not support SQLite file locks
    return sqlite3.connect(f"file:{w.db_path.as_posix()}?immutable=1", uri=True)


def build(w: Wiki) -> tuple[sqlite3.Connection, dict]:
    """Build the index in a temp dir, then copy it into place (safe on network drives)."""
    w.db_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmpname = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    tmp = Path(tmpname)
    con = sqlite3.connect(tmp)
    con.executescript(SCHEMA)
    toks = {k: _pick_tokenizer(con, v) for k, v in TOKENIZERS.items()}
    for k, tok in toks.items():
        if tok:
            con.execute(f"CREATE VIRTUAL TABLE fts_{k} USING fts5(id UNINDEXED, title, body, tags, tokenize='{tok}')")
    cols = ["id", "type", "title", "status", "project", "tags", "related", "updated", "lang", "path", "body"]
    for r in load_docs(w):
        norm = normalize(" ".join([r["title"], r["tags"], r["body"]]))
        con.execute(f"INSERT OR REPLACE INTO docs VALUES({','.join('?' * (len(cols) + 1))})",
                    [r.get(c, "") for c in cols] + [norm])
        for p in as_list(r["project"]):
            con.execute("INSERT INTO links VALUES(?,?,?)", (r["id"], p, "project"))
        for x in as_list(r["related"]):
            con.execute("INSERT INTO links VALUES(?,?,?)", (r["id"], x, "related"))
        for x in WIKILINK.findall(r["body"]):
            con.execute("INSERT INTO links VALUES(?,?,?)", (r["id"], x.strip(), "wikilink"))
        for k, tok in toks.items():
            if tok:
                con.execute(f"INSERT INTO fts_{k} VALUES(?,?,?,?)", (r["id"], r["title"], r["body"], r["tags"]))
    con.execute("INSERT INTO meta VALUES('built_at', ?)", (dt.datetime.now().isoformat(timespec="seconds"),))
    for k, tok in toks.items():
        con.execute("INSERT INTO meta VALUES(?, ?)", (f"tokenizer_{k}", tok or ""))
    con.commit()
    con.close()
    shutil.copyfile(tmp, w.db_path)
    tmp.unlink()
    ro = open_ro(w)
    counts = dict(ro.execute("SELECT type, count(*) FROM docs GROUP BY type ORDER BY type").fetchall())
    return ro, {"counts": counts, "tokenizers": toks}


def connect(w: Wiki) -> sqlite3.Connection:
    """Open the index, rebuilding it first if any source file is newer."""
    if w.db_path.exists():
        built = w.db_path.stat().st_mtime
        if all(not s.exists() or s.stat().st_mtime <= built for s in source_files(w)):
            return open_ro(w)
    return build(w)[0]


# ---------- search ----------
def _fts_quote(term: str) -> str:
    return '"' + term.replace('"', '""') + '"'


def _meta(con, key) -> str:
    r = con.execute("select value from meta where key=?", (key,)).fetchone()
    return (r[0] if r else "") or ""


def _term_hits(con: sqlite3.Connection, term: str) -> dict[str, float]:
    """Return {doc id: score} for one term. Lower score = better (FTS5 bm25 convention)."""
    nterm = normalize(term)
    hits: dict[str, float] = {}
    words, tri = _meta(con, "tokenizer_words"), _meta(con, "tokenizer_tri")
    spaced = not NO_SPACE_SCRIPT.search(term)
    if spaced and words and re.search(r"\w", term):
        # whole words with prefix matching: "deploy" finds "deployment"; accents ignored
        try:
            for i, s in con.execute("SELECT id, bm25(fts_words, 0, 4, 1, 2) FROM fts_words WHERE fts_words MATCH ?",
                                    (_fts_quote(term) + "*",)):
                hits[i] = min(hits.get(i, 0.0), s)
        except sqlite3.OperationalError:
            pass
    if tri and len(nterm) >= 3:
        # substrings in any script: 部署流程, デプロイ, "flare" inside "Cloudflare"
        try:
            for i, s in con.execute("SELECT id, bm25(fts_tri, 0, 4, 1, 2) FROM fts_tri WHERE fts_tri MATCH ?",
                                    (_fts_quote(term),)):
                hits[i] = min(hits.get(i, 0.0), s * (0.6 if spaced else 1.0))
        except sqlite3.OperationalError:
            pass
    if not hits and (len(nterm) < 3 or not tri):
        # short terms such as two-character Chinese words, or no FTS5 at all
        like = "%" + nterm.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        for i, title, norm in con.execute("SELECT id, title, norm FROM docs WHERE norm LIKE ? ESCAPE '\\'", (like,)):
            # rough relevance: a title hit counts most, then how often the term appears
            hits[i] = -(3.0 * (nterm in normalize(title)) + 0.3 * min(norm.count(nterm), 10))
    return hits


def snippet(text: str, terms: list[str], width: int = 60) -> str:
    flat = " ".join(text.split())
    nflat = normalize(flat)
    same = len(nflat) == len(flat)
    for term in terms:
        nt = normalize(term)
        i = nflat.find(nt)
        if i >= 0:
            src = flat if same else nflat
            a, b = max(0, i - width), min(len(src), i + len(nt) + width)
            return ("…" if a else "") + src[a:i] + "[" + src[i:i + len(nt)] + "]" + src[i + len(nt):b] + ("…" if b < len(src) else "")
    return flat[: width * 2] + ("…" if len(flat) > width * 2 else "")


def search(w: Wiki, terms: list[str], type: str = "", project: str = "", lang: str = "",
           limit: int = 20) -> list[dict]:
    terms = [t for t in (x.strip() for x in terms) if t]
    if not terms:
        return []
    con = connect(w)
    scores: dict[str, float] | None = None
    for term in terms:
        h = _term_hits(con, term)
        if scores is None:
            scores = h
        else:
            scores = {k: scores[k] + v for k, v in h.items() if k in scores}
        if not scores:
            return []
    out = []
    for did, score in scores.items():
        r = con.execute("select type,title,path,project,lang,updated,body,status from docs where id=?", (did,)).fetchone()
        if not r:
            continue
        if type and r[0] != type:
            continue
        if project and project not in as_list(r[3]):
            continue
        if lang and r[4] != lang:
            continue
        out.append({"id": did, "type": r[0], "title": r[1], "path": r[2], "project": r[3], "lang": r[4],
                    "updated": r[5], "status": r[7], "score": round(score, 4), "snippet": snippet(r[6], terms)})
    out.sort(key=lambda x: x["updated"], reverse=True)  # ties: newest first
    out.sort(key=lambda x: x["score"])
    return out[:limit]


def get_doc(w: Wiki, did: str) -> dict | None:
    con = connect(w)
    r = con.execute("select id,type,title,status,project,tags,related,updated,lang,path,body from docs where id=?",
                    (did,)).fetchone()
    if not r:
        return None
    keys = ["id", "type", "title", "status", "project", "tags", "related", "updated", "lang", "path", "body"]
    d = dict(zip(keys, r))
    d["backlinks"] = sorted({b for (b,) in con.execute("select src from links where dst=? and src<>?", (did, did))})
    return d


def list_docs(w: Wiki, type: str = "", project: str = "") -> list[dict]:
    con = connect(w)
    q = "select type,id,title,status,updated,project,lang from docs"
    cond, args = [], []
    if type:
        cond.append("type=?")
        args.append(type)
    if project:
        cond.append("(','||project||',') like ?")
        args.append(f"%,{project},%")
    if cond:
        q += " where " + " and ".join(cond)
    q += " order by type, updated desc, id"
    return [dict(zip(["type", "id", "title", "status", "updated", "project", "lang"], r)) for r in con.execute(q, args)]


def stats(w: Wiki) -> dict:
    con = connect(w)
    return {
        "name": w.cfg["name"],
        "by_type": dict(con.execute("select type,count(*) from docs group by type order by type")),
        "by_lang": dict(con.execute("select coalesce(nullif(lang,''),'-'),count(*) from docs group by 1 order by 2 desc")),
        "by_project": dict(con.execute(
            "select dst,count(*) from links where rel='project' group by dst order by 2 desc limit 20")),
        "recent": [dict(zip(["updated", "type", "id", "title"], r)) for r in con.execute(
            "select updated,type,id,title from docs where updated<>'' order by updated desc limit 8")],
        "built_at": _meta(con, "built_at"),
    }


READONLY_SQL = re.compile(r"^\s*(select|with|pragma\s+table_info|explain)\b", re.I)


def run_sql(w: Wiki, query: str, max_rows: int = 200) -> tuple[list[str], list[tuple]]:
    if not READONLY_SQL.match(query) or ";" in query.strip().rstrip(";"):
        raise WikiError("sql_readonly")
    con = connect(w)
    con.set_authorizer(lambda action, *a: sqlite3.SQLITE_OK if action in (
        sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION, sqlite3.SQLITE_PRAGMA,
        sqlite3.SQLITE_RECURSIVE) else sqlite3.SQLITE_DENY)
    cur = con.execute(query)
    cols = [c[0] for c in cur.description or []]
    return cols, cur.fetchmany(max_rows)


# ---------- add ----------
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


def template_text(w: Wiki, kind: str, language: str) -> str:
    own = w.root / "templates" / f"{kind}.md"
    if own.exists():
        return own.read_text(encoding="utf-8")
    for code in (language, "en"):
        f = TEMPLATE_DIR / code / f"{kind}.md"
        if f.exists():
            return f.read_text(encoding="utf-8")
    raise WikiError("no template for " + kind)


def section_for(w: Wiki, kind: str) -> str:
    for sub, typ in w.cfg["sections"].items():
        if typ == kind:
            return sub
    raise WikiError("unknown kind " + kind)


def add_doc(w: Wiki, kind: str, title: str, project: str = "", tags: str = "", id: str = "", slug: str = "",
            language: str = "") -> Path:
    folder = w.root / section_for(w, kind)
    language = language or w.cfg.get("language", "en")
    today = dt.date.today().isoformat()
    if kind == "lesson":
        pre = w.cfg.get("lesson_prefix", "L-")
        nums = [int(m.group(1)) for p in folder.glob(f"{pre}*.md") if (m := re.match(re.escape(pre) + r"(\d+)", p.name))]
        pid = id or f"{pre}{(max(nums) + 1) if nums else 1:04d}"
        s = slug or slugify(title)
        fname = f"{pid}-{s}.md" if s else f"{pid}.md"
    else:
        pid = id or slug or slugify(title)
        if not pid:
            raise WikiError("need_id")
        fname = f"{pid}.md"
    path = folder / fname
    if path.exists():
        raise WikiError("exists:" + w.rel(path))
    text = (template_text(w, kind, language).replace("{{id}}", pid).replace("{{title}}", title)
            .replace("{{date}}", today).replace("{{project}}", project)
            .replace("{{tags}}", ", ".join(as_list(tags))).replace("{{lang}}", language))
    folder.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


# ---------- check ----------
def find_secrets(w: Wiki, text: str) -> list[tuple[str, str]]:
    found = []
    for pat, label in w.secret_patterns():
        for m in re.finditer(pat, text):
            found.append((label, m.group(0)[:10]))
    return found


def check(w: Wiki) -> tuple[list[tuple], list[tuple], int]:
    """Return (problems, warnings, doc count). Each item is (message key, kwargs)."""
    problems: list[tuple] = []
    warns: list[tuple] = []
    docs = load_docs(w)
    ids: dict[str, str] = {}
    for d in docs:
        if d.get("_extra"):
            ids.setdefault(d["id"], d["path"])
            continue
        m = d["_meta"]
        for k in w.cfg["required"]:
            if not m.get(k):
                problems.append(("chk_missing", {"path": d["path"], "key": k}))
        if d["type"] != d["_dir_type"]:
            problems.append(("chk_type", {"path": d["path"], "type": d["type"], "dir": d["_dir_type"]}))
        if d["id"] in ids:
            problems.append(("chk_dup", {"path": d["path"], "id": d["id"], "other": ids[d["id"]]}))
        ids[d["id"]] = d["path"]
        if m.get("updated") and not DATE.fullmatch(m["updated"]):
            problems.append(("chk_date", {"path": d["path"]}))
    for d in docs:
        if d.get("_extra"):
            continue
        for ref in as_list(d["project"]) + as_list(d["related"]) + [x.strip() for x in WIKILINK.findall(d["body"])]:
            if ref not in ids:
                warns.append(("chk_link", {"path": d["path"], "ref": ref}))
    for sub in w.cfg["sections"]:
        for f in (w.root / sub).rglob("*.md"):
            for label, preview in find_secrets(w, f.read_text(encoding="utf-8")):
                problems.append(("chk_secret", {"path": w.rel(f), "label": label, "preview": preview}))
    return problems, warns, len(docs)


# ---------- lint ----------
def lint(w: Wiki, today: dt.date | None = None) -> dict:
    today = today or dt.date.today()
    docs = [d for d in load_docs(w) if not d.get("_extra")]
    inbound: dict[str, set] = {d["id"]: set() for d in docs}
    outbound: dict[str, set] = {}
    for d in docs:
        refs = set(as_list(d["project"]) + as_list(d["related"]) + [x.strip() for x in WIKILINK.findall(d["body"])])
        refs.discard(d["id"])
        outbound[d["id"]] = refs
        for r in refs:
            if r in inbound:
                inbound[r].add(d["id"])
    for f in [w.root / "README.md", w.root / "index.md"]:
        if f.exists():
            for r in WIKILINK.findall(f.read_text(encoding="utf-8")):
                if r.strip() in inbound:
                    inbound[r.strip()].add(f.name)
    orphans = sorted((d for d in docs if not inbound[d["id"]] and d["type"] != "company"), key=lambda d: d["id"])
    no_out = sorted((d for d in docs if d["type"] == "lesson" and not outbound[d["id"]]), key=lambda d: d["id"])
    stale = []
    for d in docs:
        lim = w.cfg.get("stale_days", {}).get(d["type"])
        if not lim or d["status"] in ("archived", "done", "closed"):
            continue
        try:
            age = (today - dt.date.fromisoformat(d["updated"])).days
        except ValueError:
            continue
        if age > lim:
            stale.append((age, d))
    dups = []
    for i, a in enumerate(docs):
        for b in docs[i + 1:]:
            if a["type"] == b["type"] and a["type"] in ("lesson", "playbook", "project"):
                r = difflib.SequenceMatcher(None, normalize(a["title"]), normalize(b["title"])).ratio()
                if r >= 0.72:
                    dups.append((r, a, b))
    supers = []
    for d in docs:
        for n, line in enumerate(d["body"].splitlines(), 1):
            if SUPERSEDE_RE.search(line):
                supers.append((d, n, line.strip()[:120]))
    return {"docs": docs, "orphans": orphans, "no_out": no_out, "stale": sorted(stale, key=lambda x: -x[0]),
            "dups": sorted(dups, key=lambda x: -x[0]), "supers": supers, "today": today}


# ---------- export ----------
def export_sql(w: Wiki) -> str:
    con = connect(w)
    lines = []
    for table in ("docs", "links", "meta"):
        cols = [c[1] for c in con.execute(f"pragma table_info({table})")]
        lines.append(f"CREATE TABLE IF NOT EXISTS {table}({', '.join(cols)});")
        for row in con.execute(f"select * from {table}"):
            vals = ", ".join("NULL" if v is None else str(v) if isinstance(v, (int, float))
                             else "'" + str(v).replace("'", "''") + "'" for v in row)
            lines.append(f"INSERT INTO {table} VALUES({vals});")
    return "\n".join(lines) + "\n"
