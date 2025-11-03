# Kubernetes Deployment for MCP Atlassian

This directory contains Kubernetes manifests and automation for deploying the MCP Atlassian server using personal token authentication for Server/Data Center deployments.

## Prerequisites

- Kubernetes cluster (v1.19+)
- `kubectl` configured to access your cluster
- `make` installed on your system
- `envsubst` (usually comes with `gettext` package)
- Personal Access Tokens for Jira and Confluence Server/Data Center

## Quick Start (Automated with Makefile)

1. **Create your environment configuration:**
   ```bash
   cd k8s
   cp .env.template .env
   ```

2. **Edit `.env` and fill in your values:**
   ```bash
   # Required
   JIRA_URL=https://jira.example.com
   CONFLUENCE_URL=https://confluence.example.com
   JIRA_PERSONAL_TOKEN=your-jira-token
   CONFLUENCE_PERSONAL_TOKEN=your-confluence-token
   NAMESPACE=default
   ```

3. **Deploy to Kubernetes:**
   ```bash
   make deploy
   ```

4. **Check deployment status:**
   ```bash
   make status
   ```

5. **View logs:**
   ```bash
   make logs
   ```

6. **Access locally:**
   ```bash
   make port-forward
   # Then visit http://localhost:8000/healthz
   ```

That's it! See the [Makefile Targets](#makefile-targets) section below for more commands.

## Makefile Targets

The Makefile provides convenient commands for managing your deployment:

| Command | Description |
|---------|-------------|
| `make help` | Display available targets and usage information |
| `make validate` | Validate configuration in .env file |
| `make deploy` | Deploy all resources to Kubernetes |
| `make delete` | Delete all resources from Kubernetes |
| `make clean` | Alias for delete |
| `make status` | Check deployment status |
| `make logs` | View logs from MCP Atlassian pods (follow mode) |
| `make port-forward` | Set up port forwarding for local access |
| `make restart` | Restart the deployment (rollout restart) |
| `make rollout-status` | Check rollout status |
| `make describe-pods` | Describe pods for troubleshooting |
| `make events` | Show recent events in the namespace |
| `make shell` | Open a shell in the MCP Atlassian pod |
| `make test-health` | Test the health endpoint |

## Generating Personal Access Tokens

