#!/usr/bin/env python3
"""One command to build every f6m figure: ``python make_all.py``.

Run it from anywhere (``cd`` into this directory first if you like):

    python /root/autodl-tmp/SEU-SRTP/experiments/2026-10-07-08-formal6m/scripts/figures/make_all.py

It imports ``fig1..fig5`` in order and calls ``build()`` on each, then prints
every product's path, size and pixel dimensions.  A missing figure module is
skipped with a warning (the pipeline never crashes because one figure is not
written yet); a module whose ``build()`` raises is reported with its traceback
and the remaining figures still run, with a non-zero exit code at the end.

Contract for a figure module (both patterns are accepted):
    * file named ``fig<N>.py`` or ``fig<N>_<slug>.py`` (N in 1..5), living in
      this directory (e.g. fig1_reward_by_scale.py);
    * module-level ``def build(camp=None, out_dir=None) -> Path | list[Path] | None``
      - ``camp`` / ``out_dir`` are passed only if the signature accepts them
      (``build`` may take no arguments at all);
    * it imports ``style`` and ``data`` from this same directory, uses
      ``style.color_for_n`` / ``data.smooth_by_steps`` and writes through
      ``style.save``; it returns the paths it wrote (optional, they are also
      found by scanning the output directory).
"""

from __future__ import annotations

import argparse
import importlib.util
import inspect
import re
import struct
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import style  # noqa: E402  (same directory, on sys.path above)
import data   # noqa: E402

N_FIGURES = 5


def _module_paths(number):
    """Candidate files for fig<N>: exact fig<N>.py first, then fig<N>_*.py."""
    exact = HERE / f"fig{number}.py"
    if exact.exists():
        return [exact]
    return sorted(p for p in HERE.glob(f"fig{number}_*.py")
                  if p.name != f"fig{number}.py")


def _load_module(path, number):
    name = f"f6m_fig{number}_{path.stem}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _call_build(mod, camp, out_dir):
    """Call mod.build() passing camp/out_dir only when the signature wants them."""
    fn = getattr(mod, "build", None)
    if fn is None:
        raise AttributeError(f"{mod.__name__}: no build() function")
    if not callable(fn):
        raise TypeError(f"{mod.__name__}.build is not callable")
    kwargs = {}
    try:
        params = inspect.signature(fn).parameters
    except (TypeError, ValueError):
        params = {}
    if "camp" in params:
        kwargs["camp"] = camp
    if "out_dir" in params:
        kwargs["out_dir"] = out_dir
    required = [p.name for p in params.values()
                if p.default is inspect.Parameter.empty
                and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD,
                               p.KEYWORD_ONLY)
                and p.name not in kwargs]
    if required:
        raise TypeError(
            f"{mod.__name__}.build() needs mandatory argument(s) {required}; "
            "make them optional (camp=None, out_dir=None)")
    return fn(**kwargs)


def _png_dims(path):
    """(width, height) read straight from the PNG IHDR chunk."""
    try:
        with open(path, "rb") as f:
            head = f.read(24)
        if head[:8] == b"\x89PNG\r\n\x1a\n":
            w, h = struct.unpack(">II", head[16:24])
            return w, h
    except OSError:
        pass
    return None


def _pdf_size_pt(path):
    """(width_pt, height_pt) from the first /MediaBox in the PDF."""
    try:
        blob = path.read_bytes()
    except OSError:
        return None
    m = re.search(rb"/MediaBox\s*\[\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)",
                  blob)
    if not m:
        return None
    x0, y0, x1, y1 = (float(v) for v in m.groups())
    return abs(x1 - x0), abs(y1 - y0)


def _format_one(path):
    kb = path.stat().st_size / 1024
    dims = ""
    if path.suffix == ".png":
        wh = _png_dims(path)
        if wh:
            dims = f"  {wh[0]}x{wh[1]} px"
    elif path.suffix == ".pdf":
        wh = _pdf_size_pt(path)
        if wh:
            dims = (f"  {wh[0] / 72:.1f}x{wh[1] / 72:.1f} in "
                    f"({wh[0]:.0f}x{wh[1]:.0f} pt)")
    return f"  {path}  ({kb:.0f} KB{dims})"


