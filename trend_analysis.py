#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trend Analysis Module with Azure Integration
Retrieve data from Azure Blob Storage and perform trend analysis
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_data import get_latest_data, azure_sentiment_analysis, fallback_sentiment_analysis
from azure_integration.config import get_azure_config

def get_latest_trends_data(blob_name: str = "retail_trends_data.json") -> Optional[List[Dict]]:
    """
    Retrieve the latest trends data from Azure Blob Storage
    
    Args:
        blob_name: Name of the blob containing trends data
        
    Returns:
        List of trend data records or None if not found
    """
    try:
        data = get_latest_data(blob_name)
        if data:
            print(f"✓ Retrieved {len(data)} trend records")
            return data
        else:
            print("✗ No trend data found")
            return None
            
    except Exception as e:
        print(f"✗ Error retrieving trends data: {e}")
        return None

def calculate_sentiment_scores(data: List[Dict]) -> Dict[str, float]:
    """
    Calculate aggregated sentiment scores from trend data
    
    Args:
        data: List of trend data records
        
    Returns:
        Dictionary containing sentiment metrics
    """
    try:
        if not data:
            return {}
        
        total_positive = sum(item.get('sentiment_counts', {}).get('positive', 0) for item in data)
        total_neutral = sum(item.get('sentiment_counts', {}).get('neutral', 0) for item in data)
        total_negative = sum(item.get('sentiment_counts', {}).get('negative', 0) for item in data)
        total_mentions = total_positive + total_neutral + total_negative
        
        if total_mentions == 0:
            return {
                'overall_sentiment_score': 0.0,
                'positive_percentage': 0.0,
                'neutral_percentage': 0.0,
                'negative_percentage': 0.0,
                'total_mentions': 0
            }
        
        # Calculate sentiment score (-1 to 1 scale)
        sentiment_score = (total_positive - total_negative) / total_mentions
        
        return {
            'overall_sentiment_score': sentiment_score,
            'positive_percentage': (total_positive / total_mentions) * 100,
            'neutral_percentage': (total_neutral / total_mentions) * 100,
            'negative_percentage': (total_negative / total_mentions) * 100,
            'total_mentions': total_mentions
        }
        
    except Exception as e:
        print(f"✗ Error calculating sentiment scores: {e}")
        return {}

def analyze_trending_products(data: List[Dict], region: str = None, category: str = None) -> List[Dict]:
    """
    Analyze trending products with optional filtering
    
    Args:
        data: List of trend data records
        region: Optional region filter
        category: Optional category filter
        
    Returns:
        List of trending products with analysis
    """
    try:
        if not data:
            return []
        
        # Filter data if needed
        filtered_data = data
        if region:
            filtered_data = [item for item in filtered_data if item.get('region') == region]
        if category:
            filtered_data = [item for item in filtered_data if item.get('category') == category]
        
        # Group by product name for analysis
        product_groups = defaultdict(list)
        for item in filtered_data:
            product_groups[item.get('name', 'Unknown')].append(item)
        
        trending_products = []
        
        for product_name, items in product_groups.items():
            if not items:
                continue
            
            # Calculate aggregated metrics
            total_mentions = sum(item.get('total_mentions', 0) for item in items)
            total_positive = sum(item.get('sentiment_counts', {}).get('positive', 0) for item in items)
            total_neutral = sum(item.get('sentiment_counts', {}).get('neutral', 0) for item in items)
            total_negative = sum(item.get('sentiment_counts', {}).get('negative', 0) for item in items)
            
            avg_trending_score = np.mean([item.get('trending_score', 0) for item in items])
            is_trending = any(item.get('is_trending', False) for item in items)
            
            regions = list(set(item.get('region') for item in items))
            categories = list(set(item.get('category') for item in items))
            
            # Calculate sentiment metrics
            total_sentiment_mentions = total_positive + total_neutral + total_negative
            sentiment_score = 0
            if total_sentiment_mentions > 0:
                sentiment_score = (total_positive - total_negative) / total_sentiment_mentions
            
            # Create trend analysis
            trend_analysis = {
                'product_name': product_name,
                'category': categories[0] if categories else 'Unknown',
                'total_mentions': total_mentions,
                'regions': regions,
                'region_count': len(regions),
                'trending_score': avg_trending_score,
                'is_trending': is_trending,
                'sentiment_analysis': {
                    'overall_score': sentiment_score,
                    'positive_count': total_positive,
                    'neutral_count': total_neutral,
                    'negative_count': total_negative,
                    'positive_percentage': (total_positive / total_sentiment_mentions * 100) if total_sentiment_mentions > 0 else 0,
                    'neutral_percentage': (total_neutral / total_sentiment_mentions * 100) if total_sentiment_mentions > 0 else 0,
                    'negative_percentage': (total_negative / total_sentiment_mentions * 100) if total_sentiment_mentions > 0 else 0
                },
                'recommendation': generate_recommendation(
                    total_mentions, sentiment_score, is_trending, avg_trending_score
                ),
                'sample_data': items[:3]  # Include up to 3 sample records
            }
            
            trending_products.append(trend_analysis)
        
        # Sort by trending score
        trending_products.sort(key=lambda x: x['trending_score'], reverse=True)
        
        print(f"✓ Analyzed {len(trending_products)} products")
        return trending_products
        
    except Exception as e:
        print(f"✗ Error analyzing trending products: {e}")
        return []

