import os
import sys
import subprocess
from pathlib import Path

def merge_audio_files(folder, audio_file1, audio_file2, output_name=None):
    """
    Fügt zwei Audio-Dateien zusammen und speichert das Ergebnis
    
    Args:
        folder (str): Relativer Pfad zum Ordner
        audio_file1 (str): Erste Audio-Datei (mp3, wav)
        audio_file2 (str): Zweite Audio-Datei (mp3, wav)
        output_name (str, optional): Name der Ausgabedatei (mp3). 
                                    Wenn None, wird "SP_" + Name der zweiten Datei (ohne Erweiterung) + ".mp3" verwendet
    
    Returns:
        bool: True bei Erfolg, False bei Fehler
    """
    # Vollständige Pfade erstellen
    folder_path = Path(folder).resolve()
    audio1_path = folder_path / audio_file1
    audio2_path = folder_path / audio_file2
    
    # Wenn kein Ausgabename angegeben ist, generiere einen
    if output_name is None:
        # Extrahiere den Basisnamen der zweiten Datei ohne Erweiterung
        base_name = Path(audio_file2).stem
        output_name = f"SP_{base_name}.mp3"
    
    output_path = folder_path / output_name
    
    # Prüfen, ob die Dateien existieren
    if not audio1_path.exists():
        print(f"Fehler: Die Datei {audio1_path} existiert nicht.")
        return False
    
    if not audio2_path.exists():
        print(f"Fehler: Die Datei {audio2_path} existiert nicht.")
        return False
    
    try:
        # Temporäre Datei für die erste Audiodatei
        temp_file1 = folder_path / "temp_audio1.mp3"
        
        # Für die zweite Datei: Wenn es eine WAV-Datei ist, konvertiere sie zu MP3 mit dem gleichen Basisnamen
        is_second_file_wav = audio_file2.lower().endswith('.wav')
        if is_second_file_wav:
            # Erstelle den MP3-Dateinamen basierend auf dem WAV-Dateinamen
            base_name = Path(audio_file2).stem
            mp3_file2 = f"{base_name}.mp3"
            temp_file2 = folder_path / mp3_file2
        else:
            # Wenn es bereits eine MP3-Datei ist, verwende einen temporären Namen
            temp_file2 = folder_path / "temp_audio2.mp3"
        
        # Konvertiere beide Dateien ins gleiche Format (MP3)
        convert_cmd1 = [
            "ffmpeg", "-y", "-i", str(audio1_path), "-acodec", "libmp3lame", 
            "-b:a", "192k", str(temp_file1)
        ]
        convert_cmd2 = [
            "ffmpeg", "-y", "-i", str(audio2_path), "-acodec", "libmp3lame", 
            "-b:a", "192k", str(temp_file2)
        ]
        
        print(f"Konvertiere erste Datei: {' '.join(convert_cmd1)}")
        result1 = subprocess.run(
            convert_cmd1,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result1.returncode != 0:
            print(f"Fehler beim Konvertieren der ersten Datei: {result1.stderr}")
            return False
            
        print(f"Konvertiere zweite Datei: {' '.join(convert_cmd2)}")
        result2 = subprocess.run(
            convert_cmd2,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result2.returncode != 0:
            print(f"Fehler beim Konvertieren der zweiten Datei: {result2.stderr}")
            return False
        
        # Direktes Zusammenführen der beiden temporären MP3-Dateien
        # Verwende den Filter_complex-Ansatz statt concat demuxer
        ffmpeg_command = [
            "ffmpeg",
            "-y",
            "-i", str(temp_file1),
            "-i", str(temp_file2),
            "-filter_complex", "[0:a][1:a]concat=n=2:v=0:a=1[out]",
            "-map", "[out]",
            "-b:a", "192k",
            str(output_path)
        ]
        
        print(f"Führe aus: {' '.join(ffmpeg_command)}")
        
        # FFmpeg ausführen
        result = subprocess.run(
            ffmpeg_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Fehler beim Ausführen von FFmpeg: {result.stderr}")
            return False
        
        print(f"Audio-Dateien erfolgreich zusammengefügt und als {output_path} gespeichert.")
        
        # Wenn die zweite Datei eine WAV-Datei war, informiere den Benutzer über die MP3-Konvertierung
        if is_second_file_wav:
            print(f"Die WAV-Datei wurde als {temp_file2} im MP3-Format gespeichert.")
        
        return True
        
    except Exception as e:
        print(f"Fehler: {str(e)}")
        return False
    
    finally:
        # Nur die temporäre Datei für die erste Audiodatei löschen
        if temp_file1.exists():
            temp_file1.unlink()
        
        # Die konvertierte zweite Datei wird nicht gelöscht, wenn es eine WAV-Datei war
        if not is_second_file_wav and 'temp_file2' in locals() and temp_file2.exists():
            temp_file2.unlink()

def main():
    # Argumente aus der Kommandozeile lesen
    if len(sys.argv) < 4:
        print("Fehler: Mindestens drei Parameter werden benötigt.")
        print("Verwendung: python script.py <ordner> <audio1> <audio2> [output_name.mp3]")
        sys.exit(1)
    
    folder = sys.argv[1]
    audio_file1 = sys.argv[2]
    audio_file2 = sys.argv[3]
    
    # Optionaler vierter Parameter für den Ausgabenamen
    output_name = None
    if len(sys.argv) > 4:
        output_name = sys.argv[4]
    
    success = merge_audio_files(folder, audio_file1, audio_file2, output_name)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()