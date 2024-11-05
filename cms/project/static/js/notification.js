function fetchNotifications() {
    fetch('/get_notifications/', {
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        },
        credentials: 'include', // Pass cookies with the request
    })
    .then(response => response.json())
    .then(data => {
        console.log("Fetched Data:", data); // Log to verify data
        const notificationsList = document.querySelector('.notifications-list');
        const notificationCount = document.querySelector('.notification-count');
        
        if (data.unread_count > 0) {
            notificationCount.textContent = data.unread_count;
            notificationCount.style.display = 'inline';
        } else {
            notificationCount.style.display = 'none';
        }

        notificationsList.innerHTML = '';
        data.notifications.forEach(notification => {
            const notifItem = document.createElement('div');
            notifItem.className = `dropdown-item ${notification.is_read ? 'read' : 'unread'}`;
            notifItem.innerHTML = `
                <div class="d-flex align-items-center notification-item">
                    <div class="flex-grow-1">
                        <p class="mb-0 ${notification.is_read ? 'text-muted' : 'fw-bold'}">${notification.message}</p>
                        <small class="text-muted">${notification.created_at}</small>
                    </div>
                    ${!notification.is_read ? `
                        <button class="btn btn-sm btn-link mark-read" 
                            onclick="markAsRead(${notification.id}, this)">
                            Mark as read
                        </button>
                    ` : ''}
                </div>
            `;
            notificationsList.appendChild(notifItem);
        });
    })
    .catch(error => console.error('Error fetching notifications:', error));
}
function markAsRead(notificationId, button) {
    fetch(`/mark_notification_read/${notificationId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            fetchNotifications();
        }
    })
    .catch(error => console.error('Error marking notification as read:', error));
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

document.addEventListener('DOMContentLoaded', () => {
    fetchNotifications();
    setInterval(fetchNotifications, 30000);
});

