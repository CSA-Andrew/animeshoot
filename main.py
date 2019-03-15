# -*- coding: utf-8 -*-
import pygame
from random import randint, random, randrange, choice
pygame.init()
pygame.mixer.music.load('assets/narutosong.wav')
pygame.mixer.music.play(-1, 0.0)

# declare colors
BLUE = (0, 0, 255)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
Quit = False

pygame.init()


# button class
class Entity(pygame.sprite.Sprite):

    def __init__(self, x, y, width, height, image='assets/youtube.png'):
        pygame.sprite.Sprite.__init__(self)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.image = pygame.image.load(image)
        # This makes a rectangle around the entity, used for anything
        # from collision to moving around.
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.entity_surface = pygame.transform.smoothscale(self.image,
                                                           self.rect.size)
        self.image = pygame.transform.scale(self.image,
                                            (self.width, self.height))

    def draw(self, surface):
        surface.blit(self.entity_surface, self.rect)


class Button:
    def __init__(self, color, w, h, x, y, caption):
        self.color = color
        self.w = w
        self.h = h
        self.x = x
        self.y = y
        self.caption = caption
        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)

    def draw(self, surface):
        text = screen_font.render(self.caption, True, WHITE)
        pygame.draw.rect(surface, self.color, self.rect)
        surface.blit(text, (self.x + self.w / 2 - text.get_rect().width / 2,
                            self.y + self.h / 2 - text.get_rect().height / 2))

    def click(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos[0], mouse_pos[1])


class Text:
    def __init__(self, text, x, y, color=WHITE):
        self.text = text
        self.x = x
        self.y = y
        self.color = color

    def update(self, surface, text):
        text = screen_font.render(self.text + str(text), True, self.color)
        surface.blit(text, (self.x, self.y))


# class used for sound definition
class Sound:
    def __init__(self, sound):
        self.sound = pygame.mixer.Sound(sound)

    def play_sound(self):
        self.sound.play()


class Projectile(Entity):
    def __init__(self, x, y, width=100, height=50, image='assets/dagger.png'):
        super().__init__(x, y, width, height, image)
        self.speed = 10
        self.is_active = True

    def update(self):
        self.rect.x += self.speed

    def draw(self, surface):
        if self.is_active:
            surface.blit(self.entity_surface, self.rect)

    def kill(self):
        self.is_active = False


class HealthBar(Entity):
    def __init__(self, child_of):
        self.child_of = child_of
        self.x = child_of.rect.x
        self.y = child_of.rect.y - 50
        self.width = int(self.child_of.rect.width * 1.5)
        self.height = 20
        super().__init__(self.x, self.y, self.width, self.height)

        self.current_value = child_of.health
        self.total_value = child_of.health
        self.is_visible = True

    def update(self):
        self.rect.y = self.child_of.rect.y - 30
        self.rect.x = self.child_of.rect.x - (self.child_of.rect.width / 4)
        self.current_value = self.child_of.health

        self.rect.width = (self.current_value / self.total_value) * self.width

    def draw(self, surface):
        if self.is_visible:
            pygame.draw.rect(surface, RED, pygame.Rect(self.rect.x, self.rect.y,
                                                       self.width,
                                                       self.rect.height))
            pygame.draw.rect(surface, GREEN, self.rect)


class Asteroid(Entity):
    def __init__(self, x, y, width, height, speed, health,
                 image='assets/enemy.png', is_boss=False):
        super().__init__(x, y, width, height, image)
        self.speed = speed
        self.health = health
        self.is_active = True
        self.healthbar = HealthBar(self)
        self.is_boss = is_boss

    def update(self):
        mult = choice([40, 50, 60, 70, 80, 90, 100])
        if self.is_boss:
            self.rect.y = mult
        self.rect.x -= self.speed
        self.healthbar.update()

    def draw(self, surface):
        if self.is_active:
            self.healthbar.draw(surface)
            surface.blit(self.entity_surface, self.rect)

    def kill(self):
        self.is_active = False


