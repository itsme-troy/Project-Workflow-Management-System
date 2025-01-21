from pyngrok import ngrok
import time

def start_ngrok():
    # Set your auth token
    ngrok.set_auth_token("2rtoc6LmVmTrR6mWEaRxeZBJZ4w_2XRgnUu2f8rxhdfvSyUx7")

    # Establish the tunnel
    public_url = ngrok.connect(8000)  # Replace 8000 with the port your Django server is running on
    print(f"Ngrok tunnel established at {public_url.public_url}")

    # Keep the listener alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Closing Ngrok tunnel")
        ngrok.disconnect(public_url.public_url)  # Disconnect the tunnel
        ngrok.kill()  # Stop the Ngrok process

if __name__ == "__main__":
    start_ngrok()
