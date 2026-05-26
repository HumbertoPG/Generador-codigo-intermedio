int main() {
    int contador;
    int suma;
    contador = 1;
    suma = 0;

    do {
        suma = suma + contador;
        contador = contador + 1;
    } while (contador <= 3);
    printf("Resultado final de DO/WHILE (suma): %d\n", suma);
}
