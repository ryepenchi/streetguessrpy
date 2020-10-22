#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 07 00:07:19 2018

@author: ryepenchi
@data: data.wien.gv.at
@Orthophoto: basemap.at
"""

import sys
import math
from os.path import join
from itertools import cycle, chain
from random import choice
import pygame
import pickle



class Game():
    def __init__(self):
        Label("select", text="Left-Click: Select Play-Area | Right-Click: Change Zoom-Level")
        Label("zoom", text="Left-Click: Confirm Play-Area | Right-Click: Go Back")
        Label("draw", text="Left-Click: Guess First Point | Right-Click: Go Back")
        Label("draw2", text="Left-Click: Guess Next Point | Right-Click: Confirm Guess")
        Label("evaluate", text="Left-Click: Next Street | Right-Click: Next Street")
        Label("street", row = 2, size = 50)
        Label("entf", row = 2, size = 50, x = 7 * SCREEN_WIDTH / 10)
        Label("meters", size= 50, x = 7 * SCREEN_WIDTH / 10)
        Label("countdown", size = 60, color = RED,row = 2, x = (SCREEN_WIDTH / 2)+60)
        Label("score", size = 60, row = 2, color = GREEN, x = SCREEN_WIDTH / 2, text= "")
        Label("gameover", text="Left-Click: New Game | Right-Click: EXIT")

    def loop(self, screen):
        clock = pygame.time.Clock()
        active_mode = Select("hard")

        while active_mode != None:
            delta_t = clock.tick( FRAME_RATE )
            (leftclick,middleclick,rightclick) = (False, False, False)
            # handle input events
            pressed_keys = pygame.key.get_pressed()
            filtered_events = []
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return # closing the window, end of the game loop
                elif event.type == pygame.KEYDOWN:
                    alt_pressed = pressed_keys[pygame.K_LALT] or pressed_keys[pygame.K_RALT]
                    if event.key == pygame.K_ESCAPE:
                        return
                    elif event.key == pygame.K_F4 and alt_pressed:
                        return
                else:
                    filtered_events.append(event)

            # render game screen
            #print(active_mode)
            active_mode.process_input(filtered_events, pressed_keys)
            active_mode.calc(leftclick, middleclick, rightclick)
            active_mode.draw(screen)
            #print(delta_t)

            active_mode = active_mode.next
            # update display
            pygame.display.update()
            # or pygame.display.flip()

    def quit(self):
        pass


class Mode():
    instances = {"select": None,
                    "zoom": None,
                    "draw": None,
                    "evaluate": None}

    def __init__(self):
        self.next = self
        self.background = None
        self.offset = [0, 0]

    def process_input(self, events, pressed_keys):
        print("Uhoh you didnt overwrite this in child class")

    def switch_to_mode(self, next_mode):
        self.next = next_mode
        if next_mode != None:
            next_mode.next = next_mode

    def draw(self, screen):
        print("Uhoh you didnt overwrite this in child class")

    def calc(self, leftclick, middleclick, rightclick):
        print("Uhoh you didnt overwrite this in child class")

    def init_borders(self):
        off = self.off_for_init_borders
        frame = self.frame
        size = SIZE
        delta_long = 16.59 - 16.16
        delta_lat = 48.34 - 48.1
        lat_min = 48.1 + delta_lat * (1-(off[1]+frame[1])/size[1])
        lat_max = 48.1 + delta_lat * (1-(off[1]/size[1]))
        long_min = 16.16 + delta_long * (off[0]/size[0])
        long_max = 16.16 + delta_long * ((off[0]+frame[0])/size[0])
        self.lomi, self.loma, self.lami, self.lama = [round(x,6) for x in [long_min, long_max, lat_min, lat_max]]
        self.borders = self.lami, self.lama, self.lomi, self.loma

    def new_street(self):
        random_street = choice(list(streetDB))
        lami, lama, lomi, loma = streetDB[random_street]["Grenzwerte"]
        while not (self.lami < lami and lama < self.lama and self.lomi < lomi and loma < self.loma):
            random_street = choice(list(streetDB))
            lami, lama, lomi, loma = streetDB[random_street]["Grenzwerte"]
        self.street = random_street
        Label.instances["street"].new_text(random_street)
        self.localize()
        self.guessed_points = []

    def localize(self):

        def wgs_to_local(tupl):
            lat, lon = tupl
            y = SCREEN_HEIGHT - (lat - self.lami) * SCREEN_HEIGHT / (self.lama - self.lami)
            x = (lon - self.lomi) * SCREEN_WIDTH / (self.loma - self.lomi)
            return round(x), round(y)

        coords = streetDB[self.street]["coords"]
        if type(coords[0]) == tuple:
            self.localcoords = [wgs_to_local(tupl) for tupl in coords]
        elif type(coords[0][0]) == tuple:
            self.localcoords = [[wgs_to_local(tupl) for tupl in sublist] for sublist in coords]

        self.localmitte = wgs_to_local(streetDB[self.street]["Mitte"])

    def draw_street(self, screen):
        if type(self.localcoords[0]) == tuple:
            if len(self.localcoords) > 1:
                pygame.draw.lines(screen, GREEN, False, self.localcoords, 3)
            else:
                pygame.draw.circle(screen, GREEN, self.localcoords[0], 3)
        elif type(self.localcoords[0][0]) == tuple:
            for sublist in self.localcoords:
                if len(sublist) > 1:
                    pygame.draw.lines(screen, GREEN, False, sublist, 3)
                else:
                    pygame.draw.circle(screen, GREEN, sublist[0], 3)


class Select(Mode):
    def __init__(self, difficulty):
        super(Select, self).__init__()
        self.instances["select"] = self
        self.menu = Menu(["hard","easy", "ortho", "schicht"], 5, THUMBNAIL_SIZE)
        self.difficulty = difficulty
        self.frame, self.zoom = next(FRAMESIZE), next(ZOOMMODE)
        self.background = imgDB[self.difficulty][1]

    def calc(self, leftclick, middleclick, rightclick):
        if self.zoom == 1:
            self.frame_corner = [0, 0]
            self.off_for_init_borders = [0, 0]
            self.off_for_drawing_bg = [0, 0]
            self.init_borders()
        else:
            f0x,f0y = pygame.mouse.get_pos()
            if f0x > SCREEN_WIDTH - self.frame[0]:
                f0x = SCREEN_WIDTH - self.frame[0]
            if f0y > SCREEN_HEIGHT - self.frame[1]:
                f0y = SCREEN_HEIGHT - self.frame[1]
            self.frame_corner = [f0x, f0y]
            self.off_for_init_borders= [f0x, f0y]
            self.off_for_drawing_bg = [-self.zoom*x for x in [f0x, f0y]]
            self.init_borders()

    def process_input(self, events, pressed_keys):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                (leftclick, middleclick, rightclick) = pygame.mouse.get_pressed()
                if rightclick:
                    self.frame, self.zoom = next(FRAMESIZE), next(ZOOMMODE)
                elif leftclick:
                    if not self.menu.mask.get_at(pygame.mouse.get_pos()):
                        self.switch_to_mode(Zoom())
                    else:
                        for item in range(len(self.menu.items)):
                            if self.menu.item_masks[item].get_at(pygame.mouse.get_pos()):
                                self.difficulty = DIFFICULTIES[item]
                                self.background = imgDB[self.difficulty][1]

    def draw(self, screen):
        self.background.draw(screen, self.offset)
        self.menu.draw(screen)
        Label.instances["select"].draw(screen)
        pygame.draw.rect(screen, RED, self.frame_corner + self.frame, 2)


class Zoom(Mode):
    def __init__(self):
        super(Zoom, self).__init__()
        self.instances["zoom"] = self
        self.zoom = Mode.instances["select"].zoom
        self.difficulty = Mode.instances["select"].difficulty
        self.frame = Mode.instances["select"].frame
        self.offset = Mode.instances["select"].off_for_drawing_bg
        #self.off_for_init_borders = Mode.instances["select"].off_for_init_borders
        self.background = imgDB[self.difficulty][self.zoom]

    def draw(self, screen):
        self.background.draw(screen, self.offset)
        Label.instances["zoom"].draw(screen)
        pygame.draw.rect(screen, RED, [0, 0, SCREEN_WIDTH, SCREEN_HEIGHT], 8)

    def calc(self, leftclick, middleclick, rightclick):
        pass

    def process_input(self, events, pressed_keys):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                (leftclick, middleclick, rightclick) = pygame.mouse.get_pressed()
                if rightclick:
                    for i in range(3):
                        next(FRAMESIZE)
                        next(ZOOMMODE)
                    self.switch_to_mode(Select(self.difficulty))
                elif leftclick:
                    self.switch_to_mode(Draw())


class Draw(Mode):
    def __init__(self):
        super(Draw, self).__init__()
        self.instances["draw"] = self
        self.difficulty = Mode.instances["zoom"].difficulty
        self.frame = Mode.instances["zoom"].frame
        self.zoom = Mode.instances["zoom"].zoom
        self.background = imgDB[self.difficulty][self.zoom]
        self.offset = Mode.instances["zoom"].offset
        self.off_for_init_borders = Mode.instances["select"].off_for_init_borders
        self.init_borders()
        self.new_street()
        self.guessed_points = []
        self.meters = 5000
        Label.instances["meters"].new_text(str(self.meters)+" Meter übrig")
        self.score = 0
        Label.instances["score"].new_text(str(self.score))
        self.start_ticks = pygame.time.get_ticks()

    def calc(self, leftclick, middleclick, rightclick):
        
        self.seconds = round((pygame.time.get_ticks() - self.start_ticks) / 1000, 1)
        count = round(10 - self.seconds, 1)
        if count < 0:
            self.switch_to_mode(Evaluate(self, guessed = False))
        Label.instances["countdown"].new_text(str(count) + " sec")
        #print(str(self.seconds) + " sec")

    def draw(self, screen):
        self.background.draw(screen, self.offset)
        if self.guessed_points:
            if len(self.guessed_points) > 1:
                pygame.draw.lines(screen, RED, False, self.guessed_points, 2)
            #pygame.draw.line(screen, RED, self.guessed_points[-1], pygame.mouse.get_pos(), 2)
            draw_dashed_line(screen, RED, self.guessed_points[-1], pygame.mouse.get_pos(), width=2)
            Label.instances["draw2"].draw(screen)
        else:
            Label.instances["draw"].draw(screen)

        Label.instances["street"].draw(screen)
        Label.instances["meters"].draw(screen)
        Label.instances["countdown"].draw(screen)
        Label.instances["score"].draw(screen)
        #self.draw_street(screen)

    def process_input(self, events, pressed_keys):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                (leftclick, middleclick, rightclick) = pygame.mouse.get_pressed()
                if rightclick:
                    if self.guessed_points:
                        self.score += 1
                        self.switch_to_mode(Evaluate(self))
                    else:
                        self.switch_to_mode(Zoom())
                elif leftclick:
                    self.guessed_points.append(pygame.mouse.get_pos())


class Evaluate(Mode):
    def __init__(self, last_mode, guessed = True):
        super(Evaluate, self).__init__()
        self.instances["evaluate"] = self
        self.background = last_mode.background
        self.offset = last_mode.offset
        self.zoom = last_mode.zoom
        self.guessed_points = last_mode.guessed_points
        self.street = last_mode.street
        self.localcoords = last_mode.localcoords
        self.localmitte = last_mode.localmitte
        self.guessed = guessed
        if guessed:
            self.calc_mitte()
            self.calc_entf(self.localmitte, self.guessedmitte)
            self.meters = last_mode.meters - self.entf
        else:
            self.meters = last_mode.meters
        Label.instances["meters"].new_text(str(self.meters)+ " Meter übrig")


    def calc_mitte(self):
        coords = self.guessed_points
        if type(coords[0]) != tuple:
            coords = list(chain.from_iterable(coords))
        y_min = min(coords,key=lambda coords:coords[1])[1]
        y_max = max(coords,key=lambda coords:coords[1])[1]

        y_mitte = round((y_min + y_max) / 2)

        x_min = min(coords,key=lambda coords:coords[0])[0]
        x_max = max(coords,key=lambda coords:coords[0])[0]

        x_mitte = round((x_min + x_max) / 2)
        self.guessedmitte = (x_mitte, y_mitte)

    def calc_entf(self, a, b):
        delta_long = 16.59 - 16.16
        delta_lat = 48.34 - 48.1
        x = a[0]-b[0]
        y = a[1]-b[1]
        d_long = (x*delta_long/(SIZE[0]*self.zoom))
        d_lat = (y*delta_lat/(SIZE[1]*self.zoom))
        meter_x = d_long / (13.52 * 10**-6) # /1m in Längengrad
        meter_y = d_lat / (8.99324 * 10**-6) # /1m in Breitengrad
        self.entf = round(math.sqrt((meter_x)**2+(meter_y)**2))
        Label.instances["entf"].new_text(str(self.entf) + " Meter daneben")

    def calc(self, leftclick, middleclick, rightclick):
        if self.next != self:
            Mode.instances["draw"].new_street()
            Mode.instances["draw"].meters = self.meters
            Label.instances["score"].new_text(str(Mode.instances["draw"].score))
            Mode.instances["draw"].start_ticks = pygame.time.get_ticks()

    def draw(self, screen):
        self.background.draw(screen, self.offset)
        Label.instances["evaluate"].draw(screen)
        Label.instances["street"].draw(screen)
        Label.instances["entf"].draw(screen)
        Label.instances["meters"].draw(screen)
        self.draw_street(screen)
        if self.guessed:
            self.draw_guess(screen)
            draw_dashed_line(screen, WHITE, self.localmitte, self.guessedmitte, width=2)

    def draw_guess(self, screen):
        if len(self.guessed_points) > 1:
            pygame.draw.lines(screen, RED, False, self.guessed_points, 3)
        else:
            pygame.draw.circle(screen, RED, self.guessed_points[0], 3)

    def process_input(self, events, pressed_keys):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if pygame.mouse.get_pressed():
                    if self.meters > 0:
                        self.switch_to_mode(Mode.instances["draw"])
                    else:
                        self.switch_to_mode(GameOver(self))


class GameOver(Mode):
    def __init__(self, last_mode):
        super(GameOver, self).__init__()
        self.instances["gameover"] = self
        self.background = Background(WHITE, None, None)
        self.meters = Mode.instances["evaluate"].meters
        self.calc_score(last_mode.background)
        #Label.instances["meters"].new_text(str(self.meters)+ " Meter übrig"

    def process_input(self, events, pressed_keys):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                (leftclick, middleclick, rightclick) = pygame.mouse.get_pressed()
                if leftclick:
                    self.switch_to_mode(Select("hard"))
                if rightclick:
                    self.switch_to_mode(None)

    def draw(self, screen):
        self.background.draw(screen, self.offset)
        Label.instances["gameover"].draw(screen)
        Label.instances["meters"].draw(screen)
        Label.instances["final"].draw(screen)
        #print(self.final_score)

    def calc(self, leftclick, middleclick, rightclick):
        pass

    def calc_score(self, used_bg):
        m1 = {"hard": 8, "easy": 4, "ortho": 2, "schicht": 6}
        m2 = {1:8, 2:4, 4:2, 8:1} #based on zoom
        self.m1 = m1[used_bg.difficulty]
        self.m2 = m2[used_bg.zoom]
        print(used_bg.difficulty, self.m1)
        print(used_bg.zoom, self.m2)
        self.score = Mode.instances["draw"].score
        print("score", self.score)
        self.final_score = self.score * self.m1 * self.m2
        print("Final Score", self.final_score)
        a = "Guessed Streets: %d\n" % self.score
        b = "BaseMap Multiplier: x%d\n" % self.m1
        c = "Zoom Multiplier: x%d\n" % self.m2
        d = "--------------------------------\n"
        e = "      Final Score: %d" % self.final_score
        text = a + b + c + d + e
        #text ="Guessed Streets: %d\nBaseMap Multiplier: x%d \nZoom Multiplier: x%d \n-------------------------------- \n        Final Score: %d" % (self.score, self.m1, self.m2, self.final_score)
        Label("final", text=text, x = 400, size = 70, row = 3)


class Background:
    def __init__(self, path, difficulty, zoom):
        self.path = path
        self.surface = None
        self.difficulty = difficulty
        self.zoom = zoom

    def draw(self, screen, offset):
        self.offset = offset
        if not self.surface:
            if self.path in [join("data", "ortho" + str(x) + ".jpeg") for x in [1, 2, 8]]:
                self.surface = pygame.image.load(join("data", "ortho4.jpeg"))
                scale = pygame.transform.scale
                zoom = int(self.path[-6])
                self.surface = scale(self.surface, [zoom*x for x in SIZE]).convert()
            elif self.path in [join("data", "schicht1.jpeg"), 
                                join("data", "schicht2.jpeg"),
                                join("data", "schicht8.jpeg")]:
                self.surface = pygame.image.load(join("data", "schicht4.jpeg"))
                scale = pygame.transform.scale
                zoom = int(self.path[-6])
                self.surface = scale(self.surface, [zoom*x for x in SIZE]).convert()
            elif self.path in [x + "_thumbnail" for x in ["hard", "easy", "ortho", "schicht"]]:
                scale = pygame.transform.scale
                pic = pygame.image.load(join("data", self.difficulty + "4.jpeg"))
                self.surface = scale(pic, THUMBNAIL_SIZE)
            elif type(self.path) == tuple:
                surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                surface.fill(self.path)
                self.surface = surface
            else:
                self.surface = pygame.image.load(self.path).convert()
        screen.blit(self.surface, self.offset)
        screen.fill(WHITE, rect = (0, SCREEN_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT + FUSSLEISTE))


class Label:
    instances = {}
    def __init__(self, mode, **kwargs):
        Label.instances[mode] = self
        self.x = 5
        self.text = ""
        self.row = 1
        self.size = 40
        self.color = FONT_COLOR
        for key in ("row", "text", "color", "size", "x", "y"):
            if key in kwargs:
                setattr(self, key, kwargs[key])
        self.lbl = [calibri(self.size).render(line, 1, self.color) for line in self.text.splitlines()]
        #self.lbl = calibri(self.size).render(self.text, 1, self.color)
        #self.y = SCREEN_HEIGHT - 5 - self.lbl.get_height() + FUSSLEISTE


    def new_text(self, text):
        self.lbl = [calibri(self.size).render(line, 1, self.color) for line in text.splitlines()]

    def draw(self, screen):
        if self.row == 1:
            self.y = SCREEN_HEIGHT - self.size + FUSSLEISTE
        if self.row == 2:
            self.y = SCREEN_HEIGHT
        if self.row == 3:
            self.y = 400
        for i, lbl in enumerate(self.lbl):
            screen.blit(lbl, (self.x, self.y + lbl.get_height() * i))


class Menu:
    def __init__(self, items, padding, thumbnail_size):
        menu_width = thumbnail_size[0] + padding
        menu_height = thumbnail_size[1] * len(items) + padding * len(items)
        menu_x = SCREEN_WIDTH - menu_width
        menu_y = padding

        menu_mask = pygame.mask.Mask((SCREEN_WIDTH, SCREEN_HEIGHT))
        for x in range(menu_x, SCREEN_WIDTH):
            for y in range(menu_y, menu_height):
                menu_mask.set_at([x, y], 1)

        item_masks = []
        item_coords = {}
        for i, name in enumerate(items):
            item_coords[name] = [menu_x, padding*(i+1)+thumbnail_size[1]*i]
            item_masks.append(pygame.mask.Mask((SCREEN_WIDTH, SCREEN_HEIGHT)))
            for x in range(menu_x, SCREEN_WIDTH - padding):
                for y in range(padding*(i+1)+thumbnail_size[1]*i, 
                                padding*(i+1)+thumbnail_size[1]*(i+1)):
                    item_masks[i].set_at([x, y], 1)

        self.items = items
        self.padding = padding
        self.thumbnail_size = thumbnail_size
        self.item_masks = item_masks
        self.mask = menu_mask
        self.item_coords = item_coords

    def draw(self, screen):
        for difficulty in self.items:
            imgDB[difficulty]["thumbnail"].draw(screen, self.item_coords[difficulty])


class Point:
    # constructed using a normal tupple
    def __init__(self, point_t = (0,0)):
        self.x = float(point_t[0])
        self.y = float(point_t[1])
    # define all useful operators
    def __add__(self, other):
        return Point((self.x + other.x, self.y + other.y))
    def __sub__(self, other):
        return Point((self.x - other.x, self.y - other.y))
    def __mul__(self, scalar):
        return Point((self.x*scalar, self.y*scalar))
    def __truediv__(self, scalar):
        try:
            return Point((self.x/scalar, self.y/scalar))
        except ZeroDivisionError:
            return 0
    def __len__(self):
        return int(math.sqrt(self.x**2 + self.y**2))
    # get back values in original tuple format
    def get(self):
        return (self.x, self.y)

def draw_dashed_line(surf, color, start_pos, end_pos, width=1, dash_length=10):
    origin = Point(start_pos)
    target = Point(end_pos)
    displacement = target - origin
    length = len(displacement)
    slope = displacement / length

    for index in range(0, length//dash_length, 2):
        start = origin + (slope *    index    * dash_length)
        end   = origin + (slope * (index + 1) * dash_length)
        pygame.draw.line(surf, color, start.get(), end.get(), width)

def load_obj(name):
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)

def calibri(size):
    return pygame.font.SysFont("Calibri", size)


# screen constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 960
FUSSLEISTE = 80
SIZE = [SCREEN_WIDTH, SCREEN_HEIGHT]
FRAME_RATE = 30
DIFFICULTIES = ["hard", "easy", "ortho", "schicht"]
THUMBNAIL_SIZE = (96, 72)
#FRAMESIZE = cycle([[640,480],[320,240],[160,120],[1280, 960]])
FRAMESIZE = cycle([[SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2], 
                    [SCREEN_WIDTH / 4, SCREEN_HEIGHT / 4],
                    [SCREEN_WIDTH / 8, SCREEN_HEIGHT / 8],
                    [SCREEN_WIDTH, SCREEN_HEIGHT]])
ZOOMMODE = cycle([2,4,8,1])

# Define some colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
SEA_GREEN = (46,139,87)
FONT_COLOR = BLACK


# set up Image dictinionary
imgDB = {}
for difficulty in DIFFICULTIES:
    imgDB[difficulty] = {}
    for zoom in [1, 2, 4, 8]:
        imgDB[difficulty][zoom] = Background(join("data", difficulty + str(zoom) + ".jpeg"), difficulty, zoom)
    imgDB[difficulty]["thumbnail"] = Background(difficulty+"_thumbnail", difficulty, 4)

# WGS - Coordinate data path from streets.pkl file
STREET_DATA = join("data","streets")
streetDB = load_obj(STREET_DATA)

def main():
    pygame.init()
    pygame.mixer.quit()
    screen = pygame.display.set_mode( (SCREEN_WIDTH, SCREEN_HEIGHT + FUSSLEISTE) )
    pygame.display.set_caption( 'StreetgssrOOP' )
    #pygame.mouse.set_visible( False )

    game = Game()
    game.loop(screen)
    game.quit()

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()