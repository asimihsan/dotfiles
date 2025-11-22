#!/usr/bin/env bash

# Script to set up mise post-install hook for fixing AWS CLI Python path issues
# This creates a hook that automatically fixes permissions after installing aws-cli or awscli

# Set up error handling
set -euo pipefail

# Define the hooks directory
HOOKS_DIR="$HOME/.config/mise/hooks"
HOOK_FILE="$HOOKS_DIR/post-install"

# Create the hooks directory if it doesn't exist
if [ ! -d "$HOOKS_DIR" ]; then
  echo "Creating mise hooks directory at $HOOKS_DIR..."
  mkdir -p "$HOOKS_DIR"
fi

# Create the post-install hook script
echo "Creating post-install hook script..."
cat > "$HOOK_FILE" << 'EOF'
#!/usr/bin/env bash

# This hook runs after any installation
# $1 = plugin name (e.g., "aws-cli" or "awscli")
# $2 = version installed

# Only process aws-cli and awscli plugins
if [[ "$1" == "aws-cli" || "$1" == "awscli" ]]; then
  pkg_path=$(mise where "$1")
  python_path="$pkg_path/aws-cli.pkg/Payload/aws-cli/python"
  
  if [ -x "$python_path" ]; then
    echo "Fixing $1 embedded Python permissions..."
    chmod -x "$python_path"
    echo "✅ Removed execute permission from $python_path"
  else
    echo "ℹ️ No executable Python found in $1 installation or already fixed"
  fi
fi
EOF

# Make the hook script executable
chmod +x "$HOOK_FILE"

echo "✅ Mise post-install hook created successfully at $HOOK_FILE"
echo "This hook will automatically fix AWS CLI Python path issues after installation"

# Fix existing installations
echo "Checking for existing AWS CLI installations to fix..."
for pkg in aws-cli awscli; do
  if command -v mise >/dev/null && mise where $pkg &>/dev/null; then
    python_path="$(mise where $pkg)/aws-cli.pkg/Payload/aws-cli/python"
    if [ -x "$python_path" ]; then
      echo "Fixing existing $pkg installation..."
      chmod -x "$python_path"
      echo "✅ Fixed $pkg embedded Python at $python_path"
    fi
  fi
done

echo "Done! Future and current AWS CLI installations will no longer cause Python path conflicts."
