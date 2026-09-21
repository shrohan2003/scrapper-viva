#!/bin/sh
# Run with `sh START_HERE.sh` or `./START_HERE.sh`.
cd "$(dirname "$0")" || exit 1

status=1
found_python=false
for candidate in python3 python /opt/homebrew/bin/python3 /usr/local/bin/python3 python3.14 python3.13 python3.12 python3.11; do
    if command -v "$candidate" >/dev/null 2>&1 &&
       "$candidate" -c 'import sys; sys.exit(sys.version_info < (3, 11))' >/dev/null 2>&1; then
        found_python=true
        "$candidate" start.py "$@"
        status=$?
        break
    fi
done

if [ "$found_python" = false ]; then
    echo "Python 3.11 or newer was not found."
    echo "Install Python from https://www.python.org/downloads/ and run this file again."
    echo "On Linux, install Python 3.11+ and its venv package with your package manager."
fi

if [ "$#" -eq 0 ] && [ -t 0 ]; then
    printf '\nPress Enter to close...'
    read -r answer
fi
exit "$status"
