#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Azure Machine Learning Workspace Connection
Connect to Azure ML Workspace for ML infrastructure
"""

import os
import sys
from typing import Optional, Dict, Any
from azure.ai.ml import MLClient
from azure.ai.ml.entities import Environment, Model, Data
from azure.core.exceptions import AzureError
from azure.identity import DefaultAzureCredential

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from azure_integration.config import get_azure_config

class AzureMLWorkspace:
    """Azure Machine Learning Workspace manager"""
    
    def __init__(self):
        self.ml_client = None
        self.workspace_name = None
        self.resource_group = None
        self.subscription_id = None
        self.compute_target = None
        self._initialize_client()
    
    def _initialize_client(self) -> bool:
        """Initialize Azure ML Client"""
        try:
            config = get_azure_config()
            ml_config = config.get_ml_workspace_config()
            
            if not all([ml_config["subscription_id"], ml_config["resource_group"], ml_config["workspace_name"]]):
                print("⚠ Azure ML Workspace configuration incomplete")
                return False
            
            self.subscription_id = ml_config["subscription_id"]
            self.resource_group = ml_config["resource_group"]
            self.workspace_name = ml_config["workspace_name"]
            
            # Initialize ML client
            credential = DefaultAzureCredential()
            self.ml_client = MLClient(
                credential=credential,
                subscription_id=self.subscription_id,
                resource_group_name=self.resource_group,
                workspace_name=self.workspace_name
            )
            
            # Test connection
            workspace = self.ml_client.workspaces.get(self.workspace_name)
            print(f"✓ Connected to Azure ML Workspace: {workspace.name}")
            print(f"  Resource Group: {self.resource_group}")
            print(f"  Subscription: {self.subscription_id}")
            
            return True
            
        except Exception as e:
            print(f"✗ Failed to initialize Azure ML Workspace: {e}")
            return False
    
    def get_workspace_info(self) -> Optional[Dict[str, Any]]:
        """Get workspace information"""
        try:
            if not self.ml_client:
                print("✗ ML Client not initialized")
                return None
            
            workspace = self.ml_client.workspaces.get(self.workspace_name)
            
            info = {
                'name': workspace.name,
                'resource_group': self.resource_group,
                'subscription_id': self.subscription_id,
                'location': workspace.location,
                'description': workspace.description,
                'friendly_name': workspace.friendly_name,
                'creation_time': workspace.creation_time,
                'storage_account': workspace.storage_account
            }
            
            print(f"✓ Retrieved workspace info for: {workspace.name}")
            return info
            
        except Exception as e:
            print(f"✗ Error getting workspace info: {e}")
            return None
    
    def list_compute_targets(self) -> Optional[Dict[str, Any]]:
        """List available compute targets"""
        try:
            if not self.ml_client:
                print("✗ ML Client not initialized")
                return None
            
            compute_targets = {}
            
            for compute in self.ml_client.compute.list():
                compute_targets[compute.name] = {
                    'type': compute.type,
                    'state': compute.provisioning_state,
                    'size': getattr(compute, 'size', 'N/A'),
                    'min_nodes': getattr(compute, 'min_nodes', 'N/A'),
                    'max_nodes': getattr(compute, 'max_nodes', 'N/A'),
                    'created_on': compute.created_on
                }
            
            print(f"✓ Found {len(compute_targets)} compute targets")
            return compute_targets
            
        except Exception as e:
            print(f"✗ Error listing compute targets: {e}")
            return None
    
    def get_compute_target(self, compute_name: str) -> Optional[Any]:
        """Get specific compute target"""
        try:
            if not self.ml_client:
                print("✗ ML Client not initialized")
                return None
            
            compute = self.ml_client.compute.get(compute_name)
            print(f"✓ Retrieved compute target: {compute_name}")
            return compute
            
        except Exception as e:
            print(f"✗ Error getting compute target '{compute_name}': {e}")
            return None
    
    def create_compute_target(self, compute_name: str, compute_type: str = "amlcompute", 
                            vm_size: str = "Standard_DS3_v2", min_nodes: int = 0, max_nodes: int = 4) -> bool:
        """Create a new compute target"""
        try:
            if not self.ml_client:
                print("✗ ML Client not initialized")
                return False
            
            from azure.ai.ml.entities import AmlCompute
            
            compute_config = AmlCompute(
                name=compute_name,
                type=compute_type,
                size=vm_size,
                min_instances=min_nodes,
                max_instances=max_nodes,
                idle_time_before_scale_down=120  # 2 minutes
            )
            
            compute = self.ml_client.compute.begin_create_or_update(compute_config)
            print(f"✓ Creating compute target: {compute_name}")
            print(f"  VM Size: {vm_size}")
            print(f"  Min Nodes: {min_nodes}, Max Nodes: {max_nodes}")
            
            return True
            
        except Exception as e:
            print(f"✗ Error creating compute target: {e}")
            return False
    
    def list_environments(self) -> Optional[Dict[str, Any]]:
        """List available environments"""
        try:
            if not self.ml_client:
                print("✗ ML Client not initialized")
                return None
            
            environments = {}
            
            for env in self.ml_client.environments.list():
                environments[env.name] = {
                    'version': env.version,
                    'description': env.description,
                    'creation_context': env.creation_context,
                    'tags': env.tags
                }
            
            print(f"✓ Found {len(environments)} environments")
            return environments
            
        except Exception as e:
            print(f"✗ Error listing environments: {e}")
            return None
    
    def create_environment(self, env_name: str, env_description: str = "Custom environment for retail trends analysis") -> bool:
        """Create a new environment"""
        try:
            if not self.ml_client:
                print("✗ ML Client not initialized")
                return False
            
            # Create environment from conda file
            conda_file = {
                "name": "retail-trends-env",
                "dependencies": [
                    "python=3.8",
                    "pip",
                    {
                        "pip": [
                            "azure-ai-textanalytics",
                            "azure-storage-blob",
                            "azure-identity",
                            "pandas",
                            "numpy",
                            "scikit-learn",
                            "matplotlib",
                            "seaborn"
                        ]
                    }
                ],
                "channels": ["conda-forge"]
            }
            
            environment = Environment(
                name=env_name,
                description=env_description,
                conda_file=conda_file,
                image="mcr.microsoft.com/azureml/openmpi3.1.2-ubuntu18.04:latest"
            )
            
            env = self.ml_client.environments.create_or_update(environment)
            print(f"✓ Created environment: {env_name}")
            return True
            
        except Exception as e:
            print(f"✗ Error creating environment: {e}")
            return False
    
    def list_models(self) -> Optional[Dict[str, Any]]:
        """List registered models"""
        try:
            if not self.ml_client:
                print("✗ ML Client not initialized")
                return None
            
            models = {}
            
            for model in self.ml_client.models.list():
                models[model.name] = {
                    'version': model.version,
                    'description': model.description,
                    'creation_context': model.creation_context,
                    'tags': model.tags,
                    'flavors': model.flavors
                }
            
            print(f"✓ Found {len(models)} registered models")
            return models
            
        except Exception as e:
            print(f"✗ Error listing models: {e}")
            return None
    
    def register_model(self, model_name: str, model_path: str, model_description: str = "Retail trends analysis model") -> bool:
        """Register a new model"""
        try:
            if not self.ml_client:
                print("✗ ML Client not initialized")
                return False
            
            model = Model(
                name=model_name,
                path=model_path,
                description=model_description,
                type="custom_model"
            )
            
            registered_model = self.ml_client.models.create_or_update(model)
            print(f"✓ Registered model: {model_name}")
            print(f"  Version: {registered_model.version}")
            return True
            
        except Exception as e:
            print(f"✗ Error registering model: {e}")
            return False
    
    def list_datasets(self) -> Optional[Dict[str, Any]]:
        """List available datasets"""
        try:
            if not self.ml_client:
                print("✗ ML Client not initialized")
                return None
            
            datasets = {}
            
            for dataset in self.ml_client.data.list():
                datasets[dataset.name] = {
                    'version': dataset.version,
                    'description': dataset.description,
                    'creation_context': dataset.creation_context,
                    'tags': dataset.tags,
                    'type': dataset.type
                }
            
            print(f"✓ Found {len(datasets)} datasets")
            return datasets
            
        except Exception as e:
            print(f"✗ Error listing datasets: {e}")
            return None
    
    def create_dataset(self, dataset_name: str, data_path: str, dataset_description: str = "Retail trends dataset") -> bool:
        """Create a new dataset"""
        try:
            if not self.ml_client:
                print("✗ ML Client not initialized")
                return False
            
            dataset = Data(
                name=dataset_name,
                description=dataset_description,
                path=data_path,
                type="uri_file"
            )
            
            created_dataset = self.ml_client.data.create_or_update(dataset)
            print(f"✓ Created dataset: {dataset_name}")
            print(f"  Version: {created_dataset.version}")
            return True
            
        except Exception as e:
            print(f"✗ Error creating dataset: {e}")
            return False
    
    def submit_job(self, job_config: Dict[str, Any]) -> Optional[str]:
        """Submit a job to the workspace"""
        try:
            if not self.ml_client:
                print("✗ ML Client not initialized")
                return None
            
            from azure.ai.ml.entities import Command
            
            job = Command(
                code=job_config.get('code_path', './'),
                command=job_config.get('command', 'python train.py'),
                environment=job_config.get('environment', 'AzureML-sklearn-0.24-ubuntu18.04-py37-cpu'),
                compute=job_config.get('compute_target', 'cpu-cluster'),
                display_name=job_config.get('display_name', 'Retail Trends Analysis Job'),
                description=job_config.get('description', 'Training job for retail trends analysis'),
                tags=job_config.get('tags', {})
            )
            
            submitted_job = self.ml_client.jobs.create_or_update(job)
            print(f"✓ Job submitted: {submitted_job.name}")
            return submitted_job.name
            
        except Exception as e:
            print(f"✗ Error submitting job: {e}")
            return None

def connect_to_workspace() -> Optional[AzureMLWorkspace]:
    """Connect to Azure ML Workspace"""
    try:
        workspace = AzureMLWorkspace()
        if workspace.ml_client:
            return workspace
        else:
            return None
            
    except Exception as e:
        print(f"✗ Error connecting to workspace: {e}")
        return None

def main():
    """Main function to demonstrate Azure ML Workspace connection"""
    try:
        print("Connecting to Azure ML Workspace...")
        
        # Connect to workspace
        workspace = connect_to_workspace()
        
        if not workspace:
            print("✗ Failed to connect to Azure ML Workspace")
            return False
        
        print("\n=== Azure ML Workspace Information ===")
        
        # Get workspace info
        info = workspace.get_workspace_info()
        if info:
            print(f"Workspace Name: {info['name']}")
            print(f"Location: {info['location']}")
            print(f"Resource Group: {info['resource_group']}")
            print(f"Creation Time: {info['creation_time']}")
        
        # List compute targets
        print("\n=== Compute Targets ===")
        compute_targets = workspace.list_compute_targets()
        if compute_targets:
            for name, details in compute_targets.items():
                print(f"  {name}: {details['type']} ({details['state']})")
        
        # List environments
        print("\n=== Environments ===")
        environments = workspace.list_environments()
        if environments:
            for name, details in list(environments.items())[:5]:  # Show first 5
                print(f"  {name} (v{details['version']})")
        
        # List models
        print("\n=== Registered Models ===")
        models = workspace.list_models()
        if models:
            for name, details in models.items():
                print(f"  {name} (v{details['version']})")
        else:
            print("  No registered models found")
        
        # List datasets
        print("\n=== Datasets ===")
        datasets = workspace.list_datasets()
        if datasets:
            for name, details in datasets.items():
                print(f"  {name} (v{details['version']})")
        else:
            print("  No datasets found")
        
        print(f"\n✓ Azure ML Workspace connection successful!")
        return True
        
    except Exception as e:
        print(f"✗ Azure ML Workspace connection failed: {e}")
        return False

if __name__ == "__main__":
    main()
