int fibonacci(int n) {
    int a;
    int b;
    int c;
    int i;
    a = 0;
    b = 1;
    i = 2;
    if (n == 0) {
        return a;
    }
    while (i <= n) {
        c = a + b;
        a = b;
        b = c;
        i = i + 1;
    }
    return b;
}

int main() {
    int posicion;
    int res;
    posicion = 7;
    res = fibonacci(posicion);
    printf("El numero de Fibonacci en la posicion 7 es: %d\n", res);
    return 0;
}
