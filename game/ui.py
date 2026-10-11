"""Общие элементы интерфейса: текст, панели, меню."""
import pygame

from config import W

_fonts = {}


def font(size):
    if size not in _fonts:
        _fonts[size] = pygame.font.Font(None, size)
    return _fonts[size]


def text(surf, s, size, pos, color=(255, 255, 255), anchor="topleft", alpha=255, shadow=True):
    f = font(size)
    img = f.render(s, True, color)
    rect = img.get_rect()
    setattr(rect, anchor, pos)
    if shadow:
        sh = f.render(s, True, (0, 0, 0))
        if alpha < 255:
            sh.set_alpha(alpha)
        surf.blit(sh, rect.move(2, 2))
    if alpha < 255:
        img.set_alpha(alpha)
    surf.blit(img, rect)
    return rect


def panel(surf, rect, alpha=170, color=(12, 10, 14), border=(230, 140, 60)):
    layer = pygame.Surface(rect.size, pygame.SRCALPHA)
    layer.fill((*color, alpha))
    surf.blit(layer, rect.topleft)
    pygame.draw.rect(surf, border, rect, 2, border_radius=8)


def dim(surf, alpha=150):
    layer = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    layer.fill((0, 0, 0, alpha))
    surf.blit(layer, (0, 0))


class Menu:
    """Список кнопок с управлением клавиатурой (стрелки, Enter) и мышью."""

    def __init__(self, items, top=300, spacing=66, width=380):
        self.items = items  # [(надпись, функция), ...]
        self.sel = 0
        self.top = top
        self.spacing = spacing
        self.width = width

    def rect(self, i):
        return pygame.Rect(W // 2 - self.width // 2, self.top + i * self.spacing, self.width, 54)

    def activate(self):
        self.items[self.sel][1]()

    def handle(self, e):
        n = len(self.items)
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_UP:
                self.sel = (self.sel - 1) % n
            elif e.key == pygame.K_DOWN:
                self.sel = (self.sel + 1) % n
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.activate()
        elif e.type == pygame.MOUSEMOTION:
            for i in range(n):
                if self.rect(i).collidepoint(e.pos):
                    self.sel = i
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i in range(n):
                if self.rect(i).collidepoint(e.pos):
                    self.sel = i
                    self.activate()
                    break

    def draw(self, surf):
        for i, (label, _) in enumerate(self.items):
            r = self.rect(i)
            sel = i == self.sel
            layer = pygame.Surface(r.size, pygame.SRCALPHA)
            layer.fill((255, 150, 60, 200) if sel else (20, 18, 24, 190))
            surf.blit(layer, r.topleft)
            pygame.draw.rect(surf, (255, 220, 160) if sel else (110, 90, 70), r, 2, border_radius=8)
            text(surf, label, 36, r.center, (20, 15, 10) if sel else (235, 225, 210), anchor="center", shadow=False)
