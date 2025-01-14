document.addEventListener('DOMContentLoaded', function () {
    // Fetch notifications when dropdown is clicked
    const notificationsDropdown = document.getElementById('notificationsDropdown');
    const notificationList = document.getElementById('notification-list');
    const notificationCount = document.getElementById('notification-count');
  
    notificationsDropdown.addEventListener('click', function () {
      fetch('/notifications/api/')
        .then(response => response.json())
        .then(data => {
          notificationList.innerHTML = ''; // Clear existing notifications
          if (data.notifications.length === 0) {
            notificationList.innerHTML = '<li class="dropdown-item text-muted">No notifications at the moment.</li>';
          } else {
            data.notifications.forEach(notification => {
              const item = document.createElement('li');
              item.classList.add('dropdown-item');
              item.innerHTML = `
                <strong>${notification.type}:</strong> ${notification.message}
                <div class="text-muted small">${notification.created_at}</div>
              `;
              item.addEventListener('click', function () {
                window.location.href = notification.redirect_url;
              });
              notificationList.appendChild(item);
            });
          }
          // Update notification count
          notificationCount.textContent = data.unread_count;
        })
        .catch(error => console.error('Error loading notifications:', error));
    });
    
  });