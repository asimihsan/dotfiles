#!/bin/bash
# clean_logger.sh - Cleans control characters from input stream

# Force perl to run unbuffered
exec perl -pe '
    BEGIN { $| = 1 }  # Force immediate flush
    s/\r//g;                          # Remove carriage returns
    s/\e\[[0-9;]*[a-zA-Z]//g;         # Remove color codes
    s/\e\[[\x30-\x3F]*[\x20-\x2F]*[\x40-\x7E]//g; # Remove other control sequences
'
