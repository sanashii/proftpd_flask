let deleteUserModal;

$(document).ready(function() {
    // for toggling the dropdown menu in user_table
    var dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'));
    dropdownElementList.map(function (dropdownToggleEl) {
        return new bootstrap.Dropdown(dropdownToggleEl);
    });
    
    // Handle 'Manage Users' click event
    $('#manage-users-link').click(function(e) {
        e.preventDefault();
        loadManageUser();
    });

    // Handle 'Create Users' click event
    $('#create-users-link').click(function(e) {
        e.preventDefault();
        loadCreateUser();
    });

    // Handle 'Home' click event
    $('#home-link').click(function(e) {
        e.preventDefault();
        loadHome();
    });

    // Handle user row click event
    $(document).on('click', 'tr.user-row', function() {
        const userId = $(this).data('user-id');
        loadManageUser(userId);
    });

    // Check if there's a user_id in the URL and load the manage user content
    const urlParams = new URLSearchParams(window.location.search);
    const userId = urlParams.get('user_id');
    if (userId) {
        loadManageUser(userId);
    }

    deleteUserModal = new bootstrap.Modal(document.getElementById('deleteUserModal'));

    // Handle delete button click
    $('#deleteUserBtn').click(function() {
        deleteUserModal.show();
    });

    // Handle delete confirmation
    $('#confirmDeleteUser').click(function() {
        const userId = document.querySelector('input[name="user_id"]').value;
        
        $.ajax({
            url: `/delete_user/${userId}`,
            type: 'POST',
            success: function(response) {
                deleteUserModal.hide();
                if (response.success) {
                    window.location.href = '/home';
                } else {
                    alert('Error deleting user');
                }
            },
            error: function() {
                deleteUserModal.hide();
                alert('Error deleting user');
            }
        });
    });
});

function loadHome() {
    fetch('/home')
        .then(response => response.text())
        .then(data => {
            document.getElementById('content').innerHTML = data;
        });
}

function loadCreateUser() {
    // Update the URL without reloading the full page
    history.pushState(null, '', `/create_user`);

    fetch('/create_user')
        .then(response => response.text())
        .then(data => {
            document.getElementById('content').innerHTML = data;
        });
}

function loadManageUser(userId) {
    // Update the URL without reloading the full page
    history.pushState(null, '', `/manage_user/${userId}`);

    // Fetch and load only the manage_user content (no navigation bar)
    fetch(`/manage_user/${userId}`)
        .then(response => response.text())
        .then(data => {
            document.getElementById('content').innerHTML = data;
        })
        .catch(error => {
            console.error('Error loading user details:', error);
        });
}

function logout() {
    window.location.href = "/";
}

function loadContent(url) {
    fetch(url)
        .then(response => response.text())
        .then(data => {
            document.getElementById('content').innerHTML = data;
    });
}

function back() {
    window.location.href = "/";
}

function validateForm() {
    var password = document.getElementById("password").value;
    var confirmPassword = document.getElementById("confirm-password").value;
    if (password != confirmPassword) {
        alert("Passwords do not match.");
        return false;
    }
    return true;
}

function updateURLParams(param, value) {
    const url = new URL(window.location);
    url.searchParams.set(param, value);
    
    const existingParams = new URLSearchParams(window.location.search);
    for (const [key, val] of existingParams) {
        if (key !== param) {
            url.searchParams.set(key, val);
        }
    }
    
    // $.ajax({
    //     url: '/home',
    //     data: url.searchParams.toString(),
    //     method: 'GET',
    //     success: function(response) {
    //         $('#content').html(response);
    //         // Update URL without reload
    //         history.pushState(null, '', `?${url.searchParams.toString()}`);
    //     },
    //     error: function(error) {
    //         console.error('Error updating content:', error);
    //     }
    // });

    window.location.href = url.toString();
}

// for card component
function fetchUserStatusCounts() {
    $.ajax({
        url: '/api/user_status_counts',
        method: 'GET',
        success: function(data) {
            $('#active-users').text(data.active_users);
            $('#inactive-users').text(data.inactive_users);
            $('#disabled-users').text(data.disabled_users);
        },
        error: function(error) {
            console.log("Error fetching user status counts", error);
        }
    });
}

$(document).ready(function() {
    fetchUserStatusCounts();

    const urlParams = new URLSearchParams(window.location.search);
    const userId = urlParams.get('user_id');
    if (userId) {
        $.ajax({
            url: `/user/${userId}`,
            type: 'GET',
            success: function(data) {
                $('#user-id').val(data.id);
                $('#username').val(data.username);
                $('#directory').val(data.directory);
                $('#status').val(data.status);
            },
            error: function() {
                alert("Error loading user details.");
            }
        });
    }
});

