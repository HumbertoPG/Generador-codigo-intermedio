int main() {
    int x;
    int y;
    x = 0;
    y = 10;

    for (x = 1; x < 5; x = x + 1;) {
        y = y * 2;
    }
    printf("Resultado final del ciclo FOR (y): %d\n", y);
}
