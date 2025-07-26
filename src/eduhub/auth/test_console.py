"""
FastAPI endpoint to serve OAuth2 testing console with integrated CSV Schedule Importer.

This provides a unified HTML interface for testing:
1. OAuth2 authentication flow (login, user info, logout)
2. CSV Schedule Importer functionality (upload, preview, import)

All testing functionality is consolidated in one place per user request.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/test", tags=["Testing"])


@router.get("/auth-console", response_class=HTMLResponse)
async def auth_console(request: Request):
    """
    Unified testing console for OAuth2 + CSV Schedule Importer.
    
    Serves an interactive HTML page that provides:
    - OAuth2 flow testing (login, user info, logout)
    - CSV file upload and processing
    - System status checking
    - Copy-to-clipboard console for debugging
    
    All functionality is consolidated per user request.
    """
    # Extract configuration from request
    auth0_domain = "dev-1fx6yhxxi543ipno.us.auth0.com"
    auth0_client_id = "s05QngyZXEI3XNdirmJu0CscW1hNgaRD"
    base_url = "http://localhost:8000"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🎓 EduHub Testing Console</title>
        <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🎓</text></svg>">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
                color: #333;
            }}
            
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            
            .header {{
                background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            
            .header h1 {{
                font-size: 2.5rem;
                margin-bottom: 10px;
            }}
            
            .header p {{
                font-size: 1.2rem;
                opacity: 0.9;
            }}
            
            .content {{
                padding: 40px;
            }}
            
            .test-section {{
                background: #f8fafc;
                border-radius: 10px;
                padding: 25px;
                margin-bottom: 30px;
                border-left: 5px solid #4f46e5;
            }}
            
            .test-section h3 {{
                font-size: 1.5rem;
                margin-bottom: 20px;
                color: #1e293b;
            }}
            
            .auth-status {{
                display: inline-block;
                padding: 10px 20px;
                border-radius: 25px;
                font-weight: bold;
                margin-bottom: 15px;
                font-size: 1.1rem;
            }}
            
            .authenticated {{
                background: #10b981;
                color: white;
            }}
            
            .not-authenticated {{
                background: #ef4444;
                color: white;
            }}
            
            .workflow-steps {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }}
            
            .workflow-step {{
                background: white;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
                border: 2px solid #e2e8f0;
                transition: all 0.3s ease;
            }}
            
            .workflow-step.active {{
                border-color: #4f46e5;
                background: #f0f9ff;
                transform: translateY(-2px);
            }}
            
            .workflow-step.completed {{
                border-color: #10b981;
                background: #f0fdf4;
            }}
            
            .test-buttons {{
                display: flex;
                flex-wrap: wrap;
                gap: 15px;
                margin: 20px 0;
            }}
            
            .btn {{
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                text-decoration: none;
                display: inline-block;
            }}
            
            .btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 8px 16px rgba(0,0,0,0.2);
            }}
            
            .btn-primary {{
                background: #4f46e5;
                color: white;
            }}
            
            .btn-success {{
                background: #10b981;
                color: white;
            }}
            
            .btn-warning {{
                background: #f59e0b;
                color: white;
            }}
            
            .btn-danger {{
                background: #ef4444;
                color: white;
            }}
            
            .btn-info {{
                background: #3b82f6;
                color: white;
            }}
            
            .btn-secondary {{
                background: #6b7280;
                color: white;
            }}
            
            .btn:disabled {{
                background: #9ca3af;
                cursor: not-allowed;
                transform: none;
            }}
            
            .credentials {{
                background: #fef3c7;
                border: 1px solid #f59e0b;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
            }}
            
            .credential-item {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin: 10px 0;
                padding: 10px;
                background: white;
                border-radius: 5px;
                cursor: pointer;
                transition: background 0.2s;
            }}
            
            .credential-item:hover {{
                background: #f9fafb;
            }}
            
            .file-upload {{
                border: 3px dashed #cbd5e1;
                border-radius: 10px;
                padding: 40px;
                text-align: center;
                margin: 20px 0;
                transition: all 0.3s ease;
                cursor: pointer;
            }}
            
            .file-upload:hover {{
                border-color: #4f46e5;
                background: #f8fafc;
            }}
            
            .file-upload.dragover {{
                border-color: #10b981;
                background: #f0fdf4;
            }}
            
            .console {{
                background: #1e293b;
                color: #e2e8f0;
                border-radius: 8px;
                padding: 20px;
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                font-size: 14px;
                max-height: 400px;
                overflow-y: auto;
                margin: 20px 0;
                white-space: pre-wrap;
                word-wrap: break-word;
            }}
            
            .console-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }}
            
            .console-header h4 {{
                color: #1e293b;
                margin: 0;
            }}
            
            .copy-btn {{
                background: #6b7280;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 0.9rem;
            }}
            
            .copy-btn:hover {{
                background: #4b5563;
            }}
            
            .instructions {{
                background: #dbeafe;
                border: 1px solid #3b82f6;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
            }}
            
            .instructions h4 {{
                color: #1e40af;
                margin-bottom: 15px;
            }}
            
            .instructions ol {{
                padding-left: 20px;
                line-height: 1.6;
            }}
            
            .instructions li {{
                margin: 8px 0;
            }}
            
            .pro-tips {{
                background: #f0f9ff;
                border: 1px solid #0ea5e9;
                border-radius: 8px;
                padding: 15px;
                margin: 15px 0;
            }}
            
            .pro-tips h5 {{
                color: #0c4a6e;
                margin-bottom: 10px;
            }}
            
            .pro-tips ul {{
                padding-left: 20px;
                line-height: 1.5;
            }}
            
            .pro-tips li {{
                margin: 5px 0;
                font-size: 0.95rem;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎓 EduHub Testing Console</h1>
                <p>OAuth2 Authentication + CSV Schedule Importer Testing</p>
            </div>
            
            <div class="content">
                <!-- Instructions Section -->
                <div class="instructions">
                    <h4>📋 Complete Testing Instructions</h4>
                    <ol>
                        <li><strong>OAuth2 Testing:</strong> Click "🚀 Start Login Flow" → use test credentials → verify user info → test logout</li>
                        <li><strong>CSV Importer Testing:</strong> Must be authenticated first → upload/drag CSV file → test preview → test import</li>
                        <li><strong>System Testing:</strong> Check system status, download template, test validation with invalid data</li>
                        <li><strong>Problem Reporting:</strong> Use "Copy All" button to copy console logs for reporting issues</li>
                    </ol>
                    
                    <div class="pro-tips">
                        <h5>💡 Pro Tips</h5>
                        <ul>
                            <li>Click test credentials below to auto-copy them</li>
                            <li>Watch the workflow tracker to see your progress</li>
                            <li>CSV importer buttons only work when authenticated</li>
                            <li>Use "Download Template" if you don't have a CSV file</li>
                            <li>Try "Test Validation" to see error handling</li>
                        </ul>
                    </div>
                </div>
                
                <!-- OAuth2 Testing Section -->
                <div class="test-section">
                    <h3>🔐 OAuth2 Authentication Testing</h3>
                    
                    <div id="authStatus" class="auth-status not-authenticated">
                        <span id="authStatusText">❌ Not authenticated</span>
                    </div>
                    
                    <div id="userInfo" style="margin: 10px 0; font-weight: bold;"></div>
                    
                    <div class="workflow-steps">
                        <div class="workflow-step" id="step1">
                            <div style="font-size: 2rem; margin-bottom: 10px;">🚀</div>
                            <div>Login Flow</div>
                        </div>
                        <div class="workflow-step" id="step2">
                            <div style="font-size: 2rem; margin-bottom: 10px;">🔑</div>
                            <div>Auth0 Login</div>
                        </div>
                        <div class="workflow-step" id="step3">
                            <div style="font-size: 2rem; margin-bottom: 10px;">✅</div>
                            <div>User Verified</div>
                        </div>
                        <div class="workflow-step" id="step4">
                            <div style="font-size: 2rem; margin-bottom: 10px;">🚪</div>
                            <div>Logout</div>
                        </div>
                    </div>
                    
                    <div class="credentials">
                        <h4>🧪 Test Credentials (Click to Copy)</h4>
                        <div class="credential-item" onclick="copyToClipboard('dev@example.com')">
                            <span>📧 dev@example.com</span>
                            <span style="color: #6b7280;">(Click to copy)</span>
                        </div>
                        <div class="credential-item" onclick="copyToClipboard('DevPassword123!')">
                            <span>🔑 DevPassword123!</span>
                            <span style="color: #6b7280;">(Click to copy)</span>
                        </div>
                        <div class="credential-item" onclick="copyToClipboard('admin@example.com')">
                            <span>👑 admin@example.com</span>
                            <span style="color: #6b7280;">(Admin account)</span>
                        </div>
                        <div class="credential-item" onclick="copyToClipboard('AdminPassword123!')">
                            <span>🔐 AdminPassword123!</span>
                            <span style="color: #6b7280;">(Admin password)</span>
                        </div>
                    </div>
                    
                    <div class="test-buttons">
                        <button class="btn btn-primary" onclick="testLogin()">🚀 Start Login Flow</button>
                        <button class="btn btn-info" onclick="testUserInfo()">👤 Get User Info</button>
                        <button class="btn btn-warning" onclick="testLogout()">🚪 Test Logout</button>
                        <button class="btn btn-secondary" onclick="openSwagger()">📖 API Docs</button>
                    </div>
                </div>
                
                <!-- CSV Schedule Importer Testing Section -->
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
                
                <!-- Console Section -->
                <div class="test-section">
                    <div class="console-header">
                        <h4>📱 Test Console</h4>
                        <button class="copy-btn" onclick="copyConsole()">Copy All</button>
                    </div>
                    <div id="console" class="console"></div>
                </div>
            </div>
        </div>

        <script>
            // Global variables
            let authToken = null;
            let selectedFile = null;
            const auth0_domain = '{auth0_domain}';
            const auth0_client_id = '{auth0_client_id}';
            const base_url = '{base_url}';

            // Initialize on page load
            document.addEventListener('DOMContentLoaded', function() {{
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
            }});

            // Console logging function
            function logConsole(message) {{
                const timestamp = new Date().toLocaleTimeString();
                const console_div = document.getElementById('console');
                console_div.textContent += `[${{timestamp}}] ${{message}}\\n`;
                console_div.scrollTop = console_div.scrollHeight;
                
                // Store in localStorage for persistence
                const logs = JSON.parse(localStorage.getItem('consoleLogs') || '[]');
                logs.push(`[${{timestamp}}] ${{message}}`);
                localStorage.setItem('consoleLogs', JSON.stringify(logs.slice(-100))); // Keep last 100 logs
            }}

            // Load persisted logs
            function loadPersistedLogs() {{
                const logs = JSON.parse(localStorage.getItem('consoleLogs') || '[]');
                const console_div = document.getElementById('console');
                console_div.textContent = logs.join('\\n') + '\\n';
                console_div.scrollTop = console_div.scrollHeight;
            }}

            // Copy console content to clipboard
            function copyConsole() {{
                const console_div = document.getElementById('console');
                navigator.clipboard.writeText(console_div.textContent).then(() => {{
                    logConsole('📋 Console output copied to clipboard');
                }}).catch(err => {{
                    logConsole('❌ Failed to copy console output: ' + err.message);
                }});
            }}

            // Copy text to clipboard
            function copyToClipboard(text) {{
                navigator.clipboard.writeText(text).then(() => {{
                    logConsole('📋 Copied: ' + text);
                }}).catch(err => {{
                    logConsole('❌ Failed to copy: ' + err.message);
                }});
            }}

            // Get auth token from cookies
            function getAuthToken() {{
                const cookies = document.cookie.split(';');
                for (let cookie of cookies) {{
                    const [name, value] = cookie.trim().split('=');
                    if (name === 'access_token' || name === 'id_token') {{
                        return value;
                    }}
                }}
                return null;
            }}

            // OAuth2 Flow Functions
            async function testLogin() {{
                logConsole('🚀 Starting OAuth2 login flow...');
                logConsole('📋 Remember to use test credentials:');
                logConsole('📧 dev@example.com / 🔑 DevPassword123!');
                logConsole('📧 admin@example.com / 🔑 AdminPassword123!');
                
                document.getElementById('step1').classList.add('active');
                
                const return_to = encodeURIComponent(window.location.href);
                const loginUrl = `/auth/login?return_to=${{return_to}}`;
                
                logConsole('🌐 Redirecting to Auth0...');
                window.location.href = loginUrl;
            }}

            async function testUserInfo() {{
                logConsole('👤 Testing user info endpoint...');
                try {{
                    const response = await fetch('/auth/user', {{
                        credentials: 'include'
                    }});
                    
                    if (response.ok) {{
                        const userData = await response.json();
                        logConsole('✅ User info retrieved successfully:');
                        logConsole('📧 Email: ' + userData.email);
                        logConsole('🆔 ID: ' + userData.sub);
                        logConsole('👤 Name: ' + userData.name);
                        logConsole('🏠 Plone ID: ' + (userData.plone_user_id || 'Not synced'));
                        
                        document.getElementById('step3').classList.add('completed');
                        return userData;
                    }} else {{
                        logConsole('❌ Failed to get user info: ' + response.status);
                        return null;
                    }}
                }} catch (error) {{
                    logConsole('❌ Error getting user info: ' + error.message);
                    return null;
                }}
            }}

            async function logout() {{
                logConsole('🚪 Logging out...');
                try {{
                    const response = await fetch('/auth/logout', {{
                        method: 'POST',
                        credentials: 'include',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify({{
                            return_to: window.location.href // This return_to is now ignored by server
                        }})
                    }});
                    
                    if (response.ok) {{
                        const result = await response.json(); // Parse JSON response
                        logConsole('✅ Logout successful');
                        
                        // Clear any remaining cookies on client side
                        document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
                        document.cookie = 'id_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
                        
                        // Update UI immediately
                        document.getElementById('authStatus').className = 'auth-status not-authenticated';
                        document.getElementById('authStatusText').textContent = '❌ Not authenticated';
                        document.getElementById('userInfo').textContent = '';
                        document.getElementById('previewBtn').disabled = true;
                        document.getElementById('importBtn').disabled = true;
                        
                        logConsole('🔄 Session cleared locally');
                        
                        // Redirect to Auth0 logout (clears Auth0 session)
                        if (result.redirect_url) {{
                            logConsole('🌐 Redirecting to complete logout...');
                            setTimeout(() => {{
                                window.location.href = result.redirect_url;
                            }}, 1000);
                        }}
                    }} else {{
                        logConsole('❌ Logout failed');
                    }}
                }} catch (error) {{
                    logConsole('❌ Logout error: ' + error.message);
                    
                    // Force clear cookies even if request failed
                    document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
                    document.cookie = 'id_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
                    
                    // Update UI
                    document.getElementById('authStatus').className = 'auth-status not-authenticated';
                    document.getElementById('authStatusText').textContent = '❌ Not authenticated';
                    document.getElementById('userInfo').textContent = '';
                    document.getElementById('previewBtn').disabled = true;
                    document.getElementById('importBtn').disabled = true;
                    
                    logConsole('🔄 Session cleared locally (fallback)');
                }}
            }}

            function testLogout() {{
                logout();
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
                    document.getElementById('authStatus').className = 'auth-status not-authenticated';
                    document.getElementById('authStatusText').textContent = '❌ Error checking status';
                    authToken = null;
                }}
            }}

            function openSwagger() {{
                logConsole('📖 Opening Swagger documentation...');
                window.open('/docs', '_blank');
            }}
            
            async function checkSystemStatus() {{
                logConsole('⚙️ Checking CSV importer system status...');
                try {{
                    const response = await fetch('/import/schedule/status');
                    if (response.ok) {{
                        const status = await response.json();
                        document.getElementById('systemStatusText').textContent = '✅ ' + status.status;
                        document.getElementById('systemCapabilities').innerHTML = '📁 Formats: ' + status.supported_formats.join(', ') + '<br>📏 Max size: ' + status.max_file_size_mb + 'MB';
                        logConsole('✅ CSV importer system operational');
                    }} else {{
                        logConsole('❌ System status check failed');
                        document.getElementById('systemStatusText').textContent = '❌ System check failed';
                    }}
                }} catch (error) {{
                    logConsole('❌ Error checking system status: ' + error.message);
                    document.getElementById('systemStatusText').textContent = '❌ Error checking system';
                }}
            }}

            function setupFileUpload() {{
                const fileUpload = document.getElementById('fileUpload');
                const fileInput = document.getElementById('fileInput');
                const fileInfo = document.getElementById('fileInfo');

                // Click to select file
                fileUpload.addEventListener('click', () => {{
                    fileInput.click();
                }});

                // Handle file selection
                fileInput.addEventListener('change', handleFileSelect);

                // Drag and drop handlers
                fileUpload.addEventListener('dragover', (e) => {{
                    e.preventDefault();
                    fileUpload.classList.add('dragover');
                }});

                fileUpload.addEventListener('dragleave', () => {{
                    fileUpload.classList.remove('dragover');
                }});

                fileUpload.addEventListener('drop', (e) => {{
                    e.preventDefault();
                    fileUpload.classList.remove('dragover');
                    
                    const files = e.dataTransfer.files;
                    if (files.length > 0) {{
                        fileInput.files = files;
                        handleFileSelect({{target: fileInput}});
                    }}
                }});
            }}

            function handleFileSelect(event) {{
                const file = event.target.files[0];
                if (file) {{
                    selectedFile = file;
                    const fileInfo = document.getElementById('fileInfo');
                    fileInfo.innerHTML = `📄 ${{file.name}} (${{(file.size / 1024).toFixed(1)}} KB)`;
                    
                    logConsole('📁 File selected: ' + file.name);
                    logConsole('📏 Size: ' + (file.size / 1024).toFixed(1) + ' KB');
                    
                    // Enable preview/import buttons if authenticated
                    checkAuthStatus();
                }}
            }}

            function downloadTemplate() {{
                logConsole('📋 Downloading CSV template...');
                window.location.href = '/import/schedule/template';
                logConsole('✅ Template download started');
            }}

            async function testPreview() {{
                if (!selectedFile) {{
                    logConsole('❌ No file selected for preview');
                    return;
                }}

                logConsole('👀 Testing preview mode with: ' + selectedFile.name);
                await uploadFile(true); // preview_only = true
            }}

            async function testImport() {{
                if (!selectedFile) {{
                    logConsole('❌ No file selected for import');
                    return;
                }}

                logConsole('⚡ Testing import mode with: ' + selectedFile.name);
                await uploadFile(false); // preview_only = false
            }}

            async function uploadFile(previewOnly) {{
                const formData = new FormData();
                formData.append('file', selectedFile);
                formData.append('preview_only', previewOnly);

                try {{
                    logConsole(`🔄 Uploading file for ${{previewOnly ? 'preview' : 'import'}}...`);
                    
                    const response = await fetch('/import/schedule', {{
                        method: 'POST',
                        body: formData,
                        credentials: 'include'
                    }});

                    if (response.ok) {{
                        const result = await response.json();
                        logConsole(`✅ ${{previewOnly ? 'Preview' : 'Import'}} successful!`);
                        logConsole('📊 Total rows: ' + result.total_rows);
                        logConsole('✅ Valid rows: ' + result.valid_rows);
                        logConsole('⚠️ Validation errors: ' + result.validation_errors.length);
                        logConsole('⚡ Conflicts: ' + result.conflicts.length);
                        logConsole('⏱️ Processing time: ' + result.processing_time_ms + 'ms');
                        
                        if (result.created_uids && result.created_uids.length > 0) {{
                            logConsole('🆔 Created UIDs: ' + result.created_uids.slice(0, 3).join(', ') + 
                                     (result.created_uids.length > 3 ? '...' : ''));
                        }}
                        
                        if (result.validation_errors.length > 0) {{
                            logConsole('📝 Validation errors found:');
                            result.validation_errors.slice(0, 5).forEach(error => {{
                                logConsole(`  Row ${{error.row_number}}: ${{error.message}}`);
                            }});
                        }}
                    }} else {{
                        const error = await response.json();
                        logConsole(`❌ ${{previewOnly ? 'Preview' : 'Import'}} failed: ` + error.detail);
                    }}
                }} catch (error) {{
                    logConsole(`❌ Upload error: ` + error.message);
                }}
            }}

            async function testValidation() {{
                logConsole('🧪 Testing validation with invalid data...');
                
                // Create a CSV with invalid data for testing
                const invalidCsv = `program,date,time,instructor,room,duration,description
Python 101,2025-02-01,09:00,Dr. Smith,Room A,90,Valid entry
,2025-02-01,14:30,Prof. Johnson,Room B,60,Missing program name
Math Workshop,invalid-date,14:30,Prof. Johnson,Room B,60,Invalid date format
Science Lab,2025-02-02,25:00,Dr. Williams,Lab 1,120,Invalid time format
History Seminar,2025-02-02,16:00,,Room C,75,Missing instructor
Art Class,2025-02-03,11:00,Ms. Davis,,90,Missing room
Physics Lecture,2025-02-03,13:00,Dr. Anderson,Auditorium,999,Duration too long`;

                const blob = new Blob([invalidCsv], {{type: 'text/csv'}});
                const file = new File([blob], 'test_validation.csv', {{type: 'text/csv'}});
                
                selectedFile = file;
                document.getElementById('fileInfo').innerHTML = '🧪 test_validation.csv (validation test)';
                
                logConsole('📁 Generated test file with validation errors');
                await uploadFile(true); // Test preview with invalid data
            }}

            // Load persisted logs on page load
            loadPersistedLogs();

            // Check auth status periodically
            setInterval(checkAuthStatus, 30000); // Every 30 seconds
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)
