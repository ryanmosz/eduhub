# Phase 4.0 Planning Brief - CSV Schedule Importer
### For Agent Task Breakdown Development

> **Target**: Create detailed `tasks/tasks-phase-4-csv-schedule-importer.md` following established project patterns

---

## 🎯 **Mission Statement**

You are tasked with creating a comprehensive task breakdown for **Phase 4.0: CSV Schedule Importer** following the same structure and methodology used in Phases 1-3. This feature enables Educational Program Operation Managers to upload CSV/Excel files containing program schedules and automatically transform them into Plone CMS content.

## 📋 **Core Feature Requirements**

### **Feature Overview**
- **Name**: CSV Schedule Importer
- **Estimated Time**: 3-4 hours implementation
- **Complexity**: Low - pandas CSV parsing + FastAPI endpoint + Plone integration
- **Risk Level**: Very low - straightforward file processing

### **User Story (PRIMARY)**
*"As a Curriculum Manager at Metro Community College, I receive schedule updates from department heads in Excel files with 200+ entries each term. Manually entering each session into the old system takes 8+ hours of error-prone data entry. With CSV import, I upload the file, review the validation results, and publish the entire schedule in under 20 minutes. That gives me 7+ hours back to focus on program quality instead of data entry."*

### **Expected CSV Format**
```csv
Program,Date,Time,Instructor,Room,Department,Capacity,Notes
"Introduction to Python",2024-03-15,"09:00-12:00","Dr. Smith","Lab A","Computer Science",25,"Bring laptops"
"Advanced Web Development",2024-03-15,"14:00-17:00","Prof. Johnson","Room 302","Computer Science",20,""
"Digital Marketing Basics",2024-03-16,"10:00-12:00","Ms. Davis","Conference Room","Business",30,"Guest speaker"
```

### **Technical Requirements**
1. **File Upload Endpoint**: FastAPI endpoint accepting CSV/Excel files
2. **Data Validation**: Verify required fields, date formats, conflicts
3. **Preview Interface**: Show parsed data before committing
4. **Plone Integration**: Create program content in Plone CMS via existing PloneClient
5. **Error Handling**: Graceful handling of malformed data, duplicate entries
6. **Batch Processing**: Handle large files (200+ rows) efficiently
7. **Rollback Capability**: Ability to undo import if issues discovered

---

## 🏗️ **Project Context & Integration Points**

### **Current System State** (as of Phase 3 completion)
- ✅ **FastAPI Application**: Modern async API layer established (`src/eduhub/main.py`)
- ✅ **Plone Integration**: Existing `PloneClient` with content creation methods (`src/eduhub/plone_integration.py`)
- ✅ **Authentication**: OAuth2/SSO system with user roles and permissions
- ✅ **Testing Framework**: Automated testing strategy and programmatic test utilities

### **Integration Dependencies**
1. **PloneClient Extension**: May need new methods for bulk content creation
2. **Authentication**: Import endpoint should require appropriate user permissions
3. **File Storage**: Temporary file handling for upload processing
4. **Database**: Consider storing import history/logs for auditing

### **Existing Code to Leverage**
- `src/eduhub/plone_integration.py` - PloneClient for content creation
- `src/eduhub/auth/` - Authentication system for securing endpoints
- `tests/` - Testing framework for programmatic validation

---

## 📁 **Files You Should Review** (Required Reading)

### **Primary Reference Documents (READ FIRST)**
1. `tasks/tasks-overall-project-plan.md` - **PROJECT OVERVIEW** - High-level phases and strategic context
2. `tasks/tasks-overall-project-plan-addendum.md` - **STRATEGIC FRAMEWORK** - Testing methodology and implementation decisions
3. `tasks/tasks-phase-3-oauth2-sso-gateway.md` - **TEMPLATE STRUCTURE** to follow exactly
4. `docs/testing-strategy.md` - Automated testing requirements (critical)
5. `.cursor/rules/RMM-workflow/testing-efficiency.mdc` - Testing efficiency rules
6. `.cursor/rules/generate-tasks.mdc` - **CORE WORKFLOW** for two-phase task generation
7. `.cursor/rules/RMM-workflow/task-subtask-expansion.mdc` - Subtask expansion methodology
8. `.cursor/rules/create-feature-prd.mdc` - Reference for clarifying questions (if feature requirements unclear)

### **Feature Context & Requirements**
9. `docs/plone_5day_plan.md` (lines 64-95) - User story and feature description
10. `docs/feature-analysis-alternatives.md` (lines 241-288) - Implementation details and rationale
11. `docs/future-gui-plans.md` (lines 71-96) - UI mockup for reference

### **Technical Integration**
12. `src/eduhub/plone_integration.py` - Existing Plone integration methods
13. `src/eduhub/main.py` - FastAPI application structure
14. `src/eduhub/auth/` - Authentication system for endpoint security

---

## 🎯 **Deliverable: Task File Structure**

Create `tasks/tasks-phase-4-csv-schedule-importer.md` with these sections:

