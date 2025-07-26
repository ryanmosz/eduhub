# Feature Task Planning Template
### For Agent Task Breakdown Development (Task-Agnostic)

> **Purpose**: Universal template for creating detailed task breakdowns for ANY feature phase

---

## 🎯 **Mission Statement**

You are tasked with creating a comprehensive task breakdown for **[FEATURE_PHASE]** following the established project structure and methodology. This template works for any feature by substituting the specific requirements.

**Two-Phase Approach:**
1. **Phase 1**: Identify high-level parent tasks (tent poles)
2. **Phase 2**: Get user approval, then expand with detailed subtasks

---

## 📋 **Required Information to Substitute**

When using this template, the user will provide:
- **Feature Name**: e.g., "CSV Schedule Importer", "Rich-Media Embeds", etc.
- **Phase Number**: e.g., "4.0", "5.0", "6.0"
- **Estimated Time**: e.g., "3-4 hours", "2-3 hours"
- **Complexity Level**: e.g., "Low", "Medium", "High"
- **Primary User Story**: The main user narrative driving the feature
- **Technical Requirements**: Core functionality that must be implemented
- **Integration Points**: What existing systems this feature connects to

---

## 📁 **Universal Reference Documents** (Always Required Reading)

### **Project Foundation & Context** (READ FIRST)
1. `tasks/tasks-overall-project-plan.md` - **PROJECT OVERVIEW** - High-level phases, feature priorities, and strategic context
2. `tasks/tasks-overall-project-plan-addendum.md` - **STRATEGIC FRAMEWORK** - Testing methodology, implementation decisions, and project approach

### **Core Workflow & Structure**
3. `tasks/tasks-phase-3-oauth2-sso-gateway.md` - **TEMPLATE STRUCTURE** to follow exactly
4. `.cursor/rules/generate-tasks.mdc` - **CORE WORKFLOW** for two-phase task generation
5. `.cursor/rules/RMM-workflow/task-subtask-expansion.mdc` - Subtask expansion methodology
6. `.cursor/rules/RMM-workflow/testing-efficiency.mdc` - Testing efficiency rules (critical)

### **Implementation Strategy**
7. `docs/testing-strategy.md` - Automated testing requirements (critical)
8. `.cursor/rules/create-feature-prd.mdc` - Reference for clarifying questions (if feature requirements unclear)

### **Technical Integration** (Feature-Specific)
9. `src/eduhub/main.py` - FastAPI application structure
10. `src/eduhub/auth/` - Authentication system for endpoint security
11. [Additional files will be specified per feature]

---

## 🔧 **Universal Process Instructions (Two-Phase Approach)**

### **🎯 CRITICAL: Follow Two-Phase Workflow**

**Phase 1: Parent Task Identification** (High-Level Tent Poles)
**Phase 2: Subtask Expansion** (Implementation Details)

---

### **Phase 1: Parent Task Generation**
Focus on **tent pole tasks** - the major high-level accomplishments needed.

#### **Step 1.1: Analysis Phase**
1. **FIRST**: Read the Project Foundation documents (tasks-overall-project-plan.md and addendum) to understand strategic context
2. Read ALL other reference documents listed above
3. Understand the existing codebase integration points for this feature
4. Review similar patterns used in completed phases
5. Understand the testing methodology requirements and project priorities

#### **Step 1.2: Identify Parent Tasks (Tent Poles)**
1. Create 4-6 high-level parent tasks that represent major accomplishments
2. **DO NOT** think about implementation details yet
3. Focus on **what** needs to be accomplished, not **how**
4. Each parent task should be a major milestone that moves the feature forward
5. When all parent tasks are complete, the entire feature should be complete

#### **Step 1.3: Present Parent Tasks for Approval**
1. Show ONLY the parent tasks (no subtasks yet)
2. Provide a brief explanation of why completing these parent tasks fulfills the overall feature
3. Include reasoning like: "These parent tasks fulfill [FEATURE_NAME] because..."
4. **STOP and wait for user approval** before proceeding to Phase 2

**Template for Presenting Parent Tasks:**
```markdown
## Proposed Parent Tasks for [FEATURE_NAME]

- [X.1] [First Major Accomplishment]
- [X.2] [Second Major Accomplishment]
- [X.3] [Third Major Accomplishment]
- [X.4] [Fourth Major Accomplishment]
- [X.5] [Fifth Major Accomplishment] (if needed)

## Why These Parent Tasks Fulfill [FEATURE_NAME]

These parent tasks fulfill [FEATURE_NAME] because:
1. Task X.1 establishes [core capability needed]
2. Task X.2 provides [essential functionality]
3. Task X.3 ensures [integration requirement]
4. Task X.4 handles [error/edge cases]
5. Task X.5 validates [testing/quality assurance]

When all these are complete, users will be able to [primary user story outcome].

Ready to proceed with subtask expansion? Please respond with "Go" to continue.
```

---

### **Phase 2: Subtask Expansion** (After User Approval)

#### **Step 2.1: Subtask Development**
1. Break each approved parent task into 3-5 specific subtasks
2. Add 2+ TEST subtasks per parent task (automated testing preferred)
3. Ensure logical dependency ordering between subtasks
4. Each subtask should be actionable and specific

#### **Step 2.2: Technical Specification**
1. List all files that will be created or modified
2. Specify new dependencies needed (e.g., pandas, requests, etc.)
3. Define API endpoint signatures if applicable
4. Document expected data models

