.PHONY: help deploy delete clean status logs port-forward check-env validate

# Default target
.DEFAULT_GOAL := help

# Color output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Load environment variables from .env file
ENV_FILE := .env
-include $(ENV_FILE)

# Export all variables for envsubst
export

# Set defaults for optional variables
NAMESPACE ?= default
TRANSPORT ?= streamable-http
PORT ?= 8000
HOST ?= 0.0.0.0
MCP_VERBOSE ?= true
JIRA_SSL_VERIFY ?= true
CONFLUENCE_SSL_VERIFY ?= true
REPLICAS ?= 1
IMAGE_TAG ?= latest
IMAGE_PULL_POLICY ?= Always
MEMORY_REQUEST ?= 128Mi
CPU_REQUEST ?= 100m
MEMORY_LIMIT ?= 512Mi
CPU_LIMIT ?= 500m

help: ## Display this help message
	@echo "$(BLUE)MCP Atlassian Kubernetes Deployment$(NC)"
	@echo ""
	@echo "$(GREEN)Available targets:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Usage:$(NC)"
	@echo "  1. Copy .env.template to .env and fill in your values"
	@echo "  2. Run 'make deploy' to deploy to Kubernetes"
	@echo "  3. Run 'make status' to check deployment status"
	@echo ""

check-env: ## Check if .env file exists and validate required variables
	@if [ ! -f "$(ENV_FILE)" ]; then \
		echo "$(RED)Error: $(ENV_FILE) file not found!$(NC)"; \
		echo ""; \
		echo "Please create $(ENV_FILE) from $(ENV_FILE).template:"; \
		echo "  cp $(ENV_FILE).template $(ENV_FILE)"; \
		echo ""; \
		echo "Then edit $(ENV_FILE) and fill in your Atlassian URLs and personal tokens."; \
		exit 1; \
	fi
	@echo "$(GREEN)✓ $(ENV_FILE) file found$(NC)"
	@# Validate required variables
	@if [ -z "$(JIRA_URL)" ]; then \
		echo "$(RED)Error: JIRA_URL is not set in $(ENV_FILE)$(NC)"; \
		exit 1; \
	fi
	@if [ -z "$(CONFLUENCE_URL)" ]; then \
		echo "$(RED)Error: CONFLUENCE_URL is not set in $(ENV_FILE)$(NC)"; \
		exit 1; \
	fi
	@if [ -z "$(JIRA_PERSONAL_TOKEN)" ]; then \
		echo "$(RED)Error: JIRA_PERSONAL_TOKEN is not set in $(ENV_FILE)$(NC)"; \
		exit 1; \
	fi
	@if [ -z "$(CONFLUENCE_PERSONAL_TOKEN)" ]; then \
		echo "$(RED)Error: CONFLUENCE_PERSONAL_TOKEN is not set in $(ENV_FILE)$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✓ All required variables are set$(NC)"

validate: check-env ## Validate the configuration
	@echo "$(BLUE)Configuration:$(NC)"
	@echo "  JIRA_URL:         $(JIRA_URL)"
	@echo "  CONFLUENCE_URL:   $(CONFLUENCE_URL)"
	@echo "  NAMESPACE:        $(NAMESPACE)"
	@echo "  REPLICAS:         $(REPLICAS)"
	@echo "  IMAGE_TAG:        $(IMAGE_TAG)"
	@echo "  TRANSPORT:        $(TRANSPORT)"
	@echo "  PORT:             $(PORT)"
	@echo ""

deploy: check-env ## Deploy MCP Atlassian to Kubernetes
	@echo "$(BLUE)Deploying MCP Atlassian to Kubernetes...$(NC)"
	@echo ""

	@# Check if namespace exists, create only if it doesn't
	@echo "$(YELLOW)Checking namespace '$(NAMESPACE)'...$(NC)"
	@if kubectl get namespace $(NAMESPACE) >/dev/null 2>&1; then \
		echo "$(GREEN)✓ Namespace '$(NAMESPACE)' already exists$(NC)"; \
	else \
		echo "$(YELLOW)Creating namespace '$(NAMESPACE)'...$(NC)"; \
		kubectl create namespace $(NAMESPACE); \
	fi
	@echo ""

	@# Base64 encode tokens for secret
	@echo "$(YELLOW)Creating Secret with personal tokens...$(NC)"
	@export JIRA_PERSONAL_TOKEN_BASE64=$$(echo -n "$(JIRA_PERSONAL_TOKEN)" | base64) && \
	export CONFLUENCE_PERSONAL_TOKEN_BASE64=$$(echo -n "$(CONFLUENCE_PERSONAL_TOKEN)" | base64) && \
	envsubst < secret.yaml | kubectl apply -f -
	@echo ""

	@# Apply ConfigMap
	@echo "$(YELLOW)Creating ConfigMap...$(NC)"
	@envsubst < configmap.yaml | kubectl apply -f -
	@echo ""

	@# Apply Deployment
	@echo "$(YELLOW)Creating Deployment...$(NC)"
	@envsubst < deployment.yaml | kubectl apply -f -
	@echo ""

	@# Apply Service
	@echo "$(YELLOW)Creating Service...$(NC)"
	@envsubst < service.yaml | kubectl apply -f -
	@echo ""

	@echo "$(GREEN)✓ Deployment complete!$(NC)"
	@echo ""
	@echo "Run '$(YELLOW)make status$(NC)' to check the deployment status"
	@echo "Run '$(YELLOW)make logs$(NC)' to view the logs"
	@echo ""

