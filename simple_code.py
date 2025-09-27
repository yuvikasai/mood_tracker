import tkinter as tk
from PIL import Image, ImageTk
import os
import glob
import random
from datetime import datetime, timedelta
import re
from collections import Counter
try:
    import pygame
    pygame_available = True
except ImportError:
    pygame_available = False
    print("pygame not found. Music functionality disabled. Install with: pip install pygame")

# Create the main window - scaled down from 1230x420 to 984x336
root = tk.Tk()
root.title("Mood Tracker")
root.geometry("984x336")
root.resizable(False, False)

# Create a canvas to hold everything - scaled down proportionally
canvas = tk.Canvas(root, width=984, height=336, highlightthickness=0, bd=0)
canvas.pack()

# Variables to track current view
current_view = "main"  # "main", "history", or "stats"
history_text = None
history_frame = None
stats_text = None
stats_frame = None

# Variables for falling leaves animation
leaves = []
leaf_photo = None

# Variables for music functionality
music_playing = False
music_paused = False
current_music_file = None
music_files = []

# Load and set the background image - scaled down
try:
    image_path = os.path.join("images", "background.png")
    background_image = Image.open(image_path).resize((984, 336), Image.Resampling.LANCZOS)
    bg_photo = ImageTk.PhotoImage(background_image)
    canvas.create_image(0, 0, image=bg_photo, anchor="nw")
except FileNotFoundError:
    print("Error: background.png not found in images folder")
    canvas.configure(bg="lightgray")
except Exception as e:
    print(f"Error loading image: {e}")
    canvas.configure(bg="lightgray")

# Load leaf image for falling leaves animation
try:
    leaf_path = os.path.join("images", "leaf.png")
    leaf_image = Image.open(leaf_path).resize((20, 20), Image.Resampling.LANCZOS)
    leaf_photo = ImageTk.PhotoImage(leaf_image)
except FileNotFoundError:
    print("Error: leaf.png not found in images folder")
    leaf_photo = None
except Exception as e:
    print(f"Error loading leaf image: {e}")
    leaf_photo = None

# Class to represent a falling leaf with natural movement
class Leaf:
    def __init__(self, canvas, leaf_photo, x, y):
        self.canvas = canvas
        self.photo = leaf_photo
        self.x = x
        self.y = y
        self.speed_x = (hash(str(x + y)) % 3) - 1  # Random horizontal drift (-1, 0, or 1)
        self.speed_y = 1 + (hash(str(x + y)) % 2)  # Random fall speed (1 or 2)
        self.swing = 0  # Swing animation counter
        self.swing_speed = 0.1 + (hash(str(x + y)) % 10) * 0.01  # Random swing speed (0.1-0.19)
        if self.photo:
            self.canvas_id = self.canvas.create_image(self.x, self.y, image=self.photo, anchor="center", tags="leaf")
        else:
            self.canvas_id = None
    
    def update(self):
        if not self.canvas_id:
            return False
        
        # Update position with swaying motion (mimics natural leaf falling)
        self.swing += self.swing_speed
        swing_offset = 2 * (0.5 - abs(0.5 - (self.swing % 1)))  # Creates a triangular wave for swaying
        self.x += self.speed_x + swing_offset
        self.y += self.speed_y
        
        # Move the leaf on canvas
        self.canvas.coords(self.canvas_id, self.x, self.y)
        
        # Remove leaf if it goes off screen
        if self.y > 350:  # Slightly below the canvas height
            self.canvas.delete(self.canvas_id)
            return False
        
        return True

# Function to create new leaves
def create_leaf():
    if leaf_photo and len(leaves) < 15:  # Limit number of leaves
        x = random.randint(-20, 1004)  # Start slightly off-screen
        y = random.randint(-50, -20)   # Start above the canvas
        new_leaf = Leaf(canvas, leaf_photo, x, y)
        leaves.append(new_leaf)

# Function to update all leaves
def update_leaves():
    global leaves
    # Update existing leaves and remove those that are off-screen
    leaves = [leaf for leaf in leaves if leaf.update()]
    
    # Randomly create new leaves (about 10% chance each update)
    if random.random() < 0.1:
        create_leaf()
    
    # Schedule next update
    root.after(50, update_leaves)  # Update every 50ms for smooth animation

