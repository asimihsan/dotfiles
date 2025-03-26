#!/bin/bash

# Fast-to-Slow Go Linters Script
# Runs Go linters in order from fast to slow, eventually building up to golangci-lint

# Enable strict error handling
set -euo pipefail

# Default values
VERBOSE=false
FIX_MODE=true
STOP_ON_ERROR=false
TARGET_DIR="./..."
SKIP_LINTERS=""

# ANSI color codes for better output readability
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
BOLD="\033[1m"
RESET="\033[0m"

# Function to display colored output
print_header() {
  echo -e "\n${BLUE}${BOLD}==>${RESET} ${BOLD}$1${RESET}"
}

print_success() {
  echo -e "${GREEN}${BOLD}✓${RESET} $1"
}

print_warning() {
  echo -e "${YELLOW}${BOLD}!${RESET} $1"
}

print_error() {
  echo -e "${RED}${BOLD}✗${RESET} $1"
}

# Function for running linters through mise
run_linter() {
  local linter=$1
  local cmd=$2
  
  # Check if this linter should be skipped
  if [[ "$SKIP_LINTERS" == *"$linter"* ]]; then
    print_warning "Skipping $linter (as requested)"
    return 0
  fi
  
  print_header "Running $linter"
  
  if [ "$VERBOSE" = true ]; then
    set -x
  fi
  
  # Run the linter with environment setup
  if mise x -- bash -c "make envfile && source external-build.env && $cmd"; then
    if [ "$VERBOSE" = true ]; then
      set +x
    fi
    print_success "$linter completed successfully"
    return 0
  else
    local exit_code=$?
    if [ "$VERBOSE" = true ]; then
      set +x
    fi
    print_error "$linter failed with exit code $exit_code"
    if [ "$STOP_ON_ERROR" = true ]; then
      exit $exit_code
    fi
    return 1
  fi
}

# Function to create WSL configuration
create_wsl_config() {
  local config_file=".wsl.toml"
  
  if [ -f "$config_file" ]; then
    print_warning "Using existing WSL config: $config_file"
    return 0
  fi
  
  print_header "Creating WSL configuration"
  
  cat > "$config_file" << EOF
# WSL (WhiteSpace Linter) Configuration

# Strict append checks: only allow append of variables used on preceding line
strict-append = true

# Allow cuddling variable declarations together
allow-cuddle-declarations = true

# Force checking if err assignments are followed by a conditional checking that error
force-cuddle-err-check-and-assign = true

# Allow cuddle with assignments and calls (x = y followed by x.call())
allow-assign-and-call-cuddle = true

# Allow trailing comments at the end of blocks
allow-trailing-comment = true

# Allow multiple comments at the beginning of a block with blank lines between
allow-separated-leading-comment = true

# Force case blocks with at least this many lines to have a trailing newline
force-case-trailing-whitespace-limit = 2

# Error variable names that will be checked with force-cuddle-err-check-and-assign
error-variable-names = ["err", "error"]

# Force short declarations to only cuddle with other short declarations
force-exclusive-short-declarations = true
EOF

  print_success "Created WSL config: $config_file"
  return 0
}

# Function to check if a command is available
check_command() {
  local cmd=$1
  if ! mise x -- bash -c "command -v $cmd > /dev/null 2>&1"; then
    print_warning "Command '$cmd' not found. Some linters may not work."
    return 1
  fi
  return 0
}

