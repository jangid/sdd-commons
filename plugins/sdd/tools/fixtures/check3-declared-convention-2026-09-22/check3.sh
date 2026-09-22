#!/bin/sh
# Check 3 (test coverage per spec) of the chunk-close layer, run over one
# fixture chunk under the declared-convention clause of
# docs/spec/chunk-close-review.md §Checklist. Run from the repository root:
#
#   sh plugins/sdd/tools/fixtures/check3-declared-convention-2026-09-22/check3.sh <chunk.md>
#
# 1. Derives the module set the convention names with the one command the
#    spec states, and diffs it against derived-set.txt beside this script
#    (a reference value: the diff is printed, never patched).
# 2. Reads the chunk's `**Module**:` line and decides Check 3 for it:
#    in the derived set -> covered, no advisory (exit 0);
#    otherwise -> advisory unless a test file imports from it (exit 2).
# Exit 1 is a usage error or a derivation that no longer matches the file.
set -u
here=$(cd "$(dirname "$0")" && pwd)
chunk=${1:?usage: check3.sh <chunk.md>}
derived=$({ grep -ohE '(^|`|python3 )plugins/sdd/tools/[a-z-]+\.py' CLAUDE.md;
  grep -ohE '^[[:space:]]*entry: (python3 )?[^ ]+\.py' .pre-commit-config.yaml; } \
  | grep -oE '[^ `]+\.py' | sort -u)
echo "derived set:"; printf '  %s\n' $derived
if [ "$derived" != "$(cat "$here/derived-set.txt")" ]; then
  echo "derived set differs from derived-set.txt (reference value on 2026-09-22)"; exit 1
fi
module=$(grep -oE '^\*\*Module\*\*: `[^`]+`' "$chunk" | sed 's/.*`\(.*\)`/\1/')
[ -n "$module" ] || { echo "no **Module**: line in $chunk"; exit 1; }
if printf '%s\n' "$derived" | grep -qxF "$module"; then
  echo "Check 3 ($module): pass — named by the declared convention, no advisory"; exit 0
fi
stem=$(basename "$module" .py | tr '-' '_')
if grep -rlE "^(import|from) $stem\b" --include='test_*.py' --include='*_test.py' . 2>/dev/null | grep -q .; then
  echo "Check 3 ($module): pass — a test file imports from it"; exit 0
fi
echo "Check 3 ($module): advisory — outside the derived set and no test file imports from it"; exit 2
