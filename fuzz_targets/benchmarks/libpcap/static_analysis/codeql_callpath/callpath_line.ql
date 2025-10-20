/**
 * @kind problem
 * @id nametoaddr-call-path-lines
 * @severity warning
 * @description Shows call paths (depth 4) to xmlSplitQName3 in tree.c, with lines of each call.
 */

import cpp

predicate isTarget(Function f) {
  f.getName() = "pcap_nametollc" and
  f.getFile().getBaseName() = "nametoaddr.c"
}

predicate callsOnLine(Function caller, Function callee, int line) {
  exists(FunctionCall fc |
    fc.getEnclosingFunction() = caller and
    fc.getTarget() = callee and
    line = fc.getLocation().getStartLine()
  )
}

from Function f1, Function f2, Function f3, Function f4,
     int l12, int l23, int l34
where
  isTarget(f4) and
  callsOnLine(f3, f4, l34) and
  callsOnLine(f2, f3, l23) and
  callsOnLine(f1, f2, l12)
select
  f1.getName() + " (calls on line " + l12.toString() + ")",
  f2.getName() + " (calls on line " + l23.toString() + ")",
  f3.getName() + " (calls on line " + l34.toString() + ")",
  f4.getName(),
  "Call path: " +
    f1.getName() + " [line " + l12.toString() + "] -> " +
    f2.getName() + " [line " + l23.toString() + "] -> " +
    f3.getName() + " [line " + l34.toString() + "] -> " +
    f4.getName()

