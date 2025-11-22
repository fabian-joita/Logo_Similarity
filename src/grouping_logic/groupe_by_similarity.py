import os
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import pairwise_distances
from collections import defaultdict
import csv
import warnings
import time

warnings.filterwarnings('ignore', category=UserWarning) 

INPUT_DIR = "logo_dataset_pca"
OUTPUT_CSV = "mapare_categorii_finale.csv"
SKIP_REPORT_CSV = "skip_report_detaliat.csv"
PCA_COMPONENTS = 50                 
SIMILARITY_THRESHOLD = 2500
IMAGE_SIZE = (100, 100)             

def load_and_vectorize_images():
    """
    Loads all images, forces resizing for matrix compatibility, and vectorizes them.
    Returns the data matrix X and a list of skipped file logs.
    """
    image_list = []
    metadata = []
    skipped_logs = []
    
    print("Loading and vectorizing images...")
    
    for filename in os.listdir(INPUT_DIR):
        if not filename.lower().endswith(".png") or filename.startswith('.'):
            continue
            
        filepath = os.path.join(INPUT_DIR, filename)
        
        try:
            img = Image.open(filepath)
            
            # Ensure Grayscale
            if img.mode != 'L':
                img = img.convert('RGB').convert('L')
            
            if img.size != IMAGE_SIZE:
                img = img.resize(IMAGE_SIZE, Image.Resampling.LANCZOS)
            
            # Vectorization (Flattening the 100x100 matrix to a 10000-element vector)
            vector = np.array(img).flatten()
            image_list.append(vector)
            
            domain_key = filename.split('.')[0].split('_')[0]
            metadata.append({"filename": filename, "domain_key": domain_key})
                
        except Exception as e:
            skipped_logs.append({
                "filename": filename,
                "error_type": e.__class__.__name__,
                "reason": str(e)
            })
            continue
            
    X = np.array(image_list)
    print(f"   X Matrix created: {X.shape} (N={X.shape[0]} samples, n={X.shape[1]} features)")
    print(f"   Total skipped files: {len(skipped_logs)}")
    return X, metadata, skipped_logs

def apply_pca_and_get_features(X):
    """ Applies PCA to reduce the 10000 features down to k principal components (scores). """
    n_features = X.shape[1]
    X_mean = X - np.mean(X, axis=0)
    
    n_comp = min(PCA_COMPONENTS, n_features)
    pca = PCA(n_components=n_comp)
    
    # Projection onto the new basis (T matrix of scores)
    T = pca.fit_transform(X_mean)
    
    print(f"   Dimensionality reduction: {n_features} -> {T.shape[1]} features (scores).")
    return T

def group_by_threshold(T, threshold, metadata):
    """ 
    Deterministic Grouping: Creates groups (connected components) based on
    Euclidean distance threshold (non-ML clustering). 
    """
    print("   Calculating distances and forming graph...")
    
    print("   Calculating distances and forming graph...")
    
    distance_matrix = pairwise_distances(T, metric='euclidean')
    
    # CODE FOR SCALING DEBUGGING
    max_distance = np.max(distance_matrix)
    avg_distance = np.mean(distance_matrix)
    
    print(f" DEBUG DISTANCES:")
    print(f"   Max Distance (between most dissimilar): {max_distance:.2f}")
    print(f"   Average Distance: {avg_distance:.2f}")
    print(f"   Current Threshold (ε): {threshold:.2f}")
    
    # threshold should be somewhere between 5% and 15% of the Max Distance
    # Example: if max_distance=141.42, threshold=14.14 (10%)
    
    N = T.shape[0]
    parent = list(range(N))
    
    def find_root(i):
        if parent[i] == i: return i
        parent[i] = find_root(parent[i])
        return parent[i]
        
    def union_sets(i, j):
        root_i = find_root(i)
        root_j = find_root(j)
        if root_i != root_j:
            parent[root_i] = root_j
            return True
        return False
        
    for i in range(N):
        for j in range(i + 1, N):
            if distance_matrix[i, j] < threshold:
                union_sets(i, j)
                
    groups = defaultdict(list)
    for i in range(N):
        root = find_root(i)
        groups[root].append(metadata[i])
        
    final_results = []
    group_counter = 0
    for root_id, members in groups.items():
        for member in members:
            final_results.append({
                "Group_ID": group_counter,
                "URL_Key": member['domain_key'],
                "Image_Filename": member['filename'],
            })
        group_counter += 1
        
    return final_results

def run_group_analysis():
    """ Orchestrates the data loading, PCA, grouping, and final report generation. """
    
    if not os.path.exists(INPUT_DIR):
        print(f"Error: Could not find image folder '{INPUT_DIR}'. Stopping.")
        return False

    X_data, metadata, skipped_logs = load_and_vectorize_images()
    
    if skipped_logs:
        try:
            df_skip = pd.DataFrame(skipped_logs)
            df_skip.to_csv(SKIP_REPORT_CSV, index=False, quoting=csv.QUOTE_NONNUMERIC)
            print(f"\nWarning! {len(skipped_logs)} files skipped. Details saved in: {SKIP_REPORT_CSV}")
        except: pass
    
    if X_data.size == 0:
        print("Fatal Error: Could not load valid images. Stopping.")
        return False

    print(f"\nTotal valid logos loaded: {X_data.shape[0]}")
    
    T_features = apply_pca_and_get_features(X_data)
    final_groups = group_by_threshold(T_features, SIMILARITY_THRESHOLD, metadata)
    
    df_results = pd.DataFrame(final_groups)
    
    total_grouped = df_results.shape[0]
    total_groups_found = df_results['Group_ID'].nunique()
    
    df_results.to_csv(OUTPUT_CSV, index=False, quoting=csv.QUOTE_NONNUMERIC)
    
    print("\n" + "="*50)
    print("SIMILARITY GROUPING COMPLETE!")
    print(f"Total logos processed (final): {total_grouped}")
    print(f"Total groups found: {total_groups_found}")
    print(f"Report saved to: {OUTPUT_CSV}")
    print("="*50)
    
    return True

if __name__ == '__main__':
    run_group_analysis()