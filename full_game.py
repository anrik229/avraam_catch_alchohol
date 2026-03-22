import pygame
import sys
import random
import os
import math

# Инициализация Pygame
pygame.init()

# Получаем путь к папке со скриптом
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Инициализация звука
pygame.mixer.init()

# Настройки экрана
BASE_WIDTH = 1200
BASE_HEIGHT = 800
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Avraam Catch Alcohol")

# Коэффициенты масштабирования
SCALE = min(SCREEN_WIDTH / BASE_WIDTH, SCREEN_HEIGHT / BASE_HEIGHT)
MODEL_SCALE = 1.21

def s(value):
    return int(value * SCALE)

def sm(value):
    return int(value * SCALE * MODEL_SCALE)

WORLD_WIDTH = s(BASE_WIDTH)
WORLD_HEIGHT = s(BASE_HEIGHT)
OFFSET_X = (SCREEN_WIDTH - WORLD_WIDTH) // 2
OFFSET_Y = (SCREEN_HEIGHT - WORLD_HEIGHT) // 2

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
SKY_BLUE = (135, 206, 235)
GREEN = (100, 200, 100)
BROWN = (139, 69, 19)
RED = (255, 0, 0)
DARK_GREEN = (50, 150, 50)
DARK_RED = (150, 0, 0)
DRUNK_COLOR = (0, 200, 0)
DRUNK_COLOR_MID = (255, 200, 0)
DRUNK_COLOR_LOW = (255, 100, 0)
DRUNK_COLOR_CRITICAL = (255, 0, 0)

# Шрифты
title_font = pygame.font.Font(None, 72)
button_font = pygame.font.Font(None, 48)
font = pygame.font.Font(None, 36)
clock = pygame.time.Clock()
FPS = 60

# ==================== ЗАГРУЗКА КАРТИНОК ====================
# Музыка
music_path = None
for path in ["sprites/background_music.mp3", "sprites/menu_music.mp3"]:
    if os.path.exists(path):
        music_path = path
        print(f"✓ Музыка найдена: {path}")
        break

# Звук gameover
gameover_sound = None
if os.path.exists("sprites/gameover.mp3"):
    gameover_sound = pygame.mixer.Sound("sprites/gameover.mp3")
    gameover_sound.set_volume(0.7)
    print("✓ Звук gameover загружен")

# Анимации игрока
player_animations = {'stand': None, 'run': None, 'jump': None}

for anim in ['stand', 'run', 'jump']:
    path = os.path.join(script_dir, "sprites", f"avraam_{anim}.png")
    if os.path.exists(path):
        player_animations[anim] = pygame.image.load(path).convert_alpha()
        player_animations[anim] = pygame.transform.scale(player_animations[anim], (sm(75), sm(93)))
        print(f"✓ {anim} загружена")

# Бутылки
bottle_img = {}
bottle_names = {'jagermaster': (50, 55), 'jackdaniels': (30, 35), 'vodka': (40, 45)}
for name, size in bottle_names.items():
    path = os.path.join(script_dir, "sprites", f"{name}.png")
    if os.path.exists(path):
        bottle_img[name] = pygame.image.load(path).convert_alpha()
        bottle_img[name] = pygame.transform.scale(bottle_img[name], (sm(size[0]), sm(size[1])))

# Аспирин
aspirin_img = None
path = os.path.join(script_dir, "sprites", "aspirin.png")
if os.path.exists(path):
    aspirin_img = pygame.image.load(path).convert_alpha()
    aspirin_img = pygame.transform.scale(aspirin_img, (sm(35), sm(35)))

# Уголь
coal_img = None
path = os.path.join(script_dir, "sprites", "coal.png")
if os.path.exists(path):
    coal_img = pygame.image.load(path).convert_alpha()
    coal_img = pygame.transform.scale(coal_img, (sm(25), sm(25)))

