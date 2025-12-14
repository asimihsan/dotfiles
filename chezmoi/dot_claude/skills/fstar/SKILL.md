---
name: fstar
description: |
  F* proof-oriented programming language for verified software development.
  Use when: (1) writing or verifying F* code (.fst/.fsti files), (2) understanding
  verification errors from Z3/SMT, (3) learning dependent types, refinement types,
  or theorem proving, (4) extracting verified code to C via Karamel or to OCaml,
  (5) working with Low*, Steel, or Pulse DSLs, (6) setting up F* projects with mise.
  Triggers: F* code, fstar.exe, refinement types, SMT solver errors, z3rlimit,
  fuel/ifuel, verification conditions, dependent types, Karamel/krml extraction.
---

# F* Language Skill

## Quick Start

### First Steps
```bash
# Check F* version and help (always do this first)
fstar.exe --version
fstar.exe --help

# Verify a file
fstar.exe MyModule.fst

# Verify with caching (faster re-verification)
fstar.exe --cache_checked_modules MyModule.fst
```

### Minimal Example
```fstar
module Hello   // Must match filename: Hello.fst

let x : int = 42

// Refinement type: nat = x:int{x >= 0}
let y : nat = 42

// Function with specification
val incr : x:int -> y:int{y = x + 1}
let incr x = x + 1
```

### Project Setup (mise)
```toml
# mise.toml
[tools]
fstar = "2025.10.06"  # or "latest"
```

### Key Points
- Module name must match filepath relative to `--include` root (`module A.B` in `A/B.fst`)
- `.fst` = implementation, `.fsti` = interface (hides implementation)
- F* uses Z3 SMT solver for proof automation (bundled with F* install)
- All functions are total (terminate) by default

## Verification Debugging Playbook

When verification fails, follow this structured approach:

### Step 1: Read the Error
```
* Error 19 at MyFile.fst(10,5-10,20):
  - Subtyping check failed
  - Expected type nat got type int
  - SMT solver says: unknown because (incomplete quantifiers)
```

Key information:
- **Location**: `MyFile.fst(10,5-10,20)` = line 10, columns 5-20
- **Error type**: "Subtyping check failed" = refinement not provable
- **SMT reason**: "incomplete quantifiers" = one possible reason Z3 couldn't prove it

### Gather Info Checklist
Before debugging, ask the user for:
- Exact command used (`fstar.exe ...`)
- F* version (`fstar.exe --version`)
- Include paths (`--include` list)
- Minimal code snippet + exact error

### Step 2: Reduce the Problem
```fstar
// Isolate the failing assertion
let debug_point () =
  assert (the_property_that_fails);  // Does this fail alone?
  ()
```

### Step 3: Add Intermediate Facts
```fstar
let my_function x =
  assert (x >= 0);           // Checkpoint 1
  let y = x + 1 in
  assert (y > 0);            // Checkpoint 2
  assert (y >= x);           // Checkpoint 3
  result
```

### Step 4: Introduce Lemmas
```fstar
// Factor out a reusable proof
val my_lemma : x:nat -> Lemma (x + 1 > 0)
let my_lemma x = ()  // Often trivial for SMT

let my_function x =
  my_lemma x;  // Call lemma to add fact to context
  ...
```

### Step 5: Control Unfolding (Local Options)
```fstar
// Prefer local options over CLI flags
#push-options "--fuel 2 --ifuel 1 --z3rlimit 20"
let complex_function x = ...
#pop-options
```

### Step 6: Only Then Increase Limits
```bash
# Use --query_stats to understand what's happening
fstar.exe --query_stats MyModule.fst

# Increase limits as last resort
fstar.exe --z3rlimit 60 --fuel 4 MyModule.fst
```

## Core Language Essentials

### Refinement Types
Types with predicates (use `type` for aliases):
```fstar
// nat is built-in: x:int{x >= 0}
type pos = x:int{x > 0}               // Positive integers
type bounded (n:nat) = x:nat{x < n}   // Bounded naturals

// Function with precondition in type
val div : x:int -> y:int{y <> 0} -> int
let div x y = x / y
```

