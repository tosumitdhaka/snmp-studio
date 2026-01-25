window.SettingsModule = {
    init: function() {
        // We can't pre-fill the password, but we can pre-fill the username if we stored it
        // document.getElementById("set-auth-user").value = "admin"; 
    },

    updateAuth: async function(e) {
        e.preventDefault();
        
        const currentPass = document.getElementById("set-auth-current-pass").value;
        const user = document.getElementById("set-auth-user").value;
        const pass = document.getElementById("set-auth-pass").value;
        const confirmPass = document.getElementById("set-auth-pass-confirm").value;
        const msgBox = document.getElementById("auth-msg");
        
        // Validation
        if (pass !== confirmPass) {
            msgBox.textContent = "New passwords do not match!";
            msgBox.classList.remove("d-none");
            return;
        }
        
        msgBox.classList.add("d-none");

        try {
            const res = await fetch('/api/settings/auth', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                // UPDATE: Send current_password
                body: JSON.stringify({ 
                    current_password: currentPass,
                    username: user, 
                    password: pass 
                })
            });

            const data = await res.json();

            if (res.ok) {
                alert("Credentials updated! You must log in again.");
                logout(); // Force logout
            } else {
                msgBox.textContent = data.detail || "Error updating credentials.";
                msgBox.classList.remove("d-none");
            }
        } catch (e) {
            console.error(e);
            msgBox.textContent = "Connection error.";
            msgBox.classList.remove("d-none");
        }
    }
};