### **1. Header Section** (Follow Phase 3 Pattern)
```markdown
## Relevant Files
[List all files that will be created/modified]

### Notes
[Key implementation notes and testing approach]
```

### **2. Parent Tasks with Subtasks** (4-6 Parent Tasks)
Follow the pattern:
```markdown
- [ ] **4.1 Parent Task Name**
  - Brief description of what this accomplishes
  - [ ] 4.1.1 Specific subtask
  - [ ] 4.1.2 Another subtask
  - [ ] 4.1.3 **TEST**: Specific automated test description
  - [ ] 4.1.4 **TEST**: Another automated test description
```

### **3. Suggested Parent Task Structure**
- **4.1**: FastAPI File Upload Endpoint Creation
- **4.2**: CSV Processing & Validation Logic
- **4.3**: Plone Content Creation Integration
- **4.4**: Error Handling & Data Validation
- **4.5**: Preview & Confirmation Interface (optional UI)
- **4.6**: Testing & Documentation

---

## ⚡ **Critical Implementation Guidelines**

### **MUST Follow Testing Strategy**
- **Every parent task MUST have 2+ TEST subtasks**
- **Prefer programmatic tests** over manual browser testing
- Use curl/httpx for API endpoint testing
- Create reusable test scripts for validation logic
- Mock external dependencies when possible

### **FastAPI Patterns to Follow**
```python
# Example endpoint structure
@router.post("/import/schedule")
async def import_schedule(
    file: UploadFile,
    preview_only: bool = False,
    current_user: User = Depends(get_current_user)
):
    # Implementation here
    pass
```

### **Plone Integration Approach**
- Extend existing `PloneClient` class with bulk operations
- Use existing content creation patterns
- Handle failures gracefully with partial rollback

### **Data Validation Requirements**
- Required fields: Program, Date, Time, Instructor
- Date format validation and parsing
- Time conflict detection
- Room booking conflicts
- Instructor schedule conflicts

---

## 🔧 **Process Instructions (Two-Phase Approach)**

### **🎯 CRITICAL: Follow Two-Phase Workflow**

**Phase 1: Parent Task Identification** (High-Level Tent Poles)
**Phase 2: Subtask Expansion** (Implementation Details)

---

### **Phase 1: Parent Task Generation**
Focus on **tent pole tasks** - the major high-level accomplishments needed.

#### **Step 1.1: Analysis Phase**
1. **FIRST**: Read the Project Foundation documents (tasks-overall-project-plan.md and addendum) to understand strategic context
2. Read ALL other reference documents listed above
3. Understand the existing PloneClient API methods
4. Review FastAPI patterns used in auth module
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
3. Wait for user approval before proceeding to Phase 2

**Example Parent Tasks for Phase 4.0:**
- 4.1 File Upload & Processing Infrastructure
- 4.2 CSV Data Validation & Parsing
- 4.3 Plone Content Creation Integration
- 4.4 Error Handling & Rollback Mechanisms
- 4.5 Testing & Documentation

---

### **Phase 2: Subtask Expansion** (After User Approval)

#### **Step 2.1: Subtask Development**
1. Break each approved parent task into 3-5 specific subtasks
2. Add 2+ TEST subtasks per parent task (automated testing preferred)
3. Ensure logical dependency ordering between subtasks
4. Each subtask should be actionable and specific

#### **Step 2.2: Technical Specification**
1. List all files that will be created or modified
2. Specify new dependencies (pandas, openpyxl, etc.)
3. Define API endpoint signatures
4. Document expected data models

#### **Step 2.3: Testing Strategy Integration**
1. **CRITICAL**: Follow automated testing principles from `docs/testing-strategy.md`
2. Specify programmatic tests for each component
3. Create test CSV files for validation
4. Plan integration tests with PloneClient

#### **Step 2.4: Quality Review**
1. Ensure task structure matches Phase 3 pattern exactly
2. Verify all testing is automated where possible
3. Check that file list is complete
4. Validate logical task ordering

---

## 🚨 **Success Criteria**

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
- ✅ Implementation can be completed in 3-4 hours
- ✅ Integrates seamlessly with existing PloneClient and auth systems

---

## 📞 **Questions to Consider**

While creating the breakdown, consider:
1. How will large CSV files (1000+ rows) be handled efficiently?
2. What happens if Plone content creation fails halfway through?
3. How will duplicate detection work across imports?
4. Should there be import history/audit logging?
5. What file formats beyond CSV should be supported (Excel, TSV)?
6. How will room/instructor conflicts be detected and resolved?
7. What user permissions are required for import operations?

---

**Remember**: This feature should feel like a natural extension of the existing system, leveraging all the infrastructure built in Phases 1-3 while providing immediate, measurable value to Educational Program Operation Managers.

**Delivery Timeline**: Aim to have the task breakdown completed and ready for implementation by the time Phase 3.5-3.6 work is finished.

---

## 📎 **For Future Features (5.0, 6.0, etc.)**

For planning subsequent features, use the task-agnostic template: `docs/feature-task-planning-template.md`

This general template contains the same two-phase workflow but can be applied to any feature without modification. Simply provide the feature-specific requirements and follow the established process.
