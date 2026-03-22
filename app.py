import flet as ft
import pygame
import os
import asyncio
import random  
from mutagen.mp3 import MP3
import base64
from mutagen.id3 import ID3, APIC

class Song:
    def __init__(self, filename, folder="canciones"):
        self.filename = filename
        self.folder = folder
        self.path = os.path.join(folder, filename)
        self.title = os.path.splitext(filename)[0]
        self.duration = self.get_duration()
        self.cover_path = self.get_cover() 

    def get_duration(self):
        try:
            audio = MP3(self.path)
            return audio.info.length
        except: return 0

    def get_cover(self):
       
        try:
            audio = ID3(self.path)
            for tag in audio.values():
                if isinstance(tag, APIC): 
                    
                    return base64.b64encode(tag.data).decode('utf-8')
        except:
            pass

        
        base_dir = os.path.dirname(self.path)
        for file in os.listdir(base_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                return os.path.join(base_dir, file)

        
        return "/default.jpg"

async def main(page: ft.Page):
    page.title = "Reproductor Musical Pro"
    page.bgcolor = ft.Colors.BLACK
    page.window_width = 400
    page.window_height = 600
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    pygame.mixer.init()

    
    current_song_index = 0  
    
    
    playlist = []
    for root, dirs, files in os.walk("canciones"):
        for file in files:
            if file.endswith(".mp3"):
                playlist.append(Song(file, folder=root))

    
    song_info = ft.Text("Selecciona una canción", size=20, color=ft.Colors.WHITE, weight="bold", text_align="center")
    current_time_text = ft.Text("00:00", color=ft.Colors.CYAN_ACCENT)
    duration_text = ft.Text("00:00", color=ft.Colors.WHITE60)
    progress_bar = ft.ProgressBar(value=0.0, width=300, color=ft.Colors.CYAN_ACCENT, bgcolor=ft.Colors.WHITE10)

    
    album_art = ft.Image(
        src="/default.jpg", 
        width=250,
        height=250,
        fit="cover",
        border_radius=20,
    )

    
    def load_song():
        if playlist:
            
            pygame.mixer.music.load(playlist[current_song_index].path)
            update_song_info()

    def update_song_info():
        if not playlist: return
        song = playlist[current_song_index]
        song_info.value = song.title
        
        
        album_art.src = ""
        album_art.src_base64 = ""

        
        if song.cover_path:
            if song.cover_path.startswith("http"):
                album_art.src = song.cover_path
            elif len(song.cover_path) > 500: 
                album_art.src_base64 = song.cover_path
            else: 
                album_art.src = song.cover_path
        else:
            album_art.src = "/default.jpg"
            
        duration_text.value = format_time(song.duration)
        progress_bar.value = 0.0
        current_time_text.value = "00:00"
        page.update()

    def format_time(seconds):
        minutes, seconds = divmod(int(seconds), 60)
        return f"{minutes:02d}:{seconds:02d}"

    def play_pause(e):
        if not playlist: return
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            play_button.icon = ft.Icons.PLAY_CIRCLE_FILL_ROUNDED
        else:
            if pygame.mixer.music.get_pos() == -1:
                load_song()
                pygame.mixer.music.play()
            else:
                pygame.mixer.music.unpause()
            play_button.icon = ft.Icons.PAUSE_CIRCLE_FILLED_ROUNDED
        page.update()

    def change_song(delta):
        nonlocal current_song_index
        if not playlist: return
        current_song_index = (current_song_index + delta) % len(playlist)
        load_song()
        pygame.mixer.music.play()
        play_button.icon = ft.Icons.PAUSE_CIRCLE_FILLED_ROUNDED
        page.update()

    
    visualizer_bars = []
    for i in range(15):
        visualizer_bars.append(
            ft.Container(
                width=15, height=10, bgcolor=ft.Colors.CYAN_400, border_radius=5,
                animate_size=ft.Animation(150, ft.AnimationCurve.EASE_IN_OUT), 
            )
        )
    visualizer_row = ft.Row(controls=visualizer_bars, alignment="center", vertical_alignment="end", height=100)

    
    async def update_ui_loop():
        while True:
            if pygame.mixer.music.get_busy():
                current_time = pygame.mixer.music.get_pos() / 1000
                if playlist:
                    total_dur = playlist[current_song_index].duration
                    progress_bar.value = current_time / total_dur if total_dur > 0 else 0
                current_time_text.value = format_time(current_time)
                for bar in visualizer_bars:
                    bar.height = random.randint(10, 90)
            else:
                for bar in visualizer_bars: bar.height = 10
            page.update()
            await asyncio.sleep(0.15)

    
    play_button = ft.IconButton(icon=ft.Icons.PLAY_CIRCLE_FILL_ROUNDED, icon_size=60, icon_color=ft.Colors.CYAN_ACCENT, on_click=play_pause)
    prev_button = ft.IconButton(icon=ft.Icons.SKIP_PREVIOUS_ROUNDED, icon_size=40, on_click=lambda _: change_song(-1))
    next_button = ft.IconButton(icon=ft.Icons.SKIP_NEXT_ROUNDED, icon_size=40, on_click=lambda _: change_song(1))

    main_container = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("REPRODUCIENDO", size=12, color=ft.Colors.CYAN_ACCENT, weight="bold"),
                album_art,
                visualizer_row, 
                song_info,
                ft.Row([current_time_text, progress_bar, duration_text], alignment="center"),
                ft.Row([prev_button, play_button, next_button], alignment="center"),
            ],
            horizontal_alignment="center",
        ),
        padding=30, bgcolor=ft.Colors.BLUE_GREY_900, border_radius=30,
    )

    page.add(main_container)

    if playlist:
        load_song()
        await update_ui_loop()
    else:
        song_info.value = "No hay MP3 en 'canciones'"
        page.update()

ft.run(main, assets_dir="static")