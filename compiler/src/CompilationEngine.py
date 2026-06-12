from JackTokenizer import JackTokenizer
from SymbolTable import SymbolTable
from VMWriter import VMWriter

class CompilationEngine:
    binaryOp = {'+': 'add', '-': 'sub', '*': 'call Math.multiply 2', '/': 'call Math.divide 2',
                '&': 'and', '|': 'or', '<': 'lt', '>': 'gt', '=': 'eq'}
    unaryOp = {'-': 'neg', '~': 'not'}
    
    def __init__(self, input_file, xml_output_file, vm_output_file):
        self.tokenizer = JackTokenizer(input_file)
        self.tokenizer.tokenize()
        self.tokenizer.write_tokens()
        
        self.xml_output_file = xml_output_file
        self.parsed_tokens = []
        self.indent_level = 0
        
        # --- STAGE 2 ADDITIONS ---
        self.symbol_table = SymbolTable()
        self.vm_writer = VMWriter(vm_output_file)
        
        self.class_name = ""
        self.label_counter = 0
        self.token_idx = 0
        # -------------------------

    # --- HELPER METHODS ---
    def current_token(self):
        if self.token_idx < len(self.tokenizer.tokens):
            return self.tokenizer.tokens[self.token_idx]
        return None

    def advance(self):
        token = self.current_token()

        if token is not None:
            self.write_token(token)
            self.token_idx += 1

        return token

    def peek(self):
        if self.token_idx + 1 < len(self.tokenizer.tokens):
            return self.tokenizer.tokens[self.token_idx + 1]
        return None

    def get_segment(self, kind):
        mapping = {'static': 'static', 'field': 'this', 'arg': 'argument', 'var': 'local'}
        return mapping.get(kind, 'none')

    def new_label(self):
        self.label_counter += 1
        return f"L{self.label_counter}"
    
    def write_open(self, tag):
        self.parsed_tokens.append(f'{"  " * self.indent_level}<{tag}>\n')
        self.indent_level += 1

    def write_close(self, tag):
        self.indent_level -= 1
        self.parsed_tokens.append(f'{"  " * self.indent_level}</{tag}>\n')

    def write_token(self, token):
        safe = self.tokenizer.xml_escapes.get(token, token)

        if token in self.tokenizer.keywords:
            tag = "keyword"
        elif token in self.tokenizer.symbols:
            tag = "symbol"
        elif token.isdigit():
            tag = "integerConstant"
        elif token.startswith('"'):
            tag = "stringConstant"
            safe = token[1:-1]
        else:
            tag = "identifier"

        self.parsed_tokens.append(
            f'{"  " * self.indent_level}<{tag}> {safe} </{tag}>\n'
        )

    # --- COMPILATION METHODS ---
    
    def compileClass(self):
        self.write_open("class")

        self.advance() # class
        self.class_name = self.advance()
        self.advance() # {

        while self.current_token() in ['static', 'field']:
            self.compileClassVarDec()

        while self.current_token() in ['constructor', 'function', 'method']:
            self.compileSubroutine()

        self.advance() # }

        self.write_close("class")

        self.vm_writer.close()

    def compileClassVarDec(self):
        self.write_open("classVarDec")
        kind = self.advance() # 'static' or 'field'
        var_type = self.advance() # type
        name = self.advance() # varName
        self.symbol_table.define(name, var_type, kind)
        
        while self.current_token() == ',':
            self.advance() # ','
            name = self.advance()
            self.symbol_table.define(name, var_type, kind)
        self.advance() # ';'
        self.write_close("classVarDec")

    def compileSubroutine(self):
        self.write_open("subroutineDec")
        self.symbol_table.reset()
        subroutine_kind = self.advance() # constructor, function, method
        
        if subroutine_kind == 'method':
            self.symbol_table.define('this', self.class_name, 'arg')
            
        return_type = self.advance() # type or 'void'
        subroutine_name = self.advance() # name
        
        self.advance() # '('
        self.compileParameterList()
        self.advance() # ')'
        self.write_open("subroutineBody")
        self.advance() # '{'
        while self.current_token() == 'var':
            self.compileVarDec()
            
        # Write function declaration
        num_locals = self.symbol_table.var_count('var')
        self.vm_writer.writeFunction(f"{self.class_name}.{subroutine_name}", num_locals)
        
        # Object allocation / This pointer setup
        if subroutine_kind == 'constructor':
            num_fields = self.symbol_table.var_count('field')
            self.vm_writer.writePush('constant', num_fields)
            self.vm_writer.writeCall('Memory.alloc', 1)
            self.vm_writer.writePop('pointer', 0)
        elif subroutine_kind == 'method':
            self.vm_writer.writePush('argument', 0)
            self.vm_writer.writePop('pointer', 0)

        self.compileStatements()
        self.advance() # '}'
        self.write_close("subroutineBody")
        self.write_close("subroutineDec")

    def compileParameterList(self):
        self.write_open("parameterList")
        if self.current_token() != ')':
            var_type = self.advance()
            name = self.advance()
            self.symbol_table.define(name, var_type, 'arg')
            while self.current_token() == ',':
                self.advance() # ','
                var_type = self.advance()
                name = self.advance()
                self.symbol_table.define(name, var_type, 'arg')
        self.write_close("parameterList")

    def compileVarDec(self):
        self.write_open("varDec")
        self.advance() # 'var'
        var_type = self.advance()
        name = self.advance()
        self.symbol_table.define(name, var_type, 'var')
        while self.current_token() == ',':
            self.advance() # ','
            name = self.advance()
            self.symbol_table.define(name, var_type, 'var')
        self.advance() # ';'
        self.write_close("varDec")

    def compileStatements(self):
        self.write_open("statements")
        while self.current_token() in ['let', 'if', 'while', 'do', 'return']:
            token = self.current_token()
            if token == 'let': self.compileLet()
            elif token == 'if': self.compileIf()
            elif token == 'while': self.compileWhile()
            elif token == 'do': self.compileDo()
            elif token == 'return': self.compileReturn()
        self.write_close("statements")

    def compileLet(self):
        self.write_open("letStatement")
        self.advance() # 'let'
        var_name = self.advance()
        is_array = False
        
        if self.current_token() == '[':
            is_array = True
            self.advance() # '['
            self.compileExpression() # index expression
            self.advance() # ']'
            
            # Push array base address and add index
            kind = self.symbol_table.kind_of(var_name)
            idx = self.symbol_table.index_of(var_name) # Ensure you have index_of in SymbolTable!
            self.vm_writer.writePush(self.get_segment(kind), idx)
            self.vm_writer.writeArithmetic('add')

        self.advance() # '='
        self.compileExpression()
        self.advance() # ';'

        if is_array:
            self.vm_writer.writePop('temp', 0)
            self.vm_writer.writePop('pointer', 1)
            self.vm_writer.writePush('temp', 0)
            self.vm_writer.writePop('that', 0)
        else:
            kind = self.symbol_table.kind_of(var_name)
            idx = self.symbol_table.index_of(var_name)
            self.vm_writer.writePop(self.get_segment(kind), idx)
        self.write_close("letStatement")

    def compileDo(self):
        self.write_open("doStatement")
        self.advance() # 'do'
        self.compileTerm() # Handles subroutine call internally in term logic
        self.advance() # ';'
        self.vm_writer.writePop('temp', 0) # Discard return value of 'do'
        self.write_close("doStatement")

    def compileIf(self):
        self.write_open("ifStatement")
        label_false = self.new_label()
        label_end = self.new_label()
        
        self.advance() # 'if'
        self.advance() # '('
        self.compileExpression()
        self.advance() # ')'
        
        self.vm_writer.writeArithmetic('not')
        self.vm_writer.writeIf(label_false)
        
        self.advance() # '{'
        self.compileStatements()
        self.advance() # '}'
        
        self.vm_writer.writeGoto(label_end)
        self.vm_writer.writeLabel(label_false)
        
        if self.current_token() == 'else':
            self.advance() # 'else'
            self.advance() # '{'
            self.compileStatements()
            self.advance() # '}'
            
        self.vm_writer.writeLabel(label_end)
        self.write_close("ifStatement")

    def compileWhile(self):
        self.write_open("whileStatement")
        label_exp = self.new_label()
        label_end = self.new_label()
        
        self.vm_writer.writeLabel(label_exp)
        self.advance() # 'while'
        self.advance() # '('
        self.compileExpression()
        self.advance() # ')'
        
        self.vm_writer.writeArithmetic('not')
        self.vm_writer.writeIf(label_end)
        
        self.advance() # '{'
        self.compileStatements()
        self.advance() # '}'
        
        self.vm_writer.writeGoto(label_exp)
        self.vm_writer.writeLabel(label_end)
        self.write_close("whileStatement")

    def compileReturn(self):
        self.write_open("returnStatement")
        self.advance() # 'return'
        if self.current_token() != ';':
            self.compileExpression()
        else:
            self.vm_writer.writePush('constant', 0)
        self.advance() # ';'
        self.vm_writer.writeReturn()
        self.write_close("returnStatement")

    def compileExpression(self):
        self.write_open("expression")
        self.compileTerm()
        while self.current_token() in self.binaryOp:
            op = self.advance()
            self.compileTerm()
            self.vm_writer.writeArithmetic(self.binaryOp[op])
        self.write_close("expression")

    def compileTerm(self):
        self.write_open("term")
        token = self.current_token()
        
        if token.isdigit():
            self.vm_writer.writePush('constant', int(self.advance()))
        elif token.startswith('"'):
            string = self.advance()[1:-1]

            self.vm_writer.writePush('constant', len(string))
            self.vm_writer.writeCall('String.new', 1)

            for ch in string:
                self.vm_writer.writePush('constant', ord(ch))
                self.vm_writer.writeCall('String.appendChar', 2)

        elif token in ['true', 'false', 'null', 'this']:
            kw = self.advance()
            if kw == 'this': self.vm_writer.writePush('pointer', 0)
            else: self.vm_writer.writePush('constant', 0)
            if kw == 'true': self.vm_writer.writeArithmetic('not')

        elif token in self.unaryOp:
            op = self.advance()
            self.compileTerm()
            self.vm_writer.writeArithmetic(self.unaryOp[op])

        elif token == '(':
            self.advance() # '('
            self.compileExpression()
            self.advance() # ')'
            
        else:
            # Could be a variable, array access, or subroutine call
            name = self.advance()
            
            if self.current_token() == '[':
                self.advance() # '['
                self.compileExpression()
                self.advance() # ']'
                kind = self.symbol_table.kind_of(name)
                idx = self.symbol_table.index_of(name)
                self.vm_writer.writePush(self.get_segment(kind), idx)
                self.vm_writer.writeArithmetic('add')
                self.vm_writer.writePop('pointer', 1)
                self.vm_writer.writePush('that', 0)
                
            elif self.current_token() in ['(', '.']:
                # Subroutine call
                num_args = 0
                if self.current_token() == '.':
                    self.advance() # '.'
                    sub_name = self.advance()
                    kind = self.symbol_table.kind_of(name)
                    if kind: # Method on a variable
                        idx = self.symbol_table.index_of(name)
                        self.vm_writer.writePush(self.get_segment(kind), idx)
                        func_name = f"{self.symbol_table.type_of(name)}.{sub_name}"
                        num_args += 1
                    else: # Function/Constructor of a Class
                        func_name = f"{name}.{sub_name}"
                else: # Method of current class
                    self.vm_writer.writePush('pointer', 0)
                    func_name = f"{self.class_name}.{name}"
                    num_args += 1
                    
                self.advance() # '('
                num_args += self.compileExpressionList()
                self.advance() # ')'
                self.vm_writer.writeCall(func_name, num_args)
            else:
                # Standard variable
                kind = self.symbol_table.kind_of(name)
                idx = self.symbol_table.index_of(name)
                self.vm_writer.writePush(self.get_segment(kind), idx)
        self.write_close("term")

    def compileExpressionList(self):
        self.write_open("expressionList")
        num_args = 0
        if self.current_token() != ')':
            self.compileExpression()
            num_args += 1
            while self.current_token() == ',':
                self.advance() # ','
                self.compileExpression()
                num_args += 1
        self.write_close("expressionList")
        return num_args

    def writeOutput(self):
        with open(self.xml_output_file, 'w') as f:
            f.writelines(self.parsed_tokens)