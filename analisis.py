import ply.lex as lex
import ply.yacc as yacc
from arbol import *
from llvmlite import ir

                                                      
                                                                        

keywords = {'int': 'INT', 'float': 'FLOAT', 'void': 'VOID', 'return': 'RETURN'}
tokens = ['ID', 'INTLIT', 'FLOATLIT'] + list(keywords.values())
literals = '+-*/%(){};='
t_ignore = ' \t\r'


def t_FLOATLIT(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t


def t_INTLIT(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = keywords.get(t.value, 'ID')
    return t

def t_COMMENT(t):
    r'//.*'
    pass

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"Error léxico: '{t.value[0]}' en línea {t.lexer.lineno}")
    t.lexer.skip(1)

                

def p_Program(p):
    """Program : FunctionList"""
    p[0] = Program(p[1])

def p_FunctionList(p):
    """FunctionList : FunctionList FunctionDecl
                    | FunctionDecl"""
    p[0] = p[1] + [p[2]] if len(p) == 3 else [p[1]]

def p_FunctionDecl(p):
    """FunctionDecl : Type ID '(' ParamList ')' Block
                    | Type ID '(' ')' Block"""
    params = p[4] if len(p) == 7 else []
    block = p[6] if len(p) == 7 else p[5]
    p[0] = FunctionDecl(p[1], p[2], params, block)

def p_ParamList(p):
    """ParamList : ParamList ',' Param
                 | Param"""
    p[0] = p[1] + [p[3]] if len(p) == 4 else [p[1]]

def p_Param(p):
    """Param : Type ID"""
    p[0] = Declaration(p[2], p[1])


def p_Block(p):
    """Block : '{' Declarations Statements '}' """
    p[0] = Block(p[2], p[3])

def p_Declarations(p):
    """Declarations : Declarations Declaration
                    | empty"""
                                                                             
    p[0] = p[1] + [p[2]] if len(p) == 3 else []

def p_Declaration(p):
    """Declaration : Type ID ';' """
    p[0] = Declaration(p[2], p[1])

def p_Type(p):
    """Type : INT
            | FLOAT
            | VOID"""
    p[0] = p[1]


def p_Statements(p):
    """Statements : Statements Statement
                  | empty"""
    p[0] = p[1] + [p[2]] if len(p) == 3 else []

def p_Statement(p):
    """Statement : Assignment
                 | ReturnStatement"""
    p[0] = p[1]

def p_Assignment(p):
    """Assignment : ID '=' Expression ';' """
    p[0] = Assignment(p[1], p[3])

def p_ReturnStatement(p):
    """ReturnStatement : RETURN Expression ';' """
    p[0] = ReturnNode(p[2])


def p_Expression(p):
    """Expression : Relation"""
    p[0] = p[1]


def p_Relation(p):
    """Relation : Relation '+' Term
                | Relation '-' Term
                | Term"""
    p[0] = BinaryOp(p[2], p[1], p[3]) if len(p) == 4 else p[1]

def p_Term(p):
    """Term : Term '*' Factor
            | Term '/' Factor
            | Factor"""
    p[0] = BinaryOp(p[2], p[1], p[3]) if len(p) == 4 else p[1]

def p_Factor(p):
    """Factor : INTLIT
              | FLOATLIT
              | ID
              | '(' Expression ')'"""
    if len(p) == 4:
        p[0] = p[2]
    elif isinstance(p[1], int):
        p[0] = Literal(p[1], 'INT')
    elif isinstance(p[1], float):
        p[0] = Literal(p[1], 'FLOAT')
    elif isinstance(p[1], str) and p.slice[1].type == 'STRING_LITERAL':
        p[0] = Literal(p[1], 'STRING')
    elif isinstance(p[1], str):
        p[0] = Variable(p[1])
    else:
        p[0] = p[1]


def p_empty(p):
    """empty :"""
    pass

def p_error(p):
    if p:
        print(f"Error de sintaxis en '{p.value}' (línea {p.lineno})")
    else:
        print("Error de sintaxis: Fin de archivo inesperado")

                           
intType = ir.IntType(32)
floatType = ir.FloatType()
voidptr_ty = ir.IntType(8).as_pointer()

class IRGenerator(Visitor):
    def __init__(self, module):
        self.module = module
        self.builder = None
        self.symbol_table = {}
        self.stack = []
        self.current_function = None

        self.printf = None


    def cast_types(self, lhs, rhs):
        if lhs.type == rhs.type:
            return lhs, rhs
        if isinstance(lhs.type, ir.IntType) and isinstance(rhs.type, ir.FloatType):
            return self.builder.sitofp(lhs, floatType), rhs
        if isinstance(lhs.type, ir.FloatType) and isinstance(rhs.type, ir.IntType):
            return lhs, self.builder.sitofp(rhs, floatType)
        return lhs, rhs

    def ir_type(self, source_type: str):
        if source_type == 'float':
            return floatType
                                                                                              
        return intType

    def visit_program(self, node: Program):
        for func in node.functions:
            func.accept(self)

    def visit_function_decl(self, node: FunctionDecl):
        ret_ty = self.ir_type(node.ret_type)
        param_types = [self.ir_type(p.type) for p in node.params]
        fnty = ir.FunctionType(ret_ty, param_types)
        func = ir.Function(self.module, fnty, name=node.name)
        self.current_function = func
        block = func.append_basic_block('entry')
        self.builder = ir.IRBuilder(block)
        self.symbol_table = {}
        for i, param in enumerate(node.params):
            arg = func.args[i]
            arg.name = param.variable
            ptr = self.builder.alloca(arg.type, name=param.variable)
            self.builder.store(arg, ptr)
            self.symbol_table[param.variable] = ptr
        node.block.accept(self)
        if node.name == 'main' and not self.builder.block.is_terminated:
            self.builder.ret(ir.Constant(intType, 0))

    def visit_block(self, node: Block):
        for decl in node.decls:
            decl.accept(self)
        for stmt in node.stmts:
            stmt.accept(self)

    def visit_declaration(self, node: Declaration):
        ty = self.ir_type(node.type)
        ptr = self.builder.alloca(ty, name=node.variable)
        self.symbol_table[node.variable] = ptr

    def visit_assignment(self, node: Assignment):
        node.expression.accept(self)
        value = self.stack.pop()
        if node.variable not in self.symbol_table:
            raise NameError(f"Variable no declarada: {node.variable}")
        ptr = self.symbol_table[node.variable]
        if isinstance(value.type, ir.IntType) and isinstance(ptr.type.pointee, ir.FloatType):
            value = self.builder.sitofp(value, floatType)
        elif isinstance(value.type, ir.FloatType) and isinstance(ptr.type.pointee, ir.IntType):
            value = self.builder.fptosi(value, intType)
        self.builder.store(value, ptr)

    def visit_variable(self, node: Variable):
        if node.name not in self.symbol_table:
            raise NameError(f"Variable no declarada: {node.name}")
        ptr = self.symbol_table[node.name]
        self.stack.append(self.builder.load(ptr, name=node.name))

    def visit_literal(self, node: Literal):
        if node.type == 'INT':
            self.stack.append(ir.Constant(intType, node.value))

        elif node.type == 'FLOAT':
            self.stack.append(ir.Constant(floatType, node.value))

    def visit_binary_op(self, node: BinaryOp):
        node.lhs.accept(self)
        node.rhs.accept(self)
        rhs = self.stack.pop()
        lhs = self.stack.pop()
        lhs, rhs = self.cast_types(lhs, rhs)
        is_float = isinstance(lhs.type, ir.FloatType)
        res = None
        if node.op == '+': res = self.builder.fadd(lhs, rhs) if is_float else self.builder.add(lhs, rhs)
        elif node.op == '-': res = self.builder.fsub(lhs, rhs) if is_float else self.builder.sub(lhs, rhs)
        elif node.op == '*': res = self.builder.fmul(lhs, rhs) if is_float else self.builder.mul(lhs, rhs)
        elif node.op == '/': res = self.builder.fdiv(lhs, rhs) if is_float else self.builder.sdiv(lhs, rhs)
        if res is None:
            raise NotImplementedError(f"Operador no soportado: {node.op}")
        self.stack.append(res)

    def visit_return(self, node: ReturnNode):
        node.expression.accept(self)
        result = self.stack.pop()
        self.builder.ret(result)


if __name__ == '__main__':
    lexer = lex.lex()
    parser = yacc.yacc(write_tables=False)
    data = """
    int main() {
        int x;
        int y;
        x = 2;
        y = x + 3;
    }
    """
    ast = parser.parse(data, lexer=lexer)
    module = ir.Module(name='prog')
    irgen = IRGenerator(module)
    ast.accept(irgen)
    print(module)