class Ship(Entity):
    def __init__(self, width=130, height=150, x=0, y=0,
                 image='assets/player.png'):
        super(Ship, self).__init__(x, y, width, height, image)
        self.speed = 5
        self.move_up = False
        self.move_down = False
        self.shoot_sound = Sound('assets/shoot.wav')
        self.bullet_damage = 70

        self.projectiles = []

    def update(self, screen_width, screen_height):
        if self.move_down:
            self.rect.y += self.speed
            if self.rect.y > (screen_height - self.rect.height):
                self.rect.y = screen_height - self.rect.height
        if self.move_up:
            self.rect.y -= self.speed
            if self.rect.y < 0:
                self.rect.y = 0

        for proj in self.projectiles:
            proj.update()

    def draw(self, surface):
        surface.blit(self.entity_surface, self.rect)

    def attack(self):
        self.shoot_sound.play_sound()
        self.projectiles.append(Projectile(self.rect.x + 150,
                                           self.rect.y + (self.height / 3)))


class GameManager:
    def __init__(self, lives, levels, points_p_hit=100, points_p_loss=100):
        self.lives = lives
        self.levels = levels
        self.points_p_hit = points_p_hit
        self.points_p_loss = points_p_loss

        self.screen_width = 1200
        self.screen_height = 800
        self.current_level = 1

        self.now = 0
        self.last = 0

        self.target = 5

        self.current_score = 0

        self.level_multiplier = 1.2

        self.player = Ship()

        self.asteroids = []

        self.score_display = Text('SCORE: ', 800, 30)

        self.round_display = Text('ROUND: ', 550, 30)

        self.asteroid_spawn_counter = 1000
        self.time_tracker = 0
        self.target_time = randrange(self.asteroid_spawn_counter // 2,
                                     self.asteroid_spawn_counter)
        self.had_boss = False
        self.life_hearts = []
        for life in range(self.lives):
            self.life_hearts.append(
                Entity(height=50, width=50, y=20, x=200 + 50 * life,
                       image='assets/heart.png'))

        self.death_sound = Sound('assets/death.wav')
        self.hit_sound = Sound('assets/hit.wav')
        self.win_sound = Sound('assets/win.wav')
        self.damage_sound = Sound('assets/take_damage.wav')
        self.kill_enemy = Sound('assets/kill_enemy.wav')

    def check_collision(self):
        self.player.update(self.screen_width, self.screen_height)

        for ast in self.asteroids[:]:
            if not ast.is_active:
                self.asteroids.remove(ast)
        for proj in self.player.projectiles[:]:
            if not proj.is_active:
                self.player.projectiles.remove(proj)

        for ast in self.asteroids:
            ast.update()

            if ast.rect.colliderect(self.player.rect) and ast.is_active:
                self.take_damage()
                ast.kill()

            if ast.rect.x <= 0 and ast.is_active:
                self.current_score -= self.points_p_loss
                ast.kill()

            if ast.health <= 0 and ast.is_active:
                ast.kill()
                self.kill_enemy.play_sound()
                self.current_score += self.points_p_hit

            for proj in self.player.projectiles:
                if proj.rect.x > self.screen_width:
                    proj.kill()
                if proj.rect.colliderect(ast):
                    if proj.is_active and ast.is_active:
                        ast.health -= self.player.bullet_damage
                        self.hit_sound.play_sound()
                        proj.kill()

    def check_keys(self, k_state, key):
        self.now = pygame.time.get_ticks()
        if key == pygame.K_UP:
            self.player.move_up = k_state
        elif key == pygame.K_DOWN:
            self.player.move_down = k_state
        elif key == pygame.K_SPACE and self.now - self.last >= 200:
            self.player.attack()
            self.last = pygame.time.get_ticks()

    def take_damage(self):
        self.lives -= 1
        self.life_hearts.pop(-1)
        self.damage_sound.play_sound()

    def has_win(self):
        if self.lives == 0:
            self.death_sound.play_sound()
            return 'loss'
        elif self.current_level == self.levels and len(self.asteroids) == 0:
            if not self.had_boss:
                self.had_boss = True
                self.asteroids.append(
                    Asteroid(health=1500, width=400, height=700,
                             x=self.screen_width - 30, y=100,
                             speed=0.000000000001, is_boss=True))
                return None
            self.win_sound.play_sound()
            return 'win'
        else:
            return None

    def spawn_asteroid(self):
        self.target -= 1
        multiplier = self.current_level * self.level_multiplier
        height = (randrange(int(40 * multiplier), int(60 * multiplier)))
        y = randint(0, self.screen_height - height)
        x = screen_width

        self.asteroids.append(Asteroid(health=(70 * multiplier),
                                       speed=((random() / 1) + 0.01) * (
                                               multiplier / 1),
                                       height=height,
                                       width
                                       =(randrange(int(20 * multiplier),
                                                   int(40 * multiplier))),
                                       x=x, y=y))

    def draw_entities(self, surface):
        self.time_tracker += 1

        self.player.draw(surface)

        self.score_display.update(surface, self.current_score)

        if self.current_level > self.levels - 1:
            rnds = 'BOSS'
        else:
            rnds = str(self.current_level) + '/' + str(self.levels - 1)
        self.round_display.update(surface, rnds)

        for proj in self.player.projectiles:
            proj.draw(surface)

        for ast in self.asteroids:
            ast.draw(surface)

        for heart in self.life_hearts:
            heart.draw(surface)

        if self.time_tracker >= self.target_time:
            self.time_tracker = 0
            self.target_time = randrange(self.asteroid_spawn_counter // 2,
                                         self.asteroid_spawn_counter)
            if self.target != 0:
                self.spawn_asteroid()
        if self.target == 0:
            if len(self.asteroids) == 0:
                self.current_level += 1
                if not self.had_boss:
                    self.target = 3 * self.current_level
                self.asteroid_spawn_counter -= (10 * self.current_level *
                                                self.level_multiplier)


