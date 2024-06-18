import re
import pandas as pd
import PyPDF2
import os

def pdf_to_text(pdf_path, txt_path):
    # Open the PDF file
    with open(pdf_path, 'rb') as pdf_file:
        # Create a PDF reader object
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # Initialize an empty string to store the text
        text = ""
        # Initialize a flag to check if we are within the target section
        in_target_section = False
        
        # Iterate through each page and extract the text
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                # Split the page text into lines
                lines = page_text.splitlines()
                
                for line in lines:
                    # Check for the start of the target section
                    if "TANGGAL KETERANGAN CBG MUTASI SALDO" in line:
                        in_target_section = True
                        continue  # Skip the line with the header
                    
                    # Check for the end of the target section
                    if "Bersambung ke Halaman berikut" in line or "SALDO AWAL :" in line:
                        in_target_section = False
                    
                    # If we are within the target section, add the line to the text
                    if in_target_section:
                        text += line.lstrip() + "\n"
        
        # Write the text to a text file
        with open(txt_path, 'w', encoding='utf-8') as txt_file:
            txt_file.write(text)

# Define patterns
date_pattern = re.compile(r'^\d{2}/\d{2}$')
db_cr_terms = ["KR", "CR", "DB"]

# Function to check if a word contains ',' before '.'
def has_comma_before_dot(word):
    return ',' in word and '.' in word and word.find(',') < word.find('.')

# Function to process a line
def process_line(line, previous_row=None):
    # Skip processing if the line is empty or contains only whitespace
    if not line.strip():
        return None

    # Initialize the dictionary for the row
    row = {
        "Date": "",
        "Keterangan": "",
        "DB/CR": "",
        "Debit": "",
        "Credit": "",
        "Saldo": ""
    }

    # Check for "SALDO AWAL"
    if "SALDO AWAL" in line:
        words = line.split()
        for word in words:
            if date_pattern.match(word):
                row["Date"] = word
            elif has_comma_before_dot(word):
                row["Saldo"] = word
        row["Keterangan"] = "Saldo Awal"
        row["DB/CR"] = "DB"
        row["Debit"] = 0
        row["Credit"] = 0
        return row

    # Split the line into an array of strings
    words = line.split()

    # Check if the first word is not a date format, then append the whole line to the previous "Keterangan"
    if previous_row and not date_pattern.match(words[0]):
        previous_row["Keterangan"] += line + " "
        return previous_row

    # First loop to process date and DB/CR terms
    for word in words:
        if date_pattern.match(word):
            row["Date"] = word
        elif word in db_cr_terms:
            if word == "KR":
                row["DB/CR"] = "CR"
            else:
                row["DB/CR"] = word
                
    # Custom conditions for DB/CR based on line content
    if "BIAYA" in line and "ADM" in line:
        row["DB/CR"] = "CR"
    elif "PAJAK" in line and "BUNGA" in line:
        row["DB/CR"] = "CR"

    # If "DB/CR" is not assigned, default it to "DB"
    if not row["DB/CR"]:
        row["DB/CR"] = "CR"

    # Second loop to process financial amounts and description
    for word in words:
        if has_comma_before_dot(word):
            if row["DB/CR"] != "DB":
                if not row["Debit"]:
                    row["Debit"] = word
                    row["Credit"] = 0
                else:
                    row["Saldo"] = word
            elif row["DB/CR"] == "DB":
                if not row["Credit"]:
                    row["Credit"] = word
                    row["Debit"] = 0
                else:
                    row["Saldo"] = word
        elif word not in db_cr_terms and not date_pattern.match(word):
            row["Keterangan"] += word + " "

    # Strip any trailing whitespace from "Keterangan"
    row["Keterangan"] = row["Keterangan"].strip()


    return row

def process_pdf(input_pdf_path, output_folder):
    try:
        # Define paths
        txt_path = os.path.join(output_folder, "output.txt")
        output_excel_path = os.path.join(output_folder, "output.xlsx")

        # Convert PDF to text
        pdf_to_text(input_pdf_path, txt_path)

        # Read lines from the file
        with open(txt_path, "r") as file:
            lines = file.readlines()

        # Process each line
        processed_rows = []
        previous_row = None
        for line in lines:
            row = process_line(line, previous_row)
            if row:
                if previous_row != row:
                    processed_rows.append(row)
                previous_row = row

        # Create a DataFrame from the processed rows
        df = pd.DataFrame(processed_rows)

        # Reorder columns
        df = df[["Date", "Keterangan", "DB/CR", "Debit", "Credit", "Saldo"]]

        # Write DataFrame to Excel
        df.to_excel(output_excel_path, index=False)

        return output_excel_path
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
