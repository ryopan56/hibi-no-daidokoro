## Task

Task12 review follow-up: fix shared UI static asset paths on non-root pages.

## Summary

- Updated `STATIC_URL` to use a root-relative `/static/` path so `{% static %}` assets resolve correctly on nested routes.
- Added a regression test that verifies the login page renders the shared CSS and JS with root-relative static URLs.

## Changed Files

- `src/hibi_no_daidokoro/settings.py`
- `src/accounts/tests.py`

## Commands

- `git status -sb`
- `git diff -- src/hibi_no_daidokoro/settings.py src/accounts/tests.py`
- `docker compose exec web python manage.py test accounts.tests.AuthFlowTests`

## Result

- The targeted auth flow test suite passed.
- Review issue about relative static asset URLs is addressed.

## Notes

- This change is limited to static URL resolution and regression coverage.
