# PaykanLang standard library

The standard library of [PaykanLang](https://github.com/parsabee/PaykanLang),
written in Paykan itself. Version **0.2.0-dev**, targeting PaykanLang
`develop` (it also runs on the 0.1.1 release).

## Using it

A program imports a standard-library module with a *system import*,
`import ::name;`, which the compiler resolves to `<stdlib dir>/name.pkn`. The
stdlib directory is `$PAYKAN_STDLIB`, so point it at this repository's
`stdlib/` directory:

```sh
PAYKAN_STDLIB=/path/to/PaykanLang_Stdlib/stdlib paykan run prog.pkn
```

```pkn
import ::collections;

fn main() -> int {
  counts = collections::HashMap<Str, int>();
  counts.put("a", 1);
  counts.put("a", counts.getOr("a", 0) + 1);
  println(counts);                       // {"a": 2}
  return 0;
}
```

> **Interim: generics are not importable yet.** Every class in `::collections`
> is generic, and PaykanLang does not export generic classes across modules
> yet ([parsabee/PaykanLang#160](https://github.com/parsabee/PaykanLang/issues/160));
> the program above is rejected today with
> `generic types and functions cannot be imported yet: 'collections::HashMap<...>' names a template of another module`.
> Until that lands, use the module by inlining it: remove the
> `import ::collections;` line, drop the `collections::` qualifier and put the
> contents of `stdlib/collections.pkn` at the top of your program. That is
> exactly what `scripts/run_tests.py` does for the tests and examples (run it
> with `--native` to use the real import form once #160 is released). The
> programs in `examples/` are written in the real form.

## Modules

| Module | Contents |
|--------|----------|
| [`::collections`](stdlib/collections.pkn) | `HashMap<K, V>`, `HashSet<V>`, `ArrayList<V>`; `join`, `listToString` |

### `::collections`

**`HashMap<K, V>`** — a hash table with insertion-ordered iteration.

| Method | Description |
|--------|-------------|
| `HashMap<K, V>()` | An empty map |
| `len() -> int`, `isEmpty() -> bool` | Size |
| `put(key: K, value: V) -> bool` | Store, replacing an existing value; `True` if the key is new |
| `get(key: K) -> V?` | The value, or `None` |
| `getOr(key: K, fallback: V) -> V` | The value, or `fallback` |
| `contains(key: K) -> bool` | Presence |
| `remove(key: K) -> bool` | Remove; `True` if it was present |
| `clear()` | Remove everything |
| `keys() -> K[]`, `values() -> V[]`, `entries() -> (K, V)[]` | Insertion order |
| `putAll(other: HashMap<K, V>)`, `copy() -> HashMap<K, V>` | Bulk copy |
| `toString() -> Str` | `{"a": 1, "b": 2}` (Str keys and values quoted) |
| `equals(other: Obj) -> bool` | Same keys mapped to `==` values, in any order; backs `==` |

**`HashSet<V>`** — a set with insertion-ordered iteration.

| Method | Description |
|--------|-------------|
| `HashSet<V>()` | An empty set |
| `len() -> int`, `isEmpty() -> bool` | Size |
| `add(v: V) -> bool` | Add; `True` if it was absent |
| `addAll(vs: V[])` | Add every element |
| `contains(v: V) -> bool`, `remove(v: V) -> bool`, `clear()` | Membership |
| `values() -> V[]` | Insertion order |
| `union(o)`, `intersection(o)`, `difference(o) -> HashSet<V>` | New sets; the inputs are untouched |
| `isSubsetOf(o: HashSet<V>) -> bool`, `copy() -> HashSet<V>` | |
| `toString() -> Str` | `{1, 2, 3}` |
| `equals(other: Obj) -> bool` | Same elements in any order; backs `==` |

**`ArrayList<V>`** — a growable list backed by a builtin array. Elements are
compared with `==`, so `V` can be any type, tuples and optionals included.

| Method | Description |
|--------|-------------|
| `ArrayList<V>()` | An empty list |
| `len() -> int`, `isEmpty() -> bool` | Size |
| `get(i: int) -> V`, `set(i: int, v: V)` | Bounds-checked element access |
| `push(v: V)`, `pushAll(vs: V[])`, `pop() -> V` | At the end |
| `insert(i: int, v: V)`, `removeAt(i: int) -> V` | Anywhere (`0 <= i <= len` for `insert`) |
| `remove(v: V) -> bool` | Remove the first element `== v` |
| `indexOf(v: V) -> int`, `lastIndexOf(v: V) -> int`, `contains(v: V) -> bool` | Search (`-1` when absent) |
| `swap(i: int, j: int)`, `reverse()`, `clear()` | In place |
| `slice(from: int, to: int) -> ArrayList<V>`, `copy() -> ArrayList<V>`, `toArray() -> V[]` | New containers |
| `equals(other: Obj) -> bool` | Same elements in the same order; backs `==` |

Free functions: `join<V>(xs: ArrayList<V>, sep: Str) -> Str` and
`listToString<V>(xs: ArrayList<V>) -> Str` (`[1, 2, 3]`, Str elements quoted).

**Keys and hashing.** A `HashMap` key or `HashSet` element must be a *hashable*
type: `int`, `float`, `bool`, `char`, `Str`, an array or a class instance.
It is hashed over the text of its `toString()` and compared with `equals()`,
so `int`, `float`, `bool`, `char` and `Str` keys have value semantics, and a
class chooses: override neither `toString` nor `equals` and it is keyed by
identity; override both consistently (equal objects print alike) and it is
keyed by value. Tuples and optionals cannot be keys (the boxing goes through
`K?`, and the language has no `(A, B)?` or `T??`). A `HashMap` value type `V`
must be hashable too (`get` returns a `V?`); `ArrayList` has no such limit.
`-0.0` and `0.0` are one key; a NaN key can never be found again.

**Iteration order.** `keys`, `values`, `entries`, `toString` and a set's
`values` follow insertion order; removing an entry keeps the order of the
others, and re-inserting a removed key puts it last. The order is the same on
every backend, so programs may rely on it.

## Repository layout

```
stdlib/            the modules; PAYKAN_STDLIB points here
tests/             one program per module (+ stress), with .expected output
examples/          small programs using the library, in the real import form
scripts/run_tests.py   the test runner (Python 3 standard library only)
.github/workflows/ci.yml
```

## Running the tests

```sh
python3 scripts/run_tests.py                     # paykan from PATH, every backend
python3 scripts/run_tests.py --paykan ~/PaykanLang/build/bin/paykan --backend llvm
python3 scripts/run_tests.py --update            # rewrite the .expected files
```

Every program is run with `--track-heap` on every backend `paykan
--list-backends` reports (`c` and `llvm`); a run passes when it exits 0, its
stdout equals the `.expected` file and the heap statistics report zero live
blocks. CI does the same against the latest PaykanLang Linux release.

## Versioning

The library's version tracks the PaykanLang version it targets: `0.2.0-dev`
is written against PaykanLang `develop` (the upcoming 0.2.0, which will export
generics across modules and install the library as compiled `.pkm` modules).
A release of the library is tagged with the compiler version it was tested
against. See [CHANGELOG.md](CHANGELOG.md).

## License

MIT, copyright (c) 2026 Parsa Bagheri. See [LICENSE](LICENSE).
