import requests
import json
import os
from time import sleep

# Game image URLs
GAME_IMAGES = {
    "1": "https://cdn.akamai.steamstatic.com/steam/apps/1091500/header.jpg",  # Cyberpunk 2077
    "2": "https://cdn.akamai.steamstatic.com/steam/apps/292030/header.jpg",   # The Witcher 3
    "3": "https://cdn.akamai.steamstatic.com/steam/apps/1174180/header.jpg",  # Red Dead Redemption 2
    "4": "https://cdn.akamai.steamstatic.com/steam/apps/1245620/header.jpg",  # Elden Ring
    "5": "https://cdn.akamai.steamstatic.com/steam/apps/1817070/header.jpg",  # God of War Ragnarök
    "6": "https://cdn.akamai.steamstatic.com/steam/apps/1817190/header.jpg",  # Spider-Man 2
    "7": "https://cdn.akamai.steamstatic.com/steam/apps/1817070/header.jpg",  # Final Fantasy XVI
    "8": "https://cdn.akamai.steamstatic.com/steam/apps/1716740/header.jpg",  # Starfield
    "9": "https://cdn.akamai.steamstatic.com/steam/apps/2050650/header.jpg",  # Resident Evil 4 Remake
    "10": "https://cdn.akamai.steamstatic.com/steam/apps/1151640/header.jpg", # Horizon Forbidden West
    "11": "https://cdn.akamai.steamstatic.com/steam/apps/1086940/header.jpg", # Baldur's Gate 3
    "12": "https://cdn.akamai.steamstatic.com/steam/apps/1364780/header.jpg", # Street Fighter 6
    "13": "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=800&h=400&fit=crop", # Diablo IV (gaming placeholder)
    "14": "https://cdn.akamai.steamstatic.com/steam/apps/1812150/header.jpg", # Assassin's Creed Mirage
    "15": "https://cdn.akamai.steamstatic.com/steam/apps/1088850/header.jpg", # Alan Wake 2
    "16": "https://cdn.akamai.steamstatic.com/steam/apps/1971870/header.jpg", # Mortal Kombat 1
    "17": "https://cdn.akamai.steamstatic.com/steam/apps/1774580/header.jpg", # Star Wars Jedi: Survivor
    "18": "https://cdn.akamai.steamstatic.com/steam/apps/1693980/header.jpg", # Dead Space Remake
    "19": "https://cdn.akamai.steamstatic.com/steam/apps/1620040/header.jpg", # Lies of P
    "20": "https://cdn.akamai.steamstatic.com/steam/apps/1716740/header.jpg"  # Sea of Stars
}

def download_image(game_id, url):
    # Create the directory if it doesn't exist
    os.makedirs("static/images/games", exist_ok=True)
    
    # Local file path
    file_path = f"static/images/games/{game_id}.jpg"
    
    try:
        # Download the image
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Save the image
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        print(f"Successfully downloaded image for game {game_id}")
        return True
    except Exception as e:
        print(f"Error downloading image for game {game_id}: {str(e)}")
        return False

def main():
    print("Starting game image downloads...")
    
    # Load products to get game names
    with open('products.json', 'r') as f:
        products = json.load(f)
    
    # Download images for each game
    for game_id, url in GAME_IMAGES.items():
        game_name = products[game_id]['name']
        print(f"\nDownloading image for {game_name} (ID: {game_id})...")
        
        if download_image(game_id, url):
            print(f"✓ Successfully downloaded {game_name}")
        else:
            print(f"✗ Failed to download {game_name}")
        
        # Add a small delay to avoid overwhelming the server
        sleep(1)
    
    print("\nDownload process completed!")

if __name__ == "__main__":
    main() 