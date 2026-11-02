# engine.py
import numpy as np
import scipy.signal as signal
import scipy.integrate as integrate
import pandas as pd
import os


class SignalGeneratorEngine:
    """Générateur de signaux temporels basé sur NumPy et SciPy."""

    WAVEFORMS = [
        "Sinus",
        "Carré",
        "Triangle",
        "Dent de scie",
        "Bruit blanc",
        "Cardinal (Sinc)",
        "Amorti (Sinus x Exp)"
    ]

    @staticmethod
    def generate_signal(waveform: str, frequency: float, amplitude: float,
                        sampling_rate: float = 1000.0, duration: float = 1.0,
                        offset: float = 0.0, phase_deg: float = 0.0):
        """Génère un vecteur temps (t) et le signal associé (y)."""
        num_samples = int(sampling_rate * duration)
        t = np.linspace(0, duration, num_samples, endpoint=False)
        phase_rad = np.radians(phase_deg)
        w = 2 * np.pi * frequency * t + phase_rad

        if waveform == "Sinus":
            y = amplitude * np.sin(w) + offset
        elif waveform == "Carré":
            y = amplitude * signal.square(w) + offset
        elif waveform == "Triangle":
            y = amplitude * signal.sawtooth(w, width=0.5) + offset
        elif waveform == "Dent de scie":
            y = amplitude * signal.sawtooth(w, width=1.0) + offset
        elif waveform == "Bruit blanc":
            y = amplitude * np.random.normal(0, 1, num_samples) + offset
        elif waveform == "Cardinal (Sinc)":
            y = amplitude * np.sinc(frequency * (t - duration / 2.0)) + offset
        elif waveform == "Amorti (Sinus x Exp)":
            y = amplitude * np.sin(w) * np.exp(-frequency * t / 2.0) + offset
        else:
            y = np.zeros(num_samples)

        return t, y


class CSVImportEngine:
    """Moteur d'importation de fichiers CSV en tableaux NumPy."""

    DELIMITERS = [
        "Virgule (,)",
        "Point-virgule (;)",
        "Tabulation (\\t)",
        "Espace ( )"
    ]

    @staticmethod
    def load_csv(file_path: str, delimiter_str: str = "Virgule (,)",
                 has_header: bool = True, time_col_idx: int = 0, signal_col_idx: int = 1,
                 default_sampling_rate: float = 1000.0):
        """Lit un fichier CSV et extrait t (temps) et y (signal amplitude)."""
        if not file_path or not os.path.exists(file_path):
            return None, None, "Fichier non trouvé"

        try:
            if "Point-virgule" in delimiter_str:
                sep = ";"
            elif "Tabulation" in delimiter_str:
                sep = "\t"
            elif "Espace" in delimiter_str:
                sep = r"\s+"
            else:
                sep = ","

            header = 0 if has_header else None
            df = pd.read_csv(file_path, sep=sep, header=header, engine='python')

            if df.empty or df.shape[1] == 0:
                return None, None, "Fichier CSV vide"

            cols = df.shape[1]
            if cols == 1:
                y = pd.to_numeric(df.iloc[:, 0], errors='coerce').fillna(0.0).to_numpy()
                n = len(y)
                t = np.linspace(0, n / default_sampling_rate, n, endpoint=False)
            else:
                t_idx = min(time_col_idx, cols - 1)
                s_idx = min(signal_col_idx, cols - 1)
                if t_idx == s_idx:
                    s_idx = (t_idx + 1) % cols

                t = pd.to_numeric(df.iloc[:, t_idx], errors='coerce').fillna(0.0).to_numpy()
                y = pd.to_numeric(df.iloc[:, s_idx], errors='coerce').fillna(0.0).to_numpy()

            return t, y, f"OK ({len(y)} points)"
        except Exception as e:
            return None, None, f"Erreur: {str(e)}"


class FilterEngine:
    """Moteur universel de filtrage numérique (Lowpass, Highpass, Bandpass, Bandstop)."""

    FILTER_TYPES = ["Butterworth", "Chebyshev", "Bessel"]

    @staticmethod
    def apply_filter(t: np.ndarray, y: np.ndarray, cutoff_freq,
                     sampling_rate: float = 1000.0, order: int = 2,
                     filter_type: str = "Butterworth", btype: str = "low") -> np.ndarray:
        """Applique un filtre numérique (low, high, bandpass, bandstop) sur un signal."""
        if t is None or y is None or len(y) == 0:
            return np.array([])

        nyquist = 0.5 * sampling_rate

        if isinstance(cutoff_freq, (list, tuple, np.ndarray)):
            normal_cutoff = [min(max(f / nyquist, 0.0001), 0.9999) for f in cutoff_freq]
            if len(normal_cutoff) >= 2 and normal_cutoff[0] >= normal_cutoff[1]:
                normal_cutoff[1] = min(normal_cutoff[0] + 0.001, 0.9999)
        else:
            normal_cutoff = min(max(float(cutoff_freq) / nyquist, 0.0001), 0.9999)

        try:
            if filter_type == "Chebyshev":
                b, a = signal.cheby1(order, rp=1, Wn=normal_cutoff, btype=btype, analog=False)
            elif filter_type == "Bessel":
                b, a = signal.bessel(order, normal_cutoff, btype=btype, analog=False)
            else:  # Butterworth
                b, a = signal.butter(order, normal_cutoff, btype=btype, analog=False)

            if len(y) > 3 * max(len(a), len(b)):
                y_filtered = signal.filtfilt(b, a, y)
            else:
                y_filtered = signal.lfilter(b, a, y)
            return y_filtered
        except Exception as e:
            print(f"Erreur lors du filtrage ({btype}): {e}")
            return np.copy(y)


