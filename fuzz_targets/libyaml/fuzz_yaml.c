#define _GNU_SOURCE
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <yaml.h>

#define MAX_SIZE 4096

int main(int argc, char **argv) {
    uint8_t buf[MAX_SIZE];
    ssize_t len;

    while (__AFL_LOOP(1000)) {
        len = read(0, buf, MAX_SIZE);
        if (len <= 0) break;

        yaml_parser_t parser;
        yaml_document_t document;

        if (!yaml_parser_initialize(&parser)) continue;

        yaml_parser_set_input_string(&parser, buf, len);
        yaml_parser_load(&parser, &document);

        yaml_document_delete(&document);
        yaml_parser_delete(&parser);
    }

    return 0;
}
