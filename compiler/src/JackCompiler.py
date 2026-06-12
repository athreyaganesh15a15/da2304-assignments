import sys
import os
from CompilationEngine import CompilationEngine

class JackCompiler:
    def __init__(self, input_file):
        self.input_file = input_file
        self.xml_output = input_file.replace('.jack', '.xml')
        self.vm_output = input_file.replace('.jack', '.vm')
        
        self.engine = CompilationEngine(self.input_file, self.xml_output, self.vm_output)
    
    def compile(self):
        self.engine.compileClass()
        self.engine.writeOutput()
        print(f"Compiled {self.input_file} -> {self.vm_output}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python JackCompiler.py <input_file_or_directory>")
        sys.exit(1)
        
    path = sys.argv[1]
    files_to_compile = []
    
    if os.path.isdir(path):
        for file in os.listdir(path):
            if file.endswith('.jack'):
                files_to_compile.append(os.path.join(path, file))
    else:
        files_to_compile.append(path)
        
    for f in files_to_compile:
        compiler = JackCompiler(f)
        compiler.compile()