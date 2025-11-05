#!/bin/bash
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}AKS Access Test - Deployment Script${NC}"
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo "Please create .env from .env.template and fill in your values."
    exit 1
fi

# Load environment variables
set -a
source .env
set +a

echo -e "${GREEN}✓ Loaded .env file${NC}"

# Validate required variables
if [ -z "$ACR_NAME" ] || [ -z "$ACR_USERNAME" ] || [ -z "$ACR_PASSWORD" ]; then
    echo -e "${RED}Error: ACR credentials not set in .env${NC}"
    exit 1
fi

if [ -z "$JIRA_URL" ] || [ -z "$JIRA_PERSONAL_TOKEN" ]; then
    echo -e "${RED}Error: Jira configuration not set in .env${NC}"
    exit 1
fi

if [ -z "$CONFLUENCE_URL" ] || [ -z "$CONFLUENCE_PERSONAL_TOKEN" ]; then
    echo -e "${RED}Error: Confluence configuration not set in .env${NC}"
    exit 1
fi

NAMESPACE=${NAMESPACE:-kagent}
IMAGE_TAG=${IMAGE_TAG:-v2}
IMAGE_NAME="${ACR_NAME}.azurecr.io/aks-access-test:${IMAGE_TAG}"

# Export for envsubst
export NAMESPACE
export IMAGE_TAG
export ACR_NAME

echo -e "${BLUE}Configuration:${NC}"
echo "  ACR: ${ACR_NAME}.azurecr.io"
echo "  Namespace: ${NAMESPACE}"
echo "  Image Tag: ${IMAGE_TAG}"
echo "  Full Image: ${IMAGE_NAME}"
echo ""

# Build Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
docker build -t aks-access-test:${IMAGE_TAG} .
echo -e "${GREEN}✓ Image built${NC}"
echo ""

# Tag image for ACR
echo -e "${YELLOW}Tagging image for ACR...${NC}"
docker tag aks-access-test:${IMAGE_TAG} "${IMAGE_NAME}"
echo -e "${GREEN}✓ Image tagged${NC}"
echo ""

# Login to ACR
echo -e "${YELLOW}Logging into ACR...${NC}"
echo "${ACR_PASSWORD}" | docker login "${ACR_NAME}.azurecr.io" -u "${ACR_USERNAME}" --password-stdin
echo -e "${GREEN}✓ Logged into ACR${NC}"
echo ""

# Push image
echo -e "${YELLOW}Pushing image to ACR...${NC}"
docker push "${IMAGE_NAME}"
echo -e "${GREEN}✓ Image pushed${NC}"
echo ""

# Create namespace if needed
echo -e "${YELLOW}Checking namespace '${NAMESPACE}'...${NC}"
if kubectl get namespace "${NAMESPACE}" >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Namespace exists${NC}"
else
    echo -e "${YELLOW}Creating namespace '${NAMESPACE}'...${NC}"
    kubectl create namespace "${NAMESPACE}"
    echo -e "${GREEN}✓ Namespace created${NC}"
fi
echo ""

# Create ACR image pull secret
echo -e "${YELLOW}Creating ACR image pull secret...${NC}"
kubectl create secret docker-registry acr-secret \
    --namespace="${NAMESPACE}" \
    --docker-server="${ACR_NAME}.azurecr.io" \
    --docker-username="${ACR_USERNAME}" \
    --docker-password="${ACR_PASSWORD}" \
    --dry-run=client -o yaml | kubectl apply -f -
echo -e "${GREEN}✓ ACR secret created${NC}"
echo ""

# Base64 encode secrets
export JIRA_URL_BASE64=$(echo -n "${JIRA_URL}" | base64)
export CONFLUENCE_URL_BASE64=$(echo -n "${CONFLUENCE_URL}" | base64)
export JIRA_PERSONAL_TOKEN_BASE64=$(echo -n "${JIRA_PERSONAL_TOKEN}" | base64)
export CONFLUENCE_PERSONAL_TOKEN_BASE64=$(echo -n "${CONFLUENCE_PERSONAL_TOKEN}" | base64)

# Deploy secret
echo -e "${YELLOW}Deploying secret...${NC}"
envsubst < secret.yaml | kubectl apply -f -
echo -e "${GREEN}✓ Secret deployed${NC}"
echo ""

# Deploy application
echo -e "${YELLOW}Deploying application...${NC}"
envsubst < deployment.yaml | kubectl apply -f -
echo -e "${GREEN}✓ Deployment created${NC}"
echo ""

# Wait for pod to be ready
echo -e "${YELLOW}Waiting for pod to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app=aks-access-test -n "${NAMESPACE}" --timeout=60s
echo -e "${GREEN}✓ Pod is ready${NC}"
echo ""

# Show logs
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Test Results (from pod logs):${NC}"
echo -e "${BLUE}============================================${NC}"
kubectl logs -n "${NAMESPACE}" -l app=aks-access-test --tail=100

echo ""
echo -e "${GREEN}Deployment complete!${NC}"
echo ""
echo "To view logs: kubectl logs -n ${NAMESPACE} -l app=aks-access-test -f"
echo "To delete: kubectl delete deployment aks-access-test -n ${NAMESPACE}"
echo "           kubectl delete secret aks-access-test-secrets -n ${NAMESPACE}"
