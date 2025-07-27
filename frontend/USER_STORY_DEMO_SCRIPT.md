# EduHub User Story Demonstration Script

## Pre-Demo Setup
1. Ensure Docker containers are running
2. Have sample CSV file ready for import
3. Open browser to http://localhost:8001

## Demo Flow

### 1. Authentication (Phase 1-3)
**User Story**: "As an administrator, I need secure access to the system"

1. **Show Login Page**
   - Point out dual login options
   - Explain saved credentials vs different user
   - Click "Sign in with saved credentials"

2. **Auth0 Flow**
   - Show Auth0 universal login
   - Login redirects back to dashboard
   - Point out user info in sidebar

3. **Account Switching**
   - Logout using sidebar button
   - Click "Sign in as different user"
   - Show how it forces account selection

### 2. Dashboard Overview
**User Story**: "As an admin, I need to see system status at a glance"

1. **Metrics Cards**
   - Total Schedules (12)
   - Media Embeds (47)
   - Public Data Sets (8) - Recently recovered
   - Active Workflows (15) - Recently recovered
   - Recent Alerts (23)

2. **Recent Activity**
   - Shows latest system events
   - Time-based ordering
   - Activity type icons

3. **Quick Actions**
   - One-click access to common tasks
   - Visual feedback on hover
   - Direct navigation to features

### 3. Schedule Import (Phase 4)
**User Story**: "As an admin, I can bulk import course schedules"

1. **Navigate to Schedule Import**
   - Click "Schedule Import" in sidebar
   - Or use Quick Action button

2. **CSV Upload Demo**
   - Drag and drop CSV file
   - Show file validation
   - Preview first 5 rows
   - Highlight any validation errors

3. **Import Process**
   - Click "Import Schedule"
   - Show success feedback
   - Display import summary

4. **Import History** (if implemented)
   - View past imports
   - Download original files
   - Check import logs

### 4. Rich Media Embeds (Phase 5)
**User Story**: "As a content creator, I can embed videos and media"

1. **Navigate to Media Embeds**
   - Click "Media Embeds" in sidebar

2. **oEmbed Demo**
   - Paste YouTube URL
   - Show instant preview
   - Display embed code
   - Try different providers (Vimeo, Twitter)

3. **Quick Test URLs**
   - Use pre-populated test buttons
   - Show various media types
   - Explain caching benefits

### 5. Open Data API (Phase 6)
**User Story**: "As a developer, I can access public data via API"

1. **Navigate to Open Data**
   - Click "Open Data" in sidebar

2. **Content Browser**
   - Show paginated content list
   - Demonstrate search functionality
   - Filter by categories

3. **Statistics Tab**
   - Total content metrics
   - API usage statistics
   - Cache performance

4. **API Access** (explain)
   - RESTful endpoints available
   - Authentication via tokens
   - Multiple export formats

### 6. Workflow Templates (Phase 7)
**User Story**: "As a manager, I can implement approval workflows"

1. **Navigate to Workflows**
   - Click "Workflows" in sidebar

2. **Template Gallery**
   - Show available templates
   - Course Approval Workflow
   - Content Review Process
   - Point out usage statistics

3. **Apply Template**
   - Click "Apply Template"
   - Select content item
   - Confirm application

4. **Active Workflows Tab**
   - Show workflows in progress
   - Different status indicators
   - Assignee information
   - Time tracking

### 7. Real-time Alerts (Phase 8)
**User Story**: "As a user, I receive instant notifications"

1. **Navigate to Alerts**
   - Click "Alerts" in sidebar

2. **Alert Feed**
   - Show WebSocket "Live" indicator
   - Unread alerts highlighted
   - Multiple alert types (info, success, warning, error)
   - Mark as read functionality

3. **Compose Alert**
   - Switch to Compose tab
   - Fill out alert form
   - Select audience
   - Send test alert

4. **Settings Tab**
   - Channel preferences (Web, Slack, Email)
   - Quiet hours configuration
   - Per-category settings

### 8. Responsive Design
**User Story**: "As a user, I can access the system from any device"

1. **Resize Browser**
   - Show mobile menu
   - Responsive tables
   - Touch-friendly buttons

### 9. Error Handling
**User Story**: "As a user, I get helpful feedback when things go wrong"

1. **Demonstrate Error States**
   - Upload invalid CSV
   - Try invalid oEmbed URL
   - Show user-friendly messages

## Key Talking Points

### Technical Architecture
- Modern React 19 with TypeScript
- FastAPI backend with Plone CMS
- WebSocket for real-time features
- Redis caching for performance
- PostgreSQL for data persistence

### Security Features
- OAuth2/Auth0 integration
- JWT token validation
- Role-based access control
- Rate limiting protection
- Secure cookie handling

### Performance Optimizations
- JIT compiled Tailwind CSS
- Lazy-loaded routes
- Cached API responses
- Optimistic UI updates
- WebSocket connection pooling

### Developer Experience
- TypeScript for type safety
- Modular component architecture
- Comprehensive error handling
- API documentation
- Mock data for testing

## Closing
"This admin interface provides a modern, user-friendly way to manage all aspects of the EduHub educational content system. Each phase builds upon the previous ones to create a comprehensive solution for educational institutions."