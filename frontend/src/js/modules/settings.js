window.SettingsModule = {
    init: function() {
        // Add password strength indicator
        const passInput = document.getElementById("set-auth-pass");
        if (passInput) {
            passInput.addEventListener('input', (e) => this.checkPasswordStrength(e.target.value));
        }
    },

    checkPasswordStrength: function(password) {
        const strengthEl = document.getElementById('password-strength');
        if (!strengthEl) return;
        
        let strength = 0;
        if (password.length >= 8) strength++;
        if (password.match(/[a-z]/) && password.match(/[A-Z]/)) strength++;
        if (password.match(/[0-9]/)) strength++;
        if (password.match(/[^a-zA-Z0-9]/)) strength++;
        
        const labels = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong'];
        const colors = ['danger', 'danger', 'warning', 'info', 'success'];
        
        strengthEl.textContent = labels[strength];
        strengthEl.className = `badge bg-${colors[strength]} ms-2`;
        
        if (password.length > 0) {
            strengthEl.classList.remove('d-none');
        } else {
            strengthEl.classList.add('d-none');
        }
    },

    updateAuth: async function(e) {
        e.preventDefault();
        
        const currentPass = document.getElementById("set-auth-current-pass").value;
        const user = document.getElementById("set-auth-user").value;
        const pass = document.getElementById("set-auth-pass").value;
        const confirmPass = document.getElementById("set-auth-pass-confirm").value;
        const msgBox = document.getElementById("auth-msg");
        
        // Clear previous messages
        msgBox.classList.add("d-none");
        
        // Validation
        if (pass !== confirmPass) {
            msgBox.textContent = "New passwords do not match!";
            msgBox.className = "alert alert-danger small py-2 mb-3";
            return;
        }
        
        if (pass.length < 6) {
            msgBox.textContent = "Password must be at least 6 characters!";
            msgBox.className = "alert alert-danger small py-2 mb-3";
            return;
        }

        // Confirmation modal
        if (!confirm(`Update credentials for user "${user}"?\n\nYou will be logged out and need to log in again.`)) {
            return;
        }

        const btn = e.target.querySelector('button[type="submit"]');
        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Updating...';

        try {
            const res = await fetch('/api/settings/auth', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    current_password: currentPass,
                    username: user, 
                    password: pass 
                })
            });

            const data = await res.json();

            if (res.ok) {
                msgBox.textContent = "✓ Credentials updated successfully. Logging out...";
                msgBox.className = "alert alert-success small py-2 mb-3";
                
                setTimeout(() => logout(), 2000);
            } else {
                msgBox.textContent = data.detail || "Error updating credentials.";
                msgBox.className = "alert alert-danger small py-2 mb-3";
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        } catch (e) {
            console.error(e);
            msgBox.textContent = "Connection error. Please try again.";
            msgBox.className = "alert alert-danger small py-2 mb-3";
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    }
};