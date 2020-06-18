#!/usr/bin/env python3

"""
Project:  Wasm3
File:     wasm2dbg.py
Author:   Volodymyr Shymanskyy
Created:  18.06.2020
"""

import re
import tempfile
import os
from shutil import which

infile = "test_app_c/app.wasm"
outfile = infile + ".dbg"

class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

sections = [
    "CODE",
    ".debug_info", ".debug_macinfo", ".debug_ranges",
    ".debug_abbrev", ".debug_line", ".debug_str"
]

utils = dotdict({
    "objdump": "llvm-objdump-10",
    "objcopy": "objcopy",
    "tail":    "tail",
    "xxd":     "xxd",
})

for name, exe in utils.items():
    if not which(exe):
        raise Exception(f"{exe} utility not found")

tmp = tempfile.TemporaryDirectory()

# Extract DWARF info from WASM file
for sect in sections:
    os.system(f"{utils.objdump} -s --section {sect} {infile} | {utils.tail} -n +5 | {utils.xxd} -r > {tmp.name}/section-{sect}")

# Create a dummy binary file
with open(f"{tmp.name}/empty.bin", 'w') as f:
     f.write("wasm")

# Create an ELF container with DWARF info
os.system(f"""
{utils.objcopy} -I binary -O elf32-i386 -B i386 \
  --add-section .debug_str={tmp.name}/section-.debug_str \
  --add-section .debug_line={tmp.name}/section-.debug_line \
  --add-section .debug_abbrev={tmp.name}/section-.debug_abbrev \
  --add-section .debug_ranges={tmp.name}/section-.debug_ranges \
  --add-section .debug_macinfo={tmp.name}/section-.debug_macinfo \
  --add-section .debug_info={tmp.name}/section-.debug_info \
  --add-section .text={tmp.name}/section-CODE \
  {tmp.name}/empty.bin {outfile}
""")
