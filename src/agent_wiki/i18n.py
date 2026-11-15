"""User-facing messages in several languages.

Language is chosen from (first match): the AGENT_WIKI_LANG environment variable, the wiki's
`language` setting, then English. Missing translations fall back to English, so adding a language
only needs the keys you translate. Contributions of new languages are welcome.
"""
from __future__ import annotations

import os

LANGUAGES = ("en", "zh", "ja", "es", "fr", "de")

M: dict[str, dict[str, str]] = {
    "no_root": {
        "en": "No wiki found. Run `wiki init` in an empty folder, or pass --root / set AGENT_WIKI_ROOT.",
        "zh": "没找到知识库。在空文件夹里运行 `wiki init`，或用 --root / 环境变量 AGENT_WIKI_ROOT 指定。",
        "ja": "Wiki が見つかりません。空のフォルダで `wiki init` を実行するか、--root または AGENT_WIKI_ROOT を指定してください。",
        "es": "No se encontró ninguna wiki. Ejecuta `wiki init` en una carpeta vacía o usa --root / AGENT_WIKI_ROOT.",
        "fr": "Aucun wiki trouvé. Lancez `wiki init` dans un dossier vide, ou utilisez --root / AGENT_WIKI_ROOT.",
        "de": "Kein Wiki gefunden. Führe `wiki init` in einem leeren Ordner aus oder nutze --root / AGENT_WIKI_ROOT.",
    },
    "init_done": {
        "en": "Created a new wiki in {path} (language: {lang}). AGENTS.md and CLAUDE.md tell your coding agent how to use it. Next: wiki add lesson \"Your first lesson\"",
        "zh": "已在 {path} 新建知识库（语言：{lang}）。AGENTS.md 和 CLAUDE.md 会告诉你的编程 agent 怎么用它。下一步：wiki add lesson \"第一条经验\" --slug first-lesson",
        "ja": "{path} に新しい Wiki を作成しました（言語: {lang}）。AGENTS.md と CLAUDE.md がコーディングエージェントに使い方を伝えます。次は: wiki add lesson \"最初の教訓\" --slug first-lesson",
        "es": "Wiki creada en {path} (idioma: {lang}). AGENTS.md y CLAUDE.md le explican a tu agente cómo usarla. Siguiente: wiki add lesson \"Tu primera lección\"",
        "fr": "Wiki créé dans {path} (langue : {lang}). AGENTS.md et CLAUDE.md expliquent à votre agent comment l'utiliser. Ensuite : wiki add lesson \"Votre première leçon\"",
        "de": "Neues Wiki in {path} angelegt (Sprache: {lang}). AGENTS.md und CLAUDE.md erklären deinem Agenten, wie er es nutzt. Weiter: wiki add lesson \"Deine erste Lektion\"",
    },
    "init_exists": {
        "en": "{path} already has an agent-wiki.json; nothing changed.",
        "zh": "{path} 已经有 agent-wiki.json，未做改动。",
        "ja": "{path} にはすでに agent-wiki.json があります。変更していません。",
        "es": "{path} ya tiene un agent-wiki.json; no se cambió nada.",
        "fr": "{path} contient déjà un agent-wiki.json ; rien n'a été modifié.",
        "de": "{path} hat bereits eine agent-wiki.json; nichts geändert.",
    },
    "built": {
        "en": "Index built: {counts} (tokenizers: {tok})",
        "zh": "已建索引：{counts}（分词器：{tok}）",
        "ja": "インデックスを作成しました: {counts}（トークナイザ: {tok}）",
        "es": "Índice creado: {counts} (tokenizadores: {tok})",
        "fr": "Index construit : {counts} (tokenizers : {tok})",
        "de": "Index erstellt: {counts} (Tokenizer: {tok})",
    },
    "usage_search": {
        "en": "Usage: wiki search <term> [term...] [--type T] [--project P] [--lang L] [--limit N] [--json]",
        "zh": "用法：wiki search 关键词 [关键词...] [--type 类型] [--project 项目] [--lang 语言] [--limit N] [--json]",
        "ja": "使い方: wiki search <語> [語...] [--type T] [--project P] [--lang L] [--limit N] [--json]",
        "es": "Uso: wiki search <término> [término...] [--type T] [--project P] [--lang L] [--limit N] [--json]",
        "fr": "Usage : wiki search <terme> [terme...] [--type T] [--project P] [--lang L] [--limit N] [--json]",
        "de": "Aufruf: wiki search <Begriff> [Begriff...] [--type T] [--project P] [--lang L] [--limit N] [--json]",
    },
    "no_results": {
        "en": "No results.", "zh": "没有结果。", "ja": "結果はありません。", "es": "Sin resultados.",
        "fr": "Aucun résultat.", "de": "Keine Treffer.",
    },
    "usage_show": {
        "en": "Usage: wiki show <id>", "zh": "用法：wiki show <id>", "ja": "使い方: wiki show <id>",
        "es": "Uso: wiki show <id>", "fr": "Usage : wiki show <id>", "de": "Aufruf: wiki show <id>",
    },
    "not_found": {
        "en": "Not found. Use `wiki search` to find the id.",
        "zh": "找不到这条。先用 `wiki search` 找 id。",
        "ja": "見つかりません。`wiki search` で id を探してください。",
        "es": "No encontrado. Usa `wiki search` para encontrar el id.",
        "fr": "Introuvable. Utilisez `wiki search` pour trouver l'id.",
        "de": "Nicht gefunden. Suche die id mit `wiki search`.",
    },
    "show_meta": {
        "en": "type {type} · status {status} · project {project} · tags {tags} · updated {updated} · lang {lang}",
        "zh": "类型 {type} · 状态 {status} · 项目 {project} · 标签 {tags} · 更新 {updated} · 语言 {lang}",
        "ja": "種類 {type} · 状態 {status} · プロジェクト {project} · タグ {tags} · 更新 {updated} · 言語 {lang}",
        "es": "tipo {type} · estado {status} · proyecto {project} · etiquetas {tags} · actualizado {updated} · idioma {lang}",
        "fr": "type {type} · statut {status} · projet {project} · tags {tags} · mis à jour {updated} · langue {lang}",
        "de": "Typ {type} · Status {status} · Projekt {project} · Tags {tags} · aktualisiert {updated} · Sprache {lang}",
    },
    "file": {"en": "file", "zh": "文件", "ja": "ファイル", "es": "archivo", "fr": "fichier", "de": "Datei"},
    "backlinks": {
        "en": "Linked from: ", "zh": "被引用：", "ja": "被リンク: ", "es": "Enlazado desde: ",
        "fr": "Lié depuis : ", "de": "Verlinkt von: ",
    },
    "list_bad_type": {
        "en": "Type must be one of: {types}", "zh": "类型只能是：{types}", "ja": "種類は次のいずれか: {types}",
        "es": "El tipo debe ser uno de: {types}", "fr": "Le type doit être l'un de : {types}",
        "de": "Typ muss einer von diesen sein: {types}",
    },
    "usage_add": {
        "en": "Usage: wiki add <{kinds}> \"Title\" [--project P] [--tags a,b] [--id ID] [--slug file-name] [--lang L]",
        "zh": "用法：wiki add <{kinds}> \"标题\" [--project 项目] [--tags a,b] [--id ID] [--slug 英文文件名] [--lang 语言]",
        "ja": "使い方: wiki add <{kinds}> \"タイトル\" [--project P] [--tags a,b] [--id ID] [--slug file-name] [--lang L]",
        "es": "Uso: wiki add <{kinds}> \"Título\" [--project P] [--tags a,b] [--id ID] [--slug nombre] [--lang L]",
        "fr": "Usage : wiki add <{kinds}> \"Titre\" [--project P] [--tags a,b] [--id ID] [--slug nom] [--lang L]",
        "de": "Aufruf: wiki add <{kinds}> \"Titel\" [--project P] [--tags a,b] [--id ID] [--slug name] [--lang L]",
    },
    "need_id": {
        "en": "Could not make an ASCII id from this title. Pass --id, e.g. --id new-project",
        "zh": "标题无法生成英文 id，请用 --id 指定，例如 --id new-project",
        "ja": "このタイトルから ASCII の id を作れません。--id を指定してください（例: --id new-project）",
        "es": "No se pudo crear un id ASCII con este título. Usa --id, p. ej. --id nuevo-proyecto",
        "fr": "Impossible de créer un id ASCII à partir de ce titre. Utilisez --id, p. ex. --id nouveau-projet",
        "de": "Aus diesem Titel lässt sich keine ASCII-id bilden. Nutze --id, z. B. --id neues-projekt",
    },
    "exists": {
        "en": "Already exists: {path}", "zh": "已存在：{path}", "ja": "すでに存在します: {path}",
        "es": "Ya existe: {path}", "fr": "Existe déjà : {path}", "de": "Existiert bereits: {path}",
    },
    "added": {
        "en": "Created {path} (id {id}). Fill in the body, then run `wiki check`.",
        "zh": "已新建 {path}（id {id}），填好正文后运行 `wiki check`。",
        "ja": "{path} を作成しました（id {id}）。本文を書いたら `wiki check` を実行してください。",
        "es": "Creado {path} (id {id}). Completa el contenido y ejecuta `wiki check`.",
        "fr": "Créé {path} (id {id}). Rédigez le contenu puis lancez `wiki check`.",
        "de": "{path} angelegt (id {id}). Inhalt ausfüllen, dann `wiki check` ausführen.",
    },
    "chk_missing": {
        "en": "{path}: missing `{key}`", "zh": "{path}：缺少 `{key}`", "ja": "{path}: `{key}` がありません",
        "es": "{path}: falta `{key}`", "fr": "{path} : `{key}` manquant", "de": "{path}: `{key}` fehlt",
    },
    "chk_type": {
        "en": "{path}: type={type} does not match its folder ({dir})",
        "zh": "{path}：type={type} 与所在目录（{dir}）不符",
        "ja": "{path}: type={type} がフォルダ（{dir}）と一致しません",
        "es": "{path}: type={type} no coincide con su carpeta ({dir})",
        "fr": "{path} : type={type} ne correspond pas à son dossier ({dir})",
        "de": "{path}: type={type} passt nicht zum Ordner ({dir})",
    },
    "chk_dup": {
        "en": "{path}: id {id} duplicates {other}", "zh": "{path}：id {id} 与 {other} 重复",
        "ja": "{path}: id {id} が {other} と重複しています", "es": "{path}: el id {id} duplica {other}",
        "fr": "{path} : l'id {id} fait doublon avec {other}", "de": "{path}: id {id} doppelt mit {other}",
    },
    "chk_date": {
        "en": "{path}: `updated` must be YYYY-MM-DD", "zh": "{path}：`updated` 应为 YYYY-MM-DD",
        "ja": "{path}: `updated` は YYYY-MM-DD 形式にしてください", "es": "{path}: `updated` debe ser AAAA-MM-DD",
        "fr": "{path} : `updated` doit être AAAA-MM-JJ", "de": "{path}: `updated` muss JJJJ-MM-TT sein",
    },
    "chk_link": {
        "en": "{path}: links to unknown id {ref}", "zh": "{path}：引用了不存在的 {ref}",
        "ja": "{path}: 存在しない id {ref} へのリンク", "es": "{path}: enlaza a un id inexistente {ref}",
        "fr": "{path} : lien vers un id inconnu {ref}", "de": "{path}: verlinkt unbekannte id {ref}",
    },
    "chk_secret": {
        "en": "{path}: looks like a {label}: {preview}… (store only the secret's name and where it is kept)",
        "zh": "{path}：疑似{label}：{preview}…（知识库里只写密钥名字和保管位置）",
        "ja": "{path}: {label} のようです: {preview}…（秘密情報は名前と保管場所だけを書いてください）",
        "es": "{path}: parece un/a {label}: {preview}… (guarda solo el nombre del secreto y dónde está)",
        "fr": "{path} : ressemble à un(e) {label} : {preview}… (n'écrivez que le nom du secret et son emplacement)",
        "de": "{path}: sieht aus wie {label}: {preview}… (nur Name und Aufbewahrungsort des Geheimnisses notieren)",
    },
    "chk_done": {
        "en": "Check finished: {docs} documents, {problems} problems, {warns} warnings.",
        "zh": "检查完成：{docs} 篇文档，{problems} 个问题，{warns} 个提醒。",
        "ja": "チェック完了: 文書 {docs} 件、問題 {problems} 件、警告 {warns} 件。",
        "es": "Revisión terminada: {docs} documentos, {problems} problemas, {warns} avisos.",
        "fr": "Vérification terminée : {docs} documents, {problems} problèmes, {warns} avertissements.",
        "de": "Prüfung fertig: {docs} Dokumente, {problems} Probleme, {warns} Warnungen.",
    },
    "lint_title": {
        "en": "Wiki health check {date}", "zh": "知识库健康检查 {date}", "ja": "Wiki ヘルスチェック {date}",
        "es": "Chequeo de salud de la wiki {date}", "fr": "Bilan de santé du wiki {date}",
        "de": "Wiki-Gesundheitscheck {date}",
    },
    "lint_summary": {
        "en": "{docs} documents. Orphans {orphans}, stale {stale}, possible duplicates {dups}, lessons without links {noout}, lines marked outdated {supers}.",
        "zh": "共 {docs} 篇。孤立 {orphans}，过时 {stale}，疑似重复 {dups}，经验无出链 {noout}，自称过时/被取代的行 {supers}。",
        "ja": "文書 {docs} 件。孤立 {orphans}、古い {stale}、重複の疑い {dups}、リンクのない教訓 {noout}、古いと書かれた行 {supers}。",
        "es": "{docs} documentos. Huérfanos {orphans}, desactualizados {stale}, posibles duplicados {dups}, lecciones sin enlaces {noout}, líneas marcadas como obsoletas {supers}.",
        "fr": "{docs} documents. Orphelins {orphans}, périmés {stale}, doublons possibles {dups}, leçons sans liens {noout}, lignes marquées obsolètes {supers}.",
        "de": "{docs} Dokumente. Verwaist {orphans}, veraltet {stale}, mögliche Duplikate {dups}, Lektionen ohne Links {noout}, als veraltet markierte Zeilen {supers}.",
    },
    "lint_howto": {
        "en": "How to fix: link orphans from a related page with [[id]]; update or archive stale pages; merge duplicates; rewrite lines that say they are outdated so only the current answer remains. This tool only gives hints; read the pages to judge contradictions.",
        "zh": "处理方法：孤立条目在相关页面用 [[id]] 链上；过时条目核实后更新或改 status: archived；疑似重复合并成一篇；自称过时的行改成最新口径，只留现在的结论。本工具只给线索，矛盾要读原文判断。",
        "ja": "対処: 孤立した文書は関連ページから [[id]] でリンク。古い文書は更新するかアーカイブ。重複は統合。「古い」と書かれた行は最新の結論だけが残るよう書き直す。このツールはヒントのみ。矛盾は本文を読んで判断してください。",
        "es": "Cómo arreglarlo: enlaza los huérfanos desde una página relacionada con [[id]]; actualiza o archiva lo desactualizado; fusiona duplicados; reescribe las líneas obsoletas para que solo quede la respuesta actual. La herramienta solo da pistas; lee las páginas para juzgar contradicciones.",
        "fr": "Correction : liez les orphelins depuis une page liée avec [[id]] ; mettez à jour ou archivez les pages périmées ; fusionnez les doublons ; réécrivez les lignes obsolètes pour ne garder que la réponse actuelle. L'outil ne donne que des indices ; lisez les pages pour trancher les contradictions.",
        "de": "Behebung: verwaiste Seiten per [[id]] von einer passenden Seite verlinken; veraltete Seiten aktualisieren oder archivieren; Duplikate zusammenführen; als veraltet markierte Zeilen so umschreiben, dass nur der aktuelle Stand bleibt. Das Tool liefert nur Hinweise; Widersprüche durch Lesen klären.",
    },
    "lint_orphans": {
        "en": "Orphans (nothing links to them)", "zh": "孤立条目（没有任何条目链接到它）",
        "ja": "孤立（どこからもリンクされていない）", "es": "Huérfanos (nada enlaza a ellos)",
        "fr": "Orphelins (aucun lien entrant)", "de": "Verwaist (nichts verlinkt sie)",
    },
    "lint_stale": {
        "en": "Stale (not updated within the configured days)", "zh": "过时条目（超过设定天数没更新）",
        "ja": "古い（設定日数以上更新なし）", "es": "Desactualizados (sin cambios en los días configurados)",
        "fr": "Périmés (pas mis à jour depuis le délai configuré)", "de": "Veraltet (länger als konfiguriert nicht aktualisiert)",
    },
    "lint_dups": {
        "en": "Possible duplicates (similar titles)", "zh": "疑似重复（标题相似）",
        "ja": "重複の疑い（似たタイトル）", "es": "Posibles duplicados (títulos parecidos)",
        "fr": "Doublons possibles (titres proches)", "de": "Mögliche Duplikate (ähnliche Titel)",
    },
    "lint_noout": {
        "en": "Lessons that link to nothing", "zh": "经验没有链接任何项目或条目",
        "ja": "どこにもリンクしていない教訓", "es": "Lecciones sin enlaces salientes",
        "fr": "Leçons sans liens sortants", "de": "Lektionen ohne ausgehende Links",
    },
    "lint_supers": {
        "en": "Lines that say they are outdated (old and new answers may coexist)",
        "zh": "自称过时或被取代的行（可能新旧口径并存）",
        "ja": "古い・置き換え済みと書かれた行（新旧の結論が混在している可能性）",
        "es": "Líneas que dicen estar obsoletas (pueden convivir respuestas viejas y nuevas)",
        "fr": "Lignes se disant obsolètes (anciennes et nouvelles réponses peuvent coexister)",
        "de": "Zeilen, die sich als veraltet bezeichnen (alter und neuer Stand könnten nebeneinander stehen)",
    },
    "lint_days": {"en": "{n} days", "zh": "{n} 天", "ja": "{n} 日", "es": "{n} días", "fr": "{n} jours", "de": "{n} Tage"},
    "lint_line": {"en": "line {n}", "zh": "第 {n} 行", "ja": "{n} 行目", "es": "línea {n}", "fr": "ligne {n}", "de": "Zeile {n}"},
    "none": {"en": "none", "zh": "无", "ja": "なし", "es": "ninguno", "fr": "aucun", "de": "keine"},
    "written": {
        "en": "Written to {path}", "zh": "已写入 {path}", "ja": "{path} に書き出しました",
        "es": "Escrito en {path}", "fr": "Écrit dans {path}", "de": "Geschrieben nach {path}",
    },
    "stats_docs": {"en": "Documents: ", "zh": "文档：", "ja": "文書: ", "es": "Documentos: ", "fr": "Documents : ", "de": "Dokumente: "},
    "stats_langs": {"en": "Languages: ", "zh": "语言：", "ja": "言語: ", "es": "Idiomas: ", "fr": "Langues : ", "de": "Sprachen: "},
    "stats_projects": {"en": "By project: ", "zh": "按项目：", "ja": "プロジェクト別: ", "es": "Por proyecto: ", "fr": "Par projet : ", "de": "Nach Projekt: "},
    "stats_recent": {"en": "Recently updated:", "zh": "最近更新：", "ja": "最近の更新:", "es": "Actualizado recientemente:", "fr": "Mis à jour récemment :", "de": "Zuletzt aktualisiert:"},
    "sql_readonly": {
        "en": "Only read-only queries (SELECT / WITH / PRAGMA) are allowed.",
        "zh": "只允许只读查询（SELECT / WITH / PRAGMA）。",
        "ja": "読み取り専用のクエリ（SELECT / WITH / PRAGMA）のみ使えます。",
        "es": "Solo se permiten consultas de lectura (SELECT / WITH / PRAGMA).",
        "fr": "Seules les requêtes en lecture (SELECT / WITH / PRAGMA) sont autorisées.",
        "de": "Nur lesende Abfragen (SELECT / WITH / PRAGMA) sind erlaubt.",
    },
    "unknown_cmd": {
        "en": "Unknown command {cmd}. Run `wiki help`.", "zh": "不认识的命令 {cmd}。运行 `wiki help` 看用法。",
        "ja": "不明なコマンド {cmd}。`wiki help` を実行してください。", "es": "Comando desconocido {cmd}. Ejecuta `wiki help`.",
        "fr": "Commande inconnue {cmd}. Lancez `wiki help`.", "de": "Unbekannter Befehl {cmd}. Siehe `wiki help`.",
    },
    "note_empty": {
        "en": "title and content must not be empty.", "zh": "title 和 content 都不能为空。",
        "ja": "title と content は空にできません。", "es": "title y content no pueden estar vacíos.",
        "fr": "title et content ne peuvent pas être vides.", "de": "title und content dürfen nicht leer sein.",
    },
    "note_long": {
        "en": "Content too long (> {n} characters).", "zh": "内容太长（超过 {n} 字符）。",
        "ja": "内容が長すぎます（{n} 文字超）。", "es": "Contenido demasiado largo (> {n} caracteres).",
        "fr": "Contenu trop long (> {n} caractères).", "de": "Inhalt zu lang (> {n} Zeichen).",
    },
    "note_secret": {
        "en": "Rejected: the note contains a {label}. Store only the secret's name and where it is kept.",
        "zh": "拒收：内容里有{label}。只写密钥名字和保管位置。",
        "ja": "受け付けません: {label} が含まれています。秘密情報は名前と保管場所だけを書いてください。",
        "es": "Rechazado: la nota contiene un/a {label}. Guarda solo el nombre del secreto y dónde está.",
        "fr": "Refusé : la note contient un(e) {label}. N'écrivez que le nom du secret et son emplacement.",
        "de": "Abgelehnt: Die Notiz enthält {label}. Nur Name und Aufbewahrungsort notieren.",
    },
    "note_path": {
        "en": "update_path must be a relative path inside the wiki.", "zh": "update_path 必须是知识库内的相对路径。",
        "ja": "update_path は Wiki 内の相対パスにしてください。", "es": "update_path debe ser una ruta relativa dentro de la wiki.",
        "fr": "update_path doit être un chemin relatif dans le wiki.", "de": "update_path muss ein relativer Pfad im Wiki sein.",
    },
    "note_ok": {
        "en": "Received as {path}. A maintainer (human or agent) reviews the inbox and merges it.",
        "zh": "已收到，存为 {path}。维护者（人或 agent）审核收件箱后并入。",
        "ja": "{path} として受け付けました。管理者（人または agent）が確認してから取り込みます。",
        "es": "Recibido como {path}. Un responsable (persona o agente) revisa la bandeja y lo integra.",
        "fr": "Reçu sous {path}. Un mainteneur (humain ou agent) relit la boîte de réception puis l'intègre.",
        "de": "Als {path} eingegangen. Eine Betreuerin oder ein Agent prüft den Eingang und übernimmt es.",
    },
}


def lang(cfg_lang: str | None = None) -> str:
    v = (os.environ.get("AGENT_WIKI_LANG") or cfg_lang or "en").lower().replace("_", "-")
    v = v.split("-")[0]
    return v if v in LANGUAGES else "en"


_current = {"lang": "en"}


def set_lang(code: str | None) -> None:
    _current["lang"] = lang(code)


def t(_key: str, **kw) -> str:
    entry = M[_key]
    text = entry.get(_current["lang"]) or entry["en"]
    return text.format(**kw) if kw else text
