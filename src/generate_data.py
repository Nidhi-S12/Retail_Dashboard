#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Synthetic Data Generator for Indian Retail Trends Dashboard
This script generates realistic synthetic social media data for retail products in India,
with dynamic data sources, refined trending logic, and varied sentiment analysis.
"""

import pandas as pd
import numpy as np
import json
import random
import os
from faker import Faker
from datetime import datetime, timedelta
from tqdm import tqdm
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer

# Set random seed for reproducibility
random.seed(42)
np.random.seed(42)
faker = Faker('en_IN')  # Use Indian locale for Faker

# Define fixed parameters
DAYS = 30  # Number of days of data to generate
MAX_TRENDING_PER_REGION = 0.1  # Max 10% of products can trend per region
GLOBAL_TRENDING_CAP = 0.05  # Max 5% of products can trend globally

def create_directory_if_not_exists(directory_path):
    """Create directory if it doesn't exist"""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

# Load external configurations
script_dir = os.path.dirname(__file__)
config_dir = os.path.abspath(os.path.join(script_dir, '..', 'config'))

# Load regions
with open(os.path.join(config_dir, 'regions.json'), 'r') as f:
    regions = json.load(f)
all_regions = [city for cities in regions.values() for city in cities]

# Load products and additional products
with open(os.path.join(config_dir, 'products.json'), 'r') as f:
    pconf = json.load(f)
product_categories = pconf['product_categories']
additional_products = pconf['additional_products']
for category, items in additional_products.items():
    product_categories[category].extend(items)

# Load festivals
with open(os.path.join(config_dir, 'festivals.json'), 'r') as f:
    festivals = json.load(f)

# Age groups for demographic insights
age_groups = ["18-24", "25-34", "35-44", "45-54", "55+"]

# Enhanced sentiment phrases with more variety and context
sentiment_phrases = {
    "positive": [
        "Just bought a {product} and it's a game-changer! {hashtag}",
        "Obsessed with my new {product}! Perfect for {occasion}. {hashtag}",
        "Wow, the {product} is so worth it! Amazing quality! {hashtag}",
        "Loving how {product} fits into my {occasion} vibe! {hashtag}",
        "Can't get enough of my {product}, such a steal! {hashtag}",
        "This {product} is my new favorite for {occasion}! {hashtag}",
        "Shoutout to {product} for making my day! {hashtag}",
        "{product} is absolutely stunning, highly recommend! {hashtag}",
        "Super happy with my {product}, it’s a must-have! {hashtag}",
        "The {product} is pure perfection! {hashtag}"
    ],
    "neutral": [
        "Trying out the {product} today, seems decent so far. {hashtag}",
        "Got a {product}, it’s okay for {occasion}. {hashtag}",
        "The {product} is alright, still testing it out. {hashtag}",
        "Picked up a {product}, nothing extraordinary. {hashtag}",
        "Using {product} for {occasion}, it’s fine. {hashtag}",
        "My {product} arrived, looks like it’ll do the job. {hashtag}",
        "Not sure about {product} yet, need more time. {hashtag}",
        "The {product} is average, expected a bit more. {hashtag}",
        "Got the {product}, it’s functional but not wow. {hashtag}",
        "Exploring the {product}, seems standard. {hashtag}"
    ],
    "negative": [
        "Not impressed with {product}, feels overpriced. {hashtag}",
        "My {product} didn’t live up to the hype. {hashtag}",
        "Disappointed with the {product}, broke too soon. {hashtag}",
        "Wish I hadn’t bought the {product}, total letdown. {hashtag}",
        "The {product} quality is below par for {occasion}. {hashtag}",
        "{product} isn’t worth the price, sadly. {hashtag}",
        "Struggling with my {product}, not user-friendly. {hashtag}",
        "The {product} doesn’t match the description. {hashtag}",
        "Really upset with {product}, expected better. {hashtag}",
        "Returning my {product}, such a waste! {hashtag}"
    ]
}

