#!/bin/bash

# Azure Deployment Script for Retail Trends Analysis Platform
# This script deploys all required Azure resources using ARM templates

set -e

# Configuration
PROJECT_NAME="retail-trends"
LOCATION="eastus"
RESOURCE_GROUP="${PROJECT_NAME}-rg"
TEMPLATE_FILE="azure_deployment_template.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Azure CLI is installed
check_azure_cli() {
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI is not installed. Please install it from https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        exit 1
    fi
    print_status "Azure CLI is installed"
}

# Function to check if user is logged in
check_login() {
    if ! az account show &> /dev/null; then
        print_error "You are not logged in to Azure. Please run 'az login' first."
        exit 1
    fi
    print_status "User is logged in to Azure"
}

# Function to create resource group
create_resource_group() {
    print_status "Creating resource group: $RESOURCE_GROUP"
    az group create --name $RESOURCE_GROUP --location $LOCATION --output table
}

# Function to deploy ARM template
deploy_template() {
    print_status "Deploying Azure resources..."
    
    DEPLOYMENT_NAME="${PROJECT_NAME}-deployment-$(date +%Y%m%d%H%M%S)"
    
    az deployment group create \
        --resource-group $RESOURCE_GROUP \
        --template-file $TEMPLATE_FILE \
        --parameters projectName=$PROJECT_NAME location=$LOCATION \
        --name $DEPLOYMENT_NAME \
        --output table
    
    print_status "Deployment completed: $DEPLOYMENT_NAME"
}

# Function to get deployment outputs
get_outputs() {
    print_status "Getting deployment outputs..."
    
    # Get the latest deployment
    DEPLOYMENT_NAME=$(az deployment group list --resource-group $RESOURCE_GROUP --query "[0].name" --output tsv)
    
    # Get outputs
    STORAGE_NAME=$(az deployment group show --resource-group $RESOURCE_GROUP --name $DEPLOYMENT_NAME --query "properties.outputs.storageAccountName.value" --output tsv)
    TEXT_ANALYTICS_NAME=$(az deployment group show --resource-group $RESOURCE_GROUP --name $DEPLOYMENT_NAME --query "properties.outputs.textAnalyticsName.value" --output tsv)
    ML_WORKSPACE_NAME=$(az deployment group show --resource-group $RESOURCE_GROUP --name $DEPLOYMENT_NAME --query "properties.outputs.mlWorkspaceName.value" --output tsv)
    FUNCTION_APP_NAME=$(az deployment group show --resource-group $RESOURCE_GROUP --name $DEPLOYMENT_NAME --query "properties.outputs.functionAppName.value" --output tsv)
    
    # Get connection string and keys
    STORAGE_CONNECTION_STRING=$(az deployment group show --resource-group $RESOURCE_GROUP --name $DEPLOYMENT_NAME --query "properties.outputs.storageConnectionString.value" --output tsv)
    TEXT_ANALYTICS_KEY=$(az deployment group show --resource-group $RESOURCE_GROUP --name $DEPLOYMENT_NAME --query "properties.outputs.textAnalyticsKey.value" --output tsv)
    TEXT_ANALYTICS_ENDPOINT=$(az deployment group show --resource-group $RESOURCE_GROUP --name $DEPLOYMENT_NAME --query "properties.outputs.textAnalyticsEndpoint.value" --output tsv)
    
    # Get subscription ID
    SUBSCRIPTION_ID=$(az account show --query id --output tsv)
    
    print_status "Deployment outputs retrieved"
}

# Function to create .env file
create_env_file() {
    print_status "Creating .env file with Azure credentials..."
    
    cat > .env << EOF
# Azure Storage Account
AZURE_STORAGE_CONNECTION_STRING="$STORAGE_CONNECTION_STRING"

# Azure AI Language Service (Text Analytics)
AZURE_AI_LANGUAGE_KEY="$TEXT_ANALYTICS_KEY"
AZURE_AI_LANGUAGE_ENDPOINT="$TEXT_ANALYTICS_ENDPOINT"

# Azure OpenAI (Optional - configure manually if needed)
AZURE_OPENAI_API_KEY=""
AZURE_OPENAI_ENDPOINT=""
AZURE_OPENAI_DEPLOYMENT_NAME=""

# Azure Machine Learning Workspace
AZURE_SUBSCRIPTION_ID="$SUBSCRIPTION_ID"
AZURE_RESOURCE_GROUP="$RESOURCE_GROUP"
AZURE_WORKSPACE_NAME="$ML_WORKSPACE_NAME"

# Azure Functions Configuration
CONTAINER_NAME="project-data"
OUTPUT_CONTAINER="processed-data"

# Local Development Settings
DEBUG=True
LOCAL_FALLBACK=True
EOF
    
    print_status ".env file created successfully"
}