def generate_recommendation(mentions: int, sentiment_score: float, is_trending: bool, trending_score: float) -> Dict[str, str]:
    """
    Generate inventory and marketing recommendations
    
    Args:
        mentions: Total mentions count
        sentiment_score: Sentiment score (-1 to 1)
        is_trending: Whether product is trending
        trending_score: Trending score
        
    Returns:
        Dictionary with recommendations
    """
    try:
        recommendation = {
            'inventory': 'Standard Stock Levels',
            'marketing': 'Standard promotion strategy',
            'priority': 'Medium',
            'details': 'Average performance indicators'
        }
        
        # High demand scenarios
        if is_trending and sentiment_score > 0.3 and mentions > 100:
            recommendation = {
                'inventory': 'High Demand - Increase Stock',
                'marketing': 'Promote heavily with trending hashtags',
                'priority': 'High',
                'details': f'Trending with {sentiment_score:.2f} sentiment score and {mentions} mentions'
            }
        elif is_trending and sentiment_score > 0.1:
            recommendation = {
                'inventory': 'Moderate Demand - Monitor Stock',
                'marketing': 'Moderate promotion focusing on trending aspects',
                'priority': 'Medium-High',
                'details': f'Trending with {sentiment_score:.2f} sentiment score'
            }
        elif sentiment_score < -0.2:
            recommendation = {
                'inventory': 'Caution - Monitor Feedback',
                'marketing': 'Focus on addressing negative sentiment',
                'priority': 'Low',
                'details': f'Negative sentiment detected ({sentiment_score:.2f})'
            }
        elif mentions > 200 and sentiment_score > 0.1:
            recommendation = {
                'inventory': 'Steady Demand - Maintain Stock',
                'marketing': 'Standard promotion with customer testimonials',
                'priority': 'Medium',
                'details': f'High mentions ({mentions}) with positive sentiment'
            }
        
        return recommendation
        
    except Exception as e:
        print(f"✗ Error generating recommendation: {e}")
        return {
            'inventory': 'Error - Manual Review Required',
            'marketing': 'Error - Manual Review Required',
            'priority': 'Unknown',
            'details': f'Error in analysis: {e}'
        }

def analyze_regional_trends(data: List[Dict]) -> Dict[str, Dict]:
    """
    Analyze trends by region
    
    Args:
        data: List of trend data records
        
    Returns:
        Dictionary with regional trend analysis
    """
    try:
        if not data:
            return {}
        
        regional_data = defaultdict(lambda: {
            'total_mentions': 0,
            'total_products': 0,
            'trending_products': 0,
            'sentiment_totals': {'positive': 0, 'neutral': 0, 'negative': 0},
            'categories': defaultdict(int),
            'top_products': []
        })
        
        # Aggregate data by region
        for item in data:
            region = item.get('region', 'Unknown')
            regional_data[region]['total_mentions'] += item.get('total_mentions', 0)
            regional_data[region]['total_products'] += 1
            
            if item.get('is_trending', False):
                regional_data[region]['trending_products'] += 1
            
            # Sentiment data
            sentiment_counts = item.get('sentiment_counts', {})
            regional_data[region]['sentiment_totals']['positive'] += sentiment_counts.get('positive', 0)
            regional_data[region]['sentiment_totals']['neutral'] += sentiment_counts.get('neutral', 0)
            regional_data[region]['sentiment_totals']['negative'] += sentiment_counts.get('negative', 0)
            
            # Category distribution
            category = item.get('category', 'Unknown')
            regional_data[region]['categories'][category] += 1
            
            # Track top products
            regional_data[region]['top_products'].append({
                'name': item.get('name', 'Unknown'),
                'mentions': item.get('total_mentions', 0),
                'trending_score': item.get('trending_score', 0),
                'is_trending': item.get('is_trending', False)
            })
        
        # Process each region's data
        for region, region_data in regional_data.items():
            # Calculate sentiment percentages
            total_sentiment = sum(region_data['sentiment_totals'].values())
            if total_sentiment > 0:
                region_data['sentiment_percentages'] = {
                    'positive': (region_data['sentiment_totals']['positive'] / total_sentiment) * 100,
                    'neutral': (region_data['sentiment_totals']['neutral'] / total_sentiment) * 100,
                    'negative': (region_data['sentiment_totals']['negative'] / total_sentiment) * 100
                }
            else:
                region_data['sentiment_percentages'] = {'positive': 0, 'neutral': 0, 'negative': 0}
            
            # Sort top products
            region_data['top_products'].sort(key=lambda x: x['trending_score'], reverse=True)
            region_data['top_products'] = region_data['top_products'][:10]  # Top 10
            
            # Calculate trending percentage
            region_data['trending_percentage'] = (region_data['trending_products'] / region_data['total_products'] * 100) if region_data['total_products'] > 0 else 0
        
        print(f"✓ Analyzed trends for {len(regional_data)} regions")
        return dict(regional_data)
        
    except Exception as e:
        print(f"✗ Error analyzing regional trends: {e}")
        return {}

