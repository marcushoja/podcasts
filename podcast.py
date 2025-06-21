import os
import sys
import subprocess
from pathlib import Path

def merge_audio_files(folder, audio_files, output_name=None, bitrate="192k"):
    """
    Fügt mehrere Audio-Dateien zusammen und speichert das Ergebnis
    
    Args:
        folder (str): Relativer Pfad zum Ordner
        audio_files (list): Liste von Audio-Dateien (mp3, wav)
                           Die erste Datei kommt ganz nach vorn, die zweite ganz nach hinten,
                           die dritte ist der Hauptteil und bestimmt den Namen
        output_name (str, optional): Name der Ausgabedatei (mp3).
                                    Wenn None, wird "SP_" + Name der dritten Datei (ohne Erweiterung) + ".mp3" verwendet
        bitrate (str, optional): Bitrate für die MP3-Konvertierung (Standard: "192k")
    
    Returns:
        bool: True bei Erfolg, False bei Fehler
    """
    # Vollständige Pfade erstellen
    folder_path = Path(folder).resolve()
    audio_paths = [folder_path / audio_file for audio_file in audio_files]
    
    # Wenn kein Ausgabename angegeben ist, generiere einen basierend auf der dritten Datei
    if output_name is None:
        # Wenn es eine dritte Datei gibt, nutze sie für den Namen
        if len(audio_files) >= 3:
            base_name = Path(audio_files[2]).stem
        else:
            # Ansonsten nutze die erste Datei
            base_name = Path(audio_files[0]).stem
        output_name = f"SP_{base_name}.mp3"
    
    output_path = folder_path / output_name
    
    # Prüfen, ob die Dateien existieren
    for i, audio_path in enumerate(audio_paths):
        if not audio_path.exists():
            print(f"Fehler: Die Datei {audio_path} existiert nicht.")
            return False
    
    try:
        # Temporäre Dateien für die Konvertierung
        temp_files = []
        
        # Konvertiere alle Dateien ins MP3-Format
        for i, (audio_file, audio_path) in enumerate(zip(audio_files, audio_paths)):
            # Prüfen, ob es eine WAV-Datei ist
            is_wav = audio_file.lower().endswith('.wav')
            
            if is_wav:
                # Erstelle den MP3-Dateinamen basierend auf dem WAV-Dateinamen
                base_name = Path(audio_file).stem
                mp3_file = f"{base_name}.mp3"
                temp_file = folder_path / mp3_file
            else:
                # Wenn es bereits eine MP3-Datei ist, verwende einen temporären Namen
                temp_file = folder_path / f"temp_audio{i+1}.mp3"
            
            temp_files.append((temp_file, is_wav))
            
            # Konvertiere die Datei ins MP3-Format
            convert_cmd = [
                "ffmpeg", "-y", "-i", str(audio_path), "-acodec", "libmp3lame", 
                "-b:a", bitrate, str(temp_file)
            ]
            
            print(f"Konvertiere Datei {i+1}: {' '.join(convert_cmd)}")
            result = subprocess.run(
                convert_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode != 0:
                print(f"Fehler beim Konvertieren der Datei {i+1}: {result.stderr}")
                return False
        
        # Ordne die Dateien in der gewünschten Reihenfolge an:
        # Datei 1, Datei 3 (falls vorhanden), Datei 2
        ordered_temp_files = []
        
        # Erste Datei kommt immer zuerst
        ordered_temp_files.append(temp_files[0])
        
        # Wenn es eine dritte Datei gibt, kommt sie in die Mitte
        if len(temp_files) >= 3:
            ordered_temp_files.append(temp_files[2])
            
            # Falls es mehr als 3 Dateien gibt, füge sie in der Originalreihenfolge hinzu
            for i in range(3, len(temp_files)):
                ordered_temp_files.append(temp_files[i])
        
        # Zweite Datei kommt immer ans Ende
        if len(temp_files) >= 2:
            ordered_temp_files.append(temp_files[1])
        
        # Filter Complex-String für die Verkettung erstellen
        filter_complex = ""
        for i in range(len(ordered_temp_files)):
            filter_complex += f"[{i}:a]"
        filter_complex += f"concat=n={len(ordered_temp_files)}:v=0:a=1[out]"
        
        # Alle temporären MP3-Dateien zusammenführen
        ffmpeg_command = ["ffmpeg", "-y"]
        
        # Alle Input-Dateien in der neuen Reihenfolge hinzufügen
        for temp_file, _ in ordered_temp_files:
            ffmpeg_command.extend(["-i", str(temp_file)])
        
        # Filter-Complex und Ausgabe hinzufügen
        ffmpeg_command.extend([
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-b:a", bitrate,
            str(output_path)
        ])
        
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
        print(f"Reihenfolge: Datei 1, Datei 3 (falls vorhanden), Datei 2")
        
        # Informiere über WAV-Dateien, die als MP3 gespeichert wurden
        for i, (audio_file, (temp_file, is_wav)) in enumerate(zip(audio_files, temp_files)):
            if is_wav:
                print(f"Die WAV-Datei {audio_file} wurde als {temp_file} im MP3-Format gespeichert.")
        
        return True
        
    except Exception as e:
        print(f"Fehler: {str(e)}")
        return False
    
    finally:
        # Temporäre Dateien aufräumen (außer konvertierte WAV-Dateien)
        for temp_file, is_wav in temp_files:
            if not is_wav and temp_file.exists():
                temp_file.unlink()

def main():
    # Argumente aus der Kommandozeile lesen
    if len(sys.argv) < 4:
        print("Fehler: Mindestens drei Parameter werden benötigt.")
        print("Verwendung: python script.py <ordner> <audio1> <audio2> [audio3] [output_name.mp3] [bitrate]")
        print("Die Dateien werden in der Reihenfolge: audio1, audio3, audio2 zusammengeführt.")
        print("Der Name der Ausgabedatei basiert auf audio3 (SP_audio3.mp3), falls vorhanden, sonst auf audio1.")
        sys.exit(1)
    
    folder = sys.argv[1]
    
    # Audio-Dateien sammeln (mindestens 2, aber kann auch mehr sein)
    audio_files = []
    for i in range(2, len(sys.argv)):
        if i >= 2 and (sys.argv[i].endswith('.mp3') or sys.argv[i].endswith('.wav')):
            audio_files.append(sys.argv[i])
        else:
            break
    
    # Prüfen, ob mindestens 2 Audio-Dateien angegeben wurden
    if len(audio_files) < 2:
        print("Fehler: Mindestens zwei Audio-Dateien werden benötigt.")
        print("Verwendung: python script.py <ordner> <audio1> <audio2> [audio3] [output_name.mp3] [bitrate]")
        sys.exit(1)
    
    # Position für optionale Parameter bestimmen
    opt_start_pos = 2 + len(audio_files)
    
    # Optionaler Parameter für den Ausgabenamen
    output_name = None
    if len(sys.argv) > opt_start_pos:
        # Prüfen, ob der Parameter eine MP3-Datei ist (also ein Ausgabename)
        if sys.argv[opt_start_pos].endswith('.mp3'):
            output_name = sys.argv[opt_start_pos]
            opt_start_pos += 1
    
    # Optionaler Parameter für die Bitrate
    bitrate = "192k"
    if len(sys.argv) > opt_start_pos:
        bitrate = sys.argv[opt_start_pos]
    
    success = merge_audio_files(folder, audio_files, output_name, bitrate)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()