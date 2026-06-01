#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="Private Markdown Converter"
APP_PATH="$PROJECT_DIR/$APP_NAME.app"
ICON_SOURCE="$PROJECT_DIR/assets/icon.icns"
LEGACY_STOP_APP_PATH="$PROJECT_DIR/Stop Private Markdown Converter.app"

create_helper_script() {
  local destination="$1"
  local target_script="$2"
  local suppress_ui="${3:-0}"

  mkdir -p "$(dirname "$destination")"

  if [[ "$suppress_ui" == "1" ]]; then
    cat > "$destination" <<EOF
#!/bin/bash
set -euo pipefail

PMC_SUPPRESS_STOP_UI=1 bash "$target_script" >/dev/null 2>&1
EOF
  else
    cat > "$destination" <<EOF
#!/bin/bash
set -euo pipefail

bash "$target_script" >/dev/null 2>&1
EOF
  fi

  chmod +x "$destination"
}

apply_icon_if_present() {
  local app_path="$1"
  local icon_dest="$app_path/Contents/Resources/applet.icns"
  local asset_catalog="$app_path/Contents/Resources/Assets.car"

  rm -f "$asset_catalog"

  if [[ -f "$ICON_SOURCE" ]]; then
    cp "$ICON_SOURCE" "$icon_dest"
    echo "Custom icon applied to $(basename "$app_path")."
  else
    echo "No custom icon found for $(basename "$app_path") at assets/icon.icns - using default applet icon."
  fi
}

echo "Building $APP_NAME.app..."
rm -rf "$APP_PATH"
rm -rf "$LEGACY_STOP_APP_PATH"
osacompile -s -o "$APP_PATH" "$PROJECT_DIR/launcher.applescript"
create_helper_script \
  "$APP_PATH/Contents/Resources/scripts/launch-helper.sh" \
  "$PROJECT_DIR/launch.sh"
create_helper_script \
  "$APP_PATH/Contents/Resources/scripts/stop-helper.sh" \
  "$PROJECT_DIR/stop.sh" \
  "1"
apply_icon_if_present "$APP_PATH"
chmod +x "$APP_PATH/Contents/MacOS/applet"
echo "'$APP_NAME.app' created."

echo ""
echo "Done. '$APP_NAME.app' was created in the project root."
echo ""
echo "Next steps:"
echo "  1. Right-click -> Open '$APP_NAME.app' the first time"
echo "  2. Drag '$APP_NAME.app' to your Dock or Applications folder"
echo "  3. Quit the app from the Dock or app menu to stop the local service"
echo "  4. Re-run bash build-app.sh after moving the project folder or after major launcher updates"
