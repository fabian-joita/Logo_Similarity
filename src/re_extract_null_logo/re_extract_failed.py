import pandas as pd
import concurrent.futures
from tqdm import tqdm
import os
import time

from main_for_test import run_pipeline_single_site 
from src.extract_logo.config import MAX_WORKERS, OUTPUT_LOG_CSV

def re_extract_worker(url):
    """
    Worker that executes the full extraction pipeline for a single failed URL.
    Returns status for logging (RE_SUCCESS or RE_FAILED).
    """
    try:
        url = str(url).strip()
        
        # Call the single-site pipeline (Requests -> Playwright -> PCA -> Save)
        # This function returns True on success, False on failure.
        status_success = run_pipeline_single_site(url) 
        
        return {"url": url, "status": "RE_SUCCESS" if status_success else "RE_FAILED"}
    except Exception as e:
        # Catch unexpected thread crashes
        return {"url": url, "status": "CRASH", "error": str(e)}

def main():
    if not os.path.exists(OUTPUT_LOG_CSV):
        print(f"Error: Log file not found at {OUTPUT_LOG_CSV}")
        return

    try:
        df = pd.read_csv(OUTPUT_LOG_CSV)
        
        failed_urls = df[df['Status'].isin(['NULL', 'FAILED_NOT_FOUND', 'FAILED_NOT_SAVED', 'INVALID_URL'])]['URL'].dropna().unique().tolist()
        
        if not failed_urls:
            print(" All logos have already been mapped. Nothing left to re-extract.")
            return

        print(f"\n Starting re-extraction for {len(failed_urls)} failed URLs...")
        print(f" Using {MAX_WORKERS} concurrent browsers.")
        
    except Exception as e:
        print(f"Error reading/filtering log: {e}")
        return

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # tqdm for the visible progress bar
        list(tqdm(executor.map(re_extract_worker, failed_urls), total=len(failed_urls), unit="site"))

    print("\nRe-extraction finalized. New logos have been saved to the 'logo_dataset_pca' folder.")
    print("\n-------------------------------------------------")
    print("CRITICAL NEXT STEP: UPDATE THE FINAL MAP")
    print("-------------------------------------------------")
    print("ACTION: Run the final mapping script (e.g., post_extraction_mapper.py) to consolidate the new results.")

if __name__ == "__main__":
    main()