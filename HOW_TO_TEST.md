# How to Test — Release Note Agent

## Prerequisites

```bash
pip install -r requirements.txt   # anthropic, python-docx, python-dotenv

cp .env.example .env
# edit .env and set:  ANTHROPIC_API_KEY=sk-ant-...
```

Verify the key is loaded correctly before running anything that calls Claude:

```bash
python tests/check_env.py
# ANTHROPIC_API_KEY: sk-ant-...  PASS
```

---

## 1 — DB Layer

```bash
python tests/test_db.py
```

Expected:
```
=== DB Layer ===
init_db:                  PASS
create_defect:            PASS
get_all_defects:          PASS
get_resolved_defects:     PASS  (2 rows)
update_defect_status:     PASS
get_release_info (miss):  PASS

All DB tests passed.
```

---

## 2 — Doc Generator

```bash
python tests/test_doc.py
```

Expected:
```
=== Doc Generator ===
create_doc:          PASS  (2 data rows + header)
remove_row:          PASS  (row <n> gone, 1 data rows remain)
remove_row (no-op):  PASS

All doc generator tests passed.
```

---

## 3 — HTTP Server + UI

Start the server in one terminal:

```bash
python server.py
# → Release Note Manager running at http://localhost:8080
```

In a second terminal:

```bash
python tests/test_server.py
```

Expected:
```
=== HTTP Server  (http://localhost:8080) ===
GET  /api/defects:          PASS  (<n> defects)
POST /api/defects:          PASS  (id=<n>)
PATCH /api/defects/<n>:     PASS  (status=RESOLVED)
GET  /:                     PASS  (UI served)

All server tests passed.
```

Open the UI manually and verify:
```bash
open http://localhost:8080
```
- Table renders all defects with colour-coded badges
- "Resolve" button turns badge green; "Revert" turns it orange
- Table auto-refreshes every 8 s

---

## 4 — Agent (conversational loop + polling)

> The agent reads `ANTHROPIC_API_KEY` from `.env` via python-dotenv.
> Run `python tests/check_env.py` first if you haven't already.

Open two terminals.

**Terminal A — start the agent:**

```bash
python agent.py --poll 5    # 5 s poll for faster testing
```

Type at the prompt:
```
> Generate release notes for v1.0
```

Expected:
- Claude responds conversationally
- `[ACTION] Generating release notes for 'v1.0'...` printed
- `release_notes_v1.0.docx` created in the project root
- Open the doc and confirm header row + RESOLVED defects

---

## 5 — Polling / Live Removal

With the agent still running in Terminal A:

**Terminal B — revert a RESOLVED defect to OPEN:**

```bash
python tests/revert_defect.py 2
```

Expected output:
```
Defect 2 → OPEN
```

Within `--poll` seconds Terminal A should print:
```
[POLL] Defect 2 reverted to OPEN — removing from 'v1.0' release notes...
[POLL] Row 2 removed from release_notes_v1.0.docx
```

Open the doc and confirm defect 2 is gone.

---

## 6 — Shutdown

```
> Shutdown
```

Expected: Claude replies, `ACTION:SHUTDOWN` is detected, agent exits cleanly.

---

## Teardown

```bash
rm -f defects.db release_notes_*.docx
```
