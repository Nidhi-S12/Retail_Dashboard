#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Data Generator with Azure Integration
Generate synthetic data and save to Azure Blob Storage with local fallback
"""

import pandas as pd
import numpy as np
import json
import random
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.core.exceptions import AzureError
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from azure_integration.config import get_azure_config

# Set random seed for reproducibility
random.seed(42)
np.random.seed(42)

# Configuration
DAYS = 30
CONTAINER_NAME = "project-data"

def create_directory_if_not_exists(directory_path):
    """Create directory if it doesn't exist"""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"Created directory: {directory_path}")

def save_to_blob_storage(data: Dict, blob_name: str) -> bool:
    """
    Save data to Azure Blob Storage with local fallback
    
    Args:
        data: Dictionary containing data to save
        blob_name: Name of the blob to save to
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        config = get_azure_config()
        blob_config = config.get_blob_storage_config()
        
        if not blob_config["connection_string"]:
            raise Exception("No Azure Blob Storage connection string available")
        
        # Initialize blob service client
        blob_service_client = BlobServiceClient.from_connection_string(blob_config["connection_string"])
        
        # Create container if it doesn't exist
        try:
            container_client = blob_service_client.create_container(CONTAINER_NAME)
            print(f"✓ Created container: {CONTAINER_NAME}")
        except Exception:
            # Container might already exist
            container_client = blob_service_client.get_container_client(CONTAINER_NAME)
        
        # Convert data to JSON string
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        
        # Upload to blob
        blob_client = blob_service_client.get_blob_client(
            container=CONTAINER_NAME, 
            blob=blob_name
        )
        
        blob_client.upload_blob(json_data, overwrite=True)
        print(f"✓ Data saved to Azure Blob Storage: {blob_name}")
        
        # Also save locally as backup
        local_fallback_save(data, blob_name)
        
        return True
        
    except Exception as e:
        print(f"✗ Azure Blob Storage save failed: {e}")
        print("Falling back to local storage...")
        return local_fallback_save(data, blob_name)

def get_latest_data(blob_name: str) -> Optional[Dict]:
    """
    Retrieve data from Azure Blob Storage with local fallback
    
    Args:
        blob_name: Name of the blob to retrieve
        
    Returns:
        Dict: Retrieved data or None if not found
    """
    try:
        config = get_azure_config()
        blob_config = config.get_blob_storage_config()
        
        if not blob_config["connection_string"]:
            raise Exception("No Azure Blob Storage connection string available")
        
        # Initialize blob service client
        blob_service_client = BlobServiceClient.from_connection_string(blob_config["connection_string"])
        
        # Get blob client
        blob_client = blob_service_client.get_blob_client(
            container=CONTAINER_NAME, 
            blob=blob_name
        )
        
        # Download blob content
        blob_data = blob_client.download_blob().readall()
        data = json.loads(blob_data.decode('utf-8'))
        
        print(f"✓ Data retrieved from Azure Blob Storage: {blob_name}")
        return data
        
    except Exception as e:
        print(f"✗ Azure Blob Storage retrieval failed: {e}")
        print("Falling back to local storage...")
        return local_fallback_load(blob_name)

def local_fallback_save(data: Dict, filename: str) -> bool:
    """
    Save data to local storage as fallback
    
    Args:
        data: Dictionary containing data to save
        filename: Name of the file to save to
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        create_directory_if_not_exists("data")
        
        # Remove .json extension if present and add it back
        if filename.endswith('.json'):
            filename = filename[:-5]
        
        filepath = os.path.join("data", f"{filename}.json")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Data saved to local storage: {filepath}")
        return True
        
    except Exception as e:
        print(f"✗ Local storage save failed: {e}")
        return False

