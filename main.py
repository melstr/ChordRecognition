from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QWidget, QFileDialog

import numpy as np

from signalProcessing import get_chroma, \
                         chordgram,\
                         chord_sequence_filter,\
                         chord_sequence,\
                         chord_sequence_with_time


from PyQt5.uic import loadUi
import sys
import pygame
from pygame import mixer
import os
import librosa
import librosa.display
import warnings
warnings.filterwarnings('ignore')
from spleeter.separator import Separator

def convertToDurationString(seconds):
    dSeconds = (int(seconds)) % 60
    dMinutes = (int(seconds)) // 60
    duration = str(dMinutes).zfill(2) + ":" + str(dSeconds).zfill(2)
    return duration

class ChromoUi(QWidget):
    def __init__(self, chroma, hl, musicDuration):
        super(ChromoUi, self).__init__()
        loadUi('Chromo.ui', self)

        ax = self.ChromaWidget.canvas.ax

        self.ChromaWidget.canvas.fig.subplots_adjust(0.055, 0.1, 0.98, 0.95)
        librosa.display.specshow(chroma, y_axis='chroma', cmap='gray_r', x_axis='time', ax=ax, hop_length= hl)
        ax.set_xlabel("Время (с)")
        ax.set_ylabel("Частотные классы")
        ax.set_xticks(np.arange(0, int(musicDuration) + 1, 2.0))
        adding = 0

        if musicDuration > 40:
            adding = int(musicDuration) * 20
        self.ChromaWidget.setMinimumSize(self.ChromaWidget.minimumWidth() + adding, self.ChromaWidget.minimumHeight())



