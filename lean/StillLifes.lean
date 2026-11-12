/-!
# Finite still lifes of B37/S2378 are exactly those of Conway's Life

A configuration is a function `L : ℤ × ℤ → Bool` (true = alive). It is a *still life* of a
Life-like rule when every live cell survives and no dead cell is born.

* `finite_stillLife_iff`: for every configuration with finitely many live cells,
  being a still life of B37/S2378 is equivalent to being a still life of B3/S23.
* `plane_counterexample`: the hypothesis of finiteness cannot be dropped (the full plane).

Proof. If a finite still life of B37/S2378 had a live cell with ≥ 7 live neighbours, take the
last one `c` in reading order. One of its later neighbours `(0,1)` or `(1,0)` is alive with
≥ 4 live neighbours inside the 3×3 block of `c` (a finite check, `local_dense`); it is not
dense, since `c` is the last dense cell, so it has 4, 5 or 6 neighbours and cannot survive.
Conversely, in a still life of Conway's Life no dead cell has 7 live neighbours: one of its
edge neighbours would be alive with ≥ 4 (`local_dead`).

Core Lean only, no Mathlib and no `import`: it compiles with the toolchain of `proofs/`
(CI: `cd lean/proofs && lake env lean ../StillLifes.lean`). The `#print axioms` lines at the
end are the audit; the main theorem uses the three standard axioms `propext`, `Classical.choice` and
`Quot.sound`, and the two finite checks use none.
-/

namespace StillLifes

abbrev Cell := Int × Int

def nbrs (p : Cell) : List Cell :=
  [(p.1 - 1, p.2 - 1), (p.1 - 1, p.2), (p.1 - 1, p.2 + 1),
   (p.1, p.2 - 1), (p.1, p.2 + 1),
   (p.1 + 1, p.2 - 1), (p.1 + 1, p.2), (p.1 + 1, p.2 + 1)]

def count (L : Cell → Bool) (p : Cell) : Nat := (nbrs p).countP L

def StillLife (live born : Nat → Bool) (L : Cell → Bool) : Prop :=
  ∀ p, (L p = true → live (count L p) = true) ∧ (L p = false → born (count L p) = false)

def conwayLive (n : Nat) : Bool := n == 2 || n == 3
def conwayBorn (n : Nat) : Bool := n == 3
def b37Live (n : Nat) : Bool := n == 2 || n == 3 || n == 7 || n == 8
def b37Born (n : Nat) : Bool := n == 3 || n == 7

def ind (b : Bool) : Nat := if b then 1 else 0

theorem count_eq (L : Cell → Bool) (x y : Int) :
    count L (x, y) = ind (L (x - 1, y - 1)) + ind (L (x - 1, y)) + ind (L (x - 1, y + 1))
      + ind (L (x, y - 1)) + ind (L (x, y + 1))
      + ind (L (x + 1, y - 1)) + ind (L (x + 1, y)) + ind (L (x + 1, y + 1)) := by
  simp only [count, nbrs, List.countP_cons, List.countP_nil, ind]
  omega

/-! ## The two finite checks (all 2⁹ values of a 3×3 block) -/

theorem local_dense : ∀ nw n ne w c e sw s se : Bool, c = true →
    7 ≤ ind nw + ind n + ind ne + ind w + ind e + ind sw + ind s + ind se →
    (e = true ∧ 4 ≤ ind n + ind ne + ind c + ind s + ind se) ∨
    (s = true ∧ 4 ≤ ind w + ind c + ind e + ind sw + ind se) := by
  decide

theorem local_dead : ∀ nw n ne w c e sw s se : Bool, c = false →
    7 ≤ ind nw + ind n + ind ne + ind w + ind e + ind sw + ind s + ind se →
    (e = true ∧ 4 ≤ ind n + ind ne + ind c + ind s + ind se) ∨
    (w = true ∧ 4 ≤ ind nw + ind n + ind c + ind sw + ind s) ∨
    (s = true ∧ 4 ≤ ind w + ind c + ind e + ind sw + ind se) ∨
    (n = true ∧ 4 ≤ ind nw + ind ne + ind w + ind c + ind e) := by
  decide

/-! ## Neighbour counts of the four edge neighbours, bounded below by the 3×3 block -/

theorem ge_e (L : Cell → Bool) (x y : Int) :
    ind (L (x - 1, y)) + ind (L (x - 1, y + 1)) + ind (L (x, y)) + ind (L (x + 1, y))
      + ind (L (x + 1, y + 1)) ≤ count L (x, y + 1) := by
  rw [count_eq]; simp only [Int.add_sub_cancel]; omega

