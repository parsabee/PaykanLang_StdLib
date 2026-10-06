# Changelog

All notable changes to the PaykanLang standard library are listed here. The
version tracks the PaykanLang version the library targets (see README).

## 0.2.0-dev (unreleased) — targets PaykanLang `develop`

### Added

- `::collections`: `HashMap<K, V>`, `HashSet<V>` and `LinkedList<V>` (a
  cycle-free, index-linked deque usable as a stack and a queue), with the
  free functions `join` and `listToString` over `V[]`. The builtin `V[]`
  remains the one array type; there is no `ArrayList`.
- `scripts/run_tests.py`: runs every test and example on every backend the
  compiler lists, with heap tracking; inlines the modules until PaykanLang
  exports generics across modules (parsabee/PaykanLang#160).
- CI on Ubuntu against the latest PaykanLang release.