# Initialize pygame mixer for music (if available)
if pygame_available:
    try:
        pygame.mixer.init()
        print("Music system initialized successfully")
    except Exception as e:
        print(f"Error initializing music system: {e}")
        pygame_available = False

# Function to load available music files
def load_music_files():
    """Load available music files from the music folder"""
    global music_files
    music_files = []
    
    if not pygame_available:
        return
    
    # Create music folder if it doesn't exist
    music_folder = "music"
    if not os.path.exists(music_folder):
        os.makedirs(music_folder)
        print("Created 'music' folder. Add .mp3, .wav, or .ogg files there for background music!")
        return
    
    # Load music files
    music_extensions = ['*.mp3', '*.wav', '*.ogg']
    for extension in music_extensions:
        files = glob.glob(os.path.join(music_folder, extension))
        music_files.extend(files)
    
    if music_files:
        print(f"Found {len(music_files)} music file(s):")
        for music_file in music_files:
            print(f"  - {os.path.basename(music_file)}")
    else:
        print("No music files found. Add .mp3, .wav, or .ogg files to the 'music' folder!")

# Function to play background music
def play_music():
    """Start or resume background music"""
    global music_playing, music_paused, current_music_file
    
    if not pygame_available or not music_files:
        return
    
    try:
        if music_paused:
            # Resume paused music
            pygame.mixer.music.unpause()
            music_paused = False
            music_playing = True
            print("Music resumed")
        elif not music_playing:
            # Start new music
            if not current_music_file:
                current_music_file = random.choice(music_files)
            
            pygame.mixer.music.load(current_music_file)
            pygame.mixer.music.play(-1)  # -1 means loop indefinitely
            music_playing = True
            print(f"Playing: {os.path.basename(current_music_file)}")
            
    except Exception as e:
        print(f"Error playing music: {e}")

# Function to pause background music
def pause_music():
    """Pause background music"""
    global music_playing, music_paused
    
    if not pygame_available or not music_playing:
        return
    
    try:
        pygame.mixer.music.pause()
        music_playing = False
        music_paused = True
        print("Music paused")
    except Exception as e:
        print(f"Error pausing music: {e}")

# Function to stop background music
def stop_music():
    """Stop background music"""
    global music_playing, music_paused, current_music_file
    
    if not pygame_available:
        return
    
    try:
        pygame.mixer.music.stop()
        music_playing = False
        music_paused = False
        current_music_file = None
        print("Music stopped")
    except Exception as e:
        print(f"Error stopping music: {e}")

# Function to toggle music on/off
def toggle_music():
    """Toggle background music on/off"""
    if music_playing:
        pause_music()
    else:
        play_music()

# Load mood images for slideshow in specific order
mood_images = []
mood_photos = []
current_mood_index = 0

# Define the desired order of moods
mood_order = ["joy", "neutral", "sadness", "anger", "annoyed", "anxiety", "fear"]

