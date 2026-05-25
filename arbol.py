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
    def visit_program(self, node): pass
    @abstractmethod
    def visit_function_decl(self, node): pass
    @abstractmethod
    def visit_block(self, node): pass
    @abstractmethod
    def visit_declaration(self, node): pass
    @abstractmethod
    def visit_assignment(self, node): pass
    @abstractmethod
    def visit_binary_op(self, node): pass
    @abstractmethod
    def visit_literal(self, node): pass
    @abstractmethod
    def visit_variable(self, node): pass
