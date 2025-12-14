# F* Module System and Build

## Module Basics

### Module Declaration
```fstar
module MyProject.Utils    // Hierarchical naming

// File must be named MyProject.Utils.fst (dots in filename)
// Can be placed anywhere on --include path: src/MyProject.Utils.fst
// Note: MyProject/Utils.fst would define module "Utils", not "MyProject.Utils"
```

### Importing Modules
```fstar
open FStar.List.Tot           // Bring all names into scope
module L = FStar.List.Tot     // Alias full module name

// Qualified access
let x = FStar.List.Tot.length [1;2;3]
let y = L.length [1;2;3]      // Use alias directly
```

**Note**: Dots are namespace separators but `FStar.List` is not a module itself - `FStar.List.Tot` is a distinct module name.

### Shadowing
Opening modules can shadow names:
```fstar
open FStar.List.Tot    // imports 'length'
open MyModule          // if MyModule also has 'length', it shadows

// Solution: use qualified names or aliases
let n = FStar.List.Tot.length xs
```

## Interface Files (.fsti)

### Abstract Types
```fstar
// Counter.fsti - public interface
module Counter
val t : Type0              // Abstract type (implementation hidden)
val create : unit -> t
val increment : t -> t
val value : t -> nat

// Counter.fst - implementation
module Counter
type t = nat               // Reveal the representation
let create () = 0
let increment x = x + 1
let value x = x
```

### Hiding Implementation Details
```fstar
// Secrets.fsti
module Secrets
val hash : string -> string    // Signature only

// Secrets.fst
module Secrets
let internal_key = "secret"    // Not exposed
let hash s = ...               // Implementation hidden
```

## Include Paths

### Command Line
```bash
# Single include
fstar.exe --include ./lib MyModule.fst

# Multiple includes
fstar.exe --include ./lib --include ./src MyModule.fst

# Relative to project root
fstar.exe --include src/core --include src/utils Main.fst
```

### FSTAR_HOME
The standard library is found via the F* installation. With mise:
```bash
# Find library location
fstar.exe --locate_lib    # Library root (ulib)
fstar.exe --locate        # Install root

# FSTAR_HOME set automatically by mise
echo $FSTAR_HOME
```

## Dependencies

### Generating Dependency Info
```bash
# Full dependency info (Makefile format, preferred)
fstar.exe --dep full MyModule.fst

# GraphViz format (for visualization)
fstar.exe --dep graph MyModule.fst > deps.dot
dot -Tpng deps.dot -o deps.png

# Note: --dep make is deprecated, use --dep full instead
```

### Dependency Order
F* verifies modules in dependency order. For multi-file projects:
```bash
# List files explicitly in dependency order
fstar.exe Lib.fst Utils.fst Main.fst

# Or use --dep full output with Make to handle ordering
fstar.exe --dep full --include src src/Main.fst > .depend
# Then use Make rules from .depend
```

## Caching

### Checked Files (.checked)
```bash
# Generate .checked files for faster re-verification
fstar.exe --cache_checked_modules MyModule.fst
# Short form: fstar.exe -c MyModule.fst

# Specify cache directory (reads and writes)
fstar.exe -c --cache_dir .fstar_cache MyModule.fst

# Reuse cached files: just run again with same --cache_dir
# F* reads existing .checked files automatically

# Force recheck (ignore cache)
fstar.exe --force MyModule.fst

# Disable caching entirely
fstar.exe --cache_off MyModule.fst
```

### Cache Invalidation
Checked files are invalidated when:
- Source file changes
- Any dependency changes
- F* version changes
- Command-line options differ

### Typical Project Setup
```
project/
├── .fstar_cache/          # Cached .checked files
├── src/
│   ├── Lib.fst
│   ├── Lib.fsti
│   └── Main.fst
├── Makefile
└── mise.toml
```

## Makefile Pattern

```makefile
FSTAR=fstar.exe
FSTAR_FLAGS=--cache_checked_modules --cache_dir .fstar_cache

# Source files in dependency order
SOURCES=src/Lib.fst src/Utils.fst src/Main.fst

.PHONY: verify clean

verify: $(SOURCES)
	$(FSTAR) $(FSTAR_FLAGS) --include src $^

# Generate dependency info
deps:
	$(FSTAR) --dep full --include src src/Main.fst

clean:
	rm -rf .fstar_cache
```

## Hints (for reproducible verification)

### Recording Hints
```bash
# Record successful SMT proofs
fstar.exe --record_hints MyModule.fst

# Hints stored in .hints files
```

### Using Hints
```bash
# Use recorded hints
fstar.exe --use_hints MyModule.fst

# Specify hints directory
fstar.exe --use_hints --hint_dir ./hints MyModule.fst
```

### Why Use Hints?
- Faster re-verification
- More reproducible proofs (less sensitivity to Z3 randomness)
- CI stability
