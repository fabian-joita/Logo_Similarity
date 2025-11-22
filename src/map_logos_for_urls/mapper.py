import pandas as pd
import os
from urllib.parse import urlparse
import csv

from src.extract_logo.config import INPUT_CSV, OUTPUT_LOG_CSV, OUTPUT_FOLDER
from src.extract_logo.utils import get_domain_key_from_url

def create_final_map():
    """
    Reads the list of processed URLs and maps each URL to a successfully
    extracted logo file on disk, using the Truncation Search method.
    """
    # 1. Load the list of unique, cleaned URLs from the input CSV
    try:
        df_input = pd.read_csv(INPUT_CSV)
        col_name = df_input.columns[0]
        # Drop NaNs and get unique URLs to process
        urls = df_input[col_name].dropna().unique().tolist()
    except Exception as e:
        print(f"Error reading CSV '{INPUT_CSV}'. Error: {e}")
        return

    # 2. Check if the output folder exists
    if not os.path.exists(OUTPUT_FOLDER):
        print(f" Output folder '{OUTPUT_FOLDER}' does not exist. Run the extraction script first.")
        return

    saved_files = os.listdir(OUTPUT_FOLDER)
    mapping_results = []
    
    print(f"🚀 Starting mapping for {len(urls)} valid URLs using aggressive search...")

    # 3. Iterate through URLs and search for the corresponding file
    for url in urls:
        url = str(url).strip()
        # Derive the base key (e.g., 'tesla', 'williamblairfunds')
        initial_key = get_domain_key_from_url(url) 
        
        if not initial_key or initial_key == "unknown":
            mapping_results.append({"URL": url, "Image_Filename": "NULL", "Status": "INVALID_URL"})
            continue

        found_filename = None
        current_key = initial_key
        min_length = 3 
        
        # --- TRUNCATION SEARCH LOGIC (Aggressive Fallback) ---
        # This loop tries 'williamblairfunds', then 'williamblairfund', 'williamblairfun', etc., 
        # to find logos saved with abbreviated or slightly incorrect names.
        while len(current_key) >= min_length:
            for filename in saved_files:
                # Match files that start with the current key and end with .png
                if filename.startswith(current_key) and filename.lower().endswith(".png"):
                    found_filename = filename
                    break
            
            if found_filename:
                break

            # Shorten the key by removing the last character
            current_key = current_key[:-1]
        
        # 4. Record the result
        if found_filename:
            mapping_results.append({
                "URL": url, 
                "Image_Filename": found_filename, 
                "Status": "SUCCESS"
            })
        else:
            mapping_results.append({
                "URL": url, 
                "Image_Filename": "NULL", 
                "Status": "FAILED_NOT_FOUND"
            })

    # 5. Final Saving and Reporting
    df_results = pd.DataFrame(mapping_results)
    
    success_count = df_results[df_results['Status'] == 'SUCCESS'].shape[0]
    failed_count = df_results[df_results['Status'] == 'FAILED_NOT_FOUND'].shape[0]
    
    df_results.to_csv(OUTPUT_LOG_CSV, index=False, quoting=csv.QUOTE_NONNUMERIC)
    
    print("\n" + "="*50)
    print("MAPPING FINALIZED!")
    print(f"Total mapped URLs (valid): {len(urls)}")
    print(f" Logos Found (SUCCESS): {success_count}")
    print(f" Missing Logos (NULL): {failed_count}")
    print(f"Mapping report saved to: {OUTPUT_LOG_CSV}")
    print("="*50)


if __name__ == "__main__":
    create_final_map()