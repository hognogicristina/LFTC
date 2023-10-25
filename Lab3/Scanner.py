from SymbolTable import SymbolTable

import os
import re


class Scanner:
    def __init__(self):
        self.program = ""
        self.tokens = []
        self.reserved_words = []
        self.symbol_table = SymbolTable(500)
        self.PIF = []
        self.index = 0
        self.current_line = 1

    def read_tokens(self):
        token_file_path = os.path.join(os.path.dirname(__file__), 'L1', 'token.in')
        try:
            with open(token_file_path, "r") as file:
                lines = file.read().splitlines()
                for line in lines:
                    token = line.split()[0]
                    if token in ["prog", "int", "real", "str", "char", "bool", "read", "if", "else", "write", "do",
                                 "while", "arr", "const", "fun", "sys", "for", "foreach", "and", "or", "not", "rad"]:
                        self.reserved_words.append(token)
                    else:
                        self.tokens.append(token)
        except FileNotFoundError:
            print("Error: 'token.in' file not found in the 'L1' directory")

    def set_program(self, program):
        self.program = program

    def skip_spaces(self):
        while self.index < len(self.program) and self.program[self.index].isspace():
            if self.program[self.index] == '\n':
                self.current_line += 1
            self.index += 1

    def skip_comments(self):
        self.skip_spaces()

        while self.index < len(self.program) - 1 and self.program[self.index:self.index + 2] == '//':
            while self.index < len(self.program) and self.program[self.index] != '\n':
                self.index += 1
            self.skip_spaces()

    def treat_string_constant(self):
        regex_for_string_constant = re.compile(r'^"[a-zA-z0-9_ ?:*^+=.!]*"')
        match = regex_for_string_constant.match(self.program[self.index:])
        if not match:
            if re.compile(r'^"[^"]"').match(self.program[self.index:]):
                raise Exception(f"Invalid string constant at line {self.current_line}")
            if re.compile(r'^"[^"]').match(self.program[self.index:]):
                raise Exception(f"Missing \" at line {self.current_line}")
            return False
        string_constant = match.group(0)
        if not self.symbol_table.has_hash(string_constant):
            position, hash_value = self.symbol_table.add_hash(string_constant)
        else:
            position, hash_value = self.symbol_table.get_position_hash(string_constant)
        self.index += len(string_constant)
        self.PIF.append([position, hash_value])
        return True

    def treat_int_constant(self):
        regex_for_int_constant = re.compile(r'^([+-]?[1-9][0-9]*|0)')
        match = regex_for_int_constant.match(self.program[self.index:])
        if not match:
            return False
        if re.compile(r'^([+-]?[1-9][0-9]*|0)[a-zA-z_]').match(self.program[self.index:]):
            return False
        int_constant = match.group(0)
        if not self.symbol_table.has_hash(int_constant):
            position, hash_value = self.symbol_table.add_hash(int_constant)
        else:
            position, hash_value = self.symbol_table.get_position_hash(int_constant)
        self.index += len(int_constant)
        self.PIF.append([position, hash_value])
        return True

    def check_if_valid(self, possible_identifier, program_substring):
        if possible_identifier in self.reserved_words:
            return False
        if re.compile(r'^[A-Za-z_][A-Za-z0-9_]*: (int|char|str|real)').search(program_substring):
            return True
        return self.symbol_table.has_hash(possible_identifier)

    def treat_identifier(self):
        regex_for_identifier = re.compile(r'^([a-zA-Z_][a-zA-Z0-9_]*)')  # Updated regex
        match = regex_for_identifier.match(self.program[self.index:])
        if not match:
            return False
        identifier = match.group(1)
        if not self.check_if_valid(identifier, self.program[self.index:]):
            return False
        if not self.symbol_table.has_hash(identifier):
            position, hash_value = self.symbol_table.add_hash(identifier)
        else:
            position, hash_value = self.symbol_table.get_position_hash(identifier)
        self.index += len(identifier)
        self.PIF.append([position, hash_value])
        return True

    def treat_from_token_list(self):
        possible_token = self.program[self.index:].split(" ")[0]
        for reserved_token in self.reserved_words:
            if possible_token.startswith(reserved_token):
                regex = f"^[a-zA-Z0-9_]*{reserved_token}[a-zA-Z0-9_]+"
                if re.compile(regex).search(possible_token):
                    return False
                self.index += len(reserved_token)
                self.PIF.append([reserved_token, -1])
                return True
        for token in self.tokens:
            if token == possible_token:
                self.index += len(token)
                self.PIF.append([token, -1])
                return True
            elif possible_token.startswith(token):
                self.index += len(token)
                self.PIF.append([token, -1])
                return True
        return False

    def next_token(self):
        self.skip_spaces()
        self.skip_comments()
        if self.index == len(self.program):
            return
        if self.treat_identifier():
            return
        if self.treat_string_constant():
            return
        if self.treat_int_constant():
            return
        if self.treat_from_token_list():
            return
        raise Exception(f"Lexical error: invalid token at line {self.current_line}, index {self.index}")

    def scan(self, program_file_name):
        try:
            with open(os.path.join("L1", program_file_name), "r") as file:
                self.set_program(file.read())
                while self.index < len(self.program):
                    self.next_token()

            with open(f"PIF{program_file_name.replace('.txt', '.out')}", "w") as pif_file:
                for token, position in self.PIF:
                    pif_file.write(f"{token}, {position}\n")

            with open(f"ST{program_file_name.replace('.txt', '.out')}", "w") as st_file:
                st_file.write(str(self.symbol_table))

            print("Lexically correct")
        except (IOError, Exception) as e:
            print(e)
