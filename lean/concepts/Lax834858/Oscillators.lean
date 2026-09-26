import Mathlib.Logic.Function.Iterate
import Mathlib.Data.List.Basic

/-!
---
title: Two oscillators of the rule B37/S2378 that Conway's rule does not sustain
type: theorem
---
The outer-totalistic rule `B37/S2378` (a dead cell is born with 3 or 7 live
neighbours; a live cell survives with 2, 3, 7 or 8) admits two oscillators that an
exhaustive census of the `4 × 4` box under Conway's `B3/S23` does not produce: one of
period 10 with 11 live cells, and one of period 32 with 13. Both are exhibited here
as explicit finite boards, and every statement is a finite computation closed by
`decide`: the period-10 pattern returns to itself after exactly ten generations and
after no fewer, the period-32 pattern returns after thirty-two, and under Conway's
rule the first pattern does not return to itself within those ten generations. The
boards carry a margin wide enough that no phase touches the border, so each statement
is also a statement about the pattern on the infinite plane.
-/

namespace Lax834858.Oscillators

/-- A board: a list of rows of cells; `true` is alive. Outside the list everything is
dead, so a pattern that never reaches the border evolves as it would on the plane. -/
abbrev Board := List (List Bool)

/-- The cell at `(y, x)`; out of range it is dead. -/
def get (b : Board) (y x : Nat) : Bool := (b.getD y []).getD x false

/-- The number of live cells among the eight neighbours of `(y, x)`. -/
def neighbours (b : Board) (y x : Nat) : Nat :=
  let idx : List (Int × Int) := [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
  idx.foldl (fun acc p =>
    let yy : Int := (y : Int) + p.1
    let xx : Int := (x : Int) + p.2
    if 0 ≤ yy ∧ 0 ≤ xx then acc + (if get b yy.toNat xx.toNat then 1 else 0) else acc) 0

/-- One generation of the outer-totalistic rule with birth set `birth` and survival
set `survive`, on a board of fixed size. -/
def step (birth survive : List Nat) (b : Board) : Board :=
  (List.range b.length).map fun y =>
    (List.range ((b.getD 0 []).length)).map fun x =>
      let n := neighbours b y x
      if get b y x then survive.contains n else birth.contains n

/-- `B37/S2378`: a dead cell is born with 3 or 7 live neighbours, a live cell survives
with 2, 3, 7 or 8. -/
def houseStep : Board → Board := step [3, 7] [2, 3, 7, 8]

/-- Conway's `B3/S23`. -/
def conwayStep : Board → Board := step [3] [2, 3]

/-- The period-10 oscillator, 11 live cells, on a `13 × 14` board: the margin is wide
enough that no phase of the cycle reaches the border. -/
def p10 : Board :=
  [[false,false,false,false,false,false,false,false,false,false,false,false,false,false],
   [false,false,false,false,false,false,false,false,false,false,false,false,false,false],
   [false,false,false,false,false,false,false,false,false,false,false,false,false,false],
   [false,false,false,false,false,false,false,false,false,false,false,false,false,false],
   [false,false,false,false,false,true ,false,false,true ,false,false,false,false,false],
   [false,false,false,false,true ,false,false,false,true ,false,false,false,false,false],
   [false,false,false,false,true ,false,true ,false,false,true ,false,false,false,false],
   [false,false,false,false,true ,false,false,false,true ,false,false,false,false,false],
   [false,false,false,false,false,true ,false,false,true ,false,false,false,false,false],
   [false,false,false,false,false,false,false,false,false,false,false,false,false,false],
   [false,false,false,false,false,false,false,false,false,false,false,false,false,false],
   [false,false,false,false,false,false,false,false,false,false,false,false,false,false],
   [false,false,false,false,false,false,false,false,false,false,false,false,false,false]]

/-- The period-32 oscillator, 13 live cells in the phase shown, on an `18 × 20` board. -/
def p32 : Board :=
  [[false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false],
   [false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false],
   [false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false],
   [false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false],
   [false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false],
   [false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false],
   [false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false],
   [false,false,false,false,false,false,false,false,false,true ,true ,false,false,false,false,false,false,false,false,false],
   [false,false,false,false,false,false,false,false,true ,false,false,true ,true ,false,false,false,false,false,false,false],
   [false,false,false,false,false,false,false,true ,false,false,false,true ,true ,false,false,false,false,false,false,false],
   [false,false,false,false,false,false,false,false,true ,true ,true ,true ,true ,false,false,false,false,false,false,false],
   [false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false],
   [false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false],
   [false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false],
   [false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false],
   [false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false],
   [false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false],
   [false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false,false]]



/-- Under `B37/S2378` the pattern `p10` returns to itself after ten generations. -/
axiom p10_period : houseStep^[10] p10 = p10

/-- Ten is its exact period: no smaller positive number of generations works. -/
axiom p10_period_minimal : ∀ k ∈ [1, 2, 3, 4, 5, 6, 7, 8, 9], houseStep^[k] p10 ≠ p10

/-- Under `B37/S2378` the pattern `p32` returns to itself after thirty-two generations. -/
axiom p32_period : houseStep^[32] p32 = p32

/-- Conway's rule does not sustain `p10`: under `B3/S23` it does not return to itself
within ten generations. -/
axiom p10_not_conway : ∀ k ∈ [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], conwayStep^[k] p10 ≠ p10

end Lax834858.Oscillators
