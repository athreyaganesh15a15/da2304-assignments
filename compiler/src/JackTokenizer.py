import os


class JackTokenizer:

    keywords = ['class', 'constructor', 'method', 'function', 'var', 'static', 'field', 'let', 'do', 'return', 'if', 'else', 'while', 'int', 'boolean', 'char', 'true', 'false', 'null', 'this', 'void']
    symbols = ['{', '}', '(', ')', '[', ']', '.', ',', ';', '+', '-', '*', '/', '&', '|', '<', '>', '=', '~']
    xml_escapes = {'<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;'}

    def __init__(self, input_file):
        self.input_file = input_file
        with open(input_file, 'r', encoding='utf-8') as f:
            self.input = f.read()
        self.tokens = []
        self.current_token_index = 0
        self.output_file = os.path.splitext(input_file)[0] + 'T.xml'

    def hasMoreTokens(self):
        return self.current_token_index < len(self.tokens)

    def advance(self):
        if self.hasMoreTokens():
            self.current_token_index += 1

    def tokenType(self):
        if self.current_token_index < len(self.tokens):
            token = self.tokens[self.current_token_index]
            if token in self.keywords:
                return 'KEYWORD'
            elif token in self.symbols:
                return 'SYMBOL'
            elif token.isdigit():
                return 'INT_CONST'
            elif token.startswith('"') and token.endswith('"'):
                return 'STRING_CONST'
            else:
                return 'IDENTIFIER'

    def keyWord(self):
        if self.tokenType() == 'KEYWORD':
            return self.tokens[self.current_token_index]

    def symbol(self):
        if self.tokenType() == 'SYMBOL':
            symbol = self.tokens[self.current_token_index]
            return self.xml_escapes.get(symbol, symbol)

    def identifier(self):
        if self.tokenType() == 'IDENTIFIER':
            return self.tokens[self.current_token_index]

    def intVal(self):
        if self.tokenType() == 'INT_CONST':
            return int(self.tokens[self.current_token_index])

    def stringVal(self):
        if self.tokenType() == 'STRING_CONST':
            return self.tokens[self.current_token_index][1:-1]

    def tokenize(self):
        self.tokens = []
        self.current_token_index = 0
        s = self.input
        i = 0
        cur = ''
        state = 'DEFAULT'
        while i < len(s):
            ch = s[i]
            if state == 'DEFAULT':
                if ch == '/' and i + 1 < len(s) and s[i+1] == '/':
                    state = 'SL_COMMENT'
                    i += 2
                    continue
                if ch == '/' and i + 1 < len(s) and s[i+1] == '*':
                    state = 'ML_COMMENT'
                    i += 2
                    continue
                if ch == '"':
                    if cur:
                        self.tokens.append(cur)
                        cur = ''
                    state = 'STRING'
                    cur = '"'
                    i += 1
                    continue
                if ch in self.symbols:
                    if cur:
                        self.tokens.append(cur)
                        cur = ''
                    self.tokens.append(ch)
                    i += 1
                    continue
                if ch.isspace():
                    if cur:
                        self.tokens.append(cur)
                        cur = ''
                    i += 1
                    continue
                cur += ch
                i += 1
            elif state == 'STRING':
                cur += ch
                i += 1
                if ch == '"':
                    self.tokens.append(cur)
                    cur = ''
                    state = 'DEFAULT'
            elif state == 'SL_COMMENT':
                if ch == '\n':
                    state = 'DEFAULT'
                i += 1
            elif state == 'ML_COMMENT':
                if ch == '*' and i + 1 < len(s) and s[i+1] == '/':
                    i += 2
                    state = 'DEFAULT'
                else:
                    i += 1

        if cur:
            self.tokens.append(cur)

    def write_tokens(self, output_file=None):
        out = output_file or self.output_file
        with open(out, 'w', encoding='utf-8') as f:
            f.write('<tokens>\n')
            for token in self.tokens:
                if token in self.keywords:
                    f.write(f'<keyword> {token} </keyword>\n')
                elif token in self.symbols:
                    esc = self.xml_escapes.get(token, token)
                    f.write(f'<symbol> {esc} </symbol>\n')
                elif token.isdigit():
                    val = int(token)
                    if not (0 <= val <= 32767):
                        raise ValueError(f"Integer constant out of range: {val}")
                    f.write(f'<integerConstant> {token} </integerConstant>\n')
                elif token.startswith('"') and token.endswith('"'):
                    f.write(f'<stringConstant> {token[1:-1]} </stringConstant>\n')
                else:
                    f.write(f'<identifier> {token} </identifier>\n')
            f.write('</tokens>\n')