def generate_hashtags(product, tags, sentiment, festival=None):
    """Generate realistic hashtags with festival context"""
    product_hashtags = [f"#{tag.capitalize()}" for tag in random.sample(tags, min(3, len(tags)))]
    product_name_parts = product.split()
    product_hashtags.append(f"#{''.join(part.capitalize() for part in product_name_parts)}")
    
    general_hashtags = [
        "#ShopIndia", "#IndianRetail", "#TrendyBuys", "#FestiveVibes",
        "#LocalLove", "#StyleIndia", "#NewIn", "#RetailTherapy",
        "#MadeForIndia", "#ShopSmart", "#InstaFinds", "#TrendyIndia"
    ]
    
    sentiment_hashtags = {
        "positive": ["#Obsessed", "#MustBuy", "#GameChanger", "#LoveIt", "#WowFactor"],
        "neutral": ["#FirstImpressions", "#TryingItOut", "#NewBuy", "#JustArrived"],
        "negative": ["#NotImpressed", "#Overrated", "#BuyerBeware", "#Disappointed"]
    }
    
    festival_hashtags = {
        "Diwali": ["#DiwaliVibes", "#FestivalOfLights", "#DiwaliShopping"],
        "Eid": ["#EidMubarak", "#EidCelebrations", "#EidGifts"],
        "Durga Puja": ["#PujoVibes", "#DurgaPuja", "#BengaliFest"],
        "Holi": ["#HoliHai", "#FestivalOfColors", "#HoliCelebration"],
        "Raksha Bandhan": ["#RakhiLove", "#SiblingBond", "#RakshaBandhan"],
        "Christmas": ["#MerryChristmas", "#WinterFest", "#ChristmasGifts"],
        "Ganesh Chaturthi": ["#GanpatiBappa", "#GaneshUtsav", "#MaharashtraFest"],
        "Onam": ["#OnamCelebration", "#KeralaFest", "#OnamVibes"]
    }
    
    all_hashtags = product_hashtags + random.sample(general_hashtags, 2)
    all_hashtags += random.sample(sentiment_hashtags[sentiment], 1)
    if festival and festival in festival_hashtags:
        all_hashtags += random.sample(festival_hashtags[festival], 2)
    
    random.shuffle(all_hashtags)
    return " ".join(all_hashtags[:6])  # Limit to 6 hashtags for realism

def generate_social_media_post(product, tags, sentiment, festival=None):
    """Generate a synthetic social media post with festival context"""
    post_template = random.choice(sentiment_phrases[sentiment])
    occasion = random.choice(["daily use", "festivals", "parties", "gifting", "home decor", "work", "celebrations"])
    if festival:
        occasion = festival
    hashtag = generate_hashtags(product, tags, sentiment, festival)
    
    # Add random emojis for realism
    emojis = {
        "positive": ["😍", "🔥", "✨", "👍", "💖"],
        "neutral": ["🤔", "😐", "👀", "🤷"],
        "negative": ["😞", "😣", "🙅", "👎", "😑"]
    }
    post_text = post_template.format(product=product, occasion=occasion, hashtag=hashtag)
    post_text += " " + "".join(random.sample(emojis[sentiment], random.randint(1, 3)))
    
    # Randomly vary post length
    if random.random() < 0.3:
        extra_text = random.choice([
            "Totally recommend checking this out!",
            "What do you guys think about this?",
            "Perfect for the season!",
            "Anyone else tried this yet?",
            "Really changed my vibe!"
        ])
        post_text = f"{post_text} {extra_text}"
    
    return post_text

