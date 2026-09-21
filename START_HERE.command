#!/bin/sh
cd "$(dirname "$0")" || exit 1

if [ ! -x ".venv/bin/python" ]; then
    echo "Create the virtual environment and install requirements first."
    printf "Press Enter to close..."
    read answer
    exit 1
fi

.venv/bin/python capture.py
status=$?

printf "\nPress Enter to close..."
read answer
exit "$status"