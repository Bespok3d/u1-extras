#!/usr/bin/env bash
# This repo's own gate: it must pass from this repo's root, with no sibling repo cloned except
# lib_bespok3d. Exits non-zero on any failure.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# The shared gate helpers and the detectors that enforce a workspace-wide rule live in one place.
# See lib_bespok3d/tooling/README.md. This is the only line that knows where they are.
B3D_TOOLING="${B3D_TOOLING:-$REPO_ROOT/lib_bespok3d/tooling}"
# shellcheck source=/dev/null
. "$B3D_TOOLING/gate-lib.sh"

cd "$REPO_ROOT" || exit 1

GCOL_DIR="$REPO_ROOT/u1-gcode-colors"

echo ""
echo "u1-extras gate"

b3d_python_tools

run_check "pytest (u1-gcode-colors)"  pytest_in_dir "$GCOL_DIR" tests
run_check "ruff (u1-gcode-colors)"    ruff_in_dir "$GCOL_DIR" files tests
# The moonraker component shell imports moonraker, so it is ruff-only; the pure mapping module
# carries the type coverage.
run_check "mypy (u1-gcode-colors)"    mypy_in_dir "$GCOL_DIR" files/moonraker/gcode_preview_color_map.py

workflow_pinning_check "$REPO_ROOT"
em_dash_check "$REPO_ROOT"
shellcheck_repo "$REPO_ROOT"

gate_summary || exit 1
