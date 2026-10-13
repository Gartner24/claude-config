# 0001. Add function

**Date**: 2026-10-13
**Status**: Proposed

## What you're agreeing to

- One file `calc.py` at the repo root with `add(a, b)`, which returns `a + b`.
- One test file `test_calc.py` at the repo root, run with `python3 -m unittest`.
- Python 3 standard library only, nothing to install.

## Requirements

**Acceptance criteria**:
- **AC-1**: `calc.add(a, b)` returns `a + b` for ints and floats: `add(2, 3) == 5`, `add(-1, 1) == 0`, `add(0.5, 0.25) == 0.75`.
- **AC-2**: `test_calc.py` uses `unittest`, imports `calc`, and covers the three cases of AC-1; `python3 -m unittest` in the repo root passes.

## Decision

**Chosen option**: a plain module function, no class, no input checks.

## Feature design

**Value sourcing**:

| Action | Value | Source |
|---|---|---|
| add | result | `a + b` of the two arguments |

**Key invariants**: no other file changes beyond `calc.py`, `test_calc.py` and the scope and spec bookkeeping.

**Security model**: none, no input crosses a trust boundary.

## Build plan

1. `calc.py` with `add(a, b)`, satisfies **AC-1**
2. `test_calc.py`, satisfies **AC-2**