try:
    # First, collect all mood files
    all_mood_files = []
    image_extensions = ['*.png', '*.jpg', '*.jpeg']
    for extension in image_extensions:
        files = glob.glob(os.path.join("images", extension))
        for file in files:
            filename = os.path.basename(file).lower()
            # Exclude UI elements and the leaf animation image from mood selection
            if not any(exclude in filename for exclude in ['background', 'arrow1', 'arrow2', 'close', 'click1','confirmation','notes','history','stats','leaf','music']):
                all_mood_files.append(file)

    # Sort files according to the specified mood order
    ordered_mood_files = []
    
    # Add files in the specified order
    for mood in mood_order:
        for file in all_mood_files:
            filename = os.path.splitext(os.path.basename(file))[0].lower()
            if filename == mood.lower():
                ordered_mood_files.append(file)
                break
    
    # Add any remaining files that weren't in the specified order
    for file in all_mood_files:
        if file not in ordered_mood_files:
            ordered_mood_files.append(file)

    # Load the ordered mood images - scaled down from 250x250 to 200x200
    for mood_file in ordered_mood_files:
        try:
            img = Image.open(mood_file).resize((200, 200), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            mood_images.append(mood_file)
            mood_photos.append(photo)
        except Exception as e:
            print(f"Error loading {mood_file}: {e}")

    print(f"Loaded {len(mood_photos)} mood images in order:")
    for i, img in enumerate(mood_images):
        print(f"{i+1}. {os.path.basename(img)}")

except Exception as e:
    print(f"Error loading mood images: {e}")

# Function to get mood name from filename
def get_mood_name(filename):
    """Extract mood name from filename (without extension)"""
    mood_name = os.path.splitext(os.path.basename(filename))[0]
    return mood_name.capitalize()

# Function to save mood log to file
def save_mood_log(mood_name, note_text):
    """Save mood and note to a text file"""
    try:
        now = datetime.now()
        date = now.strftime("%Y-%m-%d")
        time = now.strftime("%H:%M:%S")
        
        with open("mood_log.txt", "a", encoding="utf-8") as file:
            file.write(f"Date: {date} Time: {time} Mood: {mood_name}\n")
            file.write(f"Note: {note_text}\n\n")
        print(f"Mood logged: {mood_name} with note: {note_text}")
    except Exception as e:
        print(f"Error saving mood log: {e}")

# Function to load mood history from file
def load_mood_history():
    """Load all mood logs from the text file with newest first"""
    try:
        if os.path.exists("mood_log.txt"):
            with open("mood_log.txt", "r", encoding="utf-8") as file:
                content = file.read()
                if content.strip():
                    # Split by double newlines to get individual entries
                    entries = content.strip().split('\n\n')
                    # Reverse to show newest first
                    entries.reverse()
                    # Join back with double newlines
                    return '\n\n'.join(entries)
                else:
                    return "No mood logs found. Start logging your moods!"
        else:
            return "No mood logs found. Start logging your moods!"
    except Exception as e:
        return f"Error loading mood history: {e}"

# Function to calculate mood statistics
def calculate_mood_stats():
    """Calculate various mood statistics"""
    try:
        if not os.path.exists("mood_log.txt"):
            return "No mood logs found. Start logging your moods!"
        
        with open("mood_log.txt", "r", encoding="utf-8") as file:
            content = file.read()
        
        if not content.strip():
            return "No mood logs found. Start logging your moods!"
        
        # Parse mood entries
        mood_pattern = r"Date: (\d{4}-\d{2}-\d{2}) Time: (\d{2}:\d{2}:\d{2}) Mood: (\w+)"
        matches = re.findall(mood_pattern, content)
        
        if not matches:
            return "No valid mood entries found!"
        
        # Extract data
        dates = [datetime.strptime(match[0], "%Y-%m-%d").date() for match in matches]
        times = [match[1] for match in matches]
        moods = [match[2] for match in matches]
        
        # Calculate statistics
        total_entries = len(matches)
        mood_counts = Counter(moods)
        
        # Date range
        min_date = min(dates) if dates else None
        max_date = max(dates) if dates else None
        
        # Recent activity (last 7 days)
        recent_date = datetime.now().date() - timedelta(days=7)
        recent_moods = [mood for date, mood in zip(dates, moods) if date >= recent_date]
        
        # Today's entries
        today = datetime.now().date()
        today_count = sum(1 for date in dates if date == today)
        
        # Build statistics text
        stats_text = "OVERVIEW:\n"
        stats_text += f"Total Entries: {total_entries}\n"
        stats_text += f"Today's Logs: {today_count}\n"
        stats_text += f"Last 7 Days: {len(recent_moods)} entries\n\n"
        
        if min_date and max_date:
            days_tracked = (max_date - min_date).days + 1
            stats_text += f"DATE RANGE:\n"
            stats_text += f"First Entry: {min_date.strftime('%Y-%m-%d')}\n"
            stats_text += f"Latest Entry: {max_date.strftime('%Y-%m-%d')}\n"
            stats_text += f"Days Tracked: {days_tracked}\n\n"
        
        stats_text += f"TOP 3 MOODS:\n"
        for mood, count in mood_counts.most_common(3):
            percentage = (count / total_entries) * 100
            stats_text += f"{mood}: {count} times ({percentage:.1f}%)\n"
        
        return stats_text
        
    except Exception as e:
        return f"Error calculating statistics: {e}"

# Function to hide confirmation message
def hide_confirmation():
    canvas.delete("confirmation")

# Function to handle mood selection
def select_mood(event=None):
    if mood_photos and current_view == "main":
        current_mood = get_mood_name(mood_images[current_mood_index])
        note_text = note_entry.get("1.0", "end-1c")  # Get text from text widget
        
        # Save mood with note
        save_mood_log(current_mood, note_text)
        
        # Clear the note after logging
        note_entry.delete("1.0", "end")
        
        # Show confirmation message
        show_confirmation(current_mood)

def show_confirmation(mood_name):
    """Show mood logged confirmation message"""
    # Clear any existing confirmation
    canvas.delete("confirmation")
    
    # Show confirmation image if available - scaled position
    if confirmation_photo:
        canvas.create_image(792, 160, image=confirmation_photo, anchor="center", tags="confirmation")
    
    # Auto-hide confirmation after 2 seconds
    root.after(2000, hide_confirmation)

def show_main_view():
    """Show the main mood tracking interface"""
    global current_view, history_text, history_frame, stats_text, stats_frame
    current_view = "main"
    
    # Hide other widgets if they exist
    if history_text:
        history_text.destroy()
        history_text = None
    if history_frame:
        history_frame.destroy()
        history_frame = None
    if stats_text:
        stats_text.destroy()
        stats_text = None
    if stats_frame:
        stats_frame.destroy()
        stats_frame = None
    
    # Show main interface elements - scaled position
    note_entry.place(x=40, y=96)
    
    update_mood_display()

def show_history_view():
    """Show the mood history interface"""
    global current_view, history_text, history_frame, stats_text, stats_frame
    current_view = "history"
    
    # Hide main interface elements
    note_entry.place_forget()
    canvas.delete("mood", "mood_text", "click_button")
    
    # Hide stats widgets if they exist
    if stats_text:
        stats_text.destroy()
        stats_text = None
    if stats_frame:
        stats_frame.destroy()
        stats_frame = None
    
    # Create history frame - scaled dimensions
    history_frame = tk.Frame(root)
    history_frame.place(x=40, y=96, width=525, height=178)
    
    # Create text widget for history - scaled font
    history_text = tk.Text(history_frame, font=("Stardew Valley", 16), 
                          wrap=tk.WORD, bg="#ffc478", fg="#88563d",
                          relief="solid", bd=2)
    
    # Create scrollbar
    scrollbar = tk.Scrollbar(history_frame, orient="vertical", command=history_text.yview)
    history_text.configure(yscrollcommand=scrollbar.set)
    
    # Pack widgets
    history_text.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Load and display mood history
    history_content = load_mood_history()
    history_text.delete("1.0", "end")
    history_text.insert("1.0", history_content)
    
    # Make text read-only
    history_text.configure(state="disabled")
    
    # Display mood images and navigation (but disable click button)
    update_mood_display()

def show_stats_view():
    """Show the mood statistics interface"""
    global current_view, history_text, history_frame, stats_text, stats_frame
    current_view = "stats"
    
    # Hide main interface elements
    note_entry.place_forget()
    canvas.delete("mood", "mood_text", "click_button")
    
    # Hide history widgets if they exist
    if history_text:
        history_text.destroy()
        history_text = None
    if history_frame:
        history_frame.destroy()
        history_frame = None
    
    # Create stats frame - scaled dimensions
    stats_frame = tk.Frame(root)
    stats_frame.place(x=40, y=96, width=525, height=178)
    
    # Create text widget for stats - scaled font
    stats_text = tk.Text(stats_frame, font=("Stardew Valley", 16), 
                        wrap=tk.WORD, bg="#ffc478", fg="#88563d",
                        relief="solid", bd=2)
    
    # Create scrollbar
    scrollbar = tk.Scrollbar(stats_frame, orient="vertical", command=stats_text.yview)
    stats_text.configure(yscrollcommand=scrollbar.set)
    
    # Pack widgets
    stats_text.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Load and display mood statistics
    stats_content = calculate_mood_stats()
    stats_text.delete("1.0", "end")
    stats_text.insert("1.0", stats_content)
    
    # Make text read-only
    stats_text.configure(state="disabled")
    
    # Display mood images and navigation (but disable click button)
    update_mood_display()

# Functions for Notes, History, and Stats button handlers
def open_notes(event=None):
    """Switch to the main notes/mood tracking view"""
    print("Switching to Notes view")
    show_main_view()

def open_history(event=None):
    """Switch to the mood history view"""
    print("Switching to History view")
    show_history_view()

def open_stats(event=None):
    """Switch to the mood statistics view"""
    print("Switching to Statistics view")
    show_stats_view()

# Update mood display on canvas (called when mood changes or view switches)
def update_mood_display():
    # Clear existing mood elements
    canvas.delete("mood")
    canvas.delete("mood_text")
    canvas.delete("click_button")
    if mood_photos:
        # Display current mood image - scaled position
        canvas.create_image(792, 144, image=mood_photos[current_mood_index], anchor="center", tags="mood")
        
        # Display mood name below the image with scaled font
        mood_name = get_mood_name(mood_images[current_mood_index])
        canvas.create_text(792, 284, text=mood_name, font=("Stardew Valley", 32, "bold"), 
                          fill="#895837", anchor="center", tags="mood_text")
        
        # Only show click button in main view (not in history or stats)
        if current_view == "main":
            # Display click button above the mood image - scaled position
            canvas.create_image(936, 232, image=click_photo, anchor="center", tags="click_button")

def next_mood(event=None):
    global current_mood_index
    if mood_photos:
        current_mood_index = (current_mood_index + 1) % len(mood_photos)
        update_mood_display()
        print(f"Showing mood image: {os.path.basename(mood_images[current_mood_index])}")

def previous_mood(event=None):
    global current_mood_index
    if mood_photos:
        current_mood_index = (current_mood_index - 1) % len(mood_photos)
        update_mood_display()
        print(f"Showing mood image: {os.path.basename(mood_images[current_mood_index])}")

# Create text widget for multi-line notes - scaled dimensions and font
note_entry = tk.Text(root, width=52, height=8, font=("Stardew Valley", 16), 
                     wrap=tk.WORD, bg="#ffc478", relief="solid", bd=2, fg="#88563d")
note_entry.place(x=40, y=96)

# Load and place arrow images as clickable canvas items - scaled sizes and positions
try:
    arrow2_path = os.path.join("images", "arrow2.png")
    arrow2_image = Image.open(arrow2_path).resize((32, 32), Image.Resampling.LANCZOS)
    arrow2_photo = ImageTk.PhotoImage(arrow2_image)

    arrow1_path = os.path.join("images", "arrow1.png")
    arrow1_image = Image.open(arrow1_path).resize((32, 32), Image.Resampling.LANCZOS)
    arrow1_photo = ImageTk.PhotoImage(arrow1_image)

    # Add left arrow image - scaled position
    left_arrow = canvas.create_image(624, 168, image=arrow2_photo, anchor="center")
    canvas.tag_bind(left_arrow, "<Button-1>", previous_mood)

    # Add right arrow image - scaled position
    right_arrow = canvas.create_image(960, 168, image=arrow1_photo, anchor="center")
    canvas.tag_bind(right_arrow, "<Button-1>", next_mood)

    # Keep references to prevent garbage collection
    canvas.arrow_left = arrow2_photo
    canvas.arrow_right = arrow1_photo
    canvas.bg = bg_photo
    canvas.leaf = leaf_photo

except FileNotFoundError as e:
    print(f"Error: Arrow image not found - {e}")
except Exception as e:
    print(f"Error loading arrow images: {e}")

# Load click button image - scaled size
try:
    click_path = os.path.join("images", "click1.png")
    click_image = Image.open(click_path).resize((35, 35), Image.Resampling.LANCZOS)
    click_photo = ImageTk.PhotoImage(click_image)
    
    # Bind click event to the button (will be created in update_mood_display)
    canvas.tag_bind("click_button", "<Button-1>", select_mood)
    
except FileNotFoundError as e:
    print(f"Error: click1.png not found - {e}")
    click_photo = None
except Exception as e:
    print(f"Error loading click button: {e}")
    click_photo = None

# Load confirmation message image - scaled size
try:
    confirmation_path = os.path.join("images", "confirmation.png")
    confirmation_image = Image.open(confirmation_path).resize((240, 72), Image.Resampling.LANCZOS)
    confirmation_photo = ImageTk.PhotoImage(confirmation_image)
except FileNotFoundError:
    print("No confirmation image found")
    confirmation_photo = None
except Exception as e:
    print(f"Error loading confirmation image: {e}")
    confirmation_photo = None

# Load and place Notes, History, and Stats buttons - scaled sizes and positions
try:
    # Load Notes button - scaled size
    notes_path = os.path.join("images", "notes.png")
    notes_image = Image.open(notes_path).resize((144, 44), Image.Resampling.LANCZOS)
    notes_photo = ImageTk.PhotoImage(notes_image)
    
    # Load History button - scaled size
    history_path = os.path.join("images", "history.png")
    history_image = Image.open(history_path).resize((144, 44), Image.Resampling.LANCZOS)
    history_photo = ImageTk.PhotoImage(history_image)
    
    # Load Stats button - scaled size
    try:
        stats_path = os.path.join("images", "stats.png")
        stats_image = Image.open(stats_path).resize((144, 44), Image.Resampling.LANCZOS)
        stats_photo = ImageTk.PhotoImage(stats_image)
    except FileNotFoundError:
        # Create a simple stats button using text if image doesn't exist
        stats_photo = None
    
    # Load Music button - scaled size (44x44 for square icon)
    music_path = os.path.join("images", "music.png")
    music_image = Image.open(music_path).resize((44, 44), Image.Resampling.LANCZOS)
    music_photo = ImageTk.PhotoImage(music_image)
    
    # Add Notes button to canvas - scaled position
    notes_button = canvas.create_image(96, 48, image=notes_photo, anchor="center")
    canvas.tag_bind(notes_button, "<Button-1>", open_notes)
    
    # Add History button to canvas - scaled position
    history_button = canvas.create_image(256, 48, image=history_photo, anchor="center")
    canvas.tag_bind(history_button, "<Button-1>", open_history)
    
    # Add Stats button to canvas - scaled position and size
    if stats_photo:
        stats_button = canvas.create_image(416, 48, image=stats_photo, anchor="center")
        canvas.tag_bind(stats_button, "<Button-1>", open_stats)
        canvas.stats_photo = stats_photo
    else:
        # Create text-based stats button - scaled dimensions and font
        stats_button = canvas.create_rectangle(352, 28, 480, 68, fill="#ffc478", outline="#88563d", width=2)
        canvas.create_text(416, 48, text="STATISTICS", font=("Stardew Valley", 11, "bold"), fill="#88563d")
        canvas.tag_bind(stats_button, "<Button-1>", open_stats)
    
    # Add Music button to canvas - music.png only
    music_button = canvas.create_image(520, 45, image=music_photo, anchor="center")
    canvas.tag_bind(music_button, "<Button-1>", lambda e: toggle_music())
    canvas.music_photo = music_photo
    
    # Keep references to prevent garbage collection
    canvas.notes_photo = notes_photo
    canvas.history_photo = history_photo
    
except FileNotFoundError as e:
    print(f"Error: Notes or History button image not found - {e}")
except Exception as e:
    print(f"Error loading Notes/History buttons: {e}")

# Load available music files
load_music_files()

# Initialize the mood display
if mood_photos:
    update_mood_display()

# Start falling leaves animation
if leaf_photo:
    update_leaves()

# Auto-start background music if available
if pygame_available and music_files:
    play_music()

# Start the GUI event loop
root.mainloop()