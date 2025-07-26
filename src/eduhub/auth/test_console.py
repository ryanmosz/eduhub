"""
EduHub OAuth2 Test Console

Interactive browser-based testing interface for Auth0 OAuth2 flow.
Provides persistent logging and clear step-by-step testing workflow.
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/test", tags=["testing"])


@router.get("/auth-console", response_class=HTMLResponse)
async def auth_test_console():
    """
    Traditional-style OAuth2 testing console with persistent logging.

    Features:
    - Persistent console output across page navigation
    - Clear session state tracking
    - Step-by-step workflow indicators
    - Non-navigation test options where possible
    """
    base_url = "http://localhost:8000"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>EduHub Auth Test Console</title>
        <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🎓</text></svg>">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                background: #0c0c0c;
                color: #00ff00;
                min-height: 100vh;
                padding: 20px;
            }}

            .terminal {{
                max-width: 1200px;
                margin: 0 auto;
                background: #1a1a1a;
                border: 2px solid #333;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 0 20px rgba(0, 255, 0, 0.1);
            }}

            .terminal-header {{
                display: flex;
                align-items: center;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 1px solid #333;
            }}

            .terminal-title {{
                color: #00ff00;
                font-size: 1.2rem;
                font-weight: bold;
            }}

            .session-status {{
                margin-left: auto;
                padding: 4px 12px;
                border-radius: 4px;
                font-size: 0.9rem;
                font-weight: bold;
            }}

            .status-logged-out {{ background: #444; color: #ccc; }}
            .status-logged-in {{ background: #0a5d0a; color: #00ff00; }}
            .status-unknown {{ background: #5d5d0a; color: #ffff00; }}

            .test-section {{
                display: grid;
                grid-template-columns: 400px 1fr;
                gap: 20px;
                margin-bottom: 20px;
            }}

            .control-panel {{
                background: #262626;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 15px;
            }}

            .control-panel h3 {{
                color: #00ccff;
                margin-bottom: 15px;
                font-size: 1rem;
            }}

            .credentials {{
                background: #333;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 10px;
                margin-bottom: 15px;
                font-size: 0.9rem;
            }}

            .credential-item {{
                margin: 5px 0;
                cursor: pointer;
                padding: 2px 6px;
                border-radius: 3px;
                transition: background 0.2s;
            }}

            .credential-item:hover {{
                background: #444;
            }}

            .test-buttons {{
                display: grid;
                gap: 10px;
            }}

            .btn {{
                padding: 10px 15px;
                border: 1px solid #555;
                background: #333;
                color: #fff;
                border-radius: 4px;
                cursor: pointer;
                font-family: inherit;
                font-size: 0.9rem;
                transition: all 0.2s;
            }}

            .btn:hover {{
                background: #444;
                border-color: #777;
            }}

            .btn-primary {{
                background: #1a4a8a;
                border-color: #2d5aa0;
                color: #87ceeb;
            }}

            .btn-primary:hover {{
                background: #2d5aa0;
                border-color: #4169e1;
            }}

            .btn-danger {{
                background: #8a1a1a;
                border-color: #a02d2d;
                color: #ffb3b3;
            }}

            .btn-danger:hover {{
                background: #a02d2d;
                border-color: #e14141;
            }}

            .btn-secondary {{
                background: #1a8a1a;
                border-color: #2da02d;
                color: #b3ffb3;
            }}

            .btn-secondary:hover {{
                background: #2da02d;
                border-color: #41e141;
            }}

            .console-output {{
                background: #000;
                border: 1px solid #333;
                border-radius: 6px;
                padding: 15px;
                height: 500px;
                overflow-y: auto;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 0.9rem;
                line-height: 1.4;
            }}

            .log-line {{
                margin-bottom: 4px;
                word-wrap: break-word;
            }}

            .log-timestamp {{
                color: #666;
                font-size: 0.8rem;
            }}

            .log-info {{ color: #00ccff; }}
            .log-success {{ color: #00ff00; }}
            .log-warning {{ color: #ffff00; }}
            .log-error {{ color: #ff6666; }}
            .log-debug {{ color: #cc99ff; }}

            .console-controls {{
                margin-top: 10px;
                display: flex;
                gap: 10px;
            }}

            .btn-small {{
                padding: 6px 12px;
                font-size: 0.8rem;
            }}

            .workflow-status {{
                background: #262626;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 15px;
                margin-bottom: 20px;
            }}

            .workflow-step {{
                display: flex;
                align-items: center;
                margin: 8px 0;
                font-size: 0.9rem;
            }}

            .step-icon {{
                margin-right: 10px;
                font-size: 1.2rem;
            }}

            .step-pending {{ color: #666; }}
            .step-active {{ color: #ffff00; }}
            .step-complete {{ color: #00ff00; }}
            .step-error {{ color: #ff6666; }}

            .copy-credential:hover { background: #6c757d; }
            
            .file-upload {
                margin: 15px 0;
                padding: 15px;
                border: 2px dashed #ccc;
                border-radius: 8px;
                text-align: center;
                background: white;
                cursor: pointer;
            }
            .file-upload.dragover { border-color: #2196F3; background: #f0f8ff; }
            
            #systemStatus.operational { border-color: #4CAF50; background: #f8fff8; }
        </style>
    </head>
    <body>
        <div class="terminal">
            <div class="terminal-header">
                <div class="terminal-title">🎓 EduHub OAuth2 Test Console</div>
                <div id="sessionStatus" class="session-status status-unknown">Session: Unknown</div>
            </div>

            <div class="workflow-status">
                <h3 style="color: #00ccff; margin-bottom: 10px;">OAuth2 Workflow Status</h3>
                <div id="step1" class="workflow-step step-pending">
                    <span class="step-icon">⏳</span>
                    <span>1. Start unauthenticated</span>
                </div>
                <div id="step2" class="workflow-step step-pending">
                    <span class="step-icon">⏳</span>
                    <span>2. Initiate login flow</span>
                </div>
                <div id="step3" class="workflow-step step-pending">
                    <span class="step-icon">⏳</span>
                    <span>3. Auth0 authentication</span>
                </div>
                <div id="step4" class="workflow-step step-pending">
                    <span class="step-icon">⏳</span>
                    <span>4. Callback processing</span>
                </div>
                <div id="step5" class="workflow-step step-pending">
                    <span class="step-icon">⏳</span>
                    <span>5. Session established</span>
                </div>
                <div id="step6" class="workflow-step step-pending">
                    <span class="step-icon">⏳</span>
                    <span>6. Logout test</span>
                </div>
            </div>

            <div class="test-section">
                <div class="control-panel">
                    <h3>🔧 Test Controls</h3>

                    <div class="credentials">
                        <strong>Test Credentials:</strong><br>
                        <div class="credential-item" onclick="copyText('dev@example.com')" title="Click to copy">
                            📧 dev@example.com
                        </div>
                        <div class="credential-item" onclick="copyText('DevPassword123!')" title="Click to copy">
                            🔑 DevPassword123!
                        </div>
                        <div class="credential-item" onclick="copyText('admin@example.com')" title="Click to copy">
                            📧 admin@example.com
                        </div>
                        <div class="credential-item" onclick="copyText('AdminPassword123!')" title="Click to copy">
                            🔑 AdminPassword123!
                        </div>
                    </div>

                    <div class="test-buttons">
                        <button class="btn btn-primary" onclick="startLoginFlow()">🚀 Start Login Flow</button>
                        <button class="btn btn-secondary" onclick="testUserInfo()">👤 Check User Info</button>
                        <button class="btn btn-danger" onclick="testLogout()">🚪 Test Logout</button>
                        <button class="btn" onclick="checkAuthStatus()">🔍 Check Auth Status</button>
                        <button class="btn" onclick="resetTest()">🔄 Reset Test</button>
                        <button class="btn" onclick="debugCookies()">🍪 Debug Cookies</button>
                        <button class="btn" onclick="simpleLogout()">🚪 Simple Logout</button>
                        <button class="btn" onclick="window.open('{base_url}/docs', '_blank')">📚 Swagger UI</button>
                    </div>
                </div>

                <div>
                    <div class="console-output" id="console"></div>
                    <div class="console-controls">
                        <button class="btn btn-small" onclick="clearConsole()">🗑️ Clear</button>
                        <button class="btn btn-small" onclick="copyConsoleOutput()">📋 Copy Output</button>
                        <button class="btn btn-small" onclick="saveConsoleLog()">💾 Save Log</button>
                    </div>
                </div>
            </div>

            <div class="test-section">
                <h3>📁 CSV Schedule Importer Testing</h3>
                <div class="file-upload" id="fileUpload">
                    <input type="file" id="fileInput" accept=".csv, .xlsx, .xls" style="display: none;">
                    <p>Drag & drop your CSV/Excel file here, or click to select</p>
                    <p id="fileInfo">No file selected</p>
                </div>
                <div class="test-buttons">
                    <button class="btn btn-warning" id="previewBtn" onclick="testPreview()" disabled>👀 Test Preview</button>
                    <button class="btn btn-success" id="importBtn" onclick="testImport()" disabled>⚡ Test Import</button>
                    <button class="btn btn-info" onclick="testValidation()">🧪 Test Validation</button>
                    <button class="btn btn-secondary" onclick="downloadTemplate()">📋 Download Template</button>
                    <button class="btn btn-secondary" onclick="checkSystemStatus()">⚙️ System Status</button>
                </div>
                <div id="systemStatus" style="margin-top: 15px; padding: 10px; background: #f8fcff; border: 2px solid #2196F3; border-radius: 8px;">
                    <h4>System Status</h4>
                    <p id="systemStatusText">Checking...</p>
                    <p id="systemCapabilities"></p>
                </div>
            </div>
        </div>

        <script>
            // Persistent logging across page reloads
            const CONSOLE_KEY = 'eduhub_console_log';
            const SESSION_KEY = 'eduhub_session_state';

            function log(message, type = 'info') {{
                const timestamp = new Date().toLocaleTimeString();
                const logEntry = {{
                    timestamp,
                    message,
                    type,
                    id: Date.now()
                }};

                // Add to persistent storage
                const existingLogs = JSON.parse(localStorage.getItem(CONSOLE_KEY) || '[]');
                existingLogs.push(logEntry);
                localStorage.setItem(CONSOLE_KEY, JSON.stringify(existingLogs));

                // Display in console
                displayLogEntry(logEntry);

                // Auto-scroll to bottom
                const console = document.getElementById('console');
                console.scrollTop = console.scrollHeight;
            }}

            function displayLogEntry(entry) {{
                const console = document.getElementById('console');
                const line = document.createElement('div');
                line.className = 'log-line';
                line.innerHTML = '<span class="log-timestamp">[' + entry.timestamp + ']</span> <span class="log-' + entry.type + '">' + entry.message + '</span>';
                console.appendChild(line);
            }}

            function loadPersistedLogs() {{
                const logs = JSON.parse(localStorage.getItem(CONSOLE_KEY) || '[]');
                const console = document.getElementById('console');
                console.innerHTML = '';
                logs.forEach(displayLogEntry);
                console.scrollTop = console.scrollHeight;
            }}

            function clearConsole() {{
                localStorage.removeItem(CONSOLE_KEY);
                document.getElementById('console').innerHTML = '';
                log('🧹 Console cleared', 'info');
            }}

            function copyConsoleOutput() {{
                const console = document.getElementById('console');
                const text = console.innerText;
                navigator.clipboard.writeText(text).then(() => {{
                    log('📋 Console output copied to clipboard', 'success');
                }}).catch(err => {{
                    log('❌ Failed to copy: ' + err, 'error');
                }});
            }}

            function saveConsoleLog() {{
                const logs = JSON.parse(localStorage.getItem(CONSOLE_KEY) || '[]');
                const text = logs.map(l => '[' + l.timestamp + '] ' + l.message).join('\\n');
                const blob = new Blob([text], {{ type: 'text/plain' }});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'eduhub-auth-test-' + new Date().toISOString().split('T')[0] + '.log';
                a.click();
                URL.revokeObjectURL(url);
                log('💾 Console log saved', 'success');
            }}

            function copyText(text) {{
                navigator.clipboard.writeText(text).then(() => {{
                    log('📋 Copied: ' + text, 'success');
                }}).catch(err => {{
                    log('❌ Copy failed: ' + err, 'error');
                }});
            }}

            function updateWorkflowStep(stepNumber, status, icon = null) {{
                const step = document.getElementById('step' + stepNumber);
                const iconEl = step.querySelector('.step-icon');

                step.className = 'workflow-step step-' + status;
                if (icon) iconEl.textContent = icon;
            }}

            function updateSessionStatus(status) {{
                const statusEl = document.getElementById('sessionStatus');
                statusEl.className = 'session-status status-' + status;

                switch(status) {{
                    case 'logged-in':
                        statusEl.textContent = 'Session: ✅ Authenticated';
                        break;
                    case 'logged-out':
                        statusEl.textContent = 'Session: ❌ Not Authenticated';
                        break;
                    default:
                        statusEl.textContent = 'Session: ❓ Unknown';
                }}

                localStorage.setItem(SESSION_KEY, status);
            }}

            function startLoginFlow() {{
                log('🚀 Starting OAuth2 login flow...', 'info');
                updateWorkflowStep(1, 'complete', '✅');
                updateWorkflowStep(2, 'active', '⚡');

                log('📋 Remember to use test credentials:', 'warning');
                log('   📧 dev@example.com / 🔑 DevPassword123!', 'warning');
                log('   📧 admin@example.com / 🔑 AdminPassword123!', 'warning');
                log('🌐 Redirecting to Auth0...', 'info');

                // Store that we're starting login
                localStorage.setItem('login_initiated', 'true');

                // Redirect to login
                setTimeout(() => {{
                    window.location.href = '{base_url}/auth/login?return_to=/test/auth-console';
                }}, 1500);
            }}

            function getCookie(name) {{
                const value = `; ${{document.cookie}}`;
                const parts = value.split(`; ${{name}}=`);
                if (parts.length === 2) return parts.pop().split(';').shift();
                return null;
            }}

            function getAuthToken() {{
                // Try to get token from cookie first (preferred)
                const cookieToken = getCookie('access_token');
                if (cookieToken) {{
                    return cookieToken;
                }}

                // Fallback to localStorage for backward compatibility
                return localStorage.getItem('access_token');
            }}

            function testUserInfo() {{
                log('👤 Testing user info endpoint...', 'info');

                const token = getAuthToken();
                if (!token) {{
                    log('❌ No authentication token found', 'error');
                    log('💡 Try logging in first', 'warning');
                    updateSessionStatus('logged-out');
                    return;
                }}

                fetch('{base_url}/auth/user', {{
                    headers: {{
                        'Authorization': 'Bearer ' + token
                    }}
                }})
                .then(async response => {{
                    if (response.ok) {{
                        const user = await response.json();
                        log('✅ User info retrieved successfully:', 'success');
                        log('   📧 Email: ' + user.email, 'info');
                        log('   👤 Name: ' + user.name, 'info');
                        log('   🆔 Subject: ' + user.sub, 'debug');
                        updateSessionStatus('logged-in');
                        return user;
                    }} else {{
                        const error = await response.json();
                        log('❌ User info failed: ' + response.status + ' - ' + error.detail, 'error');
                        updateSessionStatus('logged-out');
                        return null;
                    }}
                }})
                .catch(error => {{
                    log('❌ Network error getting user info: ' + error.message, 'error');
                    updateSessionStatus('unknown');
                }});
            }}

            function testLogout() {{
                log('🚪 Testing logout endpoint...', 'info');
                updateWorkflowStep(6, 'active', '⚡');

                fetch('{base_url}/auth/logout', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{
                        'return_to': '{base_url}/test/auth-console'
                    }})
                }})
                .then(async response => {{
                    if (response.ok) {{
                        const data = await response.json();
                        log('✅ Logout endpoint responded:', 'success');
                        log('   📄 Message: ' + data.message, 'info');
                        log('   🔗 Auth0 logout URL generated', 'info');
                        log('🌐 Redirecting to Auth0 logout...', 'info');
                        updateWorkflowStep(6, 'complete', '✅');
                        updateSessionStatus('logged-out');

                        // Clear any stored tokens
                        document.cookie = 'access_token=; Max-Age=0; path=/';
                        localStorage.removeItem('access_token');

                        setTimeout(() => {{
                            window.location.href = data.redirect_url;
                        }}, 2000);
                    }} else {{
                        const error = await response.json();
                        log('❌ Logout failed: ' + response.status + ' - ' + error.detail, 'error');
                        updateWorkflowStep(6, 'error', '❌');
                    }}
                }})
                .catch(error => {{
                    log('❌ Logout request failed: ' + error.message, 'error');
                    updateWorkflowStep(6, 'error', '❌');
                }});
            }}

            async function checkAuthStatus() {{
                logConsole('🔍 Checking authentication status...');
                try {{
                    const response = await fetch('/auth/user', {{
                        credentials: 'include'
                    }});
                    
                    if (response.ok) {{
                        const userData = await response.json();
                        authToken = getAuthToken();
                        document.getElementById('authStatus').className = 'auth-status authenticated';
                        document.getElementById('authStatusText').textContent = '✅ Authenticated';
                        document.getElementById('userInfo').innerHTML = '👤 ' + userData.email + '<br>🆔 ' + userData.sub;
                        
                        logConsole('✅ Authenticated as: ' + userData.email);
                        logConsole('🆔 User ID: ' + userData.sub);
                        
                        // Enable CSV importer buttons if file is selected
                        if (selectedFile && document.getElementById('previewBtn')) {{
                            document.getElementById('previewBtn').disabled = false;
                            document.getElementById('importBtn').disabled = false;
                        }}
                    }} else {{
                        document.getElementById('authStatus').className = 'auth-status not-authenticated';
                        document.getElementById('authStatusText').textContent = '❌ Not authenticated';
                        document.getElementById('userInfo').innerHTML = '';
                        authToken = null;
                        
                        // Disable CSV importer buttons
                        if (document.getElementById('previewBtn')) {{
                            document.getElementById('previewBtn').disabled = true;
                            document.getElementById('importBtn').disabled = true;
                        }}
                    }}
                }} catch (error) {{
                    logConsole('❌ Error checking auth status: ' + error.message);
                }}
            }}

            function resetTest() {{
                log('🔄 Resetting test workflow...', 'info');

                // Reset workflow steps
                for (let i = 1; i <= 6; i++) {{
                    updateWorkflowStep(i, 'pending', '⏳');
                }}

                updateSessionStatus('unknown');
                localStorage.removeItem('login_initiated');
                localStorage.removeItem('access_token');
                document.cookie = 'access_token=; Max-Age=0; path=/';

                // Clear the first workflow step and set it to complete as a visual indicator
                updateWorkflowStep(1, 'complete', '✅');

                log('✅ Test reset complete', 'success');
                log('🔧 All tokens cleared and workflow reset', 'info');
                log('📊 Session status reset to unknown', 'info');
                log('🎯 Ready for a fresh test cycle', 'success');
                log('👉 Click "🚀 Start Login Flow" to begin', 'info');
            }}

            function debugCookies() {{
                log('🍪 Debug: Checking all cookies and tokens...', 'info');
                log('📋 Raw document.cookie: "' + document.cookie + '"', 'debug');

                const accessTokenCookie = getCookie('access_token');
                const localStorageToken = localStorage.getItem('access_token');

                if (accessTokenCookie) {{
                    log('✅ access_token cookie found: ' + accessTokenCookie.substring(0, 50) + '...', 'success');
                }} else {{
                    log('❌ No access_token cookie found', 'error');
                }}

                if (localStorageToken) {{
                    log('📦 localStorage token found: ' + localStorageToken.substring(0, 50) + '...', 'info');
                }} else {{
                    log('📦 No localStorage token found', 'info');
                }}

                const finalToken = getAuthToken();
                if (finalToken) {{
                    log('🔑 Final token from getAuthToken(): ' + finalToken.substring(0, 50) + '...', 'success');
                }} else {{
                    log('❌ getAuthToken() returned null', 'error');
                }}
            }}

            function simpleLogout() {{
                log('🚪 Performing simple logout (clearing tokens)...', 'info');
                document.cookie = 'access_token=; Max-Age=0; path=/';
                localStorage.removeItem('access_token');
                log('✅ Simple logout complete. Tokens cleared.', 'success');
                updateSessionStatus('logged-out');
                updateWorkflowStep(6, 'complete', '✅');
            }}

            function openSwagger() {
                logConsole('📖 Opening Swagger documentation...');
                window.open('/docs', '_blank');
            }
            
            async function checkSystemStatus() {
                logConsole('⚙️ Checking CSV importer system status...');
                try {
                    const response = await fetch('/import/schedule/status');
                    if (response.ok) {
                        const status = await response.json();
                        document.getElementById('systemStatusText').textContent = '✅ ' + status.status;
                        document.getElementById('systemCapabilities').innerHTML = '📁 Formats: ' + status.supported_formats.join(', ') + '<br>📏 Max size: ' + status.max_file_size_mb + 'MB';
                        logConsole('✅ CSV importer system operational');
                        logConsole('📁 Supported formats: ' + status.supported_formats.join(', '));
                    } else {
                        logConsole('❌ CSV importer system status check failed');
                    }
                } catch (error) {
                    logConsole('❌ System status error: ' + error.message);
                }
            }
            
            function setupFileUpload() {
                const fileUpload = document.getElementById('fileUpload');
                const fileInput = document.getElementById('fileInput');
                
                if (!fileUpload || !fileInput) return; // Elements not on this page
                
                fileUpload.onclick = () => fileInput.click();
                
                fileUpload.ondragover = (e) => {
                    e.preventDefault();
                    fileUpload.classList.add('dragover');
                };
                
                fileUpload.ondragleave = () => {
                    fileUpload.classList.remove('dragover');
                };
                
                fileUpload.ondrop = (e) => {
                    e.preventDefault();
                    fileUpload.classList.remove('dragover');
                    const files = e.dataTransfer.files;
                    if (files.length > 0) {
                        handleFileSelect(files[0]);
                    }
                };
                
                fileInput.onchange = (e) => {
                    if (e.target.files.length > 0) {
                        handleFileSelect(e.target.files[0]);
                    }
                };
            }
            
            function handleFileSelect(file) {
                selectedFile = file;
                logConsole('📁 File selected: ' + file.name + ' (' + (file.size / 1024).toFixed(2) + ' KB)');
                
                document.getElementById('fileInfo').innerHTML = '<strong>Selected file:</strong> ' + file.name + '<br><strong>Size:</strong> ' + (file.size / 1024).toFixed(2) + ' KB<br><strong>Type:</strong> ' + (file.type || 'Unknown');
                
                // Enable buttons if authenticated
                const authStatus = document.getElementById('authStatus');
                if (authStatus && authStatus.classList.contains('authenticated')) {
                    document.getElementById('previewBtn').disabled = false;
                    document.getElementById('importBtn').disabled = false;
                }
            }

            async function downloadTemplate() {
                logConsole('📋 Downloading CSV template...');
                try {
                    const response = await fetch('/import/schedule/template');
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'schedule_template.csv';
                    document.body.appendChild(a);
                    a.click();
                    logConsole('✅ Template downloaded successfully');
                } catch (error) {
                    logConsole('❌ Template download failed: ' + error.message);
                }
            }

            async function testPreview() {
                if (!selectedFile) {
                    logConsole('❌ No file selected');
                    return;
                }
                
                logConsole('👀 Testing preview mode with: ' + selectedFile.name);
                await uploadFile(true);
            }

            async function testImport() {
                if (!selectedFile) {
                    logConsole('❌ No file selected');
                    return;
                }
                
                logConsole('⚡ Testing import mode with: ' + selectedFile.name);
                await uploadFile(false);
            }

            async function uploadFile(previewOnly) {
                const formData = new FormData();
                formData.append('file', selectedFile);
                formData.append('preview_only', previewOnly.toString());
                
                try {
                    logConsole('📤 Uploading ' + selectedFile.name + '...');
                    const response = await fetch('/import/schedule', {
                        method: 'POST',
                        body: formData,
                        credentials: 'include'
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        logConsole('✅ Upload successful!');
                        logConsole('📊 Processing results:');
                        logConsole('   Total rows: ' + result.total_rows);
                        logConsole('   Valid rows: ' + result.valid_rows);
                        logConsole('   Errors: ' + (result.validation_errors?.length || 0));
                        logConsole('   Conflicts: ' + (result.conflicts?.length || 0));
                        logConsole('   Success: ' + result.success);
                        logConsole('   Processing time: ' + result.processing_time_ms + 'ms');
                        
                        if (result.validation_errors && result.validation_errors.length > 0) {
                            logConsole('🔍 Validation errors:');
                            result.validation_errors.forEach(error => {
                                logConsole('   Row ' + error.row_number + ': ' + error.message);
                            });
                        }
                    } else {
                        logConsole('❌ Upload failed: ' + (result.message || result.detail || 'Unknown error'));
                    }
                } catch (error) {
                    logConsole('❌ Upload error: ' + error.message);
                }
            }

            async function testValidation() {
                logConsole('🧪 Testing validation with invalid data...');
                
                // Create a test file with invalid data
                const invalidCsv = 'program,date,time,instructor,room,duration,description\\nTest Program,invalid-date,25:00,Dr. Test,Room A,999,Test description';
                
                const blob = new Blob([invalidCsv], { type: 'text/csv' });
                const file = new File([blob], 'test_invalid.csv', { type: 'text/csv' });
                
                const formData = new FormData();
                formData.append('file', file);
                formData.append('preview_only', 'true');
                
                try {
                    const response = await fetch('/import/schedule', {
                        method: 'POST',
                        body: formData,
                        credentials: 'include'
                    });
                    
                    const result = await response.json();
                    
                    logConsole('✅ Validation test completed');
                    if (result.validation_errors) {
                        logConsole('🔍 Validation results:');
                        result.validation_errors.forEach(error => {
                            logConsole('   Row ' + error.row_number + ': ' + error.message);
                        });
                    }
                } catch (error) {
                    logConsole('❌ Validation test error: ' + error.message);
                }
            }

            // Initialize on page load
            document.addEventListener('DOMContentLoaded', function() {
                logConsole('🎓 EduHub OAuth2 Test Console Initialized');
                logConsole('🔧 Auth0 Domain: ' + auth0_domain);
                logConsole('🆔 Client ID: ' + auth0_client_id);
                logConsole('🌐 Base URL: ' + base_url);
                logConsole('');
                logConsole('📋 Instructions:');
                logConsole('1. Click "🚀 Start Login Flow" to begin');
                logConsole('2. Use test credentials when prompted');
                logConsole('3. Watch the workflow steps above');
                logConsole('4. Test user info and logout when ready');
                logConsole('5. Test CSV Schedule Importer functionality');
                logConsole('');

                checkAuthStatus();
                setupFileUpload();
                checkSystemStatus();
            });

            let selectedFile = null;
        </script>
    </body>
    </html>
    """

    return html_content
