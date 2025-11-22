import pandas as pd
import concurrent.futures
from tqdm import tqdm
from src.extract_logo.utils import normalize_url, download_html, get_base, find_logo_in_header
from src.extract_logo.processor import process_and_save
from src.extract_logo.scraper import get_logo_with_playwright
from src.extract_logo.config import FORCE_VISUAL_RENDER, MAX_WORKERS

INPUT_CSV = "./data/veridion.csv"

def process_single_site(url):
    url = normalize_url(url)
    # print(f"Processing: {url}")
    
    success = False
    base = url
    
    if not FORCE_VISUAL_RENDER:
        html, final_url = download_html(url)
        if html:
            if final_url: base = get_base(final_url)
            logo_src = find_logo_in_header(html, base)
            if logo_src:
                success = process_and_save(logo_src, base)

    if not success:
        try:
            logo_src = get_logo_with_playwright(url)
            if logo_src:
                success = process_and_save(logo_src, url)
        except: pass
        
    return "Done"

def main():
    try:
        df = pd.read_csv(INPUT_CSV)
        urls = df.iloc[:, 0].dropna().tolist()
        
        print(f"🚀 Pornire Batch: {len(urls)} site-uri | {MAX_WORKERS} workers")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            list(tqdm(executor.map(process_single_site, urls), total=len(urls)))
            
    except Exception as e:
        print(f"Eroare: {e}")

if __name__ == "__main__":
    main()