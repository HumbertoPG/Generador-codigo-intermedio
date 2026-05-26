# Generador-codigo-intermedio

## Propósito

Este proyecto implementa un generador de código intermedio para un subconjunto de C. El resultado de la compilación es LLVM IR textual, generado a partir del análisis léxico, sintáctico y de la construcción de un AST. El objetivo no es producir un ejecutable final, sino traducir la estructura del programa fuente a una representación intermedia que pueda ser inspeccionada o procesada después por herramientas de LLVM.

El flujo completo se divide entre `main.py`, `analisis.py`, `arbol.py` y el archivo auxiliar `parsetab.py`. Cada archivo cumple un papel distinto: uno coordina la ejecución, otro define el lenguaje y construye el AST, otro representa esa estructura en memoria y el último conserva las tablas sintácticas generadas por PLY.

## Flujo general del proyecto

El proceso funciona así:

1. `main.py` localiza los archivos `.c` dentro de `codigo_c`.
2. `analisis.py` tokeniza y analiza el código fuente con PLY.
3. El parser construye nodos definidos en `arbol.py`.
4. `IRGenerator` recorre el AST y emite LLVM IR.
5. `main.py` guarda el resultado final como `.ll` en `codigo_ll`.

La comunicación entre módulos es directa y secuencial. `main.py` no conoce la gramática ni los nodos internos del AST; solo llama al parser y luego entrega el árbol al generador. `analisis.py` sí conoce la gramática y traduce cada regla reconocida a objetos de `arbol.py`. A su vez, `IRGenerator` consume esos objetos como una estructura ya resuelta, sin necesidad de volver a interpretar el texto fuente.

Esa separación es importante porque divide el problema en tres niveles claros: lectura y ejecución, análisis del lenguaje, y generación de IR. Cada nivel depende del anterior, pero no mezcla responsabilidades.

## Relación entre archivos

### `main.py` y `analisis.py`

`main.py` crea el lexer y el parser a partir del módulo `analisis`, luego parsea el texto fuente y entrega el AST al generador de IR.

```python
import analisis
from arbol import Program

lexer = lex.lex(module=analisis)
parser = yacc.yacc(module=analisis, write_tables=False, debug=False)
...
ast = parser.parse(codigo_fuente, lexer=lexer)
...
irgen = analisis.IRGenerator(nuevo_modulo)
ast.accept(irgen)
```

Esto se observa en la función `compilar_carpeta`. Esa función no genera IR por sí sola; su responsabilidad es coordinar la lectura, el análisis, la creación del módulo LLVM y la escritura del archivo `.ll`. Primero prepara el entorno de análisis, después recorre cada archivo fuente y finalmente deja que el AST recorra el generador de IR.

En términos funcionales, `main.py` actúa como puente entre el sistema de archivos y el compilador interno. También define el comportamiento de entrada y salida del proyecto: qué carpeta se lee, qué carpeta se escribe y cómo se nombran los archivos de resultado.

### `analisis.py` y `arbol.py`

`analisis.py` no produce cadenas de texto intermedias; construye nodos del AST definidos en `arbol.py`.

```python
def p_Program(p):
	"""Program : FunctionList"""
	p[0] = Program(p[1])

def p_FunctionDecl(p):
	"""FunctionDecl : Type ID '(' ParamList ')' Block
					| Type ID '(' ')' Block"""
	params = p[4] if len(p) == 7 else []
	block = p[6] if len(p) == 7 else p[5]
	p[0] = FunctionDecl(p[1], p[2], params, block)
```

	Aquí el parser toma la estructura sintáctica reconocida y crea objetos `Program` y `FunctionDecl`. Esa relación es la base del AST: el parser identifica la forma del programa y `arbol.py` define los contenedores de esa estructura.

	Lo relevante no es solo que se creen objetos, sino que cada objeto conserva la información mínima necesaria para la siguiente etapa. `FunctionDecl` guarda tipo de retorno, nombre, parámetros y bloque; `Block` guarda declaraciones y sentencias; `BinaryOp` guarda operador y operandos. Esa forma de modelado permite que la generación de IR sea mecánica y no dependa de volver a analizar texto.

### `arbol.py` y `IRGenerator`

El AST usa el patrón Visitor para permitir que `IRGenerator` recorra cada nodo sin mezclar la estructura del árbol con la lógica de generación de código.

