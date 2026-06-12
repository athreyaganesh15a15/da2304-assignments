import re

class Parser:
    regex_comment = r"//.*"
    regex_whitespace = r"\s+"

    def __init__(self, vm_file):
        self.filelocation = vm_file
        self.file = []

    def parse_current_line(self, line):
        line = re.sub(Parser.regex_comment, "", line).strip()
        line = re.sub(Parser.regex_whitespace, " ", line)
        tokens = line.split()

        if not tokens:
            return None

        while len(tokens) < 3:
            tokens.append(None)
        if len(tokens) > 3:
            print(f"ERROR LINE: '{line}' tokens: {tokens}")
            raise Exception("Too many tokens")
        
        return tokens[0], tokens[1:]

    def parse_file(self):
        with open(self.filelocation, "r") as f:
            self.file = f.read().splitlines()
        parsed_file = []
        for line in self.file:
            parsed_line = self.parse_current_line(line)
            if parsed_line:
                parsed_file.append(tuple(parsed_line))
        self.file = parsed_file
        return self.file

