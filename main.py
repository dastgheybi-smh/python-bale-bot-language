"""PyBBM: Python Bale Bot Manager Language
By: Sayed Mohammad Hassan Dastgheybi
All rights reserved.

Version: 1.2
Template Version: 1.2"""

import os.path
import re
import sys
from pathlib import Path
import chardet


def indent_with_block(base_indent: str, _code: str) -> str:
    return "\n".join(
        base_indent + line if line.strip() else line
        for line in _code.splitlines()
    )


def strip_ftab(src: str):
    codes = src.split("\n")

    return_ = False

    while True:
        for i in codes:
            if not i.strip():
                continue
            if not i.startswith(" "):
                return_ = True
                break

        if return_:
            return "\n".join(codes)

        for i in range(len(codes)):
            if codes[i].strip():
                codes[i] = codes[i][1:]



class PyBBMCompiler:
    def __init__(self, template_path: str):
        self.status_checker_indent = ""
        self.status_checker = ""
        self.status_checker_used = False
        self.template = Path(template_path).read_text(encoding="utf-8")
        self.code_blocks = {}
        self.counter = 0
        self.output_blocks = {}

    def extract_blocks(self, src: str):

        def replacer(match):
            code = strip_ftab(match.group(1))
            key = f"code_id_{self.counter}"
            self.code_blocks[key] = code
            self.counter += 1
            return key

        return re.sub(r"`([^`]*)`", replacer, src, flags=re.S)

    def extract_status_checker(self, src: str):

        def replacer(match):
            if self.status_checker is not None:
                code = match.group(1).strip()
                key = f"status_checker"
                self.status_checker = code
                return key
            raise SyntaxError("Can't have more than one status checker")

        return re.sub(r"\[\[\[(.*)]]]", replacer, src, flags=re.DOTALL)



    def insert_into_block(self, block_name: str, code: str, where: str = "end"):
        if block_name not in self.output_blocks:
            self.output_blocks[block_name] = {"start": [], "end": []}
        self.output_blocks[block_name][where].append(code)

    def compile_to_list(self, src: str, included=""):
        src = self.extract_blocks(src)
        src = self.extract_status_checker(src)
        lines = [line.strip() for line in src.split(";") if line.strip()]
        excluded = False

        if lines[0] != "#exclude" and included:
            raise SyntaxError(f"Included file \"{included}\" is not importable")

        for line in lines:
            # ---------------- on ----------------
            if line.startswith("on"):
                m = re.match(r'on\s+\((.+)\)\s*:\s*(code_id_\d+)', line)
                if not m:
                    raise SyntaxError(f"Invalid on syntax: {line}")
                text_value, code_id = m.groups()
                block = self.code_blocks[code_id]
                el = ''
                use_text = True
                if text_value.startswith('!'):
                    use_text = False
                    text_value = text_value[1:]
                if text_value.endswith('?'):
                    el = 'el'
                    text_value = text_value[:-1]
                code = f'{self.status_checker_indent}{el}if {'text == ' if use_text else ''}{text_value}:\n{indent_with_block("    " + self.status_checker_indent, block)}'
                self.insert_into_block("on_statements", code, "end")

            # ---------------- let ----------------
            elif line.startswith("let"):
                m = re.match(r'^let(?:\{(\w+)})?\s+(\w+)\s*=\s*([\s\S]+)$', line)
                if not m:
                    raise SyntaxError(f"Invalid let syntax: {line}")
                block_in, var, val = m.groups()
                if not block_in:
                    block_in = "variables"
                self.insert_into_block(block_in, f"{var} = {val}", "end")

            # ---------------- exec ----------------
            elif line.startswith("exec"):
                m = re.match(r'^exec\s+(code_id_\d+)\s+(\w+)(?:\s+(start|end))?$', line)
                if not m:
                    raise SyntaxError(f"Invalid exec syntax: {line}")
                code_id, block_name, where = m.groups()
                block = self.code_blocks[code_id]
                where = where if where else "end"
                self.insert_into_block(block_name, block, where)

            # ---------------- import -------------------
            elif line.startswith("import"):
                m = re.match(r'^import\s+\{([^\n\r}]+)}(?:\s+from\s+\{(\w+)})?$', line)
                if not m:
                    raise SyntaxError(f"Invalid import syntax: {line}")
                imported, from_ = m.groups()
                if not from_:
                    expr = f"import {imported}"
                else:
                    expr = f"from {from_} import {imported}"
                self.insert_into_block("imports", expr)

            # -------------- include_tag ----------------
            elif line.startswith("#include"):
                m = re.match(r'^#include\s+"(.+)"$', line)
                if not m:
                    raise SyntaxError(f"Invalid include syntax: {line}")
                included_file_path = m.groups()[0]
                with open(included_file_path + ".bbm", "r", encoding="utf-8") as f_:
                    included = f_.read()
                self.compile_to_list(included, included_file_path)

            # -------------- exclude_tag -------------------
            elif line.startswith("#exclude"):
                excluded = True

            # --------------- comment ------------------------
            elif line.startswith("//"):
                pass

            # ------------ status_checker -----------------
            elif line.startswith("status_checker"):
                if excluded:
                    raise SyntaxError(f"Excluded file can't have status checker")
                if self.status_checker_used:
                    raise SyntaxError("Can't have more than one status checker")
                self.status_checker_used = True
                data = self.status_checker
                datas = [li.strip() for li in data.split("::") if li.strip()]
                if not len(datas):
                    raise SyntaxError(f"Status checker can not be empty")
                el = False
                for d in datas:
                    m = re.match(r"^\[(.+)]:(.*)", d, re.DOTALL)
                    ui_base = False
                    if not m:
                        m = re.match(r"^\{(.+)}:(.*)", d, re.DOTALL)
                        ui_base = True
                    if not m:
                        raise SyntaxError(f"Invalid status checker syntax: {d}")
                    self.status_checker_indent = "    "
                    status, codes = m.groups()
                    if not ui_base:
                        self.insert_into_block("on_statements", f"{'el' if el else ''}if status == {status}:")
                        self.compile_to_list("#exclude;"+codes, f"status_checker[{status}]")
                        el = True
                    else:
                        self.insert_into_block("status_checker_redirect", f"if CONST_STATUSES[chat_id] == {status}:")
                        self.insert_into_block("status_checker_redirect", indent_with_block("    ", codes))

                self.status_checker_indent = ""

            # ------------ series ------------------
            elif line.startswith("series"):
                m = re.match(r'^series\s+(\w+)$', line)
                if not m:
                    raise SyntaxError(f"Invalid series syntax: {line}")
                series = m.groups()[0]
                self.insert_into_block("variables", "CONST_" + series.upper() + " = {}")
                self.insert_into_block("variables", f"default_{series} = \"\"")
                self.insert_into_block("series_setter", f"CONST_{series.upper()}[chat_id] = {series}")
                self.insert_into_block("series", f"""{series} = CONST_{series.upper()}.get(chat_id)
if {series} is None:
    CONST_{series.upper()}[chat_id] = default_{series}
    {series} = default_{series}""")

            # ----------------- else --------------------

            else:
                raise SyntaxError(f"Unknown statement: {line}")



    def compile_to_template(self, src: str) -> str:

        self.compile_to_list(src)

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

            start_code = indent_with_block(base_indent, start_code) if start_code else ""
            end_code = indent_with_block(base_indent, end_code) if end_code else ""

            repl = f"{base_indent}# {block_name}\n{start_code}\n{match.group(2)}{end_code}\n{match.group(3)}# end_{block_name}"
            out = re.sub(pattern, repl, out, flags=re.S | re.M)

        return out

current_path = os.path.dirname(os.path.abspath(__file__))

compiler = PyBBMCompiler(os.path.join(current_path, "template.py"))

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
        exec(compiler.compile_to_template(code))
    case "b":
        output_path = input("enter output path: ")
        if not os.path.isdir(output_path):
            print("Output path must be a directory")
            sys.exit(1)
        name = input("enter name: ")
        with open(os.path.join(output_path, f"{name}.py"), "w", encoding="utf-8") as f:
            f.write(compiler.compile_to_template(code))
    case "p":
        print("\n========= Output ===========\n\n")
        print(compiler.compile_to_template(code))
    case "bc":
        output_path = input("enter output path: ")
        if not os.path.isdir(output_path):
            print("Output path must be a directory")
            sys.exit(1)
        name = input("enter name: ")
        compiler_ = PyBBMCompiler(filepath)
        with open(os.path.join(output_path, f"{name}.py"), "w", encoding=encoding) as f:
            f.write(compiler_.compile_to_template(code))
    case _:
        print("Invalid input")
        sys.exit(1)
