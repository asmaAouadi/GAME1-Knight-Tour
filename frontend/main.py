import pygame
import sys
from backend.algorithmes import genetic_algorithm
from enum import Enum
import threading
import time
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # frontend/
ASSETS_DIR = os.path.join(BASE_DIR, "Assets")

background_path = os.path.join(ASSETS_DIR, "background.png")
pause_path = os.path.join(ASSETS_DIR, "pause.png")
play_path = os.path.join(ASSETS_DIR , "play.png")
start1_path = os.path.join(ASSETS_DIR , "start1.png")
start2_path = os.path.join(ASSETS_DIR , "start2.png")
knight_path = os.path.join(ASSETS_DIR, "knight.png")  # Add your knight PNG file

# Constants
WINDOW_WIDTH = 700
WINDOW_HEIGHT = 550
FPS = 60

# Color Scheme
BLACK = (0, 0, 0)
DARK_GRAY = (40, 40, 40)
GRAY = (120, 120, 120)
WHITE = (200, 200, 200)
LIGHT_GRAY = (180, 180, 180)
DARK_TEXT = (80, 80, 80)
ACCENT = (100, 150, 200)

class GameState(Enum):
    MENU = 1
    TRANSITION = 2
    GAME = 3

class Button:
    def __init__(self, x, y, width, height, image_path):
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (width, height))
        self.hovered = False

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

    def update(self, pos):
        self.hovered = self.rect.collidepoint(pos)


