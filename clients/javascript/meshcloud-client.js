/**
 * MeshCloud JavaScript Client Library
 * A JavaScript client for interacting with MeshCloud distributed file storage systems.
 *
 * @version 0.1.0
 * @author MeshCloud Contributors
 * @license Apache 2.0
 */

class MeshCloudError extends Error {
    constructor(message, statusCode = null, responseData = {}) {
        super(message);
        this.name = 'MeshCloudError';
        this.statusCode = statusCode;
        this.responseData = responseData;
    }
}

class AuthenticationError extends MeshCloudError {
    constructor(message) {
        super(message);
        this.name = 'AuthenticationError';
    }
}

class UploadError extends MeshCloudError {
    constructor(message) {
        super(message);
        this.name = 'UploadError';
    }
}

class APIError extends MeshCloudError {
    constructor(message, statusCode, responseData) {
        super(message, statusCode, responseData);
        this.name = 'APIError';
    }
}

class RateLimitError extends MeshCloudError {
    constructor(message, retryAfter = null) {
        super(message);
        this.name = 'RateLimitError';
        this.retryAfter = retryAfter;
    }
}

/**
 * MeshCloud Client for JavaScript
 *
 * Provides a high-level interface for file uploads, downloads, and management
 * operations in a MeshCloud distributed storage network.
 *
 * @example
 * ```javascript
 * const client = new MeshCloudClient('https://meshcloud.example.com');
 * await client.authenticate('username', 'password');
 *
 * // Upload a file
 * const result = await client.uploadFile(fileInput.files[0]);
 * console.log(`Uploaded with hash: ${result.hash}`);
 *
 * // Check file existence
 * const exists = await client.fileExists(result.hash);
 * console.log(`File exists: ${exists}`);
 * ```
 */
class MeshCloudClient {
    /**
     * Create a new MeshCloud client instance.
     *
     * @param {string} baseUrl - Base URL of the MeshCloud node
     * @param {Object} options - Configuration options
     * @param {string} options.username - Username for authentication
     * @param {string} options.password - Password for authentication
     * @param {number} options.timeout - Request timeout in milliseconds (default: 30000)
     * @param {number} options.maxRetries - Maximum number of retries (default: 3)
     * @param {boolean} options.verifySSL - Whether to verify SSL certificates (default: true)
     * @param {number} options.chunkSize - Size of chunks for file uploads in bytes (default: 4MB)
     */
    constructor(baseUrl, options = {}) {
        this.baseUrl = baseUrl.replace(/\/$/, ''); // Remove trailing slash
        this.username = options.username;
        this.password = options.password;
        this.timeout = options.timeout || 30000;
        this.maxRetries = options.maxRetries || 3;
        this.verifySSL = options.verifySSL !== false;
        this.chunkSize = options.chunkSize || 4 * 1024 * 1024; // 4MB

        // Authentication state
        this.token = null;
        this.tokenExpires = null;

        // Auto-authenticate if credentials provided
        if (this.username && this.password) {
            this.authenticate(this.username, this.password);
        }
    }

