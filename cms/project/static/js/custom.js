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