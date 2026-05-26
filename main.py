                                                                          
                                                                              
                                                                    
import os
import llvmlite.binding as llvm_bind
import sys
import ply.lex as lex
import ply.yacc as yacc
from llvmlite import ir

                                                                                  
sys.path.append(os.getcwd())

try:
    import analisis
    from arbol import Program
except ImportError:
    print("Error: No se pudieron encontrar los archivos 'analisis.py' o 'arbol.py' en el directorio actual.")
    print("Asegúrate de ejecutar este script en la misma carpeta donde se encuentran dichos archivos.")
    sys.exit(1)

def compilar_carpeta(carpeta_origen, carpeta_destino):
    """
    Lee todos los archivos .c de la carpeta_origen, los procesa con el lexer,
    parser e IRGenerator definidos en analisis.py, y guarda los archivos .ll
    en la carpeta_destino.
    """
                                              
    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)
        print(f"Carpeta de destino creada: {carpeta_destino}")

                                                                                                
    sys.modules['__main__'].__file__ = 'main.py'

                                                                                             
    try:
        lexer = lex.lex(module=analisis)
        parser = yacc.yacc(module=analisis, write_tables=False, debug=False)
    except Exception as e:
        print(f"Error al inicializar el Lexer o Parser desde 'analisis.py': {e}")
        return

    archivos_c = [f for f in os.listdir(carpeta_origen) if f.endswith('.c')]

    if not archivos_c:
        print(f"No se encontraron archivos con extensión .c en la carpeta '{carpeta_origen}'.")
        return

    print(f"=== Iniciando compilación de {len(archivos_c)} archivo(s) ===")
    print(f"Origen:  {os.path.abspath(carpeta_origen)}")
    print(f"Destino: {os.path.abspath(carpeta_destino)}")

    for archivo in archivos_c:
        ruta_entrada = os.path.join(carpeta_origen, archivo)
        nombre_base = os.path.splitext(archivo)[0]
        ruta_salida = os.path.join(carpeta_destino, f"{nombre_base}.ll")

        print(f"Procesando '{archivo}'...", end="", flush=True)

        try:
            with open(ruta_entrada, 'r', encoding='utf-8') as f:
                codigo_fuente = f.read()

                                                                          
            lexer.lineno = 1

                                                          
            ast = parser.parse(codigo_fuente, lexer=lexer)

            if ast:               
                llvm_bind.initialize_native_target()
                llvm_bind.initialize_native_asmprinter()

                                                   
                nuevo_modulo = ir.Module(name=nombre_base)

                                                                                           
                triple_string = llvm_bind.get_default_triple()
                nuevo_modulo.triple = triple_string
                target_ref = llvm_bind.Target.from_triple(triple_string)
                target_machine = target_ref.create_target_machine()
                nuevo_modulo.data_layout = str(target_machine.target_data)

                                                                                        
                irgen = analisis.IRGenerator(nuevo_modulo)

                                                                                     
                ast.accept(irgen)

                                                                         
                with open(ruta_salida, 'w', encoding='utf-8') as f_out:
                    f_out.write(str(nuevo_modulo))

                print("Generado correctamente.")
            else:
                print("AST vacío.")

        except Exception as e:
            print(f" -> [ERROR CRÍTICO]: {e}")

    print("=== Proceso de compilación terminado ===")

if __name__ == '__main__':
    CARPETA_ENTRADA = "./codigo_c"
    CARPETA_SALIDA = "./codigo_ll"

    compilar_carpeta(CARPETA_ENTRADA, CARPETA_SALIDA)
