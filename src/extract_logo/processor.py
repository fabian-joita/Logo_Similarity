from PIL import Image, ImageOps
from io import BytesIO
import numpy as np
from sklearn.decomposition import PCA
from urllib.parse import urlparse
import os
import cairosvg
import base64
from .config import PCA_COMPONENTS, TARGET_SIZE, OUTPUT_FOLDER 
from .utils import safe_folder, download_image_bytes

def process_image_with_pca(img_bytes):
    """
    The 'Brain' function: Loads image, applies smart contrast normalization,
    standardizes geometry (padding), applies PCA compression, and reconstructs the image.
    """
    try:
        img = Image.open(BytesIO(img_bytes))
        
        if img.width < 5 or img.height < 5 or img.getbbox() is None: return None

        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            img = img.convert('RGBA')
            np_img = np.array(img)
            alpha = np_img[:, :, 3]
            mask = alpha > 0
            
            if mask.sum() > 0:
                rgb = np_img[mask][:, :3]
                avg_brightness = np.mean(rgb)
            else:
                return None
        else:
            img = img.convert('RGB')
            avg_brightness = np.mean(np.array(img))

        if avg_brightness < 128: # Dark Logo (e.g., Toyota Black)
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'RGBA': background.paste(img, mask=img.split()[3])
            else: background.paste(img)
            img_processed = ImageOps.invert(background.convert('L'))
        else: # Light Logo (e.g., Mazda White)
            # Paste onto BLACK background (already results in White on Black).
            background = Image.new('RGB', img.size, (0, 0, 0))
            if img.mode == 'RGBA': background.paste(img, mask=img.split()[3])
            else: background.paste(img)
            img_processed = background.convert('L')

        img_padded = ImageOps.pad(img_processed, TARGET_SIZE, color="black", centering=(0.5, 0.5))
        
        # PCA Application
        img_matrix = np.array(img_padded)
        
        # Check for zero variance (solid color image)
        if np.std(img_matrix) < 1: return None

        # Limit components (k)
        n_comp = min(PCA_COMPONENTS, min(img_matrix.shape))
        
        print(f" Applying PCA ({n_comp} components)...")
        pca = PCA(n_components=n_comp)
        img_transformed = pca.fit_transform(img_matrix)
        img_reconstructed = pca.inverse_transform(img_transformed)
        
        img_final_array = np.clip(img_reconstructed, 0, 255).astype('uint8')
        final = Image.fromarray(img_final_array)
        
        # Export PNG bytes
        buf = BytesIO()
        final.save(buf, format="PNG")
        return buf.getvalue()

    except Exception as e:
        print(f" PCA processing error: {e}")
        return None

def process_and_save(logo_src, base_url):
    """
    Orchestrates extraction, PCA, and final saving to disk.
    Returns True on successful save, False otherwise.
    """
    safe_folder(OUTPUT_FOLDER)
    img_bytes = None
    
    if logo_src.startswith("data:"):
        try:
            if "base64," in logo_src:
                img_bytes = base64.b64decode(logo_src.split("base64,", 1)[1])
            elif "svg" in logo_src:
                from urllib.parse import unquote
                txt = unquote(logo_src.split(",", 1)[1]).replace("currentColor", "#000")
                img_bytes = txt.encode('utf-8')
        except: pass
    else:
        img_bytes = download_image_bytes(logo_src, base_url)

    if not img_bytes: return False

    # CONVERT SVG to PNG
    if logo_src.lower().endswith(".svg") or (b"<svg" in img_bytes[:300]):
        try: img_bytes = cairosvg.svg2png(bytestring=img_bytes, scale=10)
        except: pass

    # PCA & STANDARDIZATION
    final_bytes = process_image_with_pca(img_bytes)
    
    if final_bytes:
        try:
            # Correct Naming Logic (Penultimate segment)
            netloc = urlparse(base_url).netloc.replace("www.", "")
            parts = netloc.split('.')
            domain = parts[-2] if len(parts) >= 2 else parts[0]
            
            filename = f"{OUTPUT_FOLDER}/{domain}.png"
            with open(filename, "wb") as f: f.write(final_bytes)
            print(f"✅ Saved: {filename}")
            return True
        except Exception as e:
            # print(f"Error during final save/naming: {e}")
            pass
        
    return False