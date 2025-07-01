# CI/CD Setup Guide for RAISE

This guide explains how to set up a Continuous Integration and Continuous Deployment (CI/CD) pipeline for the RAISE application using GitHub Actions.

## Benefits of CI/CD

### Continuous Integration (CI)
- **Automated Testing**: Runs tests automatically on every commit and pull request
- **Code Quality**: Ensures code meets quality standards before merging
- **Early Bug Detection**: Catches issues early in the development cycle
- **Consistent Environment**: Tests run in standardized environments
- **Faster Feedback**: Developers get immediate feedback on their changes

### Continuous Deployment (CD)
- **Automated Deployment**: Reduces manual deployment errors
- **Faster Releases**: Enables rapid and frequent deployments
- **Rollback Capability**: Easy to revert to previous versions if issues arise
- **Environment Consistency**: Ensures consistent deployments across environments
- **Reduced Downtime**: Automated deployments minimize service interruptions

## GitHub Actions Setup

### 1. Project Structure

Create the following directory structure in your repository:

```
.github/
├── workflows/
│   ├── backend-ci.yml      # Backend CI pipeline
│   ├── frontend-ci.yml     # Frontend CI pipeline
│   ├── deploy-staging.yml  # Staging deployment
│   └── deploy-production.yml # Production deployment
└── dependabot.yml          # Dependency updates
```

### 2. Backend CI Pipeline

#### `.github/workflows/backend-ci.yml`

```yaml
name: Backend CI

on:
  push:
    branches: [ main, develop ]
    paths: [ 'backend/**' ]
  pull_request:
    branches: [ main, develop ]
    paths: [ 'backend/**' ]

env:
  PYTHON_VERSION: '3.11'
  MONGODB_URI: mongodb://localhost:27017
  SECRET_KEY: test-secret-key-for-ci
  ENVIRONMENT: testing

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      mongodb:
        image: mongo:6.0
        ports:
          - 27017:27017
        options: >-
          --health-cmd "mongosh --eval 'db.adminCommand({ping: 1})'"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
        cache: 'pip'
    
    - name: Install dependencies
      working-directory: backend
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run linting
      working-directory: backend
      run: |
        pip install flake8 black isort
        # Stop the build if there are Python syntax errors or undefined names
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        # Check code formatting
        black --check .
        # Check import sorting
        isort --check-only .
    
    - name: Run type checking
      working-directory: backend
      run: |
        pip install mypy
        mypy app --ignore-missing-imports
    
    - name: Run tests
      working-directory: backend
      run: |
        pytest --cov=app --cov-report=xml --cov-report=term-missing
      env:
        MONGODB_URI: ${{ env.MONGODB_URI }}
        SECRET_KEY: ${{ env.SECRET_KEY }}
        ENVIRONMENT: ${{ env.ENVIRONMENT }}
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml
        flags: backend
        name: backend-coverage
    
    - name: Security scan
      working-directory: backend
      run: |
        pip install safety bandit
        # Check for known security vulnerabilities
        safety check
        # Run static security analysis
        bandit -r app/ -f json -o bandit-report.json || true
    
    - name: Upload security scan results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: security-scan-results
        path: backend/bandit-report.json

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Build Docker image
      working-directory: backend
      run: |
        docker build -t raise-backend:${{ github.sha }} .
    
    - name: Save Docker image
      if: github.ref == 'refs/heads/main'
      run: |
        docker save raise-backend:${{ github.sha }} | gzip > backend-image.tar.gz
    
    - name: Upload Docker image artifact
      if: github.ref == 'refs/heads/main'
      uses: actions/upload-artifact@v3
      with:
        name: backend-docker-image
        path: backend-image.tar.gz
        retention-days: 1
```

### 3. Frontend CI Pipeline

#### `.github/workflows/frontend-ci.yml`

