int factorial_rec(int n) {
    if (n <= 1) {
        return 1;
    }
    // Llamada recursiva directa multiplicada por n
    return n * factorial_rec(n - 1);
}

int main() {
    int resultado;
    resultado = factorial_rec(5);
    printf("Factorial recursivo de 5 es: %d\n", resultado);
    return 0;
}
