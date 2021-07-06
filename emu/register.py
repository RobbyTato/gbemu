MAX_BYTE_VALUE = 2**8

class Registers:
    
    def __init__(self, a = 0, b = 0, c = 0, d = 0, e = 0, f = 0, h = 0, l = 0, pc = 0, sp = 0):
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.e = e
        self.f = f
        self.h = h
        self.l = l
        self.pc = pc
        self.sp = sp
    
    @property
    def af(self):
        return (self.a * MAX_BYTE_VALUE) + self.f

    @af.setter
    def af(self, val):
        self.a = val // MAX_BYTE_VALUE
        self.f = val % MAX_BYTE_VALUE
    
    @property
    def bc(self):
        return (self.b * MAX_BYTE_VALUE) + self.c

    @bc.setter
    def bc(self, val):
        self.b = val // MAX_BYTE_VALUE
        self.c = val % MAX_BYTE_VALUE
    
    @property
    def de(self):
        return (self.d * MAX_BYTE_VALUE) + self.e
    
    @de.setter
    def de(self, val):
        self.d = val // MAX_BYTE_VALUE 
        self.e = val % MAX_BYTE_VALUE
    
    @property
    def hl(self):
        return (self.h * MAX_BYTE_VALUE) + self.l

    @hl.setter
    def hl(self, val):
        self.h = val // MAX_BYTE_VALUE
        self.l = val % MAX_BYTE_VALUE

if __name__ == "__main__":
    reg = Registers()

    print("Test 1: Checking getter for 8 and 16 bit registers")
    reg.a = 0b11110000
    reg.f = 0b00001111
    print("A:", reg.a)
    assert(reg.a == 240)
    print("F:", reg.f)
    assert(reg.f == 15)
    print("AF:", reg.af)
    assert(reg.af == 61455)

    print()

    print("Test 2: Checking setter for 16 bit registers")
    reg.af = 0b1010101010101010
    print("A:", reg.a)
    assert(reg.a == 170)
    print("F:", reg.f)
    assert(reg.f == 170)
    print("AF:", reg.af)
    assert(reg.af == 43690)

        