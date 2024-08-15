#!/usr/bin/env bash

set -euo pipefail

# Ensure 1Password CLI is logged in
if ! op account get >/dev/null 2>&1; then
    echo "Please log in to 1Password CLI first using 'op signin'"
    exit 1
fi

# Retrieve credentials from 1Password
PASSWORD=$(op read --account my.1password.com "op://Private/Okta - Level Home/password")
OTP=$(op item get --account my.1password.com "JumpCloud" --otp --vault Private)

# Use expect to automate the SSH login process
expect << EOF
spawn ssh  -A asim.ihsan@control.uswest2a.level.dev
expect "Password:"
send "$PASSWORD\r"
expect "Verification code:"
send "$OTP\r"
expect "$ "
interact
EOF
