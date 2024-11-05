document.addEventListener('DOMContentLoaded', () => {
    // Smooth scroll to form on page load
    const form = document.getElementById('selectCoordinatorForm');
    if (form) {
        form.scrollIntoView({ behavior: 'smooth' });
    }

    // Add form validation feedback
    const formElement = document.querySelector('#selectCoordinatorForm');
    formElement.addEventListener('submit', function(event) {
        if (!formElement.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
            alert('Please fill out all required fields correctly.');
        }
        formElement.classList.add('was-validated');
    }, false);
});