class LowPassFilterEngine(FilterEngine):
    """Alias rétro-compatible pour le filtre passe-bas."""
    pass


class MathOperatorsEngine:
    """Moteur de calcul des opérateurs mathématiques sur signaux temporels."""

    LOG_BASES = ["log10 (base 10)", "ln (naturel)"]
    POWER_MODES = ["Puissance xⁿ", "Racine carrée √x"]

    @staticmethod
    def compute_derivative(t: np.ndarray, y: np.ndarray) -> np.ndarray:
        """Calcule la dérivée temporelle dy/dt avec la méthode des différences finies (np.gradient)."""
        if t is None or y is None or len(y) < 2:
            return np.array([])
        try:
            return np.gradient(y, t)
        except Exception as e:
            print(f"Erreur Dérivation: {e}")
            return np.zeros_like(y)

    @staticmethod
    def derive(t: np.ndarray, y: np.ndarray) -> np.ndarray:
        return MathOperatorsEngine.compute_derivative(t, y)

    @staticmethod
    def compute_integrator(t: np.ndarray, y: np.ndarray, initial_val: float = 0.0) -> np.ndarray:
        """Calcule l'intégrale temporelle ∫y(t)dt avec la méthode des trapèzes cumulés."""
        if t is None or y is None or len(y) == 0:
            return np.array([])
        if len(y) < 2:
            return np.full_like(y, initial_val)
        try:
            res = integrate.cumulative_trapezoid(y, t, initial=0.0)
            return res + initial_val
        except Exception as e:
            print(f"Erreur Intégration: {e}")
            return np.full_like(y, initial_val)

    @staticmethod
    def integrate_signal(t: np.ndarray, y: np.ndarray, initial_val: float = 0.0) -> np.ndarray:
        return MathOperatorsEngine.compute_integrator(t, y, initial_val)

    @staticmethod
    def compute_gain(y: np.ndarray, gain: float = 1.0, offset: float = 0.0) -> np.ndarray:
        """Applique une amplification/atténuation k*y + offset."""
        if y is None or len(y) == 0:
            return np.array([])
        return (gain * y) + offset

    @staticmethod
    def apply_gain_offset(y: np.ndarray, gain: float = 1.0, offset: float = 0.0) -> np.ndarray:
        return MathOperatorsEngine.compute_gain(y, gain, offset)

    @staticmethod
    def compute_inversion(y: np.ndarray) -> np.ndarray:
        """Calcule l'inversion 1/x."""
        if y is None or len(y) == 0:
            return np.array([])
        safe_denom = np.where(np.abs(y) > 1e-12, y, 1.0)
        return np.where(np.abs(y) > 1e-12, 1.0 / safe_denom, 0.0)

    @staticmethod
    def compute_abs(y: np.ndarray) -> np.ndarray:
        """Calcule la valeur absolue |x|."""
        if y is None or len(y) == 0:
            return np.array([])
        return np.abs(y)

    @staticmethod
    def compute_log(y: np.ndarray, base: str = "log10 (base 10)") -> np.ndarray:
        """Calcule le logarithme log10 ou ln."""
        if y is None or len(y) == 0:
            return np.array([])
        safe_y = np.maximum(y, 1e-12)
        if "ln" in base or "naturel" in base.lower():
            return np.log(safe_y)
        return np.log10(safe_y)

    @staticmethod
    def compute_exp(y: np.ndarray) -> np.ndarray:
        """Calcule l'exponentielle exp(x)."""
        if y is None or len(y) == 0:
            return np.array([])
        return np.exp(np.clip(y, -100.0, 100.0))

    @staticmethod
    def compute_power(y: np.ndarray, mode: str = "Puissance xⁿ", exponent: float = 2.0) -> np.ndarray:
        """Calcule la puissance xⁿ ou la racine carrée √x."""
        if y is None or len(y) == 0:
            return np.array([])
        if "Racine" in mode or "√" in mode:
            return np.sqrt(np.maximum(y, 0.0))
        return np.power(y, exponent)

    @staticmethod
    def compute_addition(t_a: np.ndarray, y_a: np.ndarray,
                         t_b: np.ndarray, y_b: np.ndarray,
                         coef_a: float = 1.0, coef_b: float = 1.0):
        """Additionne deux signaux A et B : k_A*A + k_B*B avec réalignement temporel automatique."""
        has_a = t_a is not None and y_a is not None and len(y_a) > 0
        has_b = t_b is not None and y_b is not None and len(y_b) > 0

        if not has_a and not has_b:
            return None, None

        if has_a and not has_b:
            return t_a, float(coef_a) * y_a

        if has_b and not has_a:
            return t_b, float(coef_b) * y_b

        y_a_val = float(coef_a) * y_a
        y_b_val = float(coef_b) * y_b

        if len(t_a) == len(t_b) and np.allclose(t_a, t_b):
            return t_a, y_a_val + y_b_val

        # Fenêtrage temporel actif adaptatif : union des grilles temporelles
        # pour capturer à 100% les transitoires haute fréquence (ex. foudre)
        if len(t_a) + len(t_b) <= 200000:
            t_combined = np.unique(np.concatenate([t_a, t_b]))
        else:
            dt_a = (t_a[-1] - t_a[0]) / (len(t_a) - 1) if len(t_a) > 1 else 1e-3
            dt_b = (t_b[-1] - t_b[0]) / (len(t_b) - 1) if len(t_b) > 1 else 1e-3
            if dt_a <= dt_b:
                t_combined = t_a
            else:
                t_combined = t_b

        y_a_interp = np.interp(t_combined, t_a, y_a_val, left=0.0, right=0.0)
        y_b_interp = np.interp(t_combined, t_b, y_b_val, left=0.0, right=0.0)

        return t_combined, y_a_interp + y_b_interp


