document.addEventListener('DOMContentLoaded', function() {
    
    // Function to generate a random hex color
    function generateRandomColor() {
        var letters = '0123456789ABCDEF';
        var color = '#';
        for (var i = 0; i < 6; i++) {
            color += letters[Math.floor(Math.random() * 16)];
        }
        return color;
    }

    // Attach the click event to the Random Color button
    $('#random-color-btn').on('click', function () {
        var randomColor = generateRandomColor();
        $('#schedule-color').val(randomColor); // Set the random color to the color picker
    });
    
    const startInput = document.getElementById("schedule-start");
    const endInput = document.getElementById("schedule-end");

    function formatDate(date) {
        const options = { year: 'numeric', month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' };
        return new Date(date).toLocaleString('en-GB', options); // Adjust locale if needed
    }

    // Display the formatted date when the user selects a time
    startInput.addEventListener("change", function() {
        const formattedDate = formatDate(startInput.value);
        startInput.setAttribute("data-formatted", formattedDate); // Store formatted date
    });

    endInput.addEventListener("change", function() {
        const formattedDate = formatDate(endInput.value);
        endInput.setAttribute("data-formatted", formattedDate); // Store formatted date
    });
    // document.addEventListener('click', function(event) {
    //     const dropdowns = document.querySelectorAll('.profile_dd'); // Select all dropdowns
    //     dropdowns.forEach(dropdown => {
    //         // Check if the click was outside the dropdown and its toggle
    //         if (!dropdown.contains(event.target) && !dropdown.previousElementSibling.contains(event.target)) {
    //             dropdown.classList.remove('active'); // Hide the dropdown
    //         }
    //     });
    // });

    //    const dropdownToggles = document.querySelectorAll('.top_navbar .dropdown-toggle');
    //    dropdownToggles.forEach(toggle => {
    //        toggle.addEventListener('click', function(event) {
    //            event.stopPropagation(); // Prevent the click from bubbling up to the document
    //            const dropdown = this.nextElementSibling; // Get the associated dropdown
    //            dropdown.classList.toggle('active'); // Toggle the dropdown visibility
    //        });
    //    });
   

    const alerts = document.querySelectorAll('.alert'); // Select all alerts

    alerts.forEach(function(alert) {
            // If it's NOT a custom success or error alert
            if (!alert.classList.contains('custom-success-alert') && !alert.classList.contains('custom-error-alert') && !alert.classList.contains('custom-info-alert')) {
                // Set a timeout to remove the alert after 5 seconds or any desired time
                setTimeout(function() {
                    alert.style.transition = "opacity 0.5s ease-out"; // Optional: Fade out effect
                    alert.style.opacity = "0"; // Make alert fade out

                    // After fade out, remove the alert from the DOM
                    setTimeout(function() {
                        alert.remove();
                    }, 500); // Wait for fade-out transition to complete
                }, 5000); // 5 seconds timeout for non-custom alerts
            }
    });

    // Smooth scroll to form on page load
    const form = document.getElementById('selectCoordinatorForm');
    if (form) {
        form.scrollIntoView({ behavior: 'smooth' });
    }

    // Add form validation feedback
    const formElement = document.querySelector('#selectCoordinatorForm');
    if (formElement) {
        formElement.addEventListener('submit', function(event) {
            if (!formElement.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                alert('Please fill out all required fields correctly.');
            }
            formElement.classList.add('was-validated');
        }, false);
    }

    // Smooth scroll to sections
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
                });
            });
        });
    });

    document.addEventListener('DOMContentLoaded', function() {
    const searchButton = document.getElementById('searchButton');
    if (searchButton) {
        searchButton.addEventListener('mouseover', function() {
            searchButton.title = "Click to search projects";
            });
        }
    });

    document.addEventListener('DOMContentLoaded', () => {
        // Highlight notification on hover
        const notificationItems = document.querySelectorAll('.notification-item');
        notificationItems.forEach(item => {
            item.addEventListener('mouseover', () => {
                item.style.backgroundColor = '#e9ecef';
            });
            item.addEventListener('mouseout', () => {
                item.style.backgroundColor = '';
            });
        });

    const projectIdeas = document.querySelectorAll('.list-group-item');
    projectIdeas.forEach(item => {
        item.addEventListener('mouseover', () => {
            item.style.backgroundColor = '#e9ecef'; // Change background color on hover
            item.style.transform = 'scale(1.02)'; // Slightly enlarge the item
            item.style.transition = 'transform 0.2s'; // Smooth transition
        });
        item.addEventListener('mouseout', () => {
            item.style.backgroundColor = ''; // Reset background color
            item.style.transform = 'scale(1)'; // Reset size
        });
    });

    // document.querySelectorAll('.sidebar ul li a').forEach(link => {
    //     link.addEventListener('mouseenter', function() {
    //         if (document.querySelector('.wrapper').classList.contains('active')) {
    //             const tooltip = document.createElement('div');
    //             tooltip.className = 'tooltip';
    //             tooltip.innerText = this.getAttribute('data-title');
    //             document.body.appendChild(tooltip);
    //             const rect = this.getBoundingClientRect();
    //             tooltip.style.left = `${rect.right}px`;
    //             tooltip.style.top = `${rect.top + window.scrollY}px`;
    //         }
    //     });
    
    //     link.addEventListener('mouseleave', function() {
    //         const tooltip = document.querySelector('.tooltip');
    //         if (tooltip) {
    //             tooltip.remove();
    //         }
    //     });
    // });
    
});


// function dismissNotification(button) {
//     // Find the parent list item and remove it
//     var notificationItem = button.closest('.notification-item');
//     notificationItem.remove();
// }