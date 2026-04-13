import tkinter as tk
from tkinter import messagebox
import pygame
import sys
import random
import math
import time
import os

# --- Constants ---
PLAYER_LIVES = 3
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
ENEMY_WIDTH = 30
ENEMY_HEIGHT = 30
PLAYER_WIDTH = 30
PLAYER_HEIGHT = 30
HIGH_SCORE_FILE = "high_score.txt"

# --- Enemy types ---
BEE = {"color": (255, 255, 0), "points": 30, "can_shoot": False, "health": 1}
BUTTERFLY = {"color": (0, 0, 255), "points": 40, "can_shoot": True, "health": 2}
BOSS = {"color": (128, 0, 128), "points": 50, "can_shoot": True, "health": 10}
RED = {"color": (255, 0, 0), "points": 60, "can_shoot": True, "health": 3}
PHANTOM = {"color": (180, 0, 180), "points": 80, "can_shoot": False, "health": 2}  # New enemy

# --- Power-ups ---
POWERUPS = {
    "shield": {"color": (0, 255, 255), "duration": 5000},
    "rapid_fire": {"color": (255, 140, 0), "duration": 7000},
    "spread_shot": {"color": (0, 255, 0), "duration": 7000},
}

# --- High score functions ---
def load_high_score():
    if os.path.exists(HIGH_SCORE_FILE):
        with open(HIGH_SCORE_FILE, "r") as f:
            try:
                return int(f.read())
            except:
                return 0
    return 0

def save_high_score(score):
    with open(HIGH_SCORE_FILE, "w") as f:
        f.write(str(score))

class Enemy:
    def __init__(self, start_x, start_y, target_x, target_y, enemy_type):
        self.rect = pygame.Rect(start_x, start_y, ENEMY_WIDTH, ENEMY_HEIGHT)
        self.color = enemy_type["color"]
        self.points = enemy_type["points"]
        self.can_shoot = enemy_type["can_shoot"]
        self.type = enemy_type
        self.health = enemy_type["health"]
        self.in_formation = False
        self.returning = False
        self.looping = False
        self.hit_once = False  # For phantom enemy special mechanic
        self.path = self.generate_entry_path((start_x, start_y), (target_x, target_y))
        self.path_index = 0
        self.original_pos = (target_x, target_y)
        self.target_pos = (target_x, target_y)

    def generate_entry_path(self, start, end):
        control1 = (random.randint(50, SCREEN_WIDTH - 50), random.randint(100, 250))
        control2 = (random.randint(50, SCREEN_WIDTH - 50), random.randint(250, 400))
        steps = 100
        path = []
        for t in range(steps + 1):
            t /= steps
            x = (
                (1 - t) ** 3 * start[0]
                + 3 * (1 - t) ** 2 * t * control1[0]
                + 3 * (1 - t) * t ** 2 * control2[0]
                + t ** 3 * end[0]
            )
            y = (
                (1 - t) ** 3 * start[1]
                + 3 * (1 - t) ** 2 * t * control1[1]
                + 3 * (1 - t) * t ** 2 * control2[1]
                + t ** 3 * end[1]
            )
            path.append((x, y))
        return path

    def update_entry(self):
        if self.path_index < len(self.path):
            self.rect.x, self.rect.y = map(int, self.path[self.path_index])
            self.path_index += 1
        else:
            self.in_formation = True
            self.rect.x, self.rect.y = self.original_pos

    def start_dive(self, player_x, player_y):
        self.returning = False
        self.looping = False
        # Phantom teleport mechanic: skips dive, teleports back when hit once
        if self.type == PHANTOM and self.hit_once:
            self.return_to_formation()
            return

        if self.type == BUTTERFLY:
            offset_x = random.choice([-150, 150])
            dive_target = (player_x + offset_x, SCREEN_HEIGHT + 100)
        else:
            dive_target = (player_x, SCREEN_HEIGHT + 100)
        self.path = self.generate_entry_path((self.rect.x, self.rect.y), dive_target)
        self.path_index = 0
        self.in_formation = False

    def loop_from_bottom(self):
        self.looping = True
        start = (self.rect.x, -100)
        self.path = self.generate_entry_path((self.rect.x, SCREEN_HEIGHT + 50), start)
        self.path_index = 0

    def return_to_formation(self):
        self.returning = True
        start = (random.randint(0, SCREEN_WIDTH), -100)
        self.path = self.generate_entry_path(start, self.original_pos)
        self.path_index = 0

    def update_dive(self):
        if self.path_index < len(self.path):
            self.rect.x, self.rect.y = map(int, self.path[self.path_index])
            self.path_index += 1
        else:
            if self.looping:
                self.return_to_formation()
                self.looping = False
            elif not self.returning and self.rect.bottom >= SCREEN_HEIGHT:
                self.loop_from_bottom()
            elif self.returning:
                self.in_formation = True
                self.returning = False
                self.rect.x, self.rect.y = self.original_pos

