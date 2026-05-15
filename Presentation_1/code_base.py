import os
import json
import math
import time
import threading
import queue
import enum
import hashlib
import wave
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from collections import deque

import numpy as np

try:
    import sounddevice as sd
except Exception:
    sd = None

try:
    from scipy import signal as sp_signal
except Exception:
    sp_signal = None

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn


# REQ-ARCH-001, REQ-ERR-001; EP-API/EP-AUD
class State(enum.Enum):
    BOOT = "BOOT"
    IDLE = "IDLE"
    MEASURING = "MEASURING"
    CALIBRATING = "CALIBRATING"
    ERROR = "ERROR"


@dataclass
class MeterConfig:
    """Konfiguration des SPL-Meters.

    Anforderungen: REQ-PERF-001/002, REQ-FUNC-004/006
    Epic/Features: EP-AUD (FEAT-AUD-001/004/005), EP-SIG (FEAT-SIG-003/005/006/007), EP-API (FEAT-API-005)
    """
    samplerate: int = 48000
    blocksize: int = 2048
    device: Optional[str] = None
    channels: int = 1
    weighting: str = "A"
    time_weighting: str = "F"
    ref_pa: float = 20e-6
    cal_offset_db: float = 0.0
    spec: str = "none"


@dataclass
class Metrics:
    """Laufende Messgrößen und Zähler.

    Anforderungen: REQ-FUNC-002/003/004, REQ-ERR-001
    Epic/Features: EP-SIG (FEAT-SIG-002/005/006), EP-AUD (FEAT-AUD-002/004)
    """
    timestamp: float = 0.0
    inst_db: float = float("nan")
    fast_db: float = float("nan")
    slow_db: float = float("nan")
    leq_db: float = float("nan")
    clipped_blocks: int = 0
    dropped_blocks: int = 0
    underruns: int = 0
    processed_blocks: int = 0
    uptime_s: float = 0.0
    bands: Optional[dict] = None
    recording: bool = False


class Ring:
    """Lock-freier Ringpuffer für Audio-Blöcke.

    Anforderungen: REQ-FUNC-001
    Epic/Feature: EP-AUD (FEAT-AUD-003)
    """
    def __init__(self, max_blocks: int = 16):
        """Erzeugt einen begrenzten Puffer mit max_blocks Kapazität."""
        self.q = queue.Queue(max_blocks)

    def push(self, arr: np.ndarray) -> bool:
        """Lege Block non-blocking ab; gibt False bei vollem Puffer zurück."""
        try:
            self.q.put_nowait(arr)
            return True
        except queue.Full:
            return False

    def pop(self, timeout: float = 0.5):
        """Hole nächsten Block; None bei Timeout."""
        try:
            return self.q.get(timeout=timeout)
        except queue.Empty:
            return None

    def clear(self):
        """Leere den Puffer vollständig."""
        while not self.q.empty():
            try:
                self.q.get_nowait()
            except Exception:
                break


# REQ-FUNC-004; EP-SIG (FEAT-SIG-003)
def a_weighting_mag(f: np.ndarray) -> np.ndarray:
    """A-Bewertungsmagnitudenverlauf im Frequenzbereich.

    Fallback zur IIR-A-Bewertung; dient auch zur Spektralintegration.
    """
    f = np.maximum(f, 1e-12)
    Ra = (12200.0 ** 2 * f ** 4) / (
        (f ** 2 + 20.6 ** 2)
        * np.sqrt((f ** 2 + 107.7 ** 2) * (f ** 2 + 737.9 ** 2))
        * (f ** 2 + 12200.0 ** 2)
    )
    A = 2.0 + 20.0 * np.log10(Ra)
    return np.power(10.0, A / 20.0)