```python
class Program(ASTNode):
	def __init__(self, functions: List[FunctionDecl]) -> None:
		self.functions = functions

	def accept(self, visitor: Visitor):
		visitor.visit_program(self)

class FunctionDecl(ASTNode):
	def __init__(self, ret_type: str, name: str, params: List[Declaration], block: Block) -> None:
		self.ret_type = ret_type
		self.name = name
		self.params = params
		self.block = block
```

Ese diseño permite que `IRGenerator` implemente métodos como `visit_program`, `visit_function_decl` y `visit_block` y genere IR sin modificar la estructura del AST.

También evita que la lógica de construcción del árbol tenga conocimiento sobre LLVM. Los nodos solamente representan significado del lenguaje: una función, una asignación, una condición o un retorno. El generador, en cambio, transforma ese significado en bloques básicos, instrucciones y saltos.

## Archivo `main.py`

### Función principal de compilación

La función central es `compilar_carpeta(carpeta_origen, carpeta_destino)`. Su tarea es coordinar el ciclo completo sobre los archivos fuente.

```python
def compilar_carpeta(carpeta_origen, carpeta_destino):
	if not os.path.exists(carpeta_destino):
		os.makedirs(carpeta_destino)

	lexer = lex.lex(module=analisis)
	parser = yacc.yacc(module=analisis, write_tables=False, debug=False)

	archivos_c = [f for f in os.listdir(carpeta_origen) if f.endswith('.c')]
```

Aquí se crea la carpeta destino si no existe y se prepara el análisis del código fuente.

Antes de procesar archivos, el script también ajusta el contexto del módulo principal para que PLY y las importaciones locales funcionen correctamente. Eso permite que la ejecución desde consola encuentre los archivos de soporte sin requerir configuraciones adicionales.

### Procesamiento de cada archivo

```python
for archivo in archivos_c:
	ruta_entrada = os.path.join(carpeta_origen, archivo)
	nombre_base = os.path.splitext(archivo)[0]
	ruta_salida = os.path.join(carpeta_destino, f"{nombre_base}.ll")

	with open(ruta_entrada, 'r', encoding='utf-8') as f:
		codigo_fuente = f.read()

	ast = parser.parse(codigo_fuente, lexer=lexer)
```

Este bloque lee cada archivo `.c`, obtiene el AST y prepara la salida `.ll` con el mismo nombre base.

En esta etapa también se reinicia el contador de líneas del lexer para que los mensajes de error apunten correctamente al archivo actual. Esa decisión es importante cuando se compilan varios archivos en una sola ejecución, porque evita que los errores arrastren el estado del archivo anterior.

### Creación del módulo LLVM

```python
nuevo_modulo = ir.Module(name=nombre_base)
triple_string = llvm_bind.get_default_triple()
nuevo_modulo.triple = triple_string
target_ref = llvm_bind.Target.from_triple(triple_string)
target_machine = target_ref.create_target_machine()
nuevo_modulo.data_layout = str(target_machine.target_data)

irgen = analisis.IRGenerator(nuevo_modulo)
ast.accept(irgen)
```

Esta parte enlaza el análisis con la generación de IR. El módulo se configura para la plataforma local antes de recorrer el AST.

La configuración del `triple` y del `data_layout` no es decorativa: asegura que el IR emitido sea coherente con la arquitectura del sistema donde se ejecuta el compilador. Sin ese paso, el resultado podría quedar incompleto o no coincidir con el entorno objetivo.

Después de crear el módulo, `main.py` entrega el control a `IRGenerator`. A partir de ese punto, el archivo deja de interpretar el programa fuente y solo administra el resultado producido por el recorrido del AST.

## Archivo `analisis.py`

### Definición léxica

El lexer reconoce palabras reservadas, identificadores, literales y operadores del lenguaje soportado.

```python
keywords = {
	'int': 'INT', 'float': 'FLOAT', 'void': 'VOID',
	'if': 'IF', 'else': 'ELSE', 'while': 'WHILE', 'return': 'RETURN',
	'for': 'FOR', 'do': 'DO', 'switch': 'SWITCH', 'case': 'CASE', 'default': 'DEFAULT'
}

tokens = ['ID', 'INTLIT', 'FLOATLIT', 'STRING_LITERAL',
		  'EQ', 'NE', 'LE', 'GE', 'AND', 'OR'] + list(keywords.values())
```

Esto define el vocabulario que el parser puede reconocer.

