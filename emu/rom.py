def get_instructions(file_path) -> list:
    with open(file_path, "rb") as file:
        
        instruction_list = []
        byte = file.read(1)
        
        while byte:
            instruction = hex(ord(byte))
            instruction_list.append(instruction)
            byte = file.read(1)

        return instruction_list