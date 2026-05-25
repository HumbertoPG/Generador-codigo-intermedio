_tabversion = '3.10'

_lr_method = 'LALR'

_lr_signature = "ID INTLITProgram : ID ID '(' ')' '{' Declarations Statements '}'Declarations : Declarations Declaration\n                  | DeclarationDeclaration : ID ID ';'Statements : Statements Statement\n                | StatementStatement : AssignmentAssignment : ID '=' Expression ';'Expression : Expression '+' Term\n                  | TermTerm : Term '*' Factor\n            | FactorFactor : INTLIT\n              | ID\n              | '(' Expression ')'"
    
_lr_action_items = {'ID':([0,2,6,7,8,9,11,12,13,14,15,16,17,20,26,27,28,29,],[2,3,7,10,11,-3,10,18,-2,-6,-7,-4,21,-5,21,-8,21,21,]),'$end':([1,19,],[0,-1,]),'(':([3,17,26,28,29,],[4,26,26,26,26,]),')':([4,21,23,24,25,30,31,32,33,],[5,-14,-10,-12,-13,33,-9,-11,-15,]),'{':([5,],[6,]),';':([10,21,22,23,24,25,31,32,33,],[16,-14,27,-10,-12,-13,-9,-11,-15,]),'=':([11,18,],[17,17,]),'}':([12,14,15,20,27,],[19,-6,-7,-5,-8,]),'INTLIT':([17,26,28,29,],[25,25,25,25,]),'*':([21,23,24,25,31,32,33,],[-14,29,-12,-13,29,-11,-15,]),'+':([21,22,23,24,25,30,31,32,33,],[-14,28,-10,-12,-13,28,-9,-11,-15,]),}

_lr_action = {}
for _k, _v in _lr_action_items.items():
   for _x,_y in zip(_v[0],_v[1]):
      if not _x in _lr_action:  _lr_action[_x] = {}
      _lr_action[_x][_k] = _y
del _lr_action_items

_lr_goto_items = {'Program':([0,],[1,]),'Declarations':([6,],[8,]),'Declaration':([6,8,],[9,13,]),'Statements':([8,],[12,]),'Statement':([8,12,],[14,20,]),'Assignment':([8,12,],[15,15,]),'Expression':([17,26,],[22,30,]),'Term':([17,26,28,],[23,23,31,]),'Factor':([17,26,28,29,],[24,24,24,32,]),}

_lr_goto = {}
for _k, _v in _lr_goto_items.items():
   for _x, _y in zip(_v[0], _v[1]):
       if not _x in _lr_goto: _lr_goto[_x] = {}
       _lr_goto[_x][_k] = _y
del _lr_goto_items
_lr_productions = [
  ("S' -> Program","S'",1,None,None,None),
  ('Program -> ID ID ( ) { Declarations Statements }','Program',8,'p_Program','analisis.py',34),
  ('Declarations -> Declarations Declaration','Declarations',2,'p_Declarations','analisis.py',38),
  ('Declarations -> Declaration','Declarations',1,'p_Declarations','analisis.py',39),
  ('Declaration -> ID ID ;','Declaration',3,'p_Declaration','analisis.py',43),
  ('Statements -> Statements Statement','Statements',2,'p_Statements','analisis.py',47),
  ('Statements -> Statement','Statements',1,'p_Statements','analisis.py',48),
  ('Statement -> Assignment','Statement',1,'p_Statement','analisis.py',53),
  ('Assignment -> ID = Expression ;','Assignment',4,'p_Assignment','analisis.py',57),
  ('Expression -> Expression + Term','Expression',3,'p_Expression','analisis.py',61),
  ('Expression -> Term','Expression',1,'p_Expression','analisis.py',62),
  ('Term -> Term * Factor','Term',3,'p_Term','analisis.py',66),
  ('Term -> Factor','Term',1,'p_Term','analisis.py',67),
  ('Factor -> INTLIT','Factor',1,'p_Factor','analisis.py',71),
  ('Factor -> ID','Factor',1,'p_Factor','analisis.py',72),
  ('Factor -> ( Expression )','Factor',3,'p_Factor','analisis.py',73),
]
