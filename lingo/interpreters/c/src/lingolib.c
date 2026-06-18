#include "lingolib.h"

#include <stdio.h>
#include <string.h>
#include <yaml.h>


typedef enum { CTX_ROOT, CTX_LINGO, CTX_MAIN, CTX_OTHER } Context;

LingoExeDoc lingolib_parse_exe(const char *path) {
    LingoExeDoc doc;
    memset(&doc, 0, sizeof(doc));

    FILE *f = fopen(path, "r");
    if (!f) {
        doc.lingo.error = 1;
        snprintf(doc.lingo.error_msg, sizeof(doc.lingo.error_msg),
                 "cannot open file: %s", path);
        return doc;
    }

    yaml_parser_t parser;
    yaml_event_t  event;
    yaml_parser_initialize(&parser);
    yaml_parser_set_input_file(&parser, f);

    Context ctx           = CTX_ROOT;
    int     depth         = 0;
    int     expect_key[3] = {0, 0, 0};
    char    key[256]      = "";

    for (;;) {
        if (!yaml_parser_parse(&parser, &event)) {
            doc.lingo.error = 1;
            snprintf(doc.lingo.error_msg, sizeof(doc.lingo.error_msg),
                     "yaml parse error");
            break;
        }

        switch (event.type) {
        case YAML_STREAM_END_EVENT:
        case YAML_DOCUMENT_END_EVENT:
            yaml_event_delete(&event);
            goto done;

        case YAML_MAPPING_START_EVENT:
            depth++;
            if (depth < 3) expect_key[depth] = 1;
            break;

        case YAML_MAPPING_END_EVENT:
            depth--;
            /* finished a nested mapping value; expect next key at parent */
            if (depth > 0 && depth < 3) expect_key[depth] = 1;
            if (depth == 1) ctx = CTX_ROOT;
            break;

        case YAML_SCALAR_EVENT: {
            const char *val = (const char *)event.data.scalar.value;
            if (depth == 1) {
                if (expect_key[1]) {
                    if      (strcmp(val, "lingo") == 0) ctx = CTX_LINGO;
                    else if (strcmp(val, "main")  == 0) ctx = CTX_MAIN;
                    else                                ctx = CTX_OTHER;
                    expect_key[1] = 0;
                }
            } else if (depth == 2) {
                if (expect_key[2]) {
                    strncpy(key, val, sizeof(key) - 1);
                    expect_key[2] = 0;
                } else {
                    if (ctx == CTX_LINGO) {
                        if (strcmp(key, "spec") == 0)
                            strncpy(doc.lingo.spec, val, sizeof(doc.lingo.spec) - 1);
                        else if (strcmp(key, "version") == 0)
                            strncpy(doc.lingo.version, val, sizeof(doc.lingo.version) - 1);
                    } else if (ctx == CTX_MAIN) {
                        if (strcmp(key, "str") == 0) {
                            strncpy(doc.main_str, val, sizeof(doc.main_str) - 1);
                            doc.has_main_str = 1;
                        }
                    }
                    key[0]        = '\0';
                    expect_key[2] = 1;
                }
            }
            break;
        }

        default:
            break;
        }
        yaml_event_delete(&event);
    }

done:
    yaml_parser_delete(&parser);
    fclose(f);
    return doc;
}

const char *lingolib_execute_exe(const LingoExeDoc *doc) {
    if (doc->has_main_str) return doc->main_str;
    return NULL;
}
