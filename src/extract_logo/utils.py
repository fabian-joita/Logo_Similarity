import os
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import base64
import urllib3
from .config import HEADERS, TIMEOUT 

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def safe_folder(path):
    """Creates a directory if it does not exist."""
    if not os.path.exists(path): os.makedirs(path)

def normalize_url(url):
    """Ensures the URL starts with https:// if no protocol is present."""
    url = url.strip()
    if not url.startswith("http"): return "https://" + url
    return url

def get_base(url):
    """Extracts the base URL (protocol + netloc) from a full URL."""
    try:
        return urlparse(url).scheme + "://" + urlparse(url).netloc
    except: return url

def download_html(url):
    """
    Attempts to download HTML content. Includes a fallback attempt by
    adding 'www.' if the initial connection fails.
    """
    # 1. Initial Attempt
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False)
        if r.status_code == 200: 
            return r.text, r.url
        
        # If server responds with 403/404, we print status and fail this attempt.
        print(f"[HTTP] Response Code: {r.status_code}")
        return None, None
        
    except requests.exceptions.ConnectionError:
        # 2. Connection Error -> Try with 'www.' fallback
        print(f"[HTTP] Direct connection error. Trying with www...")
        
        try:
            parsed = urlparse(url)
            netloc_no_www = parsed.netloc.replace("www.", "")
            
            # Construct the new URL: https://www.domain.com/path
            www_url = parsed.scheme + "://www." + netloc_no_www + parsed.path
            
            r = requests.get(www_url, headers=HEADERS, timeout=TIMEOUT, verify=False)
            if r.status_code == 200:
                print("[HTTP] Success with www.")
                return r.text, r.url
            
            print(f"[HTTP] WWW Response Code: {r.status_code}")
            return None, None

        except Exception as e:
            print(f"[HTML Error] Total failure at both addresses: {e}")
            return None, None
            
    except requests.exceptions.RequestException as e:
        print(f"[HTML Error] General Requests error: {e}")
        return None, None
    except: return None, None


def download_image_bytes(src, base_url):
    """Downloads image bytes from a URL, handling relative paths."""
    if not src: return None
    
    # Base64 Handling (only decoding, not cleaning)
    if src.startswith("data:"):
        try:
            if "base64," in src:
                return base64.b64decode(src.split("base64,", 1)[1])
            return None
        except: return None

    # HTTP Download
    if not src.startswith("http"): src = urljoin(base_url, src)
    try:
        r = requests.get(src, headers=HEADERS, timeout=10, verify=False)
        if r.status_code == 200: return r.content
    except: pass
    return None

def find_logo_in_header(html, base_url):
    """
    Searches HTML content for likely logo images based on common keywords 
    in src and element attributes.
    """
    try:
        soup = BeautifulSoup(html, "html.parser")
        for img in soup.find_all("img"):
            src = img.get("src")
            if not src: continue
            # Look for 'logo' or 'brand' keywords
            if "logo" in src.lower() or "brand" in str(img).lower():
                return src
    except: pass
    return None

def get_domain_key_from_url(url):
    """ 
    Extracts the safe domain key for mapping/naming files (e.g., https://www.tesla.com/ -> tesla).
    """
    try:
        url = str(url).strip()
        if not url: return None
        if not url.startswith("http"):
            url = "https://" + url
            
        netloc = urlparse(url).netloc
        
        # Strip www.
        domain = netloc.replace("www.", "").split('.')[0]
        
        # Aggressively remove hyphens to get the base brand name (e.g., mazda-dealer -> mazda)
        domain_key = domain.split('-')[0]
        
        return domain_key.lower()
    except:
        return None