#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit Tests for Azure Services Integration
Test Azure service connections and data flow
"""

import unittest
import json
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from azure_integration.config import AzureConfig
from generate_data import (
    save_to_blob_storage, 
    get_latest_data, 
    azure_sentiment_analysis,
    fallback_sentiment_analysis,
    local_fallback_save,
    local_fallback_load
)
from trend_analysis import (
    get_latest_trends_data,
    calculate_sentiment_scores,
    analyze_trending_products,
    analyze_regional_trends
)
# Skip ML workspace import for now
# from connect_workspace import AzureMLWorkspace

class TestAzureConfig(unittest.TestCase):
    """Test Azure configuration management"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_config = AzureConfig()
    
    def test_config_initialization(self):
        """Test configuration initialization"""
        self.assertIsNotNone(self.test_config)
        self.assertIsInstance(self.test_config.config, dict)
    
    def test_get_config(self):
        """Test getting configuration values"""
        # Test with environment variable
        with patch.dict(os.environ, {'AZURE_STORAGE_CONNECTION_STRING': 'test_connection'}):
            config = AzureConfig()
            self.assertEqual(config.get_config('AZURE_STORAGE_CONNECTION_STRING'), 'test_connection')
    
    def test_blob_storage_config(self):
        """Test blob storage configuration"""
        blob_config = self.test_config.get_blob_storage_config()
        self.assertIsInstance(blob_config, dict)
        self.assertIn('connection_string', blob_config)
        self.assertIn('container_name', blob_config)
        self.assertEqual(blob_config['container_name'], 'project-data')
    
    def test_text_analytics_config(self):
        """Test text analytics configuration"""
        text_config = self.test_config.get_text_analytics_config()
        self.assertIsInstance(text_config, dict)
        self.assertIn('key', text_config)
        self.assertIn('endpoint', text_config)
    
    def test_openai_config(self):
        """Test OpenAI configuration"""
        openai_config = self.test_config.get_openai_config()
        self.assertIsInstance(openai_config, dict)
        self.assertIn('api_key', openai_config)
        self.assertIn('endpoint', openai_config)
        self.assertIn('deployment_name', openai_config)
    
    def test_ml_workspace_config(self):
        """Test ML workspace configuration"""
        ml_config = self.test_config.get_ml_workspace_config()
        self.assertIsInstance(ml_config, dict)
        self.assertIn('subscription_id', ml_config)
        self.assertIn('resource_group', ml_config)
        self.assertIn('workspace_name', ml_config)
    
    def test_local_fallback_config(self):
        """Test local fallback configuration"""
        fallback_config = self.test_config.get_local_fallback_config()
        self.assertIsInstance(fallback_config, dict)
        self.assertIn('data_directory', fallback_config)
        self.assertIn('fallback_mode', fallback_config)
        self.assertTrue(fallback_config['fallback_mode'])

