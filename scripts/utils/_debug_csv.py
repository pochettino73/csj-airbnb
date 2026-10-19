import csv

CSV = r"C:\Users\droig\Proyectos\CSJ\buzon\entrante\cancelaciones.csv"
OUT = r"C:\Users\droig\Proyectos\CSJ\buzon\entrante\_temp_out.txt"

lines = []
with open(CSV, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    lines.append(f"FIELDS: {reader.fieldnames}")
    for i, row in enumerate(reader):
        if i < 5:
            lines.append(str(dict(row)))

with open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print("Done")