# Function to set up Key Vault access
setup_key_vault_access() {
    print_status "Setting up Key Vault access permissions..."
    
    # Get current user object ID
    USER_OBJECT_ID=$(az ad signed-in-user show --query objectId --output tsv)
    
    # Set Key Vault access policy
    az keyvault set-policy \
        --name $KEY_VAULT_NAME \
        --object-id $USER_OBJECT_ID \
        --secret-permissions get list set delete \
        --output table
    
    print_status "Key Vault access configured"
}

# Function to validate deployment
validate_deployment() {
    print_status "Validating deployment..."
    
    # Check if resources exist
    if az storage account show --name $STORAGE_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
        print_status "✓ Storage Account: $STORAGE_NAME"
    else
        print_error "✗ Storage Account not found"
    fi
    
    if az cognitiveservices account show --name $TEXT_ANALYTICS_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
        print_status "✓ Text Analytics: $TEXT_ANALYTICS_NAME"
    else
        print_error "✗ Text Analytics not found"
    fi
    
    if az ml workspace show --name $ML_WORKSPACE_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
        print_status "✓ ML Workspace: $ML_WORKSPACE_NAME"
    else
        print_error "✗ ML Workspace not found"
    fi
    
    if az functionapp show --name $FUNCTION_APP_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
        print_status "✓ Function App: $FUNCTION_APP_NAME"
    else
        print_error "✗ Function App not found"
    fi
}

# Function to display summary
display_summary() {
    print_status "Deployment Summary:"
    echo "===================="
    echo "Resource Group: $RESOURCE_GROUP"
    echo "Location: $LOCATION"
    echo "Storage Account: $STORAGE_NAME"
    echo "Text Analytics: $TEXT_ANALYTICS_NAME"
    echo "ML Workspace: $ML_WORKSPACE_NAME"
    echo "Function App: $FUNCTION_APP_NAME"
    echo "===================="
    echo ""
    print_status "Next steps:"
    echo "1. Install Python dependencies: pip install -r requirements.txt"
    echo "2. Test the configuration: python azure_integration/config.py"
    echo "3. Generate data: python generate_data.py"
    echo "4. Run trend analysis: python trend_analysis.py"
    echo "5. Deploy Azure Functions: func azure functionapp publish $FUNCTION_APP_NAME"
}

# Function to clean up resources
cleanup() {
    print_warning "This will delete all resources in the resource group: $RESOURCE_GROUP"
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Deleting resource group: $RESOURCE_GROUP"
        az group delete --name $RESOURCE_GROUP --yes --no-wait
        print_status "Resource group deletion initiated"
    else
        print_status "Cleanup cancelled"
    fi
}

# Main function
main() {
    print_status "Starting Azure deployment for Retail Trends Analysis Platform"
    print_status "Project: $PROJECT_NAME"
    print_status "Location: $LOCATION"
    print_status "Resource Group: $RESOURCE_GROUP"
    echo ""
    
    # Check prerequisites
    check_azure_cli
    check_login
    
    # Check if template file exists
    if [ ! -f "$TEMPLATE_FILE" ]; then
        print_error "Template file not found: $TEMPLATE_FILE"
        exit 1
    fi
    
    # Create resource group
    create_resource_group
    
    # Deploy template
    deploy_template
    
    # Get outputs
    get_outputs
    
    # Create .env file
    create_env_file
    
    # Validate deployment
    validate_deployment
    
    # Display summary
    display_summary
    
    print_status "Deployment completed successfully!"
}

# Handle command line arguments
case "${1:-}" in
    "deploy")
        main
        ;;
    "cleanup")
        cleanup
        ;;
    "validate")
        check_azure_cli
        check_login
        get_outputs
        validate_deployment
        ;;
    *)
        echo "Usage: $0 {deploy|cleanup|validate}"
        echo ""
        echo "Commands:"
        echo "  deploy   - Deploy all Azure resources"
        echo "  cleanup  - Delete all Azure resources"
        echo "  validate - Validate existing deployment"
        echo ""
        echo "Example: $0 deploy"
        exit 1
        ;;
esac