# Display usage information
usage() {
  echo "Usage: $0 [options]"
  echo ""
  echo "Options:"
  echo "  -h, --help                Show this help message"
  echo "  -v, --verbose             Enable verbose output"
  echo "  -n, --no-fix              Disable fix mode (default: enabled)"
  echo "  -d, --dir DIR             Specify target directory (default: ./...)"
  echo "  -s, --stop                Stop on first error"
  echo "  -k, --skip LINTERS        Skip specified linters (comma-separated)"
  echo "                            Available linters: vet,revive,errcheck,wsl,staticcheck,golangci"
  echo "  --create-revive-config    Create a revive config file based on golangci-lint settings"
  echo "  --create-wsl-config       Create a WSL whitespace linter config file"
  echo ""
  echo "Examples:"
  echo "  $0 --verbose --dir ./pkg/... --skip errcheck,staticcheck"
  echo "  $0 --create-revive-config"
  echo "  $0 --create-wsl-config"
  echo ""
  echo "Note:"
  echo "  Linters run hierarchically - each linter only runs if the previous one passes."
  exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)
      usage
      ;;
    -v|--verbose)
      VERBOSE=true
      shift
      ;;
    -n|--no-fix)
      FIX_MODE=false
      shift
      ;;
    -d|--dir)
      TARGET_DIR="$2"
      shift 2
      ;;
    -s|--stop)
      STOP_ON_ERROR=true
      shift
      ;;
    -k|--skip)
      SKIP_LINTERS="$2"
      shift 2
      ;;
    --create-revive-config)
      # Create a revive config file based on golangci-lint settings
      create_revive_config
      exit 0
      ;;
    --create-wsl-config)
      # Create a WSL config file
      create_wsl_config
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      usage
      ;;
  esac
done

# Run linters in order from fast to slow (hierarchical - only proceed if previous passes)
RETURN_CODE=0

# 1. go vet (fastest, built-in)
if ! run_linter "vet" "go vet $TARGET_DIR"; then
  RETURN_CODE=1
  if [ "$STOP_ON_ERROR" = true ]; then
    exit $RETURN_CODE
  fi
  print_header "Stopping linting sequence due to 'go vet' failure"
  exit $RETURN_CODE
fi

# 2. revive (fast, replacement for golint)
# Using revive with formatting similar to golangci-lint style rules
if ! run_linter "revive" "revive -formatter stylish -exclude vendor/... -exclude 'api/...' -exclude 'assets/migrations/...' -exclude 'internal/generated/...' -exclude 'ui/...' -exclude 'web/...' -exclude 'vendor/...' -max-line-length 80 $TARGET_DIR"; then
  RETURN_CODE=1
  if [ "$STOP_ON_ERROR" = true ]; then
    exit $RETURN_CODE
  fi
  print_header "Stopping linting sequence due to 'revive' failure"
  exit $RETURN_CODE
fi

# 3. errcheck (checks for unchecked errors)
if ! run_linter "errcheck" "errcheck -exclude vendor/... $TARGET_DIR"; then
  RETURN_CODE=1
  if [ "$STOP_ON_ERROR" = true ]; then
    exit $RETURN_CODE
  fi
  print_header "Stopping linting sequence due to 'errcheck' failure"
  exit $RETURN_CODE
fi

# 4. wsl (whitespace linter for proper code formatting and readability)
if ! run_linter "wsl" "golangci-lint run --disable-all --enable=wsl --allow-parallel-runners $TARGET_DIR"; then
  RETURN_CODE=1
  if [ "$STOP_ON_ERROR" = true ]; then
    exit $RETURN_CODE
  fi
  print_header "Stopping linting sequence due to 'wsl' failure"
  exit $RETURN_CODE
fi

# 5. staticcheck (more comprehensive static analysis)
if ! run_linter "staticcheck" "staticcheck -checks all,-SA1019 $TARGET_DIR"; then
  RETURN_CODE=1
  if [ "$STOP_ON_ERROR" = true ]; then
    exit $RETURN_CODE
  fi
  print_header "Stopping linting sequence due to 'staticcheck' failure"
  exit $RETURN_CODE
fi

# 6. golangci-lint (most comprehensive, slowest)
GOLANGCI_CMD="golangci-lint run"
if [ "$FIX_MODE" = true ]; then
  GOLANGCI_CMD="$GOLANGCI_CMD --fix"
fi
GOLANGCI_CMD="$GOLANGCI_CMD $TARGET_DIR"

if ! run_linter "golangci" "$GOLANGCI_CMD"; then
  RETURN_CODE=1
  if [ "$STOP_ON_ERROR" = true ]; then
    exit $RETURN_CODE
  fi
fi

if [ $RETURN_CODE -eq 0 ]; then
  print_header "All linters completed successfully!"
else
  print_header "Linting completed with errors"
fi

exit $RETURN_CODE
