Read the following source files in the project root to understand the current architecture:
- db.py          (schema, every public function and its signature)
- agent.py       (CLI args, system prompt, action tokens, shared state, poll logic)
- doc_generator.py (create_doc and remove_row behaviour)
- server.py      (every HTTP endpoint: method, path, request body, response shape)
- ui/index.html  (what the UI renders and every user action it supports)
- CLAUDE.md      (project intent and constraints)

Also read every file in tests/ to understand what each script currently asserts.

Then rewrite HOW_TO_TEST.md so that:
1. Every test section exactly matches the current code — correct function names,
   argument counts, endpoint paths, expected row/column counts, CLI flags, and
   action tokens.
2. Sections are added for any new modules or endpoints not yet covered.
3. Sections are removed or updated if the corresponding code no longer exists or
   has changed.
4. Each "Run" command points to the correct script under tests/.
5. The teardown block lists every file that the tests produce.
5. The document stays concise — one code block per test, with a one-line
   "Expected:" note after each.

Do not change the overall structure (Prerequisites → numbered sections → Teardown)
unless the architecture genuinely requires it.
