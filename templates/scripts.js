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