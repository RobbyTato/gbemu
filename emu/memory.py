import emu.rom
import emu.registers


class Memory:
    MEMORY_SIZE = 0x10000
    RAM_BANK_TOTAL_SIZE = 0x8000

    def __init__(self, rom=None):
        self.memory = [0x00] * Memory.MEMORY_SIZE
        self.registers = emu.registers.Registers(pc=0x100, s=0xFF, p=0xFE, a=0x01, f=0xB0, b=0x00, c=0x13, d=0x00,
                                                 e=0xD8, h=0x01, l=0x4D)  # we want get_opcode to start at address 0
        self.timer_counter = 0
        self.divider_counter = 0

        self.interrupt_master = True

        self.memory_banking = self.get_memory_bank_setting()  # 1 for mbc1, 2 for mbc2

        self.rom_banking = 0
        self.current_rom_bank = 1

        self.ram_banks = [0x00] * Memory.RAM_BANK_TOTAL_SIZE
        self.current_ram_bank = 0

        self.cartridge_memory = (emu.rom.get_instructions(rom) if rom is not None else None)
        self.enable_ram = False

        self.screen_data = [[[0, 0, 0]] * 144 for _ in range(160)]
        self.scanline_counter = 456

        self.joypad_state = 0

    #############################################################################
    #                                                                           #
    #                           MEMORY READ AND WRITE                           #
    #                                                                           #
    #############################################################################

    def write(self, address, data):
        if address < 0x8000:  # ROM
            self.handle_banking(address, data)
        elif 0xFE00 > address >= 0xE000:  # ECHO ram also writes to RAM
            self.memory[address] = data
            self.write(address - 0x2000, data)
        elif 0xFEFF > address >= 0xFEA0:  # Restricted area
            return
        elif address == Memory.TMC:
            current_freq = self.get_clock_freq()
            self.memory[Memory.TMC] = data
            new_freq = self.get_clock_freq()
            if current_freq != new_freq:
                self.set_clock_freq()
        elif address == 0xFF04:
            self.memory[0xFF04] = 0
        elif 0xA000 <= address <= 0xC000:
            if self.enable_ram != 0:
                new_address = address - 0xA000
                self.ram_banks[new_address + (self.current_ram_bank * 0x2000)] = data
        elif address == 0xFF44:
            self.memory[0xFF44] = 0
        elif address == 0xFF46:
            self.do_dma_transfer(data)
        else:
            self.memory[address] = data

    def read(self, address):
        if 0x4000 <= address <= 0x7FFF:
            new_address = address - 0x4000
            return self.cartridge_memory[new_address + (self.current_rom_bank * 0x4000)]
        elif 0xA000 <= address <= 0xBFFF:
            new_address = address - 0xA000
            return self.ram_banks[new_address + (self.current_ram_bank * 0x2000)]
        elif 0xFF00 == address:
            return self.get_joypad_state()
        else:
            return self.memory[address]

    def init(self):
        self.memory[0xFF05] = 0x00
        self.memory[0xFF06] = 0x00
        self.memory[0xFF07] = 0x00
        self.memory[0xFF10] = 0x80
        self.memory[0xFF11] = 0xBF
        self.memory[0xFF12] = 0xF3
        self.memory[0xFF14] = 0xBF
        self.memory[0xFF16] = 0x3F
        self.memory[0xFF17] = 0x00
        self.memory[0xFF19] = 0xBF
        self.memory[0xFF1A] = 0x7F
        self.memory[0xFF1B] = 0xFF
        self.memory[0xFF1C] = 0x9F
        self.memory[0xFF1E] = 0xBF
        self.memory[0xFF20] = 0xFF
        self.memory[0xFF21] = 0x00
        self.memory[0xFF22] = 0x00
        self.memory[0xFF23] = 0xBF
        self.memory[0xFF24] = 0x77
        self.memory[0xFF25] = 0xF3
        self.memory[0xFF26] = 0xF1
        self.memory[0xFF40] = 0x91
        self.memory[0xFF42] = 0x00
        self.memory[0xFF43] = 0x00
        self.memory[0xFF45] = 0x00
        self.memory[0xFF47] = 0xFC
        self.memory[0xFF48] = 0xFF
        self.memory[0xFF49] = 0xFF
        self.memory[0xFF4A] = 0x00
        self.memory[0xFF4B] = 0x00
        self.memory[0xFFFF] = 0x00

    #############################################################################
    #                                                                           #
    #                           TIMER HANDLING CODE                             #
    #                                                                           #
    #############################################################################

    TIMA = 0xFF05
    TMA = 0xFF06
    TMC = 0xFF07

    CLOCKSPEED = 4194304

    def update_timers(self, cycles):
        self.do_divider_register(cycles)
        if self.is_clock_enabled():
            self.timer_counter -= cycles
            if self.timer_counter <= 0:
                self.set_clock_freq()
                if self.read(Memory.TIMA) == 255:
                    self.write(Memory.TIMA, self.read(Memory.TMA))
                    self.request_interrupt(2)
                else:
                    self.write(Memory.TIMA, self.read(Memory.TIMA) + 1)

    def do_divider_register(self, cycles):
        self.divider_counter += cycles
        if self.divider_counter >= 255:
            self.divider_counter = 0
            self.memory[0xFF04] += 1

    def is_clock_enabled(self):
        return test_bit(self.read(Memory.TMC), 2)

    def get_clock_freq(self):
        return self.read(Memory.TMC) & 0x3

    def set_clock_freq(self):
        freq = self.get_clock_freq()
        if freq == 0:
            self.timer_counter = 1024  # freq 4096
        elif freq == 1:
            self.timer_counter = 16  # freq 262144
        elif freq == 2:
            self.timer_counter = 64  # freq 65536
        elif freq == 3:
            self.timer_counter = 256  # freq 16382

    #############################################################################
    #                                                                           #
    #                         INTERRUPT HANDLING CODE                           #
    #                                                                           #
    #############################################################################

    def request_interrupt(self, _id):
        req = self.read(0xFF0F)
        req = bit_set(req, _id)
        self.write(0xFF0F, req)

    def do_interrupts(self):
        if self.interrupt_master:
            req = self.read(0xFF0F)
            enabled = self.read(0xFFFF)
            if req > 0:
                for i in range(0, 5):
                    if test_bit(req, i):
                        if test_bit(enabled, i):
                            self.service_interrupt(i)

    def service_interrupt(self, interrupt):
        self.interrupt_master = False
        req = self.read(0xFF0F)
        req = bit_reset(req, interrupt)
        self.write(0xFF0F, req)

        self.push_word_onto_stack(self.registers.pc)

        if interrupt == 0:
            self.registers.pc = 0x40
        elif interrupt == 1:
            self.registers.pc = 0x48
        elif interrupt == 2:
            self.registers.pc = 0x50
        elif interrupt == 4:
            self.registers.pc = 0x60

    def push_word_onto_stack(self, pc):
        ...

    #############################################################################
    #                                                                           #
    #                        MEMORY BANK HANDLING CODE                          #
    #                                                                           #
    #############################################################################

    def get_memory_bank_setting(self):
        setting = self.read(0x147)
        if setting == 1:
            self.memory_banking = 1
        elif setting == 2:
            self.memory_banking = 1
        elif setting == 3:
            self.memory_banking = 1
        elif setting == 5:
            self.memory_banking = 2
        elif setting == 6:
            self.memory_banking = 2
        else:
            return 0

    def handle_banking(self, address, data):
        if address < 0x2000:
            if self.memory_banking != 0:
                self.do_ram_bank_enable(address, data)
        elif 0x2000 <= address < 0x4000:
            if self.memory_banking != 0:
                self.do_change_lo_rom_bank(data)
        elif 0x4000 <= address < 0x6000:
            if self.memory_banking == 1:
                if self.rom_banking:
                    self.do_change_hi_rom_bank(data)
                else:
                    self.do_ram_bank_change(data)
        elif 0x6000 <= address < 0x8000:
            if self.memory_banking == 1:
                self.do_change_rom_ram_mode(data)

    def do_ram_bank_enable(self, address, data):
        if self.memory_banking == 2:
            if address & 0b10000 >= 1:
                return
        test_data = data & 0xF
        if test_data == 0xA:
            self.enable_ram = True
        elif test_data == 0x0:
            self.enable_ram = False

    def do_change_lo_rom_bank(self, data):
        if self.memory_banking == 2:
            self.current_rom_bank = data & 0xF
            if self.current_rom_bank == 0:
                self.current_rom_bank += 1
            return

        lower5 = data & 31
        self.current_rom_bank &= 224
        self.current_rom_bank |= lower5
        if self.current_rom_bank == 0:
            self.current_rom_bank += 1

    def do_change_hi_rom_bank(self, data):
        self.current_rom_bank &= 31
        data &= 224
        self.current_rom_bank |= data
        if self.current_rom_bank == 0:
            self.current_rom_bank += 1

    def do_ram_bank_change(self, data):
        self.current_ram_bank = data & 0x3

    def do_change_rom_ram_mode(self, data):
        new_data = data & 0x1
        self.rom_banking = not (new_data == 0)
        if self.rom_banking:
            self.current_ram_bank = 0

    #############################################################################
    #                                                                           #
    #                          GRAPHICS RENDERING CODE                          #
    #                                                                           #
    #############################################################################

    def render_screen(self):
        ...

    def update_graphics(self, cycles):
        self.set_lcd_status()

        if self.is_lcd_enabled():
            self.scanline_counter -= cycles
        else:
            return

        if self.scanline_counter <= 0:
            self.memory[0xFF44] += 1
            current_line = self.read(0xFF44)
            self.scanline_counter = 456
            if current_line == 144:
                self.request_interrupt(0)
            elif current_line > 153:
                self.memory[0xFF44] = 0
            elif current_line < 144:
                self.draw_scan_line()

    def draw_scan_line(self):
        control = self.read(0xFF40)
        if test_bit(control, 0):
            self.render_tiles()
        if test_bit(control, 1):
            self.render_sprites()

    def render_tiles(self):
        un_sig = True

        scroll_y = self.read(0xFF42)
        scroll_x = self.read(0xFF43)
        window_y = self.read(0xFF4A)
        window_x = self.read(0xFF4B) - 7

        using_window = False

        if test_bit(self.read(0xFF40), 5):
            if window_y <= self.read(0xFF44):
                using_window = True

        if test_bit(self.read(0xFF40), 4):
            tile_data = 0x8000
        else:
            tile_data = 0x8800
            un_sig = False

        if using_window is False:
            if test_bit(self.read(0xFF40), 3):
                background_memory = 0x9C00
            else:
                background_memory = 0x9800
        else:
            if test_bit(self.read(0xFF40), 6):
                background_memory = 0x9C00
            else:
                background_memory = 0x9800

        if not using_window:
            y_pos = scroll_y + self.read(0xFF44)
        else:
            y_pos = self.read(0xFF44) - window_y

        tile_row = (y_pos // 8) * 32  # TODO might be wrong (change // to /)

        for pixel in range(160):
            x_pos = pixel + scroll_x
            if using_window:
                if pixel >= window_x:
                    x_pos = pixel - window_x

            tile_col = x_pos / 8
            tile_address = background_memory + tile_row + tile_col

            if un_sig:
                tile_num = self.read(tile_address)
            else:
                tile_num = self.read(tile_address) - 128

            tile_location = tile_data

            if un_sig:
                tile_location += (tile_num * 16)
            else:
                tile_location += ((tile_num + 128) * 16)

            line = y_pos % 8
            line *= 2
            data1 = self.read(tile_location + line)
            data2 = self.read(tile_location + line + 1)

            colour_bit = x_pos % 8
            colour_bit -= 7
            colour_bit *= -1

            colour_num = bit_get_val(data2, colour_bit)
            colour_num <<= 1
            colour_num |= bit_get_val(data1, colour_bit)

            col = self.get_colour(colour_num, 0xFF47)
            red = 0
            green = 0
            blue = 0

            if col == 0:
                red = 255
                green = 255
                blue = 255
            elif col == 1:
                red = 0xCC
                green = 0xCC
                blue = 0xCC
            elif col == 2:
                red = 0x77
                green = 0x77
                blue = 0x77

            scanline = self.read(0xFF44)

            if scanline < 0 or scanline > 143 or pixel < 0 or pixel > 159:
                continue

            self.screen_data[pixel][scanline][0] = red
            self.screen_data[pixel][scanline][1] = green
            self.screen_data[pixel][scanline][2] = blue

    def render_sprites(self):
        use8x16 = False
        if test_bit(self.read(0xFF40), 2):
            use8x16 = True

        for sprite in range(40):
            index = sprite * 4
            y_pos = self.read(0xFE00 + index) - 16
            x_pos = self.read(0xFE00 + index + 1) - 8
            tile_location = self.read(0xFE00 + index + 2)
            attributes = self.read(0xFE00 + index + 3)

            y_flip = test_bit(attributes, 6)
            x_flip = test_bit(attributes, 5)

            scanline = self.read(0xFF44)

            y_size = 8
            if use8x16:
                y_size = 16

            if y_pos <= scanline < (y_pos + y_size):
                line = scanline - y_pos
                if y_flip:
                    line -= y_size
                    line *= -1

                line *= 2
                data_address = (0x8000 + (tile_location * 16)) + line
                data1 = self.read(data_address)
                data2 = self.read(data_address + 1)
                for tile_pixel in range(7, -1, -1):
                    colour_bit = tile_pixel
                    if x_flip:
                        colour_bit -= 7
                        colour_bit *= -1
                    colour_num = bit_get_val(data2, colour_bit)
                    colour_num <<= 1
                    colour_num |= bit_get_val(data1, colour_bit)

                    colour_address = (0xFF49 if test_bit(attributes, 4) else 0xFF48)
                    col = self.get_colour(colour_num, colour_address)
                    red = 0
                    green = 0
                    blue = 0

                    if col == 0:
                        continue
                    elif col == 1:
                        red = 0xCC
                        green = 0xCC
                        blue = 0xCC
                    elif col == 2:
                        red = 0x77
                        green = 0x77
                        blue = 0x77

                    x_pix = 0 - tile_pixel
                    x_pix += 7

                    pixel = x_pos + x_pix

                    if scanline < 0 or scanline > 143 or pixel < 0 or pixel > 159:
                        continue

                    self.screen_data[pixel][scanline][0] = red
                    self.screen_data[pixel][scanline][1] = green
                    self.screen_data[pixel][scanline][2] = blue

    def set_lcd_status(self):
        status = self.read(0xFF41)
        if not self.is_lcd_enabled():
            self.scanline_counter = 456
            self.memory[0xFF44] = 0
            status &= 252
            status = bit_set(status, 0)
            self.write(0xFF41, status)
            return
        current_line = self.read(0xFF44)
        current_mode = status & 0b11

        mode = 0
        req_int = False

        # in v-blank so mode 1
        if current_line >= 144:
            mode = 1
            status = bit_set(status, 0)
            status = bit_reset(status, 1)
            req_int = test_bit(status, 4)
        else:
            mode2bounds = 456 - 80
            mode3bounds = mode2bounds - 172

            # mode 2
            if self.scanline_counter >= mode2bounds:
                mode = 2
                status = bit_set(status, 1)
                status = bit_reset(status, 0)
                req_int = test_bit(status, 5)
            # mode 3
            elif self.scanline_counter >= mode3bounds:
                mode = 3
                status = bit_set(status, 1)
                status = bit_set(status, 0)
            # mode 0
            else:
                mode = 0
                status = bit_reset(status, 1)
                status = bit_reset(status, 0)
                req_int = test_bit(status, 3)

        if req_int and (mode is not current_mode):
            self.request_interrupt(1)

        if current_line == self.read(0xFF45):
            status = bit_set(status, 2)
            if test_bit(status, 6):
                self.request_interrupt(1)
        else:
            status = bit_reset(status, 2)
        self.write(0xFF41, status)

    def is_lcd_enabled(self):
        return test_bit(self.read(0xFF40), 7)

    def get_colour(self, colour_num, address):
        palette = self.read(address)
        hi = (colour_num * 2) + 1
        lo = (colour_num * 2)

        colour = bit_get_val(palette, hi) << 1
        colour |= bit_get_val(palette, lo)
        return colour

    #############################################################################
    #                                                                           #
    #                               DMA TRANSFER                                #
    #                                                                           #
    #############################################################################

    def do_dma_transfer(self, data):
        address = data << 8
        for i in range(0xA0):
            self.write(0xFE00 + i, self.read(address + i))

    #############################################################################
    #                                                                           #
    #                               JOYPAD CODE                                 #
    #                                                                           #
    #############################################################################

    def get_joypad_state(self):
        res = self.memory[0xFF00]
        res ^= 0xFF

        if not test_bit(res, 4):
            top_joypad = self.joypad_state >> 4
            top_joypad |= 0xF0
            res &= top_joypad
        elif not test_bit(res, 5):
            bottom_joypad = self.joypad_state & 0xF
            bottom_joypad |= 0xF0
            res &= bottom_joypad
        return res

    def key_pressed(self, key):
        previously_unset = False
        if not test_bit(self.joypad_state, key):
            previously_unset = True

        self.joypad_state = bit_reset(self.joypad_state, key)

        if key > 3:
            button = True
        else:
            button = False

        key_req = self.memory[0xFF00]
        request_interrupt = False

        if button and not test_bit(key_req, 5):
            request_interrupt = True
        elif not button and not test_bit(key_req, 4):
            request_interrupt = True

        if request_interrupt and not previously_unset:
            self.request_interrupt(4)

    def key_released(self, key):
        self.joypad_state = bit_set(self.joypad_state, key)

    #############################################################################
    #                                                                           #
    #                              STACK FUNCTIONS                              #
    #                                                                           #
    #############################################################################

    def push_to_stack(self, address):
        self.write(self.registers.sp, address % 256)
        self.write(self.registers.sp - 1, address // 256)
        self.registers.sp -= 2

    def pop_from_stack(self):
        big = self.read(self.registers.sp + 1)
        small = self.read(self.registers.sp + 2)
        self.registers.sp += 2
        return (big << 8) | small

#############################################################################
#                                                                           #
#                             USEFUL FUNCTIONS                              #
#                                                                           #
#############################################################################


def test_bit(_input, bit):
    return bool(_input & (0b1 << bit))


def bit_get_val(_input, bit):
    return 1 if _input & (0b1 << bit) != 0 else 0


def bit_set(_input, bit):
    return _input | (0b1 << bit)


def bit_reset(_input, bit):
    if test_bit(_input, bit):
        return _input ^ (0b1 << bit)
    else:
        return _input
