#!/usr/bin/env bash

# Run the lint command and capture output
lint_output=$(mise x go -- golangci-lint run --fix ./... 2>&1)
lint_status=$?

# If lint failed (non-zero exit code)
if [ $lint_status -ne 0 ]; then
    echo "Lint found issues. Extracting files..."
    
    # Extract unique file paths from the lint output
    files=$(echo "$lint_output" | grep -o '[[:alnum:]/_.-]\+\.go:[0-9]\+:[0-9]\+' | cut -d':' -f1 | sort -u)
    
    if [ -z "$files" ]; then
        echo "No Go files found in the lint output. Copying just the lint output."
        echo -e "$lint_output" | pbcopy
        exit 1
    fi
    
    # Join the file paths with spaces for use in the yek command
    file_list=$(echo "$files" | tr '\n' ' ')
    
    echo "Reading files: $file_list"
    
    # Get the contents of those files using yek
    file_contents=$(yek $file_list 2>/dev/null)
    if [ $? -ne 0 ]; then
        echo "Error reading files. Copying just the lint output."
        echo -e "$lint_output" | pbcopy
        exit 1
    fi
    
    # Combine lint output and file contents
    combined="LINT FAILURES:\n\n$lint_output\n\nFILE CONTENTS:\n\n$file_contents"
    
    # Copy to clipboard
    echo -e "$combined" | pbcopy
    
    echo "Lint failures and file contents copied to clipboard."
else
    echo "Lint passed successfully. Nothing to copy."
fi
