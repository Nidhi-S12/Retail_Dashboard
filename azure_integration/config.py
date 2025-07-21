#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Azure Configuration Management
Centralized Azure service configurations using environment variables
"""

import os
import json
from typing import Dict, Optional, Tuple
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import AzureError
from dotenv import load_dotenv

# Load .env file with explicit path
dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if load_dotenv(dotenv_path, override=True):
    print(f"✓ Loaded .env file from {dotenv_path}")
else:
    print(f"⚠ Failed to load .env file from {dotenv_path}")

class AzureConfig:
    """Azure configuration manager using environment variables"""
    
    def __init__(self):
        self.credential = None
        self.config = {}
        self._initialize_credentials()
        self._load_configuration()
    
    def _initialize_credentials(self):
        """Initialize Azure credentials using DefaultAzureCredential"""
        try:
            self.credential = DefaultAzureCredential()
            token = self.credential.get_token("https://management.azure.com/.default")
            print("✓ Azure credentials initialized successfully")
        except Exception as e:
            print(f"⚠ Azure credentials initialization failed: {e}")
            self.credential = None
    
    def _load_configuration(self):
        """Load configuration from environment variables"""
        config_keys = [
            ("AZURE_STORAGE_CONNECTION_STRING", None),
            ("AZURE_AI_LANGUAGE_KEY", None),
            ("AZURE_AI_LANGUAGE_ENDPOINT", None),
            ("AZURE_OPENAI_API_KEY", None),
            ("AZURE_OPENAI_ENDPOINT", None),
            ("AZURE_OPENAI_DEPLOYMENT_NAME", None),
            ("AZURE_SUBSCRIPTION_ID", None),
            ("AZURE_RESOURCE_GROUP", None),
            ("AZURE_WORKSPACE_NAME", None),
            ("CONTAINER_NAME", "project-data"),
            ("OUTPUT_CONTAINER", "project-data")
        ]
        
        for key, default in config_keys:
            value = os.getenv(key) or default
            self.config[key] = value
            if value:
                print(f"✓ {key} loaded from environment")
            else:
                print(f"⚠ {key} not found in environment variables")
    
    def get_config(self, key: str) -> Optional[str]:
        """Get configuration value"""
        return self.config.get(key)
    
    def get_blob_storage_config(self) -> Dict[str, str]:
        """Get Azure Blob Storage configuration"""
        return {
            "connection_string": self.get_config("AZURE_STORAGE_CONNECTION_STRING"),
            "container_name": self.get_config("CONTAINER_NAME")
        }
    
    def get_text_analytics_config(self) -> Dict[str, str]:
        """Get Azure Text Analytics configuration"""
        return {
            "key": self.get_config("AZURE_AI_LANGUAGE_KEY"),
            "endpoint": self.get_config("AZURE_AI_LANGUAGE_ENDPOINT")
        }
    
    def get_openai_config(self) -> Dict[str, str]:
        """Get Azure OpenAI configuration"""
        return {
            "api_key": self.get_config("AZURE_OPENAI_API_KEY"),
            "endpoint": self.get_config("AZURE_OPENAI_ENDPOINT"),
            "deployment_name": self.get_config("AZURE_OPENAI_DEPLOYMENT_NAME")
        }
    
    def get_ml_workspace_config(self) -> Dict[str, str]:
        """Get Azure ML Workspace configuration"""
        return {
            "subscription_id": self.get_config("AZURE_SUBSCRIPTION_ID"),
            "resource_group": self.get_config("AZURE_RESOURCE_GROUP"),
            "workspace_name": self.get_config("AZURE_WORKSPACE_NAME")
        }
    
    def validate_azure_services(self) -> Dict[str, bool]:
        """Validate all Azure service configurations and connections"""
        validation_results = {}
        
        # Validate Blob Storage
        blob_config = self.get_blob_storage_config()
        validation_results["blob_storage"] = self._validate_blob_storage(blob_config)
        
        # Validate Text Analytics
        text_config = self.get_text_analytics_config()
        validation_results["text_analytics"] = self._validate_text_analytics(text_config)
        
        # Validate OpenAI (optional)
        openai_config = self.get_openai_config()
        validation_results["openai"] = self._validate_openai(openai_config)
        
        # Validate ML Workspace
        ml_config = self.get_ml_workspace_config()
        validation_results["ml_workspace"] = self._validate_ml_workspace(ml_config)
        
        return validation_results
    
    def _validate_blob_storage(self, config: Dict[str, str]) -> bool:
        """Validate Azure Blob Storage connection"""
        try:
            if not config["connection_string"]:
                print("⚠ Azure Blob Storage connection string not found")
                return False
            
            from azure.storage.blob import BlobServiceClient
            blob_service_client = BlobServiceClient.from_connection_string(config["connection_string"])
            
            # Test connection by listing containers
            containers = list(blob_service_client.list_containers())
            print("✓ Azure Blob Storage connection validated")
            return True
        except Exception as e:
            print(f"✗ Azure Blob Storage validation failed: {e}")
            return False
    
    def _validate_text_analytics(self, config: Dict[str, str]) -> bool:
        """Validate Azure Text Analytics connection"""
        try:
            if not config["key"] or not config["endpoint"]:
                print("⚠ Azure Text Analytics credentials not found")
                return False
            
            from azure.ai.textanalytics import TextAnalyticsClient
            from azure.core.credentials import AzureKeyCredential
            
            client = TextAnalyticsClient(
                endpoint=config["endpoint"],
                credential=AzureKeyCredential(config["key"])
            )
            
            # Test with a simple sentiment analysis
            response = client.analyze_sentiment(documents=["This is a test"])
            print("✓ Azure Text Analytics connection validated")
            return True
        except Exception as e:
            print(f"✗ Azure Text Analytics validation failed: {e}")
            return False
    
    def _validate_openai(self, config: Dict[str, str]) -> bool:
        """Validate Azure OpenAI connection (optional)"""
        try:
            if not config["api_key"] or not config["endpoint"]:
                print("⚠ Azure OpenAI credentials not found - skipping (optional)")
                return False
            
            print("✓ Azure OpenAI configuration found")
            return True
        except Exception as e:
            print(f"✗ Azure OpenAI validation failed: {e}")
            return False
    
    def _validate_ml_workspace(self, config: Dict[str, str]) -> bool:
        """Validate Azure ML Workspace connection"""
        try:
            if not all([config["subscription_id"], config["resource_group"], config["workspace_name"]]):
                print("⚠ Azure ML Workspace configuration incomplete")
                return False
            
            try:
                from azure.ai.ml import MLClient
                
                ml_client = MLClient(
                    credential=self.credential,
                    subscription_id=config["subscription_id"],
                    resource_group_name=config["resource_group"],
                    workspace_name=config["workspace_name"]
                )
                
                # Test connection
                workspace = ml_client.workspaces.get(config["workspace_name"])
                print("✓ Azure ML Workspace connection validated")
                return True
            except ImportError:
                print("⚠ Azure ML SDK not installed - skipping ML workspace validation")
                return False
        except Exception as e:
            print(f"✗ Azure ML Workspace validation failed: {e}")
            return False
    
    def get_local_fallback_config(self) -> Dict[str, str]:
        """Get local fallback configuration"""
        return {
            "data_directory": "data",
            "fallback_mode": True
        }

# Global configuration instance
azure_config = AzureConfig()

def get_azure_config() -> AzureConfig:
    """Get the global Azure configuration instance"""
    return azure_config

if __name__ == "__main__":
    # Test configuration validation
    config = get_azure_config()
    validation_results = config.validate_azure_services()
    
    print("\n=== Azure Services Validation Results ===")
    for service, is_valid in validation_results.items():
        status = "✓ Valid" if is_valid else "✗ Invalid"
        print(f"{service}: {status}")
    
    print(f"\nFallback to local storage: {not validation_results.get('blob_storage', False)}")