class TestBlobStorageOperations(unittest.TestCase):
    """Test Azure Blob Storage operations"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_data = {
            'id': 1,
            'name': 'Test Product',
            'category': 'Electronics',
            'sentiment': 'positive'
        }
        self.test_blob_name = 'test_data.json'
        
        # Create temporary directory for local fallback tests
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
    
    @patch('generate_data.BlobServiceClient')
    def test_save_to_blob_storage_success(self, mock_blob_client):
        """Test successful blob storage save"""
        # Mock blob service client
        mock_client = Mock()
        mock_blob_client.from_connection_string.return_value = mock_client
        
        # Mock container and blob clients
        mock_container = Mock()
        mock_blob = Mock()
        mock_client.create_container.return_value = mock_container
        mock_client.get_container_client.return_value = mock_container
        mock_client.get_blob_client.return_value = mock_blob
        
        # Mock configuration
        with patch('generate_data.get_azure_config') as mock_config:
            mock_config.return_value.get_blob_storage_config.return_value = {
                'connection_string': 'test_connection',
                'container_name': 'project-data'
            }
            
            result = save_to_blob_storage(self.test_data, self.test_blob_name)
            
            self.assertTrue(result)
            mock_blob.upload_blob.assert_called_once()
    
    @patch('generate_data.BlobServiceClient')
    def test_save_to_blob_storage_failure_fallback(self, mock_blob_client):
        """Test blob storage save failure with fallback"""
        # Mock blob service client to raise exception
        mock_blob_client.from_connection_string.side_effect = Exception("Connection failed")
        
        # Mock configuration
        with patch('generate_data.get_azure_config') as mock_config:
            mock_config.return_value.get_blob_storage_config.return_value = {
                'connection_string': 'test_connection',
                'container_name': 'project-data'
            }
            
            result = save_to_blob_storage(self.test_data, self.test_blob_name)
            
            # Should fallback to local storage
            self.assertTrue(result)
            self.assertTrue(os.path.exists('data/test_data.json'))
    
    @patch('generate_data.BlobServiceClient')
    def test_get_latest_data_success(self, mock_blob_client):
        """Test successful data retrieval from blob storage"""
        # Mock blob service client
        mock_client = Mock()
        mock_blob_client.from_connection_string.return_value = mock_client
        
        # Mock blob client
        mock_blob = Mock()
        mock_blob.download_blob.return_value.readall.return_value = json.dumps(self.test_data).encode('utf-8')
        mock_client.get_blob_client.return_value = mock_blob
        
        # Mock configuration
        with patch('generate_data.get_azure_config') as mock_config:
            mock_config.return_value.get_blob_storage_config.return_value = {
                'connection_string': 'test_connection',
                'container_name': 'project-data'
            }
            
            result = get_latest_data(self.test_blob_name)
            
            self.assertEqual(result, self.test_data)
    
    def test_local_fallback_save_and_load(self):
        """Test local fallback save and load operations"""
        # Test save
        result = local_fallback_save(self.test_data, self.test_blob_name)
        self.assertTrue(result)
        self.assertTrue(os.path.exists('data/test_data.json'))
        
        # Test load
        loaded_data = local_fallback_load(self.test_blob_name)
        self.assertEqual(loaded_data, self.test_data)
    
    def test_local_fallback_load_nonexistent(self):
        """Test local fallback load with nonexistent file"""
        result = local_fallback_load('nonexistent.json')
        self.assertIsNone(result)

class TestSentimentAnalysis(unittest.TestCase):
    """Test sentiment analysis operations"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_texts = [
            "This product is amazing! Love it so much!",
            "Not impressed with the quality, disappointed.",
            "It's okay, nothing special but does the job."
        ]
    
    def test_fallback_sentiment_analysis(self):
        """Test fallback sentiment analysis"""
        # Test positive sentiment
        sentiment, confidence = fallback_sentiment_analysis("This is amazing and perfect!")
        self.assertEqual(sentiment, "positive")
        self.assertGreater(confidence, 0.5)
        
        # Test negative sentiment
        sentiment, confidence = fallback_sentiment_analysis("This is terrible and disappointing!")
        self.assertEqual(sentiment, "negative")
        self.assertGreater(confidence, 0.5)
        
        # Test neutral sentiment
        sentiment, confidence = fallback_sentiment_analysis("This is a normal product.")
        self.assertEqual(sentiment, "neutral")
        self.assertGreater(confidence, 0.5)
    
    @patch('generate_data.TextAnalyticsClient')
    def test_azure_sentiment_analysis_success(self, mock_client_class):
        """Test successful Azure sentiment analysis"""
        # Mock client and response
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock response
        mock_doc = Mock()
        mock_doc.is_error = False
        mock_doc.sentiment = "positive"
        mock_doc.confidence_scores.positive = 0.9
        mock_client.analyze_sentiment.return_value = [mock_doc]
        
        # Mock configuration
        with patch('generate_data.get_azure_config') as mock_config:
            mock_config.return_value.get_text_analytics_config.return_value = {
                'key': 'test_key',
                'endpoint': 'test_endpoint'
            }
            
            results = azure_sentiment_analysis([self.test_texts[0]])
            
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0][0], "positive")
            self.assertEqual(results[0][1], 0.9)
    
    @patch('generate_data.TextAnalyticsClient')
    def test_azure_sentiment_analysis_failure_fallback(self, mock_client_class):
        """Test Azure sentiment analysis failure with fallback"""
        # Mock client to raise exception
        mock_client_class.side_effect = Exception("API error")
        
        # Mock configuration
        with patch('generate_data.get_azure_config') as mock_config:
            mock_config.return_value.get_text_analytics_config.return_value = {
                'key': 'test_key',
                'endpoint': 'test_endpoint'
            }
            
            results = azure_sentiment_analysis(self.test_texts)
            
            # Should fallback to local analysis
            self.assertEqual(len(results), len(self.test_texts))
            for result in results:
                self.assertIn(result[0], ["positive", "negative", "neutral"])
                self.assertGreater(result[1], 0)

