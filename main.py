#! /usr/bin/env python3.9

"""
a race car in pygame
"""

__author__ = "TFC343"
__version__ = "1.1.0"

import os
import sys
import time
import traceback
from math import sin, cos, tau, degrees, atan2

import pygame
import pygame.gfxdraw
from pygame.locals import *
pygame.init()
pygame.font.init()


class Line:
    def __init__(self, start, end, width=1):
        self.start = start
        self.end = end
        self.width = width

    def __repr__(self):
        return f"({self.start}, {self.end})"

    def __getitem__(self, item):
        if item == 0:
            return self.start
        if item == 1:
            return self.end

    @property
    def gradient(self):
        try:
            return (self.end[1] - self.start[1]) / (self.end[0] - self.start[0])
        except ZeroDivisionError:
            return -2.809

    @property
    def y_intercept(self):
        return self.start[1] - (self.gradient * self.start[0])

    @staticmethod
    def __ccw(A, B, C):
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

    def line_intersect(line1, line2):
        a, b, c, d = line1.start, line1.end, line2.start, line2.end
        return Line.__ccw(a, c, d) != Line.__ccw(b, c, d) and Line.__ccw(a, b, c) != Line.__ccw(a, b, d)

    def collide_point(self, x, y):
        if min(self.start[0], self.end[0]) < x < max(self.start[0], self.end[0]) and min(self.start[1], self.end[1]) < y < max(self.start[1], self.end[1]) and y - self.gradient * x - self.y_intercept < 100:
            return True
        return False

    def draw(self, surface, colour, aa=False):
        if aa:
            pygame.draw.aaline(surface, colour, self.start, self.end)
        else:
            pygame.draw.line(surface, colour, self.start, self.end, self.width)


class Track:
    def __init__(self, outer, inner, start, check_point):
        self.outer_lines = [Line(start, end) for start, end in zip(outer[:-1], outer[1:])] + [Line(outer[-1], outer[0])]
        self.inner_lines = [Line(start, end) for start, end in zip(inner[:-1], inner[1:])] + [Line(inner[-1], inner[0])]
        self.start = Line(start[0], start[1], width=3)
        self.check_points = [Line(s1, s2) for s1, s2 in check_point]
        self.checks = [False for _ in check_point]
        self.lap_start = time.perf_counter()
        self.best_time = float("inf")
        self.started = False
        self.times = []
        self.latest = -1

    def reset(self):
        self.checks = [False for _ in self.checks]
        self.lap_start = time.perf_counter()
        self.started = False

    def get_lap_time(self):
        if self.started:
            return time.perf_counter() - self.lap_start
        return 0

    def draw(self, surface):
        # for check, entity in zip(self.checks, self.check_points):
        #     entity.draw(surface, 'light blue' if check else 'blue')
        # for entity in self.outer_lines + self.inner_lines:
        #     entity.draw(surface, 'white', True)
        pygame.draw.polygon(surface, (100, 100, 100), [i.start for i in self.outer_lines])
        pygame.draw.polygon(surface, FLOOR, [i.start for i in self.inner_lines])
        self.start.draw(surface, 'blue')
        for check, entity in zip(self.checks, self.check_points):
            entity.draw(surface, 'light blue' if check else 'blue')

    def update(self, car):
        for num, point in enumerate(self.check_points):
            for line in car.get_lines():
                if point.line_intersect(line):
                    if self.checks[num-1] or num == 0:
                        self.checks[num] = True
        for line in car.get_lines():
            if self.start.line_intersect(line):
                if all(self.checks):
                    self.checks = [False for _ in self.checks]
                    self.times.append(self.get_lap_time())
                    self.latest += 1
                    if self.get_lap_time() < self.best_time:
                        self.best_time = self.get_lap_time()
                    self.lap_start = time.perf_counter()
                elif not self.started:
                    self.started = True
                    self.lap_start = time.perf_counter()


