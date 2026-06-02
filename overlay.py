import tkinter as tk
import ctypes
import queue

class OverlayWindow:
    def __init__(self):
        self.queue = queue.Queue()
        
        # 1. Create a hidden root window to prevent taskbar icon for the overlay
        self.parent = tk.Tk()
        self.parent.withdraw()
        
        # 2. Create the actual overlay window as a Toplevel
        self.root = tk.Toplevel(self.parent)
        self.root.title("Screen Solver Overlay")
        
        # 3. Apply window attributes for premium overlay feel
        self.root.overrideredirect(True)       # Borderless
        self.root.wm_attributes("-topmost", True) # Always on top
        self.root.wm_attributes("-alpha", 0.90)   # Premium semi-transparent look
        
        # Dark theme color scheme
        self.bg_color = "#181818"      # Sleek dark gray
        self.text_color = "#E0E0E0"    # Soft white for readability
        self.accent_color = "#4CAF50"  # Soft green accent for headers
        
        self.root.config(bg=self.bg_color)
        
        # Set default size and position (bottom-left area of screen)
        # Width: 480px, Height: auto (dynamic)
        self.width = 480
        self.root.geometry(f"{self.width}x180+50+500")
        
        # Dragging support state
        self.start_x = 0
        self.start_y = 0
        
        # Setup UI layout
        self.setup_ui()
        
        # Enable dragging from anywhere on the window
        self.root.bind("<Button-1>", self.start_drag)
        self.root.bind("<B1-Motion>", self.drag)
        
        # Add a right-click menu for quick actions
        self.create_context_menu()
        self.root.bind("<Button-3>", self.show_context_menu)
        
        # Double-click to clear text and minimize size
        self.root.bind("<Double-Button-1>", lambda e: self.clear_text())
        
        # 4. Exclude from screen capture (OBS, Discord, Zoom, screenshots)
        self.apply_exclusion()
        
        # Start the queue checker
        self.root.after(100, self.check_queue)

    def setup_ui(self):
        # Header/Title Bar Area
        self.header_frame = tk.Frame(self.root, bg=self.bg_color)
        self.header_frame.pack(fill=tk.X, padx=12, pady=(8, 4))
        
        self.header_label = tk.Label(
            self.header_frame, 
            text="✨ SCREEN SOLVER OVERLAY", 
            font=("Segoe UI", 8, "bold"), 
            fg=self.accent_color, 
            bg=self.bg_color
        )
        self.header_label.pack(side=tk.LEFT)
        
        # Small Close Label (top right)
        self.close_btn = tk.Label(
            self.header_frame, 
            text="✕", 
            font=("Segoe UI", 9, "bold"), 
            fg="#777777", 
            bg=self.bg_color,
            cursor="hand2"
        )
        self.close_btn.pack(side=tk.RIGHT)
        self.close_btn.bind("<Button-1>", lambda e: self.clear_text())
        
        # Divider Line
        self.divider = tk.Frame(self.root, height=1, bg="#2c2c2c")
        self.divider.pack(fill=tk.X, padx=12, pady=(0, 8))
        
        # Main text content area
        self.text_frame = tk.Frame(self.root, bg=self.bg_color)
        self.text_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))
        
        # Text label with autowrap
        self.label = tk.Label(
            self.text_frame,
            text="Чекаю запит...\nНатисніть гарячі клавіші (Ctrl + Shift + F12), щоб отримати відповідь.",
            font=("Segoe UI", 11),
            fg=self.text_color,
            bg=self.bg_color,
            justify=tk.LEFT,
            anchor="nw",
            wraplength=self.width - 24
        )
        self.label.pack(fill=tk.BOTH, expand=True)

    def start_drag(self, event):
        self.start_x = event.x
        self.start_y = event.y

    def drag(self, event):
        x = self.root.winfo_x() + (event.x - self.start_x)
        y = self.root.winfo_y() + (event.y - self.start_y)
        self.root.geometry(f"+{x}+{y}")

    def apply_exclusion(self):
        self.root.update()
        hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
        if hwnd == 0:
            hwnd = self.root.winfo_id()
            
        # WDA_EXCLUDEFROMCAPTURE = 0x00000011
        result = ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, 0x00000011)
        print(f"Exclusion display affinity applied to HWND {hwnd}: {'SUCCESS' if result else 'FAILED'}")

    def create_context_menu(self):
        # Create a Frame that acts as a custom context menu
        self.menu_frame = tk.Frame(
            self.root, 
            bg="#242424", 
            highlightbackground="#2c2c2c", 
            highlightthickness=1
        )
        
        # Styles for menu buttons
        btn_opts = {
            "bg": "#242424",
            "fg": self.text_color,
            "activebackground": self.accent_color,
            "activeforeground": "white",
            "bd": 0,
            "anchor": "w",
            "padx": 15,
            "pady": 6,
            "font": ("Segoe UI", 9)
        }
        
        self.btn_clear = tk.Button(self.menu_frame, text="Очистити", command=self.menu_clear, **btn_opts)
        self.btn_hide = tk.Button(self.menu_frame, text="Сховати на 5 сек", command=self.menu_hide, **btn_opts)
        self.btn_close = tk.Button(self.menu_frame, text="Закрити оверлей", command=self.menu_close, **btn_opts)
        
        self.btn_clear.pack(fill=tk.X)
        self.btn_hide.pack(fill=tk.X)
        self.btn_close.pack(fill=tk.X)
        
        # Hover animations
        def on_enter(e):
            e.widget.config(bg="#333333")
        def on_leave(e):
            e.widget.config(bg="#242424")
            
        for btn in [self.btn_clear, self.btn_hide, self.btn_close]:
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)

    def show_context_menu(self, event):
        # Place the menu at the cursor relative to the root window
        x = event.x
        y = event.y
        
        # Keep it within bounds
        win_width = self.root.winfo_width()
        win_height = self.root.winfo_height()
        menu_width = 140
        menu_height = 90
        
        if x + menu_width > win_width:
            x = win_width - menu_width - 5
        if y + menu_height > win_height:
            y = win_height - menu_height - 5
            
        self.menu_frame.place(x=x, y=y)
        
        # Bind left-click to detect clicks outside the menu and close it
        self.root.bind("<Button-1>", self.on_root_click, add="+")

    def on_root_click(self, event):
        # Hide menu if click is outside of the menu frame
        x, y = event.x, event.y
        if self.menu_frame.winfo_parent():
            menu_x = self.menu_frame.winfo_x()
            menu_y = self.menu_frame.winfo_y()
            menu_w = self.menu_frame.winfo_width()
            menu_h = self.menu_frame.winfo_height()
            
            if not (menu_x <= x <= menu_x + menu_w and menu_y <= y <= menu_y + menu_h):
                self.hide_context_menu()
                
    def hide_context_menu(self):
        self.menu_frame.place_forget()
        # Restore default dragging behavior
        self.root.bind("<Button-1>", self.start_drag)

    def menu_clear(self):
        self.clear_text()

    def menu_hide(self):
        self.temp_hide()

    def menu_close(self):
        self.root.withdraw()
        self.hide_context_menu()

    def clear_text(self):
        self.hide_context_menu()
        self.label.config(text="Чекаю запит...")
        self.root.geometry(f"{self.width}x80") # Minimize height

    def temp_hide(self):
        self.hide_context_menu()
        self.root.withdraw()
        self.root.after(5000, self.root.deiconify)

    def show_answer(self, text):
        self.queue.put(text)

    def check_queue(self):
        try:
            while True:
                text = self.queue.get_nowait()
                self.hide_context_menu()
                # If window is hidden, show it
                self.root.deiconify()
                
                # Format text and estimate height
                self.label.config(text=text)
                
                # Dynamic height adjustment based on text length
                # Segoe UI 11 at 450px width fits approx. 40 characters per line.
                line_count = sum(max(1, len(line) // 40) for line in text.split('\n'))
                new_height = max(80, 50 + (line_count * 22))
                self.root.geometry(f"{self.width}x{new_height}")
                
        except queue.Empty:
            pass
        self.root.after(100, self.check_queue)
        
    def start(self):
        # Run tkinter event loop
        self.parent.mainloop()
