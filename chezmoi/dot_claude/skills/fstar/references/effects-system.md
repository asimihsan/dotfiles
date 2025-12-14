# F* Effect System

## Effect Overview

| Effect | Runtime? | Pre/Post? | Total? | Typical Use |
|--------|----------|-----------|--------|-------------|
| `Tot`  | Yes | Via refinements | Yes | Pure functions (default) |
| `GTot` | No (erased) | Via refinements | Yes | Ghost/spec (trivial WP) |
| `Pure` | Yes | Yes (WP) | Yes | Functions with requires/ensures |
| `Ghost`| No (erased) | Yes (WP) | Yes | Ghost with requires/ensures |
| `Lemma`| No (erased) | Yes | Yes | Proving properties |
| `Div`  | Yes | Yes (WP) | No | Possibly divergent |
| `ST`   | Yes | Yes | No | Stateful (may diverge) |

**Note**: `GTot` is to `Ghost` as `Tot` is to `Pure` (trivial WP vs explicit WP).

## Tot and GTot

### Tot (Total)
Default effect for terminating pure functions:
```fstar
open FStar.Mul  // Required for * as multiplication

// Tot is implicit
val factorial : nat -> nat
let rec factorial n = if n = 0 then 1 else n * factorial (n - 1)

// Explicit
val factorial' : nat -> Tot nat
```

### GTot (Ghost Total)
Erased at extraction - for specifications only:
```fstar
// Ghost function (not in compiled code)
val spec_length : list 'a -> GTot nat
let rec spec_length l = match l with
  | [] -> 0
  | _::tl -> 1 + spec_length tl
```

## Pure and Lemma

### Pure Effect
Functions with weakest precondition (WP) specs:
```fstar
open FStar.Mul

// With requires/ensures
val safe_div : x:int -> y:int -> Pure int
  (requires y <> 0)
  (ensures fun r -> r * y <= x /\ x - r * y < y)

// Shorthand with refinement return type
val safe_div' : x:int -> y:int{y <> 0} -> r:int{r * y <= x}
```

### Lemma Effect
Sugar for Pure with unit result, erased at extraction:
```fstar
open FStar.Mul

// Prove a property (use == for propositional equality)
val append_length : #a:Type -> l1:list a -> l2:list a ->
  Lemma (length (l1 @ l2) == length l1 + length l2)

// With precondition
val div_mod : x:nat -> y:pos ->
  Lemma (requires True)
        (ensures x == (x / y) * y + x % y)

// With SMT pattern (trigger)
val add_comm : x:int -> y:int ->
  Lemma (x + y == y + x) [SMTPat (x + y)]
```

## Refinement Types vs Pre/Post Effects

Two styles for specifications:

### Refinement Style
```fstar
// Pre/post encoded in types directly
val incr : x:int -> y:int{y = x + 1}
let incr x = x + 1
```

### Effect Style
```fstar
// Pre/post via Pure effect
val incr : x:int -> Pure int
  (requires True)
  (ensures fun y -> y = x + 1)
let incr x = x + 1
```

Both are equivalent but:
- Refinement style is more concise for simple specs
- Effect style better for complex pre/post with multiple conditions

## Div (Divergence)

For possibly non-terminating functions:
```fstar
// May not terminate
val loop_forever : unit -> Div unit (requires True) (ensures fun _ -> False)
let rec loop_forever () = loop_forever ()

// Partial function (may diverge)
val search : f:(nat -> bool) -> Div nat
  (requires True)
  (ensures fun n -> f n == true)
```

## ST (Stateful)

For functions with heap effects:
```fstar
open FStar.ST
open FStar.Heap  // For sel

// Read and write references
val incr_ref : r:ref int -> ST unit
  (requires fun h -> True)
  (ensures fun h0 _ h1 -> sel h1 r == sel h0 r + 1)
```

## Ghost and Erased

### Ghost Computations
For specification-only values:
```fstar
open FStar.Ghost

// erased t: value type whose inhabitants are erased at extraction (compiled as unit)
val ghost_length : erased (list 'a) -> GTot nat

// reveal/hide for erased values
let use_erased (x:erased nat) : GTot nat = reveal x
let make_erased (x:nat) : erased nat = hide x
```

**Important**: `reveal` is `GTot`, so it can only be used in ghost contexts (`GTot`/`Ghost`/`Lemma`), not in computational code (`Tot`/`Pure`/`ST`).

**Note**: `hide`/`reveal` are often inserted automatically by the typechecker as coercions.

### When to Use Ghost
- Specification helpers not needed at runtime
- Proof witnesses
- Auxiliary data for verification only

## User-Defined Effects

F* supports custom effects via Dijkstra monads:

```fstar
// Effect definition (advanced)
new_effect {
  STATE : a:Type -> Effect
  with repr = ...
       return = ...
       bind = ...
}
```

### Reify and Reflect

Convert between effectful and pure representations:
```fstar
// reify: effectful -> pure representation
let pure_version = reify (stateful_computation ())

// reflect: pure representation -> effectful
let effectful_version = STATE?.reflect pure_rep
```

Useful for:
- Proving properties about effectful code
- Implementing effect handlers
- Interop between effect levels

## Effect Subtyping

Effect promotions (lifting to less restrictive effects):

- `Tot` ⊂ `Pure` (trivial WP can be given explicit WP)
- `Tot` can be lifted to `GTot` (ghostifying is safe)
- `Pure` can be lifted to `Div` (dropping termination guarantee)
- `Pure` can be lifted to `Ghost` (erasing and keeping WP)
- `Div`/`Pure` can be lifted into `ST` (adding state)

**Key rule**: A `Tot` computation can be used wherever `GTot` is expected (making it ghost), but not vice versa - you cannot use a ghost computation in a runtime context.
