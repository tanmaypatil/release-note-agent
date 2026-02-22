# How to Test — Release Note Agent

## Prerequisites

```bash
pip install -r requirements.txt   # anthropic, python-docx
export ANTHROPIC_API_KEY=<your-key>
```

---

## 1 — DB Layer

```bash
cd release-note-agent

# Tables created, no error
python -c "import db; db.init_db(); print('OK')"

# Seed test data
python -c "
import db
db.create_defect('Login crashes on Safari',  '2024-01-15', 'Fixed null pointer', 'v1.0', 'RESOLVED')
db.create_defect('Tooltip not showing',       '2024-01-16', 'Updated z-index',    'v1.0', 'RESOLVED')
db.create_defect('Password reset delayed',    '2024-01-17', '',                   'v1.0', 'OPEN')
print(db.get_all_defects())
"
```

Expected: 3 rows, 2 RESOLVED + 1 OPEN for label `v1.0`.

---

## 2 — Doc Generator

```bash
# Create doc — should produce release_notes_v1.0.docx with 2 data rows
python -c "
import doc_generator
from docx import Document
path = doc_generator.create_doc('v1.0')
doc  = Document(path)
rows = doc.tables[0].rows
print(f'Rows (incl. header): {len(rows)}')   # expect 3
assert len(rows) == 3, 'Expected 2 data rows + 1 header'
print('create_doc: PASS')
"

# Remove a row — doc should shrink to 1 data row
python -c "
import doc_generator
from docx import Document
doc_generator.remove_row('v1.0', 1)
doc  = Document('release_notes_v1.0.docx')
rows = doc.tables[0].rows
print(f'Rows after removal: {len(rows)}')   # expect 2
assert len(rows) == 2, 'Expected 1 data row + 1 header'
print('remove_row: PASS')
"

# No-op when file does not exist (should not raise)
python -c "
import doc_generator
doc_generator.remove_row('does-not-exist', 999)
print('remove_row no-op: PASS')
"
```

---

## 3 — HTTP Server + UI

Start the server in one terminal:

```bash
python server.py
# → Release Note Manager running at http://localhost:8080
```

In a second terminal (or browser):

```bash
# GET all defects
curl http://localhost:8080/api/defects | python -m json.tool

# POST — create a defect
curl -s -X POST http://localhost:8080/api/defects \
  -H 'Content-Type: application/json' \
  -d '{"title":"Test defect","date":"2024-02-01","label":"v1.0","status":"OPEN","developer_comment":""}' \
  | python -m json.tool        # expect {"id": <n>}

# PATCH — resolve it  (replace <id> with the returned id)
curl -s -X PATCH http://localhost:8080/api/defects/<id> \
  -H 'Content-Type: application/json' \
  -d '{"status":"RESOLVED"}' \
  | python -m json.tool        # expect {"id": <n>, "status": "RESOLVED"}

# UI — opens in browser
open http://localhost:8080
```

Verify in the browser:
- Table renders all defects with colour-coded badges
- "Resolve" button turns badge green; "Revert" turns it orange
- Table auto-refreshes every 8 s

---

## 4 — Agent (conversational loop + polling)

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
python -c "import db; db.update_defect_status(2, 'OPEN')"
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
