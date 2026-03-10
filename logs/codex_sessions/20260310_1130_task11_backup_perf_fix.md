# task11 backup perf fix

- date: 2026-03-10 11:30 JST
- branch: fix/task-11-backup-export-import-perf

## summary

- Replaced export-side ingredient access with prefetch-cache-friendly iteration to avoid per-log extra queries.
- Changed import photo restore from eager `archive.read()` buffering to per-photo streaming with `ZipFile.open()`.
- Kept current backup schema, validation rules, overwrite restore behavior, and optional `photos/` dir entry support.

## diff review

- `git status -sb`: only `src/meallogs/services/backup.py` changed before logging.
- `git diff --stat`: `src/meallogs/services/backup.py | 126`
- `git diff`: confirmed no edits outside backup service.

## commands

- `git status -sb`
- `git diff --stat`
- `git diff`
- `docker compose run --rm web python manage.py test`

## result

- `docker compose run --rm web python manage.py test`: passed (`Ran 40 tests in 15.130s`)