class TestTrendAnalysis(unittest.TestCase):
    """Test trend analysis operations"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_data = [
            {
                'id': 1,
                'name': 'Test Product 1',
                'category': 'Electronics',
                'region': 'Mumbai',
                'total_mentions': 100,
                'sentiment_counts': {'positive': 60, 'neutral': 25, 'negative': 15},
                'trending_score': 0.8,
                'is_trending': True
            },
            {
                'id': 2,
                'name': 'Test Product 2',
                'category': 'Fashion',
                'region': 'Delhi',
                'total_mentions': 80,
                'sentiment_counts': {'positive': 40, 'neutral': 30, 'negative': 10},
                'trending_score': 0.6,
                'is_trending': False
            }
        ]
    
    def test_calculate_sentiment_scores(self):
        """Test sentiment score calculation"""
        scores = calculate_sentiment_scores(self.test_data)
        
        self.assertIsInstance(scores, dict)
        self.assertIn('overall_sentiment_score', scores)
        self.assertIn('positive_percentage', scores)
        self.assertIn('neutral_percentage', scores)
        self.assertIn('negative_percentage', scores)
        self.assertIn('total_mentions', scores)
        
        # Check calculations
        expected_total = 100 + 80
        self.assertEqual(scores['total_mentions'], expected_total)
        
        expected_positive = (60 + 40) / expected_total * 100
        self.assertAlmostEqual(scores['positive_percentage'], expected_positive, places=1)
    
    def test_calculate_sentiment_scores_empty_data(self):
        """Test sentiment score calculation with empty data"""
        scores = calculate_sentiment_scores([])
        
        self.assertEqual(scores, {})
    
    def test_analyze_trending_products(self):
        """Test trending products analysis"""
        trending = analyze_trending_products(self.test_data)
        
        self.assertIsInstance(trending, list)
        self.assertEqual(len(trending), 2)
        
        # Check first product (should be sorted by trending score)
        first_product = trending[0]
        self.assertIn('product_name', first_product)
        self.assertIn('category', first_product)
        self.assertIn('total_mentions', first_product)
        self.assertIn('sentiment_analysis', first_product)
        self.assertIn('recommendation', first_product)
        
        # Should be sorted by trending score
        self.assertEqual(first_product['product_name'], 'Test Product 1')
    
    def test_analyze_trending_products_with_filters(self):
        """Test trending products analysis with filters"""
        # Test region filter
        trending = analyze_trending_products(self.test_data, region='Mumbai')
        self.assertEqual(len(trending), 1)
        self.assertEqual(trending[0]['product_name'], 'Test Product 1')
        
        # Test category filter
        trending = analyze_trending_products(self.test_data, category='Fashion')
        self.assertEqual(len(trending), 1)
        self.assertEqual(trending[0]['product_name'], 'Test Product 2')
    
    def test_analyze_regional_trends(self):
        """Test regional trends analysis"""
        regional = analyze_regional_trends(self.test_data)
        
        self.assertIsInstance(regional, dict)
        self.assertIn('Mumbai', regional)
        self.assertIn('Delhi', regional)
        
        # Check Mumbai data
        mumbai_data = regional['Mumbai']
        self.assertEqual(mumbai_data['total_mentions'], 100)
        self.assertEqual(mumbai_data['trending_products'], 1)
        
        # Check Delhi data
        delhi_data = regional['Delhi']
        self.assertEqual(delhi_data['total_mentions'], 80)
        self.assertEqual(delhi_data['trending_products'], 0)

class TestAzureMLWorkspace(unittest.TestCase):
    """Test Azure ML Workspace operations"""
    
    def test_workspace_initialization(self):
        """Test workspace initialization"""
        # Skip ML workspace tests for now
        print("Skipping ML workspace tests - azure.ai.ml not available")
        self.skipTest("Azure ML package not installed")
    
    def test_get_workspace_info(self):
        """Test getting workspace information"""
        # Skip ML workspace tests for now
        print("Skipping ML workspace tests - azure.ai.ml not available")
        self.skipTest("Azure ML package not installed")

class TestDataFlow(unittest.TestCase):
    """Test complete data flow integration"""
    
    def test_complete_data_flow(self):
        """Test complete data flow from generation to analysis"""
        # This test simulates the complete flow without actual Azure services
        
        # 1. Generate sample data
        sample_data = {
            'id': 1,
            'name': 'Test Product',
            'category': 'Electronics',
            'region': 'Mumbai',
            'total_mentions': 100,
            'sentiment_counts': {'positive': 60, 'neutral': 25, 'negative': 15},
            'trending_score': 0.8,
            'is_trending': True
        }
        
        # 2. Test local fallback save
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                # Save data
                result = local_fallback_save(sample_data, 'test_data.json')
                self.assertTrue(result)
                
                # Load data
                loaded_data = local_fallback_load('test_data.json')
                self.assertEqual(loaded_data, sample_data)
                
                # Analyze sentiment
                sentiment, confidence = fallback_sentiment_analysis("This is a great product!")
                self.assertEqual(sentiment, "positive")
                
                # Calculate sentiment scores
                scores = calculate_sentiment_scores([sample_data])
                self.assertGreater(scores['positive_percentage'], 50)
                
            finally:
                os.chdir(original_cwd)

def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(loader.loadTestsFromTestCase(TestAzureConfig))
    suite.addTest(loader.loadTestsFromTestCase(TestBlobStorageOperations))
    suite.addTest(loader.loadTestsFromTestCase(TestSentimentAnalysis))
    suite.addTest(loader.loadTestsFromTestCase(TestTrendAnalysis))
    suite.addTest(loader.loadTestsFromTestCase(TestAzureMLWorkspace))
    suite.addTest(loader.loadTestsFromTestCase(TestDataFlow))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    print("Running Azure Services Integration Tests...")
    success = run_tests()
    
    if success:
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Some tests failed!")
        sys.exit(1)
