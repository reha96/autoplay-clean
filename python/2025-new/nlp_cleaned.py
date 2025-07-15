#!/usr/bin/env python3
"""
Extract 184 strategy sentences for manual validation
Output: ID and sentence side by side for color coding
Export: Excel file with participant ID and feedback columns
"""
# %%%
import pandas as pd

# List of 184 participant IDs
included_ids = [0,1,2,3,4,5,6,7,10,11,13,17,18,21,22,25,26,27,28,29,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,48,49,50,51,52,53,54,57,58,59,60,61,62,64,65,66,67,68,70,71,73,74,75,76,77,78,79,80,81,83,84,85,86,87,88,89,91,92,93,94,95,96,97,98,99,100,101,103,104,105,107,108,109,110,113,115,116,117,119,120,122,123,124,125,126,128,129,130,132,133,134,135,136,137,138,141,142,143,144,146,147,149,150,151,152,153,154,155,156,157,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,180,181,182,183,184,185,186,188,189,190,192,193,194,195,196,197,198,200,201,202,203,206,207,208,209,210,211,212,213,214,215,216,217,218,219,220,221,222,223]

def extract_sentences(csv_file_path):
    # Read CSV file
    df = pd.read_csv(csv_file_path)
    
    # Extract sentences and feedback for included IDs
    data = []
    
    for participant_id in included_ids:
        if participant_id < len(df):
            strategy = df.iloc[participant_id]['strategy']
            feedback = df.iloc[participant_id]['feedback'] if 'feedback' in df.columns else None
            
            if pd.notna(strategy) and str(strategy).strip():
                data.append({
                    'participant_id': participant_id,
                    'strategy': str(strategy).strip(),
                    'feedback': str(feedback).strip() if pd.notna(feedback) else ''
                })
    
    return data

def main():
    # Extract sentences and feedback (replace 'autoplay.csv' with your file path)
    data = extract_sentences('autoplay.csv')
    
    # Create DataFrame
    df_export = pd.DataFrame(data)
    
    # Output format: ID | Sentence
    print(f"Extracted {len(data)} strategy sentences for manual validation\n")
    print("ID   | Strategy Sentence")
    print("-----|" + "-" * 80)
    
    for row in data:
        print(f"{row['participant_id']:4d} | {row['strategy']}")
    
    # Export to Excel with participant_id and feedback columns
    df_export.to_excel('/Users/reha.tuncer/Documents/GitHub/autoplay/stata/nlp-clean.xlsx', index=False)
    print(f"\nExported {len(data)} records to nlp-clean.xlsx")
    print("Columns: participant_id, strategy, feedback")

if __name__ == "__main__":
    main()
    
    # %%%