```yaml
name: Frontend CI

on:
  push:
    branches: [ main, develop ]
    paths: [ 'src/**', 'public/**', 'package.json', 'package-lock.json' ]
  pull_request:
    branches: [ main, develop ]
    paths: [ 'src/**', 'public/**', 'package.json', 'package-lock.json' ]

env:
  NODE_VERSION: '18'

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: ${{ env.NODE_VERSION }}
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Run linting
      run: |
        npm run lint
        npm run type-check
    
    - name: Run tests
      run: npm run test:ci
      env:
        CI: true
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage/lcov.info
        flags: frontend
        name: frontend-coverage
    
    - name: Run security audit
      run: npm audit --audit-level=high
    
    - name: Check bundle size
      run: npm run build
      env:
        NEXT_PUBLIC_API_URL: http://localhost:8000
    
    - name: Upload build artifacts
      if: github.ref == 'refs/heads/main'
      uses: actions/upload-artifact@v3
      with:
        name: frontend-build
        path: .next/
        retention-days: 1

  accessibility:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: ${{ env.NODE_VERSION }}
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Build application
      run: npm run build
      env:
        NEXT_PUBLIC_API_URL: http://localhost:8000
    
    - name: Run accessibility tests
      run: |
        npm install -g @axe-core/cli
        npm start &
        sleep 30
        axe http://localhost:3000 --exit
```

### 4. Staging Deployment

#### `.github/workflows/deploy-staging.yml`

```yaml
name: Deploy to Staging

on:
  push:
    branches: [ develop ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: staging
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Deploy to staging server
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.STAGING_HOST }}
        username: ${{ secrets.STAGING_USERNAME }}
        key: ${{ secrets.STAGING_SSH_KEY }}
        script: |
          cd /opt/raise-staging
          git pull origin develop
          docker-compose down
          docker-compose build
          docker-compose up -d
          
          # Health check
          sleep 30
          curl -f http://localhost:8000/health || exit 1
    
    - name: Run smoke tests
      run: |
        # Add smoke tests for critical functionality
        curl -f ${{ secrets.STAGING_URL }}/health
        curl -f ${{ secrets.STAGING_URL }}/api/info
    
    - name: Notify Slack
      if: always()
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        channel: '#deployments'
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### 5. Production Deployment

#### `.github/workflows/deploy-production.yml`

```yaml
name: Deploy to Production

on:
  release:
    types: [published]
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to deploy'
        required: true
        default: 'latest'

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      with:
        ref: ${{ github.event.release.tag_name || github.event.inputs.version }}
    
    - name: Create deployment
      id: deployment
      uses: actions/github-script@v6
      with:
        script: |
          const deployment = await github.rest.repos.createDeployment({
            owner: context.repo.owner,
            repo: context.repo.repo,
            ref: context.ref,
            environment: 'production',
            required_contexts: []
          });
          return deployment.data.id;
    
    - name: Deploy to production
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.PRODUCTION_HOST }}
        username: ${{ secrets.PRODUCTION_USERNAME }}
        key: ${{ secrets.PRODUCTION_SSH_KEY }}
        script: |
          cd /opt/raise-production
          git fetch --tags
          git checkout ${{ github.event.release.tag_name || github.event.inputs.version }}
          
          # Backup database
          docker exec mongo-container mongodump --out /backup/$(date +%Y%m%d_%H%M%S)
          
          # Deploy with zero downtime
          docker-compose pull
          docker-compose up -d --no-deps backend
          sleep 30
          
          # Health check
          curl -f http://localhost:8000/health || exit 1
          
          # Update frontend
          docker-compose up -d --no-deps frontend
          sleep 15
          curl -f http://localhost:3000 || exit 1
    
    - name: Update deployment status (success)
      if: success()
      uses: actions/github-script@v6
      with:
        script: |
          await github.rest.repos.createDeploymentStatus({
            owner: context.repo.owner,
            repo: context.repo.repo,
            deployment_id: ${{ steps.deployment.outputs.result }},
            state: 'success',
            environment_url: '${{ secrets.PRODUCTION_URL }}'
          });
    
    - name: Update deployment status (failure)
      if: failure()
      uses: actions/github-script@v6
      with:
        script: |
          await github.rest.repos.createDeploymentStatus({
            owner: context.repo.owner,
            repo: context.repo.repo,
            deployment_id: ${{ steps.deployment.outputs.result }},
            state: 'failure'
          });
    
    - name: Rollback on failure
      if: failure()
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.PRODUCTION_HOST }}
        username: ${{ secrets.PRODUCTION_USERNAME }}
        key: ${{ secrets.PRODUCTION_SSH_KEY }}
        script: |
          cd /opt/raise-production
          git checkout main
          docker-compose up -d
    
    - name: Notify team
      if: always()
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        channel: '#deployments'
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
        text: |
          Production deployment ${{ job.status }}
          Version: ${{ github.event.release.tag_name || github.event.inputs.version }}
          URL: ${{ secrets.PRODUCTION_URL }}
