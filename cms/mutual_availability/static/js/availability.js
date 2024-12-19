
document.addEventListener("DOMContentLoaded", function () {
    // Handle the form submission for filtering
    const filterForm = document.getElementById("filter-project-form");

    filterForm.addEventListener("submit", function (event) {
        event.preventDefault(); // Prevent default form submission

        const projectSelect = document.getElementById("project");
        const selectedProject = projectSelect.value;

        // Prepare the query string
        const queryParams = new URLSearchParams({ project: selectedProject });

        // Make the AJAX request
        fetch(`/mutual_availability/view_schedule?${queryParams}`, {
            headers: {
                "X-Requested-With": "XMLHttpRequest", // Indicates an AJAX request
            },
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error("Network response was not ok");
                }
                return response.json();
            })
            .then((data) => {
                // Update the list group with the new HTML
                const listGroupContainer = document.querySelector(".list-group");
                if (listGroupContainer && data.schedule_html) {
                    listGroupContainer.innerHTML = data.schedule_html;
                }
            })
            .catch((error) => {
                console.error("Error during fetch:", error);
            });
    });
});
