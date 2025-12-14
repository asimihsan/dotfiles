# Pulse and Steel: Concurrent Programming

## Overview

Steel and Pulse are F* DSLs for concurrent programming with separation logic. Pulse is the newer, more ergonomic version.

## Separation Logic Basics

### Core Predicates
```fstar
// slprop: separation logic proposition
// emp: empty/trivial resource
// **: separating conjunction (resources don't overlap)
// pts_to r v: reference r points to value v

open Steel.Memory

// r points to value v
pts_to r v

// Two non-overlapping resources
pts_to r1 v1 ** pts_to r2 v2

// Empty resource
emp
```

### Ownership
- Resources are owned exclusively
- `**` means disjoint ownership
- Frame rule: unused resources preserved automatically

## Steel Basics

### Reference Operations
```fstar
open Steel.Reference

// Read a reference
val read (#v:erased 'a) (r:ref 'a) : Steel 'a
  (pts_to r v)
  (fun x -> pts_to r x)
  (requires fun _ -> True)
  (ensures fun _ x _ -> reveal v == x)

// Write to a reference
val write (#v:erased 'a) (r:ref 'a) (x:'a) : Steel unit
  (pts_to r v)
  (fun _ -> pts_to r x)
  (requires fun _ -> True)
  (ensures fun _ _ _ -> True)
```

### Allocation
```fstar
open Steel.Reference

// Allocate new reference
val alloc ('a:Type) (x:'a) : Steel (ref 'a)
  emp
  (fun r -> pts_to r x)
  (requires fun _ -> True)
  (ensures fun _ _ _ -> True)

// Free reference
val free (#v:erased 'a) (r:ref 'a) : Steel unit
  (pts_to r v)
  (fun _ -> emp)
  (requires fun _ -> True)
  (ensures fun _ _ _ -> True)
```

## Pulse Syntax

Pulse provides a more imperative syntax:

```fstar
open Pulse

fn incr (r:ref int)
  requires pts_to r 'v
  ensures pts_to r ('v + 1)
{
  let x = !r;      // Read
  r := x + 1       // Write
}

fn swap (r1 r2:ref int)
  requires pts_to r1 'v1 ** pts_to r2 'v2
  ensures pts_to r1 'v2 ** pts_to r2 'v1
{
  let x1 = !r1;
  let x2 = !r2;
  r1 := x2;
  r2 := x1
}
```

## Parallel Composition

### Steel par
```fstar
open Steel.Effect.Common

// Run two computations in parallel
val par (#a #b:Type)
  (#pre1 #post1:slprop) (#pre2 #post2:slprop)
  (f:unit -> Steel a pre1 (fun x -> post1 x))
  (g:unit -> Steel b pre2 (fun y -> post2 y))
  : Steel (a * b)
    (pre1 ** pre2)
    (fun (x, y) -> post1 x ** post2 y)
```

### Example: Parallel Increment
```fstar
fn par_incr (r1 r2:ref int)
  requires pts_to r1 'v1 ** pts_to r2 'v2
  ensures pts_to r1 ('v1 + 1) ** pts_to r2 ('v2 + 1)
{
  par (fun () -> incr r1)
      (fun () -> incr r2)
}
```

## Frame Rule

The frame rule allows unused resources to be preserved:

```fstar
// If: f : pre -> post
// Then: f : (pre ** frame) -> (post ** frame)

fn example (r1 r2:ref int)
  requires pts_to r1 'v1 ** pts_to r2 'v2
  ensures pts_to r1 ('v1 + 1) ** pts_to r2 'v2  // r2 unchanged
{
  incr r1   // Frame: pts_to r2 'v2 preserved automatically
}
```

## Existentials

```fstar
// exists_ (fun x -> pts_to r x)
// Reference exists with some value

fn read_exists (r:ref int)
  requires exists_ (fun v -> pts_to r v)
  returns x:int
  ensures pts_to r x
{
  let x = !r;
  x
}
```

## Ghost State

```fstar
open Steel.Ghost

// Ghost references (erased at runtime)
val ghost_ref : Type -> Type

// Ghost read
val ghost_read (#v:erased 'a) (r:ghost_ref 'a) : Steel (erased 'a)
  (ghost_pts_to r v)
  (fun x -> ghost_pts_to r x)
```

## Invariants

```fstar
// Invariants for shared state
val new_invariant (p:slprop) : Steel (inv p)
  p (fun _ -> emp)

val with_invariant (#a:Type) (#p:slprop) (i:inv p)
  (#pre #post:slprop)
  (f:unit -> Steel a (p ** pre) (fun x -> p ** post x))
  : Steel a pre post
```

## Common Patterns

### Lock-based Sharing
```fstar
// Create lock protecting resource
val new_lock (p:slprop) : Steel (lock p) p (fun _ -> emp)

// Acquire lock
val acquire (l:lock p) : Steel unit emp (fun _ -> p)

// Release lock
val release (l:lock p) : Steel unit p (fun _ -> emp)
```

### Read-Only Access
```fstar
// Share for reading
val share (r:ref 'a) : Steel unit
  (pts_to r v)
  (fun _ -> pts_to r v ** pts_to_ro r v)
```

## Getting Started

1. Install F* with Steel/Pulse support
2. Import: `open Steel.Memory` or `open Pulse`
3. Start with sequential examples
4. Add parallelism gradually

## Resources

- Steel paper and tutorial
- Pulse documentation
- Book Pulse chapters: [../book/pulse/](../book/pulse/) - Getting started, arrays, linked lists, atomics
