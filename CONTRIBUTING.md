# Contributing to cobs-conformance

This repo holds the canonical COBS / COBS-R conformance vectors and the
reference implementation they are generated from.

## Getting started

Pure Python 3, no dependencies:

```console
python verify.py vectors/vectors.jsonl   # check vectors against reference.py
python generate.py                        # regenerate vectors (deterministic)
ruff check .                             # lint the Python (also enforced in CI)
```

`reference.py` is the source of truth. If you change it, regenerate the vectors
and make sure `verify.py` still passes.

## Git workflow: Trunk-Based Development with tbdflow

This project uses **[Trunk-Based Development](https://trunkbaseddevelopment.com/)**:
everyone integrates small, frequent changes into `main` (the trunk) instead of
long-lived branches. We use the [`tbdflow`](https://github.com/cladam/tbdflow)
CLI to make the safe path the easy path.

Install it once (Rust toolchain):

```console
cargo install tbdflow
```

### Everyday commits

`tbdflow commit` pulls the latest `main`, creates a
[Conventional Commit](#conventional-commits), and pushes -- all in one step:

```console
tbdflow commit --type fix --scope reference -m "handle empty input"
```

For a larger change that needs review, use a short-lived branch and merge it
back quickly (ideally within a day):

```console
tbdflow branch --type feat --name new-vector-format
# ...work...
tbdflow complete            # merges into main and deletes the branch
```

Other useful commands: `tbdflow sync` (pull + show recent history + flag stale
branches), `tbdflow radar` (spot overlapping work), `tbdflow changelog`
(generate a changelog from the commit history), and `tbdflow undo` (safely
revert a trunk commit).

### The two config files

`tbdflow init` generated the two files that drive this workflow:

- **`.tbdflow.yml`** -- the workflow + linting configuration. It sets the trunk
  branch (`main`), the allowed short-lived branch prefixes, and the **commit
  message lint rules** (allowed Conventional Commit types, lowercase scope and
  subject, max subject length 72, etc.). `tbdflow commit` refuses a commit that
  breaks these rules.
- **`.dod.yml`** -- the **Definition of Done** checklist. `tbdflow commit` shows
  it before committing so you confirm tests pass, docs are updated, and so on.
  Skip it for a trivial change with `tbdflow commit ... --no-verify`.

Run `tbdflow info` to see the effective configuration.

## Conventional Commits

Every commit message follows
[Conventional Commits](https://www.conventionalcommits.org):

```
type(scope): short imperative subject

optional body

optional BREAKING CHANGE: footer
```

Allowed **types**: `build`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`,
`refactor`, `revert`, `style`, `test`. The subject is lowercase, imperative
("add", not "added"), and has no trailing period. Breaking changes add a `!`
after the type/scope (`feat!:`) or a `BREAKING CHANGE:` footer.

This is enforced two ways: locally by `tbdflow commit`, and in CI by the
**Commit lint** workflow (`.github/workflows/commit-lint.yml`), which checks
every commit in a pull request.

## License

By contributing you agree that your contributions are licensed under the
project's [MIT License](LICENSE).
