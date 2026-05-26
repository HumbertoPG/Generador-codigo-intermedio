import ply.lex as lex
import ply.yacc as yacc
from arbol import *
from llvmlite import ir

                                                             
                                                                        

keywords = {'int': 'INT', 'float': 'FLOAT', 'void': 'VOID', 'if': 'IF', 'else': 'ELSE', 'while': 'WHILE', 'return': 'RETURN'}
tokens = ['ID', 'INTLIT', 'FLOATLIT', 'STRING_LITERAL', 'EQ', 'NE', 'LE', 'GE'] + list(keywords.values())
literals = '+-*/%(){}<>=;,:!'
t_ignore = ' \t\r'

t_EQ = r'=='
t_NE = r'!='
t_LE = r'<='
t_GE = r'>='

def t_FLOATLIT(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t


def t_STRING_LITERAL(t):
    r'"([^\
]|(\.))*?"'
    t.value = t.value[1:-1]
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
                 | IfStatement
                 | WhileStatement
                 | CallStatement
                 | ReturnStatement
                 | Block"""
    p[0] = p[1]

def p_Assignment(p):
    """Assignment : ID '=' Expression ';' """
    p[0] = Assignment(p[1], p[3])

def p_IfStatement(p):
    """IfStatement : IF '(' Expression ')' Block
                   | IF '(' Expression ')' Block ELSE Block"""
    p[0] = IfNode(p[3], p[5], p[7] if len(p) == 8 else None)

def p_WhileStatement(p):
    """WhileStatement : WHILE '(' Expression ')' Block"""
    p[0] = WhileNode(p[3], p[5])

def p_CallStatement(p):
    """CallStatement : Call ';' """
    p[0] = p[1]

def p_ReturnStatement(p):
    """ReturnStatement : RETURN Expression ';' """
    p[0] = ReturnNode(p[2])


def p_Expression(p):
    """Expression : Expression EQ Relation
                  | Expression NE Relation
                  | Expression '<' Relation
                  | Expression LE Relation
                  | Expression '>' Relation
                  | Expression GE Relation
                  | Relation"""
    p[0] = BinaryOp(p[2], p[1], p[3]) if len(p) == 4 else p[1]


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
              | STRING_LITERAL
              | ID
              | Call
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

def p_Call(p):
    """Call : ID '(' ArgList ')'
            | ID '(' ')' """
    args = p[3] if len(p) == 5 else []
    p[0] = CallNode(p[1], args)

def p_ArgList(p):
    """ArgList : ArgList ',' Expression
               | Expression"""
    p[0] = p[1] + [p[3]] if len(p) == 4 else [p[1]]


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

        printf_ty = ir.FunctionType(ir.IntType(32), [voidptr_ty], var_arg=True)
        self.printf = ir.Function(self.module, printf_ty, name="printf")


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

        elif node.type == 'STRING':
            text = node.value + '\0'
            c_text = ir.Constant(ir.ArrayType(ir.IntType(8), len(text)), bytearray(text.encode('utf8')))
            global_name = f"str_{len(list(self.module.global_values))}"
            global_text = ir.GlobalVariable(self.module, c_text.type, name=global_name)
            global_text.linkage = 'internal'
            global_text.global_constant = True
            global_text.initializer = c_text
            self.stack.append(self.builder.bitcast(global_text, voidptr_ty))

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
        elif node.op == '<=': res = self.builder.fcmp_ordered('<=', lhs, rhs) if is_float else self.builder.icmp_signed('<=', lhs, rhs)
        elif node.op == '>=': res = self.builder.fcmp_ordered('>=', lhs, rhs) if is_float else self.builder.icmp_signed('>=', lhs, rhs)
        elif node.op == '<': res = self.builder.fcmp_ordered('<', lhs, rhs) if is_float else self.builder.icmp_signed('<', lhs, rhs)
        elif node.op == '>': res = self.builder.fcmp_ordered('>', lhs, rhs) if is_float else self.builder.icmp_signed('>', lhs, rhs)
        elif node.op == '==': res = self.builder.fcmp_ordered('==', lhs, rhs) if is_float else self.builder.icmp_signed('==', lhs, rhs)
        elif node.op == '!=': res = self.builder.fcmp_ordered('!=', lhs, rhs) if is_float else self.builder.icmp_signed('!=', lhs, rhs)
        if res is None:
            raise NotImplementedError(f"Operador no soportado: {node.op}")
        self.stack.append(res)

    def visit_if(self, node: IfNode):
        if_true = self.current_function.append_basic_block('if-true')
        if_false = self.current_function.append_basic_block('if-false')
        if_merge = self.current_function.append_basic_block('if-merge')
        node.condition.accept(self)
        cond = self.stack.pop()
        self.builder.cbranch(cond, if_true, if_false)
        self.builder.position_at_start(if_true)
        node.if_body.accept(self)
        if not self.builder.block.is_terminated:
            self.builder.branch(if_merge)
        self.builder.position_at_start(if_false)
        if node.else_body:
            node.else_body.accept(self)
        if not self.builder.block.is_terminated:
            self.builder.branch(if_merge)
        self.builder.position_at_start(if_merge)


    def visit_while(self, node: WhileNode):
        while_head = self.current_function.append_basic_block('while-head')
        while_body = self.current_function.append_basic_block('while-body')
        while_exit = self.current_function.append_basic_block('while-exit')
        self.builder.branch(while_head)
        self.builder.position_at_start(while_head)
        node.condition.accept(self)
        cond = self.stack.pop()
        self.builder.cbranch(cond, while_body, while_exit)
        self.builder.position_at_start(while_body)
        node.body.accept(self)
        if not self.builder.block.is_terminated:
            self.builder.branch(while_head)
        self.builder.position_at_start(while_exit)


    def visit_call(self, node: CallNode):
        args = []
        for arg in node.args:
            arg.accept(self)
            args.append(self.stack.pop())
        if node.name == 'printf':
            self.stack.append(self.builder.call(self.printf, args))
        else:
            func = self.module.globals.get(node.name)
            if func is None:
                raise NameError(f"Función no declarada: {node.name}")
            self.stack.append(self.builder.call(func, args))


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

