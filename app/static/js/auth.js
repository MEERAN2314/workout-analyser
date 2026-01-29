/**
 * Authentication JavaScript - Handles login, registration, and token management
 */

// API Base URL
const API_BASE = '';

// Token management
class TokenManager {
    static setToken(token) {
        localStorage.setItem('access_token', token);
    }
    
    static getToken() {
        return localStorage.getItem('access_token');
    }
    
    static removeToken() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
    }
    
    static setUser(user) {
        localStorage.setItem('user', JSON.stringify(user));
    }
    
    static getUser() {
        const user = localStorage.getItem('user');
        return user ? JSON.parse(user) : null;
    }
    
    static isAuthenticated() {
        return !!this.getToken();
    }
}

// API Helper
class ApiClient {
    static async request(url, options = {}) {
        const token = TokenManager.getToken();
        
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };
        
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
        
        try {
            const response = await fetch(url, config);
            
            if (response.status === 401) {
                // Token expired or invalid
                TokenManager.removeToken();
                if (window.location.pathname !== '/auth/login') {
                    window.location.href = '/auth/login';
                }
                throw new Error('Authentication required');
            }
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || 'Request failed');
            }
            
            return data;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }
    
    static async get(url) {
        return this.request(url, { method: 'GET' });
    }
    
    static async post(url, data) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
    
    static async put(url, data) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }
    
    static async delete(url) {
        return this.request(url, { method: 'DELETE' });
    }
}

// Alert Helper
function showAlert(message, type = 'info', containerId = 'alert-container') {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    container.innerHTML = alertHtml;
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alert = container.querySelector('.alert');
        if (alert) {
            alert.remove();
        }
    }, 5000);
}

// Loading Helper
function setLoading(buttonId, loading = true) {
    const button = document.getElementById(buttonId);
    if (!button) return;
    
    if (loading) {
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
    } else {
        button.disabled = false;
        // Restore original content (you might want to store this)
        if (buttonId === 'login-btn') {
            button.innerHTML = '<i class="fas fa-sign-in-alt me-2"></i>Login';
        } else if (buttonId === 'register-btn') {
            button.innerHTML = '<i class="fas fa-user-plus me-2"></i>Create Account';
        }
    }
}

// Login Functions
async function loginUser(username, password) {
    try {
        setLoading('login-btn', true);
        
        const response = await ApiClient.post('/auth/api/login', {
            username: username,
            password: password
        });
        
        // Store token and user data
        TokenManager.setToken(response.access_token);
        TokenManager.setUser(response.user);
        
        showAlert('Login successful! Redirecting...', 'success');
        
        // Redirect to dashboard after short delay
        setTimeout(() => {
            window.location.href = '/dashboard';
        }, 1500);
        
    } catch (error) {
        showAlert(error.message || 'Login failed', 'danger');
    } finally {
        setLoading('login-btn', false);
    }
}

function initializeLoginForm() {
    const form = document.getElementById('login-form');
    if (!form) return;
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;
        
        if (!username || !password) {
            showAlert('Please fill in all fields', 'warning');
            return;
        }
        
        await loginUser(username, password);
    });
    
    // Check if already logged in
    if (TokenManager.isAuthenticated()) {
        showAlert('You are already logged in. Redirecting...', 'info');
        setTimeout(() => {
            window.location.href = '/dashboard';
        }, 2000);
    }
}

// Registration Functions
async function registerUser(userData) {
    try {
        setLoading('register-btn', true);
        
        const response = await ApiClient.post('/auth/api/register', userData);
        
        showAlert('Registration successful! Please login with your credentials.', 'success');
        
        // Redirect to login after short delay
        setTimeout(() => {
            window.location.href = '/auth/login';
        }, 2000);
        
    } catch (error) {
        showAlert(error.message || 'Registration failed', 'danger');
    } finally {
        setLoading('register-btn', false);
    }
}

function initializeRegistrationForm() {
    // Check if already logged in
    if (TokenManager.isAuthenticated()) {
        showAlert('You are already logged in. Redirecting...', 'info');
        setTimeout(() => {
            window.location.href = '/dashboard';
        }, 2000);
    }
}

// Profile Functions
async function getCurrentUser() {
    try {
        return await ApiClient.get('/auth/api/me');
    } catch (error) {
        console.error('Failed to get current user:', error);
        return null;
    }
}

async function updateProfile(userData) {
    try {
        const response = await ApiClient.put('/auth/api/me', userData);
        TokenManager.setUser(response);
        showAlert('Profile updated successfully!', 'success');
        return response;
    } catch (error) {
        showAlert(error.message || 'Failed to update profile', 'danger');
        throw error;
    }
}

async function changePassword(oldPassword, newPassword) {
    try {
        await ApiClient.post('/auth/api/change-password', {
            old_password: oldPassword,
            new_password: newPassword
        });
        showAlert('Password changed successfully!', 'success');
    } catch (error) {
        showAlert(error.message || 'Failed to change password', 'danger');
        throw error;
    }
}

// Logout Function
function logout() {
    TokenManager.removeToken();
    showAlert('Logged out successfully', 'info');
    setTimeout(() => {
        window.location.href = '/auth/login';
    }, 1000);
}

// Navigation Helper
function updateNavigation() {
    const user = TokenManager.getUser();
    const isAuthenticated = TokenManager.isAuthenticated();
    
    // Update navigation based on auth status
    const authLinks = document.querySelectorAll('.auth-required');
    const guestLinks = document.querySelectorAll('.guest-only');
    const userInfo = document.querySelectorAll('.user-info');
    
    authLinks.forEach(link => {
        link.style.display = isAuthenticated ? 'block' : 'none';
    });
    
    guestLinks.forEach(link => {
        link.style.display = isAuthenticated ? 'none' : 'block';
    });
    
    if (user && userInfo.length > 0) {
        userInfo.forEach(element => {
            element.textContent = user.username || user.full_name || 'User';
        });
    }
}

// Protected Route Helper
function requireAuth() {
    if (!TokenManager.isAuthenticated()) {
        showAlert('Please login to access this page', 'warning');
        setTimeout(() => {
            window.location.href = '/auth/login';
        }, 2000);
        return false;
    }
    return true;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    updateNavigation();
    
    // Add logout handlers
    document.querySelectorAll('.logout-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            logout();
        });
    });
});

// Export for global use
window.Auth = {
    TokenManager,
    ApiClient,
    loginUser,
    registerUser,
    getCurrentUser,
    updateProfile,
    changePassword,
    logout,
    requireAuth,
    showAlert,
    setLoading
};