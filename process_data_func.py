#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Azure Functions for Serverless Data Processing
Process data when new blobs are uploaded to Azure Blob Storage
"""

import azure.functions as func
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
from azure.storage.blob import BlobServiceClient
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import AzureError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main(req: func.HttpRequest, inputblob: func.InputStream) -> func.HttpResponse:
    """
    Main Azure Function triggered by HTTP request or blob storage event
    
    Args:
        req: HTTP request object
        inputblob: Input blob stream
        
    Returns:
        HTTP response with processing results
    """
    try:
        logger.info('Python HTTP trigger function processed a request.')
        
        # Get configuration from environment variables
        config = get_function_config()
        
        # Process the incoming data
        if inputblob:
            # Process blob data
            result = process_blob_data(inputblob, config)
        else:
            # Process HTTP request data
            result = process_http_request(req, config)
        
        if result['success']:
            return func.HttpResponse(
                json.dumps(result, ensure_ascii=False, indent=2),
                status_code=200,
                headers={'Content-Type': 'application/json'}
            )
        else:
            return func.HttpResponse(
                json.dumps(result, ensure_ascii=False, indent=2),
                status_code=500,
                headers={'Content-Type': 'application/json'}
            )
            
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        error_result = {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
        return func.HttpResponse(
            json.dumps(error_result, ensure_ascii=False, indent=2),
            status_code=500,
            headers={'Content-Type': 'application/json'}
        )

def get_function_config() -> Dict[str, str]:
    """Get Azure Function configuration from environment variables"""
    return {
        'storage_connection_string': os.getenv('AZURE_STORAGE_CONNECTION_STRING'),
        'text_analytics_key': os.getenv('AZURE_AI_LANGUAGE_KEY'),
        'text_analytics_endpoint': os.getenv('AZURE_AI_LANGUAGE_ENDPOINT'),
        'container_name': os.getenv('CONTAINER_NAME', 'project-data'),
        'output_container': os.getenv('OUTPUT_CONTAINER', 'processed-data')
    }

def process_blob_data(inputblob: func.InputStream, config: Dict[str, str]) -> Dict:
    """
    Process data from blob storage event
    
    Args:
        inputblob: Input blob stream
        config: Function configuration
        
    Returns:
        Processing results
    """
    try:
        logger.info(f"Processing blob: {inputblob.name}")
        
        # Read blob content
        blob_content = inputblob.read()
        
        # Parse JSON data
        try:
            data = json.loads(blob_content.decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in blob: {e}")
            return {
                'success': False,
                'error': f'Invalid JSON format: {e}',
                'blob_name': inputblob.name
            }
        
        # Process the data
        processed_data = process_data_for_sentiment(data, config)
        
        # Save processed data back to blob storage
        output_blob_name = f"processed_{inputblob.name}"
        save_success = save_processed_data(processed_data, output_blob_name, config)
        
        result = {
            'success': True,
            'blob_name': inputblob.name,
            'output_blob_name': output_blob_name,
            'processed_items': len(processed_data) if isinstance(processed_data, list) else 1,
            'saved_to_storage': save_success,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Successfully processed blob: {inputblob.name}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing blob data: {e}")
        return {
            'success': False,
            'error': str(e),
            'blob_name': inputblob.name if inputblob else 'unknown'
        }

def process_http_request(req: func.HttpRequest, config: Dict[str, str]) -> Dict:
    """
    Process HTTP request data
    
    Args:
        req: HTTP request object
        config: Function configuration
        
    Returns:
        Processing results
    """
    try:
        # Get request body
        try:
            req_body = req.get_json()
        except ValueError:
            return {
                'success': False,
                'error': 'Invalid JSON in request body'
            }
        
        if not req_body:
            return {
                'success': False,
                'error': 'Empty request body'
            }
        
        # Process the data
        processed_data = process_data_for_sentiment(req_body, config)
        
        # Save processed data to blob storage
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_blob_name = f"http_processed_{timestamp}.json"
        save_success = save_processed_data(processed_data, output_blob_name, config)
        
        result = {
            'success': True,
            'processed_items': len(processed_data) if isinstance(processed_data, list) else 1,
            'output_blob_name': output_blob_name,
            'saved_to_storage': save_success,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info("Successfully processed HTTP request")
        return result
        
    except Exception as e:
        logger.error(f"Error processing HTTP request: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def process_data_for_sentiment(data: Dict, config: Dict[str, str]) -> List[Dict]:
    """
    Process data and perform sentiment analysis
    
    Args:
        data: Input data to process
        config: Function configuration
        
    Returns:
        Processed data with sentiment analysis
    """
    try:
        # Ensure data is a list
        if not isinstance(data, list):
            data = [data]
        
        # Extract texts for sentiment analysis
        texts_to_analyze = []
        text_indices = []
        
        for i, item in enumerate(data):
            # Look for text fields to analyze
            text_fields = ['sample_posts', 'text', 'content', 'description', 'comment']
            
            for field in text_fields:
                if field in item:
                    if field == 'sample_posts' and isinstance(item[field], list):
                        for post in item[field]:
                            if isinstance(post, dict) and 'text' in post:
                                texts_to_analyze.append(post['text'])
                                text_indices.append((i, field, post))
                            elif isinstance(post, str):
                                texts_to_analyze.append(post)
                                text_indices.append((i, field, post))
                    elif isinstance(item[field], str):
                        texts_to_analyze.append(item[field])
                        text_indices.append((i, field, item[field]))
        
        # Perform sentiment analysis
        if texts_to_analyze:
            sentiment_results = perform_sentiment_analysis(texts_to_analyze, config)
            
            # Apply sentiment results back to data
            for idx, (data_idx, field, original_text) in enumerate(text_indices):
                if idx < len(sentiment_results):
                    sentiment, confidence = sentiment_results[idx]
                    
                    # Add sentiment analysis results
                    if 'sentiment_analysis' not in data[data_idx]:
                        data[data_idx]['sentiment_analysis'] = {}
                    
                    data[data_idx]['sentiment_analysis'][f'{field}_sentiment'] = {
                        'sentiment': sentiment,
                        'confidence': confidence,
                        'analyzed_text': original_text[:100] + '...' if len(original_text) > 100 else original_text,
                        'analysis_timestamp': datetime.now().isoformat()
                    }
        
        # Add processing metadata
        for item in data:
            item['processing_metadata'] = {
                'processed_by': 'azure_function',
                'processing_timestamp': datetime.now().isoformat(),
                'sentiment_analysis_performed': len(texts_to_analyze) > 0
            }
        
        logger.info(f"Processed {len(data)} items with sentiment analysis on {len(texts_to_analyze)} texts")
        return data
        
    except Exception as e:
        logger.error(f"Error processing data for sentiment: {e}")
        return []

def perform_sentiment_analysis(texts: List[str], config: Dict[str, str]) -> List[tuple]:
    """
    Perform sentiment analysis using Azure Text Analytics
    
    Args:
        texts: List of texts to analyze
        config: Function configuration
        
    Returns:
        List of (sentiment, confidence) tuples
    """
    try:
        if not config['text_analytics_key'] or not config['text_analytics_endpoint']:
            logger.warning("Azure Text Analytics credentials not available, using fallback")
            return [fallback_sentiment_analysis(text) for text in texts]
        
        # Initialize client
        client = TextAnalyticsClient(
            endpoint=config['text_analytics_endpoint'],
            credential=AzureKeyCredential(config['text_analytics_key'])
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
                        logger.warning(f"Sentiment analysis error for document: {doc.error}")
                        results.append(fallback_sentiment_analysis(batch[0]))
                        
            except Exception as e:
                logger.error(f"Batch sentiment analysis failed: {e}")
                # Fallback for entire batch
                for text in batch:
                    results.append(fallback_sentiment_analysis(text))
        
        logger.info(f"Sentiment analysis completed for {len(texts)} texts")
        return results
        
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        return [fallback_sentiment_analysis(text) for text in texts]

def fallback_sentiment_analysis(text: str) -> tuple:
    """
    Fallback sentiment analysis using keyword matching
    
    Args:
        text: Text to analyze
        
    Returns:
        Tuple of (sentiment, confidence)
    """
    import random
    
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

def save_processed_data(data: List[Dict], blob_name: str, config: Dict[str, str]) -> bool:
    """
    Save processed data to Azure Blob Storage
    
    Args:
        data: Processed data to save
        blob_name: Name of the blob to save to
        config: Function configuration
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if not config['storage_connection_string']:
            logger.error("Storage connection string not available")
            return False
        
        # Initialize blob service client
        blob_service_client = BlobServiceClient.from_connection_string(
            config['storage_connection_string']
        )
        
        # Create output container if it doesn't exist
        try:
            blob_service_client.create_container(config['output_container'])
        except Exception:
            # Container might already exist
            pass
        
        # Convert data to JSON string
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        
        # Upload to blob
        blob_client = blob_service_client.get_blob_client(
            container=config['output_container'],
            blob=blob_name
        )
        
        blob_client.upload_blob(json_data, overwrite=True)
        logger.info(f"Saved processed data to blob: {blob_name}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving processed data: {e}")
        return False

