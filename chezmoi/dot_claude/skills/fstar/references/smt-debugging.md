# SMT Debugging in F*

## Understanding SMT Failures

When F* says "SMT solver could not prove the query", the proof obligation was sent to Z3 but couldn't be discharged.

### Common Failure Reasons
```
- unknown because (incomplete quantifiers)  # Z3 couldn't instantiate quantifiers
- canceled                                   # Timed out
- resource limits reached                    # Hit rlimit
```

## Resource and Fuel Knobs

### z3rlimit
Sets Z3 per-query resource limit (rlimit units). Not a strict wall-clock timeout, but roughly correlates with seconds:
```bash
fstar.exe --z3rlimit 60 file.fst    # Default is 5 (~5s)
fstar.exe --z3rlimit_factor 2 file.fst  # Multiply all rlimits by 2
```

```fstar
// Local override
#push-options "--z3rlimit 60"
let expensive_proof x = ...
#pop-options
```

### fuel and ifuel
Control recursive unfolding. F* has initial and max values:
- `--initial_fuel` (default 2), `--max_fuel` (default 8)
- `--initial_ifuel` (default 1), `--max_ifuel` (default 2)

```fstar
// fuel: unrolling of recursive functions
// ifuel: unrolling of inductive datatypes in SMT encoding
#push-options "--fuel 4 --ifuel 2"
let needs_unfolding x = ...
#pop-options

// Use comma syntax to set initial,max separately
#push-options "--fuel 2,8 --ifuel 1,2"  // Preserves defaults explicitly
```

**Note**: `--fuel N` sets both initial and max to N, which can unintentionally cap unrolling.

**Guidance**:
- Start with defaults (`initial_fuel=2`, `max_fuel=8`, `initial_ifuel=1`, `max_ifuel=2`)
- Increase only for specific definitions
- Prefer lemmas over global fuel increases

## Quantifiers and Triggers

### The Trigger Problem
Z3 needs "triggers" to instantiate quantified formulas:
```fstar
// Good: SMTPat provides trigger
val my_lemma : x:nat -> Lemma (x + 1 > x) [SMTPat (x + 1)]

// Without trigger, Z3 may not instantiate
val orphan_lemma : x:nat -> Lemma (some_property x)
// If Z3 doesn't instantiate, call explicitly to add concrete instance:
// orphan_lemma x;  -- or add/adjust SMTPat patterns
```

### Choosing Triggers
```fstar
// Trigger on function application
val list_lemma : l:list 'a -> Lemma (length l >= 0)
  [SMTPat (length l)]

// Multiple patterns
val two_list_lemma : l1:list 'a -> l2:list 'a ->
  Lemma (length (l1 @ l2) = length l1 + length l2)
  [SMTPat (l1 @ l2)]

// Or patterns (either triggers)
[SMTPatOr [[SMTPat (f x)]; [SMTPat (g x)]]]
```

## Controlling Unfolding

### Opaque Definitions
Hide definitions from SMT:
```fstar
[@@"opaque_to_smt"]
let internal_helper x = complex_computation x

// SMT won't unfold internal_helper
// Must use reveal_opaque to expose when needed
```

### Selective Reveal
```fstar
open FStar.Pervasives

// Reveal opaque definition locally
let proof_needing_helper x =
  reveal_opaque (`%internal_helper) internal_helper;
  ...
```

### Abstraction Boundaries
Interface files (.fsti) naturally hide implementations:
```fstar
// Module.fsti - only signature visible to SMT
val f : x:nat -> y:nat{y > x}

// Module.fst - implementation hidden
let f x = x + 1  // SMT in other modules won't see this
```

## Local Options

### #push-options / #pop-options
```fstar
#push-options "--fuel 2 --ifuel 1 --z3rlimit 20"
let locally_tuned x = ...
#pop-options

// Nested options
#push-options "--fuel 4"
  #push-options "--z3rlimit 100"
  let very_expensive x = ...
  #pop-options
#pop-options
```

### #restart-solver
Reset solver state between definitions:
```fstar
#restart-solver
let fresh_context x = ...
```

Useful when previous proofs pollute the context.

## Debugging Workflow

### Step 1: Get Query Stats
```bash
fstar.exe --query_stats file.fst
```
Shows fuel/ifuel/rlimit used per query.

### Step 2: Log Failing Queries
```bash
fstar.exe --log_failing_queries file.fst
# Creates failedQueries-<Module>-<n>.smt2 files

fstar.exe --log_queries file.fst
# Creates queries-*.smt2 files (all queries, not just failures)
```

### Step 3: Inspect Goals
```fstar
// Add assertions to see intermediate state
let debug x =
  assert (x >= 0);           // Check this passes
  assert (some_property x);  // Check this
  assert (final_goal x)      // Find where it fails
```

### Step 4: Isolate the Problem
```fstar
// Create minimal reproducer
let minimal_failing_example x =
  assume (known_facts x);
  assert (failing_goal x)
```

## Hints for Reproducibility

### Recording Hints
```bash
fstar.exe --record_hints file.fst
# Creates file.fst.hints
```

### Using Hints
```bash
fstar.exe --use_hints file.fst
```

Benefits:
- Faster re-verification
- Less sensitivity to Z3 randomness
- More stable CI

## Common Patterns

### Adding Intermediate Lemmas
```fstar
// Instead of one big proof:
let big_theorem x =
  step1_lemma x;      // Adds fact 1 to context
  step2_lemma x;      // Adds fact 2
  step3_lemma x;      // Adds fact 3
  // Now final goal provable with context
  ()
```

### Normalizing Before Proof
```fstar
let proof x =
  assert_norm (expensive_computation x = simple_result);
  // Now use simple_result
  ()
```

### Manual Case Split
```fstar
let proof x =
  if x > 0 then begin
    assert (positive_case x);
    ()
  end else begin
    assert (non_positive_case x);
    ()
  end
```
