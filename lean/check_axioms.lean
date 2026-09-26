/-
Axiom audit of the four proofs, run by CI after `lake build`:

    cd lean/proofs && lake env lean ../check_axioms.lean

Each line must report `propext` only. In particular none may depend on
`sorryAx`, on `Lean.ofReduceBool` (which `native_decide` would bring in), or on
the statements declared in `concepts/` (the Lax archive states the claims there
as axioms and the proofs in `proofs/` discharge them independently).
-/
import Lax834858Proofs

#print axioms Lax834858Proofs.Oscillators.p10_period
#print axioms Lax834858Proofs.Oscillators.p10_period_minimal
#print axioms Lax834858Proofs.Oscillators.p32_period
#print axioms Lax834858Proofs.Oscillators.p10_not_conway
