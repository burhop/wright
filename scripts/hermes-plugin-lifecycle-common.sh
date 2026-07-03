#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

IMAGE_TAG="${WRIGHT_DOCKER_IMAGE:-wright:test}"
PLUGIN_NAME="${WRIGHT_PLUGIN_NAME:-wright}"
PLUGIN_REPO_URL="${WRIGHT_PLUGIN_REPO_URL:-https://github.com/burhop/wright}"
PLUGIN_REF="${WRIGHT_PLUGIN_REF:-dev}"
PLUGIN_SUBDIR="${WRIGHT_PLUGIN_SUBDIR:-hermes-plugin-wright}"
PLUGIN_SOURCE_MODE="${WRIGHT_PLUGIN_SOURCE_MODE:-subdir}"
PLUGIN_IDENTIFIER_OVERRIDE="${WRIGHT_PLUGIN_IDENTIFIER:-}"
HERMES_EXPECTED_VERSION="${WRIGHT_HERMES_EXPECTED_VERSION:-0.18.0}"
PLUGIN_IDENTIFIER=""

# Root mirror identifier pattern: ${PLUGIN_REPO_URL}/tree/${PLUGIN_REF}
# Subdirectory identifier pattern: ${PLUGIN_REPO_URL}/tree/${PLUGIN_REF}/${PLUGIN_SUBDIR}
build_plugin_identifier() {
  if [ -n "$PLUGIN_IDENTIFIER_OVERRIDE" ]; then
    printf '%s' "$PLUGIN_IDENTIFIER_OVERRIDE"
    return
  fi

  case "$PLUGIN_SOURCE_MODE" in
    root)
      printf '%s/tree/%s' "$PLUGIN_REPO_URL" "$PLUGIN_REF"
      ;;
    subdir)
      printf '%s/tree/%s/%s' "$PLUGIN_REPO_URL" "$PLUGIN_REF" "$PLUGIN_SUBDIR"
      ;;
    *)
      log_error "WRIGHT_PLUGIN_SOURCE_MODE must be root or subdir; got $PLUGIN_SOURCE_MODE"
      exit 2
      ;;
  esac
}

log_step() {
  echo -e "\n${YELLOW}$1${NC}"
}

log_ok() {
  echo -e "${GREEN}✓ $1${NC}"
}

log_error() {
  echo -e "${RED}✗ $1${NC}"
}

print_lifecycle_usage() {
  cat <<USAGE
Usage: $0 [--ref dev|main] [--dev] [--main] [--repo-url URL] [--subdir PATH] [--mirror-root] [--identifier IDENTIFIER]

Options:
  --mirror-root          Install from the repository root, e.g. https://github.com/burhop/hermes-plugin-wright/tree/dev.
  --subdir PATH          Install from a monorepo subdirectory, default: hermes-plugin-wright.
  --repo-url URL         Repository URL, default: https://github.com/burhop/wright.
  --ref dev|main         Branch to test, default: dev.
  --identifier VALUE     Exact Hermes plugin identifier, bypassing repo/ref/subdir construction.
USAGE
}

configure_lifecycle_args() {
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --ref)
        if [ "$#" -lt 2 ]; then
          log_error "--ref requires dev or main"
          exit 2
        fi
        PLUGIN_REF="$2"
        shift 2
        ;;
      --dev)
        PLUGIN_REF="dev"
        shift
        ;;
      --main)
        PLUGIN_REF="main"
        shift
        ;;
      --repo-url)
        if [ "$#" -lt 2 ]; then
          log_error "--repo-url requires a GitHub repository URL"
          exit 2
        fi
        PLUGIN_REPO_URL="$2"
        shift 2
        ;;
      --subdir)
        if [ "$#" -lt 2 ]; then
          log_error "--subdir requires a plugin subdirectory path"
          exit 2
        fi
        PLUGIN_SOURCE_MODE="subdir"
        PLUGIN_SUBDIR="$2"
        shift 2
        ;;
      --mirror-root)
        PLUGIN_SOURCE_MODE="root"
        shift
        ;;
      --identifier)
        if [ "$#" -lt 2 ]; then
          log_error "--identifier requires a Hermes plugin identifier"
          exit 2
        fi
        PLUGIN_IDENTIFIER_OVERRIDE="$2"
        shift 2
        ;;
      -h|--help)
        print_lifecycle_usage
        exit 0
        ;;
      *)
        log_error "Unknown option: $1"
        print_lifecycle_usage >&2
        exit 2
        ;;
    esac
  done

  case "$PLUGIN_REF" in
    dev|main) ;;
    *)
      log_error "WRIGHT_PLUGIN_REF/--ref must be dev or main; got $PLUGIN_REF"
      exit 2
      ;;
  esac

  case "$PLUGIN_SOURCE_MODE" in
    root|subdir) ;;
    *)
      log_error "WRIGHT_PLUGIN_SOURCE_MODE must be root or subdir; got $PLUGIN_SOURCE_MODE"
      exit 2
      ;;
  esac

  PLUGIN_IDENTIFIER="$(build_plugin_identifier)"
}

