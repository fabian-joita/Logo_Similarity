# 🤖 Logo Extractor & Vector Similarity Grouping Pipeline

## Project: Numerical Analysis & Web Scraping
### Author: Joița Fabian-Gabriel

I developed a robust pipeline for **Advanced Numerical Analysis** and **Web Scraping**, designed to automatically extract thousands of logos and group them based on **visual similarity** using **PCA** (Principal Component Analysis) and **Graph Theory**.

***

## 💡 Core Objective: Vector Simplification for Rapid Comparison

I started with the premise of creating a system capable of comparing logos quickly and efficiently. I concluded that the optimal solution was to create a **vectorial difference** between the most important components of each logo.

I implemented a **Dimensionality Reduction process using PCA** to create an essential "fingerprint" of just **$50$ numbers** (score vectors) per logo, transforming a slow $10,000$-dimensional comparison into a near-instantaneous one.

---

## Phase 1 & 2: Hybrid Extraction and Standardization

### 🚀 Extraction (The Anti-Bot Layer)

I implemented a *failover strategy* to achieve a success rate of $\mathbf{98.88\%}$:

1.  **Fast Method (`requests`):** I attempt a simple HTTP request.
2.  **Robust Method (Playwright):** If the fast method fails, I launch a real browser (Chromium, using `headless=False` for anti-bot measures) with an advanced **Scoring System**. This system assigns scores to the visual elements found and prioritizes: **high position** (in the `header`), **reasonable size**, and **match with the brand name** extracted from the URL.

### 📐 Data Standardization (Cleaning)

I standardized all logos to be **perfectly uniform**, which is essential for PCA:

* **SVG $\to$ PNG Conversion:** I rasterized vector logos (SVG) into pixels because **PCA only works with pixel matrices.**
* **Contrast Normalization:** I detected white logos and inverted them onto a black background, resulting in a **"Signal-on-Zero"** format (visible shape on a zero background).
* **Uniform Padding:** I framed all images within a **$100 \times 100$ pixel** canvas, ensuring every logo has exactly $10,000$ input dimensions.

---

## Phase 3: Numerical Analysis and Grouping

### 3.1. Feature Extraction (PCA - "Eigenlogos")

I used PCA to compress the $10,000$ dimensions of information into a short vector of $k=50$ numbers:

$$\mathbf{X} \in \mathbb{R}^{3378 \times 10000} \xrightarrow{\text{PCA}} \mathbf{T} \in \mathbb{R}^{3378 \times 50}$$

* **Result:** The Score Matrix $\mathbf{T}$, where each row is the **50-number mathematical fingerprint** of the logo's structure.

### 3.2. Deterministic Grouping (Union-Find)

I applied a method based on **Graph Theory** to find groups based on a strict neighborhood rule, avoiding K-Means:

* **Similarity Measurement:** I calculated the **Euclidean Distance** between all 50-score vectors.
    $$\text{Dist}(\mathbf{T}_i, \mathbf{T}_j) = \sqrt{\sum_{k=1}^{50} (T_{ik} - T_{jk})^2}$$
* **Threshold ($\epsilon$):** I established a strict threshold. If $\text{Dist} < \epsilon$, I drew an edge (link) between the logos.
* **Connected Components (Union-Find):** The algorithm identifies all logos that are linked (directly or indirectly) and places them into the same **Connected Component (Group\_ID)**.

---

## 🎉 Results and Conclusion

I achieved an extraction rate of $\mathbf{98.88\%}$ and generated a complete grouping report.

**Model Calibration Capability**
By adjusting the numerical parameters, I can fine-tune the grouping granularity:

* **`SIMILARITY_THRESHOLD`** ($\epsilon$): By increasing the threshold, I get **fewer, but larger** groups (high tolerance).
* **`PCA_COMPONENTS`** ($k$): By modifying the number of components retained, I control how coarse or detailed the shape analysis is.

I have attached **two grouped data sets** in this GitHub repo to show the difference: one with a strict threshold (resulting in many unique groups) and one with a relaxed threshold, demonstrating that by changing `SIMILARITY_THRESHOLD` and optionally `PCA_COMPONENTS`, **I can obtain more or fewer categories based on the user's desire.**
