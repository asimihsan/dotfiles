# F* Tactics and Metaprogramming

## Overview

When SMT automation fails, F* provides tactics for interactive proof construction via Meta-F*.

## The Tac Effect

Tactics run in the `Tac` effect:
```fstar
open FStar.Tactics

// A tactic returning unit
val my_tactic : unit -> Tac unit

// A tactic computing a value
val find_witness : unit -> Tac nat
```

## Basic Tactics

### Proof Goals
```fstar
// dump: show current goals
let debug_tactic () : Tac unit =
  dump "Current state"

// goals: get list of goals
let check_goals () : Tac unit =
  let gs = goals () in
  if Nil? gs then fail "No goals!"
  else ()
```

### Simple Tactics
```fstar
// trivial: solve if goal is trivially true
let easy_proof () : Tac unit = trivial ()

// trefl: reflexivity for equality goals
let refl_proof () : Tac unit = trefl ()

// assumption: solve from context
let from_context () : Tac unit = assumption ()
```

### Computation
```fstar
// compute: normalize goal
let simplify () : Tac unit = compute ()

// norm: normalize with specific steps
let partial_norm () : Tac unit =
  norm [delta; iota; zeta]
```

## Using Tactics in Proofs

### assert_by_tactic
```fstar
let my_proof x =
  assert (x + 0 = x) by (compute ());
  assert (complex_property x) by (my_custom_tactic ());
  ()
```

### Tactic-based Lemmas
```fstar
let lemma_with_tactic x : Lemma (property x) =
  assert (property x) by (
    // Tactic script
    compute ();
    trivial ()
  )
```

## Common Tactics

### split
Split conjunction goals:
```fstar
// Goal: A /\ B
// After split: two goals A and B
let prove_and () : Tac unit =
  split ();
  // now prove each part
  trivial ();
  trivial ()
```

### left, right
Choose disjunction branch:
```fstar
// Goal: A \/ B
// left gives goal A, right gives goal B
let prove_or_left () : Tac unit =
  left ();
  trivial ()
```

### intro
Introduce hypothesis:
```fstar
// Goal: forall x. P x
// After intro: goal is P x with x in context
let prove_forall () : Tac unit =
  let x = intro () in
  // now prove P x
  trivial ()
```

### apply
Apply lemma or function:
```fstar
// If we have: lemma : A -> B
// And goal: B
// apply lemma gives goal: A
let use_lemma () : Tac unit =
  apply (`lemma_name);
  trivial ()
```

### mapply
Apply with implicit argument handling:
```fstar
let use_implicit_lemma () : Tac unit =
  mapply (`polymorphic_lemma);
  trivial ()
```

## Quotations and Antiquotations

### Quoting Terms
```fstar
// Quote a term (creates syntax)
let plus_term = `(1 + 2)

// Quote a name
let name = `some_definition
```

### Antiquotation
```fstar
// Splice in a computed term
let make_assertion (t:term) : Tac unit =
  let goal = `(assert (`#t)) in
  ...
```

## Inspecting Terms

### Term Views
```fstar
open FStar.Reflection

let inspect_term (t:term) : Tac unit =
  match inspect t with
  | Tv_Var v -> print "Variable"
  | Tv_App hd arg -> print "Application"
  | Tv_Abs bv body -> print "Lambda"
  | Tv_Arrow bv c -> print "Arrow type"
  | _ -> print "Other"
```

## When to Use Tactics

### SMT Friendly (skip tactics)
- Linear arithmetic
- Simple induction
- Refinement checking

### Tactics Useful For
- Nonlinear arithmetic
- Complex case splits
- Custom proof strategies
- Proof search
- Domain-specific automation

## Example: Custom Automation

```fstar
// Tactic to solve arithmetic goals
let arith_tactic () : Tac unit =
  // Try normalization first
  compute ();
  // Then try SMT
  try smt () with _ ->
  // Manual case split if needed
  cases_or () (fun () ->
    trivial ()
  ) (fun () ->
    trivial ()
  )

// Use it
let proof x =
  assert (x * 2 = x + x) by (arith_tactic ())
```

## Debugging Tactics

```fstar
let debug_tactic () : Tac unit =
  // Show goals
  dump "Before";

  // Do something
  compute ();

  // Show result
  dump "After"
```

## Resources

- Meta-F* paper and documentation
- FStar.Tactics module source
- Book Part 5: [../book/part5/](../book/part5/) - Metaprogramming and tactics
