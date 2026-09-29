import os
import json
import numpy as np
import scipy.signal

class FFTAnalyzer:
    WINDOW_TYPES = ["Aucun (Rectangulaire)", "Hann", "Hamming", "Blackman", "Flat-top"]
    N_POINTS_OPTIONS = ["Auto", "512", "1024", "2048", "4096", "8192", "16384"]

    @staticmethod
    def compute_fft(x_data, y_data, window_type="Hann", n_points="Auto", f_min=None, f_max=None):
        """
        Calcule le spectre d'amplitude par FFT.
        """
        if len(x_data) < 2 or len(y_data) < 2:
            return np.array([]), np.array([]), 0.0

        # Estimation de la période d'échantillonnage et de la fréquence de sampling
        dt_vec = np.diff(x_data)
        dt = float(np.mean(dt_vec)) if len(dt_vec) > 0 and np.mean(dt_vec) > 0 else 1.0
        fs = 1.0 / dt

        # Détermination de N
        if str(n_points).lower() == "auto" or str(n_points) == "0":
            N = len(y_data)
        else:
            try:
                N = int(n_points)
            except ValueError:
                N = len(y_data)

        # Extraction du segment
        y_segment = y_data[:min(N, len(y_data))]
        if len(y_segment) < N:
            # Zero-padding
            y_segment = np.pad(y_segment, (0, N - len(y_segment)), 'constant')

        # Fenêtrage
        w = FFTAnalyzer._get_window(window_type, len(y_segment))
        y_windowed = y_segment * w

        # Calcul FFT réelle
        fft_vals = np.fft.rfft(y_windowed, n=N)
        freqs = np.fft.rfftfreq(N, d=dt)

        # Spectre d'amplitude normalisé
        # Compensation moyenne de la fenêtre
        w_gain = np.mean(w) if np.mean(w) > 0 else 1.0
        amplitude = (2.0 / (N * w_gain)) * np.abs(fft_vals)
        amplitude[0] /= 2.0  # composante continue

        # Filtrage par f_min / f_max
        if f_min is not None or f_max is not None:
            mask = np.ones_like(freqs, dtype=bool)
            if f_min is not None:
                mask &= (freqs >= f_min)
            if f_max is not None:
                mask &= (freqs <= f_max)
            freqs = freqs[mask]
            amplitude = amplitude[mask]

        return freqs, amplitude, fs

    @staticmethod
    def _get_window(window_type, size):
        if "Hann" in window_type:
            return np.hanning(size)
        elif "Hamming" in window_type:
            return np.hamming(size)
        elif "Blackman" in window_type:
            return np.blackman(size)
        elif "Flat-top" in window_type:
            return scipy.signal.windows.flattop(size)
        else:
            return np.ones(size)

    @staticmethod
    def detect_peaks(freqs, amplitude, num_peaks=5):
        """
        Détecte les N pics principaux dans le spectre.
        """
        if len(amplitude) < 3:
            return []

        # Recherche de maxima locaux
        peaks_idx, _ = scipy.signal.find_peaks(amplitude)
        if len(peaks_idx) == 0:
            # Fallback sur les valeurs maximales
            sorted_idx = np.argsort(amplitude)[::-1]
            peaks_idx = sorted_idx[:min(num_peaks, len(sorted_idx))]
        else:
            # Trier par amplitude décroissante
            sorted_by_amp = sorted(peaks_idx, key=lambda idx: amplitude[idx], reverse=True)
            peaks_idx = sorted_by_amp[:min(num_peaks, len(sorted_by_amp))]

        # Re-trier les pics retenus par fréquence croissante pour la lisibilité
        peaks_idx = sorted(peaks_idx, key=lambda idx: freqs[idx])

        results = []
        for rank, idx in enumerate(peaks_idx, 1):
            results.append({
                "rank": rank,
                "freq": float(freqs[idx]),
                "amplitude": float(amplitude[idx])
            })

        return results
