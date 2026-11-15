# Contributing

Thanks for helping. Issues and pull requests are welcome.

- **Run the tests:** `pip install -e ".[dev]" && pytest`
- **Add an interface language:** add the code to `LANGUAGES` in `src/agent_wiki/i18n.py`, translate the strings
  (keep every `{placeholder}`; a test checks this), and add `src/agent_wiki/templates/<code>/{lesson,project,playbook}.md`.
  Untranslated strings fall back to English, so partial translations are fine.
- **Search quality:** add a failing case to `tests/test_wiki.py` with a page in `examples/demo-wiki/`, then fix it.
- **Keep the core dependency-free.** Anything that needs a third-party package goes behind an optional extra.
- Never put real secrets, customer data or personal information in examples or tests.