class NoiseEngine:
    """Moteur d'injection de bruits et parasites sur signaux."""

    NOISE_TYPES = ["Bruit blanc gaussien", "Bruit impulsionnel (Spikes)", "Bruit rose (1/f)"]

    @staticmethod
    def apply_noise(t: np.ndarray, y: np.ndarray, noise_type: str = "Bruit blanc gaussien",
                    std_dev: float = 0.1, spike_prob: float = 0.02, spike_amp: float = 1.0) -> np.ndarray:
        if t is None or y is None or len(y) == 0:
            return np.array([])

        y_noisy = np.copy(y)
        num_samples = len(y)

        if "blanc" in noise_type.lower():
            noise = np.random.normal(0, std_dev, num_samples)
            y_noisy += noise

        elif "impulsionnel" in noise_type.lower() or "spike" in noise_type.lower():
            spikes = np.random.choice([0.0, 1.0, -1.0], size=num_samples, p=[1.0 - spike_prob, spike_prob / 2.0, spike_prob / 2.0])
            y_noisy += spikes * spike_amp

        elif "rose" in noise_type.lower():
            unequal_freqs = np.fft.rfftfreq(num_samples)
            unequal_freqs[0] = 1.0
            scaling = 1.0 / np.sqrt(unequal_freqs)
            noise_white = np.random.normal(0, 1, len(unequal_freqs))
            pink_fft = noise_white * scaling
            pink = np.fft.irfft(pink_fft, n=num_samples)
            pink_norm = pink / (np.std(pink) + 1e-12)
            y_noisy += pink_norm * std_dev

        return y_noisy