class PowerUp:
    def __init__(self, x, y, kind):
        self.rect = pygame.Rect(x, y, 20, 20)
        self.kind = kind
        self.color = POWERUPS[kind]["color"]
        self.duration = POWERUPS[kind]["duration"]
        self.speed = 3

    def update(self):
        self.rect.y += self.speed

def create_wave(round_count):
    enemies = []
    start_y = 80
    rows = 5
    cols = 6

    x_spacing = ENEMY_WIDTH + 20
    y_spacing = ENEMY_HEIGHT + 20
    formation_width = cols * x_spacing - 20
    left_offset = (SCREEN_WIDTH - formation_width) // 2

    base_health = 1 + (round_count - 1)  # Increase enemy health per round

    # Boss wave every 5 rounds
    boss_wave = (round_count % 5 == 0)

    for row in range(rows):
        for col in range(cols):
            x = left_offset + col * x_spacing
            y = start_y + row * y_spacing

            if boss_wave:
                enemy_type = BOSS
            else:
                if row == 0:
                    enemy_type = BOSS
                elif row == 1:
                    enemy_type = RED
                elif row == 2:
                    enemy_type = BUTTERFLY
                elif row == 3:
                    enemy_type = PHANTOM
                else:
                    enemy_type = BEE

            enemy = Enemy(random.randint(-400, SCREEN_WIDTH + 400), -100, x, y, enemy_type)
            # Increase health progressively
            if enemy_type == BOSS:
                enemy.health = enemy_type["health"] + round_count // 2
            else:
                enemy.health = 2
                enemies.append(enemy)

    return enemies

def show_game_over(score, round_count):
    # Save high score
    high_score = load_high_score()
    if score > high_score:
        save_high_score(score)
        high_score = score

    over = tk.Tk()
    over.title("Game Over")
    over.geometry("500x450")
    over.configure(bg="black")

    title = tk.Label(over, text="GAME OVER", font=("Impact", 40), fg="red", bg="black")
    title.pack(pady=30)

    score_label = tk.Label(over, text=f"Final Score: {score}\nRound Reached: {round_count}\nHigh Score: {high_score}",
                           font=("Arial", 18), fg="white", bg="black")
    score_label.pack(pady=20)

    def back_to_menu():
        over.destroy()
        show_menu()

    button = tk.Button(over, text="Return to Menu", font=("Arial", 16), bg="gray", fg="white", command=back_to_menu)
    button.pack(pady=30)

    over.mainloop()

