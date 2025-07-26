# EduHub Documentation Hub

## 📚 Documentation Overview

This is the central hub for all EduHub project documentation. The docs are organized by audience and purpose to help you find exactly what you need.

## 🚨 Documentation Quality Notice

**Latest Update: January 2025** - A comprehensive documentation audit was completed to ensure all content accurately reflects the implemented system. Misleading or outdated documentation has been moved to the `archive/` folder.

### 📁 Archive Folder
The `docs/archive/` folder contains documentation that was removed from the main structure because it described unimplemented features or contained outdated information. See `docs/archive/ARCHIVE_NOTE.md` for details.

## 🎯 Quick Navigation by Role

### **👩‍💻 New Developer**
Start here to get productive quickly:
1. [`getting-started/developer-onboarding.md`](getting-started/developer-onboarding.md) - Essential setup guide
2. [`getting-started/authentication-setup.md`](getting-started/authentication-setup.md) - Auth0 configuration
3. [`development/testing-strategy.md`](development/testing-strategy.md) - Testing methodology

### **🏗️ System Architect**
Understand the technical decisions and system design:
1. [`architecture/system-architecture.md`](architecture/system-architecture.md) - Overall system design
2. [`architecture/tech-stack-overview.md`](architecture/tech-stack-overview.md) - Technology choices
3. [`architecture/plone-integration.md`](architecture/plone-integration.md) - Legacy system integration

### **📋 Project Manager**
Track progress and understand implementation approach:
1. [`/tasks/tasks-overall-project-plan.md`](../tasks/tasks-overall-project-plan.md) - High-level roadmap
2. [`project-history/phase-reports/`](project-history/phase-reports/) - Completed phase summaries
3. [`development/feature-planning-template.md`](development/feature-planning-template.md) - Planning methodology

### **🧪 QA Engineer**
Understand testing approach and quality standards:
1. [`development/testing-strategy.md`](development/testing-strategy.md) - Testing methodology
2. [`getting-started/authentication-setup.md`](getting-started/authentication-setup.md) - Auth testing procedures
3. [`/scripts/quick_integration_test.py`](../scripts/quick_integration_test.py) - Automated testing

## 📂 Documentation Structure

### **🚀 Getting Started**
Essential information for new team members:
- [`developer-onboarding.md`](getting-started/developer-onboarding.md) - Setup checklist and key facts
- [`authentication-setup.md`](getting-started/authentication-setup.md) - Auth0 configuration guide

### **🏗️ Architecture**
Technical design and system integration:
- [`system-architecture.md`](architecture/system-architecture.md) - Complete system design
- [`tech-stack-overview.md`](architecture/tech-stack-overview.md) - Technology stack details
- [`plone-integration.md`](architecture/plone-integration.md) - Legacy CMS integration
- [`deployment-strategy.md`](architecture/deployment-strategy.md) - Production deployment

### **💻 Development**
Development workflows and planning:
- [`testing-strategy.md`](development/testing-strategy.md) - Testing methodology and efficiency
- [`gui-development-plans.md`](development/gui-development-plans.md) - UI/UX strategy
- [`phase-4-planning.md`](development/phase-4-planning.md) - Next phase planning brief
- [`feature-planning-template.md`](development/feature-planning-template.md) - Universal planning template

### **📜 Project History**
Historical context and completed work:
- [`roadmap/`](project-history/roadmap/) - Original planning documents
- [`phase-reports/`](project-history/phase-reports/) - Completed phase summaries
- [`original-assignment/`](project-history/original-assignment/) - Initial requirements

## 🔍 Quick Reference

### **Current System Status (Phase 3 Complete)**
- ✅ **Auth0 OAuth2**: Complete authorization code flow with JWT validation
- ✅ **FastAPI Gateway**: Async Python API with auto-generated documentation
- ✅ **Plone Integration**: HTTP bridge with user mapping and role synchronization
- ✅ **Security Features**: Rate limiting, CORS, audit logging
- ✅ **Test Console**: Interactive authentication testing interface

### **Key Technical Decisions**
- **Authentication**: Auth0 OAuth2 (not custom implementation)
- **Backend**: FastAPI + httpx (not Django + SQLAlchemy)
- **Legacy Bridge**: HTTP API calls (not direct database access)
- **Frontend**: HTML templates (React planned for future)
- **Deployment**: Stateless design (no Redis/PostgreSQL currently required)

### **Next Phase**: CSV Schedule Importer
See [`development/phase-4-planning.md`](development/phase-4-planning.md) for detailed planning brief.

## 📋 Documentation Standards

### **Accuracy First**
- ✅ **Document what exists** - Only describe implemented features
- ❌ **Don't document aspirations** - No speculative or planned features as current
- 🔄 **Update with changes** - Keep docs synchronized with implementation
- 📝 **Archive outdated content** - Move misleading docs to archive

### **Audience-Focused**
- **New developers**: Setup guides and essential knowledge
- **Architects**: Technical decisions and system design
- **Project managers**: Progress tracking and planning
- **QA engineers**: Testing procedures and quality standards

### **Contributing Guidelines**
1. **Before documenting**: Verify the feature/process actually exists
2. **Use clear structure**: Follow existing document templates
3. **Test instructions**: Ensure setup guides work for new users
4. **Update related docs**: Keep cross-references current
5. **Consider archive**: Move outdated content rather than deleting

## 🔗 External Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Auth0 Documentation**: https://auth0.com/docs
- **Plone Documentation**: https://docs.plone.org/
- **API Documentation**: http://localhost:8000/docs (when server running)

## ❓ Getting Help

- **Setup Issues**: Check [`getting-started/authentication-setup.md`](getting-started/authentication-setup.md) troubleshooting
- **Technical Questions**: Review [`architecture/`](architecture/) documents
- **Testing Problems**: See [`development/testing-strategy.md`](development/testing-strategy.md)
- **Planning Questions**: Use [`development/feature-planning-template.md`](development/feature-planning-template.md)

---

**📝 Contributing**: When updating documentation, remember that accuracy and clarity are more valuable than comprehensiveness. Document what works, archive what doesn't, and help the next developer be productive quickly.
