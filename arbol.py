from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, List

class ASTNode(ABC):
    @abstractmethod
    def accept(self, visitor: Visitor) -> None:
        pass

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
    def accept(self, visitor: Visitor):
        visitor.visit_function_decl(self)

class Block(ASTNode):
    def __init__(self, decls: List[Declaration], stmts: List[ASTNode]) -> None:
        self.decls = decls
        self.stmts = stmts
    def accept(self, visitor: Visitor):
        visitor.visit_block(self)

class Declaration(ASTNode):
    def __init__(self, variable: str, type: str) -> None:
        self.variable = variable
        self.type = type
    def accept(self, visitor: Visitor):
        visitor.visit_declaration(self)

class Assignment(ASTNode):
    def __init__(self, variable: str, expression: ASTNode) -> None:
        self.variable = variable
        self.expression = expression
    def accept(self, visitor: Visitor):
        visitor.visit_assignment(self)

class IfNode(ASTNode):
    def __init__(self, condition: ASTNode, if_body: ASTNode, else_body: ASTNode = None) -> None:
        self.condition = condition
        self.if_body = if_body
        self.else_body = else_body
    def accept(self, visitor: Visitor):
        visitor.visit_if(self)

class WhileNode(ASTNode):
    def __init__(self, condition: ASTNode, body: ASTNode) -> None:
        self.condition = condition
        self.body = body
    def accept(self, visitor: Visitor):
        visitor.visit_while(self)

class CallNode(ASTNode):
    def __init__(self, name: str, args: List[ASTNode]) -> None:
        self.name = name
        self.args = args
    def accept(self, visitor: Visitor):
        visitor.visit_call(self)

class ReturnNode(ASTNode):
    def __init__(self, expression: ASTNode) -> None:
        self.expression = expression
    def accept(self, visitor: Visitor):
        visitor.visit_return(self)

class ForNode(ASTNode):
    def __init__(self, init: ASTNode, cond: ASTNode, incr: ASTNode, body: ASTNode) -> None:
        self.init = init
        self.cond = cond
        self.incr = incr
        self.body = body
    def accept(self, visitor: Visitor):
        visitor.visit_for(self)

class DoWhileNode(ASTNode):
    def __init__(self, body: ASTNode, cond: ASTNode) -> None:
        self.body = body
        self.cond = cond
    def accept(self, visitor: Visitor):
        visitor.visit_dowhile(self)

class SwitchNode(ASTNode):
    def __init__(self, expr: ASTNode, cases: list, default_stmt: ASTNode = None) -> None:
        self.expr = expr
        self.cases = cases
        self.default_stmt = default_stmt
    def accept(self, visitor: Visitor):
        visitor.visit_switch(self)

class BinaryOp(ASTNode):
    def __init__(self, op: str, lhs: ASTNode, rhs: ASTNode) -> None:
        self.op = op
        self.lhs = lhs
        self.rhs = rhs
    def accept(self, visitor: Visitor):
        visitor.visit_binary_op(self)

class Literal(ASTNode):
    def __init__(self, value: Any, type: str) -> None:
        self.value = value
        self.type = type
    def accept(self, visitor: Visitor):
        visitor.visit_literal(self)

class Variable(ASTNode):
    def __init__(self, name: str) -> None:
        self.name = name
    def accept(self, visitor: Visitor):
        visitor.visit_variable(self)

class Visitor(ABC):
    @abstractmethod
    def visit_program(self, node: Program): pass
    @abstractmethod
    def visit_function_decl(self, node: FunctionDecl): pass
    @abstractmethod
    def visit_block(self, node: Block): pass
    @abstractmethod
    def visit_declaration(self, node: Declaration): pass
    @abstractmethod
    def visit_assignment(self, node: Assignment): pass
    @abstractmethod
    def visit_if(self, node: IfNode): pass
    @abstractmethod
    def visit_while(self, node: WhileNode): pass
    @abstractmethod
    def visit_call(self, node: CallNode): pass
    @abstractmethod
    def visit_return(self, node: ReturnNode): pass
    @abstractmethod
    def visit_binary_op(self, node: BinaryOp): pass
    @abstractmethod
    def visit_literal(self, node: Literal): pass
    @abstractmethod
    def visit_variable(self, node: Variable): pass
    @abstractmethod
    def visit_for(self, node: ForNode): pass
    @abstractmethod
    def visit_dowhile(self, node: DoWhileNode): pass
    @abstractmethod
    def visit_switch(self, node: SwitchNode): pass
