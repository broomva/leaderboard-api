#!/usr/bin/env bash
# gates/10-no-raw-body.sh — unvalidated request bodies never reach a file or a log.
bad="$(git diff "$FACTORY_BASE" -- app | grep -E '^\+' | grep -nE '\.body\(\)|\.stream\(\)|await request\.json\(\)' || true)"
if [ -n "$bad" ]; then echo "The change reads the raw request body; use the validated pydantic model instead:"; echo "$bad"; exit 1; fi
echo "No raw request bodies."