def perform_advanced_sentiment_analysis(texts: List[str]) -> List[Dict]:
    """
    Perform advanced sentiment analysis on new texts
    
    Args:
        texts: List of texts to analyze
        
    Returns:
        List of sentiment analysis results
    """
    try:
        # Use Azure sentiment analysis
        sentiment_results = azure_sentiment_analysis(texts)
        
        advanced_results = []
        for i, (sentiment, confidence) in enumerate(sentiment_results):
            result = {
                'text': texts[i],
                'sentiment': sentiment,
                'confidence': confidence,
                'analysis_method': 'azure' if confidence > 0.6 else 'fallback',
                'timestamp': datetime.now().isoformat()
            }
            advanced_results.append(result)
        
        print(f"✓ Advanced sentiment analysis completed for {len(texts)} texts")
        return advanced_results
        
    except Exception as e:
        print(f"✗ Error in advanced sentiment analysis: {e}")
        return []

def main():
    """Main function to demonstrate trend analysis"""
    try:
        print("Starting trend analysis with Azure integration...")
        
        # Validate Azure services
        config = get_azure_config()
        validation_results = config.validate_azure_services()
        
        print("\n=== Azure Services Status ===")
        for service, is_valid in validation_results.items():
            status = "✓ Available" if is_valid else "✗ Unavailable"
            print(f"{service}: {status}")
        
        # Get latest trends data
        print("\nRetrieving latest trends data...")
        data = get_latest_trends_data()
        
        if not data:
            print("No data available for analysis")
            return
        
        # Perform various analyses
        print("\n=== Trend Analysis Results ===")
        
        # Overall sentiment analysis
        sentiment_metrics = calculate_sentiment_scores(data)
        print(f"\nOverall Sentiment Metrics:")
        print(f"  Sentiment Score: {sentiment_metrics.get('overall_sentiment_score', 0):.2f}")
        print(f"  Positive: {sentiment_metrics.get('positive_percentage', 0):.1f}%")
        print(f"  Neutral: {sentiment_metrics.get('neutral_percentage', 0):.1f}%")
        print(f"  Negative: {sentiment_metrics.get('negative_percentage', 0):.1f}%")
        print(f"  Total Mentions: {sentiment_metrics.get('total_mentions', 0)}")
        
        # Trending products analysis
        trending_products = analyze_trending_products(data)
        print(f"\nTop 5 Trending Products:")
        for i, product in enumerate(trending_products[:5], 1):
            print(f"  {i}. {product['product_name']}")
            print(f"     Category: {product['category']}")
            print(f"     Mentions: {product['total_mentions']}")
            print(f"     Trending Score: {product['trending_score']:.2f}")
            print(f"     Sentiment: {product['sentiment_analysis']['overall_score']:.2f}")
            print(f"     Recommendation: {product['recommendation']['inventory']}")
        
        # Regional trends analysis
        regional_trends = analyze_regional_trends(data)
        print(f"\nTop 3 Regions by Activity:")
        sorted_regions = sorted(regional_trends.items(), key=lambda x: x[1]['total_mentions'], reverse=True)
        for i, (region, region_data) in enumerate(sorted_regions[:3], 1):
            print(f"  {i}. {region}")
            print(f"     Total Mentions: {region_data['total_mentions']}")
            print(f"     Trending Products: {region_data['trending_products']}")
            print(f"     Sentiment: {region_data['sentiment_percentages']['positive']:.1f}% positive")
        
        # Sample advanced sentiment analysis
        sample_texts = [
            "This new product is absolutely amazing! Love the quality and design.",
            "Not very impressed with the purchase, expected better quality.",
            "It's okay, nothing special but serves the purpose well."
        ]
        
        print(f"\nSample Advanced Sentiment Analysis:")
        advanced_sentiment = perform_advanced_sentiment_analysis(sample_texts)
        for result in advanced_sentiment:
            print(f"  Text: {result['text'][:50]}...")
            print(f"  Sentiment: {result['sentiment']} (confidence: {result['confidence']:.2f})")
            print(f"  Method: {result['analysis_method']}")
        
        print(f"\n✓ Trend analysis completed successfully!")
        
    except Exception as e:
        print(f"✗ Trend analysis failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
