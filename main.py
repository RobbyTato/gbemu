from emu.rom import *
from emu.memory import *
from emu.cpu import *
from emu import *

if __name__ == "__main__":
    # Quick CPU memory test
    cpu = CPU()
    print(cpu.memory[0:4])
    print(cpu.get_opcode())
    print(cpu.get_opcode())
    print(cpu.get_opcode())
    print(cpu.get_opcode())
