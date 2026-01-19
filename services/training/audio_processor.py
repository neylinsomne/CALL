"""
Audio Processor with Academic Standards
LUFS normalization, sample rate conversion, and quality validation
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Tuple, Optional, List
import json

import numpy as np
import soundfile as sf
from scipy import signal


# ===========================================
# ACADEMIC STANDARDS CONFIGURATION
# ===========================================
STANDARDS = {
    "sample_rate": 24000,          # 24kHz for F5-TTS
    "sample_rate_recording": 48000, # 48kHz for recording (downsampled later)
    "bit_depth": 16,               # 16-bit PCM minimum
    "channels": 1,                 # Mono
    "target_lufs": -23.0,          # EBU R128 broadcast standard
    "lufs_tolerance": 1.0,         # ±1 LUFS tolerance
    "min_duration": 3.0,           # Minimum 3 seconds
    "max_duration": 15.0,          # Maximum 15 seconds
    "max_peak_db": -1.0,           # True peak limit
    "silence_threshold_db": -40,   # For VAD
}


# ===========================================
# LUFS MEASUREMENT (Simplified K-weighting)
# ===========================================
def measure_lufs(audio: np.ndarray, sample_rate: int) -> float:
    """
    Measure Loudness Units Full Scale (LUFS) - simplified implementation
    Based on ITU-R BS.1770-4
    """
    # Pre-filter (K-weighting approximation)
    # High-shelf filter
    b_hs, a_hs = signal.butter(2, 1500 / (sample_rate / 2), btype='high')
    audio_filtered = signal.filtfilt(b_hs, a_hs, audio)
    
    # High-pass filter
    b_hp, a_hp = signal.butter(2, 38 / (sample_rate / 2), btype='high')
    audio_filtered = signal.filtfilt(b_hp, a_hp, audio_filtered)
    
    # Mean square
    mean_square = np.mean(audio_filtered ** 2)
    
    # Avoid log of zero
    if mean_square < 1e-10:
        return -100.0
    
    # LUFS calculation
    lufs = -0.691 + 10 * np.log10(mean_square)
    
    return lufs


def normalize_lufs(
    audio: np.ndarray, 
    sample_rate: int, 
    target_lufs: float = STANDARDS["target_lufs"]
) -> Tuple[np.ndarray, float]:
    """
    Normalize audio to target LUFS level
    
    Returns:
        Tuple of (normalized_audio, gain_applied_db)
    """
    current_lufs = measure_lufs(audio, sample_rate)
    
    if current_lufs < -99:
        # Silent audio
        return audio, 0.0
    
    # Calculate gain needed
    gain_db = target_lufs - current_lufs
    gain_linear = 10 ** (gain_db / 20)
    
    # Apply gain
    normalized = audio * gain_linear
    
    # Check for clipping and apply limiter if needed
    max_peak = np.max(np.abs(normalized))
    peak_db = 20 * np.log10(max_peak) if max_peak > 0 else -100
    
    if peak_db > STANDARDS["max_peak_db"]:
        # Apply soft limiter
        limit_db = STANDARDS["max_peak_db"]
        limit_linear = 10 ** (limit_db / 20)
        normalized = np.clip(normalized, -limit_linear, limit_linear)
    
    return normalized, gain_db


def measure_true_peak(audio: np.ndarray) -> float:
    """Measure true peak in dBTP (with 4x oversampling)"""
    # Upsample 4x for true peak measurement
    upsampled = signal.resample(audio, len(audio) * 4)
    peak = np.max(np.abs(upsampled))
    
    if peak < 1e-10:
        return -100.0
    
    return 20 * np.log10(peak)


# ===========================================
# SAMPLE RATE CONVERSION
# ===========================================
def resample_audio(
    audio: np.ndarray, 
    original_sr: int, 
    target_sr: int
) -> np.ndarray:
    """High-quality resampling using polyphase filtering"""
    if original_sr == target_sr:
        return audio
    
    # Calculate resampling ratio
    duration = len(audio) / original_sr
    target_samples = int(duration * target_sr)
    
    # Use scipy's resample for anti-aliasing
    resampled = signal.resample(audio, target_samples)
    
    return resampled


# ===========================================
# AUDIO VALIDATION
# ===========================================
def validate_audio(
    audio: np.ndarray, 
    sample_rate: int
) -> dict:
    """
    Validate audio against academic standards
    
    Returns dict with validation results and issues
    """
    issues = []
    warnings = []
    
    duration = len(audio) / sample_rate
    lufs = measure_lufs(audio, sample_rate)
    true_peak = measure_true_peak(audio)
    
    # Check duration
    if duration < STANDARDS["min_duration"]:
        issues.append(f"Duration too short: {duration:.1f}s < {STANDARDS['min_duration']}s")
    elif duration > STANDARDS["max_duration"]:
        issues.append(f"Duration too long: {duration:.1f}s > {STANDARDS['max_duration']}s")
    
    # Check LUFS
    lufs_diff = abs(lufs - STANDARDS["target_lufs"])
    if lufs_diff > STANDARDS["lufs_tolerance"]:
        warnings.append(f"LUFS deviation: {lufs:.1f} (target: {STANDARDS['target_lufs']})")
    
    # Check true peak
    if true_peak > STANDARDS["max_peak_db"]:
        warnings.append(f"True peak too high: {true_peak:.1f}dB > {STANDARDS['max_peak_db']}dB")
    
    # Check for DC offset
    dc_offset = np.mean(audio)
    if abs(dc_offset) > 0.01:
        warnings.append(f"DC offset detected: {dc_offset:.4f}")
    
    # Check for clipping
    if np.max(np.abs(audio)) >= 0.999:
        issues.append("Audio is clipping (peak at 0dBFS)")
    
    return {
        "valid": len(issues) == 0,
        "duration": duration,
        "lufs": lufs,
        "true_peak_db": true_peak,
        "dc_offset": dc_offset,
        "issues": issues,
        "warnings": warnings,
    }


# ===========================================
# COMPLETE AUDIO PROCESSOR
# ===========================================
class AudioProcessor:
    """Complete audio processor for TTS training data"""
    
    def __init__(self, target_sr: int = STANDARDS["sample_rate"]):
        self.target_sr = target_sr
        
    def process_file(
        self, 
        input_path: str, 
        output_path: str,
        normalize: bool = True
    ) -> dict:
        """
        Process a single audio file to meet academic standards
        
        Steps:
        1. Load and convert to mono
        2. Resample to target sample rate
        3. Remove DC offset
        4. Normalize to target LUFS
        5. Validate and save
        """
        # Load audio
        audio, original_sr = sf.read(input_path)
        
        # Convert to mono if stereo
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)
        
        # Ensure float64 for processing
        audio = audio.astype(np.float64)
        
        # Remove DC offset
        audio = audio - np.mean(audio)
        
        # Resample to target
        audio = resample_audio(audio, original_sr, self.target_sr)
        
        # Normalize LUFS
        if normalize:
            audio, gain_applied = normalize_lufs(audio, self.target_sr)
        else:
            gain_applied = 0.0
        
        # Validate
        validation = validate_audio(audio, self.target_sr)
        
        # Convert to float32 for saving (more compatible)
        audio = audio.astype(np.float32)
        
        # Save
        sf.write(
            output_path, 
            audio, 
            self.target_sr, 
            subtype='PCM_16'  # 16-bit PCM
        )
        
        return {
            "input": input_path,
            "output": output_path,
            "original_sr": original_sr,
            "target_sr": self.target_sr,
            "gain_applied_db": gain_applied,
            "validation": validation
        }
    
    def process_directory(
        self, 
        input_dir: str, 
        output_dir: str,
        extensions: set = {'.wav', '.mp3', '.flac', '.ogg', '.m4a'}
    ) -> dict:
        """Process all audio files in a directory"""
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = {
            "processed": 0,
            "failed": 0,
            "total_duration": 0.0,
            "files": []
        }
        
        audio_files = [
            f for f in input_path.iterdir() 
            if f.suffix.lower() in extensions
        ]
        
        print(f"Processing {len(audio_files)} audio files...")
        
        for audio_file in audio_files:
            try:
                output_file = output_path / (audio_file.stem + ".wav")
                result = self.process_file(str(audio_file), str(output_file))
                
                if result["validation"]["valid"]:
                    results["processed"] += 1
                    results["total_duration"] += result["validation"]["duration"]
                else:
                    results["failed"] += 1
                    print(f"  ⚠ {audio_file.name}: {result['validation']['issues']}")
                
                results["files"].append(result)
                
            except Exception as e:
                results["failed"] += 1
                print(f"  ✗ {audio_file.name}: {str(e)}")
        
        print(f"\nProcessed: {results['processed']}, Failed: {results['failed']}")
        print(f"Total duration: {results['total_duration']/60:.1f} minutes")
        
        return results


# ===========================================
# FFmpeg-based LUFS (More Accurate)
# ===========================================
def measure_lufs_ffmpeg(audio_path: str) -> Optional[float]:
    """Measure LUFS using FFmpeg (more accurate than pure Python)"""
    try:
        result = subprocess.run(
            [
                'ffmpeg', '-i', audio_path,
                '-af', 'loudnorm=I=-23:LRA=7:TP=-1:print_format=json',
                '-f', 'null', '-'
            ],
            capture_output=True,
            text=True
        )
        
        # Parse JSON output from FFmpeg
        output = result.stderr
        json_start = output.rfind('{')
        json_end = output.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            loudness_data = json.loads(output[json_start:json_end])
            return float(loudness_data.get('input_i', -23))
            
    except Exception as e:
        print(f"FFmpeg LUFS measurement failed: {e}")
    
    return None


def normalize_lufs_ffmpeg(
    input_path: str, 
    output_path: str,
    target_lufs: float = -23.0
) -> bool:
    """Normalize audio using FFmpeg loudnorm filter (most accurate)"""
    try:
        # Two-pass loudnorm for best results
        # First pass: measure
        measure_cmd = [
            'ffmpeg', '-i', input_path,
            '-af', f'loudnorm=I={target_lufs}:LRA=7:TP=-1:print_format=json',
            '-f', 'null', '-'
        ]
        result = subprocess.run(measure_cmd, capture_output=True, text=True)
        
        # Parse measurements
        output = result.stderr
        json_start = output.rfind('{')
        json_end = output.rfind('}') + 1
        
        if json_start >= 0:
            stats = json.loads(output[json_start:json_end])
            
            # Second pass: normalize with measured values
            normalize_cmd = [
                'ffmpeg', '-y', '-i', input_path,
                '-af', (
                    f"loudnorm=I={target_lufs}:LRA=7:TP=-1:"
                    f"measured_I={stats['input_i']}:"
                    f"measured_LRA={stats['input_lra']}:"
                    f"measured_TP={stats['input_tp']}:"
                    f"measured_thresh={stats['input_thresh']}:"
                    f"linear=true"
                ),
                '-ar', str(STANDARDS['sample_rate']),
                '-ac', '1',
                output_path
            ]
            subprocess.run(normalize_cmd, capture_output=True, check=True)
            return True
            
    except Exception as e:
        print(f"FFmpeg normalization failed: {e}")
    
    return False


# ===========================================
# CLI
# ===========================================
if __name__ == "__main__":
    import click
    
    @click.command()
    @click.option('--input', '-i', 'input_path', required=True, help='Input file or directory')
    @click.option('--output', '-o', 'output_path', required=True, help='Output file or directory')
    @click.option('--sample-rate', '-sr', default=24000, help='Target sample rate')
    @click.option('--use-ffmpeg/--no-ffmpeg', default=True, help='Use FFmpeg for normalization')
    def main(input_path: str, output_path: str, sample_rate: int, use_ffmpeg: bool):
        """Process audio files to meet TTS training standards"""
        processor = AudioProcessor(target_sr=sample_rate)
        
        input_p = Path(input_path)
        
        if input_p.is_file():
            if use_ffmpeg:
                success = normalize_lufs_ffmpeg(input_path, output_path)
                print(f"{'✓' if success else '✗'} Processed: {input_path}")
            else:
                result = processor.process_file(input_path, output_path)
                print(f"Processed: {result['validation']}")
        else:
            processor.process_directory(input_path, output_path)
    
    main()
