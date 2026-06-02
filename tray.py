import threading
from PIL import Image, ImageDraw
import pystray

class SystemTrayApp:
    def __init__(self, on_exit_callback, on_toggle_callback):
        self.on_exit_callback = on_exit_callback
        self.on_toggle_callback = on_toggle_callback
        self.is_paused = False
        self.icon = None
        
    def create_image(self, width, height, color1, color2):
        """Generates a premium-looking icon dynamically (indigo camera style)."""
        image = Image.new('RGB', (width, height), color1)
        dc = ImageDraw.Draw(image)
        # Draw a sleek camera representation
        dc.rounded_rectangle([width//4, height//4, width*3//4, height*3//4], radius=6, fill=color2)
        dc.ellipse([width//3, height//3, width*2//3, height*2//3], fill=color1)
        dc.rectangle([width//2 - 4, height//6, width//2 + 4, height//4], fill=color2)
        return image

    def _on_toggle(self, icon, item):
        self.is_paused = not self.is_paused
        self.on_toggle_callback(self.is_paused)
        # Update the tray icon menu state
        icon.update_menu()

    def _on_exit(self, icon, item):
        icon.stop()
        self.on_exit_callback()

    def run(self):
        """Starts the system tray icon loop."""
        # Create standard icon (indigo background, white camera)
        icon_image = self.create_image(64, 64, (79, 70, 229), (255, 255, 255))
        
        # Create menu
        menu = pystray.Menu(
            pystray.MenuItem(
                text=lambda item: "⏸️ Призупинити гарячі клавіші" if not self.is_paused else "▶️ Відновити роботу",
                action=self._on_toggle
            ),
            pystray.MenuItem(
                text="❌ Вийти з програми",
                action=self._on_exit
            )
        )
        
        self.icon = pystray.Icon("screensolver", icon_image, "Screen Solver Bot", menu)
        self.icon.run()
