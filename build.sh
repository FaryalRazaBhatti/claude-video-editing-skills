#!/bin/sh
# Copy the shared engine and fonts into every skill folder, then zip each skill.
set -e
cd "$(dirname "$0")"
mkdir -p dist
for s in skills/*/; do
  name=$(basename "$s")
  rm -rf "$s/scripts/reelkit" "$s/fonts"
  cp -r lib/reelkit "$s/scripts/reelkit"
  cp -r lib/fonts "$s/fonts"
  find "$s" -name "__pycache__" -prune -exec rm -rf {} +
  (cd skills && rm -f "../dist/$name.zip" && zip -qr "../dist/$name.zip" "$name")
done
ls -la dist
