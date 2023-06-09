import re
import sys
from enum import Enum, Flag, auto

# matches instruction_name + endl
instruction_regex = re.compile(
    r"add|and|div|mult|jr|mfhi|mflo|sll|sllv|slt|srav|srl|sub|break|rte|xchg|addi|addiu|beq|bne|ble|bgt|sram|lb|lh|lui|lw|sb|sh|slti|sw|j|jal|abc$")

# matches (integers of up to 10 digits (may be negative) or register names) + maybe a comma + endl
# example strings:
# 12345,
# 12345
# -3
# $s0,
# $zero
arg_regex = re.compile(
    r"((-?[0-9]{0,10})|(\$((zero)|(at)|(gp)|(sp)|(fp)|(ra)|(v[0-1])|(a[0-3])|(t[0-9])|(s[0-7])|(k[0-1])))),?$")

# matches integers of up to 5 digits (may be negative) + (register number or name) + endl
# example strings:
# 0(10)
# 300($zero)
# -24($t5)
memarg_regex = re.compile(
    r"-?[0-9]{1,5}\((([0-3][0-9]?)|(\$((zero)|(at)|(gp)|(sp)|(fp)|(ra)|(v[0-1])|(a[0-3])|(t[0-9])|(s[0-7])|(k[0-1]))))\)$")

# matches registers by (number or name) + endl
# example strings:
# 0
# 25
# $at
# $a2
register_regex = re.compile(
    "((([0-2][0-9]?)|3[0-1])|(\$((zero)|(at)|(gp)|(sp)|(fp)|(ra)|(v[0-1])|(a[0-3])|(t[0-9])|(s[0-7])|(k[0-1]))))$")

# matches integers of up to 5 digits (may be negative) + endl
immediate_regex = re.compile("-?[0-9]{1,5}$")

# matches integers of up to 8 digits + endl
offset_regex = re.compile("[0-9]{1,8}$")

reg_names = {"$zero": "0", "$at": "1", "$v0": "2", "$v1": "3", "$a0": "4", "$a1": "5", "$a2": "6", "$a3": "7",
             "$t0": "8", "$t1": "9", "$t2": "10", "$t3": "11", "$t4": "12", "$t5": "13", "$t6": "14", "$t7": "15",
             "$s0": "16", "$s1": "17", "$s2": "18", "$s3": "19", "$s4": "20", "$s5": "21", "$s6": "22", "$s7": "23",
             "$t8": "24", "$t9": "25", "$k0": "26", "$k1": "27", "$gp": "28", "$sp": "29", "$fp": "30", "$ra": "31"}

opcodes = {"abc": "111111", "addi": "001000", "addiu": "001001", "beq": "000100", "bne": "000101", "ble": "000110",
           "bgt": "000111", "sram": "000001", "lb": "100000", "lh": "100001", "lui": "001111", "lw": "100011",
           "sb": "101000", "sh": "101001", "slti": "001010", "sw": "101011", "j": "000010", "jal": "000011"}

functs = {"add": "100000", "and": "100100", "div": "011010", "mult": "011000", "jr": "001000", "mfhi": "010000",
          "mflo": "010010", "sll": "000000", "sllv": "000100", "slt": "101010", "sra": "000011", "srav": "000111",
          "srl": "000010", "sub": "100010", "break": "001101", "rte": "010011", "xchg": "000101", "abc": "111111"}


def tokenizer(instruction):
    token_list = []
    for i in instruction:
        if instruction_regex.match(i):
            token_list.append(Token(TokenTypes.INSTRUCTION, i))
        elif arg_regex.match(i):
            if "," in i:
                aux = i[:-1]
            else:
                aux = i
            token_list.append(Token(TokenTypes.ARG, aux))
        elif memarg_regex.match(i):
            token_list.append(Token(TokenTypes.MEMARG, i))
        else:
            raise ValueError(f"Unexpected token while parsing: \"{i}\"")
    return token_list