theorem ge_s (L : Cell → Bool) (x y : Int) :
    ind (L (x, y - 1)) + ind (L (x, y)) + ind (L (x, y + 1)) + ind (L (x + 1, y - 1))
      + ind (L (x + 1, y + 1)) ≤ count L (x + 1, y) := by
  rw [count_eq]; simp only [Int.add_sub_cancel]; omega

theorem ge_w (L : Cell → Bool) (x y : Int) :
    ind (L (x - 1, y - 1)) + ind (L (x - 1, y)) + ind (L (x, y)) + ind (L (x + 1, y - 1))
      + ind (L (x + 1, y)) ≤ count L (x, y - 1) := by
  rw [count_eq]; simp only [Int.sub_add_cancel]; omega

theorem ge_n (L : Cell → Bool) (x y : Int) :
    ind (L (x - 1, y - 1)) + ind (L (x - 1, y + 1)) + ind (L (x, y - 1)) + ind (L (x, y))
      + ind (L (x, y + 1)) ≤ count L (x - 1, y) := by
  rw [count_eq]; simp only [Int.sub_add_cancel]; omega

/-! ## Arithmetic of the rules -/

theorem b37Live_mid (n : Nat) (h1 : 4 ≤ n) (h2 : n ≤ 6) : b37Live n = false := by
  have : n = 4 ∨ n = 5 ∨ n = 6 := by omega
  rcases this with rfl | rfl | rfl <;> rfl

theorem conwayLive_le (n : Nat) (h : conwayLive n = true) : n ≤ 3 := by
  simp [conwayLive] at h; omega

theorem conway_live_b37 (n : Nat) (h : conwayLive n = true) : b37Live n = true := by
  simp [conwayLive] at h; simp [b37Live]; omega

theorem b37_live_conway (n : Nat) (h : b37Live n = true) (h6 : n ≤ 6) : conwayLive n = true := by
  simp [b37Live] at h; simp [conwayLive]; omega

theorem b37_born_conway (n : Nat) (h : b37Born n = false) : conwayBorn n = false := by
  simp [b37Born] at h; simp [conwayBorn]; omega

/-! ## The last dense cell in reading order -/

def lexLt (p q : Cell) : Prop := p.1 < q.1 ∨ (p.1 = q.1 ∧ p.2 < q.2)

theorem exists_last (D : List Cell) (h : D ≠ []) : ∃ c ∈ D, ∀ p ∈ D, ¬ lexLt c p := by
  induction D with
  | nil => exact absurd rfl h
  | cons d rest ih =>
    by_cases hr : rest = []
    · subst hr
      refine ⟨d, by simp, ?_⟩
      intro p hp
      simp at hp
      subst hp
      unfold lexLt; omega
    · obtain ⟨c, hc, hmax⟩ := ih hr
      by_cases hcd : lexLt c d
      · refine ⟨d, by simp, ?_⟩
        intro p hp
        simp at hp
        rcases hp with rfl | hp
        · unfold lexLt; omega
        · intro hdp
          apply hmax p hp
          unfold lexLt at *
          omega
      · refine ⟨c, by simp [hc], ?_⟩
        intro p hp
        simp at hp
        rcases hp with rfl | hp
        · exact hcd
        · exact hmax p hp

theorem dense_contra (L : Cell → Bool) (x y : Int)
    (hSL : StillLife b37Live b37Born L) (hc : L (x, y) = true) (h7 : 7 ≤ count L (x, y))
    (post : ∀ q, lexLt (x, y) q → L q = true → count L q ≤ 6) : False := by
  rw [count_eq] at h7
  rcases local_dense _ _ _ _ _ _ _ _ _ hc h7 with ⟨he, h4⟩ | ⟨hs, h4⟩
  · have h6 := post (x, y + 1) (by unfold lexLt; dsimp only; omega) he
    have hlo := ge_e L x y
    have hlive := (hSL (x, y + 1)).1 he
    rw [b37Live_mid _ (by omega) h6] at hlive
    exact Bool.false_ne_true hlive
  · have h6 := post (x + 1, y) (by unfold lexLt; dsimp only; omega) hs
    have hlo := ge_s L x y
    have hlive := (hSL (x + 1, y)).1 hs
    rw [b37Live_mid _ (by omega) h6] at hlive
    exact Bool.false_ne_true hlive

