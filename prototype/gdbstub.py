#!/usr/bin/env python3

"""
Project:  Wasm3
File:     gdbstub.py
Author:   Volodymyr Shymanskyy
Created:  18.06.2020
"""

import re
import socket
import binascii

HOST = '127.0.0.1'
PORT = 4444
PACKET_SIZE = 4096

FAKE_BREAK = 0x000001A6

regsInfo = [
    b'name:eax;bitsize:32;offset:80;encoding:uint;format:hex;set:General Purpose Registers;ehframe:0;dwarf:0;',
    b'name:ecx;bitsize:32;offset:88;encoding:uint;format:hex;set:General Purpose Registers;ehframe:1;dwarf:1;',
    b'name:edx;bitsize:32;offset:96;encoding:uint;format:hex;set:General Purpose Registers;ehframe:2;dwarf:2;',
    b'name:ebx;bitsize:32;offset:40;encoding:uint;format:hex;set:General Purpose Registers;ehframe:3;dwarf:3;',
    b'name:esp;alt-name:sp;bitsize:32;offset:152;encoding:uint;format:hex;set:General Purpose Registers;ehframe:4;dwarf:4;generic:sp;',
    b'name:ebp;alt-name:fp;bitsize:32;offset:32;encoding:uint;format:hex;set:General Purpose Registers;ehframe:5;dwarf:5;generic:fp;',
    b'name:esi;bitsize:32;offset:104;encoding:uint;format:hex;set:General Purpose Registers;ehframe:6;dwarf:6;',
    b'name:edi;bitsize:32;offset:112;encoding:uint;format:hex;set:General Purpose Registers;ehframe:7;dwarf:7;',

    b'name:eip;alt-name:pc;bitsize:32;offset:128;encoding:uint;format:hex;set:General Purpose Registers;ehframe:8;dwarf:8;generic:pc;',
    b'name:eflags;alt-name:flags;bitsize:32;offset:144;encoding:uint;format:hex;set:General Purpose Registers;ehframe:9;dwarf:9;generic:flags;',

    b'name:cs;bitsize:32;offset:136;encoding:uint;format:hex;set:General Purpose Registers;dwarf:41;',
    b'name:ss;bitsize:32;offset:160;encoding:uint;format:hex;set:General Purpose Registers;dwarf:42;',
    b'name:ds;bitsize:32;offset:184;encoding:uint;format:hex;set:General Purpose Registers;dwarf:43;',
    b'name:es;bitsize:32;offset:192;encoding:uint;format:hex;set:General Purpose Registers;dwarf:40;',
    b'name:fs;bitsize:32;offset:200;encoding:uint;format:hex;set:General Purpose Registers;dwarf:44;',
    b'name:gs;bitsize:32;offset:208;encoding:uint;format:hex;set:General Purpose Registers;dwarf:45;',
]

