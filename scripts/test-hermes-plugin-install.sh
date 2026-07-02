#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/hermes-plugin-lifecycle-common.sh"
configure_lifecycle_args "$@"

echo -e "${YELLOW}=== Testing Hermes Wright Plugin Install ===${NC}"
ensure_docker_image

HERMES_TEST_HOME="$(create_hermes_home)"
trap 'cleanup_hermes_home "$HERMES_TEST_HOME"' EXIT

log_step "Installing ${PLUGIN_IDENTIFIER} as a Hermes user plugin..."
run_in_hermes_container "$HERMES_TEST_HOME" '
  set -euo pipefail
  '"$assert_hermes_version_command"'
  hermes plugins install "$WRIGHT_PLUGIN_IDENTIFIER" --enable
  '"$assert_plugin_installed_command"'
'

log_ok "Hermes plugin install path works for ${PLUGIN_NAME}."