### Implicit Arguments
```fstar
// #a means implicit - inferred by compiler
val length : #a:Type -> list a -> nat
let rec length #a l = match l with
  | [] -> 0
  | _::tl -> 1 + length tl

// Usage: type inferred
let n = length [1;2;3]        // a inferred as int
let m = length #int [1;2;3]   // explicit instantiation
```

### Inductive Types
```fstar
// Simple enumeration
type color = | Red | Green | Blue

// Parameterized recursive type (custom, not built-in)
type tree (a:Type) =
  | Leaf : tree a
  | Node : left:tree a -> value:a -> right:tree a -> tree a

// Pattern matching on custom type
let rec tree_size #a (t:tree a) : nat =
  match t with
  | Leaf -> 0
  | Node left _ right -> 1 + tree_size left + tree_size right

// Built-in list uses [] and :: syntax
let head_or_default #a (default:a) (l:list a) : a =
  match l with
  | [] -> default
  | hd::_ -> hd
```

### Effects Overview
Every computation has an effect:

| Effect | Terminates? | Side effects? | Erased? | Use for |
|--------|-------------|---------------|---------|---------|
| `Tot`  | Yes | No | No | Pure functions (default) |
| `GTot` | Yes | No | Yes | Ghost computations (specs) |
| `Pure` | Yes | No | No | Pre/post style specs |
| `Lemma`| Yes | No | Yes | Proving properties |
| `Div`  | Maybe | No | No | Possibly divergent |
| `ST`   | Yes | Yes | No | Stateful code |

```fstar
// Tot is default, usually omitted
val factorial : nat -> nat
let rec factorial n = if n = 0 then 1 else n * factorial (n - 1)

// Lemma for proving (erased at extraction)
// Note: nonlinear arithmetic may need fuel/hints
val factorial_pos : n:nat -> Lemma (factorial n > 0)
let rec factorial_pos n = if n = 0 then () else factorial_pos (n - 1)

// Pure with requires/ensures (canonical pattern)
val incr_pure : x:int -> Pure int (requires True) (ensures fun r -> r == x + 1)
let incr_pure x = x + 1
```

### Termination
F* requires termination proofs for soundness:
```fstar
// Default: lexicographic on arguments
let rec length l = match l with
  | [] -> 0
  | _::tl -> 1 + length tl  // tl is subterm of l

// Explicit decreases clause
let rec ackermann (m n:nat) : nat (decreases %[m; n]) =
  if m = 0 then n + 1
  else if n = 0 then ackermann (m - 1) 1
  else ackermann (m - 1) (ackermann m (n - 1))
```

## SMT Interaction

### Key Compiler Flags
```bash
fstar.exe --z3rlimit 60 file.fst      # Increase Z3 resource limit (default 5)
fstar.exe --fuel 4 --ifuel 2 file.fst # Control unfolding
fstar.exe --query_stats file.fst      # Debug slow/failing proofs
fstar.exe --log_queries file.fst      # Dump SMT queries
fstar.exe --lax file.fst              # Typecheck only (admit all VCs)
```

### Fuel and iFuel
- `fuel` - Unfolding depth for recursive functions
- `ifuel` - Unfolding depth for inductive type matches
- Higher = more unfolding = slower but may prove more
- **Prefer**: lemma calls + selective unfolding; **Avoid**: global fuel increases

### Using admit and assume (Carefully!)
```fstar
// admit temporarily skips proof - ALWAYS mark clearly
let work_in_progress x =
  admit ();  // TODO: prove this property holds
  x + 1

// assume introduces an axiom - DANGEROUS if wrong
assume val trusted_property : x:nat -> Lemma (x * x >= x)
```
**Warning**:
- `admit`: temporary hole, label clearly with TODO
- `assume`/`assume val`: introduces axioms that can make proofs unsound if incorrect - use only for trusted external facts

### Quantifiers and Triggers
Quantified formulas need "triggers" for SMT:
```fstar
// SMTPat provides trigger for automatic instantiation
val my_lemma : x:nat -> Lemma (x + 1 > x) [SMTPat (x + 1)]

// Without trigger, may need explicit lemma calls
val no_trigger_lemma : x:nat -> Lemma (some_property x)
let use_it x =
  no_trigger_lemma x;  // Must call explicitly
  ...
```