# REQ-FUNC-002/004; EP-SIG (FEAT-SIG-001/002/003/004)
def weighted_rms(x: np.ndarray, fs: int, mode: str) -> float:
    """Blockweises RMS mit wählbarer A/Z-Bewertung via rFFT.

    Dient als Referenz/Backup, falls IIR nicht verfügbar ist.
    """
    N = len(x)
    X = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(N, 1.0 / fs)
    if mode == "A":
        W = a_weighting_mag(freqs)
    else:
        W = np.ones_like(freqs)
    S = (np.abs(X) ** 2) * (W ** 2)
    if N % 2 == 0:
        if S.size > 2:
            S[1:-1] *= 2.0
    else:
        if S.size > 1:
            S[1:] *= 2.0
    energy = np.sum(S) / (N ** 2)
    return float(np.sqrt(energy))


# REQ-FUNC-002/005; EP-SIG/EP-SPC (Hilfsfunktion)
def rfft_onesided(x: np.ndarray, fs: int):
    """Einseitiges Leistungs­spektrum S sowie Frequenzachse liefern.

    Unterstützt SPL/Leq und Bandpegelberechnung.
    """
    N = len(x)
    X = np.fft.rfft(x)
    S = (np.abs(X) ** 2)
    if N % 2 == 0:
        if S.size > 2:
            S[1:-1] *= 2.0
    else:
        if S.size > 1:
            S[1:] *= 2.0
    freqs = np.fft.rfftfreq(N, 1.0 / fs)
    return S, freqs, N