def syntax(tokenized_inst):
    if tokenized_inst[0].token_type is not TokenTypes.INSTRUCTION:
        raise ValueError(f"\"{tokenized_inst[0].content}\" is not a recognizable instruction")
    inst = tokenized_inst[0].content
    # R instructions
    if inst in ["add", "and", "sub", "sllv", "slt", "srav", "abc"]:
        try:
            if register_regex.match(tokenized_inst[1].content):
                if register_regex.match(tokenized_inst[2].content):
                    if register_regex.match(tokenized_inst[3].content):
                        if not len(tokenized_inst) > 4:
                            parsed_instruction = Instruction(inst, tokenized_inst[1:])
                        else:
                            raise ValueError("Too many arguments")
                    else:
                        raise ValueError(f"\"{tokenized_inst[3].content}\" is not a register number or id")
                else:
                    raise ValueError(f"\"{tokenized_inst[2].content}\" is not a register number or id")
            else:
                raise ValueError(f"\"{tokenized_inst[1].content}\" is not a register number or id")
        except IndexError:
            raise ValueError("Too few arguments")
    elif inst in ["div", "mult", "xchg"]:
        try:
            if register_regex.match(tokenized_inst[1].content):
                if register_regex.match(tokenized_inst[2].content):
                    if not len(tokenized_inst) > 3:
                        parsed_instruction = Instruction(inst, tokenized_inst[1:])
                    else:
                        raise ValueError("Too many arguments")
                else:
                    raise ValueError(f"\"{tokenized_inst[2].content}\" is not a register number or id")
            else:
                raise ValueError(f"\"{tokenized_inst[1].content}\" is not a register number or id")
        except IndexError:
            raise ValueError("Too few arguments")
    elif inst in ["jr", "mfhi", "mflo"]:
        try:
            if register_regex.match(tokenized_inst[1].content):
                if not len(tokenized_inst) > 2:
                    parsed_instruction = Instruction(inst, tokenized_inst[1:])
                else:
                    raise ValueError("Too many arguments")
            else:
                raise ValueError(f"\"{tokenized_inst[1].content}\" is not a register number or id")
        except IndexError:
            raise ValueError("Too few arguments")
    elif inst in ["sll", "sra", "srl"]:
        try:
            if register_regex.match(tokenized_inst[1].content):
                if register_regex.match(tokenized_inst[2].content):
                    if immediate_regex.match(
                            tokenized_inst[3].content) and 0 <= int(tokenized_inst[3].content) < 32:
                        if not len(tokenized_inst) > 4:
                            parsed_instruction = Instruction(inst, tokenized_inst[1:])
                        else:
                            raise ValueError("Too many arguments")
                    else:
                        raise ValueError(
                            f"\"{tokenized_inst[3].content}\" is not an shamt value or does not fit in 5 bits")
                else:
                    raise ValueError(f"\"{tokenized_inst[2].content}\" is not a register number or id")
            else:
                raise ValueError(f"\"{tokenized_inst[1].content}\" is not a register number or id")
        except IndexError:
            raise ValueError("Too few arguments")
    elif inst in ["break", "rte"]:
        if not len(tokenized_inst) > 1:
            parsed_instruction = Instruction(inst, ["nope"])
        else:
            raise ValueError("Too many arguments")
    # I instructions
    elif inst in ["addi", "addiu", "slti", "beq", "bne", "ble", "bgt"]:
        try:
            if register_regex.match(tokenized_inst[1].content):
                if register_regex.match(tokenized_inst[2].content):
                    if immediate_regex.match(
                            tokenized_inst[3].content) and -32769 < int(tokenized_inst[3].content) < 32768:
                        if not len(tokenized_inst) > 4:
                            parsed_instruction = Instruction(inst, tokenized_inst[1:])
                        else:
                            raise ValueError("Too many arguments")
                    else:
                        raise ValueError(
                            f"\"{tokenized_inst[3].content}\" is not an immediate value or does not fit in 16 bits (signed)")
                else:
                    raise ValueError(f"\"{tokenized_inst[2].content}\" is not a register number or id")
            else:
                raise ValueError(f"\"{tokenized_inst[1].content}\" is not a register number or id")
        except IndexError:
            raise ValueError("Too few arguments")
    elif inst in ["sram", "lb", "lh", "lw", "sb", "sh", "sw"]:
        try:
            if register_regex.match(tokenized_inst[1].content):
                if tokenized_inst[2].token_type is TokenTypes.MEMARG:
                    if not len(tokenized_inst) > 3:  # TODO CHECK FOR OFFSET SIZE AND FIX SIGN STUFF
                        parsed_instruction = Instruction(inst, tokenized_inst[1:])
                    else:
                        raise ValueError("Too many arguments")
                else:
                    raise ValueError(f"\"{tokenized_inst[2].content}\" is not a memory address")
            else:
                raise ValueError(f"\"{tokenized_inst[1].content}\" is not a register number or id")
        except IndexError:
            raise ValueError("Too few arguments")
    elif inst == "lui":
        try:
            if register_regex.match(tokenized_inst[1].content):
                if immediate_regex.match(tokenized_inst[2].content) and 0 <= int(tokenized_inst[2].content) < 65536:
                    if not len(tokenized_inst) > 3:
                        parsed_instruction = Instruction(inst, tokenized_inst[1:])
                    else:
                        raise ValueError("Too many arguments")
                else:
                    raise ValueError(
                        f"\"{tokenized_inst[2].content}\" is not an immediate value or does not fit in 16 bits")
            else:
                raise ValueError(f"\"{tokenized_inst[1].content}\" is not a register number or id")
        except IndexError:
            raise ValueError("Too few arguments")
    # J instructions
    elif inst in ["j", "jal"]:
        try:
            if offset_regex.match(tokenized_inst[1].content) and 0 <= int(tokenized_inst[1].content) < 67108864:
                if not len(tokenized_inst) > 2:
                    parsed_instruction = Instruction(inst, tokenized_inst[1:])
                else:
                    raise ValueError("Too many arguments")
            else:
                raise ValueError(f"\"{tokenized_inst[1].content}\" is not an offset value or does not fit in 26 bits")
        except IndexError:
            raise ValueError("Too few arguments")
    else:
        raise ValueError("This error should never happen. https://xkcd.com/2200/")
    return parsed_instruction