### Local Options (Preferred)
```fstar
#push-options "--fuel 2 --ifuel 1 --z3rlimit 20"
let locally_tuned_function x = ...
#pop-options

// Per-definition attribute
[@@"opaque_to_smt"]  // Hide from SMT completely
let implementation_detail x = ...
```

## Project Structure

### Module System
```fstar
module MyProject.Utils  // Hierarchical naming

open FStar.List.Tot     // Import module
module L = FStar.List   // Alias

// Qualified access
let x = FStar.List.Tot.length [1;2;3]
let y = L.Tot.length [1;2;3]  // Using alias
```

### Interface Files (.fsti)
```fstar
// Counter.fsti - public interface
module Counter
val t : Type0              // Abstract type
val create : unit -> t
val increment : t -> t
val value : t -> nat

// Counter.fst - hidden implementation
module Counter
type t = nat
let create () = 0
let increment x = x + 1
let value x = x
```

### Dependencies and Build
```bash
# Generate dependency graph
fstar.exe --dep make MyModule.fst

# Add include paths
fstar.exe --include ./lib --include ./src MyModule.fst

# Cache checked modules
fstar.exe --cache_checked_modules --cache_dir .fstar_cache MyModule.fst
```

### Version Awareness
Always check F* version when debugging:
```bash
fstar.exe --version
# Flags and behavior can differ between versions
```

## Optional Tracks

### [TRACK] Low* and Karamel Extraction
For C code generation, see [references/lowstar-karamel.md](references/lowstar-karamel.md):
- Low* memory model (Stack, Heap, HyperStack)
- Buffer operations and safety proofs
- Karamel extraction pipeline:
  ```bash
  fstar.exe --codegen krml MyModule.fst  # Generates .krml
  krml -skip-compilation MyModule.krml   # Generates .c/.h
  ```

### [TRACK] Pulse/Steel Concurrency
For concurrent verified code, see [references/pulse-steel.md](references/pulse-steel.md):
- Separation logic (slprop, **, emp, pts_to)
- Ownership and frame rule
- Parallel composition

### [TRACK] Tactics and Metaprogramming
For proof automation, see [references/tactics-meta.md](references/tactics-meta.md):
- The `Tac` effect
- Core tactics: `compute()`, `trivial()`, `split`, `mapply`

## Reference Files

- [references/modules-build.md](references/modules-build.md) - Module system, dependencies, caching
- [references/effects-system.md](references/effects-system.md) - Effect hierarchy and user-defined effects
- [references/smt-debugging.md](references/smt-debugging.md) - SMT solver tuning and debugging
- [references/common-errors.md](references/common-errors.md) - Error messages and fixes

## Teaching F*

### Learning Progression
1. **Basic types**: `int`, `bool`, `unit`, simple functions
2. **Refinement types**: `nat = x:int{x >= 0}`, specifications as types
3. **Inductive types**: `list`, `option`, pattern matching
4. **Recursive functions**: Termination, `decreases` clauses
5. **Lemmas**: Proving properties, `Lemma` effect
6. **Effects**: `Tot`, `Pure`, `Ghost`, `ST`
7. **Advanced**: Tactics, Low*, Pulse

### When Helping Users
1. Ask for F* version: `fstar.exe --version`
2. Ask for include paths and project structure
3. Request the exact error message
4. Start with minimal reproducing example

### Resources
- Book: "Proof-oriented Programming in F*" - see [book/](book/) directory:
  - [book/part1/](book/part1/) - Getting started, basic proofs, termination
  - [book/part2/](book/part2/) - Inductive families, equality, logical connectives
  - [book/part3/](book/part3/) - Typeclasses, interfaces, a la carte
  - [book/part4/](book/part4/) - Effects (Tot, Pure, Div, Ghost)
  - [book/part5/](book/part5/) - Metaprogramming and tactics
  - [book/pulse/](book/pulse/) - Pulse DSL for separation logic
  - [book/under_the_hood/](book/under_the_hood/) - SMT encoding details
- Examples: F* repository `examples/` directory (34 categories)
- Online: https://fstar-lang.org/
- Help: `fstar.exe --help`
