# Testing Strategy & Efficiency Guidelines

## Core Principle: **Automate Before Asking**

**CRITICAL RULE**: Before requesting any manual testing from the user, MUST re-evaluate if the test can be automated programmatically. Manual testing is a major efficiency blocker and should only be used as a last resort.

## Testing Hierarchy (Preference Order)

### 1. **Programmatic Unit Tests** ⭐ (PREFERRED)
- **When**: Testing individual functions, classes, data models
- **Tools**: Python test scripts, pytest, direct function calls
- **Benefits**: Fast, repeatable, no external dependencies
- **Example**: Testing `generate_plone_username()`, `extract_roles_from_auth0()`

```python
# Example: test_integration.py
python test_integration.py  # Tests core logic without external services
```

### 2. **API Testing with curl/httpx** ⭐ (PREFERRED)
- **When**: Testing HTTP endpoints, authentication flows
- **Tools**: `curl`, `httpx`, `requests`
- **Benefits**: Tests real API behavior without browser
- **Example**: Testing auth endpoints programmatically

```bash
# Test server health
curl http://localhost:8000/

# Test auth endpoints (when JWT available)
curl -H "Authorization: Bearer $JWT_TOKEN" http://localhost:8000/auth/user
```

### 3. **Integration Test Scripts** ⭐ (PREFERRED)
- **When**: Testing component interactions, external service integrations
- **Tools**: Python async scripts, mock services
- **Benefits**: Tests complex flows without manual clicking
- **Example**: Auth0 + Plone integration test

### 4. **Service Health Checks** ⭐ (PREFERRED)
- **When**: Verifying external services, database connections
- **Tools**: Connection tests, health endpoints
- **Benefits**: Quickly identifies configuration issues

### 5. **Browser Automation** 🔄 (CONDITIONAL)
- **When**: Testing UI interactions, JavaScript behavior
- **Tools**: Playwright, Selenium, headless browsers
- **Benefits**: Tests full user flow without manual clicking
- **Use**: Only when manual testing would be required multiple times

### 6. **Manual Testing** ❌ (LAST RESORT)
- **When**: Complex UX flows, visual confirmation, one-off verification
- **Requirements**: Must be justified - explain why automation isn't possible
- **Process**:
  1. **Re-evaluate first** - can this be automated?
  2. If manual testing required, provide specific steps
  3. User response "reevaluate" = find automated alternative

## Testing Implementation Guidelines

### For Auth0/OAuth Integration:
1. **✅ Unit test** individual functions (username generation, role mapping)
2. **✅ Integration test** Auth0 ↔ Plone bridge with mocked data
3. **✅ API test** endpoints with mock JWT tokens
4. **❌ Manual test** only for final UX verification (if automation not possible)

### For Database/External Service Integration:
1. **✅ Connection test** - verify service availability
2. **✅ Mock test** - test logic with fake data
3. **✅ Health check** - programmatic service verification
4. **❌ Manual test** - avoid unless visual confirmation needed

### For API Endpoints:
1. **✅ curl test** - verify HTTP behavior
2. **✅ Schema validation** - test request/response models
3. **✅ Error handling** - test edge cases programmatically
4. **❌ Manual test** - only for complex UI flows

## Efficiency Rules

### DO ✅:
- Write test scripts for complex logic
- Use curl/httpx for API testing
- Mock external services when testing integration
- Test error handling and edge cases programmatically
- Create reusable test utilities
- Test graceful fallbacks (e.g., when Plone is down)

### DON'T ❌:
- Ask for manual testing without re-evaluation
- Require browser interaction for simple API tests
- Test one-off scenarios manually when they could be scripted
- Skip automated testing because "it works"
- Assume manual testing is faster (it's not in the long run)

## Testing Tools Available

### Command Line:
```bash
# Server health
curl http://localhost:8000/

# Kill server processes
pkill -f uvicorn

# Start server
source .venv/bin/activate.fish && uvicorn src.eduhub.main:app --reload --host 127.0.0.1 --port 8000

# Run tests
python test_integration.py
pytest tests/
```

### Python Testing:
```python
# Direct function testing
from src.eduhub.auth.plone_bridge import generate_plone_username
result = generate_plone_username("test@example.com", "auth0|123")

# Async integration testing
import asyncio
result = asyncio.run(test_async_function())

# HTTP client testing
import httpx
response = httpx.get("http://localhost:8000/auth/user", headers={"Authorization": f"Bearer {token}"})
```

## Decision Tree: When Manual Testing is Acceptable

```
Is this testing request manual? → NO → Proceed with automated test
                                ↓ YES
Can this be tested with curl/HTTP client? → YES → Use curl/httpx instead
                                          ↓ NO
Can the logic be unit tested in isolation? → YES → Write Python test script
                                           ↓ NO
Can external services be mocked? → YES → Write integration test with mocks
                                 ↓ NO
Is this a one-time verification? → YES → Consider if browser automation is worth it
                                ↓ NO (recurring test)
                                → Must automate with browser automation or reconsider approach
```

## Example: Testing Auth0 Integration

**❌ Poor approach:**
"Go to the browser, login, click buttons, check if user info shows roles"

**✅ Good approach:**
1. Unit test role extraction: `python test_role_extraction.py`
2. Integration test full flow: `python test_auth_integration.py`
3. API test endpoints: `curl` with test JWT
4. Only manual test final UX if automation isn't feasible

## Time Efficiency Benefits

- **Automated tests**: Run in seconds, repeatable, catch regressions
- **Manual tests**: Minutes per test, error-prone, need re-testing after changes
- **Long-term ROI**: 1 hour of automation saves 10+ hours of manual testing
- **Confidence**: Automated tests provide reliable feedback on changes

## Summary

**The Goal**: Enable continuous development without manual testing bottlenecks. Every time manual testing is avoided, development velocity increases and software quality improves through consistent, repeatable verification.

**The Rule**: When tempted to ask for manual testing, first ask: "How can I test this programmatically?"
