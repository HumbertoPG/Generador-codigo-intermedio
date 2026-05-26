int factorial(int n) {
    int f;
    int i;
    f = 1;
    i = 1;
    while (i <= n) {
        f = f * i;
        i = i + 1;
    }
    return f;
}

int main() {
    int num;
    int result;
    num = 5;
    result = factorial(num);
    printf("El factorial de 5 es: %d\n", result);
    return 0;
}
