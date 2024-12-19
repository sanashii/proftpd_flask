let deleteUserModal;

const pageCache = {
    data: new Map(),
    maxSize: 20, // Maximum number of pages to cache
    
    set: function(key, value) {
        if (this.data.size >= this.maxSize) {
            // Remove oldest entry
            const firstKey = this.data.keys().next().value;
            this.data.delete(firstKey);
        }
        this.data.set(key, {
            content: value,
            timestamp: Date.now()
        });
    },
    
    get: function(key) {
        const entry = this.data.get(key);
        if (entry) {
            entry.timestamp = Date.now(); // Update last accessed time
            return entry.content;
        }
        return null;
    },

    clear: function() {
        this.data.clear();
    }
};

$(document).ready(function() {
    fetchUserStatusCounts();
    initBulkOperations();

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

    // for toggling the dropdown menu in user_table
    const dropdowns = document.querySelectorAll('.dropdown-toggle');
    dropdowns.forEach(dropdown => {
        new bootstrap.Dropdown(dropdown);
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

    // Handle 'Create Profile' click event
    $('#create-profile-link').click(function(e) {
        e.preventDefault();
        loadCreateProfile();
    });

    // Handle 'Home' click event
    $('#home-link').click(function(e) {
        e.preventDefault();
        loadHome();
    });

    // Handle user row click event
    $(document).on('click', 'tr.user-row', function() {
        const userName = $(this).data('username');
        loadManageUser(userName);
    });

    // Handle sort dropdown clicks
    $(document).on('click', '.dropdown-item', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const param = $(this).closest('.dropdown').data('param-type');
        const value = $(this).data('value');
        
        if (param && value) {
            updateURLParams(param, value);
        }
    });

    // Handle nested dropdowns
    $('.dropdown-submenu > a.dropdown-toggle').on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        // Close all other submenus
        $('.dropdown-submenu .dropdown-menu').not($(this).next()).hide();
        
        // Toggle this submenu
        $(this).next('.dropdown-menu').toggle();
        
        // Add/remove show class
        $(this).toggleClass('show');
    });

    // Handle group selection
    $('.dropdown-submenu .dropdown-item').on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const value = $(this).data('value');
        if (value) {
            updateURLParams('filter_by', value);
            
            // Hide all submenus
            $('.dropdown-submenu .dropdown-menu').hide();
            $('.dropdown-toggle').removeClass('show');
        }
    });

    // Close submenus when clicking outside
    $(document).on('click', function(e) {
        if (!$(e.target).closest('.dropdown-submenu').length) {
            $('.dropdown-submenu .dropdown-menu').hide();
            $('.dropdown-toggle').removeClass('show');
        }
    });
    
    const userName = urlParams.get('username');
    if (userName) {
        loadManageUser(userName);
    }

    // Initialize delete user modal
    const deleteUserModalElement = document.getElementById('deleteUserModal');
    let deleteUserModal;
    if (deleteUserModalElement) {
        deleteUserModal = new bootstrap.Modal(deleteUserModalElement);
    }

    // Handle delete button click
    $(document).on('click', '#deleteUserBtn', function(e) {
        e.preventDefault();
        if (deleteUserModal) {
            deleteUserModal.show();
        }
    });

    // Handle delete confirmation
    $(document).on('click', '#confirmDeleteUser', function(e) {
        e.preventDefault();
        const username = $('input[name="username"]').val();

        $.ajax({
            url: `/delete_user/${encodeURIComponent(username)}`,
            type: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            success: function(response) {
                if (deleteUserModal) {
                    deleteUserModal.hide();
                }
                if (response.success) {
                    window.location.href = '/home';
                } else {
                    alert(response.message || 'Error deleting user');
                }
            },
            error: function(xhr, status, error) {
                if (deleteUserModal) {
                    deleteUserModal.hide();
                }
                alert('Error deleting user: ' + (error || xhr.statusText));
                console.error('Error deleting user:', error);
            }
        });
    });

    $('.edit-profile').click(function() {
        const username = $(this).data('username');
        const row = $(`#row-${username}`);
        
        // Enable inputs
        row.find('input, select').prop('disabled', false);
        
        // Show/hide buttons
        $(this).addClass('d-none');
        row.find('.save-profile, .cancel-edit').removeClass('d-none');
    });

    $('.save-profile').click(function() {
        const username = $(this).data('username');
        const row = $(`#row-${username}`);
        
        const data = {
            is_enabled: row.find('.status-toggle').prop('checked'),
            user_type: row.find('.user-type').val(),
            can_view: row.find('.can-view').prop('checked'),
            can_create: row.find('.can-create').prop('checked'),
            can_modify: row.find('.can-modify').prop('checked')
        };

        $.ajax({
            url: `/update_profile/${username}`,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(data),
            success: function(response) {
                if (response.success) {
                    // Disable inputs
                    row.find('input, select').prop('disabled', true);
                    
                    // Show/hide buttons
                    row.find('.edit-profile').removeClass('d-none');
                    row.find('.save-profile, .cancel-edit').addClass('d-none');
                }
            }
        });
    });

    $('.cancel-edit').click(function() {
        const username = $(this).data('username');
        const row = $(`#row-${username}`);
        
        // Disable inputs and reset to original values
        row.find('input, select').prop('disabled', true);
        
        // Show/hide buttons
        row.find('.edit-profile').removeClass('d-none');
        row.find('.save-profile, .cancel-edit').addClass('d-none');
        
        // Reload page to reset values
        location.reload();
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

function loadManageUser(userName) {
    // Update the URL without reloading the full page
    history.pushState(null, '', `/manage_user/${userName}`);

    // Fetch and load only the manage_user content (no navigation bar)
    fetch(`/manage_user/${userName}`)
        .then(response => response.text())
        .then(data => {
            document.getElementById('content').innerHTML = data;
        })
        .catch(error => {
            console.error('Error loading user details:', error);
        });
}

function loadCreateProfile() {
    // Update the URL without reloading the full page
    history.pushState(null, '', `/create_profile`);

    fetch('/create_profile')
        .then(response => response.text())
        .then(data => {
            document.getElementById('content').innerHTML = data;
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
    if ($('.table-responsive').hasClass('loading')) return;
    
    const url = new URL(window.location);
    url.searchParams.set(param, value);
    
    // Generate cache key
    const cacheKey = JSON.stringify({
        page: url.searchParams.get('page'),
        sort_by: url.searchParams.get('sort_by'),
        filter_by: url.searchParams.get('filter_by'),
        search: url.searchParams.get('search')
    });

    // Check cache first
    const cachedContent = pageCache.get(cacheKey);
    if (cachedContent) {
        $('.table-responsive').html(cachedContent);
        restoreCheckboxStates();
        updateBulkActionBar();
        history.pushState(null, '', `?${url.searchParams.toString()}`);
        return;
    }
    
    $('.table-responsive').addClass('loading');
    
    $.ajax({
        url: '/home',
        data: url.searchParams.toString(),
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Cache-Control': 'no-cache'
        },
        success: function(response) {
            const temp = document.createElement('div');
            temp.innerHTML = response;
            
            // Get components in correct order
            const navbarContent = temp.querySelector('#userTableNavBar');
            const bulkActionsBar = temp.querySelector('#bulkActionsBar');  // Add this
            const tableContent = temp.querySelector('table');
            const paginationContent = temp.querySelector('#userTablePagination');
            
            // Construct content maintaining order
            const finalContent = document.createElement('div');
            if (navbarContent) finalContent.appendChild(navbarContent.cloneNode(true));
            if (bulkActionsBar) finalContent.appendChild(bulkActionsBar.cloneNode(true));  // Add this
            if (tableContent) finalContent.appendChild(tableContent.cloneNode(true));
            if (paginationContent) finalContent.appendChild(paginationContent.cloneNode(true));
            
            // Cache the content
            pageCache.set(cacheKey, finalContent.innerHTML);
            
            // Update DOM
            $('.table-responsive').html(finalContent.innerHTML);
            
            // Restore selections and update toolbar
            restoreCheckboxStates();
            updateBulkActionBar();

            // Reinitialize dropdowns
            const dropdowns = document.querySelectorAll('.dropdown-toggle');
            dropdowns.forEach(dropdown => {
                new bootstrap.Dropdown(dropdown);
            });
            
            // Reinitialize bulk operations event handlers
            initBulkOperations();  // Add this
            
            history.pushState(null, '', `?${url.searchParams.toString()}`);
            updateDropdownText(param, value);
            $('.table-responsive').removeClass('loading');
            
            $(temp).remove();
        },
        error: function(error) {
            console.error('Error updating content:', error);
            $('.table-responsive').removeClass('loading');
        }
    });
}

function updateDropdownText(param, value) {
    if (param === 'sort_by') {
        $('#sortDropdown').text(`Sort by: ${value.charAt(0).toUpperCase() + value.slice(1)}`);
    } else if (param === 'filter_by') {
        $('#filterDropdown').text(`Filter by: ${value.charAt(0).toUpperCase() + value.slice(1)}`);
    }
}

// Add selectedUsers Set to store selections across pages
const selectedUsers = new Set();

function initBulkOperations() {
    // Initialize bulk operations on page load
    updateBulkActionBar();
    restoreCheckboxStates();

    // Select all functionality
    $('#selectAll').on('change', function() {
        const isChecked = $(this).prop('checked');
        $('.user-select').each(function() {
            const username = $(this).val();
            $(this).prop('checked', isChecked);
            if (isChecked) {
                selectedUsers.add(username);
            } else {
                selectedUsers.delete(username);
            }
        });
        updateBulkActionBar();
    });

    // Individual select
    $(document).on('change', '.user-select', function(e) {
        e.stopPropagation(); // Prevent row click
        const username = $(this).val();
        if ($(this).prop('checked')) {
            selectedUsers.add(username);
        } else {
            selectedUsers.delete(username);
        }
        updateBulkActionBar();
    });

    // Prevent row click when clicking checkbox
    $(document).on('click', '.user-select', function(e) {
        e.stopPropagation();
    });

    // Bulk actions
    $(document).on('click', '.bulk-action', function() {
        const action = $(this).data('action');
        if (selectedUsers.size === 0) return;

        // Add loading state
        $('.table-responsive').addClass('loading');

        $.ajax({
            url: `/bulk_${action}`,
            method: 'POST',
            data: JSON.stringify({ users: Array.from(selectedUsers) }),
            contentType: 'application/json',
            success: function(response) {
                if (response.success) {
                    selectedUsers.clear();
                    // Don't remove loading state before reload
                    window.location.reload();
                }
            },
            error: function() {
                // Only remove loading on error
                $('.table-responsive').removeClass('loading');
            }
        });
    });

    // Handle bulk group assignment
    $(document).on('click', '.bulk-group', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        if (selectedUsers.size === 0) return;
        
        const groupId = $(this).data('gid');
        
        $('.table-responsive').addClass('loading');

        $.ajax({
            url: '/bulk_assign_group',
            method: 'POST',
            data: JSON.stringify({
                users: Array.from(selectedUsers),
                group_id: groupId
            }),
            contentType: 'application/json',
            success: function(response) {
                if (response.success) {
                    selectedUsers.clear();
                    // Don't remove loading state before reload
                    window.location.reload();
                } else {
                    $('.table-responsive').removeClass('loading');
                    alert(response.message || 'Error assigning group');
                }
            },
            error: function(xhr, status, error) {
                $('.table-responsive').removeClass('loading');
                alert('Error assigning group: ' + error);
            }
        });
    });

    // Update export with loading state
    $('#exportUsers').on('click', function() {
        if (selectedUsers.size === 0) return;
        $('.table-responsive').addClass('loading');
        window.location.href = `/export_users?users=${Array.from(selectedUsers).join(',')}`;
        setTimeout(() => {
            $('.table-responsive').removeClass('loading');
        }, 1000);
    });

    // Update import with loading state
    $('#importUsers').on('click', function() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.csv';
        input.onchange = e => {
            const file = e.target.files[0];
            const formData = new FormData();
            formData.append('file', file);
            
            $('.table-responsive').addClass('loading');
            
            $.ajax({
                url: '/import_users',
                method: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                success: function(response) {
                    if (response.success) {
                        // Don't remove loading state before reload
                        window.location.reload();
                    } else {
                        // Only remove loading on error
                        $('.table-responsive').removeClass('loading');
                        alert(response.message || 'Error importing users');
                    }
                },
                error: function(xhr, status, error) {
                    // Only remove loading on error
                    $('.table-responsive').removeClass('loading');
                    alert('Error importing users: ' + error);
                }
            });
        };
        input.click();
    });
}

function updateBulkActionBar() {
    const selectedCount = selectedUsers.size;
    $('#selectedCount').text(selectedCount);
    $('#bulkActionsBar').toggleClass('d-none', !selectedCount);

    // Update selectAll checkbox state
    const allSelected = $('.user-select').length > 0 && 
                       $('.user-select:not(:checked)').length === 0;
    $('#selectAll').prop('checked', allSelected);
}

function restoreCheckboxStates() {
    $('.user-select').each(function() {
        const username = $(this).val();
        $(this).prop('checked', selectedUsers.has(username));
    });
}

$('.dropdown-item').on('click', function(e) {
    const href = $(this).attr('href');
    if (href && href !== '#') {
        window.location.href = href;
    }
});

// Clear cache when filters change
$('#sortDropdown, #filterDropdown').on('click', 'a', function() {
    pageCache.clear();
});

$('input[name="search"]').on('input', function() {
    pageCache.clear();
});

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

// for pagination back and forward
window.addEventListener('popstate', function() {
    loadContent(window.location.pathname + window.location.search);
});

// for admin dropdown tab in index.html
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all dropdowns
    var dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'))
    var dropdownList = dropdownElementList.map(function (dropdownToggleEl) {
        return new bootstrap.Dropdown(dropdownToggleEl)
    });

    // click handler for dropdown items
    document.querySelectorAll('.dropdown-item').forEach(item => {
        item.addEventListener('click', function(e) {
            if (this.getAttribute('href')) {
                window.location.href = this.getAttribute('href');
            }
        });
    });
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