    /**
     * Authenticate with the MeshCloud node.
     *
     * @param {string} username - Username for authentication
     * @param {string} password - Password for authentication
     * @returns {Promise<Object>} Authentication response
     * @throws {AuthenticationError} If authentication fails
     */
    async authenticate(username, password) {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        try {
            const response = await fetch(`${this.baseUrl}/token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData,
                signal: AbortSignal.timeout(this.timeout),
            });

            if (!response.ok) {
                if (response.status === 401) {
                    throw new AuthenticationError('Invalid username or password');
                }
                throw new APIError(`Authentication failed: ${response.statusText}`, response.status);
            }

            const tokenData = await response.json();
            this.token = tokenData.access_token;
            this.tokenExpires = Date.now() + (30 * 60 * 1000); // 30 minutes

            return tokenData;
        } catch (error) {
            if (error instanceof MeshCloudError) {
                throw error;
            }
            throw new APIError(`Connection failed: ${error.message}`);
        }
    }

    /**
     * Ensure client is authenticated and token is valid.
     * @private
     */
    _ensureAuthenticated() {
        if (!this.token) {
            throw new AuthenticationError('Not authenticated. Call authenticate() first.');
        }

        // Check if token is about to expire (within 5 minutes)
        if (this.tokenExpires && Date.now() > (this.tokenExpires - 5 * 60 * 1000)) {
            if (this.username && this.password) {
                return this.authenticate(this.username, this.password);
            } else {
                throw new AuthenticationError('Token expired and no credentials available for renewal');
            }
        }
    }

    /**
     * Make an authenticated HTTP request.
     * @private
     */
    async _makeRequest(method, endpoint, options = {}) {
        await this._ensureAuthenticated();

        const url = `${this.baseUrl}${endpoint}`;
        const headers = {
            'Authorization': `Bearer ${this.token}`,
            ...options.headers,
        };

        const requestOptions = {
            method,
            headers,
            signal: AbortSignal.timeout(this.timeout),
            ...options,
        };

        let lastError;
        for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
            try {
                const response = await fetch(url, requestOptions);
                return this._handleResponse(response);
            } catch (error) {
                lastError = error;
                if (attempt < this.maxRetries && this._isRetryableError(error)) {
                    await this._delay(Math.pow(2, attempt) * 1000); // Exponential backoff
                    continue;
                }
                break;
            }
        }

        throw new APIError(`Request failed after ${this.maxRetries + 1} attempts: ${lastError.message}`);
    }

    /**
     * Check if an error is retryable.
     * @private
     */
    _isRetryableError(error) {
        return error.name === 'TypeError' || error.message.includes('fetch');
    }

    /**
     * Add delay for retry backoff.
     * @private
     */
    _delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Handle HTTP response and raise appropriate exceptions.
     * @private
     */
    async _handleResponse(response) {
        if (response.status === 401) {
            throw new AuthenticationError('Authentication required or token expired');
        } else if (response.status === 403) {
            throw new MeshCloudError('Access denied', response.status);
        } else if (response.status === 404) {
            throw new MeshCloudError('Resource not found', response.status);
        } else if (response.status === 413) {
            throw new MeshCloudError('File too large', response.status);
        } else if (response.status === 429) {
            const retryAfter = response.headers.get('Retry-After');
            throw new RateLimitError(
                'Rate limit exceeded',
                retryAfter ? parseInt(retryAfter) : null
            );
        } else if (!response.ok) {
            let message = response.statusText;
            try {
                const errorData = await response.json();
                message = errorData.detail || errorData.error || message;
            } catch (e) {
                // Ignore JSON parsing errors
            }
            throw new APIError(message, response.status);
        }

        return response;
    }

    /**
     * Get node status information.
     *
     * @returns {Promise<Object>} Node status information
     */
    async getStatus() {
        const response = await this._makeRequest('GET', '/');
        return response.json();
    }

    /**
     * Perform a health check on the node.
     *
     * @returns {Promise<Object>} Health status information
     */
    async healthCheck() {
        const response = await this._makeRequest('GET', '/health');
        return response.json();
    }

    /**
     * Check if a file exists on the node.
     *
     * @param {string} fileHash - SHA256 hash of the file
     * @returns {Promise<boolean>} True if file exists, false otherwise
     */
    async fileExists(fileHash) {
        try {
            const response = await this._makeRequest('GET', `/has_file/${fileHash}`);
            const data = await response.json();
            return data.exists || false;
        } catch (error) {
            if (error.statusCode === 404) {
                return false;
            }
            throw error;
        }
    }

    /**
     * Get all nodes that have a copy of the file.
     *
     * @param {string} fileHash - SHA256 hash of the file
     * @returns {Promise<string[]>} List of node URLs that have the file
     */
    async getFileLocations(fileHash) {
        const response = await this._makeRequest('GET', `/file_locations/${fileHash}`);
        const data = await response.json();
        return data.nodes || [];
    }

    /**
     * Upload a file to MeshCloud.
     *
     * @param {File|Blob} file - File to upload
     * @param {Object} options - Upload options
     * @param {string} options.filename - Optional filename override
     * @param {Function} options.onProgress - Progress callback function
     * @returns {Promise<Object>} Upload result with file hash and metadata
     */
    async uploadFile(file, options = {}) {
        const filename = options.filename || file.name;
        const onProgress = options.onProgress;

        // For large files, use chunked upload
        if (file.size > this.chunkSize) {
            return this._uploadChunked(file, filename, onProgress);
        } else {
            return this._uploadSimple(file, filename, onProgress);
        }
    }

    /**
     * Upload a file in a single request.
     * @private
     */
    async _uploadSimple(file, filename, onProgress) {
        // Note: This would need to be implemented based on the actual API
        // For now, we'll use chunked upload for all files
        return this._uploadChunked(file, filename, onProgress);
    }

    /**
     * Upload a file using chunked upload.
     * @private
     */
    async _uploadChunked(file, filename, onProgress) {
        const numChunks = Math.ceil(file.size / this.chunkSize);

        // Start upload session
        const startResponse = await this._makeRequest('POST', '/start_upload', {
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                filename: filename,
                total_chunks: numChunks
            }),
        });

        const { upload_id: uploadId } = await startResponse.json();

        try {
            const chunks = [];

            for (let chunkIndex = 0; chunkIndex < numChunks; chunkIndex++) {
                const start = chunkIndex * this.chunkSize;
                const end = Math.min(start + this.chunkSize, file.size);
                const chunk = file.slice(start, end);

                // Calculate chunk hash
                const chunkHash = await this._calculateHash(chunk);

                // Upload chunk
                const formData = new FormData();
                formData.append('upload_id', uploadId);
                formData.append('chunk_index', chunkIndex.toString());
                formData.append('chunk_hash', chunkHash);
                formData.append('file', chunk, 'chunk');

                await this._makeRequest('POST', '/upload_chunk', {
                    body: formData,
                    // Don't set Content-Type header - let browser set it with boundary
                    headers: {},
                });

                chunks.push(chunkHash);

                // Progress callback
                if (onProgress) {
                    const progress = ((chunkIndex + 1) / numChunks) * 100;
                    onProgress(progress, chunkIndex + 1, numChunks);
                }
            }

            // Finalize upload
            const finalizeResponse = await this._makeRequest('POST', '/finalize_upload', {
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    upload_id: uploadId,
                    chunks: chunks,
                    filename: filename
                }),
            });

            return finalizeResponse.json();

        } catch (error) {
            // TODO: Cleanup partial upload
            throw new UploadError(`Upload failed: ${error.message}`);
        }
    }

    /**
     * Calculate SHA256 hash of a Blob/File.
     * @private
     */
    async _calculateHash(blob) {
        const buffer = await blob.arrayBuffer();
        const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }

    /**
     * Get the status of an ongoing upload.
     *
     * @param {string} uploadId - Upload session ID
     * @returns {Promise<Object>} Upload status information
     */
    async getUploadStatus(uploadId) {
        const response = await this._makeRequest('GET', `/upload_status/${uploadId}`);
        return response.json();
    }

    /**
     * Get system or application metrics.
     *
     * @param {string} metricType - Type of metrics ('system', 'application', or 'health')
     * @returns {Promise<Object>} Metrics data
     */
    async getMetrics(metricType = 'application') {
        let endpoint;
        if (metricType === 'health') {
            endpoint = '/metrics/health/detailed';
        } else if (metricType === 'system') {
            endpoint = '/metrics/system';
        } else {
            endpoint = '/metrics/application';
        }

        const response = await this._makeRequest('GET', endpoint);
        return response.json();
    }

    /**
     * Get recent API requests.
     *
     * @param {number} limit - Maximum number of requests to return
     * @returns {Promise<Object>} Recent request data
     */
    async getRecentRequests(limit = 50) {
        const response = await this._makeRequest('GET', `/metrics/requests/recent?limit=${limit}`);
        return response.json();
    }

    /**
     * Get recent API errors.
     *
     * @param {number} limit - Maximum number of errors to return
     * @returns {Promise<Object>} Recent error data
     */
    async getRecentErrors(limit = 20) {
        const response = await this._makeRequest('GET', `/metrics/errors/recent?limit=${limit}`);
        return response.json();
    }
}

// Export for different module systems
if (typeof module !== 'undefined' && module.exports) {
    // CommonJS
    module.exports = {
        MeshCloudClient,
        MeshCloudError,
        AuthenticationError,
        UploadError,
        APIError,
        RateLimitError,
    };
} else if (typeof define === 'function' && define.amd) {
    // AMD
    define([], function() {
        return {
            MeshCloudClient,
            MeshCloudError,
            AuthenticationError,
            UploadError,
            APIError,
            RateLimitError,
        };
    });
} else if (typeof window !== 'undefined') {
    // Browser global
    window.MeshCloudClient = MeshCloudClient;
    window.MeshCloudError = MeshCloudError;
    window.AuthenticationError = AuthenticationError;
    window.UploadError = UploadError;
    window.APIError = APIError;
    window.RateLimitError = RateLimitError;
}