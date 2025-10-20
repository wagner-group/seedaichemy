#include <plist/plist.h>
#include <stdio.h>
#include <stdlib.h>

extern "C" int LLVMFuzzerTestOneInput(const unsigned char* data, size_t size)
{
    plist_t root_node = NULL;
    plist_from_bin(reinterpret_cast<const char*>(data), size, &root_node);
    plist_free(root_node);

    return 0;
}

// Adapter for AFL++
int main(int argc, char** argv) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <file>\n", argv[0]);
        return 1;
    }

    FILE* f = fopen(argv[1], "rb");
    if (!f) return 1;

    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    fseek(f, 0, SEEK_SET);

    unsigned char* buf = (unsigned char*)malloc(size);
    fread(buf, 1, size, f);
    fclose(f);

    LLVMFuzzerTestOneInput(buf, size);

    free(buf);
    return 0;
}