def _flatten_returned(returned):
    """Nested lists/tuples of Path/str (e.g. ``[save(fig, ...)]`` where save()
    returns ``(png, pdf)``) -> flat list of Path; anything else is ignored."""
    out = []

    def walk(item):
        if item is None:
            return
        if isinstance(item, (str, Path)):
            out.append(Path(item))
        elif isinstance(item, (list, tuple, set)):
            for sub in item:
                walk(sub)

    walk(returned)
    return out


def _collect(returned, out_dir, before, claimed):
    """Paths to report for one module: whatever its build() returned plus files
    it is responsible for in the output directory (new or rewritten since the
    run started), each path reported exactly once across the whole run."""
    paths = _flatten_returned(returned)
    for path in sorted(Path(out_dir).glob("*")):
        if path.suffix not in (".png", ".pdf"):
            continue
        if before.get(path) != path.stat().st_mtime_ns:
            paths.append(path)
    uniq = []
    for p in paths:
        p = Path(p)
        if p.exists() and p not in claimed and p not in uniq:
            uniq.append(p)
    return uniq


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", default=None,
                    help="comma-separated figure numbers, e.g. --only 1,3")
    ap.add_argument("--camp", default=str(data.CAMPAIGN),
                    help="campaign root (default: %(default)s)")
    ap.add_argument("--out", default=str(style.OUT_DIR),
                    help="output directory (default: %(default)s)")
    args = ap.parse_args(argv)

    only = None
    if args.only:
        only = {int(tok) for tok in args.only.replace(" ", "").split(",") if tok}
        bad = only - set(range(1, N_FIGURES + 1))
        if bad:
            ap.error(f"--only accepts 1..{N_FIGURES}, got {sorted(bad)}")
    camp = Path(args.camp).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    style.apply_style()

    print(f"campaign   : {camp}")
    print(f"output     : {out_dir}")
    print(f"smoothing  : rolling mean over {data.DEFAULT_WINDOW:,} env steps "
          f"(data.DEFAULT_WINDOW)")
    print(f"runs known : {len(data.RUN_META)} (scaling "
          f"{len(data.runs_of('scaling'))}, official "
          f"{len(data.runs_of('official'))})")
    problems = data.audit()
    if problems:
        print("RUN_META audit: %d problem(s)" % len(problems))
        for p in problems:
            print(f"  ! {p}")
    else:
        print("RUN_META audit: OK (14 runs match the curve CSVs)")
    print()

    before = {p: p.stat().st_mtime_ns for p in out_dir.glob("*")
              if p.suffix in (".png", ".pdf")}
    claimed = set()

    built, skipped, failed, products = [], [], [], []
    for number in range(1, N_FIGURES + 1):
        if only is not None and number not in only:
            continue
        paths = _module_paths(number)
        if not paths:
            print(f"[fig{number}] warning: no fig{number}.py / fig{number}_*.py "
                  f"module in {HERE} - skipped", flush=True)
            skipped.append(number)
            continue
        for path in paths:
            label = path.name
            try:
                mod = _load_module(path, number)
                returned = _call_build(mod, camp, out_dir)
            except Exception:
                sys.stdout.flush()
                print(f"[fig{number}] FAILED: {label}", file=sys.stderr)
                traceback.print_exc()
                failed.append(label)
                continue
            got = _collect(returned, out_dir, before, claimed)
            claimed.update(got)
            if got:
                print(f"[fig{number}] {label} -> {len(got)} file(s)")
                for p in got:
                    print(_format_one(p))
                products.extend(got)
                built.append(label)
            else:
                print(f"[fig{number}] {label} ran but wrote nothing into "
                      f"{out_dir}  (allowed only for a deliberate skip)")
                built.append(label)
            sys.stdout.flush()

    print()
    print(f"figure modules: {len(built)} built, {len(skipped)} missing "
          f"({', '.join('fig%d' % n for n in skipped) or '-'}), "
          f"{len(failed)} failed")
    if products:
        products = sorted(set(products))
        print(f"products ({len(products)}):")
        for p in products:
            print(_format_one(p))
    else:
        print("products: none")
    if failed:
        sys.stdout.flush()
        print("failed modules: " + ", ".join(failed), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
