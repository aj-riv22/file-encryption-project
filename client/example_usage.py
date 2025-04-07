from cloud_client import CloudClient
from config import Config

def main():
    client = CloudClient(
        server_url=Config.SERVER_URL,
        username="your_username",
        password="your_password"
    )
    
    if client.authenticate():
        print("Authentication successful!")
        # Start syncing the default directory
        client.start_sync(Config.DEFAULT_SYNC_DIR)
    else:
        print("Authentication failed!")

if __name__ == "__main__":
    main() 