La lista de tokens no es arbitraria: está alineada con las construcciones que realmente soporta la gramática. Si una palabra o símbolo no aparece aquí, el parser no puede reconocerlo después. Por eso este bloque marca el límite formal del lenguaje que acepta el proyecto.

```python
def t_FLOATLIT(t):
	r'\d+\.\d+'
	t.value = float(t.value)
	return t

def t_INTLIT(t):
	r'\d+'
	t.value = int(t.value)
	return t
```

Estas funciones transforman texto fuente en valores numéricos utilizables por el AST.

Además de reconocer la sintaxis básica, el lexer normaliza valores. Un literal `123` pasa a ser un entero real dentro del AST; un literal `12.5` pasa a un flotante. Esa conversión temprana simplifica la etapa de generación de IR porque el generador trabaja con tipos ya interpretados.

### Gramática sintáctica

La gramática define cómo se construyen programas, funciones, bloques y sentencias.

```python
def p_Program(p):
	"""Program : FunctionList"""
	p[0] = Program(p[1])

def p_Statement(p):
	"""Statement : Assignment
				 | IfStatement
				 | WhileStatement
				 | CallStatement
				 | ReturnStatement
				 | ForStatement
				 | DoWhileStatement
				 | SwitchStatement
				 | Block"""
	p[0] = p[1]
```

```python
def p_IfStatement(p):
	"""IfStatement : IF '(' Expression ')' Block %prec IFX
				   | IF '(' Expression ')' Block ELSE Block"""
	p[0] = IfNode(p[3], p[5], p[7] if len(p) == 8 else None)
```

Estas reglas convierten la sintaxis reconocida en nodos del AST.

La gramática también define la precedencia y la asociación de operadores, así como la manera en que se agrupan las estructuras de control. Eso evita ambigüedades al analizar expresiones como `a + b * c` o bloques condicionales con `else`.

En este archivo también queda concentrada la lógica de construcción semántica inicial. Por ejemplo, un `if` sin `else` y un `if` con `else` terminan representados por el mismo tipo de nodo, pero con una diferencia en el contenido de su rama alternativa. Esa simplificación ayuda a que la etapa de IR sea uniforme.

### Generación de IR

`IRGenerator` es la parte que traduce el AST a LLVM IR.

```python
class IRGenerator(Visitor):
	def __init__(self, module):
		self.module = module
		self.builder = None
		self.symbol_table = {}
		self.stack = []
		self.current_function = None
```

La clase mantiene el módulo, el constructor de instrucciones, la tabla de símbolos y una pila temporal para resultados intermedios.

La pila temporal se usa para recuperar valores generados por subexpresiones. Por ejemplo, una operación binaria primero visita sus operandos, deja sus resultados en la pila y luego los consume para crear una instrucción LLVM concreta. La tabla de símbolos, en cambio, conserva dónde vive cada variable dentro de una función.

```python
def visit_function_decl(self, node: FunctionDecl):
	ret_ty = floatType if node.ret_type == 'float' else intType
	param_types = [floatType if p.type == 'float' else intType for p in node.params]
	fnty = ir.FunctionType(ret_ty, param_types)
	func = ir.Function(self.module, fnty, name=node.name)
```

Aquí se genera la firma LLVM de cada función a partir del tipo de retorno y de los parámetros.

Después de crear la firma, el generador crea el bloque de entrada, reserva espacio local para parámetros y registra cada variable en la tabla de símbolos. Eso significa que el cuerpo de la función ya puede usar los parámetros como valores almacenados en memoria local, no solo como argumentos temporales.

```python
def visit_if(self, node: IfNode):
	ifTrue = self.current_function.append_basic_block('if-true')
	ifFalse = self.current_function.append_basic_block('if-false')
	ifMerge = self.current_function.append_basic_block('if-merge')
```

Este patrón se repite en `while`, `for`, `do/while` y `switch`: se crean bloques básicos y se encadenan con saltos condicionales o incondicionales.

La razón de crear bloques separados es que LLVM IR trabaja con flujo explícito. Cada estructura de control se traduce a una combinación de bloques con ramas, y la lógica de salida o convergencia se resuelve con un bloque de unión cuando corresponde.

```python
def visit_switch(self, node: SwitchNode):
	node.expr.accept(self)
	switch_val = self.stack.pop()
	switch_exit = self.current_function.append_basic_block('switch-exit')
	default_block = self.current_function.append_basic_block('switch-default')
```

