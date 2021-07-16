ld1 = [
    (0x02, ("address", "bc"), ("register", "a"), 8),
    (0x12, ("address", "de"), ("register", "a"), 8),
    (0x22, ("address", "hl"), ("register", "a"), 8),
    (0x32, ("address", "hl"), ("register", "a"), 8),
    (0x06, ("register", "b"), ("immediate", "8"), 8),
    (0x16, ("register", "d"), ("immediate", "8"), 8),
    (0x26, ("register", "h"), ("immediate", "8"), 8),
    (0x36, ("address", "hl"), ("immediate", "8"), 12),
    (0x0A, ("register", "a"), ("address", "bc"), 8),
    (0x1A, ("register", "a"), ("address", "de"), 8),
    (0x2A, ("register", "a"), ("address", "hl"), 8),
    (0x3A, ("register", "a"), ("address", "hl"), 8),
    (0x0E, ("register", "c"), ("immediate", "8"), 8),
    (0x1E, ("register", "e"), ("immediate", "8"), 8),
    (0x2E, ("register", "l"), ("immediate", "8"), 8),
    (0x3E, ("register", "a"), ("immediate", "8"), 8)
]

list = ["b", "c", "d", "e", "h", "l", "hl", "a"]

base = 0x40

for i in list:
    for j in list:
        ld1.append((base, ("register" if i != "hl" else "address", i), ("register" if j != "hl" else "address", j), 8 if any([i == "hl", j == "hl"]) else 4))
        base += 1


with open("result.py", "a") as f:
    for v in ld1:
        f.write(f"elif opcode == {hex(v[0])}:\n")
        if v[1][0] == "address":
            f.write(f"\tself.MEMORY.write(self.REGISTERS.{v[1][1]}, ")
        elif v[1][0] == "register":
            f.write(f"\tself.set_reg(\"{v[1][1]}\", ")
        elif v[1][0] == "immediate":
            f.write(f"\tself.MEMORY.write(self.get_nn_bytes(), ")
        if v[2][0] == "address":
            f.write(f"self.MEMORY.read(self.REGISTERS.{v[2][1]}))\n")
        elif v[2][0] == "register":
            f.write(f"self.REGISTERS.{v[2][1]})\n")
        elif v[2][0] == "immediate":
            f.write(f"self.get_n_byte())\n")
        f.write(f"\treturn {v[3]}\n")