class Car(pygame.sprite.Sprite):
    def __init__(self, pos=(186, 435)):
        self.exact_pos = list(pos)
        self.velocity = [0, 0]
        self.rel_vel = [0, 0]
        self.angle = 0
        size_mod = 2
        self.width, self.height = int(10*size_mod), int(23*size_mod)
        self.image = pygame.transform.scale(pygame.image.load(resource_path("car.png")), (self.width, self.height))
        self.original_image = self.image
        self.rect = self.image.get_rect()
        self.rect.center = pos
        super().__init__()

    def reset(self):
        self.exact_pos = [186, 435]
        self.velocity = [0, 0]
        self.rel_vel = [0, 0]
        self.angle = 0

    def update(self):
        # friction:
        # self.velocity[0] = self.velocity[0] * 0.985
        # self.velocity[1] = self.velocity[1] * 0.985
        self.rel_vel[0] *= 0.975
        self.rel_vel[1] *= 0.94
        # print(self.rel_vel)

        # self.exact_pos[0] += self.velocity[0]
        self.exact_pos[0] += self.rel_vel[0] * sin(self.angle) + self.rel_vel[1] * cos(self.angle)
        # print(self.rect.centerx - self.rect.left)
        bounce = -0.9
        if self.exact_pos[0] - (self.exact_pos[0] - self.left) < 0:
            self.exact_pos[0] = (self.exact_pos[0] - self.left) + 0
            self.velocity[0] *= bounce
        elif self.exact_pos[0] + (self.right - self.exact_pos[0]) > 1270:
            self.exact_pos[0] = 1270 - (self.right - self.exact_pos[0])
            self.velocity[0] *= bounce
        # self.exact_pos[1] += self.velocity[1]
        self.exact_pos[1] += self.rel_vel[0] * cos(self.angle) - self.rel_vel[1] * sin(self.angle)
        if self.exact_pos[1] - (self.exact_pos[1] - self.top) < 0:
            self.exact_pos[1] = 0 + (self.exact_pos[1] - self.top)
            self.velocity[1] *= bounce
        elif self.exact_pos[1] + (self.bottom - self.exact_pos[1]) > 720:
            self.exact_pos[1] = 720 - (self.bottom - self.exact_pos[1])
            self.velocity[1] *= bounce
        # self.move_toward()

    def get_corners(self):
        return (self.exact_pos[0] - cos(tau/4-self.angle) * self.height/2 + sin(tau/4-self.angle) * self.width/2, self.exact_pos[1] - cos(tau/4-self.angle) * self.width/2 - sin(tau/4-self.angle) * self.height/2), \
               (self.exact_pos[0] + cos(tau/4-self.angle) * self.height/2 + sin(tau/4-self.angle) * self.width/2, self.exact_pos[1] - cos(tau/4-self.angle) * self.width/2 + sin(tau/4-self.angle) * self.height/2), \
               (self.exact_pos[0] + cos(tau/4-self.angle) * self.height/2 - sin(tau/4-self.angle) * self.width/2, self.exact_pos[1] + cos(tau/4-self.angle) * self.width/2 + sin(tau/4-self.angle) * self.height/2), \
               (self.exact_pos[0] - cos(tau/4-self.angle) * self.height/2 - sin(tau/4-self.angle) * self.width/2, self.exact_pos[1] + cos(tau/4-self.angle) * self.width/2 - sin(tau/4-self.angle) * self.height/2),

    def get_lines(self):
        corners = self.get_corners()
        return Line(corners[0], corners[1]), Line(corners[1], corners[3]), Line(corners[0], corners[2]), Line(corners[2], corners[3])

    def draw(self, surface):
        self.temp = pygame.transform.rotate(self.original_image, degrees(self.angle))
        surface.blit(self.temp, self.temp.get_rect(center=self.exact_pos))

    def accelerate(self, mag):
        self.velocity[0] += mag*sin(self.angle)
        self.velocity[1] += mag*cos(self.angle)
        self.rel_vel[0] += mag

    def turn(self, ang):
        t_vel: list = self.rel_vel[:]
        t_vel[0] = self.rel_vel[0] * cos(ang) + self.rel_vel[1] * sin(ang)
        t_vel[1] = - self.rel_vel[0] * sin(ang) + self.rel_vel[1] * cos(ang)
        # self.rel_vel = t_vel
        # TODO add drift
        self.angle += ang

    def break_(self, force):
        self.rel_vel[0] *= 0.88

    def move_toward(self, pos=(625, 360)):
        x, y = pos
        new_angle = tau/4 - atan2(self.exact_pos[1] - y, self.exact_pos[0] - x)
        self.velocity[0] += -0.06*sin(new_angle)
        self.velocity[1] += -0.06*cos(new_angle)

    @property
    def bottom(self):
        return max(self.get_corners(), key=lambda x: x[1])[1]

    @property
    def top(self):
        return min(self.get_corners(), key=lambda x: x[1])[1]

    @property
    def left(self):
        return min(self.get_corners(), key=lambda x: x[0])[0]

    @property
    def right(self):
        return max(self.get_corners(), key=lambda x: x[0])[0]


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