class SamplingConversionEngine:
    """Moteur d'échantillonnage, interpolation, extrapolation et simulation DAC."""

    INTERP_METHODS = ["Linéaire", "Spline cubique", "Plus proche voisin (Nearest)"]
    EXTRAP_MODES = ["Maintien (Hold)", "Linéaire", "Valeur nulle (Zero)"]
    DAC_RECONSTRUCTIONS = ["Bloqueur d'ordre zéro (ZOH)", "Interpolation linéaire"]
    DAC_OUTPUT_UNITS = ["Code Numérique (LSB)", "Tension Reconstruite (V)"]

    @staticmethod
    def resample_signal(t: np.ndarray, y: np.ndarray, target_fs: float = 500.0, anti_aliasing: bool = True):
        """Changement de fréquence d'échantillonnage avec option de filtrage anti-repliement."""
        if t is None or y is None or len(y) < 2:
            return t, y

        duration = t[-1] - t[0]
        if duration <= 0:
            return t, y

        num_samples = max(2, int(duration * target_fs))
        t_resampled = np.linspace(t[0], t[-1], num_samples, endpoint=False)

        current_fs = (len(y) - 1) / duration if duration > 0 else 1000.0
        y_proc = np.copy(y)

        # Filtre anti-repliement si sous-échantillonnage
        if anti_aliasing and target_fs < current_fs:
            nyq = 0.5 * current_fs
            cutoff = min(0.45 * target_fs, 0.95 * nyq)
            if cutoff < nyq and cutoff > 0:
                b, a = signal.butter(4, cutoff / nyq, btype='low')
                if len(y) > 15:
                    y_proc = signal.filtfilt(b, a, y)

        y_resampled = np.interp(t_resampled, t, y_proc)
        return t_resampled, y_resampled

    @staticmethod
    def interpolate_signal(t: np.ndarray, y: np.ndarray, target_fs: float = 1000.0,
                           method: str = "Linéaire", extrap: str = "Maintien (Hold)"):
        """Interpolation et extrapolation de signal sur une grille de temps ré-échantillonnée."""
        if t is None or y is None or len(y) < 2:
            return t, y

        duration = t[-1] - t[0]
        if duration <= 0:
            return t, y

        num_samples = max(2, int(duration * target_fs))
        t_new = np.linspace(t[0], t[-1], num_samples, endpoint=False)

        if "spline" in method.lower() or "cubique" in method.lower():
            try:
                kind = 'cubic' if len(y) >= 4 else 'linear'
                fill_val = 'extrapolate' if "linéaire" in extrap.lower() else (y[0], y[-1])
                if "zero" in extrap.lower() or "nulle" in extrap.lower():
                    fill_val = 0.0
                f_interp = interpolate.interp1d(t, y, kind=kind, bounds_error=False, fill_value=fill_val)
                y_new = f_interp(t_new)
            except Exception:
                y_new = np.interp(t_new, t, y)
        elif "voisin" in method.lower() or "nearest" in method.lower():
            idx = np.searchsorted(t, t_new, side='left')
            idx = np.clip(idx, 0, len(y) - 1)
            y_new = y[idx]
        else:  # Linéaire
            y_new = np.interp(t_new, t, y)

        return t_new, y_new

    @staticmethod
    def dac_simulation(t: np.ndarray, y: np.ndarray, dac_fs: float = 100.0,
                       bits: int = 8, vref: float = 5.0, offset_dc: float = 2.5,
                       output_unit: str = "Code Numérique (LSB)",
                       mode: str = "Bloqueur d'ordre zéro (ZOH)",
                       vref_min: float = None, vref_max: float = None):
        """Simule la conversion CAN/CNA unipolaire N-bits avec V_ref, V_DC, saturation à 0 LSB et ZOH."""
        if t is None or y is None or len(y) < 2:
            return t, y

        # Rétro-compatibilité si vref_min/vref_max sont encore présents
        if vref_min is not None and vref_max is not None:
            vref = abs(vref_max - vref_min)
            offset_dc = -min(vref_min, vref_max)

        duration = t[-1] - t[0]
        if duration <= 0:
            return t, y

        # 1. Grille temporelle d'échantillonnage à la fréquence DAC (dac_fs)
        dt_dac = 1.0 / max(float(dac_fs), 0.001)
        t_samples = np.arange(t[0], t[-1] + dt_dac * 0.5, dt_dac)
        y_samples = np.interp(t_samples, t, y)

        # 2. Ajout du décalage DC d'entrée V_DC (ex: +2.5V pour centrer un signal alternatif)
        v_in = y_samples + float(offset_dc)

        # 3. Saturation unipolaire [0, V_ref] : tout ce qui est < 0V est bloqué à 0 LSB
        safe_vref = max(float(vref), 1e-6)
        v_in_clipped = np.clip(v_in, 0.0, safe_vref)

        # 4. Quantification N-bits
        num_bits = int(min(max(bits, 1), 32))
        max_lsb = (1 << num_bits) - 1

        codes_lsb = np.round((v_in_clipped / safe_vref) * max_lsb)
        codes_lsb = np.clip(codes_lsb, 0, max_lsb)

        # Format des échantillons : Code Numérique (LSB) ou Tension Reconstruite (V)
        if "lsb" in str(output_unit).lower() or "code" in str(output_unit).lower():
            y_quant = codes_lsb
        else:
            y_quant = codes_lsb * (safe_vref / max_lsb)

        # 5. Reconstruction temporelle sur la grille continue t
        if "zoh" in str(mode).lower() or "bloqueur" in str(mode).lower() or "zéro" in str(mode).lower():
            # Bloqueur d'Ordre Zéro (ZOH) : maintien de la valeur constante jusqu'à l'échantillon suivant
            idx = np.searchsorted(t_samples, t, side='right') - 1
            idx = np.clip(idx, 0, len(y_quant) - 1)
            y_dac = y_quant[idx]
        else:
            # Interpolation linéaire entre échantillons
            y_dac = np.interp(t, t_samples, y_quant)

        return t, y_dac


