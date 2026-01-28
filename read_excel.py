import pandas as pd

xl = pd.ExcelFile('Costos call center.xlsx')
print('Hojas encontradas:', xl.sheet_names)

for sheet in xl.sheet_names:
    print(f'\n{"="*60}')
    print(f'=== {sheet} ===')
    print(f'{"="*60}')
    df = pd.read_excel(xl, sheet)
    print(df.to_string())
    print(f'\nColumnas: {list(df.columns)}')
