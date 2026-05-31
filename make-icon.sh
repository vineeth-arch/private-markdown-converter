#!/bin/bash
set -euo pipefail

SOURCE_PNG="${1:-}"
if [[ -z "$SOURCE_PNG" ]] || [[ ! -f "$SOURCE_PNG" ]]; then
  echo "Usage: bash make-icon.sh path/to/image.png"
  echo "Image should be at least 1024x1024 pixels."
  exit 1
fi

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ICONSET_DIR="$PROJECT_DIR/assets/icon.iconset"
OUTPUT_ICNS="$PROJECT_DIR/assets/icon.icns"

mkdir -p "$ICONSET_DIR"

declare -A SIZES=(
  ["icon_16x16.png"]=16
  ["icon_16x16@2x.png"]=32
  ["icon_32x32.png"]=32
  ["icon_32x32@2x.png"]=64
  ["icon_128x128.png"]=128
  ["icon_128x128@2x.png"]=256
  ["icon_256x256.png"]=256
  ["icon_256x256@2x.png"]=512
  ["icon_512x512.png"]=512
  ["icon_512x512@2x.png"]=1024
)

for filename in "${!SIZES[@]}"; do
  size="${SIZES[$filename]}"
  sips -z "$size" "$size" "$SOURCE_PNG" --out "$ICONSET_DIR/$filename" >/dev/null 2>&1
done

iconutil -c icns "$ICONSET_DIR" -o "$OUTPUT_ICNS"
rm -rf "$ICONSET_DIR"

echo "Icon created at: $OUTPUT_ICNS"
echo "Now run: bash build-app.sh"
