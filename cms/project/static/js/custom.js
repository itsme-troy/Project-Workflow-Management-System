document.addEventListener('DOMContentLoaded', () => {
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
    

});

// function dismissNotification(button) {
//     // Find the parent list item and remove it
//     var notificationItem = button.closest('.notification-item');
//     notificationItem.remove();
// }