"""Resolve git conflicts where both sides only added lines: keep ours then theirs."""
import re
import subprocess
import sys

files = subprocess.run(["git", "diff", "--name-only", "--diff-filter=U"], capture_output=True, text=True).stdout.split()
for p in files:
    s = open(p, encoding="utf-8").read()
    s = re.sub(r"<<<<<<< [^\n]*\n(.*?)=======\n(.*?)>>>>>>> [^\n]*\n", lambda m: m.group(1) + m.group(2), s, flags=re.S)
    open(p, "w", encoding="utf-8").write(s)
    subprocess.run(["git", "add", p], check=True)
print("resolved:", files)
