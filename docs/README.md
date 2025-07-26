# 📚 EduHub Documentation

Welcome to the EduHub documentation! This guide helps you find the information you need quickly and efficiently.

## 🧭 Quick Navigation

### 🚀 **New to EduHub?** Start Here:
- **[Developer Onboarding](getting-started/developer-onboarding.md)** - Essential setup guide for new developers
- **[Authentication Setup](getting-started/authentication-setup.md)** - OAuth2/Auth0 configuration guide
- **[Tech Stack Overview](getting-started/tech-stack-overview.md)** - Complete technology overview

### 🏗️ **Understanding the System?** Architecture:
- **[System Architecture](architecture/system-architecture.md)** - Core system design and integration patterns
- **[API Structure](architecture/api-structure.md)** - FastAPI endpoint organization and patterns
- **[Plone Integration](architecture/plone-integration.md)** - Legacy CMS integration strategy
- **[Deployment Strategy](architecture/deployment-strategy.md)** - Container deployment and infrastructure

### 👨‍💻 **Active Development?** Development Resources:
- **[Testing Strategy](development/testing-strategy.md)** - Automated testing methodology and efficiency rules
- **[Feature Planning Template](development/feature-planning-template.md)** - Universal template for planning new features
- **[Phase 4 Planning](development/phase-4-planning.md)** - Next phase (CSV Schedule Importer) planning brief
- **[GUI Development Plans](development/gui-development-plans.md)** - Frontend strategy and roadmap

### 📚 **Project Context?** Historical Documentation:
- **[Original Assignment](project-history/original-assignment/)** - G2P6 Enterprise Week specification
- **[Project Roadmap](project-history/roadmap/)** - Initial plans and feature analysis
- **[Phase Reports](project-history/phase-reports/)** - Completed phase summaries and benchmarks

---

## 📁 Directory Structure

```
docs/
├── README.md                          # 👈 You are here
├── getting-started/                   # 🚀 For new developers/users
│   ├── developer-onboarding.md       # Setup guide and repository overview
│   ├── authentication-setup.md       # OAuth2/Auth0 configuration
│   └── tech-stack-overview.md        # Technology choices and integration
├── architecture/                      # 🏗️ System design & technical decisions
│   ├── system-architecture.md        # Core architectural patterns
│   ├── api-structure.md             # FastAPI endpoint organization
│   ├── plone-integration.md         # Legacy CMS integration strategy
│   └── deployment-strategy.md       # Infrastructure and deployment
├── development/                       # 👨‍💻 Active development resources
│   ├── testing-strategy.md          # Automated testing methodology
│   ├── feature-planning-template.md # Universal feature planning template
│   ├── phase-4-planning.md         # CSV Schedule Importer planning
│   └── gui-development-plans.md     # Frontend strategy and roadmap
├── project-history/                  # 📚 Historical context & completed work
│   ├── original-assignment/         # G2P6 Enterprise Week specification
│   ├── roadmap/                     # Initial project plans and analysis
│   └── phase-reports/               # Completed phase documentation
└── archive/                          # 🗄️ Outdated/superseded documents
```

---

## 🎯 Documentation by Role

### **🆕 New Developer**
1. Start with **[Developer Onboarding](getting-started/developer-onboarding.md)**
2. Set up authentication: **[Authentication Setup](getting-started/authentication-setup.md)**
3. Understand the stack: **[Tech Stack Overview](getting-started/tech-stack-overview.md)**
4. Review architecture: **[System Architecture](architecture/system-architecture.md)**

### **🏗️ System Architect**
1. **[System Architecture](architecture/system-architecture.md)** - High-level design patterns
2. **[Plone Integration](architecture/plone-integration.md)** - Legacy system integration
3. **[Deployment Strategy](architecture/deployment-strategy.md)** - Infrastructure planning
4. **[Tech Stack Overview](getting-started/tech-stack-overview.md)** - Technology decisions

### **📋 Product Manager**
1. **[Project Roadmap](project-history/roadmap/initial-5day-plan.md)** - Original feature planning
2. **[Feature Analysis](project-history/roadmap/feature-analysis.md)** - Feature prioritization decisions
3. **[Phase 4 Planning](development/phase-4-planning.md)** - Next development phase
4. **[GUI Development Plans](development/gui-development-plans.md)** - Frontend strategy

### **🧪 QA Engineer**
1. **[Testing Strategy](development/testing-strategy.md)** - Automated testing approach
2. **[Authentication Setup](getting-started/authentication-setup.md)** - Testing OAuth flows
3. **[Performance Benchmarks](project-history/phase-reports/performance-benchmarks.md)** - Performance baselines

### **🚀 DevOps Engineer**
1. **[Deployment Strategy](architecture/deployment-strategy.md)** - Infrastructure requirements
2. **[System Architecture](architecture/system-architecture.md)** - Service dependencies
3. **[Tech Stack Overview](getting-started/tech-stack-overview.md)** - Runtime requirements

---

## 🏆 Project Status

### ✅ **Completed Phases**
- **Phase 1**: [Bootstrap & Initial Setup](project-history/phase-reports/phase-1-bootstrap-report.md)
- **Phase 2**: [Python 3.11 Upgrade](project-history/phase-reports/phase-2-python311-report.md)
- **Phase 3**: [OAuth2/SSO Gateway](getting-started/authentication-setup.md) ← **Current**

### 🔄 **In Progress**
- **Phase 4**: [CSV Schedule Importer](development/phase-4-planning.md) ← **Next**

### 📋 **Planned Features**
- Rich-Media Embeds (oEmbed)
- Open Data API Endpoints
- Role-Based Workflow Templates
- Real-Time Alert Broadcasting

---

## 🔍 Quick Reference

### **Common Tasks**
- **Set up development environment**: [Developer Onboarding](getting-started/developer-onboarding.md)
- **Configure Auth0**: [Authentication Setup](getting-started/authentication-setup.md)
- **Plan new feature**: [Feature Planning Template](development/feature-planning-template.md)
- **Run tests**: [Testing Strategy](development/testing-strategy.md)
- **Deploy system**: [Deployment Strategy](architecture/deployment-strategy.md)

### **Key Concepts**
- **Hybrid Architecture**: Modern FastAPI + Legacy Plone CMS
- **OAuth2 Gateway**: Auth0 integration with JWT tokens
- **Async HTTP Bridge**: PloneClient for legacy system integration
- **Progressive Enhancement**: HTML templates → React SPA migration

### **External Resources**
- **Auth0 Dashboard**: [dev-1fx6yhxxi543ipno.us.auth0.com](https://manage.auth0.com/dashboard/us/dev-1fx6yhxxi543ipno)
- **API Documentation**: `http://localhost:8000/docs` (when running locally)
- **Test Console**: `http://localhost:8000/test/auth-console`

---

## 💡 Contributing to Documentation

When adding new documentation:

1. **Follow the naming convention**: `kebab-case.md`
2. **Place in appropriate directory** based on content type
3. **Update this README** if adding new major sections
4. **Include clear headings** and table of contents for long documents
5. **Cross-reference related documents** using relative links

### **Documentation Standards**
- Use **clear, descriptive titles**
- Include **overview/summary** at the top
- Add **code examples** where relevant
- Maintain **consistent formatting** with existing docs
- **Test all links** before committing

---

*Last updated: Phase 3 completion (OAuth2/SSO Gateway)*
*Next update: Phase 4 planning (CSV Schedule Importer)*
