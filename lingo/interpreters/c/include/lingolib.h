#ifndef LINGOLIB_H
#define LINGOLIB_H


typedef struct {
	char spec[64];
	char version[64];
	int  error;
	char error_msg[256];
} LingoEnvelope;

typedef struct {
	LingoEnvelope lingo;
	char          main_str[256];
	int           has_main_str;
} LingoExeDoc;

/* parse an exe spec YAML file; check doc.lingo.error before using result */
LingoExeDoc lingolib_parse_exe(const char *path);

/* evaluate the main expression; returns NULL on failure */
const char *lingolib_execute_exe(const LingoExeDoc *doc);


#endif
