import csv

CSV = r"C:\Users\droig\Proyectos\CSJ\buzon\entrante\cancelaciones.csv"
OUT = r"C:\Users\droig\Proyectos\CSJ\buzon\entrante\_temp_out.txt"

lines = []

# Try semicolon
with open(CSV, newline='', encoding='utf-8') as f:
    reader = csv.reader(f, delimiter=';')
    for i, row in enumerate(reader):
        if i < 6:
            lines.append(f"ROW {i}: {row}")

lines.append("---")

# Also show raw first 3 lines
with open(CSV, encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i < 3:
            lines.append(f"RAW {i}: {repr(line[:200])}")

with open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print("Done")
