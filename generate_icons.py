import os
from PIL import Image

def generate_icons():
    source_icon = 'src/icon.png'
    
    if not os.path.exists(source_icon):
        print(f"Error: {source_icon} not found!")
        return

    # Define targets: (output_path, size)
    targets = [
        # WeChat MiniGame
        ('src/wechat-minigame/images/icon-1024.png', 1024),
        ('src/wechat-minigame/images/icon-512.png', 512),
        ('src/wechat-minigame/images/icon-256.png', 256),
        ('src/wechat-minigame/images/icon-144.png', 144),
        ('src/wechat-minigame/images/icon-128.png', 128),
        ('src/wechat-minigame/images/icon-64.png', 64),
        
        # Web Frontend
        ('src/frontend/public/icon-192.png', 192),
        ('src/frontend/public/icon-512.png', 512),
        ('src/frontend/public/favicon.ico', 32), # Save as .ico or .png
        
        # iOS App (Expo/React Native)
        ('src/ios-app/assets/icon.png', 1024),
        ('src/ios-app/assets/adaptive-icon.png', 1024),
        ('src/ios-app/assets/favicon.png', 192),
    ]

    try:
        with Image.open(source_icon) as img:
            # Ensure it's square
            width, height = img.size
            if width != height:
                print(f"Warning: Source image is not square ({width}x{height}). It will be resized potentially distorting aspect ratio.")
            
            for path, size in targets:
                # Ensure directory exists
                os.makedirs(os.path.dirname(path), exist_ok=True)
                
                # Resize
                resized_img = img.resize((size, size), Image.Resampling.LANCZOS)
                
                # Save
                if path.endswith('.ico'):
                    resized_img.save(path, format='ICO')
                else:
                    resized_img.save(path, format='PNG')
                
                print(f"Generated: {path} ({size}x{size})")
                
    except Exception as e:
        print(f"Failed to process image: {e}")
        print("Please ensure 'Pillow' is installed: pip install Pillow")

if __name__ == "__main__":
    generate_icons()
