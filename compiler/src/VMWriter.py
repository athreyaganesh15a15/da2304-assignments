class VMWriter:
    def __init__(self, output_file):
        self.output_file = output_file
        self.output = []

    def writePush(self, segment, index):
        self.output.append(f'push {segment} {index}\n')

    def writePop(self, segment, index):
        self.output.append(f'pop {segment} {index}\n')
    
    def writeArithmetic(self, command):
        self.output.append(f'{command}\n')
        
    def writeLabel(self, label):
        self.output.append(f'label {label}\n')

    def writeGoto(self, label):
        self.output.append(f'goto {label}\n')
    
    def writeIf(self, label):
        self.output.append(f'if-goto {label}\n')

    def writeCall(self, name, nArgs):
        self.output.append(f'call {name} {nArgs}\n')

    def writeFunction(self, name, nLocals):
        self.output.append(f'function {name} {nLocals}\n')

    def writeReturn(self):
        self.output.append('return\n')

    def close(self):
        with open(self.output_file, 'w') as file:
            file.writelines(self.output)

    