import Lax834858.Oscillators

/-!
Each statement is a finite evaluation on a bounded board, so `decide` closes it in the
kernel; no `native_decide` and no assumption beyond `propext` is used. The boards are
lists, so the kernel needs more recursion depth and more heartbeats than the defaults.
-/

set_option maxRecDepth 40000
set_option maxHeartbeats 2000000

namespace Lax834858Proofs.Oscillators

open Lax834858.Oscillators

/--
---
conclusion: Lax834858.Oscillators.p10_period
---
Ten generations of `B37/S2378` evaluated on the board.
-/
theorem p10_period : houseStep^[10] p10 = p10 := by decide

/--
---
conclusion: Lax834858.Oscillators.p10_period_minimal
---
The nine shorter returns are each refuted by evaluation.
-/
theorem p10_period_minimal : ∀ k ∈ [1, 2, 3, 4, 5, 6, 7, 8, 9], houseStep^[k] p10 ≠ p10 := by
  decide

/--
---
conclusion: Lax834858.Oscillators.p32_period
---
Thirty-two generations of `B37/S2378` evaluated on the board.
-/
theorem p32_period : houseStep^[32] p32 = p32 := by decide

/--
---
conclusion: Lax834858.Oscillators.p10_not_conway
---
The same ten evaluations under `B3/S23`: the pattern is not periodic there within its
own period, so the clauses that distinguish the two rules are the ones sustaining it.
-/
theorem p10_not_conway : ∀ k ∈ [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], conwayStep^[k] p10 ≠ p10 := by
  decide

end Lax834858Proofs.Oscillators
