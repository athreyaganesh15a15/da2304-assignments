from parser import Parser
from codewriter import CodeWriter
import sys

def translate(vm_file_path):
    output_path = vm_file_path.replace(".vm", ".asm")

    parser = Parser(vm_file_path)
    writer = CodeWriter(output_path)
    writer.set_file_name(vm_file_path)

    parsed_commands = parser.parse_file()
    
    for command_tuple in parsed_commands:
        if command_tuple is None:
            continue
        command = command_tuple[0]
        args = command_tuple[1]
        
        writer.file.write(f"// {command}, {" ".join(filter(None, args))}\n")
        if command in ["add", "sub", "neg", "not", "and", "or", "eq", "gt", "lt"]:
            writer.write_arithmetic(command)
        elif command in ["push", "pop"]:
            writer.write_push_pop(command, args[0], args[1])
        elif command == "label":
            writer.write_label(args[0])
        elif command == "goto":
            writer.write_goto(args[0])
        elif command == "if-goto":
            writer.write_if(args[0])
        elif command == "function":
            writer.write_function(args[0], args[1])
        elif command == "call":
            writer.write_call(args[0], args[1])
        elif command == "return":
            writer.write_return()
        
        
    writer.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <file.vm>")
        sys.exit(1)
    translate(sys.argv[1])