class DSPFilterEngine:
    """Moteur de traitement numérique des signaux (DSP) : Moyennes fixes, glissantes et filtre médian."""

    SAMPLE_SIZES = ["2", "4", "8", "16", "32", "64", "128", "256", "512", "1024", "2048", "4096"]
    RATE_MODES = ["Fréquence (Hz)", "Période (ms)", "Période (µs)"]
    WINDOWS = ["Rectangulaire (Uniforme)", "Hann", "Hamming", "Triangle (Bartlett)"]
    OUTPUT_MODES_FIXED = ["Signal Décimé (1 point/bloc)", "Signal Continu (Bloqueur ZOH)"]

    @staticmethod
    def get_window_weights(N: int, window_type: str = "Rectangulaire (Uniforme)") -> np.ndarray:
        if N <= 1:
            return np.array([1.0])
        w_type = str(window_type).lower()
        if "hann" in w_type:
            w = np.hanning(N)
        elif "hamming" in w_type:
            w = np.hamming(N)
        elif "triangle" in w_type or "bartlett" in w_type:
            w = np.bartlett(N)
        else:
            w = np.ones(N)
        sum_w = np.sum(w)
        return w / sum_w if sum_w > 0 else np.ones(N) / float(N)

    @staticmethod
    def fixed_average(t: np.ndarray, y: np.ndarray, sample_size: int = 16,
                      sampling_rate: float = 1000.0, time_offset: float = 0.0,
                      window_type: str = "Rectangulaire (Uniforme)",
                      output_mode: str = "Signal Décimé (1 point/bloc)"):
        """Calcule la moyenne par bloc de N échantillons (disjoints)."""
        if t is None or y is None or len(y) < 2:
            return t, y

        N = int(max(sample_size, 1))

        duration = t[-1] - t[0]
        if duration <= 0:
            return t, y

        current_fs = (len(t) - 1) / duration if duration > 0 else 1000.0
        target_fs = float(sampling_rate)

        if target_fs > 0 and abs(current_fs - target_fs) / current_fs > 0.001:
            num_samples = max(2, int(np.round(duration * target_fs)))
            t_proc = np.linspace(t[0], t[-1], num_samples, endpoint=False)
            y_proc = np.interp(t_proc, t, y, left=y[0], right=y[-1])
        else:
            t_proc = t
            y_proc = np.copy(y)

        if abs(time_offset) > 1e-12:
            dt = (t_proc[-1] - t_proc[0]) / (len(t_proc) - 1) if len(t_proc) > 1 else 1.0 / max(target_fs, 0.1)
            shift_samples = int(np.round(time_offset / dt)) if dt > 0 else 0
            if shift_samples != 0:
                y_proc = np.roll(y_proc, shift_samples)

        weights = DSPFilterEngine.get_window_weights(N, window_type)
        num_blocks = len(y_proc) // N

        if num_blocks < 1:
            return t_proc, y_proc

        block_means = []
        block_times = []

        for b in range(num_blocks):
            seg_y = y_proc[b*N : (b+1)*N]
            seg_t = t_proc[b*N : (b+1)*N]
            weighted_val = np.sum(seg_y * weights)
            block_means.append(weighted_val)
            block_times.append(np.mean(seg_t))

        block_means = np.array(block_means)
        block_times = np.array(block_times)

        if "décimé" in str(output_mode).lower() or "decim" in str(output_mode).lower():
            return block_times, block_means
        else:
            # Reconstruction ZOH (continu) sur le vecteur temps t_proc d'origine
            y_zoh = np.zeros_like(y_proc)
            for b in range(num_blocks):
                y_zoh[b*N : (b+1)*N] = block_means[b]
            if len(y_proc) > num_blocks * N:
                y_zoh[num_blocks*N :] = block_means[-1]
            return t_proc, y_zoh

    @staticmethod
    def moving_average(t: np.ndarray, y: np.ndarray, sample_size: int = 16,
                       sampling_rate: float = 1000.0, time_offset: float = 0.0,
                       window_type: str = "Rectangulaire (Uniforme)"):
        """Filtre RIF à moyenne glissante de N échantillons."""
        if t is None or y is None or len(y) < 2:
            return t, y

        N = int(max(sample_size, 1))

        duration = t[-1] - t[0]
        if duration <= 0:
            return t, y

        current_fs = (len(t) - 1) / duration if duration > 0 else 1000.0
        target_fs = float(sampling_rate)

        if target_fs > 0 and abs(current_fs - target_fs) / current_fs > 0.001:
            num_samples = max(2, int(np.round(duration * target_fs)))
            t_proc = np.linspace(t[0], t[-1], num_samples, endpoint=False)
            y_proc = np.interp(t_proc, t, y, left=y[0], right=y[-1])
        else:
            t_proc = t
            y_proc = np.copy(y)

        if abs(time_offset) > 1e-12:
            dt = (t_proc[-1] - t_proc[0]) / (len(t_proc) - 1) if len(t_proc) > 1 else 1.0 / max(target_fs, 0.1)
            shift_samples = int(np.round(time_offset / dt)) if dt > 0 else 0
            if shift_samples != 0:
                y_proc = np.roll(y_proc, shift_samples)

        weights = DSPFilterEngine.get_window_weights(N, window_type)
        y_avg = np.convolve(y_proc, weights, mode='same')
        return t_proc, y_avg

    KERNEL_SIZES_MEDIAN = ["3", "5", "7", "9", "11", "15", "21", "31", "51", "101", "201", "501"]

    @staticmethod
    def median_filter(t: np.ndarray, y: np.ndarray, kernel_size: int = 5,
                      sampling_rate: float = 1000.0, time_offset: float = 0.0):
        """Filtre médian glissant non-linéaire sur N échantillons (N impair)."""
        if t is None or y is None or len(y) < 2:
            return t, y

        N = int(max(kernel_size, 1))
        if N % 2 == 0:
            N += 1

        duration = t[-1] - t[0]
        if duration <= 0:
            return t, y

        current_fs = (len(t) - 1) / duration if duration > 0 else 1000.0
        target_fs = float(sampling_rate)

        if target_fs > 0 and abs(current_fs - target_fs) / current_fs > 0.001:
            num_samples = max(2, int(np.round(duration * target_fs)))
            t_proc = np.linspace(t[0], t[-1], num_samples, endpoint=False)
            y_proc = np.interp(t_proc, t, y, left=y[0], right=y[-1])
        else:
            t_proc = t
            y_proc = np.copy(y)

        if abs(time_offset) > 1e-12:
            dt = (t_proc[-1] - t_proc[0]) / (len(t_proc) - 1) if len(t_proc) > 1 else 1.0 / max(target_fs, 0.1)
            shift_samples = int(np.round(time_offset / dt)) if dt > 0 else 0
            if shift_samples != 0:
                y_proc = np.roll(y_proc, shift_samples)

        try:
            y_med = signal.medfilt(y_proc, kernel_size=N)
        except Exception:
            import scipy.ndimage as ndimage
            y_med = ndimage.median_filter(y_proc, size=N)

        return t_proc, y_med

