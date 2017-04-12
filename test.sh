#! /bin/bash

# Test script that sets environmental variables, then launches the dir-index.cgi script
# Original script at: https://gist.github.com/jow-/743363c332d09cb58a60dd1f216b6ee4

# To run:
#   cd <main directory of repo>
#   test.sh > SampleData/index.html

export DOCUMENT_ROOT="./SampleData/"
export PATH_INFO="releases/17.01.0/targets/ar71xx/generic/"

perl dir-index.cgi
