
import pandas as pd
try:
    df = pd.read_csv('datasets_4123_6408_framingham.csv')
    rec = df[df['TenYearCHD']==1].iloc[0]
    
    with open('unhealthy_case.txt', 'w') as f:
        f.write("Unhealthy Case Data:\n")
        for col, val in rec.items():
            f.write(f"{col}: {val}\n")
            
    print("Data extracted to unhealthy_case.txt")
except Exception as e:
    print(f"Error: {e}")
