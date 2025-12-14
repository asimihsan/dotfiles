# Common F* Errors and Fixes

## Subtyping Check Failed

```
* Error 19: Subtyping check failed
  - Expected type nat got type int
```

**Cause**: Value doesn't satisfy refinement predicate.

**Fixes**:
1. Add assertion to help SMT:
   ```fstar
   assert (x >= 0);
   let y : nat = x
   ```
2. Add explicit precondition:
   ```fstar
   val f : x:int{x >= 0} -> nat
   ```
3. Check your logic - maybe the property doesn't hold

## SMT Timeout / Resource Limits

```
* Error: SMT solver says: canceled (rlimit=5; fuel=8)
```

**Cause**: Z3 couldn't prove within resource limit.

**Fixes**:
1. Increase limit locally:
   ```fstar
   #push-options "--z3rlimit 60"
   let my_function x = ...
   #pop-options
   ```
2. Add intermediate lemma:
   ```fstar
   helper_lemma x;  // Adds fact to context
   ```
3. See [smt-debugging.md](smt-debugging.md) for full workflow

## Incomplete Quantifiers

```
* Error: unknown because (incomplete quantifiers)
```

**Cause**: Z3 couldn't instantiate universal/existential.

**Fixes**:
1. Add SMT pattern (trigger):
   ```fstar
   val lemma : x:t -> Lemma (P x) [SMTPat (f x)]
   ```
2. Call lemma explicitly:
   ```fstar
   lemma x;  // Instantiates for this x
   ```
3. Increase fuel for inductive unfolding:
   ```fstar
   #push-options "--fuel 4"
   ```

## Non-terminating Function

```
* Error: Cannot prove termination
```

**Cause**: F* can't verify function terminates.

**Fixes**:
1. Add decreases clause:
   ```fstar
   let rec f (x:nat) : nat (decreases x) =
     if x = 0 then 0 else f (x - 1)
   ```
2. For multiple arguments:
   ```fstar
   let rec f (m n:nat) : nat (decreases %[m; n]) = ...
   ```
3. Use well-founded relation:
   ```fstar
   let rec f (x:t) : Tot r (decreases %[my_measure x]) = ...
   ```

## Effect Mismatch

```
* Error: Expected effect Tot but got effect GTot
```

**Cause**: Trying to use ghost/spec code in runtime context.

**Fixes**:
1. Check if function should be ghost:
   ```fstar
   val spec_only : x:nat -> GTot nat  // Not extracted
   ```
2. Use `reveal` for erased values:
   ```fstar
   let x = reveal (erased_value)
   ```
3. See [effects-system.md](effects-system.md) for effect hierarchy

## Module Name Mismatch

```
* Error 6: Module declaration "module Foo" does not match filename
```

**Cause**: Module name doesn't match file path.

**Fixes**:
- `module Foo` must be in `Foo.fst`
- `module A.B` must be in `A/B.fst` or `A.B.fst`
- Check `--include` paths

## Type Mismatch

```
* Error: Expected type int -> int but got int -> nat
```

**Cause**: Types don't unify.

**Fixes**:
1. Add type annotation:
   ```fstar
   let f : int -> int = fun x -> x
   ```
2. Use coercion if subtype:
   ```fstar
   let y : int = (x <: int)  // if x:nat
   ```

## Unknown Identifier

```
* Error 72: Identifier not found: some_name
```

**Cause**: Name not in scope.

**Fixes**:
1. Open the module:
   ```fstar
   open FStar.List.Tot
   ```
2. Use qualified name:
   ```fstar
   FStar.List.Tot.length
   ```
3. Check spelling and imports

## Interface/Implementation Mismatch

```
* Error: Interface contains abstract 'type' declaration; use 'val' instead
```

**Cause**: Using `type t` in .fsti for abstract type.

**Fix**: Use `val` for abstract types in interfaces:
```fstar
// In .fsti
val t : Type0

// In .fst
type t = nat
```

## Assertion Failed

```
* Error: assertion failed
```

**Cause**: `assert` couldn't be proven.

**Fixes**:
1. Check if assertion is actually true
2. Add intermediate assertions:
   ```fstar
   assert (fact1);
   assert (fact2);
   assert (final_goal);  // Now provable
   ```
3. Use tactic:
   ```fstar
   assert (goal) by (compute (); trivial ())
   ```

## Fuel Exhausted

```
* Warning: Fuel exhausted for recursive function
```

**Cause**: Not enough unfolding to prove property.

**Fix**: Increase fuel locally:
```fstar
#push-options "--fuel 4"
let proof_needing_unfolding x = ...
#pop-options
```

## General Debugging Tips

1. **Isolate the problem**: Create minimal reproducing example
2. **Add checkpoints**: Insert `assert` statements
3. **Check versions**: `fstar.exe --version`
4. **Use query stats**: `fstar.exe --query_stats file.fst`
5. **Ask for help**: Include exact error, F* version, and minimal code
