#!/usr/bin/env bash
# Block (without an LLM) until a shared coordination file changes, then exit.
# Usage: scripts/wait-change.sh <file> [timeout_s=3600] [state_regex]
#   state_regex: for JSON status files, only return when "state" matches it.
# Exit 0 = changed (prints new sha), 2 = timeout. The last seen hash is kept
# locally, so a change made while the caller was busy is reported at once.
set -euo pipefail
file=$1; timeout=${2:-3600}; states=${3:-}; interval=5
seen_dir="${XDG_CACHE_HOME:-$HOME/.cache}/isaac-bus"; mkdir -p "$seen_dir"
seen="$seen_dir/$(basename "$file").sha"

digest() { [ -f "$file" ] && shasum -a 256 "$file" | cut -d' ' -f1 || echo missing; }
matches() {
    [ -z "$states" ] && return 0
    grep -Eq "\"state\"[[:space:]]*:[[:space:]]*\"($states)\"" "$file" 2>/dev/null
}

deadline=$((SECONDS + timeout))
while [ $SECONDS -lt $deadline ]; do
    now=$(digest)
    if [ "$now" != "$(cat "$seen" 2>/dev/null)" ]; then
        sleep 2  # let a non-atomic writer finish
        if [ "$(digest)" = "$now" ] && matches; then
            echo "$now" > "$seen"; echo "changed $file $now"; exit 0
        fi
    fi
    sleep $interval
done
echo "timeout $file"; exit 2
