# Repository Development Guidelines

## 1. Branching & Gitflow Standards
- **Active Branch**: All work must be conducted on feature or fix branches branched exclusively from `dev`.
- **Target Branch**: All Pull Requests must target `dev`. NEVER open a PR directly against `main`.
- **Protected Main**: `main` is only updated via fast-forward or release merges from `dev` upon Nikolas's request.

## 2. Local Verification Checklist (Pre-PR)
Before pushing commits or opening PRs:
1. In `searchboost_warden`: `cargo fmt --all -- --check` and `cargo clippy --all-targets -- -D warnings` must return 0.
2. In `searchboost_api`: `npm test` and `npx tsc --noEmit` must return 0.
3. In `searchboost_ui`: `npm test` and `npm run build` must return 0.
4. In `searchboost_service`: Python unit tests must return 0.
