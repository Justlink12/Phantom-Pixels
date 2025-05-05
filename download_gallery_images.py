import requests
import json
import os
from time import sleep

# Steam App IDs for games
STEAM_APP_IDS = {
    "1": "1091500",  # Cyberpunk 2077
    "2": "292030",   # The Witcher 3
    "3": "1174180",  # Red Dead Redemption 2
    "4": "1245620",  # Elden Ring
    "5": "1817070",  # God of War Ragnarök
    "6": "1817190",  # Spider-Man 2
    "7": "1817070",  # Final Fantasy XVI
    "8": "1716740",  # Starfield
    "9": "2050650",  # Resident Evil 4 Remake
    "10": "1151640", # Horizon Forbidden West
    "11": "1086940", # Baldur's Gate 3
    "12": "1364780", # Street Fighter 6
    "13": None,      # Diablo IV (not on Steam)
    "14": "1812150", # Assassin's Creed Mirage
    "15": "1088850", # Alan Wake 2
    "16": "1971870", # Mortal Kombat 1
    "17": "1774580", # Star Wars Jedi: Survivor
    "18": "1693980", # Dead Space Remake
    "19": "1627720", # Lies of P
    "20": "1244090"  # Sea of Stars
}

# Fallback Unsplash images for games not on Steam or when Steam fails
UNSPLASH_FALLBACKS = {
    "1": [  # Cyberpunk 2077
        "https://images.unsplash.com/photo-1542751371-adc38448a05e",
        "https://images.unsplash.com/photo-1538481199705-c710c4e965fc",
        "https://images.unsplash.com/photo-1552820728-8b83bb6b773f",
        "https://images.unsplash.com/photo-1550745165-9bc0b252726f"
    ],
    "2": [  # The Witcher 3
        "https://images.unsplash.com/photo-1511512578047-dfb367046420",
        "https://images.unsplash.com/photo-1486572788966-cfd3df1f5b42",
        "https://images.unsplash.com/photo-1548484352-ea579e93b434",
        "https://images.unsplash.com/photo-1551103782-8ab07afd45c1"
    ],
    "3": [  # Red Dead Redemption 2
        "https://images.unsplash.com/photo-1533158326339-7f3cf2404354",
        "https://images.unsplash.com/photo-1564509143629-ddada1c579b7",
        "https://images.unsplash.com/photo-1533158388470-9a56699990c6",
        "https://images.unsplash.com/photo-1516651029879-bcd191e7d33b"
    ],
    "4": [  # Elden Ring
        "https://images.unsplash.com/photo-1496167117681-944f702be1f4",
        "https://images.unsplash.com/photo-1518709268805-4e9042af9f23",
        "https://images.unsplash.com/photo-1510915361894-db8b60106cb1",
        "https://images.unsplash.com/photo-1531297484001-80022131f5a1"
    ],
    "13": [  # Diablo IV
        "https://images.unsplash.com/photo-1542751371-adc38448a05e",
        "https://images.unsplash.com/photo-1538481199705-c710c4e965fc",
        "https://images.unsplash.com/photo-1552820728-8b83bb6b773f",
        "https://images.unsplash.com/photo-1550745165-9bc0b252726f"
    ],
    "19": [  # Lies of P
        "https://images.unsplash.com/photo-1518709268805-4e9042af9f23",
        "https://images.unsplash.com/photo-1510915361894-db8b60106cb1",
        "https://images.unsplash.com/photo-1531297484001-80022131f5a1",
        "https://images.unsplash.com/photo-1496167117681-944f702be1f4"
    ],
    "20": [  # Sea of Stars
        "https://images.unsplash.com/photo-1496167117681-944f702be1f4",
        "https://images.unsplash.com/photo-1518709268805-4e9042af9f23",
        "https://images.unsplash.com/photo-1510915361894-db8b60106cb1",
        "https://images.unsplash.com/photo-1531297484001-80022131f5a1"
    ]
}

def get_steam_screenshots(app_id):
    """Get Steam screenshots for a game using its Steam App ID"""
    try:
        # Steam API endpoint for game details
        url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data[str(app_id)]['success']:
            # Get screenshots from the game details
            screenshots = data[str(app_id)]['data'].get('screenshots', [])
            return [screenshot['path_full'] for screenshot in screenshots[:4]]
    except Exception as e:
        print(f"Error fetching Steam screenshots for app ID {app_id}: {str(e)}")
    
    return []

