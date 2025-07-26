# Archived Documentation

This folder contains documentation that was removed from the main docs structure because it contained misleading or outdated information that could confuse developers.

## Archive Reasons

### `api-structure.md` (from docs/architecture/)
**Archived**: January 2025  
**Reason**: This document described a complete API structure with endpoints like `/content/`, `/users/`, complex schemas, and SDKs that were never implemented. The actual EduHub API is much simpler, focused on Auth0 OAuth2 integration and Plone bridging. This aspirational documentation would have misled new developers about the current system capabilities.

**Current Reality**: The actual API consists of:
- `/auth/*` endpoints for OAuth2 authentication
- `/plone/*` endpoints for legacy CMS integration  
- `/ ` root endpoint for basic API info
- FastAPI auto-generated `/docs` and `/openapi.json`

### Guidelines for Documentation

- ✅ **Document what exists** - Accurately reflect implemented features
- ❌ **Don't document aspirations** - Avoid describing planned/desired functionality as current
- 🔄 **Update regularly** - Keep docs in sync with actual implementation
- 📝 **Archive misleading content** - Remove docs that would confuse developers

---

*For current, accurate documentation, see the main `/docs/` folder structure.* 