ensure_docker_image() {
  if [ "${WRIGHT_DOCKER_BUILD:-0}" = "1" ]; then
    log_step "Building Docker image ${IMAGE_TAG}..."
    docker build -t "$IMAGE_TAG" -f "$ROOT_DIR/docker/Dockerfile" "$ROOT_DIR"
    return
  fi

  if docker image inspect "$IMAGE_TAG" >/dev/null 2>&1; then
    log_ok "Using existing Docker image ${IMAGE_TAG}."
    return
  fi

  if [ "${WRIGHT_DOCKER_SKIP_BUILD:-0}" = "1" ]; then
    log_error "Docker image ${IMAGE_TAG} does not exist and WRIGHT_DOCKER_SKIP_BUILD=1 is set."
    exit 1
  fi

  log_step "Docker image ${IMAGE_TAG} not found; building it..."
  docker build -t "$IMAGE_TAG" -f "$ROOT_DIR/docker/Dockerfile" "$ROOT_DIR"
}

create_hermes_home() {
  mktemp -d "${TMPDIR:-/tmp}/wright-hermes-plugin-test.XXXXXX"
}

cleanup_hermes_home() {
  local hermes_home="$1"
  if [ "${WRIGHT_KEEP_TEST_HOME:-0}" = "1" ]; then
    echo "Keeping test Hermes home: ${hermes_home}"
    return
  fi
  rm -rf "$hermes_home"
}

run_in_hermes_container() {
  local hermes_home="$1"
  shift

  docker run --rm \
    --entrypoint /bin/bash \
    -e HOME=/home/agent \
    -e HERMES_HOME=/tmp/hermes-home \
    -e WRIGHT_PLUGIN_NAME="$PLUGIN_NAME" \
    -e WRIGHT_PLUGIN_IDENTIFIER="$PLUGIN_IDENTIFIER" \
    -e WRIGHT_HERMES_EXPECTED_VERSION="$HERMES_EXPECTED_VERSION" \
    -v "$hermes_home:/tmp/hermes-home" \
    -v "$ROOT_DIR:/wright-src:ro" \
    "$IMAGE_TAG" \
    -c "$*"
}

assert_hermes_version_command='
  hermes_version="$(hermes --version | head -1)"
  echo "$hermes_version"
  case "$hermes_version" in
    *"v$WRIGHT_HERMES_EXPECTED_VERSION"*) ;;
    *)
      echo "Expected Hermes v$WRIGHT_HERMES_EXPECTED_VERSION in the test container." >&2
      exit 1
      ;;
  esac
'

assert_plugin_installed_command='
  test -d "$HERMES_HOME/plugins/$WRIGHT_PLUGIN_NAME"
  test -f "$HERMES_HOME/plugins/$WRIGHT_PLUGIN_NAME/plugin.yaml"
  grep -q "name: $WRIGHT_PLUGIN_NAME" "$HERMES_HOME/plugins/$WRIGHT_PLUGIN_NAME/plugin.yaml"
  hermes plugins list --user --plain | grep -q "$WRIGHT_PLUGIN_NAME"
'
