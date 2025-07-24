# EduHub Deployment Instructions

This guide explains how to deploy the EduHub project to GitHub and validate the CI/CD pipeline.

## 🚀 GitHub Repository Setup

### 1. Create GitHub Repository
```bash
# Option A: Using GitHub CLI (recommended)
gh repo create eduhub --public --description "Modern education portal modernizing Plone CMS with FastAPI"

# Option B: Manual setup at https://github.com/new
# Repository name: eduhub
# Description: Modern education portal modernizing Plone CMS with FastAPI
# Visibility: Public (or Private)
```

### 2. Connect Local Repository
```bash
# Add GitHub remote (replace USERNAME with your GitHub username)
git remote add origin https://github.com/USERNAME/eduhub.git

# Push initial code
git branch -M main
git push -u origin main
```

### 3. Verify Repository Setup
- ✅ Code is visible in GitHub
- ✅ CI workflow appears in Actions tab
- ✅ README displays with badges (may show errors initially)

## 🔧 Configure GitHub Secrets

### Required Secrets (for full CI functionality)
Navigate to: **Repository Settings → Secrets and variables → Actions**

1. **`DOCKER_USERNAME`**
   - Your Docker Hub username
   - Example: `myusername`

2. **`DOCKER_PASSWORD`**  
   - Docker Hub personal access token (NOT password)
   - Generate at: Docker Hub → Account Settings → Security → Access Tokens
   - Permissions: Public Repo Write

### Optional Secrets
3. **`CODECOV_TOKEN`** (for enhanced coverage reporting)
   - Sign up at [codecov.io](https://codecov.io)
   - Add your repository and copy the token

## 🧪 CI Pipeline Validation

### Automatic Trigger
The CI pipeline will trigger automatically when you push to GitHub:
```bash
git push origin main
```

### Expected Results

#### ✅ Core Jobs (Must Pass)
| Job | Expected | Validation |
|-----|----------|------------|
| **Lint** | ✅ Pass | Black, isort, MyPy checks |
| **Test** | ✅ Pass | 63% coverage > 60% threshold |
| **Integration** | ✅ Pass | Plone-FastAPI bridge tests |
| **Build** | ✅ Pass | Python package validation |

#### ⚠️ Optional Jobs (May Warn)
| Job | Expected | Notes |
|-----|----------|-------|
| **Security** | ⚠️ Warnings OK | Safety/Bandit may flag issues |
| **Docker** | ⚠️ May fail | Requires Docker Hub secrets |

#### 🎯 Quality Gates
- **Core Gates**: Should evaluate as PASSED
- **Optional Gates**: Warnings acceptable  
- **Overall Pipeline**: Should complete successfully

### Manual Testing
You can also trigger the workflow manually:
1. Go to **Actions** tab in GitHub
2. Select **CI Pipeline** workflow
3. Click **Run workflow**
4. Choose branch and click **Run workflow**

## 📊 Monitoring CI Results

### GitHub Actions Interface
1. **Actions Tab**: View all workflow runs
2. **Job Details**: Click on individual jobs to see logs
3. **Quality Gates**: Check the final summary job

### Status Badge Updates
After successful CI run:
- [![CI Pipeline](https://img.shields.io/badge/CI-passing-brightgreen)](#) Should show "passing"
- Coverage badge will show actual percentage
- Quality gates badge should show "passing"

### Troubleshooting Common Issues

#### Docker Job Fails
```
Error: Username and password required
```
**Solution**: Add `DOCKER_USERNAME` and `DOCKER_PASSWORD` secrets

#### Quality Gates Fail
```
❌ GATE FAILED: Unit tests failed
```
**Solution**: Check test job logs, fix failing tests

#### Coverage Below Threshold
```
Coverage failure: total of X% is less than fail-under=60%
```
**Solution**: Add tests or adjust threshold in workflow

#### MyPy Errors
```
Found X errors in Y files
```
**Solution**: Fix type annotations or adjust MyPy settings

## 🔄 Continuous Updates

### Branch Protection (Optional)
Protect your main branch:
1. **Settings → Branches**
2. **Add rule** for `main` branch
3. **Require status checks**: Select CI jobs
4. **Require up-to-date branches**

### Quality Improvements
As your project grows:
1. **Increase coverage threshold**: 60% → 70% → 80%
2. **Enable strict MyPy**: Remove `--ignore-missing-imports`
3. **Add performance testing**: Load testing, benchmarks
4. **Security hardening**: SAST/DAST scanning

## 📋 Deployment Checklist

### Initial Setup
- [ ] GitHub repository created
- [ ] Local git repository connected
- [ ] Initial code pushed to main branch
- [ ] CI workflow visible in Actions tab

### Secrets Configuration  
- [ ] `DOCKER_USERNAME` secret added
- [ ] `DOCKER_PASSWORD` secret added (access token)
- [ ] `CODECOV_TOKEN` added (optional)

### CI Validation
- [ ] Pipeline triggered on push
- [ ] All core jobs pass (lint, test, integration, build)
- [ ] Quality gates evaluate correctly
- [ ] Status badges update (may take a few minutes)

### Documentation Updates
- [ ] Update README badges with correct repository URL
- [ ] Replace `USERNAME/REPO_NAME` placeholders
- [ ] Verify Mermaid diagrams render correctly
- [ ] Test all documentation links

## 🎯 Success Metrics

Your deployment is successful when:
- ✅ CI pipeline completes successfully
- ✅ All core quality gates pass
- ✅ README displays correctly with status badges
- ✅ Docker images build (if secrets configured)
- ✅ Coverage reports generate correctly

## 🆘 Getting Help

### Common Issues
- **CI failures**: Check `.github/QUALITY_GATES.md`
- **Docker issues**: Review `.github/SECRETS.md`
- **Test failures**: Run `pytest -v` locally
- **Format issues**: Run `black src tests && isort src tests`

### Support Resources
- **GitHub Actions docs**: https://docs.github.com/en/actions
- **FastAPI docs**: https://fastapi.tiangolo.com/
- **Docker Hub**: https://hub.docker.com/
- **Project issues**: GitHub Issues tab

---

**Ready to modernize education technology! 🚀** 