```

### 6. Dependency Management

#### `.github/dependabot.yml`

```yaml
version: 2
updates:
  # Backend Python dependencies
  - package-ecosystem: "pip"
    directory: "/backend"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 5
    reviewers:
      - "team-backend"
    assignees:
      - "lead-developer"
    labels:
      - "dependencies"
      - "backend"
    
  # Frontend npm dependencies
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 5
    reviewers:
      - "team-frontend"
    assignees:
      - "lead-developer"
    labels:
      - "dependencies"
      - "frontend"
    
  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "monthly"
    labels:
      - "dependencies"
      - "github-actions"
```

## Environment Setup

### 1. GitHub Secrets

Configure the following secrets in your GitHub repository settings:

#### Staging Environment
```
STAGING_HOST=your-staging-server.com
STAGING_USERNAME=deploy
STAGING_SSH_KEY=<private-ssh-key>
STAGING_URL=https://staging.yourapp.com
```

#### Production Environment
```
PRODUCTION_HOST=your-production-server.com
PRODUCTION_USERNAME=deploy
PRODUCTION_SSH_KEY=<private-ssh-key>
PRODUCTION_URL=https://yourapp.com
```

#### Notifications
```
SLACK_WEBHOOK=https://hooks.slack.com/services/...
CODECOV_TOKEN=<codecov-token>
```

### 2. Environment Variables

#### Backend `.env` files

**Staging (.env.staging)**
```env
ENVIRONMENT=staging
DEBUG=false
SECRET_KEY=your-staging-secret-key
MONGODB_URI=mongodb://staging-db:27017
TOGETHER_AI_API_KEY=your-staging-api-key
ALLOWED_ORIGINS=https://staging.yourapp.com
SECURE_COOKIES=true
```

**Production (.env.production)**
```env
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-production-secret-key
MONGODB_URI=mongodb://production-db:27017
TOGETHER_AI_API_KEY=your-production-api-key
ALLOWED_ORIGINS=https://yourapp.com
SECURE_COOKIES=true
```

#### Frontend Environment Variables

**Staging**
```env
NEXT_PUBLIC_API_URL=https://staging-api.yourapp.com
NEXT_PUBLIC_ENVIRONMENT=staging
```

**Production**
```env
NEXT_PUBLIC_API_URL=https://api.yourapp.com
NEXT_PUBLIC_ENVIRONMENT=production
```

## Docker Configuration

### Backend Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Build application
COPY . .
RUN npm run build

# Production image
FROM node:18-alpine AS runner

WORKDIR /app

# Create non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy built application
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next

USER nextjs

EXPOSE 3000

CMD ["node", "server.js"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URI=mongodb://mongodb:27017
    depends_on:
      - mongodb
    restart: unless-stopped
    
  frontend:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend
    restart: unless-stopped
    
  mongodb:
    image: mongo:6.0
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

volumes:
  mongodb_data:
```

## Best Practices

### 1. Security
- Use secrets for sensitive information
- Implement proper access controls
- Regular security scanning
- Use HTTPS in production

### 2. Testing
- Run tests on every commit
- Maintain high test coverage
- Include integration tests
- Test deployment process

### 3. Monitoring
- Set up application monitoring
- Configure alerts for failures
- Track deployment metrics
- Monitor resource usage

### 4. Rollback Strategy
- Implement blue-green deployments
- Maintain database backups
- Test rollback procedures
- Document recovery processes

### 5. Documentation
- Document deployment processes
- Maintain runbooks
- Update README files
- Version all configurations

This CI/CD setup provides a robust foundation for developing, testing, and deploying the RAISE application with confidence and reliability.