class FFTAnalysisEngine:
    """Moteur de calcul de Transformée de Fourier Rapide (FFT)."""

    WINDOW_TYPES = ["Hann", "Hamming", "Blackman", "Flattop", "Kaiser", "Rectangulaire"]
    FFT_SIZES = ["128", "256", "512", "1024", "2048", "4096", "8192", "Taille complète du signal"]
    SPECTRUM_UNITS = ["Amplitude (V)", "Décibels (dB)"]

    @staticmethod
    def compute_fft(t: np.ndarray, y: np.ndarray, window_type: str = "Rectangulaire",
                    n_fft_str: str = "1024", unit: str = "Amplitude (V)"):
        """
        Calcule la FFT monolatérale (fréquences positives) d'un signal temporel.
        Retourne : freqs (Hz), magnitude (V ou dB)
        """
        if t is None or y is None or len(y) == 0:
            return np.array([]), np.array([])

        N = len(y)
        dt = (t[-1] - t[0]) / (N - 1) if N > 1 else 0.001
        fs = 1.0 / dt if dt > 0 else 1000.0

        if n_fft_str == "Taille complète du signal" or not n_fft_str.isdigit():
            n_fft = N
        else:
            n_fft = int(n_fft_str)

        fft_size = min(n_fft, N) if n_fft > 0 else N
        segment = y[:fft_size]
        L = len(segment)

        if window_type == "Hann":
            win = np.hanning(L)
        elif window_type == "Hamming":
            win = np.hamming(L)
        elif window_type == "Blackman":
            win = np.blackman(L)
        elif window_type == "Flattop":
            win = signal.windows.flattop(L) if hasattr(signal, "windows") and hasattr(signal.windows, "flattop") else np.hanning(L)
        elif window_type == "Kaiser":
            win = np.kaiser(L, beta=14)
        else:
            win = np.ones(L)

        windowed_signal = segment * win
        win_sum = np.sum(win)
        scale_factor = 2.0 / win_sum if win_sum > 0 else 2.0 / L

        fft_vals = np.fft.rfft(windowed_signal, n=fft_size)
        freqs = np.fft.rfftfreq(fft_size, d=1.0/fs)

        magnitude = np.abs(fft_vals) * scale_factor
        if len(magnitude) > 0:
            magnitude[0] /= 2.0

        if "dB" in unit:
            magnitude = 20.0 * np.log10(np.maximum(magnitude, 1e-9))

        return freqs, magnitude


class CalculationEngine:
    """Moteur global de traitement."""
    def __init__(self):
        self.signal_engine = SignalGeneratorEngine()
        self.csv_engine = CSVImportEngine()
        self.filter_engine = FilterEngine()
        self.math_engine = MathOperatorsEngine()
        self.noise_engine = NoiseEngine()
        self.sampling_engine = SamplingConversionEngine()
        self.dsp_engine = DSPFilterEngine()
        self.fft_engine = FFTAnalysisEngine()
        self.do160_engine = DO160Engine()
        self.thd_engine = THDAnalysisEngine()


# Append DO160Engine to engine.py
import scipy.optimize as opt

