# project-progress-dashboard proofs

**HEAD**: 7c57984
**Tree**: clean
**Shell**: C:/Program Files/Git\bin\bash.exe
**Result**: 4 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run tests / tests/unit/test_project_progress.py::test_dashboard_lists_verified_deliveries_and_evidence PASSED` | pass |
| C2 | `run tests / tests/unit/test_project_progress.py::test_dashboard_lists_unprioritized_roadmap PASSED` | pass |
| C3 | `run tests / tests/unit/test_project_progress.py::test_dashboard_requires_same_commit_updates PASSED` | pass |
| C4 | `run tests / tests/unit/test_project_progress.py::test_completed_dashboard_rows_have_passing_verification PASSE` | pass |

## Output

`Run tests` - exit 0

```
============================= test session starts =============================
platform win32 -- Python 3.12.4, pytest-9.2.0, pluggy-1.7.0 -- C:\Users\Elon\AppData\Local\Programs\Python\Python312\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\Elon\.copilot\session-state\49a0cb37-ceb0-4ddf-9fe0-43d8c8a061b5\progress-tracker-final-verification-worktree
configfile: pyproject.toml
plugins: anyio-4.16.0
collecting ... collected 4 items

tests/unit/test_project_progress.py::test_dashboard_lists_verified_deliveries_and_evidence PASSED [ 25%]
tests/unit/test_project_progress.py::test_dashboard_lists_unprioritized_roadmap PASSED [ 50%]
tests/unit/test_project_progress.py::test_dashboard_requires_same_commit_updates PASSED [ 75%]
tests/unit/test_project_progress.py::test_completed_dashboard_rows_have_passing_verification PASSED [100%]

============================== 4 passed in 0.14s ==============================
```