def write_highscore(c_score):
    file = open('assets/highscores.txt', 'a')
    file.write(str(c_score) + '\n')
    file.close()


def get_highscores():
    return [line.rstrip('\n') for line in open('assets/highscores.txt')]


# declare screen
screen_width = 1200
screen_height = 800
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('ANIVASION')
pygame.display.flip()
pygame.font.init()
screen_font = pygame.font.SysFont('Arial', 30)

# declare which buttons we will use
play_button = Button(RED, screen_width / 4, screen_height / 6,
                     (screen_width / 2) - ((screen_width / 4) / 2),
                     (screen_height / 2), 'PLAY')

play_again = Button(RED, screen_width / 4, screen_height / 6,
                    (screen_width / 2) - ((screen_width / 4) / 2),
                    (screen_height - 100), 'PLAY AGAIN')

title = u'HIGHSCORES'

start_sound = Sound('assets/start.wav')

menu_text = Text(title, 500, 70, color=BLACK)
current_screen = 'menu'
game = GameManager(5, 5)

title_image = Entity(height=screen_height, width=screen_width, x=0, y=0,
                     image='assets/splash.png')
highscores = []
while not Quit:
    screen.fill(BLACK)
    if current_screen == 'menu':
        title_image.draw(screen)
        play_button.draw(screen)
    elif current_screen == 'game':
        game.draw_entities(screen)
        game.check_collision()
        f = game.has_win()
        if f is not None:
            write_highscore(game.current_score)
            highscores = []
            current_highscores = [int(x) for x in get_highscores()]
            current_highscores.sort(reverse=True)
            current_highscores = current_highscores[:13]
            for num, score in enumerate(current_highscores):
                highscores.append(Text(str((num + 1)) + '. ' + str(score), 550,
                                       110 + (40 * (num + 1)), color=BLACK))

            if f == 'win':
                title_image = Entity(height=screen_height, width=screen_width,
                                     x=0, y=0,
                                     image='assets/win.png')
            elif f == 'loss':
                title_image = Entity(height=screen_height, width=screen_width,
                                     x=0, y=0,
                                     image='assets/lost.png')
            current_screen = 'end'
    elif current_screen == 'end':
        title_image.draw(screen)
        play_again.draw(screen)
        menu_text.update(screen, '')
        for score in highscores:
            score.update(text='', surface=screen)

    for event in pygame.event.get():
        if event == pygame.QUIT:
            Quit = True
            pygame.quit()
            sys.exit()
        elif (event.type == pygame.KEYDOWN or event.type == pygame.KEYUP) and \
                current_screen == 'game':
            key_state = (event.type == pygame.KEYDOWN)
            game.check_keys(key_state, event.key)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if current_screen == 'menu':
                if play_button.click(pygame.mouse.get_pos()):
                    current_screen = 'game'
                    start_sound.play_sound()
            elif current_screen == 'end':
                if play_again.click(pygame.mouse.get_pos()):
                    current_screen = 'menu'
                    title_image = Entity(height=screen_height,
                                         width=screen_width, x=0, y=0,
                                         image='assets/splash.png')
                    game = GameManager(5, randrange(3, 7))

    pygame.display.update()