def local_fallback_load(filename: str) -> Optional[Dict]:
    """
    Load data from local storage as fallback
    
    Args:
        filename: Name of the file to load from
        
    Returns:
        Dict: Retrieved data or None if not found
    """
    try:
        # Remove .json extension if present and add it back
        if filename.endswith('.json'):
            filename = filename[:-5]
        
        filepath = os.path.join("data", f"{filename}.json")
        
        if not os.path.exists(filepath):
            print(f"✗ Local file not found: {filepath}")
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✓ Data loaded from local storage: {filepath}")
        return data
        
    except Exception as e:
        print(f"✗ Local storage load failed: {e}")
        return None

def azure_sentiment_analysis(texts: List[str]) -> List[Tuple[str, float]]:
    """
    Perform sentiment analysis using Azure Text Analytics
    
    Args:
        texts: List of texts to analyze
        
    Returns:
        List of tuples (sentiment_label, confidence_score)
    """
    try:
        config = get_azure_config()
        text_config = config.get_text_analytics_config()
        
        if not text_config["key"] or not text_config["endpoint"]:
            raise Exception("Azure Text Analytics credentials not available")
        
        # Initialize client
        client = TextAnalyticsClient(
            endpoint=text_config["endpoint"],
            credential=AzureKeyCredential(text_config["key"])
        )
        
        # Process in batches of 10
        batch_size = 10
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            try:
                response = client.analyze_sentiment(documents=batch)
                
                for doc in response:
                    if not doc.is_error:
                        sentiment = doc.sentiment
                        confidence = doc.confidence_scores.__dict__[sentiment]
                        results.append((sentiment, confidence))
                    else:
                        # Fallback for failed individual documents
                        results.append(fallback_sentiment_analysis(batch[0]))
                        
            except Exception as e:
                print(f"✗ Batch sentiment analysis failed: {e}")
                # Fallback for entire batch
                for text in batch:
                    results.append(fallback_sentiment_analysis(text))
        
        print(f"✓ Azure sentiment analysis completed for {len(texts)} texts")
        return results
        
    except Exception as e:
        print(f"✗ Azure sentiment analysis failed: {e}")
        print("Falling back to local sentiment analysis...")
        return [fallback_sentiment_analysis(text) for text in texts]

def fallback_sentiment_analysis(text: str) -> Tuple[str, float]:
    """
    Fallback sentiment analysis using keyword matching
    
    Args:
        text: Text to analyze
        
    Returns:
        Tuple of (sentiment_label, confidence_score)
    """
    positive_words = ["love", "amazing", "great", "best", "perfect", "happy", "excellent", "awesome", "obsessed", "stunning"]
    negative_words = ["disappointed", "bad", "waste", "poor", "regret", "broke", "terrible", "avoid", "overpriced", "letdown"]
    
    text_lower = text.lower()
    positive_score = sum(1.5 if word in text_lower else 0 for word in positive_words)
    negative_score = sum(1.5 if word in text_lower else 0 for word in negative_words)
    
    if positive_score > negative_score:
        return ("positive", 0.75 + random.uniform(-0.1, 0.1))
    elif negative_score > positive_score:
        return ("negative", 0.75 + random.uniform(-0.1, 0.1))
    else:
        return ("neutral", 0.65 + random.uniform(-0.05, 0.05))