# ==================== КЛАССЫ ====================
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = int(sm(75) * 0.9)
        self.height = int(sm(85) * 0.9)
        self.vel_x = 0
        self.vel_y = 0
        self.speed = 6 * SCALE
        self.jump_power = -20 * SCALE
        self.gravity = 0.8 * SCALE
        self.on_ground = False
        self.animation_state = 'stand'
        self.drop_through = False
        
    def get_animation(self):
        if not self.on_ground:
            return 'jump'
        elif abs(self.vel_x) > 0.5:
            return 'run'
        return 'stand'
    
    def move(self, keys):
        if keys[pygame.K_LEFT]:
            self.vel_x = -self.speed
        elif keys[pygame.K_RIGHT]:
            self.vel_x = self.speed
        else:
            self.vel_x = 0
            
        self.drop_through = keys[pygame.K_DOWN]
        
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vel_y = self.jump_power
            self.on_ground = False
    
    def update(self, platforms):
        new_state = self.get_animation()
        if new_state != self.animation_state:
            self.animation_state = new_state
        
        old_hitbox = self.get_rect()
        
        # Горизонтальное движение
        self.x += self.vel_x
        hitbox = self.get_rect()
        for plat in platforms:
            if hitbox.colliderect(plat.rect):
                if self.vel_x > 0 and old_hitbox.right <= plat.rect.left:
                    self.x += plat.rect.left - hitbox.right
                    self.vel_x = 0
                elif self.vel_x < 0 and old_hitbox.left >= plat.rect.right:
                    self.x += plat.rect.right - hitbox.left
                    self.vel_x = 0
                hitbox = self.get_rect()
        
        # Вертикальное движение
        self.vel_y += self.gravity
        self.y += self.vel_y
        self.on_ground = False
        hitbox = self.get_rect()
        
        for plat in platforms:
            if hitbox.colliderect(plat.rect):
                if self.drop_through and self.vel_y > 0:
                    continue
                
                if self.vel_y > 0 and old_hitbox.bottom <= plat.rect.top:
                    self.y += plat.rect.top - hitbox.bottom
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0 and old_hitbox.top >= plat.rect.bottom:
                    self.y += plat.rect.bottom - hitbox.top
                    self.vel_y = 0
                hitbox = self.get_rect()
        
        # Границы
        if self.x < 0:
            self.x = 0
        if self.x + self.width > WORLD_WIDTH:
            self.x = WORLD_WIDTH - self.width
    
    def draw(self, screen):
        sx = self.x + OFFSET_X
        sy = self.y + OFFSET_Y
        current_image = player_animations.get(self.animation_state)
        
        if current_image:
            img = pygame.transform.scale(current_image, (self.width, self.height))
            if self.vel_x < 0:
                img = pygame.transform.flip(img, True, False)
            if self.drop_through:
                img.set_alpha(128)
            screen.blit(img, (sx, sy))
    
    def get_rect(self):
        hitbox_width = int(self.width * 0.75)
        hitbox_x = self.x + (self.width - hitbox_width) / 2
        return pygame.Rect(hitbox_x, self.y, hitbox_width, self.height)

class Platform:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        
    def draw(self, screen):
        x = self.rect.x + OFFSET_X
        y = self.rect.y + OFFSET_Y
        pygame.draw.rect(screen, BROWN, (x, y, self.rect.width, self.rect.height))
        for i in range(0, self.rect.width, s(20)):
            pygame.draw.line(screen, BLACK, (x + i, y), (x + i, y + self.rect.height), s(2))
        for i in range(0, self.rect.height, s(15)):
            pygame.draw.line(screen, BLACK, (x, y + i), (x + self.rect.width, y + i), s(1))

