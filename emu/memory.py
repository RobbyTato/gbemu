MEMORY_SIZE = 0x10000

class Memory:
    def __init__(self, bootstrap = None, rom = None):
        self.memory = [0x00] * MEMORY_SIZE
        if bootstrap:
            self.memory[0:len(bootstrap)] = bootstrap