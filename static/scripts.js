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

    // Handle delete button click
    $('#deleteUserBtn').click(function() {
        var deleteUserModal = new bootstrap.Modal(document.getElementById('deleteUserModal'));
        deleteUserModal.show();
    });

    // Handle delete confirmation
    $('#confirmDeleteUser').click(function() {
        const userId = $('input[name="user_id"]').val();
        $.ajax({
            url: `/delete_user/${userId}`,
            type: 'POST',
            success: function(response) {
                deleteUserModal.hide();
                if (response.success) {
                    document.body.dataset.showModal = 'success';
                    window.location.href = '/home';
                } else {
                    document.body.dataset.showModal = 'error';
                }
            },
            error: function(xhr, status, error) {
                deleteUserModal.hide();
                document.body.dataset.showModal = 'error';
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
    
    // Preserve existing parameters
    const existingParams = new URLSearchParams(window.location.search);
    for (const [key, val] of existingParams) {
        if (key !== param) {
            url.searchParams.set(key, val);
        }
    }
    
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
});

$(document).ready(function() {
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