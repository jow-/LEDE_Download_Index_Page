#! /bin/bash

# Test script that sets environmental variables, then launches the dir-index.cgi script
# Original script at: https://gist.github.com/jow-/743363c332d09cb58a60dd1f216b6ee4

# Script writes the two files into the test/ directory
#
# 1) targets.html shows the "targets" directory
# 2) directory.html displays a standard (non "target") directory

# Open the pages in a browser and reload after each run

# To run:
#   cd <main directory of repo>
#   sh test.sh

# Display a "target" directory with OpenWrt firmware binary files
#
export DOCUMENT_ROOT="./samples/"                   # becomes $phys
export PATH_INFO="releases/19.07.6/targets/x86/64/" # becomes $virt

perl dir-index.cgi >./test/targets.html

# Display a simple directory listing
#
export DOCUMENT_ROOT="./" # becomes $phys
export PATH_INFO="./"     # becomes $virt

perl dir-index.cgi >./test/directory.html

# Display 404 page
#
export DOCUMENT_ROOT="./glorph"                             # becomes $phys
export PATH_INFO="releases/17.01.0/targets/ar71xx/generic/" # becomes $virt

perl dir-index.cgi >./test/404.html

# Display JSON output
#
export DOCUMENT_ROOT="./samples"             # becomes $phys
export PATH_INFO="releases/19.07.6/targets/" # becomes $virt
export QUERY_STRING="json"

perl dir-index.cgi >./test/output.json