def generate_synthetic_data() -> Dict:
    """
    Generate synthetic retail trends data
    
    Returns:
        Dict: Generated data structure
    """
    # Load configurations
    script_dir = os.path.dirname(__file__)
    config_dir = os.path.join(script_dir, 'config')
    
    with open(os.path.join(config_dir, 'regions.json'), 'r') as f:
        regions = json.load(f)
    
    with open(os.path.join(config_dir, 'products.json'), 'r') as f:
        products_config = json.load(f)
    
    with open(os.path.join(config_dir, 'festivals.json'), 'r') as f:
        festivals = json.load(f)
    
    # Generate sample data
    all_data = []
    product_id = 1
    
    # Date range for data generation
    end_date = datetime.now()
    start_date = end_date - timedelta(days=DAYS)
    
    # Sample texts for sentiment analysis
    sample_texts = [
        "This product is amazing! Love it so much!",
        "Not impressed with the quality, disappointed.",
        "It's okay, nothing special but does the job.",
        "Absolutely love this purchase! Highly recommend!",
        "Terrible quality, waste of money.",
        "Great product, perfect for daily use.",
        "Average product, could be better.",
        "Excellent quality and fast delivery!",
        "Poor packaging, product was damaged.",
        "Really happy with this purchase!"
    ]
    
    print("Performing sentiment analysis on sample texts...")
    sentiments = azure_sentiment_analysis(sample_texts)
    
    # Generate data for each product and region
    for category, products in products_config['product_categories'].items():
        sample_products = random.sample(products, min(5, len(products)))
        
        for product in sample_products:
            for region_type, region_list in regions.items():
                sample_regions = random.sample(region_list, min(3, len(region_list)))
                
                for region in sample_regions:
                    # Generate mentions and sentiment data
                    total_mentions = random.randint(50, 500)
                    
                    # Use pre-analyzed sentiments
                    sentiment_data = random.choice(sentiments)
                    
                    # Generate product entry
                    product_data = {
                        "id": product_id,
                        "name": product["name"],
                        "category": category,
                        "region": region,
                        "region_type": region_type,
                        "total_mentions": total_mentions,
                        "sentiment_counts": {
                            "positive": int(total_mentions * 0.6),
                            "neutral": int(total_mentions * 0.25),
                            "negative": int(total_mentions * 0.15)
                        },
                        "sentiment_percentages": {
                            "positive": 60.0,
                            "neutral": 25.0,
                            "negative": 15.0
                        },
                        "trending_score": random.uniform(0.5, 1.0),
                        "is_trending": random.choice([True, False]),
                        "recommendation": "Standard Stock Levels",
                        "recommendation_details": "Average demand patterns observed.",
                        "marketing_recommendation": "Standard promotion strategy recommended.",
                        "demographics": {
                            "age_groups": {
                                "18-24": random.randint(10, 30),
                                "25-34": random.randint(20, 40),
                                "35-44": random.randint(15, 35),
                                "45-54": random.randint(10, 25),
                                "55+": random.randint(5, 15)
                            },
                            "gender": {
                                "male": random.randint(40, 60),
                                "female": random.randint(40, 60)
                            }
                        },
                        "tags": product["tags"],
                        "sample_posts": sample_texts[:3],
                        "daily_stats": [
                            {
                                "date": (start_date + timedelta(days=i)).strftime("%Y-%m-%d"),
                                "mentions": random.randint(1, 20)
                            }
                            for i in range(DAYS)
                        ]
                    }
                    
                    all_data.append(product_data)
                    product_id += 1
    
    return all_data

def main():
    """Main function to generate and save data"""
    try:
        print("Starting data generation with Azure integration...")
        
        # Validate Azure services
        config = get_azure_config()
        validation_results = config.validate_azure_services()
        
        print("\n=== Azure Services Status ===")
        for service, is_valid in validation_results.items():
            status = "✓ Available" if is_valid else "✗ Unavailable"
            print(f"{service}: {status}")
        
        # Generate synthetic data
        print("\nGenerating synthetic data...")
        data = generate_synthetic_data()
        
        # Save to Azure Blob Storage (with local fallback)
        print(f"\nSaving {len(data)} records...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        blob_name = f"retail_trends_data_{timestamp}.json"
        
        success = save_to_blob_storage(data, blob_name)
        
        # Also save as the main data file
        save_to_blob_storage(data, "retail_trends_data.json")
        
        if success:
            print(f"✓ Data generation completed successfully!")
            print(f"Records generated: {len(data)}")
            print(f"Blob name: {blob_name}")
        else:
            print("⚠ Data generation completed with fallback to local storage")
            
    except Exception as e:
        print(f"✗ Data generation failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
