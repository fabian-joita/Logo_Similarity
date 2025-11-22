# Disguising the bot
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive'
}

TIMEOUT = 15            # General timeout for HTTP requests (in seconds)
MAX_WORKERS = 4         # Maximum number of concurrent browser threads (workers)
                        # it can can be increased based on system capabilities

FORCE_VISUAL_RENDER = False  # If True, skips the fast HTTP request and forces Playwright for quality extraction. 
                             # Set to False to prioritize speed.

# IMAGE PROCESSING (PCA & STANDARDIZATION)
PCA_COMPONENTS = 25          # Number of principal components to retain.
TARGET_SIZE = (100, 100)     # Standardized pixel dimension for all final logos.

INPUT_CSV = "data/veridion.csv"
OUTPUT_FOLDER = "logo_dataset_pca"
OUTPUT_LOG_CSV = "data/mapare_finala_verificata.csv"