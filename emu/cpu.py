import emu.memory
import emu.registers
import emu.rom

class CPU:
    def __init__(self):
        self.memory = emu.memory.Memory(emu.rom.get_DMGbootstrap()).memory
        self.registers = emu.registers.Registers(pc=-1) # we want get_opcode to start at address 0

    def get_opcode(self):
        self.registers.pc += 1
        return self.memory[self.registers.pc]

    
        

    