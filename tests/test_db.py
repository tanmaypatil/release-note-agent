"""
Section 1 — DB layer tests.

Run from the project root:
    python tests/test_db.py
"""
import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db

# Use a temporary database so each run starts from a clean slate
_tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
db.DB_PATH = _tmp.name
_tmp.close()

LABEL = 'v1.0'


def test_init():
    db.init_db()
    print('init_db:                  PASS')


def test_create_and_fetch():
    id1 = db.create_defect('Login crashes on Safari', '2024-01-15', 'Fixed null pointer', LABEL, 'RESOLVED')
    id2 = db.create_defect('Tooltip not showing',     '2024-01-16', 'Updated z-index',    LABEL, 'RESOLVED')
    id3 = db.create_defect('Password reset delayed',  '2024-01-17', '',                   LABEL, 'OPEN')

    assert id1 and id2 and id3, 'create_defect should return a row id'
    print('create_defect:            PASS')

    all_defects = db.get_all_defects()
    assert len(all_defects) >= 3, f'Expected at least 3 defects, got {len(all_defects)}'
    print('get_all_defects:          PASS')

    resolved = db.get_resolved_defects(LABEL)
    assert len(resolved) == 2, f'Expected 2 RESOLVED for {LABEL}, got {len(resolved)}'
    print(f'get_resolved_defects:     PASS  ({len(resolved)} rows)')

    return id1, id2, id3


def test_update_status(defect_id):
    db.update_defect_status(defect_id, 'OPEN')
    all_defects = {d['id']: d['status'] for d in db.get_all_defects()}
    assert all_defects[defect_id] == 'OPEN', 'Status should be OPEN after update'
    print('update_defect_status:     PASS')


def test_release_info_missing():
    info = db.get_release_info('nonexistent-label')
    assert info is None, 'Expected None for unknown label'
    print('get_release_info (miss):  PASS')


def main():
    print('=== DB Layer ===')
    test_init()
    id1, id2, id3 = test_create_and_fetch()
    test_update_status(id1)
    test_release_info_missing()
    print('\nAll DB tests passed.')
    os.unlink(db.DB_PATH)


if __name__ == '__main__':
    main()
