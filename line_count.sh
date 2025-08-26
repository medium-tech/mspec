find ./test-gen \
    -type d -name .venv -prune -o \
    -type d -name node_modules -prune -o \
    -type d -name playwright-report -prune -o \
    -type d -name test-results -prune -o \
    -type f -exec cat {} + | wc -l