def download_gallery_image(game_id, image_num, url):
    # Create the directory if it doesn't exist
    os.makedirs("static/images/games/gallery", exist_ok=True)
    
    # Add parameters for image size and quality if it's an Unsplash URL
    if "unsplash.com" in url:
        url = f"{url}?w=1200&h=800&fit=crop&q=80"
    
    # Local file path
    file_path = f"static/images/games/gallery/{game_id}_{image_num}.jpg"
    
    try:
        # Download the image
        response = requests.get(url)
        response.raise_for_status()
        
        # Save the image
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        print(f"Successfully downloaded gallery image {image_num} for game {game_id}")
        return True
    except Exception as e:
        print(f"Error downloading gallery image {image_num} for game {game_id}: {str(e)}")
        return False

def main():
    print("Starting gallery image downloads...")
    
    # Load products to get game names
    with open('products.json', 'r') as f:
        products = json.load(f)
    
    # Download gallery images for each game
    for game_id in products.keys():
        game_name = products[game_id]['name']
        print(f"\nProcessing {game_name} (ID: {game_id})...")
        
        # Try Steam screenshots first
        steam_app_id = STEAM_APP_IDS.get(game_id)
        if steam_app_id:
            print(f"Attempting to fetch Steam screenshots for {game_name}...")
            steam_urls = get_steam_screenshots(steam_app_id)
            
            if steam_urls:
                print(f"Found {len(steam_urls)} Steam screenshots")
                for i, url in enumerate(steam_urls, 1):
                    if download_gallery_image(game_id, i, url):
                        print(f"✓ Successfully downloaded Steam screenshot {i}")
                    else:
                        print(f"✗ Failed to download Steam screenshot {i}")
                    sleep(1)
                continue
        
        # Fall back to Unsplash images if Steam screenshots failed
        print(f"Falling back to Unsplash images for {game_name}...")
        fallback_urls = UNSPLASH_FALLBACKS.get(game_id, [
            f"https://images.unsplash.com/photo-1496167117681-944f702be1f4?w=1200&h=800&fit=crop&q=80",
            f"https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1200&h=800&fit=crop&q=80",
            f"https://images.unsplash.com/photo-1510915361894-db8b60106cb1?w=1200&h=800&fit=crop&q=80",
            f"https://images.unsplash.com/photo-1531297484001-80022131f5a1?w=1200&h=800&fit=crop&q=80"
        ])
        
        for i, url in enumerate(fallback_urls, 1):
            if download_gallery_image(game_id, i, url):
                print(f"✓ Successfully downloaded fallback image {i}")
            else:
                print(f"✗ Failed to download fallback image {i}")
            sleep(1)
    
    print("\nGallery download process completed!")

def download_specific_game(game_id):
    """Download gallery images for a specific game"""
    print(f"Starting gallery image download for game {game_id}...")
    
    # Load products to get game names
    with open('products.json', 'r') as f:
        products = json.load(f)
    
    if game_id not in products:
        print(f"Game ID {game_id} not found in products.json")
        return
        
    game_name = products[game_id]['name']
    print(f"\nProcessing {game_name} (ID: {game_id})...")
    
    # Try Steam screenshots first
    steam_app_id = STEAM_APP_IDS.get(game_id)
    if steam_app_id:
        print(f"Attempting to fetch Steam screenshots for {game_name}...")
        steam_urls = get_steam_screenshots(steam_app_id)
        
        if steam_urls:
            print(f"Found {len(steam_urls)} Steam screenshots")
            for i, url in enumerate(steam_urls, 1):
                if download_gallery_image(game_id, i, url):
                    print(f"✓ Successfully downloaded Steam screenshot {i}")
                else:
                    print(f"✗ Failed to download Steam screenshot {i}")
                sleep(1)
            return
    
    # Fall back to Unsplash images if Steam screenshots failed
    print(f"Falling back to Unsplash images for {game_name}...")
    fallback_urls = UNSPLASH_FALLBACKS.get(game_id, [
        f"https://images.unsplash.com/photo-1496167117681-944f702be1f4?w=1200&h=800&fit=crop&q=80",
        f"https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1200&h=800&fit=crop&q=80",
        f"https://images.unsplash.com/photo-1510915361894-db8b60106cb1?w=1200&h=800&fit=crop&q=80",
        f"https://images.unsplash.com/photo-1531297484001-80022131f5a1?w=1200&h=800&fit=crop&q=80"
    ])
    
    for i, url in enumerate(fallback_urls, 1):
        if download_gallery_image(game_id, i, url):
            print(f"✓ Successfully downloaded fallback image {i}")
        else:
            print(f"✗ Failed to download fallback image {i}")
        sleep(1)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        # If game ID is provided as argument, download only that game
        game_id = sys.argv[1]
        download_specific_game(game_id)
    else:
        # Otherwise run the full download
        main() 