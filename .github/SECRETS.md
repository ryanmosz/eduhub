# GitHub Actions Secrets Configuration

This document describes the required GitHub Actions secrets for the EduHub CI/CD pipeline.

## Required Secrets

### Docker Registry Secrets

The CI pipeline pushes Docker images to Docker Hub. Configure these secrets in your GitHub repository:

1. **`DOCKER_USERNAME`**
   - **Description**: Docker Hub username for image publishing
   - **Value**: Your Docker Hub username
   - **Usage**: Used to authenticate with Docker Hub registry
   - **Example**: `myusername`

2. **`DOCKER_PASSWORD`**
   - **Description**: Docker Hub personal access token (NOT your password)
   - **Value**: Generate a personal access token from Docker Hub
   - **Security**: Use personal access tokens instead of passwords for better security
   - **Setup Instructions**:
     1. Go to Docker Hub → Account Settings → Security
     2. Create new Access Token with "Public Repo Write" permissions
     3. Copy the token and add it as this secret

### Optional Deployment Secrets

For future deployment automation, you may need:

3. **`CODECOV_TOKEN`** (Optional)
   - **Description**: Codecov token for coverage reporting
   - **Value**: Generate from codecov.io for your repository
   - **Usage**: Enhanced coverage reporting and PR comments

4. **`DEPLOY_SSH_KEY`** (Future use)
   - **Description**: SSH private key for deployment servers
   - **Value**: Private key content (if using SSH deployment)
   - **Security**: Use dedicated deployment keys, not personal keys

5. **`DEPLOY_HOST`** (Future use)
   - **Description**: Deployment server hostname
   - **Value**: Your deployment server domain/IP
   - **Usage**: Server address for automated deployments

## How to Configure Secrets

### In GitHub Repository

1. Navigate to your repository on GitHub
2. Go to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Enter the secret name (e.g., `DOCKER_USERNAME`)
5. Enter the secret value
6. Click **Add secret**

### Security Best Practices

- ✅ **Use personal access tokens** instead of passwords
- ✅ **Limit token permissions** to minimum required scope
- ✅ **Rotate tokens regularly** (every 6-12 months)
- ✅ **Use organization secrets** for shared repositories
- ❌ **Never commit secrets** to code or logs
- ❌ **Don't use personal passwords** as secret values

## Testing Without Secrets

The CI pipeline is designed to work without secrets:

- **Pull Requests**: Docker images are built but not pushed
- **Forks**: Secrets are not available, pipeline skips push steps
- **Development**: All quality checks run without requiring secrets

## Secret Validation

To verify your secrets are working:

1. Check that `DOCKER_USERNAME` and `DOCKER_PASSWORD` are set
2. Trigger a workflow on the main branch
3. Monitor the "Docker Build & Push" job
4. Verify successful authentication and image push

## Troubleshooting

### Common Issues

**Authentication Failed**:
- Verify `DOCKER_USERNAME` matches your Docker Hub username exactly
- Ensure `DOCKER_PASSWORD` is an access token, not your account password
- Check token has correct permissions (Public Repo Write)

**Image Push Failed**:
- Verify repository name in secrets matches the expected format
- Check Docker Hub repository exists and is accessible
- Ensure sufficient storage quota on Docker Hub

**Missing Secrets**:
- The workflow will skip push steps if secrets are missing
- Check repository settings → secrets to verify configuration
- Organization-level secrets may override repository secrets

## Environment-Specific Configuration

### Development/Staging
```yaml
DOCKER_USERNAME: myusername
DOCKER_PASSWORD: dckr_pat_xxxxx (access token)
```

### Production  
```yaml
DOCKER_USERNAME: myorg
DOCKER_PASSWORD: dckr_pat_yyyyy (org access token)
CODECOV_TOKEN: xxxxx-xxxx-xxxx (optional)
```

## Workflow Integration

The secrets are used in the CI workflow as follows:

```yaml
- name: Log in to Docker Hub
  if: github.event_name != 'pull_request'
  uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKER_USERNAME }}
    password: ${{ secrets.DOCKER_PASSWORD }}
```

This ensures:
- Secrets are only used on push events (not PRs)
- Failed authentication doesn't block the entire pipeline
- Docker images can still be built and tested without secrets 