delete: ## Delete MCP Atlassian from Kubernetes
	@echo "$(YELLOW)Deleting MCP Atlassian from Kubernetes...$(NC)"
	@kubectl delete -n $(NAMESPACE) deployment mcp-atlassian --ignore-not-found=true
	@kubectl delete -n $(NAMESPACE) service mcp-atlassian --ignore-not-found=true
	@kubectl delete -n $(NAMESPACE) configmap mcp-atlassian-config --ignore-not-found=true
	@kubectl delete -n $(NAMESPACE) secret mcp-atlassian-secrets --ignore-not-found=true
	@echo "$(GREEN)✓ Deleted successfully$(NC)"

clean: delete ## Alias for delete

status: ## Check deployment status
	@echo "$(BLUE)MCP Atlassian Status:$(NC)"
	@echo ""
	@echo "$(YELLOW)Namespace:$(NC)"
	@kubectl get namespace $(NAMESPACE) 2>/dev/null || echo "  $(RED)Namespace '$(NAMESPACE)' not found$(NC)"
	@echo ""
	@echo "$(YELLOW)Deployment:$(NC)"
	@kubectl get -n $(NAMESPACE) deployment mcp-atlassian 2>/dev/null || echo "  $(RED)Deployment not found$(NC)"
	@echo ""
	@echo "$(YELLOW)Pods:$(NC)"
	@kubectl get -n $(NAMESPACE) pods -l app=mcp-atlassian 2>/dev/null || echo "  $(RED)No pods found$(NC)"
	@echo ""
	@echo "$(YELLOW)Service:$(NC)"
	@kubectl get -n $(NAMESPACE) service mcp-atlassian 2>/dev/null || echo "  $(RED)Service not found$(NC)"
	@echo ""
	@echo "$(YELLOW)ConfigMap:$(NC)"
	@kubectl get -n $(NAMESPACE) configmap mcp-atlassian-config 2>/dev/null || echo "  $(RED)ConfigMap not found$(NC)"
	@echo ""
	@echo "$(YELLOW)Secret:$(NC)"
	@kubectl get -n $(NAMESPACE) secret mcp-atlassian-secrets 2>/dev/null || echo "  $(RED)Secret not found$(NC)"
	@echo ""

logs: ## View logs from MCP Atlassian pods
	@echo "$(BLUE)MCP Atlassian Logs:$(NC)"
	@echo ""
	@kubectl logs -n $(NAMESPACE) -l app=mcp-atlassian --tail=100 -f

port-forward: ## Set up port forwarding to access MCP server locally
	@echo "$(BLUE)Setting up port forwarding...$(NC)"
	@echo ""
	@echo "$(GREEN)MCP Server will be accessible at:$(NC)"
	@echo "  http://localhost:8000/mcp"
	@echo "  http://localhost:8000/healthz"
	@echo ""
	@echo "$(YELLOW)Press Ctrl+C to stop port forwarding$(NC)"
	@echo ""
	@kubectl port-forward -n $(NAMESPACE) service/mcp-atlassian 8000:80

restart: ## Restart the deployment (rollout restart)
	@echo "$(YELLOW)Restarting MCP Atlassian deployment...$(NC)"
	@kubectl rollout restart -n $(NAMESPACE) deployment/mcp-atlassian
	@echo "$(GREEN)✓ Restart initiated$(NC)"
	@echo ""
	@echo "Run '$(YELLOW)make status$(NC)' to check the rollout status"

rollout-status: ## Check rollout status
	@echo "$(BLUE)Rollout Status:$(NC)"
	@kubectl rollout status -n $(NAMESPACE) deployment/mcp-atlassian

describe-pods: ## Describe pods for troubleshooting
	@echo "$(BLUE)Pod Details:$(NC)"
	@kubectl describe -n $(NAMESPACE) pods -l app=mcp-atlassian

events: ## Show recent events in the namespace
	@echo "$(BLUE)Recent Events:$(NC)"
	@kubectl get events -n $(NAMESPACE) --sort-by='.lastTimestamp' | tail -20

shell: ## Open a shell in the MCP Atlassian pod
	@echo "$(BLUE)Opening shell in MCP Atlassian pod...$(NC)"
	@kubectl exec -n $(NAMESPACE) -it deployment/mcp-atlassian -- sh

test-health: ## Test the health endpoint
	@echo "$(BLUE)Testing health endpoint...$(NC)"
	@echo ""
	@echo "$(YELLOW)Setting up temporary port forward...$(NC)"
	@kubectl port-forward -n $(NAMESPACE) service/mcp-atlassian 8000:80 > /dev/null 2>&1 & \
	PID=$$!; \
	sleep 2; \
	echo "$(YELLOW)Checking health endpoint...$(NC)"; \
	curl -s http://localhost:8000/healthz | jq . || curl -s http://localhost:8000/healthz; \
	echo ""; \
	kill $$PID 2>/dev/null || true
