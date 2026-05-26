int main() {
    int selector;
    int resultado;
    selector = 2;
    resultado = 0;

    switch (selector) {
        case 1:
            resultado = 100;
        case 2:
            resultado = 200;
        default:
            resultado = 999;
    }
    printf("Resultado final del SWITCH: %d\n", resultado);
}
