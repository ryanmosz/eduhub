"""
Unified test console for CSV Schedule Importer with OAuth2 integration.

Provides a single-page interface for testing the complete schedule import workflow
including authentication, file upload, validation, and results display.
"""

import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/test")


@router.get("/schedule-test", response_class=HTMLResponse)
async def schedule_test_console(request: Request):
    """
    Unified test console for CSV Schedule Importer.

    Single page that handles:
    - OAuth2 authentication flow
    - File upload testing
    - Results display
    - Console output with copy functionality
    """

    # Get configuration from environment
    auth0_domain = os.getenv("AUTH0_DOMAIN", "dev-1fx6yhxxi543ipno.us.auth0.com")
    auth0_client_id = os.getenv("AUTH0_CLIENT_ID", "s05QngyZXEI3XNdirmJu0CscW1hNgaRD")
    base_url = str(request.url).replace(str(request.url.path), "")

    html_content = (
        """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 CSV Schedule Importer - Test Console</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📊</text></svg>">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #f0f0f0;
        }
        .status-section {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }
        .auth-status, .system-status {
            padding: 20px;
            border-radius: 8px;
            border: 2px solid #e0e0e0;
        }
        .auth-status.authenticated { border-color: #4CAF50; background: #f8fff8; }
        .auth-status.not-authenticated { border-color: #f44336; background: #fff8f8; }
        .system-status.operational { border-color: #2196F3; background: #f8fcff; }

        .test-section {
            margin-bottom: 30px;
            padding: 20px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            background: #fafafa;
        }
        .test-buttons { display: flex; gap: 10px; flex-wrap: wrap; margin: 15px 0; }
        .btn {
            padding: 12px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            text-decoration: none;
            display: inline-block;
            transition: all 0.2s;
        }
        .btn-primary { background: #2196F3; color: white; }
        .btn-primary:hover { background: #1976D2; }
        .btn-success { background: #4CAF50; color: white; }
        .btn-success:hover { background: #45a049; }
        .btn-warning { background: #FF9800; color: white; }
        .btn-warning:hover { background: #e68900; }
        .btn-danger { background: #f44336; color: white; }
        .btn-danger:hover { background: #d32f2f; }
        .btn-secondary { background: #757575; color: white; }
        .btn-secondary:hover { background: #616161; }

        .file-upload {
            margin: 15px 0;
            padding: 15px;
            border: 2px dashed #ccc;
            border-radius: 8px;
            text-align: center;
            background: white;
        }
        .file-upload.dragover { border-color: #2196F3; background: #f0f8ff; }

        .console {
            background: #1e1e1e;
            color: #00ff00;
            padding: 20px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            height: 300px;
            overflow-y: auto;
            position: relative;
        }
        .console-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .copy-btn {
            background: #333;
            color: #fff;
            border: 1px solid #555;
            padding: 8px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            font-weight: bold;
        }
        .copy-btn:hover { background: #555; }

        .credentials {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
        }
        .credential-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 8px 0;
        }
        .copy-credential {
            background: #6c757d;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }

        .results { margin-top: 20px; }
        .result-item {
            padding: 10px;
            margin: 5px 0;
            border-radius: 4px;
            border-left: 4px solid #ccc;
        }
        .result-success { background: #d4edda; border-color: #28a745; }
        .result-error { background: #f8d7da; border-color: #dc3545; }
        .result-warning { background: #fff3cd; border-color: #ffc107; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 CSV Schedule Importer - Test Console</h1>
            <p>Complete testing interface for file upload, authentication, and validation</p>
        </div>
        
        <div class="test-section" style="background: #e8f5e8; border-color: #28a745;">
            <h3>📋 Testing Instructions</h3>
            <div style="background: white; padding: 15px; border-radius: 8px; margin: 15px 0;">
                <h4>🎯 How to Test the CSV Schedule Importer:</h4>
                <ol style="margin: 10px 0; padding-left: 20px; line-height: 1.6;">
                    <li><strong>🔐 Authenticate First:</strong> Click "🚀 Login with Auth0" and use the test credentials below (click Copy buttons for easy access)</li>
                    <li><strong>📁 Upload a File:</strong> Either drag & drop a CSV/Excel file or click the upload area to select one</li>
                    <li><strong>📋 Get a Template:</strong> If you need a sample file, click "📋 Download Template" for the correct format</li>
                    <li><strong>👀 Test Preview:</strong> Click "👀 Test Preview" to validate your file without creating any content</li>
                    <li><strong>⚡ Test Import:</strong> Click "⚡ Test Import" to process the file and create actual Plone content</li>
                    <li><strong>🧪 Test Validation:</strong> Click "🧪 Test Validation" to see how the system handles invalid data</li>
                    <li><strong>📋 Copy Results:</strong> Use "📋 Copy All" button to copy the entire console output for sharing</li>
                </ol>
                <div style="background: #fff3cd; padding: 10px; border-radius: 4px; margin: 10px 0; border-left: 4px solid #ffc107;">
                    <strong>💡 Pro Tips:</strong>
                    <ul style="margin: 5px 0; padding-left: 20px;">
                        <li>Preview mode shows validation errors without creating content</li>
                        <li>Import mode creates actual Plone events (only works with valid data)</li>
                        <li>All test results appear in the console below and in the Results section</li>
                        <li>File size limit is 10MB, supports CSV, XLSX, and XLS formats</li>
                    </ul>
                </div>
            </div>
        </div>
        
        <div class="status-section">
            <div class="auth-status not-authenticated" id="authStatus">
                <h3>🔐 Authentication Status</h3>
                <p id="authStatusText">Not authenticated</p>
                <p id="userInfo"></p>
            </div>
            <div class="system-status operational" id="systemStatus">
                <h3>⚙️ System Status</h3>
                <p id="systemStatusText">Checking...</p>
                <p id="systemCapabilities"></p>
            </div>
        </div>

        <div class="test-section">
            <h3>🔑 Authentication</h3>
            <div class="credentials">
                <h4>Test Credentials:</h4>
                <div class="credential-row">
                    <span>📧 <strong>dev@example.com</strong></span>
                    <button class="copy-credential" onclick="copyToClipboard('dev@example.com')">Copy</button>
                </div>
                <div class="credential-row">
                    <span>🔑 <strong>DevPassword123!</strong></span>
                    <button class="copy-credential" onclick="copyToClipboard('DevPassword123!')">Copy</button>
                </div>
                <div class="credential-row">
                    <span>📧 <strong>admin@example.com</strong></span>
                    <button class="copy-credential" onclick="copyToClipboard('admin@example.com')">Copy</button>
                </div>
                <div class="credential-row">
                    <span>🔑 <strong>AdminPassword123!</strong></span>
                    <button class="copy-credential" onclick="copyToClipboard('AdminPassword123!')">Copy</button>
                </div>
            </div>
            <div class="test-buttons">
                <button class="btn btn-primary" onclick="startLogin()">🚀 Login with Auth0</button>
                <button class="btn btn-warning" onclick="checkAuthStatus()">🔍 Check Auth Status</button>
                <button class="btn btn-danger" onclick="logout()">🚪 Logout</button>
            </div>
        </div>

        <div class="test-section">
            <h3>📁 File Upload Testing</h3>
            <div class="file-upload" id="fileUpload">
                <p>📎 Drag and drop CSV/Excel files here or click to select</p>
                <input type="file" id="fileInput" accept=".csv,.xlsx,.xls" style="display: none;">
                <p style="margin-top: 10px; font-size: 14px; color: #666;">
                    Supported formats: CSV, XLSX, XLS | Max size: 10MB
                </p>
            </div>
            <div class="test-buttons">
                <button class="btn btn-secondary" onclick="downloadTemplate()">📋 Download Template</button>
                <button class="btn btn-primary" onclick="testPreview()" id="previewBtn" disabled>👀 Test Preview</button>
                <button class="btn btn-success" onclick="testImport()" id="importBtn" disabled>⚡ Test Import</button>
                <button class="btn btn-warning" onclick="testValidation()">🧪 Test Validation</button>
            </div>
            <div id="fileInfo" style="margin-top: 10px;"></div>
        </div>

        <div class="console-header">
            <h3>🖥️ Console Output</h3>
            <button class="copy-btn" onclick="copyConsole()">📋 Copy All</button>
        </div>
        <div class="console" id="console"></div>

        <div class="results" id="results"></div>
    </div>

    <script>
        let selectedFile = null;
        let authToken = null;

        // Initialize on page load
        document.addEventListener('DOMContentLoaded', function() {
            logConsole('🎓 CSV Schedule Importer Test Console Initialized');
            logConsole('🔧 Auth0 Domain: """
        + auth0_domain
        + """');
            logConsole('🆔 Client ID: """
        + auth0_client_id
        + """');
            logConsole('🌐 Base URL: """
        + base_url
        + """');
            logConsole('');
            logConsole('📋 Instructions:');
            logConsole('1. Click "🚀 Login with Auth0" to authenticate');
            logConsole('2. Upload a CSV/Excel file for testing');
            logConsole('3. Use Preview or Import buttons to test functionality');
            logConsole('4. Copy console output if you need to share results');
            logConsole('');

            checkAuthStatus();
            checkSystemStatus();
            setupFileUpload();
        });

        function logConsole(message) {
            const console = document.getElementById('console');
            const timestamp = new Date().toLocaleTimeString();
            console.innerHTML += '[' + timestamp + '] ' + message + '\\n';
            console.scrollTop = console.scrollHeight;
        }

        function copyConsole() {
            const consoleText = document.getElementById('console').innerText;
            navigator.clipboard.writeText(consoleText).then(() => {
                logConsole('📋 Console output copied to clipboard');
            });
        }

        function copyToClipboard(text) {
            navigator.clipboard.writeText(text).then(() => {
                logConsole('📋 Copied: ' + text);
            });
        }

        function startLogin() {
            logConsole('🚀 Starting OAuth2 login flow...');
            logConsole('📋 Remember to use test credentials:');
            logConsole('📧 dev@example.com / 🔑 DevPassword123!');
            logConsole('📧 admin@example.com / 🔑 AdminPassword123!');
            logConsole('🌐 Redirecting to Auth0...');

            const returnTo = encodeURIComponent(window.location.href);
            const authUrl = '/auth/login?return_to=' + returnTo;
            window.location.href = authUrl;
        }

        async function checkAuthStatus() {
            logConsole('🔍 Checking authentication status...');
            try {
                const response = await fetch('/auth/user', {
                    credentials: 'include'
                });

                if (response.ok) {
                    const userData = await response.json();
                    authToken = getAuthToken();

                    document.getElementById('authStatus').className = 'auth-status authenticated';
                    document.getElementById('authStatusText').textContent = '✅ Authenticated';
                    document.getElementById('userInfo').innerHTML = '👤 ' + userData.email + '<br>🆔 ' + userData.sub;

                    logConsole('✅ Authenticated as: ' + userData.email);
                    logConsole('🆔 User ID: ' + userData.sub);

                    // Enable file upload buttons
                    document.getElementById('previewBtn').disabled = false;
                    document.getElementById('importBtn').disabled = false;
                } else {
                    document.getElementById('authStatus').className = 'auth-status not-authenticated';
                    document.getElementById('authStatusText').textContent = '❌ Not authenticated';
                    document.getElementById('userInfo').textContent = '';
                    logConsole('❌ Not currently authenticated');

                    // Disable file upload buttons
                    document.getElementById('previewBtn').disabled = true;
                    document.getElementById('importBtn').disabled = true;
                }
            } catch (error) {
                logConsole('❌ Error checking auth status: ' + error.message);
            }
        }

        function getAuthToken() {
            // Try to get JWT from cookies
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                const [name, value] = cookie.trim().split('=');
                if (name === 'access_token' || name === 'id_token') {
                    return value;
                }
            }
            return null;
        }

        async function logout() {
            logConsole('🚪 Logging out...');
            try {
                const response = await fetch('/auth/logout', {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        return_to: window.location.href
                    })
                });

                if (response.ok) {
                    const result = await response.json();
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
                    if (result.redirect_url) {
                        logConsole('🌐 Redirecting to complete logout...');
                        setTimeout(() => {
                            window.location.href = result.redirect_url;
                        }, 1000);
                    }
                } else {
                    logConsole('❌ Logout failed');
                }
            } catch (error) {
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
            }
        }

        async function checkSystemStatus() {
            logConsole('⚙️ Checking system status...');
            try {
                const response = await fetch('/import/schedule/status');
                if (response.ok) {
                    const status = await response.json();
                    document.getElementById('systemStatusText').textContent = '✅ ' + status.status;
                    document.getElementById('systemCapabilities').innerHTML = '📁 Formats: ' + status.supported_formats.join(', ') + '<br>📏 Max size: ' + status.max_file_size_mb + 'MB';
                    logConsole('✅ System operational');
                    logConsole('📁 Supported formats: ' + status.supported_formats.join(', '));
                } else {
                    logConsole('❌ System status check failed');
                }
            } catch (error) {
                logConsole('❌ System status error: ' + error.message);
            }
        }

        function setupFileUpload() {
            const fileUpload = document.getElementById('fileUpload');
            const fileInput = document.getElementById('fileInput');

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
            if (authToken || document.getElementById('authStatus').classList.contains('authenticated')) {
                document.getElementById('previewBtn').disabled = false;
                document.getElementById('importBtn').disabled = false;
            }
        }

        async function downloadTemplate() {
            logConsole('📋 Downloading CSV template...');
            try {
                const response = await fetch('/import/schedule/template');
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'schedule_template.csv';
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
                    displayResult(result, 'success');
                    logConsole('📊 Processing results:');
                    logConsole('   Total rows: ' + result.total_rows);
                    logConsole('   Valid rows: ' + result.valid_rows);
                    logConsole('   Errors: ' + (result.validation_errors?.length || 0));
                    logConsole('   Conflicts: ' + (result.conflicts?.length || 0));
                    logConsole('   Success: ' + result.success);
                    logConsole('   Processing time: ' + result.processing_time_ms + 'ms');
                } else {
                    logConsole('❌ Upload failed: ' + (result.message || 'Unknown error'));
                    displayResult(result, 'error');
                }
            } catch (error) {
                logConsole('❌ Upload error: ' + error.message);
                displayResult({error: error.message}, 'error');
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

                if (response.ok || response.status === 422) {
                    logConsole('✅ Validation test completed');
                    displayResult(result, 'warning');
                    logConsole('🔍 Validation results:');
                    if (result.validation_errors) {
                        result.validation_errors.forEach(error => {
                            logConsole('   Row ' + error.row_number + ': ' + error.message);
                        });
                    }
                } else {
                    logConsole('❌ Validation test failed: ' + result.message);
                }
            } catch (error) {
                logConsole('❌ Validation test error: ' + error.message);
            }
        }

        function displayResult(result, type) {
            const resultsDiv = document.getElementById('results');
            const resultItem = document.createElement('div');
            resultItem.className = 'result-item result-' + type;
            resultItem.innerHTML = '<h4>📊 ' + (type === 'success' ? 'Success' : type === 'error' ? 'Error' : 'Warning') + '</h4><pre>' + JSON.stringify(result, null, 2) + '</pre>';
            resultsDiv.appendChild(resultItem);

            // Scroll to results
            resultItem.scrollIntoView({ behavior: 'smooth' });
        }
    </script>
</body>
</html>
    """
    )

    return html_content