### For Jira Server/Data Center:
1. Log in to your Jira instance
2. Click on your profile icon → Settings
3. Navigate to "Personal Access Tokens" (under Security)
4. Click "Create token"
5. Give it a name (e.g., "MCP Atlassian K8s")
6. Copy the generated token (you won't be able to see it again)

### For Confluence Server/Data Center:
1. Log in to your Confluence instance
2. Click on your profile icon → Settings
3. Navigate to "Personal Access Tokens" (under Security)
4. Click "Create token"
5. Give it a name (e.g., "MCP Atlassian K8s")
6. Copy the generated token (you won't be able to see it again)

## Configuration

All configuration is managed through the `.env` file. Copy `.env.template` to `.env` and customize:

### Required Variables:
```bash
JIRA_URL=https://jira.example.com
CONFLUENCE_URL=https://confluence.example.com
JIRA_PERSONAL_TOKEN=your-token
CONFLUENCE_PERSONAL_TOKEN=your-token
NAMESPACE=default
```

### Optional Variables:
```bash
# Deployment
REPLICAS=1
IMAGE_TAG=latest
IMAGE_PULL_POLICY=Always

# Resources
MEMORY_REQUEST=128Mi
CPU_REQUEST=100m
MEMORY_LIMIT=512Mi
CPU_LIMIT=500m

# Logging
MCP_VERBOSE=true
MCP_VERY_VERBOSE=false

# Access Control
READ_ONLY_MODE=false
CONFLUENCE_SPACES_FILTER=SPACE1,SPACE2
JIRA_PROJECTS_FILTER=PROJ1,PROJ2

# SSL
JIRA_SSL_VERIFY=true
CONFLUENCE_SSL_VERIFY=true
```

The Makefile automatically:
- Validates that .env exists and contains required variables
- Creates the namespace if it doesn't exist
- Base64 encodes your tokens for the Kubernetes Secret
- Substitutes all environment variables into the manifests
- Applies all resources in the correct order

**IMPORTANT**: Never commit your `.env` file to version control!

## Manual Deployment (Without Makefile)

If you prefer to deploy manually without the Makefile:

1. **Set environment variables:**
   ```bash
   export JIRA_URL=https://jira.example.com
   export CONFLUENCE_URL=https://confluence.example.com
   export JIRA_PERSONAL_TOKEN=your-token
   export CONFLUENCE_PERSONAL_TOKEN=your-token
   export NAMESPACE=default
   export TRANSPORT=streamable-http
   export PORT=8000
   export HOST=0.0.0.0
   export MCP_VERBOSE=true
   export REPLICAS=1
   export IMAGE_TAG=latest
   export IMAGE_PULL_POLICY=Always
   export MEMORY_REQUEST=128Mi
   export CPU_REQUEST=100m
   export MEMORY_LIMIT=512Mi
   export CPU_LIMIT=500m
   ```

2. **Create namespace:**
   ```bash
   kubectl create namespace $NAMESPACE
   ```

3. **Create resources with envsubst:**
   ```bash
   # Base64 encode tokens
   export JIRA_PERSONAL_TOKEN_BASE64=$(echo -n "$JIRA_PERSONAL_TOKEN" | base64)
   export CONFLUENCE_PERSONAL_TOKEN_BASE64=$(echo -n "$CONFLUENCE_PERSONAL_TOKEN" | base64)

   # Apply manifests
   envsubst < configmap.yaml | kubectl apply -f -
   envsubst < secret.yaml | kubectl apply -f -
   envsubst < deployment.yaml | kubectl apply -f -
   envsubst < service.yaml | kubectl apply -f -
   ```

4. **Verify deployment:**
   ```bash
   kubectl get pods -n $NAMESPACE -l app=mcp-atlassian
   kubectl logs -n $NAMESPACE -l app=mcp-atlassian
   ```

## Accessing the MCP Server

### From within the cluster

The MCP server is available at:
- **Service URL**: `http://mcp-atlassian.<namespace>.svc.cluster.local`
- **MCP Endpoint**: `http://mcp-atlassian.<namespace>.svc.cluster.local/mcp`
- **Health Check**: `http://mcp-atlassian.<namespace>.svc.cluster.local/healthz`

(Replace `<namespace>` with your actual namespace)

### From outside the cluster (Port Forward)

Using Makefile:
```bash
make port-forward
# Then access http://localhost:8000/mcp
```

Or manually:
```bash
kubectl port-forward -n $NAMESPACE svc/mcp-atlassian 8000:80
# Then access http://localhost:8000/mcp
```

### Using an Ingress (Optional)

If you need external access, create an Ingress resource:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: mcp-atlassian
  namespace: ${NAMESPACE}
  annotations:
    # Add your ingress controller specific annotations
    # Example for nginx:
    # nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: mcp-atlassian.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: mcp-atlassian
            port:
              number: 80
```

## Architecture

```
┌─────────────────────────────────────────────┐
│         Kubernetes Cluster                  │
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │  ConfigMap: mcp-atlassian-config      │ │
│  │  - Jira/Confluence URLs               │ │
│  │  - Transport settings                 │ │
│  └───────────────────────────────────────┘ │
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │  Secret: mcp-atlassian-secrets        │ │
│  │  - Jira Personal Token                │ │
│  │  - Confluence Personal Token          │ │
│  └───────────────────────────────────────┘ │
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │  Deployment: mcp-atlassian            │ │
│  │  ┌─────────────────────────────────┐  │ │
│  │  │  Pod: mcp-atlassian-xxxxx       │  │ │
│  │  │  ┌───────────────────────────┐  │  │ │
│  │  │  │ Container: mcp-atlassian  │  │  │ │
│  │  │  │ Port: 8000               │  │  │ │
│  │  │  │ Health: /healthz         │  │  │ │
│  │  │  └───────────────────────────┘  │  │ │
│  │  └─────────────────────────────────┘  │ │
│  └───────────────────────────────────────┘ │
│                   │                         │
│  ┌────────────────▼──────────────────────┐ │
│  │  Service: mcp-atlassian               │ │
│  │  Type: ClusterIP                      │ │
│  │  Port: 80 → 8000                      │ │
│  └───────────────────────────────────────┘ │
│                                             │
└─────────────────────────────────────────────┘
```

## Configuration Options

All configuration is managed through the `.env` file. See `.env.template` for a complete list of available options.

### Key Configuration Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `JIRA_URL` | (required) | Jira Server/DC URL |
| `CONFLUENCE_URL` | (required) | Confluence Server/DC URL |
| `JIRA_PERSONAL_TOKEN` | (required) | Jira personal access token |
| `CONFLUENCE_PERSONAL_TOKEN` | (required) | Confluence personal access token |
| `NAMESPACE` | `default` | Kubernetes namespace |
| `TRANSPORT` | `streamable-http` | Transport mode |
| `PORT` | `8000` | HTTP server port |
| `MCP_VERBOSE` | `true` | Enable verbose logging |
| `REPLICAS` | `1` | Number of replicas |
| `MEMORY_REQUEST` | `128Mi` | Memory request |
| `MEMORY_LIMIT` | `512Mi` | Memory limit |
| `CPU_REQUEST` | `100m` | CPU request |
| `CPU_LIMIT` | `500m` | CPU limit |

See `.env.template` for additional optional variables including SSL verification, content filtering, and proxy settings.

## Troubleshooting

### Pods not starting

```bash
# Using Makefile
make status
make describe-pods
make events

# Or manually
kubectl describe pod -n $NAMESPACE -l app=mcp-atlassian
kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp'
```

### Authentication errors

```bash
# Check logs for auth errors
make logs

# Verify secrets exist
kubectl get secret -n $NAMESPACE mcp-atlassian-secrets
kubectl describe secret -n $NAMESPACE mcp-atlassian-secrets
```

### Connection issues to Atlassian

```bash
# Check if URLs are correct in ConfigMap
kubectl get configmap -n $NAMESPACE mcp-atlassian-config -o yaml

# Test connectivity from within the pod
make shell
# Inside pod: wget -O- $JIRA_URL
```

### Health check failures

```bash
# Test health endpoint
make test-health

# Or manually
make port-forward
# In another terminal:
curl -v http://localhost:8000/healthz

# Check container logs
make logs
```

### Configuration issues

```bash
# Validate your .env configuration
make validate

# Check deployed configuration
kubectl get configmap -n $NAMESPACE mcp-atlassian-config -o yaml
```

## Scaling

To scale the deployment:

**Option 1: Update .env and redeploy**
```bash
# Edit .env and change REPLICAS
REPLICAS=3

# Redeploy
make deploy
```

**Option 2: Scale directly**
```bash
kubectl scale deployment -n $NAMESPACE mcp-atlassian --replicas=3
```

**Note**: The MCP Atlassian server is stateless when using personal tokens, so it can be scaled horizontally without issues.

## Cleanup

Using Makefile:
```bash
make delete
# or
make clean
```

Or manually:
```bash
kubectl delete -n $NAMESPACE deployment mcp-atlassian
kubectl delete -n $NAMESPACE service mcp-atlassian
kubectl delete -n $NAMESPACE configmap mcp-atlassian-config
kubectl delete -n $NAMESPACE secret mcp-atlassian-secrets
```

## Security Considerations

1. **Environment File**: Never commit `.env` file to version control - it's already in `.gitignore`
2. **Secrets Management**: Consider using external secrets management (e.g., Sealed Secrets, External Secrets Operator, Vault)
3. **Network Policies**: Add NetworkPolicy to restrict traffic
4. **RBAC**: Create ServiceAccount with minimal permissions
5. **Token Rotation**: Regularly rotate personal access tokens
6. **SSL Verification**: Keep SSL verification enabled unless absolutely necessary
7. **Read-Only Mode**: Enable if only read operations are needed by setting `READ_ONLY_MODE=true` in `.env`
8. **Namespace Isolation**: Use dedicated namespace for better isolation

## Files

- **`.env.template`** - Template for environment variables (safe to commit)
- **`.env`** - Your actual configuration (DO NOT COMMIT - listed in .gitignore)
- **`Makefile`** - Automation for deployment and management
- **`configmap.yaml`** - ConfigMap template with variable substitution
- **`secret.yaml`** - Secret template with variable substitution
- **`deployment.yaml`** - Deployment template with variable substitution
- **`service.yaml`** - Service template with variable substitution
- **`README.md`** - This documentation

## Additional Resources

- [MCP Atlassian Documentation](https://github.com/sooperset/mcp-atlassian)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Atlassian Personal Access Tokens](https://confluence.atlassian.com/enterprise/using-personal-access-tokens-1026032365.html)
- [Model Context Protocol](https://modelcontextprotocol.io/)
