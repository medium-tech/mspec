#include <stdio.h>
#include <string.h>

#include "lingolib.h"


static const char *HELP =
    "usage: lingolib [--help] <command> [args]\n"
    "\n"
    "commands:\n"
    "  exe <path>    load, parse, execute an exe spec and print result\n"
    "\n"
    "supported specs: exe\n";

int main(int argc, char *argv[]) {
    if (argc < 2
            || strcmp(argv[1], "--help") == 0
            || strcmp(argv[1], "-h") == 0) {
        printf("%s", HELP);
        return 0;
    }
    if (strcmp(argv[1], "exe") == 0) {
        if (argc < 3) {
            fprintf(stderr, "error: exe requires a path argument\n");
            return 1;
        }
        LingoExeDoc doc = lingolib_parse_exe(argv[2]);
        if (doc.lingo.error) {
            fprintf(stderr, "error: %s\n", doc.lingo.error_msg);
            return 1;
        }
        const char *result = lingolib_execute_exe(&doc);
        if (!result) {
            fprintf(stderr, "error: exe execution failed\n");
            return 1;
        }
        printf("%s\n", result);
        return 0;
    }
    fprintf(stderr, "error: unknown command: %s\n", argv[1]);
    return 1;
}