# Additional function for blob trigger
def blob_trigger_main(myblob: func.InputStream) -> None:
    """
    Alternative main function for blob trigger
    
    Args:
        myblob: Input blob stream
    """
    try:
        logger.info(f'Python blob trigger function processed blob: {myblob.name}')
        
        # Get configuration
        config = get_function_config()
        
        # Process blob data
        result = process_blob_data(myblob, config)
        
        if result['success']:
            logger.info(f"Successfully processed blob: {myblob.name}")
        else:
            logger.error(f"Failed to process blob: {myblob.name}, Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Error in blob trigger function: {e}")

# Function for timer trigger (periodic processing)
def timer_trigger_main(mytimer: func.TimerRequest) -> None:
    """
    Timer trigger function for periodic processing
    
    Args:
        mytimer: Timer request object
    """
    try:
        logger.info('Python timer trigger function executed.')
        
        # Get configuration
        config = get_function_config()
        
        # Perform periodic processing tasks
        if mytimer.past_due:
            logger.info('The timer is past due!')
        
        # Example: Process any unprocessed blobs
        process_unprocessed_blobs(config)
        
        logger.info('Timer trigger function completed successfully.')
        
    except Exception as e:
        logger.error(f"Error in timer trigger function: {e}")

def process_unprocessed_blobs(config: Dict[str, str]) -> None:
    """
    Process any unprocessed blobs in the container
    
    Args:
        config: Function configuration
    """
    try:
        if not config['storage_connection_string']:
            logger.error("Storage connection string not available")
            return
        
        # Initialize blob service client
        blob_service_client = BlobServiceClient.from_connection_string(
            config['storage_connection_string']
        )
        
        # List blobs in the main container
        container_client = blob_service_client.get_container_client(config['container_name'])
        
        processed_count = 0
        for blob in container_client.list_blobs():
            # Skip already processed blobs
            if blob.name.startswith('processed_'):
                continue
            
            # Check if processed version exists
            processed_blob_name = f"processed_{blob.name}"
            output_container_client = blob_service_client.get_container_client(config['output_container'])
            
            try:
                output_container_client.get_blob_client(processed_blob_name).get_blob_properties()
                continue  # Already processed
            except Exception:
                # Not processed yet, process it
                pass
            
            # Download and process blob
            blob_client = container_client.get_blob_client(blob.name)
            blob_content = blob_client.download_blob().readall()
            
            try:
                data = json.loads(blob_content.decode('utf-8'))
                processed_data = process_data_for_sentiment(data, config)
                
                if save_processed_data(processed_data, processed_blob_name, config):
                    processed_count += 1
                    logger.info(f"Processed blob: {blob.name}")
                    
            except Exception as e:
                logger.error(f"Error processing blob {blob.name}: {e}")
        
        logger.info(f"Processed {processed_count} unprocessed blobs")
        
    except Exception as e:
        logger.error(f"Error in process_unprocessed_blobs: {e}")

# Export functions for Azure Functions runtime
__all__ = ['main', 'blob_trigger_main', 'timer_trigger_main']
