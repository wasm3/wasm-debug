# wasm-debug

Direct, source-level WebAssembly debugger

**This is work-in-progress, and highly experimental!**

We're exploring the possibility of **direct**, **source-level** debugging of WebAssembly binaries.  
`rustc`/`clang` compilers can generate DWARF debug info, and embed it into the **wasm** binaries,  
however debuggers like `gdb`/`lldb` currently do not know how to work with such files directly.

Achievements:
- Created `wasm2dbg.py` utility to repackage the DWARF info from `wasm` to `elf` format.  
  The resulting file can be loaded into unmodified versions of debuggers.
- Created `gdb-stub.py`, which uses **GDB Remote Serial Protocol** to communicate to `gdb` and `lldb`.  
  This a prototype of a VM that succesfully emulates a breakpoint hit.  

Next:
- Implement `Wasm3`-based opcode-level debugger
- Connect `Wasm3` to `gdb`/`lldb` via `Remote Serial Protocol`

It's all just a prototype.  
This work should actually be a good starting point to start adding direct **wasm** support to debuggers.

## Building test apps

See [Rust](test_app_rust/README.md) and [C](test_app_c/README.md) example apps.

## Extracting DWARF debug info

```sh
./wasm2dbg.py ./test_app_c/app.wasm

# Strip debug info from the wasm file (optional):
wasm-strip ./test_app_c/app.wasm
```

## Debugging

```sh
# Using GDB:
./prototype/gdbstub.py &
cd test_app_c
gdb -q -x ../.gdbscript app.wasm.dbg

# Or LLDB:
./prototype/gdbstub.py &
cd test_app_c
lldb -s ../.lldbscript app.wasm.dbg
```

### Examining the GDB RSP protocol

To debug the RSP packets, it's convenient to use `tcpdump` + `tcpflow`:

```sh
sudo tcpdump -i lo -l -w - port 4444 | tcpflow -C -g -r -
```

Also, debuggers provide built-in logs for this:

GDB:
```log
(gdb) set debug remote 1
```

GDB, log to a separate file:
```log
(gdb) set remotelogfile gdb-rsp.log
```

LLDB:
```log
(lldb) log enable gdb-remote packets
```

### Examining the produced wasm binaries

After building the app, it may be interesting to inspect WASM contents.  
There are multiple tools for that, here are some examples:

```sh
llvm-objdump-10 -h app.wasm
llvm-dwarfdump-10 app.wasm --all -o app.dwarfdump
wasm-objdump -hxd app.wasm > app.objdump
wasm-dis -sm app.wasm.map app.wasm -o app.dis
wasm-decompile app.wasm -o app.decompile
```

### License
This project is released under The MIT License (MIT)