class Ui(QtWidgets.QMainWindow):
    timerDelay = 40
    musicStarted = False
    musicDurationS = 0
    currentTimeS = 0
    musicDuration = "00:00"
    currentTime = "00:00"
    filePath = ''
    sr = 20050
    n_fft = 4096
    hl = 512
    filter_coef = 0.4


    def __init__(self):
        super(Ui, self).__init__()
        loadUi('MainWindow.ui', self)
        self.setWindowTitle('ChordRec')
        mixer.init()
        mixer.music.set_volume(float(self.VolumeSlider.value()) / 100)
        self.OpenFileButton.clicked.connect(self.browseFiles)
        self.PlayButton.clicked.connect(self.playOrPause)
        self.StopButton.clicked.connect(self.stop)
        self.VolumeSlider.valueChanged.connect(self.changeVolume)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.timerTick)
        self.init_spectra()
        self.OpenChromo.clicked.connect(self.openChromo)
        self.stemsButton.clicked.connect(self.separateStems)
        self.scrollArea.setWidgetResizable(True)
        self.deleteSpines(self.ChordsWidget.canvas.ax)
        self.chords_minimum_width = self.ChordsWidget.minimumWidth()

    def openChromo(self):
        self.cWindow = ChromoUi( chroma = self.chroma, hl = self.hl, musicDuration=self.musicDurationS)
        self.cWindow.show()

    def init_spectra(self):
        self.SpectroWidget.canvas.ax.spines.right.set_visible(False)
        self.SpectroWidget.canvas.ax.spines.top.set_visible(False)
        self.SpectroWidget.canvas.ax.spines.left.set_visible(False)
        self.SpectroWidget.canvas.ax.set_yticks([])
        self.SpectroWidget.canvas.ax.set_ylim([0, 150])
        self.SpectroWidget.canvas.ax.set_xlim([0, 1500])

    def plot_spectra(self, x, y):
        canvas = self.SpectroWidget.canvas
        ax = canvas.ax
        ax.cla()
        ax.plot(x, y)

        ax.set_yticks([])
        ax.spines.left.set_visible(False)
        canvas.draw()

    def loadFile(self, filepath):
        self.filePath = filepath
        self.SongName.setText(os.path.splitext(os.path.basename(filepath))[0])
        self.lineEdit.setText(filepath)
        self.PlayButton.setEnabled(True)
        self.StopButton.setEnabled(True)
        data, fs = librosa.load(filepath)
        self.sr = fs
        self.data = data
        self.musicDurationS = librosa.get_duration(y=data, sr=fs)
        mixer.music.load(filepath)
        self.updateSong()
        self.songSTFT = np.abs(librosa.stft(y=data, n_fft=self.n_fft, hop_length=self.hl))
        CHRM = get_chroma(data=self.data, fs=self.sr, hop_length=self.hl)
        self.chroma = CHRM
        CHRD = chordgram(CHRM)
        SQ = chord_sequence(CHRD)
        AL = chord_sequence_with_time(CHRD, sr=self.sr, hop_length=self.hl)

        FLT = chord_sequence_filter(AL,duration= self.musicDurationS, koef=self.filter_coef)
        self.wavePlot(chord_list=FLT, data1=data)
        self.stemsButton.setEnabled(False)
        self.StemsList.setEnabled(False)

    def browseFiles(self):
        fname = ''
        fname = QFileDialog.getOpenFileName(self, 'Откройте аудиофайл для распознавания аккордов ', '/home/my_user_name/', 'Аудиофайлы .wav (*.wav)')

        if fname != '':
            self.loadFile(filepath=fname[0])
            self.OpenChromo.setEnabled(True)
            self.stemsButton.setEnabled(True)
            self.StemsList.setEnabled(True)

    def separateStems(self):
        print(self.StemsList.currentText())
        saveTo =''
        stemName = ''
        saveTo = QFileDialog.getExistingDirectory(self,"Выберите папку для сохранения инструментов ","/home/my_user_name/", QFileDialog.ShowDirsOnly)
        stems = ''
        if saveTo != '':
            if self.StemsList.currentText() == 'Фортепиано':
                stems = 'spleeter:5stems'
                stemName ='piano.wav'
            elif self.StemsList.currentText() == 'Аккомпанемента':
                stems = 'spleeter:2stems'
                stemName = 'accompaniment.wav'
            elif self.StemsList.currentText() == 'Аккомпанемента без баса и барабанов':
                stems = 'spleeter:4stems'
                stemName = 'other.wav'

            separator = Separator(stems)
            separator.separate_to_file(self.filePath,
                                       saveTo)
            filepath = saveTo + '/' + str(os.path.splitext(os.path.basename(self.filePath))[0]) + '/' + stemName
            print(filepath)
            self.loadFile(filepath = filepath)

    def deleteSpines(self, ax):
        ax.set_yticks([])
        ax.spines.left.set_visible(False)
        ax.spines.top.set_visible(False)
        ax.spines.right.set_visible(False)

    def wavePlot(self, chord_list, data1):

        ax1 = self.ChordsWidget.canvas.ax
        ax1.cla()

        librosa.display.waveplot(y=data1, sr=self.sr, x_axis="time", ax=ax1, offset= 0.0)
        ax1.set_ylim([-3, 3])
        ax1.set_xticks(np.arange(0, int(self.musicDurationS) + 1, 2.0))
        for c in chord_list:
            ax1.text(float(c[0]), 2, c[1], style='italic',fontsize=18)
        adding = 0

        if self.musicDurationS > 40:
            adding = int(self.musicDurationS)*22
        self.ChordsWidget.setMinimumSize(self.chords_minimum_width+adding,self.ChordsWidget.minimumHeight())
        self.deleteSpines(ax = ax1)
        self.ChordsWidget.canvas.draw()

    def tickSpectra(self):
        frame = librosa.time_to_frames(sr=self.sr, n_fft=self.n_fft, hop_length=self.hl, times=self.currentTimeS)
        Y = self.songSTFT.transpose()[frame]
        X = np.linspace(0, self.sr / 2, len(Y))
        amount_freq_parts = int(len(Y) * 0.1)
        self.plot_spectra(X[:amount_freq_parts], Y[:amount_freq_parts])

    def updateSong(self):
        # self.TimeSlider.setMaximum(int(self.musicDurationS))
        if self.musicStarted:
            self.stop()
        self.musicDuration = convertToDurationString(int(self.musicDurationS))
        self.TimingLabel.setText(self.currentTime + " / " + self.musicDuration)

    def timerTick(self):
        self.setCurrentTime()
        self.tickSpectra()

    def setCurrentTime(self):
        if mixer.music.get_busy():
            self.currentTimeS = mixer.music.get_pos()/1000
            self.currentTime = (convertToDurationString(mixer.music.get_pos()//1000))
            # self.TimeSlider.setValue(mixer.music.get_pos()//1000)
            self.TimingLabel.setText(self.currentTime + " / " + self.musicDuration)
        else:
            self.timer.stop()
            self.TimingLabel.setText(self.musicDuration + " / " + self.musicDuration)
            # self.TimeSlider.setValue(int(self.musicDurationS))
            self.musicStarted = False

    def playOrPause(self):
        if self.musicStarted == False:
            mixer.music.play()
            self.timer.start(self.timerDelay)
            self.musicStarted = True
        elif mixer.music.get_busy():
            pygame.mixer.music.pause()
            self.timer.stop()
        else:
            self.timer.start()
            pygame.mixer.music.unpause()

    def stop(self):
        pygame.mixer.music.stop()
        self.timer.stop()
        self.TimingLabel.setText("00:00 / " + self.musicDuration)
        self.musicStarted = False

    def changeVolume(self):
        mixer.music.set_volume(float(self.VolumeSlider.value())/100)
        self.VolumeLabel.setText(str(self.VolumeSlider.value())+"%")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    window.show()
    app.exec_()
