import sys
import os

class CodeWriter:
    def __init__(self, outputfile):
        self.file = open(outputfile, "w")
        self.filename = ""
        self.label_count = 0
        self.current_function_name = "main"
        self.segment_map = {
            "local": "LCL",
            "argument": "ARG",
            "this": "THIS",
            "that": "THAT"
        }

    def set_file_name(self, filename):
        self.filename = os.path.basename(filename).replace(".vm", "")

    def write_arithmetic(self, command):
        if command == "add":
            self._write_lines([
                "@SP", "AM=M-1", "D=M", 
                "A=A-1", "M=D+M"
            ])
        elif command == "sub":
            self._write_lines([
                "@SP", "AM=M-1", "D=M",
                "A=A-1", "M=M-D"
            ])
        elif command == "and":
            self._write_lines([
                "@SP", "AM=M-1", "D=M", 
                "A=A-1", "M=D&M"
            ])
        elif command == "or":
            self._write_lines([
                "@SP", "AM=M-1", "D=M", 
                "A=A-1", "M=M|D"
            ])
        elif command == "neg":
            self._write_lines([
                "@SP", "A=M-1", "M=-M"
            ])
        elif command == "not":
            self._write_lines([
                "@SP", "A=M-1", "M=!M"
            ])
        elif command in ["eq", "gt", "lt"]:
            label_true = f"{command.upper()}_TRUE_{self.label_count}"
            label_end = f"{command.upper()}_END_{self.label_count}"
            self.label_count += 1

            jump_instruction = ""
            if command == "eq":
                jump_instruction = "JEQ"
            elif command == "gt":
                jump_instruction = "JGT"
            elif command == "lt":
                jump_instruction = "JLT"
            
            self._write_lines([
                "@SP", "AM=M-1", "D=M", 
                "A=A-1", "D=M-D", 
                f"@{label_true}", f"D;{jump_instruction}",
                "@SP", "A=M-1", "M=0", 
                f"@{label_end}", "0;JMP", 
                f"({label_true})", "@SP", "A=M-1", "M=-1",
                f"({label_end})"
            ])
    def write_push_pop(self, command, segment, index):
        if command == "push":
            if segment == "constant":
                self._write_lines([
                    f"@{index}", "D=A", "@SP", "A=M", "M=D", 
                    "@SP", "M=M+1"
                ])
            elif segment in ["local", "argument", "this", "that"]:
                symbol = self.segment_map[segment]
                self._write_lines([
                    f"@{index}", "D=A",
                    f"@{symbol}", "A=M", "A=D+A", "D=M", 
                    "@SP", "A=M", "M=D",
                    "@SP", "M=M+1"
                ])
            elif segment == "temp":
                addr = 5 + int(index)
                self._write_lines([
                    f"@{addr}", "D=M",
                    "@SP", "A=M", "M=D",
                    "@SP", "M=M+1"
                ])
            elif segment == "static":
                self._write_lines([
                    f"@{self.filename}.{index}", "D=M",
                    "@SP", "A=M", "M=D",
                    "@SP", "M=M+1"
                ])
            elif segment == "pointer":
                target = "THIS" if index == "0" else "THAT"
                self._write_lines([
                    f"@{target}", "D=M",
                    "@SP", "A=M", "M=D",
                    "@SP", "M=M+1"
                ])
        elif command == "pop":
            if segment in self.segment_map:
                symbol = self.segment_map[segment]
                self._write_lines([
                    f"@{index}", "D=A", 
                    f"@{symbol}", "D=D+M", 
                    "@13", "M=D", 
                    "@SP", "AM=M-1", "D=M", 
                    "@13", "A=M", "M=D"
                ])
            elif segment in ["temp", "static"]:
                if segment == "temp":
                    addr = 5 + int(index)
                else:
                    addr = f"{self.filename}.{index}"
                self._write_lines([
                    "@SP", "AM=M-1", "D=M", 
                    f"@{addr}", "M=D"        
                ])
            elif segment == "pointer":
                target = "THIS" if str(index) == "0" else "THAT"
                self._write_lines([
                    "@SP", "AM=M-1", "D=M",  
                    f"@{target}", "M=D"      
                ])

    def write_label(self, label):
        self._write_lines([
            f"({self.current_function_name}${label})"
        ])

    def write_goto(self, label):
        self._write_lines([
            f"@{self.current_function_name}${label}",
            "0;JMP"
        ])

    def write_if(self, label):
        self._write_lines([
            "@SP",
            "AM=M-1",
            "D=M",
            f"@{self.current_function_name}${label}",
            "D;JNE"
        ])

    def write_call(self, function_name, num_args):
        return_address = f"{function_name}$ret.{self.label_count}"
        self.label_count += 1
        
        self._write_lines([
            f"@{return_address}", "D=A", "@SP", "A=M", "M=D", "@SP", "M=M+1",
            "@LCL", "D=M", "@SP", "A=M", "M=D", "@SP", "M=M+1",
            "@ARG", "D=M", "@SP", "A=M", "M=D", "@SP", "M=M+1",
            "@THIS", "D=M", "@SP", "A=M", "M=D", "@SP", "M=M+1",
            "@THAT", "D=M", "@SP", "A=M", "M=D", "@SP", "M=M+1",
            "@SP", "D=M", f"@{num_args}", "D=D-A", "@5", "D=D-A", "@ARG", "M=D",
            "@SP", "D=M", "@LCL", "M=D",
            f"@{function_name}", "0;JMP",
            f"({return_address})"
        ])

    def write_return(self):
        self._write_lines([
            "@LCL", "D=M", "@R13", "M=D",
            "@5", "A=D-A", "D=M", "@R14", "M=D",
            "@SP", "AM=M-1", "D=M", "@ARG", "A=M", "M=D",
            "@ARG", "D=M+1", "@SP", "M=D",
            "@R13", "D=M", "A=D-1", "D=M", "@THAT", "M=D",
            "@R13", "D=M", "@2", "A=D-A", "D=M", "@THIS", "M=D",
            "@R13", "D=M", "@3", "A=D-A", "D=M", "@ARG", "M=D",
            "@R13", "D=M", "@4", "A=D-A", "D=M", "@LCL", "M=D",
            "@R14", "A=M", "0;JMP"
        ])

    def write_function(self, function_name, num_locals):
        self.current_function_name = function_name
        self._write_lines([
            f"({function_name})"
        ])
        for _ in range(int(num_locals)):
            self._write_lines([
                "@SP", "A=M", "M=0", "@SP", "M=M+1"
            ])

    def close(self):
        self.file.close()
    
    def _write_lines(self, lines):
        for line in lines:
            self.file.write(line + "\n")
    