def start_game():
    window.destroy()
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("From Beyond")

    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 30)

    black = (0, 0, 0)
    white = (255, 255, 255)

    player = pygame.Rect(SCREEN_WIDTH // 2 - PLAYER_WIDTH // 2, SCREEN_HEIGHT - 70, PLAYER_WIDTH, PLAYER_HEIGHT)
    player_speed = 5
    bullets = []
    enemy_bullets = []
    bullet_speed = 10
    enemy_bullet_speed = 6
    shoot_cooldown = 500
    enemy_shoot_interval = 2000
    last_shot_time = pygame.time.get_ticks()
    last_enemy_shoot_time = pygame.time.get_ticks()

    enemies = create_wave(1)
    formation_speed = 1.5

    lives = PLAYER_LIVES
    score = 0
    diving_enemies = []

    wave_count = 0
    round_count = 1
    max_divers = 3

    player_alive = True
    invincible = False
    invincible_start_time = 0
    enemies_returning = False
    paused = False

    pattern_state = {"direction": 1}

    powerups = []
    active_powerups = {}
    powerup_timers = {}

    # Controls text to show on screen
    
    # Helper function to activate power-ups
    def activate_powerup(kind):
        active_powerups[kind] = True
        powerup_timers[kind] = pygame.time.get_ticks()

        nonlocal invincible, shoot_cooldown
        if kind == "shield":
            invincible = True
            invincible_start_time = pygame.time.get_ticks()
        elif kind == "rapid_fire":
            shoot_cooldown = 200
        elif kind == "spread_shot":
            pass  # handled in shooting logic

    # Helper to deactivate expired power-ups
    def check_powerup_expiry():
        current_time = pygame.time.get_ticks()
        to_remove = []
        nonlocal invincible, shoot_cooldown
        for kind in active_powerups:
            elapsed = current_time - powerup_timers[kind]
            if elapsed > POWERUPS[kind]["duration"]:
                to_remove.append(kind)
        for kind in to_remove:
            del active_powerups[kind]
            del powerup_timers[kind]
            if kind == "shield":
                invincible = False
            elif kind == "rapid_fire":
                shoot_cooldown = 500

    while True:
        screen.fill(black)
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    paused = not paused
                if event.key == pygame.K_f:
                    # Toggle fullscreen
                    if screen.get_flags() & pygame.FULLSCREEN:
                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
                    else:
                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)

        if invincible and current_time - invincible_start_time >= 3000:
            # Only disable if shield not active
            if "shield" not in active_powerups:
                invincible = False

        keys = pygame.key.get_pressed()
        if player_alive and not enemies_returning and not paused:
            if keys[pygame.K_LEFT] and player.left > 0:
                player.x -= player_speed
            if keys[pygame.K_RIGHT] and player.right < SCREEN_WIDTH:
                player.x += player_speed
            if keys[pygame.K_UP] and player.top > SCREEN_HEIGHT - 200:
                player.y -= player_speed
            if keys[pygame.K_DOWN] and player.bottom < SCREEN_HEIGHT - 30:
                player.y += player_speed
            if keys[pygame.K_SPACE] and not invincible and current_time - last_shot_time >= shoot_cooldown:
                if "spread_shot" in active_powerups:
                    # Fire three bullets spread
                    bullets.append(pygame.Rect(player.centerx - 2, player.top, 5, 15))
                    bullets.append(pygame.Rect(player.centerx - 10, player.top + 5, 5, 15))
                    bullets.append(pygame.Rect(player.centerx + 6, player.top + 5, 5, 15))
                else:
                    bullet = pygame.Rect(player.centerx - 2, player.top, 5, 15)
                    bullets.append(bullet)
                last_shot_time = current_time

        # Update power-up expiry
        check_powerup_expiry()

        # Update bullets
        for bullet in bullets[:]:
            if not paused:
                bullet.y -= bullet_speed
                if bullet.bottom < 0:
                    bullets.remove(bullet)

        # Update enemy bullets
        for eb in enemy_bullets[:]:
            if not paused:
                eb.y += enemy_bullet_speed
                if eb.top > SCREEN_HEIGHT:
                    enemy_bullets.remove(eb)
                elif eb.colliderect(player) and not invincible:
                    lives -= 1
                    player_alive = False
                    bullets.clear()
                    diving_enemies.clear()
                    enemy_bullets.clear()
                    powerups.clear()
                    active_powerups.clear()
                    if lives > 0:
                        player.x = SCREEN_WIDTH // 2 - PLAYER_WIDTH // 2
                        player.y = SCREEN_HEIGHT - 70
                        player_alive = True
                        invincible = True
                        invincible_start_time = pygame.time.get_ticks()
                    else:
                        pygame.quit()
                        time.sleep(0.5)
                        show_game_over(score, round_count)
                        return
                    break

        # Diving enemy collision damage
        for diver in diving_enemies[:]:
            if diver.rect.colliderect(player) and not invincible:
                lives -= 1
                player_alive = False
                bullets.clear()
                diving_enemies.clear()
                enemy_bullets.clear()
                powerups.clear()
                active_powerups.clear()
                if lives > 0:
                    player.x = SCREEN_WIDTH // 2 - PLAYER_WIDTH // 2
                    player.y = SCREEN_HEIGHT - 70
                    player_alive = True
                    invincible = True
                    invincible_start_time = pygame.time.get_ticks()
                else:
                    pygame.quit()
                    time.sleep(0.5)
                    show_game_over(score, round_count)
                    return
                break

        # Update enemies (entry or dive)
        if not paused:
            for enemy in enemies:
                if not enemy.in_formation and not enemy.returning:
                    enemy.update_entry()
                elif enemy.returning or not enemy.in_formation:
                    enemy.update_dive()

            # Move formation enemies side to side
            in_formation_enemies = [e for e in enemies if e.in_formation]
            if in_formation_enemies:
                dx = formation_speed * pattern_state["direction"]
                min_x = min(e.rect.left for e in in_formation_enemies)
                max_x = max(e.rect.right for e in in_formation_enemies)

                if min_x + dx < 0 or max_x + dx > SCREEN_WIDTH:
                    pattern_state["direction"] *= -1
                    dx = formation_speed * pattern_state["direction"]

                for e in in_formation_enemies:
                    e.rect.x += dx
                    e.original_pos = (e.rect.x, e.rect.y)

            # Enemies start diving if allowed
            if player_alive and not enemies_returning and len(diving_enemies) < max_divers:
                potential_divers = [e for e in enemies if e.in_formation and e not in diving_enemies]
                random.shuffle(potential_divers)
                needed = max_divers - len(diving_enemies)
                for diver in potential_divers[:needed]:
                    diver.start_dive(player.centerx, player.centery)
                    diving_enemies.append(diver)

            # Update diving enemies shooting and state
            for diver in diving_enemies[:]:
                # Enemy shoots randomly more frequently each round
                shoot_chance = 5 + round_count * 3  # increases per round
                if diver.can_shoot and random.randint(0, 1000) < shoot_chance:
                    bullet = pygame.Rect(diver.rect.centerx - 2, diver.rect.bottom, 5, 15)
                    enemy_bullets.append(bullet)
                if diver.path_index >= len(diver.path) and not diver.returning and not diver.looping:
                    diver.return_to_formation()
                elif diver.path_index >= len(diver.path) and diver.returning:
                    diver.in_formation = True
                    diver.returning = False
                    diving_enemies.remove(diver)

        # Bullet collision with enemies (player bullets)
        if not paused:
            for bullet in bullets[:]:
                for e in enemies[:]:
                    if bullet.colliderect(e.rect):
                        bullets.remove(bullet)
                        if e.type in [BEE, PHANTOM]:
                            # Divers die immediately (except phantom teleport mechanic)
                            if e.type == PHANTOM:
                                if e.hit_once:
                                    enemies.remove(e)
                                    score += e.points
                                    if e in diving_enemies:
                                        diving_enemies.remove(e)
                                else:
                                    e.hit_once = True
                                    e.return_to_formation()
                            else:
                                enemies.remove(e)
                                score += e.points
                                if e in diving_enemies:
                                    diving_enemies.remove(e)
                                # Chance to drop power-up
                                if random.random() < 0.1:
                                    kind = random.choice(list(POWERUPS.keys()))
                                    powerups.append(PowerUp(e.rect.centerx, e.rect.centery, kind))
                        else:
                            # Other enemies take 2 shots to die (except boss special rule below)
                            if e.type == BOSS:
                                e.health -= 1
                                if e.health <= 0:
                                    enemies.remove(e)
                                    score += e.points
                                    if e in diving_enemies:
                                        diving_enemies.remove(e)
                                    if random.random() < 0.2:
                                        kind = random.choice(list(POWERUPS.keys()))
                                        powerups.append(PowerUp(e.rect.centerx, e.rect.centery, kind))
                            else:
                                e.health -= 1
                                if e.health <= 0:
                                    enemies.remove(e)
                                    score += e.points
                                    if e in diving_enemies:
                                        diving_enemies.remove(e)
                                    if random.random() < 0.1:
                                        kind = random.choice(list(POWERUPS.keys()))
                                        powerups.append(PowerUp(e.rect.centerx, e.rect.centery, kind))
                        break

        # Update powerups falling and player collecting
        if not paused:
            for p in powerups[:]:
                p.update()
                if p.rect.colliderect(player):
                    activate_powerup(p.kind)
                    powerups.remove(p)
                elif p.rect.top > SCREEN_HEIGHT:
                    powerups.remove(p)

        # Check if round complete
        if not enemies and not enemies_returning:
            round_count += 1
            enemies = create_wave(round_count)
            max_divers = min(5, round_count + 2)
            diving_enemies.clear()
            player_alive = True
            invincible = True
            invincible_start_time = pygame.time.get_ticks()

        # Draw player
        if player_alive:
            if invincible:
                # Blink effect
                if (current_time // 300) % 2 == 0:
                    pygame.draw.rect(screen, (0, 255, 255), player)
            else:
                pygame.draw.rect(screen, white, player)

        # Draw bullets
        for bullet in bullets:
            pygame.draw.rect(screen, white, bullet)

        # Draw enemy bullets
        for eb in enemy_bullets:
            pygame.draw.rect(screen, (255, 0, 0), eb)

        # Draw enemies
        for e in enemies:
            pygame.draw.rect(screen, e.color, e.rect)
            if e.type == BOSS:
                # Health bar
                health_ratio = e.health / (BOSS["health"] + round_count // 2)
                pygame.draw.rect(screen, (0, 255, 0), (e.rect.x, e.rect.y - 6, ENEMY_WIDTH * health_ratio, 4))

        # Draw power-ups
        for p in powerups:
            pygame.draw.rect(screen, p.color, p.rect)

        # Draw HUD
        score_text = font.render(f"Score: {score}", True, white)
        lives_text = font.render(f"Lives: {lives}", True, white)
        round_text = font.render(f"Round: {round_count}", True, white)
        screen.blit(score_text, (10, 10))
        screen.blit(lives_text, (SCREEN_WIDTH - 120, 10))
        screen.blit(round_text, (SCREEN_WIDTH // 2 - 50, 10))

        # Draw controls text at bottom left
        
        if paused:
            pause_text = font.render("PAUSED - Press P to resume", True, white)
            screen.blit(pause_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))

        pygame.display.flip()
        clock.tick(60)

def show_menu():
    global window
    window = tk.Tk()
    window.title("From Beyond")
    window.geometry("500x450")
    window.configure(bg="black")

    title = tk.Label(window, text="FROM BEYOND", font=("Impact", 40), fg="red", bg="black")
    title.pack(pady=30)

    start_button = tk.Button(window, text="Start Game", font=("Arial", 20), bg="gray", fg="white", command=start_game)
    start_button.pack(pady=10)

    controls_button = tk.Button(window, text="Controls", font=("Arial", 20), bg="gray", fg="white",
                                command=lambda: messagebox.showinfo("Controls",
                                "Arrow keys to move\nSpace to shoot\nP to pause\nF to toggle fullscreen"))
    controls_button.pack(pady=10)

    quit_button = tk.Button(window, text="Quit", font=("Arial", 20), bg="gray", fg="white", command=window.destroy)
    quit_button.pack(pady=10)

    window.mainloop()

if __name__ == "__main__":
    show_menu()