if __name__ == '__main__':

    singleRun = True

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        s.bind((HOST, PORT))
        s.listen()
        while True:
            print('Waiting for GDB conection...')
            conn, addr = s.accept()
            with conn:
                print('Connected by', addr)
                buff = b""
                hasAck = True

                def sendPacket(p):
                    checksum = sum(p) % 256
                    rsp = (b'$', p, b'#', b'%.2x' % checksum)
                    rsp = b''.join(rsp)
                    #print(f"<< {rsp}")
                    conn.sendall(rsp)
                    if hasAck:
                        conn.recv(1) # Get '+'
                        
                def hex_num(n):
                    return int(n).to_bytes(4, byteorder='little').hex().encode('utf8')

                def hex_str(s):
                    return binascii.hexlify(str(s).encode('utf8'))
                
                conn.recv(1) # Get initial '+'

                while True:
                    packet = conn.recv(PACKET_SIZE)
                    if not packet:
                        break
                    
                    cmd = None
                    buff += packet
                    if buff[:1] == b'\x03' :
                        cmd = "vCtrlC"
                        buff = buff[1:]
                    elif buff[:1] == b'+':
                        cmd = buff[:1].decode('utf8')
                        buff = buff[1:]
                    else:
                        m = re.match(b'\\$(?P<data>.*?)#(?P<checksum>..)', buff)
                        if m:
                            data = m.group('data')
                            checksum = int(m.group('checksum'), 16)
                            if sum(data) % 256 != checksum:
                                raise ChecksumError('Invalid packet checksum')

                            cmd = data.decode('utf8')
                            buff = buff[m.endpos+1:]

                    if cmd == None:
                        continue
                    
                    #print(f">> {cmd}")
                    if hasAck:
                        conn.sendall(b'+')
                    
                    if cmd == '+':
                        conn.sendall(b'+')
                    elif cmd == '!':
                        sendPacket(b'OK')
                    elif cmd.startswith("qSupported"):
                        sendPacket(b'swbreak+;hwbreak+;QStartNoAckMode+;PacketSize=%d' % PACKET_SIZE) #vContSupported+;
                    elif cmd == "QStartNoAckMode":
                        sendPacket(b'OK')
                        hasAck = False

                    elif cmd == "qHostInfo":
                        sendPacket(b'triple:7838365f36342d70632d6c696e75782d676e75;endian:little;ptrsize:8;')
                    elif cmd == "qProcessInfo":
                        sendPacket(b'pid:10b18;triple:693338362d70632d6c696e75782d676e75;ostype:linux;endian:little;ptrsize:4;')
                    elif cmd == "qOffsets":
                        sendPacket(b'Text=0;Data=0;Bss=0')
                    elif cmd == "qSymbol::":
                        sendPacket(b'OK')
                    #elif cmd == "vCont?":
                    #    sendPacket(b'vCont;c;C;t;s;S;r')
                    elif cmd.startswith("qRegisterInfo"):
                        num = int(cmd.replace("qRegisterInfo", ""), 16)
                        if num < len(regsInfo):
                            sendPacket(regsInfo[num])
                        else:
                            sendPacket(b'E45')
                    elif cmd.startswith("qMemoryRegionInfo:"):
                        addr = int(cmd.replace("qMemoryRegionInfo:", ""), 16)
                        sendPacket(b'start:0;size:1000;permissions:rx;name:5b7664736f5d;')

                    elif cmd == "?":
                        val = FAKE_BREAK
                        sendPacket(b'S%.2x' % 2)
                        #thread:10b18;name:app.elf;threads:10b18;
                        #sendPacket(b'T0200:00000000;01:00000000;02:00000000;03:00000000;04:00000000;05:00000000;06:00000000;07:f0cdffff;08:%s;09:00020000;0a:23000000;0b:00000000;0c:00000000;0d:2b000000;0e:2b000000;0f:2b000000;reason:signal;' % hex_num(val))

                    # Set Thread
                    elif cmd.startswith("H"):
                        sendPacket(b'OK')
                        
                    # Get Thread
                    elif cmd.startswith("qC"):
                        sendPacket(b'')

                    # Read Registers
                    elif cmd == "g":
                        
                        regs = [0,0,0,0,0,0,0,0, #EAX, ECX, EDX, EBX, ESP, EBP, ESI, EDI,
                                FAKE_BREAK,      #EIP
                                0,               #eflags
                                0,0,0,0,0,0]     #CS, SS, DS, ES, FS, GS
                        
                        regs = map(hex_num, regs)
                        sendPacket(b''.join(regs))

                    # Write Registers
                    #elif cmd == "G":
                    
                    # Read a Register
                    elif cmd.startswith("p"):
                        num = int(cmd[1:], 16)
                        if num == 8:
                            sendPacket(hex_num(FAKE_BREAK))
                        else:
                            sendPacket(b'00000000')

                    # Write a Register
                    #elif cmd == "P":

                    # Read Memory
                    #elif cmd == "m":

                    # Write Memory
                    #elif cmd == "M":

                    # Set Breakpoint
                    elif cmd.startswith("Z"):
                        args = cmd[1:].split(',')
                        args = list(map(lambda val: int(val, 16), args))
                        print("Break ", args)
                        sendPacket(b'OK')

                    # Clear Breakpoint
                    #elif cmd.startswith("z"):
                    
                    # Continue
                    elif cmd == "c" or cmd == "vCont;c":
                        sendPacket(b'OK')
                        
                        sendPacket(b'O' + hex_str("-> Debugging WebAssembly ^_^\n"))

                    # Step
                    elif cmd == "s" or cmd == "vCont;s":
                        sendPacket(b'OK')

                    elif cmd == "vCtrlC":
                        sendPacket(b'S%.2x' % 2)
                        
                    # Set Thread
                    elif cmd.startswith("k"):
                        sendPacket(b'OK')
                        break

                    else:
                        sendPacket(b'')
                
                if singleRun:
                    break
