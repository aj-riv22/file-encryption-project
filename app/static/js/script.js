// Client-side functionality for the file encryption project

document.addEventListener('DOMContentLoaded', function() {
    // Show loading indicator when forms are submitted
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Processing...';
                submitButton.disabled = true;
            }
        });
    });

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-important)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const closeButton = alert.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            }
        }, 5000);
    });

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Function to copy share link to clipboard
function copyShareLink(linkId) {
    const linkElement = document.getElementById(linkId);
    const textArea = document.createElement('textarea');
    textArea.value = linkElement.getAttribute('data-link');
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand('copy');
    document.body.removeChild(textArea);
    
    // Show copied message
    const button = document.querySelector(`[onclick="copyShareLink('${linkId}')"]`);
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-check me-1"></i>Copied!';
    setTimeout(() => {
        button.innerHTML = originalText;
    }, 2000);
}

// File upload preview
function previewFile() {
    const fileInput = document.getElementById('file-upload');
    const filePreview = document.getElementById('file-preview');
    
    if (fileInput && filePreview && fileInput.files.length > 0) {
        const file = fileInput.files[0];
        const fileSize = (file.size / 1024 / 1024).toFixed(2); // in MB
        
        let icon = 'fa-file';
        if (file.type.startsWith('image/')) icon = 'fa-file-image';
        else if (file.type.startsWith('video/')) icon = 'fa-file-video';
        else if (file.type.startsWith('audio/')) icon = 'fa-file-audio';
        else if (file.type.startsWith('text/')) icon = 'fa-file-alt';
        else if (file.type.includes('pdf')) icon = 'fa-file-pdf';
        else if (file.type.includes('word')) icon = 'fa-file-word';
        else if (file.type.includes('excel')) icon = 'fa-file-excel';
        else if (file.type.includes('zip') || file.type.includes('archive')) icon = 'fa-file-archive';
        
        filePreview.innerHTML = `
            <div class="text-center p-3">
                <i class="fas ${icon} fa-3x mb-3 text-primary"></i>
                <h5>${file.name}</h5>
                <p class="mb-0 text-muted">${fileSize} MB</p>
            </div>
        `;
        filePreview.style.display = 'block';
    } else if (filePreview) {
        filePreview.style.display = 'none';
    }
}

// Password strength checker
function checkPasswordStrength(password) {
    let strength = 0;
    
    // Length check
    if (password.length >= 8) strength += 1;
    if (password.length >= 12) strength += 1;
    
    // Character variety checks
    if (/[a-z]/.test(password)) strength += 1;
    if (/[A-Z]/.test(password)) strength += 1;
    if (/[0-9]/.test(password)) strength += 1;
    if (/[^a-zA-Z0-9]/.test(password)) strength += 1;
    
    return {
        score: strength,
        max: 6,
        feedback: getStrengthFeedback(strength)
    };
}

function getStrengthFeedback(strength) {
    switch(strength) {
        case 0:
        case 1:
            return {
                message: "Very weak password",
                suggestions: ["Make it longer", "Add numbers and symbols"]
            };
        case 2:
            return {
                message: "Weak password",
                suggestions: ["Add uppercase letters", "Add symbols"]
            };
        case 3:
        case 4:
            return {
                message: "Moderate password",
                suggestions: ["Add more variety of characters"]
            };
        case 5:
            return {
                message: "Strong password",
                suggestions: []
            };
        case 6:
            return {
                message: "Very strong password",
                suggestions: []
            };
        default:
            return {
                message: "Password strength unknown",
                suggestions: ["Use a longer password with a mix of characters"]
            };
    }
}

// Function to update UI based on file encryption/decryption progress
function updateProgressBar(percentage) {
    const progressBar = document.getElementById('encryption-progress');
    if (progressBar) {
        progressBar.style.width = percentage + '%';
        progressBar.setAttribute('aria-valuenow', percentage);
        
        if (percentage === 100) {
            setTimeout(() => {
                document.getElementById('progress-container').classList.add('d-none');
                document.getElementById('success-message').classList.remove('d-none');
            }, 500);
        }
    }
}

// Initialize file upload listeners
document.addEventListener('DOMContentLoaded', function() {
    const fileUpload = document.getElementById('file-upload');
    if (fileUpload) {
        fileUpload.addEventListener('change', previewFile);
    }
    
    // Initialize password strength meters
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(input => {
        input.addEventListener('input', function() {
            const strengthMeter = document.getElementById('password-strength');
            const feedbackElement = document.getElementById('password-feedback');
            
            if (strengthMeter && feedbackElement) {
                const result = checkPasswordStrength(this.value);
                const percentage = (result.score / result.max) * 100;
                
                strengthMeter.style.width = percentage + '%';
                feedbackElement.textContent = result.feedback.message;
                
                // Update color based on strength
                strengthMeter.className = 'progress-bar';
                if (percentage < 30) {
                    strengthMeter.classList.add('bg-danger');
                } else if (percentage < 70) {
                    strengthMeter.classList.add('bg-warning');
                } else {
                    strengthMeter.classList.add('bg-success');
                }
            }
        });
    });
});