#### **Step 2.3: Testing Strategy Integration**
1. **CRITICAL**: Follow automated testing principles from `docs/testing-strategy.md`
2. Specify programmatic tests for each component
3. Create test data/files for validation
4. Plan integration tests with existing systems

#### **Step 2.4: Quality Review**
1. Ensure task structure matches Phase 3 pattern exactly
2. Verify all testing is automated where possible
3. Check that file list is complete and accurate
4. Validate logical task ordering and dependencies

---

## 🎯 **Deliverable Structure (Universal)**

Create `tasks/tasks-phase-[X]-[feature-name].md` with these sections:

### **1. Header Section**
```markdown
## Relevant Files

- `path/to/potential/file1.ts` - Contains the main component for this feature.
- `path/to/file1.test.ts` - Unit tests for `file1.ts`.
- `path/to/another/file.tsx` - API route handler for data submission.
- `path/to/another/file.test.tsx` - Unit tests for `another/file.tsx`.
- `lib/utils/helpers.ts` - Utility functions needed for calculations.
- `lib/utils/helpers.test.ts` - Unit tests for `helpers.ts`.

- **Dependencies / Integration Points** – List existing modules or services this feature touches (e.g., auth middleware, Plone bridge, external APIs).

- **Sample Fixtures** – Enumerate any test assets required (e.g., `fixtures/sample_valid.csv`, `fixtures/avatar.png`).

### Notes

- Unit tests should typically be placed alongside the code files they are testing (e.g., `MyComponent.tsx` and `MyComponent.test.tsx` in the same directory).
- Use `npx jest [optional/path/to/test/file]` to run tests. Running without a path executes all tests found by the Jest configuration.
```

### **2. Parent Tasks with Subtasks**
Follow the exact pattern:
```markdown
- [ ] **[X.1] Parent Task Name**
  - Brief description of what this accomplishes
  - **Risk & Mitigation**: _One-line summary of potential blocker & fallback._
  - **Benchmark / Acceptance Target**: _If applicable (e.g., "response time <200 ms")._
  - [ ] [X.1.1] Specific subtask
  - [ ] [X.1.2] Another subtask
  - [ ] [X.1.3] **TEST**: Automated check — specify tool (`pytest`, `TestClient`, `Playwright`, etc.) and any mocks/stubs used
  - [ ] [X.1.4] **TEST**: Another automated test — specify tool and mocks/stubs
```

---

## ⚡ **Universal Implementation Guidelines**

### **MUST Follow Testing Strategy**
- **Every parent task MUST have 2+ TEST subtasks**
- **Prefer programmatic tests** over manual browser testing
- Use curl/httpx for API endpoint testing where applicable
- Create reusable test scripts for validation logic
- Mock external dependencies when possible

### **FastAPI Patterns to Follow** (if applicable)
```python
# Example endpoint structure
@router.post("/[feature-endpoint]")
async def [feature_function](
    [parameters],
    current_user: User = Depends(get_current_user)
):
    # Implementation here
    pass
```

### **Integration Approach**
- Leverage existing systems (PloneClient, Auth, etc.)
- Use established patterns from completed phases
- Handle failures gracefully with appropriate error responses
- Follow security best practices

---

## 🚨 **Universal Success Criteria**

**Phase 1 Success (Parent Tasks):**
- ✅ Presents 4-6 high-level parent tasks that represent major milestones
- ✅ Parent tasks focus on **what** needs to be accomplished, not **how**
- ✅ Completing all parent tasks would fulfill the entire feature requirement
- ✅ Provides clear rationale for why these parent tasks fulfill the overall objective
- ✅ Waits for user approval before proceeding to Phase 2

**Phase 2 Success (Complete Task Breakdown):**
- ✅ Follows exact structure pattern of `tasks-phase-3-oauth2-sso-gateway.md`
- ✅ Contains approved parent tasks with 3-5 subtasks each
- ✅ Every parent task has 2+ **TEST** subtasks emphasizing automation
- ✅ All files are listed in "Relevant Files" section
- ✅ Testing approach prioritizes programmatic validation
- ✅ Implementation aligns with estimated time frame
- ✅ Integrates seamlessly with existing project architecture

---

## 📞 **Universal Questions to Consider**

While creating any feature breakdown, consider:
1. How does this feature integrate with existing authentication?
2. What happens if external dependencies fail?
3. How will data validation and error handling work?
4. What user permissions are required?
5. How will this feature be tested programmatically?
6. What edge cases need to be handled?
7. How will this feature scale with larger data sets?

---

## 🔄 **How to Use This Template**

1. **Copy this template** for the specific feature you're planning
2. **Replace placeholders** like [FEATURE_NAME], [X.1], etc. with actual values
3. **Add feature-specific requirements** and technical details
4. **Follow the two-phase process** exactly as outlined
5. **Reference feature-specific files** in the integration section

**Example Usage:**
*"Here's the general task planning template. Follow this process for Phase 5.0: Rich-Media Embeds (oEmbed). The feature should enable YouTube/Vimeo embedding via oEmbed protocol integration."*

---

**Remember**: This template ensures consistency across all features while allowing for feature-specific customization. The two-phase approach ensures high-level planning approval before diving into implementation details, maximizing efficiency and reducing rework.
