$(document).ready(function() {
    // Handle 'Manage Users' click event
    $('#manage-users-link').click(function(e) {
        e.preventDefault();
        loadManageUsers();
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
});

function loadHome() {
    fetch('/home')
        .then(response => response.text())
        .then(data => {
            document.getElementById('content').innerHTML = data;
        });
}

function loadManageUsers() {
    fetch('/manage_user')
        .then(response => response.text())
        .then(data => {
            document.getElementById('content').innerHTML = data;
        });
}

function loadManageUser(userId) {
    // Change the URL to /manage_user/<user_id>
    history.pushState(null, '', `/manage_user/${userId}`);
    // Perform an AJAX call to fetch the manage_user component for a specific user
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

// // for manage user component
// document.addEventListener("DOMContentLoaded", () => {
//     const rows = document.querySelectorAll("tr.user-row");
//     rows.forEach((row) => {
//       const userId = row.dataset.userId;
//       row.addEventListener("click", () => goToManageUser(userId));
//     });
// });

// function goToManageUser(id) {
//     console.log(`Navigating to user ID: ${id}`);
//     window.location.href = `/manage-user/${id}`;
// }

// function loadManageUser(userId) {
//     // Perform an AJAX call to fetch the manage_user component for a specific user
//     $.get(`/user/${userId}`, function(data) {
//         $('#content').html(data);
//     });
// }
