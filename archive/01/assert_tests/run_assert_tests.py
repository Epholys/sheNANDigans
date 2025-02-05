import os
import re
import subprocess
import tempfile
import pathlib

def find_c_files():
    """Scan the current directory for all files with a .c extension."""
    return [f for f in os.listdir() if f.endswith('.c')]

def extract_names_from_file(file_path):
    """Extract the value between '<<<' and '>>>' in the file."""
    with open(file_path, 'r') as file:
        content = file.read()
        matches = re.findall(r'<<<(.*?)>>>', content)
        if len(matches) > 0:
            return matches
    return None

def create_temp_file_with_main(original_file, name):
    """Create a temporary file with the content of the original file and the main function appended."""
    with open(original_file, 'r') as file:
        content = file.read()
    
    main_function = f"\nint main() {{ {name}(); return 0; }}\n"
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".c")
    with open(temp_file.name, 'w') as file:
        file.write(content)
        file.write(main_function)
    
    return temp_file.name

def compile_c_file(temp_file_path, output_name):
    """Compile the temporary .c file using gcc."""
    compile_command = f"gcc -Wall -Wextra -Wno-missing-braces -g -fsanitize=address -fsanitize=undefined -std=c99 -I../src ../src/ring.c {temp_file_path} -o {output_name} -lasan"
    subprocess.run(compile_command, shell=True)

def execute_and_check_output(executable):
    """Execute the executable and check if any line contains 'failed'."""
    retcode = 0
    result = subprocess.run(f"./{executable}", shell=True, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, text=True, check=False)
    retcode = result.returncode
    if retcode != 0:
        print(result.stdout)
        lines = result.stdout.splitlines()
        for line in lines:
            if 'failed.' in line:
                return True            
    return False

def cleanup(files):        
    for file in files:
        if os.path.isfile(file):
            os.remove(file)    

def main():
    c_files = find_c_files()
    executables = []
    temp_files = []
    for c_file in c_files:
        names = extract_names_from_file(c_file)
        for name in names:
            temp_file = create_temp_file_with_main(c_file, name)
            temp_files.append(temp_file)
            c_name = pathlib.Path(c_file).with_suffix('')
            exe_name = f'{c_name}_{name}'
            compile_c_file(temp_file, exe_name)
            executables.append(exe_name)

    failed_compilations = []    
    for executable in executables:
        if not os.path.isfile(executable):
            print(f"KO! Executable {executable} failed to compile")
            failed_compilations.append(executable)
    
    print("")
    if len(failed_compilations) != 0:
        print("KO! These executables couldn't be compiled:")
        for failed in failed_compilations:
            print(f"\t{failed}")
        cleanup(executables + temp_files)
        return
    
    failed_executables = []
    for executable in executables:
        if not execute_and_check_output(f"{executable}"):
            failed_executables.append(executable)
    
    print("\n")
    # Display the names of executables that did not produce 'failed' in their output
    if len(failed_executables) != 0:
        print("KO! The following tests either should have failed, or aborted for another reason:")
        for executable in failed_executables:
            print(f"\t{executable}")
    else:
        print(f"ok. All assertions were correctly triggered: {len(executables)} tests executed")    

    cleanup(executables + temp_files)

if __name__ == "__main__":
    main()