def is_festival_season(date, festivals):
    """Check if a given date falls within any festival season"""
    month = date.month
    day = date.day
    
    for festival in festivals:
        festival_month = festival["month"]
        festival_start_day = max(1, 15 - festival["duration"] // 2)
        festival_end_day = min(30, 15 + festival["duration"] // 2)
        
        if month == festival_month and festival_start_day <= day <= festival_end_day:
            return True, festival["name"], festival["tags"]
    
    return False, None, None

def calculate_popularity_boost(date, product_category, product_name, tags, region):
    """Calculate realistic popularity boost with dynamic factors"""
    popularity = 1.0
    
    # Festival season boost
    is_festival, festival_name, festival_tags = is_festival_season(date, festivals)
    if is_festival:
        festival_boosts = {
            "Fashion": 2.0 if any(tag in festival_tags for tag in tags if tag in ["traditional", "ethnic", "festive"]) else 1.4,
            "Electronics": 1.6 if "gifts" in festival_tags else 1.2,
            "Home Decor": 2.2 if any(tag in festival_tags for tag in tags if tag in ["lights", "decoration", "traditional"]) else 1.5,
            "Beauty": 1.5 if "gift" in festival_tags else 1.3
        }
        popularity *= festival_boosts.get(product_category, 1.3)
    
    # Brand-specific boosts
    brand_boosts = {
        "iPhone": 1.5,
        "boAt": 1.3,
        "Forest Essentials": 1.4,
        "Lakmé": 1.2,
        "Samsung": 1.3,
        "Jaipur Rugs": 1.3
    }
    for brand, boost in brand_boosts.items():
        if brand.lower() in product_name.lower():
            popularity *= boost
    
    # Regional preferences with more variation
    regional_preferences = {
        "Delhi NCR": {"Fashion": 1.5, "Electronics": 1.4, "Home Decor": 1.2, "Beauty": 1.3},
        "Mumbai": {"Fashion": 1.6, "Electronics": 1.3, "Home Decor": 1.1, "Beauty": 1.4},
        "Bangalore": {"Fashion": 1.3, "Electronics": 1.6, "Home Decor": 1.2, "Beauty": 1.2},
        "Chennai": {"Fashion": 1.4, "Electronics": 1.2, "Home Decor": 1.3, "Beauty": 1.1},
        "Kolkata": {"Fashion": 1.5, "Electronics": 1.1, "Home Decor": 1.5, "Beauty": 1.2},
        "Hyderabad": {"Fashion": 1.4, "Electronics": 1.4, "Home Decor": 1.2, "Beauty": 1.3}
    }
    
    if region not in regional_preferences:
        if region in regions["Tier-1"]:
            regional_preferences[region] = {
                "Fashion": 1.3 + random.uniform(-0.15, 0.15),
                "Electronics": 1.2 + random.uniform(-0.15, 0.15),
                "Home Decor": 1.3 + random.uniform(-0.15, 0.15),
                "Beauty": 1.2 + random.uniform(-0.15, 0.15)
            }
        else:  # Tier-2
            regional_preferences[region] = {
                "Fashion": 1.1 + random.uniform(-0.2, 0.2),
                "Electronics": 1.0 + random.uniform(-0.2, 0.2),
                "Home Decor": 1.4 + random.uniform(-0.2, 0.2),
                "Beauty": 1.1 + random.uniform(-0.2, 0.2)
            }
    
    popularity *= regional_preferences.get(region, {}).get(product_category, 1.0)
    
    # Product-specific boosts based on tags
    if any(tag in ["luxury", "premium", "designer"] for tag in tags):
        popularity *= 1.3
    elif any(tag in ["affordable", "value-for-money"] for tag in tags):
        popularity *= 1.1
    
    # Random fluctuation for natural variability
    popularity *= random.uniform(0.7, 1.3)
    
    return min(max(popularity, 0.5), 3.0)  # Cap popularity to avoid extreme values

def get_sentiment_model():
    """Load the sentiment analysis model from Hugging Face"""
    try:
        model_name = "nlptown/bert-base-multilingual-uncased-sentiment"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        sentiment_analyzer = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)
        return sentiment_analyzer
    except Exception as e:
        print(f"Error loading sentiment model: {e}")
        print("Using fallback method for sentiment analysis...")
        return None

def analyze_sentiment(text, sentiment_analyzer=None):
    """Analyze sentiment with improved fallback"""
    if sentiment_analyzer:
        try:
            result = sentiment_analyzer(text)
            score = result[0]['score']
            label = result[0]['label']
            if '1' in label or '2' in label:
                return "negative", score
            elif '3' in label:
                return "neutral", score
            else:
                return "positive", score
        except Exception as e:
            print(f"Error in sentiment analysis: {e}")
            return fallback_sentiment_analysis(text)
    else:
        return fallback_sentiment_analysis(text)

def fallback_sentiment_analysis(text):
    """Enhanced fallback sentiment analysis with keyword weighting"""
    positive_words = ["love", "amazing", "great", "best", "perfect", "happy", "excellent", "awesome", "obsessed", "stunning"]
    negative_words = ["disappointed", "bad", "waste", "poor", "regret", "broke", "terrible", "avoid", "overpriced", "letdown"]
    
    text_lower = text.lower()
    positive_score = sum(1.5 if word in text_lower else 0 for word in positive_words)
    negative_score = sum(1.5 if word in text_lower else 0 for word in negative_words)
    
    if positive_score > negative_score:
        return "positive", 0.75 + random.uniform(-0.1, 0.1)
    elif negative_score > positive_score:
        return "negative", 0.75 + random.uniform(-0.1, 0.1)
    else:
        return "neutral", 0.65 + random.uniform(-0.05, 0.05)

def generate_demographics(region):
    """Generate realistic demographic insights"""
    if region in regions["Metro"]:
        age_distribution = {"18-24": 0.35, "25-34": 0.3, "35-44": 0.2, "45-54": 0.1, "55+": 0.05}
    elif region in regions["Tier-1"]:
        age_distribution = {"18-24": 0.25, "25-34": 0.35, "35-44": 0.25, "45-54": 0.1, "55+": 0.05}
    else:
        age_distribution = {"18-24": 0.2, "25-34": 0.3, "35-44": 0.3, "45-54": 0.15, "55+": 0.05}
    
    for age_group in age_distribution:
        age_distribution[age_group] += random.uniform(-0.1, 0.1)
        age_distribution[age_group] = max(0.05, min(0.5, age_distribution[age_group]))
    
    total = sum(age_distribution.values())
    for age_group in age_distribution:
        age_distribution[age_group] /= total
    
    gender_distribution = {"male": random.uniform(0.45, 0.55), "female": 0.0}
    gender_distribution["female"] = 1 - gender_distribution["male"]
    
    return {
        "age_groups": age_distribution,
        "gender": gender_distribution
    }

def generate_product_data(sentiment_analyzer=None):
    """Generate synthetic data with enhanced realism"""
    all_data = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=DAYS)
    date_range = [start_date + timedelta(days=i) for i in range(DAYS + 1)]
    
    product_id = 1
    for category, products in product_categories.items():
        sample_size = int(len(products) * random.uniform(0.8, 1.0))  # Randomly select 80-100% of products
        category_products = random.sample(products, sample_size)
        for product_info in category_products:
            product_name = product_info['name']
            product_tags = product_info['tags']
            
            for region in all_regions:
                spike_dates = random.sample(date_range, k=random.randint(1, 3))
                sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
                posts = []
                daily_stats = []
                
                for date in date_range:
                    is_festival, festival_name, festival_tags = is_festival_season(date, festivals)
                    popularity = calculate_popularity_boost(date, category, product_name, product_tags, region)
                    weekly_factor = 1 + 0.4 * np.sin(2 * np.pi * date.weekday() / 7)
                    popularity *= weekly_factor
                    if date in spike_dates:
                        popularity *= random.uniform(1.8, 3.5)
                    
                    # Adjust mentions based on region type
                    region_factor = 1.2 if region in regions["Metro"] else 1.0 if region in regions["Tier-1"] else 0.8
                    lam = max(1, popularity * region_factor * random.uniform(1.5, 3.0))
                    daily_mentions = int(np.random.poisson(lam))
                    daily_stats.append({"date": date.strftime("%Y-%m-%d"), "mentions": daily_mentions})
                    
                    # Dynamic sentiment bias based on product tags
                    sentiment_bias = {
                        "positive": 0.65,
                        "neutral": 0.25,
                        "negative": 0.1
                    }
                    if any(tag in ["luxury", "premium", "designer"] for tag in product_tags):
                        sentiment_bias["positive"] += 0.1
                        sentiment_bias["neutral"] -= 0.05
                        sentiment_bias["negative"] -= 0.05
                    elif any(tag in ["affordable", "value-for-money"] for tag in product_tags):
                        sentiment_bias["neutral"] += 0.1
                        sentiment_bias["positive"] -= 0.05
                        sentiment_bias["negative"] -= 0.05
                    if is_festival and any(tag in festival_tags for tag in product_tags):
                        sentiment_bias["positive"] += 0.1
                        sentiment_bias["neutral"] -= 0.05
                        sentiment_bias["negative"] -= 0.05
                    
                    for _ in range(daily_mentions):
                        sentiment = random.choices(
                            list(sentiment_bias.keys()),
                            weights=list(sentiment_bias.values()),
                            k=1
                        )[0]
                        post_text = generate_social_media_post(product_name, product_tags, sentiment, festival_name)
                        analyzed_sentiment, sentiment_score = analyze_sentiment(post_text, sentiment_analyzer)
                        sentiment_counts[analyzed_sentiment] += 1
                        posts.append({
                            "text": post_text,
                            "date": date.strftime("%Y-%m-%d"),
                            "sentiment": analyzed_sentiment,
                            "sentiment_score": float(sentiment_score)
                        })
                
                total_mentions = sum(sentiment_counts.values())
                sentiment_percentages = {
                    sentiment: count / total_mentions * 100 if total_mentions > 0 else 0
                    for sentiment, count in sentiment_counts.items()
                }
                
                demographics = generate_demographics(region)
                
                # Enhanced trending score
                trending_score = (
                    (sentiment_counts["positive"] * 1.8 +
                     sentiment_counts["neutral"] * 0.4 -
                     sentiment_counts["negative"] * 1.2) /
                    max(1, total_mentions)
                ) * total_mentions / 8
                trending_score = max(0, trending_score * random.uniform(0.8, 1.2))
                
                product_data = {
                    "id": product_id,
                    "name": product_name,
                    "category": category,
                    "region": region,
                    "region_type": next((rt for rt, cities in regions.items() if region in cities), "Other"),
                    "total_mentions": total_mentions,
                    "sentiment_counts": sentiment_counts,
                    "sentiment_percentages": sentiment_percentages,
                    "trending_score": trending_score,
                    "is_trending": False,  # Will be updated later
                    "recommendation": "Pending",
                    "recommendation_details": "Pending",
                    "marketing_recommendation": "Pending",
                    "demographics": demographics,
                    "sample_posts": posts[:5],
                    "daily_stats": daily_stats,
                    "tags": product_tags
                }
                
                all_data.append(product_data)
                product_id += 1
    
    # Apply trending logic
    grouped = {}
    for item in all_data:
        key = (item['region'], item['category'])
        grouped.setdefault(key, []).append(item)
    
    for (region, category), items in grouped.items():
        num_trending = max(1, int(len(items) * MAX_TRENDING_PER_REGION))
        sorted_items = sorted(items, key=lambda x: x['trending_score'], reverse=True)
        trending_ids = {it['id'] for it in sorted_items[:num_trending]}
        for it in items:
            it['is_trending'] = it['id'] in trending_ids
            if it['is_trending'] and it['sentiment_percentages']['positive'] > 65:
                it['recommendation'] = "High Demand - Increase Stock"
                it['recommendation_details'] = f"Trending with {it['sentiment_percentages']['positive']:.1f}% positive sentiment. Increase inventory by 30-50%."
                top_hashtags = list(set([tag for post in it['sample_posts'] for tag in post['text'].split() if tag.startswith('#')]))
                top_age_group = max(it['demographics']['age_groups'].items(), key=lambda x: x[1])[0]
                it['marketing_recommendation'] = f"Promote heavily with {', '.join(top_hashtags[:3] if top_hashtags else ['#TrendingNow'])} targeting {top_age_group} age group"
            elif it['is_trending'] and it['sentiment_percentages']['positive'] > 45:
                it['recommendation'] = "Moderate Demand - Maintain Stock"
                it['recommendation_details'] = f"Steady popularity with {it['sentiment_percentages']['positive']:.1f}% positive sentiment. Maintain current inventory."
                it['marketing_recommendation'] = "Moderate promotion focusing on product features"
            elif it['sentiment_percentages']['negative'] > 35:
                it['recommendation'] = "Caution - Monitor Feedback"
                it['recommendation_details'] = f"High negative sentiment ({it['sentiment_percentages']['negative']:.1f}%). Address customer concerns."
                it['marketing_recommendation'] = "Focus on improving product perception"
            else:
                it['recommendation'] = "Standard Stock Levels"
                it['recommendation_details'] = "Average demand. Maintain standard inventory."
                it['marketing_recommendation'] = "Standard promotion with customer testimonials"
    
    # Cap global trending
    global_count = max(1, int(len(all_data) * GLOBAL_TRENDING_CAP))
    top_global = sorted(all_data, key=lambda x: x['trending_score'], reverse=True)[:global_count]
    global_ids = {it['id'] for it in top_global}
    for item in all_data:
        if item['id'] in global_ids:
            item['is_trending'] = True
            if item['sentiment_percentages']['positive'] > 65:
                item['recommendation'] = "High Demand - Increase Stock"
                item['recommendation_details'] = f"Global trending with {item['sentiment_percentages']['positive']:.1f}% positive sentiment. Increase inventory by 30-50%."
    
    return all_data

def main():
    print("Loading sentiment analysis model...")
    sentiment_analyzer = get_sentiment_model()
    
    print("Generating synthetic data...")
    data = generate_product_data(sentiment_analyzer)
    
    create_directory_if_not_exists("data")
    
    output_file = "data/retail_trends_data.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Data generation complete. Generated {len(data)} product-region entries.")
    print(f"Data saved to {output_file}")

if __name__ == "__main__":
    main()