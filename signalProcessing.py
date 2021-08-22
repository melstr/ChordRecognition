import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import stft
from scipy.stats import mode

COL_NAMES_NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]



def chord_templates():
    template = {}
    # Запишем названия мажорных и минорных аккордов
    majors = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    minors = ["Cm", "C#m", "Dm", "D#m", "Em", "Fm", "F#m", "Gm", "G#m", "Am", "A#m", "Bm"]

    # Шаблоны для аккордов "До мажор" и "До минор"
    C = [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1]
    Cm = [1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0]
    shifted = 0

    # Составляем шаблоны для остальных аккордов, путем сдвига массивов
    for chord in majors:
        template[chord] = C[12 - shifted:] + C[:12 - shifted]
        shifted += 1

    for chord in minors:
        template[chord] = Cm[12 - shifted:] + Cm[:12 - shifted]
        shifted += 1

    # Составляем шаблон для отсутствия аккорда
    NC = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    template["NC"] = NC

    return template

def cossim(u, v):

    return np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v))

def chordgram(chroma):

    # Для сопоставления хромогаммы, получим количество векторов
    frames = chroma.shape[1]

    # Инициализируем необходимые структуры
    template = chord_templates()
    chords = list(template.keys())
    chroma_vectors = np.transpose(chroma)

    crd_gram = []

    for n in np.arange(frames):
        cr = chroma_vectors[n]
        sims = []

        for chord in chords:
            t = template[chord]
            # Вычисляем косинусовое сходство, выставляем понижающий весовой коэффициент для
            if chord == "NC":
                sim = cossim(cr, t) * 0.7
            else:
                sim = cossim(cr, t)
            sims += [sim]
        crd_gram += [sims]
    crd_gram = np.transpose(crd_gram)

    return crd_gram


# Аккордовая последовательность по кадрам
def chord_sequence(crd_gram):
    # Инициализируем необходимые структуры
    template = chord_templates()
    chords = list(template.keys())

    frames = crd_gram.shape[1]
    crd_gram = np.transpose(crd_gram)
    crd_sequence = []

    for n in np.arange(frames):
        index = np.argmax(crd_gram[n])
        if crd_gram[n][index] == 0.0:
            chord = "NC"
        else:
            chord = chords[index]

        crd_sequence += [chord]

    return crd_sequence


def chord_sequence_filter(R, duration, koef = 0.5):
    #Фильтруем лишние короткие сигналы
    list = []
    i = 1
    while i < R.shape[0]:
        if (float(R[i][0]) - float(R[i-1][0])) < koef:
            list.append(i-1)
        i += 1

    K = np.delete(R, list, axis=0)

    i = 1
    list1 = []
    while i < K.shape[0]:
        if (K[i][1]) == (K[i - 1][1]):
            list1.append(i)
        i += 1
    if (duration - float(K[i-1][0]))<koef:
        list1.append(i-1)
    return np.delete(K, list1, axis=0)

def chord_sequence_with_time(H, sr = 22050, hop_length = 512):
    template = chord_templates()
    chords = list(template.keys())

    frames = H.shape[1]
    H = np.transpose(H)
    R = [[],[]]
    prev = "NC"
    for n in np.arange(frames):
        index = np.argmax(H[n])
        if H[n][index] == 0.0:
            chord = "NC"
        else:
            chord = "|"+chords[index]
        if prev != chord:
            prev = chord
            pair_time_chord = [hop_length*n/sr], [chord]
            # print(pair_time_chord)
            R = np.append(R, pair_time_chord,axis =1)
            # print(R)
    R = np.transpose(R)
    return R



def full_signal_fft_spectogram(signal, fs, title, f_koef=1):
    # Производим быстрое преобразование Фурье для всего аудиофайла
    ft = np.fft.fft(signal)

    # Так как нам нужны только значения частот, получаем массив положительных вещественных значений
    fr_spectrum = np.abs(ft)

    # Создаем гарфик со спектром частот
    plt.figure(figsize=(18, 5))

    # Создаем массив частот, для которых будет отображаться график
    frequency = np.linspace(0, fs, len(fr_spectrum))
    amount_freq_parts = int(len(frequency) * f_koef)

    # Обрезаем верхние частоты в зависимости от коэффициента f_koef, и строим график

    plt.plot(frequency[:amount_freq_parts], fr_spectrum[:amount_freq_parts])
    plt.xlabel("Частота (Гц)")
    plt.title(title)
    plt.show()


def plot_signal(signal, Fs, title, xlabel, ylabel):
    time_axis = np.arange(0, len(signal) / Fs, 1 / Fs)
    plt.plot(time_axis, signal)
    plt.title(title)
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')


# FFT_SIZE = 4096
# HOP_SIZE = 1024
def get_chroma(data, fs, fft_n = 4096,hop_length = 1024):
    chroma = librosa.feature.chroma_cqt(y=data, sr=fs, norm=2, hop_length=hop_length)
    # chroma = librosa.feature.chroma_stft(y=data,sr=fs, norm=2, hop_length=hop_length, n_fft=fft_n)

    return chroma

