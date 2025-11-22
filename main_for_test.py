import sys
from src.extract_logo.config import FORCE_VISUAL_RENDER
from src.extract_logo.utils import normalize_url, download_html, get_base, find_logo_in_header
from src.extract_logo.scraper import get_logo_with_playwright
from src.extract_logo.processor import process_and_save

def run_pipeline_single_site(url):
    """
    Main logic:
    1. Try Requests (Fast)
    2. If it fails, activate Playwright (Robust)
    3. Send result to Processing (PCA + Save)
    """
    url = normalize_url(url)
    print(f"\n--- ! Start Analysis: {url} ! ---")
    
    success = False
    base = url
    logo_src = None

    # FAST METHOD (HTTP REQUESTS)
    if not FORCE_VISUAL_RENDER:
        print("1 Trying fast method (Requests)...")
        html, final_url = download_html(url)
        
        if html:
            if final_url: 
                base = get_base(final_url)
            
            logo_src = find_logo_in_header(html, base)
            
            if logo_src:
                if process_and_save(logo_src, base):
                    print(" [FAST] Logo extracted and processed successfully!")
                    success = True

    # BRUTE METHOD => higher time and resource consumption (PLAYWRIGHT)
    if not success:
        print(" [FALLBACK] Activating Special Mode (Playwright)...")
        try:
            # Playwright returns Base64 PNG directly
            logo_src = get_logo_with_playwright(url)
            
            if logo_src:
                if process_and_save(logo_src, url):
                    print("SOLVED => [BROWSER] Logo extracted via screenshot!")
                    success = True
        except Exception as e:
            print(f"!!!!! Error in Playwright mode: {e}")

    # FINALIZATION
    if not success:
        print(" [FAILURE] Could not extract a valid logo for this site.")
        return False
    
    return True

if __name__ == "__main__":
    # You can run this file directly to test a specific site
    # Example: python main.py tesla.com
    
    target_site = "tesla.com"
    
    # If a command line argument is provided, use it
    if len(sys.argv) > 1:
        target_site = sys.argv[1]
        
    run_pipeline_single_site(target_site)