Esta función muestra cómo se traduce `switch` a bloques LLVM con casos y salida común.

El caso por defecto se gestiona como un bloque independiente, y cada caso explícito se conecta al bloque de salida al terminar. Con eso se reproduce la semántica básica de un `switch` en términos de flujo de control de bajo nivel.

## Archivo `arbol.py`

`arbol.py` define únicamente la estructura del AST y la interfaz de visita. No analiza texto ni genera IR por sí mismo.

```python
class ASTNode(ABC):
	@abstractmethod
	def accept(self, visitor: Visitor) -> None:
		pass

class Program(ASTNode):
	def __init__(self, functions: List[FunctionDecl]) -> None:
		self.functions = functions

	def accept(self, visitor: Visitor):
		visitor.visit_program(self)
```

Cada nodo encapsula la información necesaria para su traducción posterior.

La ventaja de esta organización es que el AST permanece independiente del formato de entrada. Si mañana el lenguaje se alimentara desde otra fuente, estos nodos podrían seguir siendo válidos mientras representen la misma estructura semántica.

```python
class Assignment(ASTNode):
	def __init__(self, variable: str, expression: ASTNode) -> None:
		self.variable = variable
		self.expression = expression

	def accept(self, visitor: Visitor):
		visitor.visit_assignment(self)
```

```python
class BinaryOp(ASTNode):
	def __init__(self, op: str, lhs: ASTNode, rhs: ASTNode) -> None:
		self.op = op
		self.lhs = lhs
		self.rhs = rhs

	def accept(self, visitor: Visitor):
		visitor.visit_binary_op(self)
```

Los nodos de expresiones y sentencias solo almacenan datos y delegan el comportamiento al visitante.

Eso hace que `arbol.py` sea un archivo de definición de modelo, no un archivo de ejecución. Su responsabilidad es describir qué existe en el programa fuente, no qué se hace con ello.

```python
class Visitor(ABC):
	@abstractmethod
	def visit_program(self, node: Program): pass
	@abstractmethod
	def visit_function_decl(self, node: FunctionDecl): pass
```

Esa interfaz es la base que permite que `IRGenerator` recorra el árbol con una responsabilidad separada.

En la práctica, cada método del visitante corresponde a una clase del AST. Esa correspondencia uno a uno simplifica el mantenimiento, porque cuando se agrega un nuevo nodo, también queda claro qué método del generador debe implementarse o ampliarse.

## Archivo `parsetab.py`

`parsetab.py` contiene las tablas sintácticas generadas por PLY. Su función es acelerar la carga del parser y evitar la regeneración de tablas en cada ejecución. No contiene la lógica principal del compilador, pero sí forma parte del flujo de análisis.

En otras palabras, este archivo no define el lenguaje, sino que materializa el resultado de la definición gramatical de `analisis.py`. Si la gramática cambia, estas tablas dejan de ser representativas y deben regenerarse.

## Entrada y salida

- Los archivos fuente deben ubicarse en `codigo_c`.
- La salida se genera en `codigo_ll` con el mismo nombre base del archivo de entrada.
- El resultado final es texto LLVM IR con extensión `.ll`.

El flujo de entrada y salida está pensado para trabajar por lotes. No se procesa un solo archivo aislado de forma manual, sino todos los `.c` presentes en la carpeta de origen. Eso hace que el proyecto funcione como una utilidad de compilación repetible.

## Requisitos

- Python 3.8 o superior.
- Dependencias: `llvmlite` y `ply`.

## Instalación rápida

```bash
pip install llvmlite ply
```

## Uso

```bash
python main.py
```

El comando analiza todos los archivos `.c` presentes en `codigo_c` y escribe sus equivalentes `.ll` en `codigo_ll`.

## Limitaciones

- El proyecto trabaja sobre un subconjunto de C.
- No implementa punteros, estructuras, arreglos, typedefs ni macros.
- El sistema de tipos es básico y las conversiones entre `int` y `float` se hacen durante la generación de IR.
- No genera binarios; para ello se debe usar `llc` o `clang` sobre los `.ll` generados.

El objetivo del proyecto es ser un generador de IR, no un compilador completo. Por eso se enfoca en las construcciones que pueden traducirse de forma directa y deja fuera características avanzadas del lenguaje que exigirían un análisis semántico mucho más amplio.
