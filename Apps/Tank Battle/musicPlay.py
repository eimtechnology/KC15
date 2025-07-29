from buzzer_music import music
from time import sleep
 
#Example songs

from machine import Pin

class musicPlay:
    def __init__(self):
        self.play=1
        self.welcomeMusic="0 A#6 1 43;1 C#7 1 43;2 B6 1 43;3 D7 1 43;4 A#6 1 43;5 C#7 1 43;6 B6 1 43;7 G6 1 43;8 B6 1 43;9 C#7 1 43;10 A6 1 43;11 D7 1 43"

        self.backGroundMusic="0 C5 1 43;1 A#4 1 43;3 G4 1 43;4 C5 1 43;7 G4 1 43;8 C5 1 43;10 A#4 1 43;11 G4 1 43;12 A4 1 43;13 B4 1 43;14 A#4 1 43;15 G#4 1 43;15 G4 1 43;6 A4 1 43" 

        self.shotedSound="0 D3 1 43"

        self.shotSound="0 C3 1 43"

        self.overMusic="0 D#5 1 43;0 C#5 1 43;2 D#5 1 43;2 C#5 1 43;1 F5 1 43;3 D5 1 43;4 D#5 1 43;4 C#5 1 43;6 D#5 1 43;6 C#5 1 43;5 A#4 1 43;7 E5 1 43;8 C#5 1 43;8 D#5 1 43;9 A5 1 43;10 C#5 1 43;10 D#5 1 43;11 F#5 1 43"
        
        self.welcomeMusicPlay=music(self.welcomeMusic,pins=[Pin(23)])
        self.backGroundMusicPlay = music(self.backGroundMusic, pins=[Pin(23)])
        self.overMusicPlay = music (self.overMusic,pins=[Pin(23)])
        
    def bgmPlay(self):
        if self.play:
            self.backGroundMusicPlay.tick()
    def welPlay(self):
        if self.play:
            self.welcomeMusicPlay.tick()
            sleep(0.1)
    def overPlay(self):
        if self.play:
            self.overMusicPlay.tick()
            sleep(0.1)
    def shotSoundPlay(self):
        if self.play:
            sound=music(self.shotSound,pins=[Pin(23)])
            sound.tick()
            sleep(0.1)
            sound.stop()
    def shotedSoundPlay(self):
        if self.play:
            sound=music(self.shotedSound,pins=[Pin(23)])
            sound.tick()
            sleep(0.1)
            sound.stop()
    def stop(self):
        self.welcomeMusicPlay.stop()
    def switch(self):
        if self.play:
            self.play=0
        else:
            self.play=1
        self.stop()
