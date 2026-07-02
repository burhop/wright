#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/hermes-plugin-lifecycle-common.sh"
configure_lifecycle_args "$@"

echo -e "${YELLOW}=== Testing Hermes Wright Plugin Update ===${NC}"
ensure_docker_image

HERMES_TEST_HOME="$(create_hermes_home)"
trap 'cleanup_hermes_home "$HERMES_TEST_HOME"' EXIT

log_step "Installing ${PLUGIN_IDENTIFIER} before update test..."
run_in_hermes_container "$HERMES_TEST_HOME" '
  set -euo pipefail
  '"$assert_hermes_version_command"'
  hermes plugins install "$WRIGHT_PLUGIN_IDENTIFIER" --enable
  '"$assert_plugin_installed_command"'
'

log_step "Updating ${PLUGIN_NAME} through Hermes..."
run_in_hermes_container "$HERMES_TEST_HOME" '
  set -euo pipefail
  '"$assert_hermes_version_command"'
  if [ ! -d "$HERMES_HOME/plugins/$WRIGHT_PLUGIN_NAME/.git" ]; then
    echo "Plugin $WRIGHT_PLUGIN_NAME was installed without .git metadata." >&2
    echo "Hermes plugins update requires the plugin directory itself to be a git checkout." >&2
    echo "Install from a repository with plugin.yaml at the repo root, or remove and reinstall subdirectory plugins." >&2
    exit 1
  fi
  hermes plugins update "$WRIGHT_PLUGIN_NAME"
  '"$assert_plugin_installed_command"'
'

log_ok "Hermes plugin update path works for ${PLUGIN_NAME}."