BLACK = pygame.Color(0, 0, 0)
WHITE = pygame.Color(255, 255, 255)
FPS = 60
FONT = pygame.font.SysFont('arial', 30)
TROPHY = pygame.Color(212, 175, 55), pygame.Color(192, 192, 192), pygame.Color(176, 141, 87)
FLOOR = pygame.color.Color((244, 226, 198))


def main():
    surf = pygame.display.set_mode((1270, 720), pygame.SRCALPHA)
    pygame.display.set_caption("race car")

    car = Car()
    player = pygame.sprite.Group(car)

    fps = pygame.time.Clock()

    outer_track_point = [(149, 464), (133, 138), (157, 113), (553, 35), (693, 205), (981, 160), (1163, 251), (1093, 607), (448, 682), (163, 547)]
    inner_track_points = [(228, 486), (208, 210), (253, 158), (496, 113), (661, 274), (943, 238), (1041, 292), (1015, 544), (469, 597)]
    check_points = [((138, 242), (209, 237)),
                    ((336, 77), (341, 142)),
                    ((575, 62), (509, 126)),
                    ((681, 192), (628, 241)),
                    ((790, 189), (796, 254)),
                    ((1034, 188), (992, 264)),
                    ((1036, 335), (1142, 356)),
                    ((1108, 529), (1018, 519)),
                    ((919, 626), (907, 557)),
                    ((482, 678), (491, 596)),
                    ((297, 610), (340, 538))]
    track = Track(outer_track_point, inner_track_points, ((145, 378), (221, 374)), check_points)

    running = True
    while running:
        pressed_keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            if event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    print(event.pos)
            if event.type == KEYDOWN:
                if event.key == K_k:
                    car.turn(-tau/4)
                if event.key == K_ESCAPE:
                    car.reset()
                    track.reset()

        if pressed_keys[K_w]:
            car.accelerate(-0.20)
        if pressed_keys[K_s]:
            car.accelerate(0.20)
        if pressed_keys[K_a]:
            car.turn(0.06*0.95)
        if pressed_keys[K_d]:
            car.turn(-0.06*0.95)
        if pressed_keys[K_SPACE]:
            car.break_(4)
        if pressed_keys[K_q]:
            car.rel_vel[1] += -0.06
        if pressed_keys[K_e]:
            car.rel_vel[1] += 0.06
        car.update()
        track.update(car)

        surf.fill(FLOOR)
        in_bound = True
        corners = car.get_corners()
        for corner in corners:
            colls = 0
            for wall in track.outer_lines + track.inner_lines:
                l = Line((635, 360), corner)
                # l.draw(surf, 'red')
                if l.line_intersect(wall):
                    colls += 1
            if not colls % 2:
                in_bound = False

        if not in_bound: track.lap_start -= 0.001

        # draw_polygon(surf, WHITE, poly, )
        track.draw(surf)
        rend = FONT.render(str(round(track.get_lap_time(), 5)), True, (255, 255, 255) if in_bound else (255, 0, 0))
        surf.blit(rend, (0, 0))
        for i, time_ in enumerate(sorted(track.times)[:10]):
            if track.times.index(time_) == track.latest:
                c = pygame.Color(0, 255, 0)
            elif i < 3:
                c = TROPHY[i]
            else:
                c = WHITE
            rend = FONT.render(str(round(time_, 5)), True, c)
            surf.blit(rend, (0, 50*i+60))

        car.draw(surf)
        pygame.display.update()

        fps.tick(FPS)


if __name__ == '__main__':
    try:
        main()
    finally:
        pygame.quit()
        if sys.exc_info()[0] is not None:
            info = sys.exc_info()
            traceback.print_exc()
            input()
            raise sys.exc_info()[1]