def assemble(instruction):
    temp_bin = ""
    # R instructions
    if instruction.action in ["add", "and", "sub", "sllv", "slt", "srav", "abc"]:
        if instruction.action not in opcodes.keys():
            temp_bin += "000000"
        else:
            temp_bin += opcodes[instruction.action]
        temp_bin += get_register_binary(instruction.payload[1])
        temp_bin += get_register_binary(instruction.payload[2])
        temp_bin += get_register_binary(instruction.payload[0])
        temp_bin += "00000"
        temp_bin += functs[instruction.action]
    elif instruction.action in ["div", "mult", "xchg"]:
        temp_bin += "000000"
        temp_bin += get_register_binary(instruction.payload[0])
        temp_bin += get_register_binary(instruction.payload[1])
        temp_bin += "00000"
        temp_bin += "00000"
        temp_bin += functs[instruction.action]
    elif instruction.action == "jr":
        temp_bin += "000000"
        temp_bin += get_register_binary(instruction.payload[0])
        temp_bin += "00000"
        temp_bin += "00000"
        temp_bin += "00000"
        temp_bin += functs[instruction.action]
    elif instruction.action in ["mfhi", "mflo"]:
        temp_bin += "000000"
        temp_bin += "00000"
        temp_bin += "00000"
        temp_bin += get_register_binary(instruction.payload[0])
        temp_bin += "00000"
        temp_bin += functs[instruction.action]
    elif instruction.action in ["sll", "sra", "srl"]:
        temp_bin += "000000"
        temp_bin += "00000"
        temp_bin += get_register_binary(instruction.payload[1])
        temp_bin += get_register_binary(instruction.payload[0])
        temp_bin += '{:0>5b}'.format(int(instruction.payload[2].content))
        temp_bin += functs[instruction.action]
    elif instruction.action in ["break", "rte"]:
        temp_bin += "000000"
        temp_bin += "00000"
        temp_bin += "00000"
        temp_bin += "00000"
        temp_bin += "00000"
        temp_bin += functs[instruction.action]
    # I instructions
    elif instruction.action in ["addi", "addiu", "slti"]:  # TODO IS SLTI SIGNED?
        temp_bin += opcodes[instruction.action]
        temp_bin += get_register_binary(instruction.payload[1])
        temp_bin += get_register_binary(instruction.payload[0])
        temp_bin += get_immediate_binary(instruction.payload[2])
    elif instruction.action in ["beq", "bne", "ble", "bgt"]:
        temp_bin += opcodes[instruction.action]
        temp_bin += get_register_binary(instruction.payload[0])
        temp_bin += get_register_binary(instruction.payload[1])
        temp_bin += '{:0>16b}'.format(int(instruction.payload[2].content))
    elif instruction.action in ["sram", "lb", "lh", "lw", "sb", "sh", "sw"]:  # TODO THIS
        temp_bin += opcodes[instruction.action]
        temp_bin += get_rs_from_memarg(instruction.payload[1])
        temp_bin += get_register_binary(instruction.payload[0])
        # temp_bin += get_offset_from_memarg()
    elif instruction.action == "lui":
        temp_bin += opcodes["lui"]
        temp_bin += "00000"
        temp_bin += get_register_binary(instruction.payload[0])
        temp_bin += '{:0>16b}'.format(int(instruction.payload[1].content))
    # J instructions
    elif instruction.action in ["j", "jal"]:
        temp_bin += opcodes[instruction.action]
        temp_bin += '{:0>26b}'.format(int(instruction.payload[0].content))
    else:
        raise ValueError("This error should never happen. https://xkcd.com/2200/")
    endian_result = [temp_bin[24:32], temp_bin[16:24], temp_bin[8:16], temp_bin[0:8]]
    return endian_result


