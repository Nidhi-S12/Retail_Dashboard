# Indian Retail Trends Dashboard

A proof of concept (PoC) for a web-based dashboard tailored for Indian retailers to identify trending retail products in their specific region by analyzing social media data and providing actionable inventory and marketing recommendations.

## Overview

This dashboard is inspired by Zomato's Food Trends platform but focused on retail products relevant to the Indian market. It provides retailers with insights on trending products based on synthetic social media data, helping them make informed decisions about inventory management and marketing strategies.

## Features

- **Region-Based Filtering**: Select specific regions (e.g., Delhi, Mumbai, Tier-2 cities) to view trends relevant to your location.
- **Product Category Filtering**: Filter by product categories like Fashion, Electronics, Beauty, and Home Decor.
- **Sentiment Analysis**: View sentiment breakdown (positive, neutral, negative) for each product.
- **Trending Products**: Identify which products are currently trending in your selected region.
- **Actionable Recommendations**: Get inventory and marketing recommendations for each product.
- **Demographic Insights**: Understand which age groups and demographics are interested in specific products.
- **Sample Social Media Posts**: View sample posts to understand customer opinions and language.

## Project Structure

```
.
├── data/
│   └── retail_trends_data.json     # Generated synthetic data
├── src/
│   ├── generate_data.py            # Python script to generate synthetic data
│   └── app.py                      # Flask server to serve the dashboard
├── index.html                      # Main dashboard HTML/React application
└── requirements.txt                # Python dependencies
```

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. Clone or download this repository.

2. Install the required Python packages:

```bash
pip install -r requirements.txt
```

3. Generate the synthetic data:

```bash
python src/generate_data.py
```

4. Start the Flask server:

```bash
python src/app.py
```

5. Open your browser and navigate to `http://localhost:5000` to view the dashboard.

## Technical Details

### Data Generation

The synthetic data is generated using Python and includes:
- Product information for various categories (Fashion, Electronics, Home Decor, Beauty)
- Regional data for different Indian cities
- Sentiment analysis using Hugging Face transformers
- Demographic insights based on region and product
- Sample social media posts with hashtags

### Dashboard

The dashboard is built using:
- React (loaded via CDN)
- Tailwind CSS for styling
- Chart.js for data visualization

## Use Cases

1. **Inventory Management**: Use the dashboard to identify trending products in your region and adjust inventory levels accordingly.
2. **Marketing Strategy**: Get insights on which hashtags and demographics to target for specific products.
3. **Regional Insights**: Understand how product trends vary across different regions in India.
4. **Sentiment Analysis**: Gauge customer satisfaction and identify products with negative sentiment that might need attention.

## Assumptions

- The PoC uses synthetic data instead of real social media APIs.
- The dashboard focuses on major Indian regions and popular product categories.
- Sentiment analysis is performed using Hugging Face transformers on synthetic posts.
- The UI/UX is inspired by Zomato Trends but simplified for the PoC scope.

## Acknowledgements

This project is a proof of concept created for demonstration purposes. All data is synthetic and generated for illustrative purposes only.