class DO160Engine:
    """Moteur de génération des formes d'ondes normatives RTCA DO-160G Section 22 (Effets indirects de la foudre)."""

    DOUBLE_EXP_PRESETS = [
        "WF1 (6.4 µs / 69 µs - Courant)",
        "WF2 (0.1 µs / 6.4 µs - Tension)",
        "WF4 (6.4 µs / 69 µs - Tension)",
        "WF5A (40 µs / 120 µs - Forte énergie)",
        "WF5B (50 µs / 500 µs - Longue durée)",
        "Personnalisé"
    ]

    DAMPED_SINE_PRESETS = [
        "WF3 - 1 MHz (Sinus Amorti)",
        "WF3 - 10 MHz (Sinus Amorti)",
        "Personnalisé"
    ]

    T2_MODES = [
        "50% Amplitude (Standard)",
        "0% Amplitude / Zero (WF2)"
    ]

    LEVELS_DO160 = [
        "Niveau 1 (50V / 100A)",
        "Niveau 2 (125V / 250A)",
        "Niveau 3 (300V / 600A)",
        "Niveau 4 (750V / 1500A)",
        "Niveau 5 (1600V / 3000A)",
        "Personnalisé"
    ]

    LEVEL_PEAKS_V = {
        "Niveau 1 (50V / 100A)": 50.0,
        "Niveau 2 (125V / 250A)": 125.0,
        "Niveau 3 (300V / 600A)": 300.0,
        "Niveau 4 (750V / 1500A)": 750.0,
        "Niveau 5 (1600V / 3000A)": 1600.0,
    }

    LEVEL_PEAKS_WF3_V = {
        "Niveau 1 (50V / 100A)": 100.0,
        "Niveau 2 (125V / 250A)": 250.0,
        "Niveau 3 (300V / 600A)": 600.0,
        "Niveau 4 (750V / 1500A)": 1500.0,
        "Niveau 5 (1600V / 3000A)": 3200.0,
    }

    @staticmethod
    def get_double_exp_coefficients(t1_s: float, t2_s: float, t2_mode: str = "50% Amplitude (Standard)"):
        """Calcule alpha, beta et k pour y(t) = k*(exp(-alpha*t) - exp(-beta*t))."""
        t1 = max(float(t1_s), 1e-10)
        t2 = max(float(t2_s), t1 * 1.05)
        is_zero_mode = ("0% Amplitude" in str(t2_mode) or "Zero" in str(t2_mode) or str(t2_mode).startswith("0%")) and not ("50%" in str(t2_mode))
        target = 0.01 if is_zero_mode else 0.50

        def func(log_x):
            x = np.exp(log_x)
            if x <= 1.0001:
                return 1e6
            a = np.log(x) / (t1 * (x - 1.0))
            b = x * a
            val_peak = np.exp(-a * t1) - np.exp(-b * t1)
            val_t2 = np.exp(-a * t2) - np.exp(-b * t2)
            return (val_t2 / val_peak) - target

        try:
            res = opt.root_scalar(func, bracket=[0.0001, 25.0], method='brentq')
            x = np.exp(res.root)
            a = np.log(x) / (t1 * (x - 1.0))
            b = x * a
            k = 1.0 / max(np.exp(-a * t1) - np.exp(-b * t1), 1e-12)
            return a, b, k
        except Exception:
            b = 1.0 / t1
            a = 1.0 / t2
            k = 1.0
            return a, b, k

    @staticmethod
    def generate_double_exponential(t1_us: float = 6.4, t2_us: float = 69.0,
                                   v_peak: float = 300.0, t2_mode: str = "50% Amplitude (Standard)",
                                   t_offset_us: float = 1.0, sampling_rate_mhz: float = 50.0,
                                   duration_us: float = 200.0):
        """Génère un signal temporel double exponentielle DO-160."""
        t1_s = max(float(t1_us), 0.01) * 1e-6
        t2_s = max(float(t2_us), t1_us * 1.05) * 1e-6
        t_offset_s = max(float(t_offset_us), 0.0) * 1e-6
        fs_hz = max(float(sampling_rate_mhz), 0.1) * 1e6
        dur_s = max(float(duration_us), 1.0) * 1e-6

        num_samples = max(2, int(np.round(dur_s * fs_hz)))
        t = np.linspace(t_offset_s, t_offset_s + dur_s, num_samples, endpoint=False)

        a, b, k = DO160Engine.get_double_exp_coefficients(t1_s, t2_s, t2_mode)
        t_rel = t - t_offset_s

        y = float(v_peak) * k * (np.exp(-a * t_rel) - np.exp(-b * t_rel))
        return t, y

    @staticmethod
    def generate_damped_sine(freq_mhz: float = 1.0, v_peak: float = 600.0,
                             r5_percent: float = 50.0, phase_deg: float = 0.0,
                             t_offset_us: float = 1.0, sampling_rate_mhz: float = 100.0,
                             duration_us: float = 10.0):
        """Génère un signal temporel sinus amorti DO-160 (Waveform 3)."""
        freq_hz = max(float(freq_mhz), 0.001) * 1e6
        t_offset_s = max(float(t_offset_us), 0.0) * 1e-6
        fs_hz = max(float(sampling_rate_mhz), 0.1) * 1e6
        dur_s = max(float(duration_us), 0.1) * 1e-6

        num_samples = max(2, int(np.round(dur_s * fs_hz)))
        t = np.linspace(t_offset_s, t_offset_s + dur_s, num_samples, endpoint=False)

        r5 = max(min(float(r5_percent) / 100.0, 0.99), 0.01)
        sigma = - (freq_hz / 4.0) * np.log(r5)

        w = 2 * np.pi * freq_hz
        phase_rad = np.radians(phase_deg)

        # Calcul exact du facteur de normalisation pour que l'amplitude crête soit exactement v_peak
        t_peak = np.arctan(w / max(sigma, 1e-9)) / w if sigma > 0 else 1.0 / (4.0 * freq_hz)
        k_norm = 1.0 / max(np.exp(-sigma * t_peak) * np.abs(np.sin(w * t_peak + phase_rad)), 1e-12)

        t_rel = t - t_offset_s
        y = float(v_peak) * k_norm * np.exp(-sigma * t_rel) * np.sin(w * t_rel + phase_rad)
        return t, y


