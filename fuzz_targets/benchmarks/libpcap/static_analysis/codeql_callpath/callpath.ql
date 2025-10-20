/**
 * @kind problem
 * @id functions-in-sf-pcap
 * @severity warning
 * @description List all functions defined in sf-pcap.c
 */
import cpp

predicate isTarget(Function f) {
  f.getName() = "pcap_nametollc" and
  f.getFile().getBaseName() = "nametoaddr.c"
}

predicate calls(Function caller, Function callee) {
  exists(FunctionCall fc |
    fc.getEnclosingFunction() = caller and
    fc.getTarget() = callee
  )
}

from Function f1, Function f2, Function f3, Function f4
where
  isTarget(f4) and
  calls(f3, f4) and
  calls(f2, f3) and
  calls(f1, f2)
select f1, f2, f3, f4, "Call path: " + f1.getName() + " -> " + f2.getName() + " -> " + f3.getName() + " -> " + f4.getName()
