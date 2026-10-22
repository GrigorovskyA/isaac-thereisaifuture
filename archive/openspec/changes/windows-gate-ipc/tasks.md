# Tasks

## 1. Implementation

- [x] 1.1 Add bounded atomic/read/remove helpers and clip gate I/O to original deadlines.
- [x] 1.2 Preserve primary errors through initial/reset/stop cleanup; guarantee harness cleanup assertions.

## 2. Verification

- [x] 2.1 Add deterministic sharing/deadline/failure tests and real Windows concurrency; remove the known-defect xfail in favor of bounded success/failure assertions.
- [x] 2.2 Run full Windows Check.ps1, strict OpenSpec and review coupled Lua/socket/CPU learner evidence; document limitations and updated experiment blockers.