def get_register_binary(register):
    if register.content.isnumeric():
        aux = '{:0>5b}'.format(int(register.content))
    else:
        aux = '{:0>5b}'.format(int(reg_names[register.content]))
    return aux


def get_immediate_binary(immediate):  # TODO TWO's COMPLEMENT
    # if int(int(immediate.content)) >= 0:
    #     aux = '{:0>16b}'.format(int(immediate.content))
    # else:
    #     aux = immediate.content[1:]
    #     aux = '{:0>16b}'.format(aux)
    #     temp = ""
    #     for i in aux:
    #         if i == "1":
    #             temp += "0"
    #         else:
    #             temp
    return "AAAAAAAAAAAAAAAA"


def get_rs_from_memarg(memarg):
    aux = memarg.content.split("(")
    rs = aux[1][:-1]
    if rs.isnumeric():
        result = '{:0>5b}'.format(int(rs))
    else:
        result = '{:0>5b}'.format(int(reg_names[rs]))
    return result


class Token:
    def __init__(self, token_type, content):
        self.token_type = token_type
        self.content = content


class TokenTypes(Enum):
    INSTRUCTION = auto()
    ARG = auto()
    MEMARG = auto()


class ArgFlags(Flag):
    HELP = auto()
    FILE = auto()
    STDOUT = auto()


def display_help():
    print("Help text")
    exit()


def output(binary, flags):
    if flags & ArgFlags.STDOUT:
        print(binary)
    elif flags & ArgFlags.FILE:
        pass
    else:
        pass


class Instruction:
    def __init__(self, action, payload):
        self.action = action
        self.payload = payload


if __name__ == '__main__':
    argumentList = sys.argv[1:]
    flags = ArgFlags(0)
    try:
        if "-h" in argumentList or "--help" in argumentList:
            flags = flags | flags.HELP
            display_help()
        if "-f" in argumentList or "--file" in argumentList:
            flags = flags | flags.FILE
        if "-o" in argumentList or "--output" in argumentList:
            flags = flags | flags.STDOUT
        file = argumentList[0]
        if file[-4:] != ".txt":  # change extension
            display_help()
    except IndexError:
        display_help()

    try:
        file = open(file, "r")  # refactor to use with
    except FileNotFoundError:
        print("No such file exists")
    except IsADirectoryError:
        print(f"{file} is a directory")

    lines = file.readlines()
    index = 0
    words = []
    for line in lines:
        if "#" in line:
            line = line.split("#")
            line = line[0]
        line = line.strip().split(" ")
        if line[0] != "":
            try:
                tokens = tokenizer(line)
                parsed = syntax(tokens)
                binary = assemble(parsed)
                words.append(binary)
            except ValueError as e:
                print(str(e) + f" at line {index}")
                exit()
        index += 1
    output(words, flags)
