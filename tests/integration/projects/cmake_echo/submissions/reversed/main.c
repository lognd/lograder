#include <stdio.h>

int main(int argc, char *argv[]) {
    for (int i = argc - 1; i >= 1; i--) {
        if (i < argc - 1) printf(" ");
        printf("%s", argv[i]);
    }
    printf("\n");
    return 0;
}
