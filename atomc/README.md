# AtomC — Rynx 2.0 Intercompiler

Industrial-grade formal implementation of the Rynx 2.0 language engine.  
**Not a demo. Not a toy.** Full compile-time analysis and direct AST execution.

## Requirements

- Python 3.10+

## System

- **Language**: Rynx (.ryx source)
- **Tools**: rxc (compiler), rxopt (optimizer), rxld (linker), rxrun (runtime)
- **AtomC Developer Console**: TUI for running the toolchain

## Toolchain (build pipeline)

1. **Compile** — `.ryx` → `.ro` (object)  
   `rxc src/main.ryx -o main.ro`

2. **Optimize** — `.ro` → `.ro`  
   `rxopt main.ro -O2 -o main.opt.ro`

3. **Link** — `.ro` → `.rxe` (executable)  
   `rxld main.opt.ro -o app.rxe`

4. **Run** — execute `.rxe`  
   `rxrun app.rxe`

## Usage

### Toolchain (separate steps)

```bash
# Compile
python -m atomc.tools.rxc atomc/examples/hello.ryx -o main.ro

# Optimize
python -m atomc.tools.rxopt main.ro -O2 -o main.opt.ro

# Link
python -m atomc.tools.rxld main.opt.ro -o app.rxe

# Run
python -m atomc.tools.rxrun app.rxe
```

### AtomC Developer Console (TUI)

```bash
python -m atomc.console.console
```

Then at the prompt:

```
> rxc src/main.ryx -o main.ro
> rxopt main.ro -O2 -o main.opt.ro
> rxld main.opt.ro -o app.rxe
> rxrun app.rxe
Hello, World
```

### One-shot run (legacy)

```bash
python -m atomc.cli.atomc run atomc/examples/hello.ryx
python -m atomc.cli.atomc check atomc/examples/hello.ryx
```

Exit codes:

- `0` — success (end 0)
- `1` — runtime error (end 1 or RX5xx)
- `2` — compile error (RX1xx / RX2xx)

## Examples

- `examples/hello.ryx` — minimal start / end 0
- `examples/factorial.ryx` — task, when/else, loop, show

## Execution model

Every executable Rynx program must have:

```ryx
start {
    ...
    end 0;   // or end 1;
}
```

Missing `start`/`end` → **RX213 Execution block missing** (execution structure error, not syntax error).

## Error format

Compile and runtime errors follow the Rynx 2.0 Error & Diagnostics Specification:  
`[RYNX COMPILE ERROR] RX###: ...` or `[RYNX RUNTIME ERROR] RX###: ...`  
with File, Line, Column, and snippet. First error only. Deterministic.

## License

See LICENSE.
