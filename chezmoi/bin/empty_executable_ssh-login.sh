#!/usr/bin/env bash
set -euo pipefail

# Check for the correct number of arguments.
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <username> <hostname>"
    exit 1
fi

# Parameterize username and hostname.
USERNAME="$1"
HOST="$2"

# Ensure 1Password CLI is logged in.
if ! op account get >/dev/null 2>&1; then
    echo "Please log in to 1Password CLI first using 'op signin'"
    exit 1
fi

# Retrieve credentials from 1Password.
PASSWORD=$(op read --account my.1password.com "op://Private/Okta - Level Home/password")
OTP=$(op item get --account my.1password.com "JumpCloud" --otp --vault Private)

# Use expect to automate the SSH login process.
expect <<EOF
    # Set timeout to unlimited so that the session does not close.
    set timeout -1
    # Start the SSH session with parameterized username and hostname.
    spawn ssh -tt -A -o ProxyCommand='ssh -tt -A ${USERNAME}@ctdev-bastion.level.co -W %h:%p' ${USERNAME}@${HOST}
    expect "Password:"
    send "$PASSWORD\r"
    expect "Verification code:"
    send "$OTP\r"
    # Optionally, wait for a prompt on the final host.
    # This regular expression is an example; adjust it to match the expected prompt.
    expect -re {[$#] }
    # Hand over the interactive session to you.
    interact
EOF
