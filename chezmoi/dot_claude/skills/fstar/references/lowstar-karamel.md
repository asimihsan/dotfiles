# Low* and Karamel Extraction

## Overview

Low* is an embedded DSL in F* for writing C-like code with verification. Karamel extracts Low* to readable C.

## Low* Memory Model

### Memory Regions
```fstar
open LowStar.Buffer
open FStar.HyperStack.ST

// Stack: automatically freed on function return
// Heap: manually managed
// HyperStack: unified model
```

### Buffers
```fstar
open LowStar.Buffer

// Buffer of n uint8 values
val b : buffer uint8

// Buffer with known length
val sized_buf : lbuffer uint8 16

// Operations
let x = index b 0ul        // Read at index
upd b 0ul value            // Write at index
```

## Stack Allocation

```fstar
open LowStar.Buffer
open FStar.HyperStack.ST

let stack_example () : ST unit
  (requires fun h -> True)
  (ensures fun h0 _ h1 -> modifies loc_none h0 h1)
=
  // Allocate on stack (push_frame/pop_frame)
  push_frame ();

  let buf = alloca 0uy 16ul in  // 16 bytes, initialized to 0
  upd buf 0ul 42uy;

  pop_frame ()
```

## Heap Allocation

```fstar
open LowStar.Buffer
open FStar.HyperStack.ST

let heap_example () : ST (buffer uint8)
  (requires fun h -> True)
  (ensures fun h0 r h1 -> live h1 r)
=
  // Allocate on heap
  let buf = malloc HyperStack.root 0uy 16ul in
  buf

// Must free manually
let cleanup (buf:buffer uint8) : ST unit
  (requires fun h -> freeable buf /\ live h buf)
  (ensures fun h0 _ h1 -> True)
=
  free buf
```

## Safety Predicates

### Liveness
```fstar
// live h buf: buffer is valid in heap h
val read_safe : buf:buffer uint8 -> ST uint8
  (requires fun h -> live h buf /\ length buf > 0)
  (ensures fun h0 r h1 -> h0 == h1)
=
  index buf 0ul
```

### Disjointness
```fstar
// disjoint buf1 buf2: buffers don't overlap
val copy_safe : src:buffer uint8 -> dst:buffer uint8 -> len:uint32 -> ST unit
  (requires fun h ->
    live h src /\ live h dst /\
    length src >= v len /\ length dst >= v len /\
    disjoint src dst)
  (ensures fun h0 _ h1 ->
    modifies (loc_buffer dst) h0 h1)
```

### Modifies
```fstar
// modifies loc h0 h1: only loc changed between heaps
val increment : r:ref uint32 -> ST unit
  (requires fun h -> live h r)
  (ensures fun h0 _ h1 ->
    modifies (loc_buffer r) h0 h1 /\
    sel h1 r = sel h0 r + 1ul)
```

## Example: Verified memcpy

```fstar
module VerifiedMemcpy

open LowStar.Buffer
open FStar.HyperStack.ST
open FStar.UInt32

let rec memcpy (len:uint32) (src dst:buffer uint8) (i:uint32{v i <= v len}) : ST unit
  (requires fun h ->
    live h src /\ live h dst /\
    length src >= v len /\ length dst >= v len /\
    disjoint src dst)
  (ensures fun h0 _ h1 ->
    modifies (loc_buffer dst) h0 h1 /\
    (forall (j:nat). j < v len ==> get h1 dst j = get h0 src j))
=
  if i <^ len then begin
    upd dst i (index src i);
    memcpy len src dst (i +^ 1ul)
  end
```

## Karamel Extraction

### Basic Workflow
```bash
# Step 1: Generate .krml from F*
fstar.exe --codegen krml --extract MyModule MyModule.fst

# Step 2: Generate C from .krml
krml MyModule.krml -skip-compilation -tmpdir out

# Step 3: Compile C
cd out && gcc -c MyModule.c
```

### Key Karamel Flags
```bash
krml file.krml \
  -skip-compilation        # Don't compile C, just generate
  -tmpdir ./out            # Output directory
  -no-prefix MyModule      # Don't prefix C names
  -bundle 'MyModule=*'     # Bundle into single C file
  -add-include '"myheader.h"'  # Add includes
  -ftail-calls            # Optimize tail calls
```

### Extraction Annotations
```fstar
// Control extraction name
[@@"c_name" "my_c_function"]
let fstar_function x = ...

// Inline in generated C
[@@"inline"]
let small_helper x = ...

// Don't extract (for spec-only code)
[@@"noextract"]
let spec_only_function x = ...
```

## Project Structure

```
project/
├── src/
│   ├── Lib.fst           # F* implementation
│   └── Lib.fsti          # F* interface
├── out/
│   ├── Lib.c             # Generated C
│   └── Lib.h             # Generated header
├── Makefile
└── mise.toml
```

### Makefile Pattern
```makefile
FSTAR=fstar.exe
KRML=krml

SOURCES=src/Lib.fst src/Main.fst

.PHONY: verify extract compile

verify:
	$(FSTAR) --include src $(SOURCES)

extract: verify
	$(FSTAR) --codegen krml --include src --odir out $(SOURCES)
	$(KRML) out/*.krml -skip-compilation -tmpdir out

compile: extract
	cd out && gcc -I. -c *.c
```

## Common Patterns

### Loops as Recursion
```fstar
// Low* doesn't have while loops - use tail recursion
let rec loop (i:uint32) (n:uint32) : ST unit
  (requires fun h -> v i <= v n)
  (ensures fun h0 _ h1 -> True)
  (decreases (v n - v i))
=
  if i <^ n then begin
    // loop body
    loop (i +^ 1ul) n
  end
```

### Machine Integers
```fstar
open FStar.UInt32
open FStar.UInt8

// Use machine integers, not nat/int
let add_u32 (x y:uint32) : uint32 = x +^ y
let mul_u8 (x y:uint8) : uint8 = x *^ y
```

## Limitations

- No closures (C doesn't support)
- No exceptions
- Manual memory management required
- Some F* patterns don't extract cleanly

## Resources

- Low* paper and tutorial
- Karamel documentation
- HACL* as example codebase