class ChessBoard:
    def __init__(self, x, y, cell_size):
        self.x = x
        self.y = y
        self.cell_size = cell_size
        self.squares = {}
        self.knight_pos = None
        self.current_step = 0
        self.is_animating = False
        self.animation_delay = 0.3
        self.visited_positions = set()
        
        # Load knight image
        try:
            self.knight_image = pygame.image.load(knight_path).convert_alpha()
            # Scale knight image to fit cell size
            knight_size = int(cell_size * 0.8)  # 80% of cell size
            self.knight_image = pygame.transform.scale(self.knight_image, (knight_size, knight_size))
        except:
            print(f"Could not load knight image from {knight_path}")
            self.knight_image = None

        # Create square dict: (row, col) -> position mapping
        for row in range(8):
            for col in range(8):
                px = x + col * cell_size
                py = y + row * cell_size
                self.squares[(row, col)] = (px, py)

    def draw(self, surface, path, current_step):
        # Draw board with gray and white squares
        for row in range(8):
            for col in range(8):
                px, py = self.squares[(row, col)]
                color = WHITE if (row + col) % 2 == 0 else GRAY
                pygame.draw.rect(surface, color, (px, py, self.cell_size, self.cell_size))

                # Draw step numbers only for visited positions (up to current_step)
                if path and (row, col) in path[:current_step + 1]:
                    step_num = path.index((row, col)) + 1
                    font = pygame.font.Font(None, 24)
                    text = font.render(str(step_num), True, BLACK)
                    text_rect = text.get_rect(center=(px + self.cell_size // 2, py + self.cell_size // 2))
                    surface.blit(text, text_rect)

                # Draw border
                pygame.draw.rect(surface, DARK_GRAY, (px, py, self.cell_size, self.cell_size), 2)

        # Draw knight using PNG image
        if self.knight_pos:
            px, py = self.squares[self.knight_pos]
            if self.knight_image:
                # Center the knight image in the cell
                knight_x = px + (self.cell_size - self.knight_image.get_width()) // 2
                knight_y = py + (self.cell_size - self.knight_image.get_height()) // 2
                surface.blit(self.knight_image, (knight_x, knight_y))
            else:
                # Fallback to circle if image not available
                pygame.draw.circle(surface, ACCENT, (px + self.cell_size // 2, py + self.cell_size // 2), 15)
                font = pygame.font.Font(None, 24)
                text = font.render("♞", True, WHITE)
                text_rect = text.get_rect(center=(px + self.cell_size // 2, py + self.cell_size // 2))
                surface.blit(text, text_rect)

    def update_position(self, path, current_index):
        if path and 0 <= current_index < len(path):
            self.knight_pos = path[current_index]


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Knight's Tour - Genetic Algorithm")
        self.clock = pygame.time.Clock()
        self.running = True

        self.state = GameState.MENU
        self.transition_alpha = 0
        self.transition_speed = 5
        self.transition_frames = 20
        self.transition_counter = 0
        self.algorithm_started = False

        # Menu elements
        self.start_button = None
        self.button_rect = None
        self.base_button = None
        self.button_hover = None
        self.button_pressed = None
        self.load_start_button()

        # Game elements
        self.board = ChessBoard(150, 50, 40)
        self.path = None
        self.generation = 0
        self.current_step = 0
        self.is_playing = False
        self.last_frame_time = 0
        self.animation_speed = 0.2
        self.execution_time = 0  # Store execution time

        # Position buttons under the board
        self.play_button = Button(250, 400, 60, 60, play_path)
        self.pause_button = Button(320, 400, 60, 60, pause_path)

        # Threading for algorithm
        self.algorithm_thread = None
        self.algorithm_running = False
        self.algorithm_result = None

    def load_start_button(self):
        """Load start button with hover and pressed states"""
        try:
            self.base_button = pygame.image.load(start2_path).convert_alpha()
            self.base_button = pygame.transform.scale(self.base_button, (250, 60))

            self.button_hover = self.base_button.copy()
            hover_overlay = pygame.Surface(self.button_hover.get_size(), pygame.SRCALPHA)
            hover_overlay.fill((255, 255, 255, 40))
            self.button_hover.blit(hover_overlay, (0, 0))

            self.button_pressed = self.base_button.copy()
            pressed_overlay = pygame.Surface(self.button_pressed.get_size(), pygame.SRCALPHA)
            pressed_overlay.fill((0, 0, 0, 70))
            self.button_pressed.blit(pressed_overlay, (0, 0))
            
            self.button_rect = self.base_button.get_rect(center=(WINDOW_WIDTH // 2, 450))
            self.start_button = Button(self.button_rect.x, self.button_rect.y, 
                                      self.button_rect.width, self.button_rect.height, start2_path)
        except Exception as e:
            print("Could not load start_button2.png:", e)
            self.base_button = self.button_hover = self.button_pressed = None
            self.button_rect = None
            # Fallback to original button
            self.start_button = Button(225, 423, 250, 60, start1_path)

    def run_algorithm(self):
        """Run genetic algorithm in background"""
        self.algorithm_running = True
        try:
            result = genetic_algorithm(50)
            if isinstance(result, tuple) and len(result) == 2:
                self.path, exec_time = result
                self.execution_time = exec_time  # Store execution time
                self.generation = 0
                print(f"Solution found! Execution time: {exec_time:.2f} seconds")
                self.algorithm_result = (self.path, exec_time)
            else:
                print(f"Unexpected result format from genetic_algorithm: {result}")
                self.algorithm_result = None
        except Exception as e:
            print(f"Error running algorithm: {e}")
            self.algorithm_result = None
        finally:
            self.algorithm_running = False

    def handle_menu_input(self, pos):
        if self.start_button.is_clicked(pos) and not self.algorithm_started:
            self.algorithm_started = True
            self.state = GameState.TRANSITION
            self.transition_counter = 0
            # Start algorithm in background
            self.algorithm_thread = threading.Thread(target=self.run_algorithm, daemon=True)
            self.algorithm_thread.start()

    def handle_game_input(self, pos):
        if self.play_button.is_clicked(pos):
            self.is_playing = True
        if self.pause_button.is_clicked(pos):
            self.is_playing = False

    def draw_menu(self):
        # Black background
        self.screen.fill(BLACK)
        
        # Draw background image if available
        try:
            bg = pygame.image.load(background_path).convert()
            bg = pygame.transform.scale(bg, (WINDOW_WIDTH, WINDOW_HEIGHT))
            self.screen.blit(bg, (0, 0))
        except:
            pass

        # Title with dark gray text
        font_title = pygame.font.Font(None, 72)
        title = font_title.render("", True, DARK_TEXT)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)

        # Draw start button with hover effect
        mouse_pos = pygame.mouse.get_pos()
        self.start_button.update(mouse_pos)
        
        if self.base_button and self.button_rect:
            if self.start_button.hovered:
                self.screen.blit(self.button_hover, self.button_rect)
            else:
                self.screen.blit(self.base_button, self.button_rect)
        else:
            self.start_button.draw(self.screen)

    def draw_transition(self):
        # Transition animation
        if self.transition_counter < self.transition_frames:
            # Draw menu background
            self.screen.fill(BLACK)
            try:
                bg = pygame.image.load(background_path).convert()
                bg = pygame.transform.scale(bg, (WINDOW_WIDTH, WINDOW_HEIGHT))
                self.screen.blit(bg, (0, 0))
            except:
                pass
            
            # Draw scaling button
            if self.base_button and self.button_rect:
                scale = 1.0 + 0.04 * (self.transition_counter + 1)
                new_w = max(1, int(self.base_button.get_width() * scale))
                new_h = max(1, int(self.base_button.get_height() * scale))
                scaled = pygame.transform.smoothscale(self.base_button, (new_w, new_h))
                scaled_rect = scaled.get_rect(center=self.button_rect.center)
                self.screen.blit(scaled, scaled_rect)
            
            # Draw fading overlay
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            overlay_alpha = int(255 * (self.transition_counter + 1) / self.transition_frames)
            overlay.set_alpha(overlay_alpha)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))
            
            self.transition_counter += 1
        else:
            # Transition complete - show loading until algorithm finishes
            if not self.algorithm_running and self.algorithm_result is not None:
                # Algorithm finished successfully
                self.path, exec_time = self.algorithm_result
                self.execution_time = exec_time
                self.state = GameState.GAME
                self.current_step = 0  # Start at position 0 (no movement yet)
                self.is_playing = False  # Don't start moving until play button is clicked
                # Set initial knight position
                if self.path:
                    self.board.update_position(self.path, 0)
            else:
                # Still computing, show loading message
                self.screen.fill(BLACK)
                
                # Draw loading text with dark gray color
                font_large = pygame.font.Font(None, 48)
                font_small = pygame.font.Font(None, 24)
                
                loading_text = font_large.render("Working on it...", True, DARK_TEXT)
                loading_rect = loading_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 30))
                self.screen.blit(loading_text, loading_rect)
                
                info_text = font_small.render("Finding the optimal Knight's Tour path", True, DARK_TEXT)
                info_rect = info_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 20))
                self.screen.blit(info_text, info_rect)
                
                # Animated dots
                dots = "." * ((pygame.time.get_ticks() // 500) % 4)
                dots_text = font_small.render(dots, True, DARK_TEXT)
                dots_rect = dots_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
                self.screen.blit(dots_text, dots_rect)

    def draw_game(self):
        # Black background
        self.screen.fill(BLACK)

        # Draw board with current step to show numbers only for visited positions
        self.board.draw(self.screen, self.path, self.current_step)

        # Draw sidebar info with dark gray text
        info_x = 500
        font_title = pygame.font.Font(None, 32)
        font_text = pygame.font.Font(None, 24)

        # Title
        title = font_title.render("INFO", True, DARK_TEXT)
        self.screen.blit(title, (info_x, 50))

        # Moves
        moves_count = self.current_step + 1 if self.path else 0
        total_moves = len(self.path) if self.path else 0
        moves_text = font_text.render(f"Moves: {moves_count}/{total_moves}", True, DARK_TEXT)
        self.screen.blit(moves_text, (info_x, 120))

        # Status
        status = "Complete!" if moves_count == total_moves and total_moves > 0 else "Ready" if not self.is_playing else "In Progress"
        status_text = font_text.render(f"Status: {status}", True, DARK_TEXT)
        self.screen.blit(status_text, (info_x, 160))

        # Execution Time
        if self.execution_time > 0:
            time_text = font_text.render(f"Solution Time: {self.execution_time:.2f}s", True, DARK_TEXT)
            self.screen.blit(time_text, (info_x, 200))

        # Instructions
        if not self.is_playing and self.current_step == 0 and self.path:
            instruction_text = font_text.render("Click PLAY to start", True, DARK_TEXT)
            self.screen.blit(instruction_text, (info_x, 250))

        # Draw buttons under the board
        self.play_button.update(pygame.mouse.get_pos())
        self.pause_button.update(pygame.mouse.get_pos())
        self.play_button.draw(self.screen)
        self.pause_button.draw(self.screen)

        # Draw button labels with dark gray text
        font_small = pygame.font.Font(None, 16)
        play_label = font_small.render("PLAY", True, DARK_TEXT)
        pause_label = font_small.render("PAUSE", True, DARK_TEXT)
        self.screen.blit(play_label, (self.play_button.rect.x + 15, self.play_button.rect.y + 65))
        self.screen.blit(pause_label, (self.pause_button.rect.x + 10, self.pause_button.rect.y + 65))

    def update(self):
        if self.state == GameState.MENU:
            pass
        elif self.state == GameState.TRANSITION:
            pass
        elif self.state == GameState.GAME:
            if self.is_playing and self.path:
                current_time = time.time()
                if current_time - self.last_frame_time > self.animation_speed:
                    if self.current_step < len(self.path) - 1:
                        self.current_step += 1
                    else:
                        self.is_playing = False
                    self.last_frame_time = current_time

                self.board.update_position(self.path, self.current_step)

    def draw(self):
        if self.state == GameState.MENU:
            self.draw_menu()
        elif self.state == GameState.TRANSITION:
            self.draw_transition()
        elif self.state == GameState.GAME:
            self.draw_game()

        pygame.display.flip()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == GameState.MENU:
                    self.handle_menu_input(event.pos)
                elif self.state == GameState.GAME:
                    self.handle_game_input(event.pos)

    def main_loop(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.main_loop()