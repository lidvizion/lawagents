# Tool Scoring Methodology

How we score and compare legal technology tools. Designed for sync from external sources (G2, Capterra, etc.) and eventual database storage.

---

## Score Components

| Component | Weight | Source | Description |
|-----------|--------|--------|--------------|
| **Numeric rating** | 40% | G2, Capterra, SoftwareReviews | Star rating normalized to 0–10 |
| **Sentiment** | 25% | Review text analysis | Positive / neutral / negative |
| **Review count** | 15% | Platform | More reviews = higher confidence |
| **Recency** | 10% | Review date | Prefer reviews from last 12 months |
| **Feature fit** | 10% | Manual / practice area mapping | Fit for target use case |

---

## Normalization Rules

### Numeric Rating (0–10)

| Source | Original Scale | Formula |
|--------|----------------|---------|
| G2 | 1–5 stars | `(stars - 1) * 2.5` |
| Capterra | 1–5 stars | `(stars - 1) * 2.5` |
| SoftwareReviews | 0–10 | Use as-is |
| TrustRadius | 1–10 | Use as-is |

**Example:** G2 4.6/5 → (4.6 - 1) × 2.5 = **9.0**

### Sentiment Score (0–10)

| Sentiment | Score | Criteria |
|-----------|-------|----------|
| Positive | 8–10 | Majority positive; "recommend," "easy," "saves time" |
| Neutral | 5–7 | Mixed; no strong recommendation |
| Negative | 0–4 | Complaints; "glitchy," "poor support," "abandoned migration" |

**Sources:** Review text from G2, Capterra, Reddit, vendor support forums.

### Review Count (0–10)

| Count | Score |
|-------|-------|
| 500+ | 10 |
| 200–499 | 8 |
| 50–199 | 6 |
| 10–49 | 4 |
| 1–9 | 2 |
| 0 | 0 |

### Recency (0–10)

| % Reviews in Last 12 Months | Score |
|----------------------------|-------|
| 80%+ | 10 |
| 50–79% | 7 |
| 25–49% | 4 |
| <25% | 2 |

### Feature Fit (0–10)

Manual or rule-based. Does the tool fit the target use case?

| Practice Area / Use Case | Fit Criteria |
|--------------------------|--------------|
| General practice management | Broad feature set |
| PI-specific | SOL tracking, lien tracking, medical chronology |
| Transactional | Checklists, document assembly, closing books |
| E-discovery | Doc review, production, privilege |
| Solo / small firm | Price, ease of use, support |

---

## Composite Score

```
Composite = (Rating × 0.40) + (Sentiment × 0.25) + (ReviewCount × 0.15) + (Recency × 0.10) + (FeatureFit × 0.10)
```

**Output:** 0–10 scale. Higher = better.

---

## Confidence Level

| Review Count | Confidence |
|--------------|------------|
| 100+ | High |
| 20–99 | Medium |
| 1–19 | Low |
| 0 | No score |

---

## Sync Data to Capture

For each tool, capture from sync sources:

| Field | Source | Example |
|-------|--------|---------|
| `rating` | G2, Capterra | 4.6 |
| `rating_scale` | Platform | 5 |
| `review_count` | Platform | 641 |
| `nps` | Capterra, SoftwareReviews | 9.1 |
| `sentiment_summary` | Review text | "Mostly positive; pricing concerns" |
| `last_synced` | Internal | 2025-03-03 |
| `sync_url` | This doc | https://www.g2.com/products/clio/reviews |

---

## Reddit / Community Sentiment

For tools with limited formal reviews, use:

- **r/LawFirm**, **r/Lawyertalk**, **r/paralegal** — Search tool name
- **Sentiment:** Positive / Mixed / Negative
- **Common themes:** Document in catalog file under "Community feedback"

---

## When to Re-Score

- **Quarterly:** Pull latest from G2, Capterra, SoftwareReviews
- **On major release:** Vendor announces major update
- **On incident:** Widespread outage or negative news
