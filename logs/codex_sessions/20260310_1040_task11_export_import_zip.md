# task11 export/import zip

- date: 2026-03-10 10:40 JST
- branch: feat/task-11-export-import-zip

## summary

- Added `/export/` and `/import/` backup flows for meal log data.
- Implemented ZIP export/import service with `logs.json` plus `photos/`.
- Added schema document for `logs.json`.
- Added tests for export shape, overwrite restore, invalid ZIP rejection, and optional `photos/` dir entry handling.

## commands

- `git checkout -b feat/task-11-export-import-zip`
- `python3 -m py_compile src/meallogs/views.py src/meallogs/forms.py src/meallogs/services/backup.py src/meallogs/tests.py`
- `docker compose run --rm web python manage.py test`

## result

- `python3 -m py_compile ...`: passed
- `docker compose run --rm web python manage.py test`: passed (`Ran 40 tests in 14.846s`)
