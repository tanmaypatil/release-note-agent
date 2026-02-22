"""
Section 5 helper — revert a defect status to OPEN to trigger the poll loop.

Run from the project root:
    python tests/revert_defect.py <defect_id>

Example:
    python tests/revert_defect.py 2
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db


def main():
    if len(sys.argv) < 2:
        print('Usage: python tests/revert_defect.py <defect_id>')
        sys.exit(1)

    defect_id = int(sys.argv[1])
    db.update_defect_status(defect_id, 'OPEN')

    all_defects = {d['id']: d['status'] for d in db.get_all_defects()}
    status = all_defects.get(defect_id, 'NOT FOUND')
    print(f'Defect {defect_id} → {status}')


if __name__ == '__main__':
    main()
