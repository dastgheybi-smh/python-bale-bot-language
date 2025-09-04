"""PyBBM: Python Bale Bot Manager Language
By: Sayed Mohammad Hassan Dastgheybi
All rights reserved.

Version: 1.0
Template Version: 1.0"""

import os.path
import re
import sys
from pathlib import Path
import chardet

def indent_with_block(base_indent: str, code: str) -> str:
    return "\n".join(
        base_indent + line if line.strip() else line
        for line in code.splitlines()
    )

class PyBBMCompiler:
    def __init__(self, template_path: str):
        self.template = Path(template_path).read_text(encoding="utf-8")
        self.code_blocks = {}
        self.counter = 0
        self.output_blocks = {}

    def extract_blocks(self, src: str):

        def replacer(match):
            code = match.group(1).strip()
            key = f"code_id_{self.counter}"
            self.code_blocks[key] = code
            self.counter += 1
            return key

        return re.sub(r"\{([^}]*)\}", replacer, src, flags=re.S)

    def insert_into_block(self, block_name: str, code: str, where: str = "end"):
        if block_name not in self.output_blocks:
            self.output_blocks[block_name] = {"start": [], "end": []}
        self.output_blocks[block_name][where].append(code)

    def compile(self, src: str) -> str:
        src = self.extract_blocks(src)
        lines = [line.strip() for line in src.split(";") if line.strip()]

        for line in lines:
            # ---------------- on ----------------
            if line.startswith("on"):
                m = re.match(r'on\s+"([^"]+)"\s*:\s*(code_id_\d+)', line)
                if not m:
                    raise SyntaxError(f"Invalid on syntax: {line}")
                text_value, code_id = m.groups()
                block = self.code_blocks[code_id]
                code = f'if text == "{text_value}":\n{indent_with_block("    ", block)}'
                self.insert_into_block("on_statements", code, "end")

            # ---------------- let ----------------
            elif line.startswith("let"):
                m = re.match(r'let\s+(\w+)\s*=\s*(.+)', line)
                if not m:
                    raise SyntaxError(f"Invalid let syntax: {line}")
                var, val = m.groups()
                self.insert_into_block("variables", f"{var} = {val}", "end")

            # ---------------- exec ----------------
            elif line.startswith("exec"):
                m = re.match(r'exec\s+(code_id_\d+)\s+(\w+)(?:\s+(start|end))?', line)
                if not m:
                    raise SyntaxError(f"Invalid exec syntax: {line}")
                code_id, block_name, where = m.groups()
                block = self.code_blocks[code_id]
                where = where if where else "end"
                self.insert_into_block(block_name, block, where)

            else:
                raise SyntaxError(f"Unknown statement: {line}")

        out = self.template

        # ---------------- placement ----------------
        for block_name, parts in self.output_blocks.items():
            start_code = "\n".join(parts["start"])
            end_code = "\n".join(parts["end"])

            # finding block
            pattern = rf"(^[ \t]*)# {block_name}\n(.*?)(^[ \t]*)# end_{block_name}"
            match = re.search(pattern, out, flags=re.S | re.M)
            if not match:
                raise ValueError(f"Block '{block_name}' not found in template!")

            base_indent = match.group(1)

            # کدها با ایندنت بلاک
            start_code = indent_with_block(base_indent, start_code) if start_code else ""
            end_code = indent_with_block(base_indent, end_code) if end_code else ""

            repl = f"{base_indent}# {block_name}\n{start_code}\n{match.group(2)}{end_code}\n{match.group(3)}# end_{block_name}"
            out = re.sub(pattern, repl, out, flags=re.S | re.M)

        return out

compiler = PyBBMCompiler("template.txt")

if len(sys.argv) > 1:
    filepath = sys.argv[1]
else:
    filepath = input("enter filepath: ")


if not os.path.exists(filepath):
    print("File not found")
    sys.exit(1)
else:
    with open(filepath, "rb") as f:
        encoding = chardet.detect(f.read())["encoding"]
    with open(filepath, encoding=encoding) as f:
        code = f.read()

work = input("[R]un , [B]uild or [P]rint: ")
match work.lower():
    case "r":
        os.system("py -m pip install requests")
        exec(compiler.compile(code))
    case "b":
        output_path = input("enter output path: ")
        if not os.path.isdir(output_path):
            print("Output path must be a directory")
            sys.exit(1)
        name = input("enter name: ")
        with open(os.path.join(output_path, f"{name}.py"), "w", encoding="utf-8") as f:
            f.write(compiler.compile(code))
    case "p":
        print("\n========= Output ===========\n\n")
        print(compiler.compile(code))
    case _:
        print("Invalid input")
        sys.exit(1)
