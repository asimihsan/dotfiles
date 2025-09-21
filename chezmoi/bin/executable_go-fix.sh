#!/usr/bin/env bash

set -euxo pipefail

# A. Inspect persistent go env (NOT the shell env)
which go
mise ls go
go version
go env GOROOT GOPATH GOENV GOTOOLCHAIN GOEXPERIMENT GOFLAGS

# B. If GOEXPERIMENT or GOFLAGS is non-empty, clear them
go env -u GOEXPERIMENT || true
go env -u GOFLAGS || true

# C. Make sure GOROOT is not forcibly set; if it is, unset it
go env -u GOROOT || true

# D. Clean caches so std can be rebuilt consistently
go clean -cache -testcache -modcache
# Optional but helpful if things are really wedged:
# rm -rf "$(go env GOROOT)/pkg" 2>/dev/null || true

# E. Pin a single Go binary everywhere (shell + editor).
# Given your mise install, pin to exactly 1.25.1:
mise install go@1.25.1
mise use -g go@1.25.1

# F. Verify the single path used everywhere
which go
go env GOROOT
go version

# G. Minimal sanity check: should build cleanly if env is fixed
tmpdir="$(mktemp -d)"; cd "$tmpdir"
go mod init example.com/tmp
cat > main.go <<'EOF'
package main
import (
    "context"
    "fmt"
)
func main() { _ = context.Background(); fmt.Println("ok") }
EOF
go build .
echo "OK"
