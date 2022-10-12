#!/usr/bin/env bash

set -euo pipefail

#/usr/local/bin/wakeonlan 00:11:32:EC:EF:A7
/sbin/ping -o -c 3 -t 5 snail.local

/usr/bin/osascript <<EOF
mount volume "smb://wrongtalk@snail.local/Incoming"
mount volume "smb://wrongtalk@snail.local/OldHardDrives"
mount volume "smb://wrongtalk@snail.local/SouthEast01"
mount volume "smb://wrongtalk@snail.local/archivebox"
mount volume "smb://wrongtalk@snail.local/dump"
mount volume "smb://wrongtalk@snail.local/dump2"
mount volume "smb://wrongtalk@snail.local/git"
mount volume "smb://wrongtalk@snail.local/minio"
EOF
