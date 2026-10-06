#!/usr/bin/env python3
"""Run the standard-library tests on every backend the paykan binary lists.

Each tests/*_test.pkn (and each examples/*.pkn) is a program that imports a
module with `import ::name;` and uses it as `name::Thing`. Until PaykanLang
exports generic classes across modules (parsabee/PaykanLang#160) the real
import form is rejected, so by default the runner inlines the module: it
removes the import line, drops the `name::` qualifier and prepends
stdlib/name.pkn to the program, then compiles the result as one file.
`--native` runs the programs unchanged with PAYKAN_STDLIB pointing at stdlib/,
which is what the tests will do once #160 lands.

A program passes on a backend when it exits 0, its stdout equals the
`.expected` file next to it, and `--track-heap` reports zero live blocks.
`--update` rewrites the .expected files from the first backend's output.
Only the Python 3 standard library is used.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STDLIB = os.path.join(ROOT, "stdlib")
IMPORT_RE = re.compile(r"^\s*import\s+::(\w+)\s*;\s*$", re.M)
LIVE_RE = re.compile(r"^\s*live blocks\s*:\s*(-?\d+)\s*$", re.M)


def find_paykan(explicit):
    if explicit:
        return explicit
    found = shutil.which("paykan")
    if not found:
        sys.exit("error: paykan not found on PATH (pass --paykan /path/to/paykan)")
    return found


def list_backends(paykan):
    out = subprocess.run([paykan, "--list-backends"], capture_output=True, text=True, check=True).stdout
    backends = []
    for line in out.splitlines():
        name = line.split(":")[0].split()[0] if line.strip() else ""
        if name:
            backends.append(name)
    return backends


def inline_modules(source):
    """Return `source` with every `import ::m;` replaced by the module's text."""
    modules = IMPORT_RE.findall(source)
    body = IMPORT_RE.sub("", source)
    prelude = []
    for name in modules:
        path = os.path.join(STDLIB, name + ".pkn")
        with open(path, encoding="utf-8") as f:
            prelude.append(f"// ---- inlined from stdlib/{name}.pkn (interim, see scripts/run_tests.py)\n" + f.read())
        body = body.replace(name + "::", "")
    return "\n".join(prelude) + "\n// ---- test program\n" + body


def run_one(paykan, backend, program, native, workdir):
    env = dict(os.environ)
    if native:
        env["PAYKAN_STDLIB"] = STDLIB
        path = program
    else:
        with open(program, encoding="utf-8") as f:
            text = inline_modules(f.read())
        path = os.path.join(workdir, os.path.basename(program))
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
    cmd = [paykan, f"--backend={backend}", "--track-heap", "run", path]
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=workdir)
    return proc


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--paykan", help="the paykan binary (default: from PATH)")
    ap.add_argument("--backend", action="append", help="run only this backend (repeatable)")
    ap.add_argument("--update", action="store_true", help="rewrite the .expected files")
    ap.add_argument("--native", action="store_true", help="use the real `import ::name;` with PAYKAN_STDLIB")
    ap.add_argument("programs", nargs="*", help="programs to run (default: tests/*_test.pkn and examples/*.pkn)")
    args = ap.parse_args()

    paykan = find_paykan(args.paykan)
    backends = args.backend or list_backends(paykan)
    programs = [os.path.abspath(p) for p in args.programs] or sorted(
        os.path.join(ROOT, d, f)
        for d in ("tests", "examples")
        if os.path.isdir(os.path.join(ROOT, d))
        for f in os.listdir(os.path.join(ROOT, d))
        if f.endswith(".pkn")
    )

    failures = 0
    with tempfile.TemporaryDirectory(prefix="paykan-stdlib-tests-") as workdir:
        for program in programs:
            expected_path = os.path.splitext(program)[0] + ".expected"
            for backend in backends:
                proc = run_one(paykan, backend, program, args.native, workdir)
                problems = []
                if proc.returncode != 0:
                    problems.append(f"exit code {proc.returncode}")
                m = LIVE_RE.search(proc.stderr)
                if m is None:
                    problems.append("no heap statistics in stderr")
                elif int(m.group(1)) != 0:
                    problems.append(f"{m.group(1)} live blocks")
                if args.update and backend == backends[0] and proc.returncode == 0:
                    with open(expected_path, "w", encoding="utf-8") as f:
                        f.write(proc.stdout)
                if os.path.exists(expected_path):
                    with open(expected_path, encoding="utf-8") as f:
                        if f.read() != proc.stdout:
                            problems.append("stdout differs from " + os.path.relpath(expected_path, ROOT))
                else:
                    problems.append("missing " + os.path.relpath(expected_path, ROOT))
                rel = os.path.relpath(program, ROOT)
                if problems:
                    failures += 1
                    print(f"FAIL {rel} [{backend}]: " + "; ".join(problems))
                    diag = proc.stderr.strip()
                    if diag:
                        print("  " + "\n  ".join(diag.splitlines()[:20]))
                else:
                    print(f"ok   {rel} [{backend}]")
    total = len(programs) * len(backends)
    print(f"{total - failures}/{total} passed on backends: {', '.join(backends)}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
