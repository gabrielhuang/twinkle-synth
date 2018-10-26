import pygame
import numpy as np
from engine import MasterPlayer, NaivePoly, ADSR, sawtooth

HEIGHT = 600
WIDTH = 800
FPS = 240

KEYS = "awsedftgyhujkolp;'"  # C/C#/D/D#/E/F/F#/G/G#/A/A#/B/C/C#/D/D#/E/F
OCTAVE_DOWN = 'z'
OCTAVE_UP = 'x'

WHITENOTES = [0, 2, 4, 5, 7, 9, 11]  # position in octave
WHITENOTESNAMES = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
BLACKNOTES = [1, 3, 6, 8, 10]  # position in octave

class KeyboardNotes(object):
    MAX_OCTAVE = 8
    KEYRATIO = 5
    BLACKRATIO = 0.6

    def __init__(self):
        self.octave = 3
        self.pressed = np.zeros(12*self.MAX_OCTAVE, dtype=int)

    def next_octave(self):
        self.octave = min(self.octave+1, self.MAX_OCTAVE)

    def prev_octave(self):
        self.octave = max(self.octave-1, 0)

    def note_for(self, key):
        idx = KEYS.find(key)
        if idx == -1:
            return None
        else:
            return self.octave*12 + idx

    def is_pressed(self, key):
        return self.pressed[key] == 1

    def press(self, key):
        self.pressed[key] = 1

    def release(self, key):
        self.pressed[key] = 0

    def draw_keys(self):
        self.keywidth = WIDTH / (self.MAX_OCTAVE * 7)
        self.border = int(self.keywidth * 0.1)
        self.keyheight = self.keywidth*self.KEYRATIO
        self.blackwidth = int(0.8*self.keywidth)
        self.blackheight = int(self.BLACKRATIO * self.keyheight)
        self.offset = 400
        # Draw octave pointer
        i = self.octave * 7
        x = i * self.keywidth
        y = self.offset + self.keyheight + 5
        width = 11 * self.keywidth
        height = 3
        pygame.draw.rect(screen, pygame.color.Color('#2e8b57'), (x, y, width, height))

        for octave in xrange(self.MAX_OCTAVE):
            # Draw white keys
            for j in xrange(7):
                i = octave * 7 + j
                x = i*self.keywidth+ self.border
                y = self.offset + self.border
                width = self.keywidth - 2 * self.border
                height = self.keyheight - 2 * self.border

                # Get note
                note = octave * 12 + WHITENOTES[j]

                if self.is_pressed(note):
                    color = (155, 255, 155)
                else:
                    color = (255, 255, 255)

                pygame.draw.rect(screen, color, (x, y, width, height))

                # Draw name
                label = tiny.render('{}{}'.format(WHITENOTESNAMES[j], octave), 0, (0, 0, 0))
                #screen.blit(label, (x, y+self.keyheight*0.8))

            # Draw black keys
            for idx, j in enumerate([1, 2, 4, 5, 6]): # C# D# F# G# A#
                i = octave * 7 + j
                x = i*self.keywidth + self.border - self.blackwidth/2
                width = self.blackwidth - 2 * self.border
                height = self.blackheight

                # Get note
                note = octave * 12 + BLACKNOTES[idx]

                if self.is_pressed(note):
                    color = (0, 200, 0)
                else:
                    color = (0, 0, 0)

                pygame.draw.rect(screen, color, (x, y, width, height))


# Divide screen in two parts
pygame.init()
myfont = pygame.font.SysFont(pygame.font.get_default_font(), 75)
tiny = pygame.font.SysFont("monospace", 10)
tiny.set_bold(True)

# load and set the logo
pygame.display.set_caption("Twinkle Synth")

# create a surface on screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))

# define a variable to control the main loop
running = True

keyboard_notes = KeyboardNotes()

# Initialize master player
master = MasterPlayer()

#adsr = ADSR(a=1, d=1, s=0.5, r=1)
adsr = ADSR(a=0.005, d=1., s=0.5, r=0.5)
#adsr = ADSR()
def motherwave(x):
    return 0.5*(np.sin(x) + np.sin(2*x)/2 + np.sin(3*x)/12 + np.sin(4*x)/4 + np.sin(5*x)/20)
def motherwave(x):
    return 0.2*(np.sin(x) + np.sin(3*x) + np.sin(5*x) + np.sin(7*x) + np.sin(9*x) + np.sin(11*x))
def motherwave(x):
    return 0.5*(sawtooth(x) + sawtooth(2*x)/4 + sawtooth(3*x)/10)
synth = NaivePoly(keyboard_notes.MAX_OCTAVE,
                  master.samplesPerSecond,
                  adsr,
                  motherwave)
synth.register(master)

master.play()

# main loop
clock = pygame.time.Clock()
frame = 0
while running:
    frame += 1

    dt = clock.tick(FPS)


    # event handling, gets all event from the eventqueue
    for event in pygame.event.get():
        # only do something if the event is of type QUIT
        if event.type == pygame.QUIT:
            # change the value to False, to exit the main loop
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key not in range(256):
                continue
            character = chr(event.key)
            print '\nDOWN Key', event.key, character

            if character == 'z':  # previous octave
                print 'Previous octave'
                keyboard_notes.prev_octave()
            elif character == 'x':
                print 'Next octave'
                keyboard_notes.next_octave()
            # Which note is played?
            note = keyboard_notes.note_for(character)
            if note is not None:
                keyboard_notes.press(note)
                print 'Note is {}'.format(note)
                # Press note
                synth.press(note)

        elif event.type == pygame.KEYUP:
            character = chr(event.key)
            print '\nUP ', event.key, character

            # Which note is up?
            note = keyboard_notes.note_for(character)
            if note is not None:
                keyboard_notes.release(note)
                print 'Note is {}'.format(note)

                # Release Note
                synth.release(note)


    # Poll keys
    state = pygame.key.get_pressed()
    if state[pygame.K_LEFT]:
        pass

    if frame % 8 == 0:
        # Draw screen background
        screen.fill((220, 20, 60))

        # Render name
        label = myfont.render('Twinkle Synth', 1, (255, 255, 255))
        screen.blit(label, (20, 20))

        # Draw keys
        keyboard_notes.draw_keys()

        # Refresh display
        pygame.display.flip()

master.stop()

