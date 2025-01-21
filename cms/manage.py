#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pyngrok import ngrok,conf  # Import Ngrok
import threading  # For running Ngrok in a separate thread
def start_ngrok():
    """Start Ngrok and establish a tunnel."""
    conf.get_default().auth_token = "2rtoc6LmVmTrR6mWEaRxeZBJZ4w_2XRgnUu2f8rxhdfvSyUx7"  # Set the Ngrok auth token
    if not ngrok.get_ngrok_process():  # Check if an Ngrok process already exists
        public_url = ngrok.connect(8000)  # Replace 8000 with your Django server's port
        print(f"Ngrok tunnel established at {public_url.public_url}")
        print("Forwarding requests to Django development server...")
    else:
        print("Ngrok is already running. Using the existing tunnel.")

def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cms.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # Start Ngrok in a separate thread after 'runserver' starts
    # if "runserver" in sys.argv:
    #     threading.Thread(target=start_ngrok, daemon=True).start()

    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
