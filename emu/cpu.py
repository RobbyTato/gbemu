import emu.memory
import emu.registers
import emu.rom
from emu.memory import test_bit, bit_set, bit_reset, bit_get_val
from emu.registers import FLAG_Z, FLAG_C, FLAG_H, FLAG_N


#
#               LITTLE
#             ENDIANNESS
#                DONT
#               FORGET
#
# So for example if the stack pointer is 0xff00 and I want to load it into address 0x1234, the instruction would look like this: 0x08 0x34 0x12 And memory at 0x1234 and 0x1235 would look like this?: 0x1234 - 0x00 0x1235 - 0xff Is that correct?
#

class CPU:
    def __init__(self, rom=None):
        self.MEMORY = emu.memory.Memory(rom)
        self.REGISTERS = self.MEMORY.registers
        self.clockcycles = 0
        self.MEMORY.init()

    def update(self):
        MAX_CYCLES_PER_SECOND = 4194304
        MAX_CYCLES = MAX_CYCLES_PER_SECOND / 60
        cyclesthisupdate = 0

        while cyclesthisupdate < MAX_CYCLES:
            cycles = self.execute_next_opcode()
            cyclesthisupdate += cycles
            self.clockcycles += cycles
            self.MEMORY.update_timers(cycles)
            self.MEMORY.update_graphics(cycles)
            self.MEMORY.do_interrupts()

        self.MEMORY.render_screen()

    def set_reg(self, reg, val):
        self.REGISTERS.__setattr__(reg, val)

    def get_reg(self, reg):
        return self.REGISTERS.__getattribute__(reg)

    def execute_next_opcode(self):
        opcode = self.MEMORY.read(self.REGISTERS.pc)
        self.REGISTERS.pc += 1
        return self.execute_opcode(opcode)

    def execute_opcode(self, opcode) -> int:
        if opcode > 0xFF:
            raise ValueError("Unknown opcode")
        # NOP
        elif opcode == 0x00:
            return 4

        # LD load
        elif opcode == 0x2:
            self.MEMORY.write(self.REGISTERS.bc, self.REGISTERS.a)
            return 8

        elif opcode == 0x12:
            self.MEMORY.write(self.REGISTERS.de, self.REGISTERS.a)
            return 8

        elif opcode == 0x22:
            self.MEMORY.write(self.REGISTERS.hl, self.REGISTERS.a)
            self.REGISTERS.hl += 1
            return 8
        elif opcode == 0x32:
            self.MEMORY.write(self.REGISTERS.hl, self.REGISTERS.a)
            self.REGISTERS.hl -= 1
            return 8
        elif opcode == 0x6:
            self.set_reg("b", self.get_n_byte())
            return 8
        elif opcode == 0x16:
            self.set_reg("d", self.get_n_byte())
            return 8
        elif opcode == 0x26:
            self.set_reg("h", self.get_n_byte())
            return 8
        elif opcode == 0x36:
            self.MEMORY.write(self.REGISTERS.hl, self.get_n_byte())
            return 12
        elif opcode == 0xa:
            self.set_reg("a", self.MEMORY.read(self.REGISTERS.bc))
            return 8
        elif opcode == 0x1a:
            self.set_reg("a", self.MEMORY.read(self.REGISTERS.de))
            return 8
        elif opcode == 0x2a:
            self.set_reg("a", self.MEMORY.read(self.REGISTERS.hl))
            self.REGISTERS.hl += 1
            return 8
        elif opcode == 0x3a:
            self.set_reg("a", self.MEMORY.read(self.REGISTERS.hl))
            self.REGISTERS.hl -= 1
            return 8
        elif opcode == 0xe:
            self.set_reg("c", self.get_n_byte())
            return 8
        elif opcode == 0x1e:
            self.set_reg("e", self.get_n_byte())
            return 8
        elif opcode == 0x2e:
            self.set_reg("l", self.get_n_byte())
            return 8
        elif opcode == 0x3e:
            self.set_reg("a", self.get_n_byte())
            return 8
        elif opcode == 0x40:
            self.set_reg("b", self.REGISTERS.b)
            return 4
        elif opcode == 0x41:
            self.set_reg("b", self.REGISTERS.c)
            return 4
        elif opcode == 0x42:
            self.set_reg("b", self.REGISTERS.d)
            return 4
        elif opcode == 0x43:
            self.set_reg("b", self.REGISTERS.e)
            return 4
        elif opcode == 0x44:
            self.set_reg("b", self.REGISTERS.h)
            return 4
        elif opcode == 0x45:
            self.set_reg("b", self.REGISTERS.l)
            return 4
        elif opcode == 0x46:
            self.set_reg("b", self.MEMORY.read(self.REGISTERS.hl))
            return 8
        elif opcode == 0x47:
            self.set_reg("b", self.REGISTERS.a)
            return 4
        elif opcode == 0x48:
            self.set_reg("c", self.REGISTERS.b)
            return 4
        elif opcode == 0x49:
            self.set_reg("c", self.REGISTERS.c)
            return 4
        elif opcode == 0x4a:
            self.set_reg("c", self.REGISTERS.d)
            return 4
        elif opcode == 0x4b:
            self.set_reg("c", self.REGISTERS.e)
            return 4
        elif opcode == 0x4c:
            self.set_reg("c", self.REGISTERS.h)
            return 4
        elif opcode == 0x4d:
            self.set_reg("c", self.REGISTERS.l)
            return 4
        elif opcode == 0x4e:
            self.set_reg("c", self.MEMORY.read(self.REGISTERS.hl))
            return 8
        elif opcode == 0x4f:
            self.set_reg("c", self.REGISTERS.a)
            return 4
        elif opcode == 0x50:
            self.set_reg("d", self.REGISTERS.b)
            return 4
        elif opcode == 0x51:
            self.set_reg("d", self.REGISTERS.c)
            return 4
        elif opcode == 0x52:
            self.set_reg("d", self.REGISTERS.d)
            return 4
        elif opcode == 0x53:
            self.set_reg("d", self.REGISTERS.e)
            return 4
        elif opcode == 0x54:
            self.set_reg("d", self.REGISTERS.h)
            return 4
        elif opcode == 0x55:
            self.set_reg("d", self.REGISTERS.l)
            return 4
        elif opcode == 0x56:
            self.set_reg("d", self.MEMORY.read(self.REGISTERS.hl))
            return 8
        elif opcode == 0x57:
            self.set_reg("d", self.REGISTERS.a)
            return 4
        elif opcode == 0x58:
            self.set_reg("e", self.REGISTERS.b)
            return 4
        elif opcode == 0x59:
            self.set_reg("e", self.REGISTERS.c)
            return 4
        elif opcode == 0x5a:
            self.set_reg("e", self.REGISTERS.d)
            return 4
        elif opcode == 0x5b:
            self.set_reg("e", self.REGISTERS.e)
            return 4
        elif opcode == 0x5c:
            self.set_reg("e", self.REGISTERS.h)
            return 4
        elif opcode == 0x5d:
            self.set_reg("e", self.REGISTERS.l)
            return 4
        elif opcode == 0x5e:
            self.set_reg("e", self.MEMORY.read(self.REGISTERS.hl))
            return 8
        elif opcode == 0x5f:
            self.set_reg("e", self.REGISTERS.a)
            return 4
        elif opcode == 0x60:
            self.set_reg("h", self.REGISTERS.b)
            return 4
        elif opcode == 0x61:
            self.set_reg("h", self.REGISTERS.c)
            return 4
        elif opcode == 0x62:
            self.set_reg("h", self.REGISTERS.d)
            return 4
        elif opcode == 0x63:
            self.set_reg("h", self.REGISTERS.e)
            return 4
        elif opcode == 0x64:
            self.set_reg("h", self.REGISTERS.h)
            return 4
        elif opcode == 0x65:
            self.set_reg("h", self.REGISTERS.l)
            return 4
        elif opcode == 0x66:
            self.set_reg("h", self.MEMORY.read(self.REGISTERS.hl))
            return 8
        elif opcode == 0x67:
            self.set_reg("h", self.REGISTERS.a)
            return 4
        elif opcode == 0x68:
            self.set_reg("l", self.REGISTERS.b)
            return 4
        elif opcode == 0x69:
            self.set_reg("l", self.REGISTERS.c)
            return 4
        elif opcode == 0x6a:
            self.set_reg("l", self.REGISTERS.d)
            return 4
        elif opcode == 0x6b:
            self.set_reg("l", self.REGISTERS.e)
            return 4
        elif opcode == 0x6c:
            self.set_reg("l", self.REGISTERS.h)
            return 4
        elif opcode == 0x6d:
            self.set_reg("l", self.REGISTERS.l)
            return 4
        elif opcode == 0x6e:
            self.set_reg("l", self.MEMORY.read(self.REGISTERS.hl))
            return 8
        elif opcode == 0x6f:
            self.set_reg("l", self.REGISTERS.a)
            return 4
        elif opcode == 0x70:
            self.MEMORY.write(self.REGISTERS.hl, self.REGISTERS.b)
            return 8
        elif opcode == 0x71:
            self.MEMORY.write(self.REGISTERS.hl, self.REGISTERS.c)
            return 8
        elif opcode == 0x72:
            self.MEMORY.write(self.REGISTERS.hl, self.REGISTERS.d)
            return 8
        elif opcode == 0x73:
            self.MEMORY.write(self.REGISTERS.hl, self.REGISTERS.e)
            return 8
        elif opcode == 0x74:
            self.MEMORY.write(self.REGISTERS.hl, self.REGISTERS.h)
            return 8
        elif opcode == 0x75:
            self.MEMORY.write(self.REGISTERS.hl, self.REGISTERS.l)
            return 8
        elif opcode == 0x77:
            self.MEMORY.write(self.REGISTERS.hl, self.REGISTERS.a)
            return 8
        elif opcode == 0x78:
            self.set_reg("a", self.REGISTERS.b)
            return 4
        elif opcode == 0x79:
            self.set_reg("a", self.REGISTERS.c)
            return 4
        elif opcode == 0x7a:
            self.set_reg("a", self.REGISTERS.d)
            return 4
        elif opcode == 0x7b:
            self.set_reg("a", self.REGISTERS.e)
            return 4
        elif opcode == 0x7c:
            self.set_reg("a", self.REGISTERS.h)
            return 4
        elif opcode == 0x7d:
            self.set_reg("a", self.REGISTERS.l)
            return 4
        elif opcode == 0x7e:
            self.set_reg("a", self.MEMORY.read(self.REGISTERS.hl))
            return 8
        elif opcode == 0x7f:
            self.set_reg("a", self.REGISTERS.a)
            return 4

    def get_n_byte(self):
        n = self.MEMORY.read(self.REGISTERS.pc)
        self.REGISTERS.pc += 1
        return n

    def get_nn_bytes(self):
        n1 = self.MEMORY.read(self.REGISTERS.pc)
        n2 = self.MEMORY.read(self.REGISTERS.pc + 1)
        self.REGISTERS.pc += 2
        return (n2 << 8) | n1

    def add8bit(self, reg, to_add, use_immediate, add_carry):
        before = self.get_reg(reg)

        if use_immediate:
            n = self.MEMORY.read(self.REGISTERS.pc)
            self.REGISTERS.pc += 1
            adding = n
        else:
            adding = to_add

        if add_carry:
            if test_bit(self.REGISTERS.f, FLAG_C):
                adding += 1

        ans = before + adding

        if ans > 0xFF:
            ans -= 0x100

        self.set_reg(reg, ans)
        self.REGISTERS.f = 0

        if ans == 0:
            self.REGISTERS.f = bit_set(self.REGISTERS.f, FLAG_Z)

        htest = before & 0xF
        htest += adding & 0xF

        if htest > 0xF:
            self.REGISTERS.f = bit_set(self.REGISTERS.f, FLAG_H)

        if before + adding > 0xFF:
            self.REGISTERS.f = bit_set(self.REGISTERS.f, FLAG_C)

    def sub8bit(self, reg, to_sub, use_immediate, sub_carry):
        before = self.get_reg(reg)

        if use_immediate:
            n = self.MEMORY.read(self.REGISTERS.pc)
            self.REGISTERS.pc += 1
            subbing = n
        else:
            subbing = to_sub

        if sub_carry:
            if test_bit(self.REGISTERS.f, FLAG_C):
                subbing += 1

        ans = before - subbing

        if ans < 0:
            ans += 0x100

        self.set_reg(reg, ans)
        self.REGISTERS.f = 0

        if ans == 0:
            self.REGISTERS.f = bit_set(self.REGISTERS.f, FLAG_Z)

        htest = before & 0xF
        htest -= subbing & 0xF

        if htest < 0:
            self.REGISTERS.f = bit_set(self.REGISTERS.f, FLAG_H)

        if before < subbing:
            self.REGISTERS.f = bit_set(self.REGISTERS.f, FLAG_C)

    def xor8bit(self, reg, to_xor, use_immediate):
        before = self.get_reg(reg)

        if use_immediate:
            n = self.MEMORY.read(self.REGISTERS.pc)
            self.REGISTERS.pc += 1
            xor = n
        else:
            xor = to_xor

        ans = before ^ xor

        self.set_reg(reg, ans)
        self.REGISTERS.f = 0

        if ans == 0:
            self.REGISTERS.f = bit_set(self.REGISTERS.f, FLAG_Z)

    def rrc8bit(self, reg):
        val = self.get_reg(reg)
        is_lsb_set = test_bit(val, 0)

        self.REGISTERS.f = 0

        val >>= 1

        if is_lsb_set:
            self.REGISTERS.f = bit_set(self.REGISTERS.f, FLAG_C)
            val = bit_set(val, 7)

        if val == 0:
            self.REGISTERS.f = bit_set(self.REGISTERS.f, FLAG_Z)

        self.set_reg(reg, val)

    def test8bit(self, reg, bit):
        if test_bit(self.get_reg(reg), bit):
            self.REGISTERS.f = bit_reset(self.REGISTERS.f, FLAG_Z)
        else:
            self.REGISTERS.f = bit_set(self.REGISTERS.f, FLAG_Z)

        self.REGISTERS.f = bit_reset(self.REGISTERS.f, FLAG_N)
        self.REGISTERS.f = bit_set(self.REGISTERS.f, FLAG_H)
