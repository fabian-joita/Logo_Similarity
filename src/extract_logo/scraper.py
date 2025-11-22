from playwright.sync_api import sync_playwright
from urllib.parse import urlparse
import base64
import time
import re

def extract_brand_name(url):
    """
    Extracts the base brand name from the URL for targeted scraping.
    Ex: 'https://mazda-autohaus.de' -> 'mazda'
    """
    try:
        domain = urlparse(url).netloc.replace("www.", "")
        return domain.split('.')[0].split('-')[0]
    except: return None

def get_logo_with_playwright(url):
    """
    Launches a visible (non-headless) Chromium instance for robust logo extraction,
    applies dynamic selectors, scores candidates, and returns a Base64 screenshot.
    """
    brand_name = extract_brand_name(url)
    print(f"🚀 [SPECIAL MODE] Analyzing: {url} (Brand: {brand_name})")

    logo_data = None

    with sync_playwright() as p:
        # Launch visible browser (headless=False) to bypass aggressive anti-bot detection (Tesla, etc.)
        browser = p.chromium.launch(
            headless=False, 
            args=["--disable-blink-features=AutomationControlled", "--start-maximized"]
        )
        
        # Context setup: standard resolution and ignores self-signed SSL errors
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            ignore_https_errors=True
        )
        page = context.new_page()

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # SMART WAIT for full network idle
            try:
                # Wait up to 10 seconds for network activity to settle.
                page.wait_for_load_state("networkidle", timeout=10000)
                print(" Site loaded (Network Idle).")
            except:
                print("!!! Network timeout reached, proceeding with rendering.")
                pass

            # Handle Cookies/Consent Banners
            try:
                # Look for common acceptance buttons
                cookie_btn = page.locator("button").filter(has_text=re.compile(r"(Accept|Agree|Allow|Salli|Hyväksy|Cookies|OK|Alle)", re.IGNORECASE)).first
                cookie_btn.click(timeout=2000)
                time.sleep(1) # Short delay for banner to disappear
            except: pass

            # LIST OF SELECTORS (Hybrid: Structural + Dynamic + Fuzzy)
            container_selectors = [
                # Static & Critical Selectors (Tesla, Home Link SVG)
                "header a[href='/']",
                "a[href='/'] svg",
                "header svg",
                
                # Dynamic/Brand Specific Selectors
                "a[aria-label='Home']",
                "a[aria-label*='Tesla']",
            ]

            if brand_name:
                container_selectors.append(f"img[alt*='{brand_name}' i]")
                container_selectors.append(f"img[src*='{brand_name}' i]")
                container_selectors.append(f"a[aria-label*='{brand_name}' i]")

            #  Fuzzy Fallback Selectors (WWF, Elementor sites)
            container_selectors.extend([
                "img[src*='logo' i]", 
                "img[class*='logo' i]", 
                ".navbar-brand", 
                ".logo a", 
                ".custom-logo-link", 
                ".elementor-widget-image img"
            ])

            candidates = []

            # Scan and Score
            for selector in container_selectors:
                elements = page.locator(selector).all()
                for el in elements:
                    if el.is_visible():
                        box = el.bounding_box()
                        
                        # Filter: Must be of reasonable size (not 1x1 pixel or massive banner)
                        if box and box['width'] > 20 and box['height'] > 10 and box['width'] < 900:
                            
                            src = el.get_attribute("src") or ""
                            alt = el.get_attribute("alt") or ""
                            aria = el.get_attribute("aria-label") or ""
                            href = el.get_attribute("href") or ""
                            tag = el.evaluate("el => el.tagName").lower()
                            
                            # SCORING LOGIC
                            score = 0
                            
                            # 1. Primary Link Bonus (Critical)
                            if href == '/' or href == url or href == url + '/': score += 300
                            if selector == "header a[href='/']": score += 350
                            
                            # 2. Brand Match Bonus (e.g., Mazda dealer)
                            if brand_name and (brand_name in src or brand_name in alt or brand_name in aria): score += 400
                            
                            # 3. Position Bonus (Logo is always at the top)
                            if box['y'] < 150: score += 100
                            if box['y'] > 300: score -= 500 # Penalize low-page content images

                            # 4. SVG/Quality Bonus
                            if tag == 'svg' or ".svg" in src: score += 50
                            
                            # 5. Width (Preference for text)
                            score += min(box['width'], 300) / 5

                            candidates.append({
                                "element": el,
                                "width": box['width'],
                                "score": score,
                                "selector": selector
                            })

            if candidates:
                # Select the winner based on the highest score
                candidates.sort(key=lambda x: x['score'], reverse=True)
                best = candidates[0]
                element_to_capture = best['element']
                
                print(f" Winner: {int(best['width'])}px (Score: {best['score']:.1f}) Selector: {best['selector']}")

                # Visual Fix: Inject White Background (for transparent logos like Tesla)
                try:
                    element_to_capture.evaluate("""el => {
                        el.style.backgroundColor = '#FFFFFF'; 
                        el.style.padding = '10px';
                        el.style.display = 'inline-block';
                        el.style.visibility = 'visible';
                        el.style.opacity = '1';
                        if(el.tagName === 'svg' || el.tagName === 'path') {
                             el.style.fill = 'black'; # Ensure white SVGs show up as black for processing
                        }
                    }""")
                    time.sleep(0.5)
                except: pass

                # Screenshot
                png_bytes = element_to_capture.screenshot()
                b64 = base64.b64encode(png_bytes).decode('utf-8')
                logo_data = f"data:image/png;base64,{b64}"
                print(" Screenshot successful!")

            else:
                print(" No suitable candidates found.")
                
        except Exception as e:
            print(f" Browser error: {e}")
            pass
        finally:
            browser.close()
            
    return logo_data