class Bottle:
    def __init__(self, x, y, sx, sy, typ):
        self.x, self.y, self.sx, self.sy = x, y, sx, sy
        self.type = typ
        self.w, self.h = sm(20), sm(15)
        self.angle, self.rs = 0, random.randint(3, 10)
        
    def update(self):
        self.x += self.sx
        self.y += self.sy
        self.angle += self.rs
        
    def draw(self, screen):
        sx, sy = self.x + OFFSET_X, self.y + OFFSET_Y
        img = None
        if self.type == 1:
            img = bottle_img.get('jagermaster')
        elif self.type == 2:
            img = bottle_img.get('jackdaniels')
        elif self.type == 3:
            img = bottle_img.get('vodka')
        
        if img:
            rot = pygame.transform.rotate(img, self.angle)
            rect = rot.get_rect(center=(sx + self.w//2, sy + self.h//2))
            screen.blit(rot, rect)
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)

class Bonus:
    def __init__(self, x, y, sx, sy, typ):
        self.x, self.y, self.sx, self.sy = x, y, sx, sy
        self.type = typ
        self.w, self.h = sm(25), sm(25)
        self.angle, self.rs = 0, random.randint(2, 5)
        
    def update(self):
        self.x += self.sx
        self.y += self.sy
        self.angle += self.rs
        
    def draw(self, screen):
        sx, sy = self.x + OFFSET_X, self.y + OFFSET_Y
        if self.type == 1 and aspirin_img:
            rot = pygame.transform.rotate(aspirin_img, self.angle)
            rect = rot.get_rect(center=(sx + self.w//2, sy + self.h//2))
            screen.blit(rot, rect)
        elif self.type == 2 and coal_img:
            rot = pygame.transform.rotate(coal_img, self.angle)
            rect = rot.get_rect(center=(sx + self.w//2, sy + self.h//2))
            screen.blit(rot, rect)
        
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)

class MenuBottle:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = -50
        self.sy = random.uniform(1, 3)
        self.sx = random.uniform(-1, 1)
        self.angle = 0
        self.rs = random.uniform(2, 6)
        images = [v for v in bottle_img.values() if v]
        self.img = random.choice(images) if images else None
        
    def update(self):
        self.y += self.sy
        self.x += self.sx
        self.angle += self.rs
        
    def draw(self, screen):
        if self.img:
            rot = pygame.transform.rotate(self.img, self.angle)
            rect = rot.get_rect(center=(self.x, self.y))
            screen.blit(rot, rect)
    
    def is_off(self):
        return self.y > SCREEN_HEIGHT + 50

class Button:
    def __init__(self, x, y, w, h, text, color, hover, action):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color, self.hover, self.action = color, hover, action
        self.hovered = False
        
    def draw(self, screen):
        color = self.hover if self.hovered else self.color
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 3)
        surf = button_font.render(self.text, True, WHITE)
        screen.blit(surf, surf.get_rect(center=self.rect.center))
        
    def handle(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.hovered and self.action:
                return self.action()
        return None

# ==================== ПЛАТФОРМЫ ====================
platforms = [
    Platform(s(300), s(615), s(600), sm(30)),
    Platform(s(300), s(267), s(600), sm(30)),
    Platform(s(75), s(440), s(225), sm(30)),
    Platform(s(900), s(440), s(225), sm(30))
]

def get_player_spawn():
    p = platforms[0]
    return p.rect.x + (p.rect.width - sm(75)) // 2, p.rect.y - sm(85) - s(10)

# ==================== ИГРА ====================
def run_game():
    # Сброс всех переменных
    player = Player(*get_player_spawn())
    bottles = []
    bonuses = []
    collected = 0
    drunk = 50
    start = pygame.time.get_ticks()
    bottle_timer = 0
    bonus_timer = 0
    spawn_delay = 2000
    spawn_bonus_delay = 3000
    game_over = False
    reason = ""
    show_rules = True
    drunk_timer = 0
    
    # Запускаем музыку
    if music_path:
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(0.4)
        pygame.mixer.music.play(-1)
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.mixer.music.stop()
                    return "menu"
                if event.key == pygame.K_SPACE and game_over:
                    # Перезапуск - возвращаем restart, который перезапустит функцию
                    return "restart"
        
        if not game_over:
            now = pygame.time.get_ticks()
            
            if show_rules and now - start > 5000:
                show_rules = False
            
            game_time = 0 if show_rules else now - start
            diff = 1.0 + min(game_time / 30000.0, 3.0)
            cur_spawn = max(300, int(spawn_delay / diff))
            cur_bonus = max(400, int(spawn_bonus_delay / diff))
            
            # Спавн бутылок
            if not show_rules and now - bottle_timer > cur_spawn:
                bottle_timer = now
                side = random.randint(0, 3)
                if side == 0:
                    x, y = random.randint(0, WORLD_WIDTH - s(50)), -s(55)
                elif side == 1:
                    x, y = random.randint(0, WORLD_WIDTH - s(50)), WORLD_HEIGHT + s(55)
                elif side == 2:
                    x, y = -s(50), random.randint(0, WORLD_HEIGHT - s(55))
                else:
                    x, y = WORLD_WIDTH + s(50), random.randint(0, WORLD_HEIGHT - s(55))
                
                tx = WORLD_WIDTH // 2 + random.randint(-s(300), s(300))
                ty = WORLD_HEIGHT // 2 + random.randint(-s(200), s(200))
                dx, dy = tx - (x + s(25)), ty - (y + s(27.5))
                length = math.hypot(dx, dy)
                if length > 0:
                    dx /= length
                    dy /= length
                sp = random.randint(5, 8)
                bottles.append(Bottle(x, y, dx * sp, dy * sp, random.randint(1, 3)))
            
            # Спавн бонусов
            if not show_rules and now - bonus_timer > cur_bonus:
                bonus_timer = now
                side = random.randint(0, 3)
                if side == 0:
                    x, y = random.randint(0, WORLD_WIDTH - s(25)), -s(25)
                elif side == 1:
                    x, y = random.randint(0, WORLD_WIDTH - s(25)), WORLD_HEIGHT + s(25)
                elif side == 2:
                    x, y = -s(25), random.randint(0, WORLD_HEIGHT - s(25))
                else:
                    x, y = WORLD_WIDTH + s(25), random.randint(0, WORLD_HEIGHT - s(25))
                
                tx = player.x + player.width // 2
                ty = player.y + player.height // 2
                dx, dy = tx - (x + s(12.5)), ty - (y + s(12.5))
                length = math.hypot(dx, dy)
                if length > 0:
                    dx /= length
                    dy /= length
                sp = random.randint(9, 12)
                bonuses.append(Bonus(x, y, dx * sp, dy * sp, random.randint(1, 2)))
            
            # Обновление бутылок
            for b in bottles[:]:
                b.update()
                if b.y > WORLD_HEIGHT + s(100) or b.y < -s(100) or b.x > WORLD_WIDTH + s(100) or b.x < -s(100):
                    bottles.remove(b)
                    continue
                if player.get_rect().colliderect(b.get_rect()):
                    collected += 1
                    drunk = min(50, drunk + 4)
                    bottles.remove(b)
            
            # Обновление бонусов
            for b in bonuses[:]:
                b.update()
                if b.y > WORLD_HEIGHT + s(100) or b.y < -s(100) or b.x > WORLD_WIDTH + s(100) or b.x < -s(100):
                    bonuses.remove(b)
                    continue
                if player.get_rect().colliderect(b.get_rect()):
                    if b.type == 1:
                        drunk = max(0, drunk - 7)
                    else:
                        drunk = max(0, drunk - 5)
                    bonuses.remove(b)
            
            # Уменьшение опьянения
            if not show_rules and now - drunk_timer > 700:
                drunk_timer = now
                drunk -= 1
                if drunk <= 0:
                    game_over = True
                    reason = "sober"
                    pygame.mixer.music.stop()
                    if gameover_sound:
                        gameover_sound.play()
            
            # Движение игрока
            keys = pygame.key.get_pressed()
            player.move(keys)
            player.update(platforms)
            
            # Проверка падения
            if player.y + player.height > WORLD_HEIGHT:
                game_over = True
                reason = "fall"
                pygame.mixer.music.stop()
                if gameover_sound:
                    gameover_sound.play()
        
        # Отрисовка игры
        screen.fill(SKY_BLUE)
        pygame.draw.rect(screen, GREEN, (0, OFFSET_Y + WORLD_HEIGHT - s(65), SCREEN_WIDTH, s(65)))
        
        for p in platforms:
            p.draw(screen)
        for b in bottles:
            b.draw(screen)
        for b in bonuses:
            b.draw(screen)
        player.draw(screen)
        
        # Правила
        if show_rules and not game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill(BLACK)
            screen.blit(overlay, (0, 0))
            title = font.render("АВРААМ БУХОЙ!", True, WHITE)
            screen.blit(title, title.get_rect(center=(OFFSET_X + WORLD_WIDTH//2, OFFSET_Y + s(100))))
            rules = ["не дай ему протрезветь!", "Лови бутылки!", "Уворачивайся от таблеток!", "Не упади в кусты!"]
            y = OFFSET_Y + s(180)
            small_font = pygame.font.Font(None, s(28))
            for r in rules:
                t = small_font.render(r, True, WHITE)
                screen.blit(t, t.get_rect(center=(OFFSET_X + WORLD_WIDTH//2, y)))
                y += s(50)
        
        # Интерфейс
        if not game_over:
            t = font.render(f"Время: {game_time//1000} сек", True, BLACK)
            screen.blit(t, (OFFSET_X + s(10), OFFSET_Y + s(10)))
            t = font.render(f"Собрано: {collected}", True, BLACK)
            screen.blit(t, (OFFSET_X + s(10), OFFSET_Y + s(40)))
            
            if drunk > 35: bc = DRUNK_COLOR
            elif drunk > 20: bc = DRUNK_COLOR_MID
            elif drunk > 10: bc = DRUNK_COLOR_LOW
            else: bc = DRUNK_COLOR_CRITICAL
            bar_w = s(200)
            pygame.draw.rect(screen, (100,100,100), (OFFSET_X + s(10), OFFSET_Y + s(85), bar_w, s(20)))
            pygame.draw.rect(screen, bc, (OFFSET_X + s(10), OFFSET_Y + s(85), int(bar_w * drunk / 50), s(20)))
            pygame.draw.rect(screen, BLACK, (OFFSET_X + s(10), OFFSET_Y + s(85), bar_w, s(20)), s(2))
            t = font.render(f"Опьянение: {drunk}/50", True, BLACK)
            screen.blit(t, (OFFSET_X + s(10), OFFSET_Y + s(65)))
        
        # Game Over
        if game_over:
            text = "Авраам протрезвел! Пробел = заново" if reason == "sober" else "Авраам упал! Пробел = заново"
            t = font.render(text, True, BLACK)
            screen.blit(t, t.get_rect(center=(OFFSET_X + WORLD_WIDTH//2, OFFSET_Y + WORLD_HEIGHT//2)))
        
        pygame.display.flip()
        clock.tick(FPS)

# ==================== МЕНЮ ====================
def run_menu():
    menu_bottles = [MenuBottle() for _ in range(30)]
    
    def start_action():
        return "start"
    def exit_action():
        return "exit"
    
    start_btn = Button(SCREEN_WIDTH//2 - 125, SCREEN_HEIGHT//2 + 50, 250, 60, "СТАРТ", DARK_GREEN, GREEN, start_action)
    exit_btn = Button(SCREEN_WIDTH//2 - 125, SCREEN_HEIGHT//2 + 130, 250, 60, "ВЫХОД", DARK_RED, RED, exit_action)
    
    # Музыка для меню
    if music_path:
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(0.4)
        pygame.mixer.music.play(-1)
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            result = start_btn.handle(event)
            if result:
                return result
            result = exit_btn.handle(event)
            if result:
                return result
        
        screen.fill(BLACK)
        for b in menu_bottles[:]:
            b.update()
            b.draw(screen)
            if b.is_off():
                menu_bottles.remove(b)
                menu_bottles.append(MenuBottle())
        
        title = title_font.render("CATCH ALCOHOL", True, WHITE)
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 80)))
        sub = font.render("Avraam vs Alcohol", True, GRAY)
        screen.blit(sub, sub.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 20)))
        start_btn.draw(screen)
        exit_btn.draw(screen)
        credit = pygame.font.Font(None, 20).render("made by: anr1k", True, GRAY)
        screen.blit(credit, (SCREEN_WIDTH - 110, SCREEN_HEIGHT - 30))
        
        pygame.display.flip()
        clock.tick(FPS)

# ==================== ГЛАВНЫЙ ЦИКЛ ====================
while True:
    result = run_menu()
    if result == "quit":
        pygame.quit()
        sys.exit()
    elif result == "start":
        while True:
            game_result = run_game()
            if game_result == "quit":
                pygame.quit()
                sys.exit()
            elif game_result == "menu":
                break
            elif game_result == "restart":
                continue
    elif result == "exit":
        pygame.quit()
        sys.exit()