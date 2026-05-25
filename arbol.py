from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any


class ASTNode(ABC):
    @abstractmethod
    def accept(self, visitor: Visitor) -> None:
        pass

class Program(ASTNode):
    def __init__(self, decls: Any, stmts: ASTNode) -> None:
        self.decls = decls
        self.stmts = stmts

    def accept(self, visitor: Visitor):
        visitor.visit_program(self)

class Declaration(ASTNode):
    def __init__(self, variable: Any, type: Any) -> None:
        self.variable = variable
        self.type = type

    def accept(self, visitor: Visitor):
        visitor.visit_declaration(self)

class Declarations(ASTNode):
    def __init__(self, decls: Declarations | None, decl: Declaration) -> None:
        self.decls = decls
        self.decl = decl

    def accept(self, visitor: Visitor):
        visitor.visit_declarations(self)

class Statements(ASTNode):
    def __init__(self, stmts: Statements | None, stmt: ASTNode) -> None:
        self.stmts = stmts
        self.stmt = stmt

    def accept(self, visitor: Visitor):
        visitor.visit_statements(self)

class Assignment(ASTNode):
    def __init__(self, variable: Any, expression: ASTNode) -> None:
        self.variable = variable
        self.expression = expression

    def accept(self, visitor: Visitor):
        visitor.visit_assignment(self)

class Literal(ASTNode):
    def __init__(self, value: Any, type: str) -> None:
        self.value = value
        self.type = type

    def accept(self, visitor: Visitor):
        visitor.visit_literal(self)

    def __str__(self):
        return f"[LIT, {self.value}]"

class Variable(ASTNode):
    def __init__(self, name: Any, type: str = 'INT') -> None:
        self.name = name
        self.type = type

    def accept(self, visitor: Visitor):
        visitor.visit_variable(self)

class BinaryOp(ASTNode):
    def __init__(self, op: str, lhs: ASTNode, rhs: ASTNode) -> None:
        self.lhs = lhs
        self.rhs = rhs
        self.op = op

    def accept(self, visitor: Visitor):
        visitor.visit_binary_op(self)

    def __str__(self):
        return f"[{self.op}, {self.lhs}, {self.rhs}]"

class Visitor(ABC):
    @abstractmethod
    def visit_program(self, node: Program) -> None: pass
    @abstractmethod
    def visit_declarations(self, node: Declarations) -> None: pass
    @abstractmethod
    def visit_statements(self, node: Statements) -> None: pass
    @abstractmethod
    def visit_declaration(self, node: Declaration) -> None: pass
    @abstractmethod
    def visit_assignment(self, node: Assignment) -> None: pass
    @abstractmethod
    def visit_literal(self, node: Literal) -> None: pass
    @abstractmethod
    def visit_variable(self, node: Variable) -> None: pass
    @abstractmethod
    def visit_binary_op(self, node: BinaryOp) -> None: pass

class Calculator(Visitor):
    def __init__(self):
        self.stack = []
        self.values = {}

    def visit_program(self, node: Program) -> None:
        node.decls.accept(self)
        node.stmts.accept(self)

    def visit_declarations(self, node: Declarations) -> None:
        if node.decls is not None:
            node.decls.accept(self)
        self.values.setdefault(node.decl.variable, 0)

    def visit_statements(self, node: Statements) -> None:
        if node.stmts is not None:
            node.stmts.accept(self)
        node.stmt.accept(self)

    def visit_declaration(self, node: Declaration) -> None:
        self.values.setdefault(node.variable, 0)

    def visit_assignment(self, node: Assignment) -> None:
        node.expression.accept(self)
        self.values[node.variable] = self.stack.pop()

    def visit_literal(self, node: Literal) -> None:
        self.stack.append(node.value)

    def visit_variable(self, node: Variable) -> None:
        self.stack.append(self.values[node.name])

    def visit_binary_op(self, node: BinaryOp) -> None:
        node.lhs.accept(self)
        node.rhs.accept(self)
        rhs = self.stack.pop()
        lhs = self.stack.pop()
        if node.op == '+':
            self.stack.append(lhs + rhs)
        elif node.op == '*':
            self.stack.append(lhs * rhs)