/-- In a FINITE still life of B37/S2378 no live cell has 7 or 8 live neighbours. -/
theorem no_dense (L : Cell → Bool) (hfin : ∃ cells : List Cell, ∀ p, L p = true → p ∈ cells)
    (hSL : StillLife b37Live b37Born L) : ∀ p, L p = true → count L p ≤ 6 := by
  intro p hp
  refine Nat.le_of_not_lt (fun hlt => ?_)
  obtain ⟨cells, hcells⟩ := hfin
  let D := cells.filter (fun q => L q && decide (7 ≤ count L q))
  have hpD : p ∈ D := by
    simp only [D, List.mem_filter, hcells p hp, hp, Bool.true_and, decide_eq_true_eq, true_and]
    omega
  have hD : D ≠ [] := by
    intro h; rw [h] at hpD; simp at hpD
  obtain ⟨c, hcD, hmax⟩ := exists_last D hD
  simp only [D, List.mem_filter, Bool.and_eq_true, decide_eq_true_eq] at hcD
  obtain ⟨_, hcL, hc7⟩ := hcD
  have post : ∀ q, lexLt (c.1, c.2) q → L q = true → count L q ≤ 6 := by
    intro q hq hLq
    refine Nat.le_of_not_lt (fun h => hmax q ?_ hq)
    simp only [D, List.mem_filter, hcells q hLq, hLq, Bool.true_and, decide_eq_true_eq, true_and]
    omega
  exact dense_contra L c.1 c.2 hSL hcL hc7 post

/-- In ANY still life of Conway's Life (finite or not) no dead cell has 7 or more live neighbours. -/
theorem conway_no_dead7 (L : Cell → Bool) (hSL : StillLife conwayLive conwayBorn L)
    (x y : Int) (hd : L (x, y) = false) : count L (x, y) < 7 := by
  refine Nat.lt_of_not_le (fun h7 => ?_)
  rw [count_eq] at h7
  rcases local_dead _ _ _ _ _ _ _ _ _ hd h7 with ⟨he, h4⟩ | ⟨hw, h4⟩ | ⟨hs, h4⟩ | ⟨hn, h4⟩
  · have := conwayLive_le _ ((hSL (x, y + 1)).1 he); have := ge_e L x y; omega
  · have := conwayLive_le _ ((hSL (x, y - 1)).1 hw); have := ge_w L x y; omega
  · have := conwayLive_le _ ((hSL (x + 1, y)).1 hs); have := ge_s L x y; omega
  · have := conwayLive_le _ ((hSL (x - 1, y)).1 hn); have := ge_n L x y; omega

theorem conway_to_b37 (L : Cell → Bool) (h : StillLife conwayLive conwayBorn L) :
    StillLife b37Live b37Born L := by
  intro ⟨x, y⟩
  refine ⟨fun hL => conway_live_b37 _ ((h (x, y)).1 hL), fun hL => ?_⟩
  have h3 := (h (x, y)).2 hL
  have h7 := conway_no_dead7 L h x y hL
  simp [conwayBorn] at h3
  simp [b37Born]
  omega

theorem b37_to_conway (L : Cell → Bool) (hfin : ∃ cells : List Cell, ∀ p, L p = true → p ∈ cells)
    (h : StillLife b37Live b37Born L) : StillLife conwayLive conwayBorn L := by
  intro p
  exact ⟨fun hL => b37_live_conway _ ((h p).1 hL) (no_dense L hfin h p hL),
         fun hL => b37_born_conway _ ((h p).2 hL)⟩

/-- **Main theorem.** For configurations with finitely many live cells, the still lifes of
B37/S2378 are exactly the still lifes of Conway's Life B3/S23. -/
theorem finite_stillLife_iff (L : Cell → Bool)
    (hfin : ∃ cells : List Cell, ∀ p, L p = true → p ∈ cells) :
    StillLife b37Live b37Born L ↔ StillLife conwayLive conwayBorn L :=
  ⟨b37_to_conway L hfin, conway_to_b37 L⟩

/-- Finiteness is needed: the full plane is a still life of B37/S2378 but not of Conway's Life. -/
theorem plane_counterexample :
    StillLife b37Live b37Born (fun _ => true) ∧ ¬ StillLife conwayLive conwayBorn (fun _ => true) := by
  have h8 : ∀ p, count (fun _ => true) p = 8 := fun p => by simp [count, nbrs]
  refine ⟨fun p => ⟨fun _ => by rw [h8]; rfl, fun h => absurd h (by simp)⟩, fun h => ?_⟩
  have := (h (0, 0)).1 rfl
  rw [h8] at this
  exact absurd this (by decide)

end StillLifes

#print axioms StillLifes.finite_stillLife_iff
#print axioms StillLifes.plane_counterexample
#print axioms StillLifes.local_dense
#print axioms StillLifes.local_dead
