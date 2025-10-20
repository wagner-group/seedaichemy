/**
 * @kind table
 * @id call-path-depth4-nametollc
 * @description Show call paths (depth 4) to pcap_nametollc in nametoaddr.c, with call lines and enclosing statement types/lines.
 */

import cpp

predicate isTarget(Function f) {
  f.getName() = "pcap_nametollc" and
  f.getFile().getBaseName() = "nametoaddr.c"
}

predicate callsOnLine(Function caller, Function callee, FunctionCall call, int line) {
  call.getEnclosingFunction() = caller and
  call.getTarget() = callee and
  line = call.getLocation().getStartLine()
}

// Helper to show type of statement
private string stmtType(Stmt s) {
  if s instanceof IfStmt
    then result = "IfStmt"
  else if s instanceof WhileStmt
    then result = "WhileStmt"
  else if s instanceof ForStmt
    then result = "ForStmt"
  else if s instanceof SwitchStmt
    then result = "SwitchStmt"
  else if s instanceof ExprStmt
    then result = "ExprStmt"
  else if s instanceof ReturnStmt
    then result = "ReturnStmt"
  else
    result = "OtherStmt"
}

from Function f1, Function f2, Function f3, Function f4,
     FunctionCall c12, int l12, Stmt s12,
     FunctionCall c23, int l23, Stmt s23,
     FunctionCall c34, int l34, Stmt s34
where
  isTarget(f4) and
  callsOnLine(f3, f4, c34, l34) and s34 = c34.getEnclosingStmt() and
  callsOnLine(f2, f3, c23, l23) and s23 = c23.getEnclosingStmt() and
  callsOnLine(f1, f2, c12, l12) and s12 = c12.getEnclosingStmt()
select
  f1.getName(), l12, stmtType(s12), s12.getLocation().getStartLine(),
  f2.getName(), l23, stmtType(s23), s23.getLocation().getStartLine(),
  f3.getName(), l34, stmtType(s34), s34.getLocation().getStartLine(),
  f4.getName(),
  "Path: " +
   f1.getName() + " [line " + l12.toString() + ", " + stmtType(s12) + "@" + s12.getLocation().getStartLine().toString() + "] → " +
   f2.getName() + " [line " + l23.toString() + ", " + stmtType(s23) + "@" + s23.getLocation().getStartLine().toString() + "] → " +
   f3.getName() + " [line " + l34.toString() + ", " + stmtType(s34) + "@" + s34.getLocation().getStartLine().toString() + "] → " +
   f4.getName()
