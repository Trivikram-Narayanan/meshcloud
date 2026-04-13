const API_URL = '';
let token = localStorage.getItem('mesh_token');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    if (token) {
        showDashboard();
    } else {
        showLogin();
    }

    document.getElementById('login-form').addEventListener('submit', handleLogin);
});

function showLogin() {
    document.getElementById('login-screen').classList.remove('hidden');
    document.getElementById('dashboard-screen').classList.add('hidden');
}

function showDashboard() {
    document.getElementById('login-screen').classList.add('hidden');
    document.getElementById('dashboard-screen').classList.remove('hidden');
    fetchData();
    setInterval(fetchMetrics, 5000); // Refresh metrics every 5s
}

async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);

        const res = await fetch(`${API_URL}/token`, {
            method: 'POST',
            body: formData
        });

        if (!res.ok) throw new Error('Invalid credentials');

        const data = await res.json();
        token = data.access_token;
        localStorage.setItem('mesh_token', token);
        
        document.getElementById('username').value = '';
        document.getElementById('password').value = '';
        showDashboard();
    } catch (err) {
        document.getElementById('login-error').textContent = err.message;
    }
}

function logout() {
    token = null;
    localStorage.removeItem('mesh_token');
    showLogin();
}

async function fetchWithAuth(endpoint, options = {}) {
    if (!options.headers) options.headers = {};
    options.headers['Authorization'] = `Bearer ${token}`;
    
    const res = await fetch(`${API_URL}${endpoint}`, options);
    if (res.status === 401) {
        logout();
        throw new Error('Session expired');
    }
    return res.json();
}

async function fetchData() {
    try {
        const user = await fetchWithAuth('/users/me');
        document.getElementById('display-username').textContent = user.username;
        
        await fetchMetrics();
        await fetchFiles();
    } catch (e) {
        console.error(e);
    }
}

async function fetchMetrics() {
    const system = await fetchWithAuth('/metrics/system');
    const app = await fetchWithAuth('/metrics/application');
    const status = await fetchWithAuth('/');

    document.getElementById('system-metrics').innerHTML = `
        <div class="metric-row"><span>CPU:</span> <span>${system.cpu_percent}%</span></div>
        <div class="metric-row"><span>Memory:</span> <span>${system.memory_percent}%</span></div>
        <div class="metric-row"><span>Disk:</span> <span>${system.disk_usage_percent}%</span></div>
        <div class="metric-row"><span>Uptime:</span> <span>${Math.round(app.uptime_seconds / 60)} min</span></div>
    `;

    document.getElementById('network-stats').innerHTML = `
        <div class="metric-row"><span>Status:</span> <span>${status.status}</span></div>
        <div class="metric-row"><span>Peers:</span> <span>${status.peers}</span></div>
        <div class="metric-row"><span>Req/sec:</span> <span>${app.request_rate_per_second.toFixed(2)}</span></div>
    `;
}

async function fetchFiles() {
    const files = await fetchWithAuth('/api/files?limit=10');
    const tbody = document.querySelector('#files-table tbody');
    tbody.innerHTML = files.map(f => `
        <tr>
            <td>${f.filename}</td>
            <td><small>${f.hash.substring(0, 12)}...</small></td>
            <td>${new Date(f.created_at).toLocaleString()}</td>
            <td><button onclick="alert('Download not implemented in UI yet')">Download</button></td>
        </tr>
    `).join('');
}

async function uploadFile() {
    const input = document.getElementById('file-upload');
    const file = input.files[0];
    if (!file) return;

    const chunkSize = 4 * 1024 * 1024; // 4MB
    const numChunks = Math.ceil(file.size / chunkSize);
    const progressDiv = document.getElementById('upload-progress');

    progressDiv.textContent = 'Starting upload...';

    try {
        // 1. Start session
        const startResponse = await fetchWithAuth('/start_upload', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename: file.name, total_chunks: numChunks })
        });
        const { upload_id: uploadId } = startResponse;

        // 2. Upload chunks
        const chunkHashes = [];
        for (let i = 0; i < numChunks; i++) {
            progressDiv.textContent = `Uploading chunk ${i + 1}/${numChunks}...`;
            const start = i * chunkSize;
            const end = Math.min(start + chunkSize, file.size);
            const chunk = file.slice(start, end);

            const chunkHashBuffer = await crypto.subtle.digest('SHA-256', await chunk.arrayBuffer());
            const chunkHash = Array.from(new Uint8Array(chunkHashBuffer)).map(b => b.toString(16).padStart(2, '0')).join('');
            chunkHashes.push(chunkHash);

            const formData = new FormData();
            formData.append('upload_id', uploadId);
            formData.append('chunk_index', i);
            formData.append('chunk_hash', chunkHash);
            formData.append('file', chunk, 'chunk');

            // Use raw fetch for FormData to let browser set Content-Type
            const chunkRes = await fetch(`${API_URL}/upload_chunk`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData
            });

            if (!chunkRes.ok) {
                const errorData = await chunkRes.json();
                throw new Error(`Chunk upload failed: ${errorData.detail || 'Unknown error'}`);
            }
        }

        // 3. Finalize upload
        progressDiv.textContent = 'Finalizing...';
        await fetchWithAuth('/finalize_upload', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                upload_id: uploadId,
                chunks: chunkHashes,
                filename: file.name
            })
        });

        progressDiv.textContent = 'Upload complete!';
        await fetchFiles(); // Refresh file list

    } catch (e) {
        progressDiv.textContent = `Error: ${e.message}`;
        console.error(e);
    }
}