class THDAnalysisEngine:
    """Moteur de calcul du Taux de Distorsion Harmonique (THD) et du spectre des harmoniques."""

    FUNDAMENTAL_MODES = ["Saisie Manuelle", "Détection Automatique"]
    DISPLAY_UNITS = ["% de la Fondamentale", "Amplitude (V)", "Décibels (dB)"]
    WINDOW_TYPES = ["Rectangulaire", "Hann", "Hamming", "Blackman", "Flattop"]

    @staticmethod
    def compute_thd(t: np.ndarray, y: np.ndarray,
                    fundamental_mode: str = "Saisie Manuelle",
                    fundamental_freq: float = 50.0,
                    max_harmonics: int = 10,
                    display_unit: str = "% de la Fondamentale",
                    window_type: str = "Rectangulaire"):
        """
        Calcule le THD % et extrait l'amplitude jusqu'à N harmoniques (2 <= N <= 50).
        Retourne : (harm_orders, harm_freqs, harm_disp, thd_percent, f0, v1_amp, harm_v_raw)
        """
        if t is None or y is None or len(y) < 4:
            empty = np.array([])
            return empty, empty, empty, 0.0, 0.0, 0.0, empty

        N_samples = len(y)
        dt = (t[-1] - t[0]) / (N_samples - 1) if N_samples > 1 else 0.001
        fs = 1.0 / dt if dt > 0 else 1000.0

        if window_type == "Hann":
            win = np.hanning(N_samples)
        elif window_type == "Hamming":
            win = np.hamming(N_samples)
        elif window_type == "Blackman":
            win = np.blackman(N_samples)
        elif window_type == "Flattop":
            win = signal.windows.flattop(N_samples) if hasattr(signal, "windows") and hasattr(signal.windows, "flattop") else np.hanning(N_samples)
        else:
            win = np.ones(N_samples)

        # Soustraction de la composante continue (DC) pour éviter la fuite spectrale à basse fréquence
        y_ac = y - np.mean(y)

        win_sum = np.sum(win)
        scale_factor = 2.0 / win_sum if win_sum > 0 else 2.0 / N_samples

        fft_vals = np.fft.rfft(y_ac * win)
        freqs = np.fft.rfftfreq(N_samples, d=1.0/fs)
        magnitude = np.abs(fft_vals) * scale_factor

        if "auto" in fundamental_mode.lower():
            fft_vals = np.fft.rfft(y_ac * win)
            freqs = np.fft.rfftfreq(N_samples, d=1.0/fs)
            magnitude = np.abs(fft_vals) * scale_factor
            df = freqs[1] - freqs[0] if len(freqs) > 1 else 1.0
            
            mask = freqs > 0.5
            if np.any(mask) and np.max(magnitude[mask]) > 1e-6:
                m = np.argmax(magnitude[mask])
                m_idx = np.where(mask)[0][m]
                if 0 < m_idx < len(magnitude) - 1:
                    y1, y2, y3 = np.log(np.maximum(magnitude[m_idx-1:m_idx+2], 1e-12))
                    denom = (2 * y2 - y1 - y3)
                    if abs(denom) > 1e-12:
                        delta = 0.5 * (y3 - y1) / denom
                        f0 = float((m_idx + delta) * df)
                    else:
                        f0 = float(freqs[m_idx])
                else:
                    f0 = float(freqs[m_idx])
            else:
                f0 = float(max(fundamental_freq, 0.1))
        else:
            f0 = float(max(fundamental_freq, 0.1))

        num_h = int(min(max(max_harmonics, 2), 50))
        harm_orders = np.arange(1, num_h + 1)
        harm_freqs = harm_orders * f0
        harm_v_raw = []

        f_nyquist = fs / 2.0

        for k, fk in zip(harm_orders, harm_freqs):
            if fk >= f_nyquist:
                harm_v_raw.append(0.0)
            else:
                val_dtft = np.sum(y_ac * win * np.exp(-1j * 2 * np.pi * fk * t))
                mag = float(np.abs(val_dtft) * scale_factor)
                harm_v_raw.append(mag)

        harm_freqs = np.array(harm_freqs)
        harm_v_raw = np.array(harm_v_raw)

        v1_amp = float(harm_v_raw[0])
        v_harm_sum_sq = float(np.sum(harm_v_raw[1:] ** 2))

        if v1_amp > 1e-12:
            thd_percent = (float(np.sqrt(v_harm_sum_sq)) / v1_amp) * 100.0
        else:
            thd_percent = 0.0

        if "%" in display_unit:
            harm_disp = (harm_v_raw / v1_amp * 100.0) if v1_amp > 1e-12 else np.zeros_like(harm_v_raw)
        elif "dB" in display_unit:
            if v1_amp > 1e-12:
                harm_disp = 20.0 * np.log10(np.maximum(harm_v_raw / v1_amp, 1e-6))
            else:
                harm_disp = 20.0 * np.log10(np.maximum(harm_v_raw, 1e-6))
        else:
            harm_disp = harm_v_raw

        return harm_orders, harm_freqs, harm_disp, thd_percent, f0, v1_amp, harm_v_raw
