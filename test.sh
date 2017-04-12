#! /bin/bash

# Test script that sets environmental variables, then launches the dir-index.cgi script

# To run:
#   cd <main directory of repo>
#   test.sh > SampleData/test.html

export DOCUMENT_ROOT="./SampleData/"
export PATH_INFO="releases/17.01.0/targets/ar71xx/generic/"

perl dir-index.cgi