// for paginaction back and forward
window.addEventListener('popstate', function() {
    loadContent(window.location.pathname + window.location.search);
});

// for password generator
document.addEventListener('DOMContentLoaded', function() {
    const generateBtn = document.getElementById('generateBtn');
    const popup = document.getElementById('generatorPopup');
    const passwordInput = document.getElementById('password');
    const generatePassword = document.getElementById('generatePassword');
    const strengthBar = document.getElementById('strengthBar');
    const strengthText = document.getElementById('strengthText');
    
    generateBtn.addEventListener('click', () => {
        popup.style.display = popup.style.display === 'none' ? 'block' : 'none';
    });

    generatePassword.addEventListener('click', () => {
        const length = document.getElementById('lengthRange').value;
        const useUpper = document.getElementById('uppercase').checked;
        const useNumbers = document.getElementById('numbers').checked;
        const useSymbols = document.getElementById('symbols').checked;
        
        const password = generateRandomPassword(length, useUpper, useNumbers, useSymbols);
        passwordInput.value = password;
        checkPasswordStrength(password);
    });

    passwordInput.addEventListener('input', function() {
        checkPasswordStrength(this.value);
    });

    function generateRandomPassword(length, useUpper, useNumbers, useSymbols) {
        const lower = 'abcdefghijklmnopqrstuvwxyz';
        const upper = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
        const numbers = '0123456789';
        const symbols = '!@#$%^&*()_+-=[]{}|;:,.<>?';
        
        let chars = lower;
        if (useUpper) chars += upper;
        if (useNumbers) chars += numbers;
        if (useSymbols) chars += symbols;
        
        return Array(Number(length))
            .fill(chars)
            .map(x => x[Math.floor(Math.random() * x.length)])
            .join('');
    }

    function checkPasswordStrength(password) {
        let strength = 0;
        
        if (password.length >= 8) strength += 20;
        if (password.match(/[A-Z]/)) strength += 20;
        if (password.match(/[a-z]/)) strength += 20;
        if (password.match(/[0-9]/)) strength += 20;
        if (password.match(/[^A-Za-z0-9]/)) strength += 20;

        strengthBar.style.width = strength + '%';
        strengthBar.style.backgroundColor = getStrengthColor(strength);
        
        let strengthLabel = 'Weak';
        if (strength >= 80) strengthLabel = 'Strong';
        else if (strength >= 60) strengthLabel = 'Good';
        else if (strength >= 40) strengthLabel = 'Medium';
        
        strengthText.textContent = `Password Strength: ${strengthLabel}`;
    }

    function getStrengthColor(strength) {
        if (strength >= 80) return '#4CAF50';
        if (strength >= 60) return '#2196F3';
        if (strength >= 40) return '#FFC107';
        return '#F44336';
    }

    // Update length value display
    document.getElementById('lengthRange').addEventListener('input', function() {
        document.getElementById('lengthValue').textContent = this.value;
    });

    // Copy password functionality
    const copyButton = document.getElementById('copyPassword');
    if (copyButton) {
        copyButton.addEventListener('click', async function() {
            const passwordInput = document.getElementById('password');
            const icon = this.querySelector('i');
            
            try {
                await navigator.clipboard.writeText(passwordInput.value);
                
                // Visual feedback
                icon.classList.replace('fa-copy', 'fa-check');
                
                // Reset icon after 2 seconds
                setTimeout(() => {
                    icon.classList.replace('fa-check', 'fa-copy');
                }, 2000);
                
            } catch (err) {
                console.error('Failed to copy:', err);
                // Error feedback
                icon.classList.replace('fa-copy', 'fa-times');
                setTimeout(() => {
                    icon.classList.replace('fa-times', 'fa-copy');
                }, 2000);
            }
        });
    }
});

// for copying generated password
document.getElementById('copyPassword').addEventListener('click', function() {
    const passwordInput = document.getElementById('password');
    
    // Copy password to clipboard
    navigator.clipboard.writeText(passwordInput.value).then(function() {
        // Visual feedback
        const icon = this.querySelector('i');
        icon.classList.remove('fa-copy');
        icon.classList.add('fa-check');
        
        // Reset icon after 2 seconds
        setTimeout(() => {
            icon.classList.remove('fa-check');
            icon.classList.add('fa-copy');
        }, 2000);
    }.bind(this)).catch(function(err) {
        console.error('Failed to copy: ', err);
    });
});