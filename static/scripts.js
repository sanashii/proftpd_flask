$(document).ready(function() {
    // Handle 'Manage Users' click event
    $('#users-link').click(function(e) {
        e.preventDefault();
        // Make an AJAX request to get the user table
        $.ajax({
            url: '/users', // This should map to your Flask route
            type: 'GET',
            success: function(data) {
                // Update content area with user table
                $('#content-area').html(data);
            },
            error: function() {
                alert("Error loading users.");
            }
        });
    });

    // Handle 'Home' click event
    $('#home-link').click(function(e) {
        e.preventDefault();
        // Reload initial home content
        $('#content-area').html('<h1>Welcome to MyApp</h1><p>Use the navigation to manage users or go back to home.</p>');
    });
});

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

// for manage user component
document.addEventListener("DOMContentLoaded", () => {
    const rows = document.querySelectorAll("tr.user-row");
    rows.forEach((row) => {
      const userId = row.dataset.userId;
      row.addEventListener("click", () => goToManageUser(userId));
    });
});

function goToManageUser(id) {
    console.log(`Navigating to user ID: ${id}`);
    window.location.href = `/manage-user/${id}`;
}

function loadManageUser(userId) {
    // Perform an AJAX call to fetch the manage_user component for a specific user
    $.get(`/user/${userId}`, function(data) {
        $('#content').html(data);
    });
}
