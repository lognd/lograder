#include <stdio.h>
#include "grader.h"

int main(int argc, char *argv[]) {
    printf("version=%s\n", GRADER_VERSION);
    printf("add=%d\n", grader_add(3, 4));
    return 0;
}
