#!/bin/bash

# A handy bash script for linux/osx to set your PYTHONPATH environment variable to include this repos.
# To use this script you need to 'source it' to update the environment of the shell that is sourcing it.
#
# Usage:
#  source  add_pypath.sh
#
REPO_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
export PYTHONPATH=$REPO_DIR/lib:$PYTHONPATH