# REQ-FUNC-005; EP-SPC (FEAT-SPC-001)
def band_definitions(mode: str):
    """Bandmitten und -grenzen (Oktav/Terz) definieren.

    Liefert Liste (fc, fl, fu).
    """
    if mode == "octave":
        centers = [31.5, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
        k = 0.5
    elif mode == "terz":
        centers = [
            25, 31.5, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630,
            800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000, 10000,
            12500, 16000
        ]
        k = 1.0/6.0
    else:
        return []
    bands = []
    for fc in centers:
        fl = fc / (2 ** k)
        fu = fc * (2 ** k)
        bands.append((fc, fl, fu))
    return bands


# REQ-FUNC-005; EP-SPC (FEAT-SPC-002)
def compute_band_levels_db(S: np.ndarray, freqs: np.ndarray, N: int, ref2: float, mode: str):
    """Bandpegel in dB aus dem Spektrum integrieren.

    Gibt Dict fc→dB zurück; None falls keine Bänder.
    """
    bands = band_definitions(mode)
    if not bands:
        return None
    out = {}
    for fc, fl, fu in bands:
        m = (freqs >= fl) & (freqs < fu)
        if not np.any(m):
            out[str(fc)] = None
            continue
        e = float(np.sum(S[m]) / (N ** 2))
        if e <= 0.0:
            out[str(fc)] = None
        else:
            out[str(fc)] = 10.0 * math.log10(e / ref2)
    return out


# REQ-FUNC-004, REQ-STD-001; EP-SIG (FEAT-SIG-003)
def design_a_weighting_sos(fs: int):
    """Entwirft A-Bewertung als IIR (SOS), skaliert auf 0 dB @ 1 kHz.

    Nutzt SciPy (bilinear zpk→sos). Fallback: a_weighting_mag().
    """
    if sp_signal is None:
        return None
    f1 = 20.598997
    f2 = 107.65265
    f3 = 737.86223
    f4 = 12194.217
    z = [0.0, 0.0, 0.0, 0.0]
    p = [
        -2.0 * np.pi * f1,
        -2.0 * np.pi * f1,
        -2.0 * np.pi * f4,
        -2.0 * np.pi * f4,
        -2.0 * np.pi * f2,
        -2.0 * np.pi * f3,
    ]
    k = (2.0 * np.pi * f4) ** 2
    zz, pp, kk = sp_signal.bilinear_zpk(z, p, k, fs=fs)
    sos = sp_signal.zpk2sos(zz, pp, kk)
    _, h = sp_signal.sosfreqz(sos, worN=[1000], fs=fs)
    g = 1.0 / float(np.abs(h[0])) if np.abs(h[0]) != 0 else 1.0
    sos[0, 0:3] *= g
    return sos


class SPLMeter:
    """Hauptkomponente: Audioaufnahme, Signalverarbeitung, Kalibrierung, Export.

    Anforderungen: REQ-FUNC-001..008, REQ-PERF-001/002, REQ-QUAL-001, REQ-ERR-001
    Epics: EP-AUD, EP-SIG, EP-SPC, EP-CAL, EP-EXP, optional EP-REC
    """
    def __init__(self, config: MeterConfig):
        """Initialisiert Zustände, Puffer und Aufnahme/Recording-Strukturen.

        REQ-ARCH-001; EP-AUD (FEAT-AUD-003), EP-REC (FEAT-REC-001/002)
        """
        self.config = config
        self.state = State.IDLE
        self.metrics = Metrics()
        self._lock = threading.Lock()
        self._ring = Ring(16)
        self._stream = None
        self._consumer = None
        self._running = threading.Event()
        self._t0 = time.time()
        self._fast_e = 0.0
        self._slow_e = 0.0
        self._leq_e = 0.0
        self._leq_t = 0.0
        self._sos = None
        self._zi = None
        self._use_iir = False
        self._hist_blocks = deque()
        self._hist_samples = 0
        self._hist_max_s = 2.0
        self._rec_enabled = False
        self._rec_queue = queue.Queue(64)
        self._rec_thread = None
        self._rec_file = None
        self._rec_path = None

    def _prepare_weighting(self):
        """Bereitet A/Z-Bewertung vor; bevorzugt IIR-A (SOS) bei Verfügbarkeit.

        REQ-FUNC-004/STD-001; EP-SIG (FEAT-SIG-003/004)
        """
        if self.config.weighting == "A" and sp_signal is not None:
            self._sos = design_a_weighting_sos(self.config.samplerate)
            if self._sos is not None:
                try:
                    self._zi = sp_signal.sosfilt_zi(self._sos)
                except Exception:
                    self._zi = np.zeros((self._sos.shape[0], 2), dtype=np.float64)
                self._use_iir = True
                return
        self._sos = None
        self._zi = None
        self._use_iir = False

    def _audio_callback(self, indata, frames, tinfo, status):
        """Audio-Producer-Callback: schreibt int32-Blöcke in Ringpuffer.

        REQ-FUNC-001/QUAL-001; EP-AUD (FEAT-AUD-002/003)
        """
        if getattr(status, "input_underflow", False):
            with self._lock:
                self.metrics.underruns += 1
        block = indata.copy().reshape(-1)
        clipped = bool(np.any(block == np.int32(2147483647)) or np.any(block == np.int32(-2147483648)))
        ok = self._ring.push(block)
        if not ok:
            with self._lock:
                self.metrics.dropped_blocks += 1
        if clipped:
            with self._lock:
                self.metrics.clipped_blocks += 1
        if self._rec_enabled:
            try:
                self._rec_queue.put_nowait(block.copy())
            except queue.Full:
                pass

    def start(self):
        """Startet die Audio-Pipeline und den Consumer-Thread.

        REQ-FUNC-001; EP-AUD (FEAT-AUD-004/001)
        """
        if self.state == State.MEASURING:
            return
        if sd is None:
            self.state = State.ERROR
            return
        self._ring.clear()
        self._running.set()
        self._t0 = time.time()
        self._fast_e = 0.0
        self._slow_e = 0.0
        self._leq_e = 0.0
        self._leq_t = 0.0
        self._prepare_weighting()
        dtype = "int32"
        self._stream = sd.InputStream(
            samplerate=self.config.samplerate,
            blocksize=self.config.blocksize,
            dtype=dtype,
            channels=self.config.channels,
            callback=self._audio_callback,
            device=self.config.device,
        )
        self._stream.start()
        self._consumer = threading.Thread(target=self._consumer_loop, daemon=True)
        self._consumer.start()
        self.state = State.MEASURING

    def stop(self):
        """Stoppt die Audio-Pipeline sicher.

        REQ-FUNC-001; EP-AUD (FEAT-AUD-004)
        """
        self._running.clear()
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        self.state = State.IDLE

    def _consumer_loop(self):
        """Consumer: Rechnet A/Z‑Bewertung, F/S‑Zeitbewertung, Leq und Bänder.

        REQ-FUNC-002/003/004/005; EP-SIG (FEAT-SIG-002/005/006/007), EP-SPC (FEAT-SPC-002)
        """
        while self._running.is_set():
            block = self._ring.pop(timeout=0.5)
            if block is None:
                continue
            x = block.astype(np.float32) / 2147483648.0
            self._hist_blocks.append(x)
            self._hist_samples += len(x)
            max_samples = int(self.config.samplerate * self._hist_max_s)
            while self._hist_samples > max_samples and self._hist_blocks:
                old = self._hist_blocks.popleft()
                self._hist_samples -= len(old)
            if self.config.weighting == "A" and self._use_iir and sp_signal is not None and self._sos is not None:
                y, self._zi = sp_signal.sosfilt(self._sos, x, zi=self._zi)
                e = float(np.mean(y * y))
            elif self.config.weighting == "A":
                S_w, freqs_w, N_w = rfft_onesided(x, self.config.samplerate)
                W = a_weighting_mag(freqs_w)
                e = float(np.sum(S_w * (W ** 2)) / (N_w ** 2))
            else:
                e = float(np.mean(x * x))
            dt = len(x) / float(self.config.samplerate)
            af = math.exp(-dt / 0.125)
            aS = math.exp(-dt / 1.0)
            self._fast_e = af * self._fast_e + (1.0 - af) * e
            self._slow_e = aS * self._slow_e + (1.0 - aS) * e
            self._leq_e += e * dt
            self._leq_t += dt
            ref2 = self.config.ref_pa * self.config.ref_pa
            inst_db = -float("inf") if e <= 0.0 else 10.0 * math.log10(e / ref2) + self.config.cal_offset_db
            fast_db = -float("inf") if self._fast_e <= 0.0 else 10.0 * math.log10(self._fast_e / ref2) + self.config.cal_offset_db
            slow_db = -float("inf") if self._slow_e <= 0.0 else 10.0 * math.log10(self._slow_e / ref2) + self.config.cal_offset_db
            leq_db = -float("inf") if self._leq_t <= 0.0 or self._leq_e <= 0.0 else 10.0 * math.log10((self._leq_e / self._leq_t) / ref2) + self.config.cal_offset_db
            bands = None
            if self.config.spec in ("octave", "terz"):
                S_b, freqs_b, N_b = rfft_onesided(x, self.config.samplerate)
                bands = compute_band_levels_db(S_b, freqs_b, N_b, ref2, self.config.spec)
            with self._lock:
                self.metrics.inst_db = inst_db
                self.metrics.fast_db = fast_db
                self.metrics.slow_db = slow_db
                self.metrics.leq_db = leq_db
                self.metrics.processed_blocks += 1
                self.metrics.timestamp = time.time()
                self.metrics.uptime_s = self.metrics.timestamp - self._t0
                self.metrics.bands = bands
                self.metrics.recording = self._rec_enabled

    def set_config(self, weighting=None, time_weighting=None, samplerate=None, blocksize=None, device=None):
        """Setzt Konfiguration; stream-neustart bei SR/Block/Device-Änderung.

        REQ-FUNC-006; EP-API (FEAT-API-005)
        """
        need_restart = False
        if weighting:
            self.config.weighting = weighting
            self._prepare_weighting()
        if time_weighting:
            self.config.time_weighting = time_weighting
        if samplerate and samplerate != self.config.samplerate:
            self.config.samplerate = samplerate
            need_restart = True
        if blocksize and blocksize != self.config.blocksize:
            self.config.blocksize = blocksize
            need_restart = True
        if device is not None and device != self.config.device:
            self.config.device = device
            need_restart = True
        if need_restart and self.state == State.MEASURING:
            self.stop()
            self.start()

    def read_metrics(self):
        """Gibt aktuelle Kennwerte und Zähler als JSON-geeignetes Dict zurück.

        REQ-FUNC-006/007; EP-API (FEAT-API-003)
        """
        with self._lock:
            m = self.metrics
            def safe(v):
                try:
                    return float(v) if math.isfinite(float(v)) else None
                except Exception:
                    return None
            return {
                "timestamp": m.timestamp,
                "inst_db": safe(m.inst_db),
                "fast_db": safe(m.fast_db),
                "slow_db": safe(m.slow_db),
                "leq_db": safe(m.leq_db),
                "clipped_blocks": m.clipped_blocks,
                "dropped_blocks": m.dropped_blocks,
                "underruns": m.underruns,
                "processed_blocks": m.processed_blocks,
                "uptime_s": m.uptime_s,
                "state": self.state.value,
                "weighting": self.config.weighting,
                "time_weighting": self.config.time_weighting,
                "samplerate": self.config.samplerate,
                "blocksize": self.config.blocksize,
                "device": self.config.device,
                "spec": self.config.spec,
                "bands": m.bands,
                "recording": m.recording,
            }

    def calibrate_set_offset(self, reference_db: float) -> bool:
        """Setzt Kalibrier-Offset so, dass gemessener Leq/Fast auf Referenz passt.

        REQ-FUNC-008; EP-CAL (FEAT-CAL-002/005)
        """
        m = self.read_metrics()
        leq = m.get("leq_db")
        fast = m.get("fast_db")
        cur = leq if (leq is not None) else fast
        if cur is None:
            return False
        self.config.cal_offset_db += (reference_db - float(cur))
        return True

    def _recent_window(self, seconds: float) -> Optional[np.ndarray]:
        """Liefert die letzten Sekunden Audiodaten als Float32-Fenster.

        Hilfsfunktion für Kalibratordetektion.
        """
        n = int(self.config.samplerate * max(0.0, seconds))
        if n <= 0 or self._hist_samples <= 0:
            return None
        want = min(n, self._hist_samples)
        acc = []
        got = 0
        for arr in reversed(self._hist_blocks):
            if got >= want:
                break
            take = min(len(arr), want - got)
            if take == len(arr):
                acc.append(arr)
            else:
                acc.append(arr[-take:])
            got += take
        if got <= 0:
            return None
        acc.reverse()
        buf = np.concatenate(acc)
        if len(buf) > want:
            buf = buf[-want:]
        return buf

    def detect_cal_tone_1khz(self, window_s: float = 1.0):
        """Detektiert 1 kHz-Kalibratorton im Fenster, schätzt Pegel und Güte.

        REQ-FUNC-008; EP-CAL (FEAT-CAL-001)
        """
        seg = self._recent_window(window_s)
        if seg is None or len(seg) < int(0.25 * self.config.samplerate):
            return {"present": False, "db": None, "ratio": 0.0, "n": 0}
        S, freqs, N = rfft_onesided(seg, self.config.samplerate)
        k = int(np.argmin(np.abs(freqs - 1000.0)))
        k0 = max(0, k - 1)
        k1 = min(len(S), k + 2)
        e1k = float(np.sum(S[k0:k1]) / (N ** 2))
        etot = float(np.sum(S) / (N ** 2))
        ratio = (e1k / etot) if etot > 0 else 0.0
        ref2 = self.config.ref_pa * self.config.ref_pa
        db = None if e1k <= 0.0 else 10.0 * math.log10(e1k / ref2) + self.config.cal_offset_db
        return {"present": bool(ratio > 0.5), "db": db, "ratio": ratio, "n": int(N)}

    def start_recording_wav(self, path: Optional[Path] = None) -> str:
        """Startet optionale WAV-Aufnahme (32-bit PCM, LE) in separatem Thread.

        REQ-FUNC-010; EP-REC (FEAT-REC-001/002)
        """
        if self._rec_enabled:
            return str(self._rec_path) if self._rec_path else ""
        if path is None:
            d = Path("records")
            d.mkdir(parents=True, exist_ok=True)
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            path = d / f"rec_{ts}.wav"
        self._rec_file = wave.open(str(path), "wb")
        self._rec_file.setnchannels(self.config.channels)
        self._rec_file.setsampwidth(4)
        self._rec_file.setframerate(self.config.samplerate)
        self._rec_path = path
        self._rec_enabled = True
        self._rec_thread = threading.Thread(target=self._recording_consumer, daemon=True)
        self._rec_thread.start()
        with self._lock:
            self.metrics.recording = True
        return str(path)

    def _recording_consumer(self):
        """Consumer-Thread: schreibt Pufferblöcke streaming-fähig in WAV-Datei.

        REQ-FUNC-010; EP-REC (FEAT-REC-002/003)
        """
        while self._rec_enabled or not self._rec_queue.empty():
            try:
                blk = self._rec_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                self._rec_file.writeframes(blk.astype("<i4").tobytes())
            except Exception:
                pass
        try:
            self._rec_file.close()
        except Exception:
            pass
        self._rec_file = None

    def stop_recording(self) -> Optional[str]:
        """Beendet Aufnahme und schließt Datei robust.

        REQ-FUNC-010; EP-REC (FEAT-REC-003)
        """
        if not self._rec_enabled:
            return None
        self._rec_enabled = False
        if self._rec_thread is not None:
            try:
                self._rec_thread.join(timeout=5.0)
            except Exception:
                pass
            self._rec_thread = None
        p = self._rec_path
        with self._lock:
            self.metrics.recording = False
        self._rec_path = None
        return str(p) if p else None

    def save_calibration(self, device_id: str = "default", path: Path = Path("calibration.json")):
        """Speichert Kalibrierfaktor gerätebezogen.

        REQ-FUNC-008; EP-CAL (FEAT-CAL-003)
        """
        data = {}
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                data = {}
        data[device_id] = {
            "cal_offset_db": self.config.cal_offset_db,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_calibration(self, device_id: str = "default", path: Path = Path("calibration.json")) -> bool:
        """Lädt Kalibrierfaktor beim Start.

        REQ-FUNC-008; EP-CAL (FEAT-CAL-004)
        """
        if not path.exists():
            return False
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return False
        if device_id in data and "cal_offset_db" in data[device_id]:
            self.config.cal_offset_db = float(data[device_id]["cal_offset_db"])
            return True
        return False

    def export_snapshot(self, directory: Path = Path("exports")):
        """Exportiert aktuellen Zustand als JSON und erstellt SHA256-Datei.

        REQ-FUNC-007, REQ-DATA-001; EP-EXP (FEAT-EXP-001/002)
        """
        directory.mkdir(parents=True, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        base = directory / f"session_{ts}.json"
        payload = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "config": {
                "samplerate": self.config.samplerate,
                "blocksize": self.config.blocksize,
                "device": self.config.device,
                "weighting": self.config.weighting,
                "time_weighting": self.config.time_weighting,
                "ref_pa": self.config.ref_pa,
                "cal_offset_db": self.config.cal_offset_db,
            },
            "metrics": self.read_metrics(),
        }
        base.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        sha = hashlib.sha256(base.read_bytes()).hexdigest()
        (directory / (base.name + ".sha256")).write_text(sha + "  " + base.name + "\n", encoding="utf-8")
        return str(base), sha


meter = SPLMeter(MeterConfig())
meter.load_calibration()

app = FastAPI()


class ConfigPayload(BaseModel):
    """Payload für /config.

    REQ-FUNC-006; EP-API (FEAT-API-005)
    """
    weighting: Optional[str] = None
    time_weighting: Optional[str] = None
    samplerate: Optional[int] = None
    blocksize: Optional[int] = None
    device: Optional[str] = None
    spec: Optional[str] = None


class CalPayload(BaseModel):
    """Payload für /calibrate.

    REQ-FUNC-008; EP-CAL (FEAT-CAL-002/003/004)
    """
    reference_db: float = 94.0
    device_id: Optional[str] = "default"
    save: bool = True


class AutoCalPayload(BaseModel):
    """Payload für /calibrate_auto (Assistenzfunktion).

    REQ-FUNC-008; EP-CAL (FEAT-CAL-001/002)
    """
    reference_db: float = 94.0
    window_s: float = 1.0
    threshold: float = 0.5
    save: bool = True
    device_id: Optional[str] = "default"


class RecordStartPayload(BaseModel):
    """Payload für /record/start.

    REQ-FUNC-010; EP-REC (FEAT-REC-001)
    """
    path: Optional[str] = None


@app.get("/status")
def api_status():
    """Gibt Status/Zustand zurück.

    REQ-FUNC-006; EP-API (FEAT-API-002)
    """
    return meter.read_metrics()


@app.get("/metrics")
def api_metrics():
    """Liefert aktuelle Kennwerte als JSON.

    REQ-FUNC-006/007; EP-API (FEAT-API-003)
    """
    return meter.read_metrics()


@app.post("/start")
def api_start():
    """Startet Messung.

    REQ-FUNC-006; EP-API (FEAT-API-004)
    """
    meter.start()
    return {"ok": True, "state": meter.state.value}


@app.post("/stop")
def api_stop():
    """Stoppt Messung.

    REQ-FUNC-006; EP-API (FEAT-API-004)
    """
    meter.stop()
    return {"ok": True, "state": meter.state.value}


@app.post("/config")
def api_set_config(p: ConfigPayload):
    """Setzt Konfiguration (Bewertung, Zeit, SR, Block, Device, Spektren).

    REQ-FUNC-006; EP-API (FEAT-API-005)
    """
    if p.weighting and p.weighting not in ("A", "Z"):
        raise HTTPException(400, "weighting must be 'A' or 'Z'")
    if p.time_weighting and p.time_weighting not in ("F", "S"):
        raise HTTPException(400, "time_weighting must be 'F' or 'S'")
    if p.spec and p.spec not in ("none", "octave", "terz"):
        raise HTTPException(400, "spec must be 'none', 'octave', or 'terz'")
    if p.spec is not None:
        meter.config.spec = p.spec
    meter.set_config(p.weighting, p.time_weighting, p.samplerate, p.blocksize, p.device)
    return {"ok": True, "config": meter.read_metrics()}


@app.post("/calibrate")
def api_calibrate(p: CalPayload):
    """Setzt Kalibrier-Offset manuell.

    REQ-FUNC-008; EP-CAL (FEAT-CAL-002/003)
    """
    ok = meter.calibrate_set_offset(p.reference_db)
    if not ok:
        raise HTTPException(400, "no valid measurement to calibrate")
    if p.save:
        meter.save_calibration(p.device_id or "default")
    return {"ok": True, "cal_offset_db": meter.config.cal_offset_db}


@app.get("/detect_cal_1khz")
def api_detect_cal(window_s: float = 1.0):
    """Detektiert 1 kHz-Kalibrator im Fenster; liefert Pegel und Güte.

    REQ-FUNC-008; EP-API (FEAT-API-007), EP-CAL (FEAT-CAL-001)
    """
    return meter.detect_cal_tone_1khz(window_s)


@app.post("/calibrate_auto")
def api_calibrate_auto(p: AutoCalPayload):
    """Automatische Kalibration via Detektion und Referenzpegel.

    REQ-FUNC-008; EP-API (FEAT-API-008), EP-CAL (FEAT-CAL-001/002)
    """
    d = meter.detect_cal_tone_1khz(p.window_s)
    if not d.get("present") or d.get("db") is None or float(d.get("ratio", 0.0)) < p.threshold:
        raise HTTPException(400, "cal tone not detected with sufficient confidence")
    delta = p.reference_db - float(d["db"])
    meter.config.cal_offset_db += delta
    if p.save:
        meter.save_calibration(p.device_id or "default")
    return {"ok": True, "cal_offset_db": meter.config.cal_offset_db, "measured_db": d["db"], "ratio": d["ratio"]}


@app.post("/record/start")
def api_record_start(p: RecordStartPayload):
    """Startet optionale WAV-Aufnahme.

    REQ-FUNC-010; EP-REC (FEAT-REC-001)
    """
    path = Path(p.path) if p.path else None
    out = meter.start_recording_wav(path)
    return {"ok": True, "path": out}


@app.post("/record/stop")
def api_record_stop():
    """Stoppt optionale WAV-Aufnahme.

    REQ-FUNC-010; EP-REC (FEAT-REC-003)
    """
    out = meter.stop_recording()
    return {"ok": True, "path": out}


@app.get("/export")
def api_export():
    """Exportiert Snapshot (JSON + SHA256).

    REQ-FUNC-007, REQ-DATA-001; EP-API (FEAT-API-006), EP-EXP (FEAT-EXP-001/002)
    """
    path, sha = meter.export_snapshot()
    return {"ok": True, "file": path, "sha256": sha}


@app.get("/")
def root():
    """Minimales eingebettetes Dashboard (HTML/JS) für Live-Ansicht.

    REQ-FUNC-006, REQ-UI-001; EP-UI (FEAT-UI-004)
    """
    html = """<!doctype html>
<html><head><meta charset=\"utf-8\"><title>SPL Meter</title><style>body{font-family:system-ui,Arial;margin:20px} .v{font-size:48px} .row{margin:10px 0} button{padding:8px 16px;margin-right:8px}</style></head>
<body>
<h1>SPL Meter</h1>
<div class=\"row\"><span>State: </span><span id=\"state\"></span></div>
<div class=\"row\"><span class=\"v\" id=\"inst\">--.- dB</span> <span id=\"mode\"></span></div>
<div class=\"row\">F: <span id=\"fast\">--.- dB</span> | S: <span id=\"slow\">--.- dB</span> | Leq: <span id=\"leq\">--.- dB</span></div>
<div class=\"row\"><button onclick=\"start()\">Start</button><button onclick=\"stop()\">Stop</button><button onclick=\"cal()\">Cal 94 dB</button><button onclick=\"autocal()\">AutoCal</button><button onclick=\"exp()\">Export</button></div>
<div class=\"row\"><button onclick=\"recstart()\">Rec Start</button><button onclick=\"recstop()\">Rec Stop</button> <span>Recording: </span><span id=\"rec\">off</span></div>
<div class=\"row\">Underruns: <span id=\"u\">0</span> | Dropped: <span id=\"d\">0</span> | Clipped: <span id=\"c\">0</span></div>
<div class=\"row\">Bands (<span id=\"spec\">none</span>): <pre id=\"bands\" style=\"white-space:pre-wrap; background:#f7f7f7; padding:8px;\"></pre></div>
<script>
async function fetchMetrics(){const r=await fetch('/metrics'); const m=await r.json();
document.getElementById('state').textContent=m.state;
document.getElementById('mode').textContent='(' + m.weighting + ', ' + m.time_weighting + ')';
function f(x){return (x===null||!isFinite(x)) ? '--.-' : x.toFixed(1);} 
document.getElementById('inst').textContent=f(m.inst_db)+' dB';
document.getElementById('fast').textContent=f(m.fast_db)+' dB';
document.getElementById('slow').textContent=f(m.slow_db)+' dB';
document.getElementById('leq').textContent=f(m.leq_db)+' dB';
document.getElementById('u').textContent=m.underruns;
document.getElementById('d').textContent=m.dropped_blocks;
document.getElementById('c').textContent=m.clipped_blocks;
document.getElementById('spec').textContent=m.spec;
if(m.bands){const keys=Object.keys(m.bands).sort((a,b)=>parseFloat(a)-parseFloat(b));
const lines=keys.map(k=>k+" Hz: "+(isFinite(m.bands[k])?m.bands[k].toFixed(1):"--.-")+" dB");
document.getElementById('bands').textContent=lines.join("\n");} else {document.getElementById('bands').textContent='';}
document.getElementById('rec').textContent=m.recording? 'on':'off';
}
async function start(){await fetch('/start',{method:'POST'});} 
async function stop(){await fetch('/stop',{method:'POST'});} 
async function cal(){await fetch('/calibrate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({reference_db:94.0, save:true})});}
async function autocal(){const r=await fetch('/calibrate_auto',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({reference_db:94.0, window_s:1.0, threshold:0.5, save:true})}); if(r.ok){alert('AutoCal done');}else{alert('AutoCal failed');}}
async function exp(){const r=await fetch('/export'); const m=await r.json(); alert('Export: '+m.file+'\nsha256: '+m.sha256);} 
async function recstart(){await fetch('/record/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({})});}
async function recstop(){await fetch('/record/stop',{method:'POST'});}
setInterval(fetchMetrics, 500); fetchMetrics();
</script>
</body></html>"""
    return HTMLResponse(content=html)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))

