import json
import os

# File paths
USERS_FILE = 'data/users.json'

def clear_user_data():
    # Clear users
    with open(USERS_FILE, 'w') as f:
        json.dump({"users": []}, f, indent=4)
    
    print("User data has been cleared successfully!")

if __name__ == '__main__':
    clear_user_data() 