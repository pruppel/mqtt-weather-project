import json
import time
from datetime import datetime
import paho.mqtt.client as mqtt

# MQTT Settings
broker = "localhost"
port = 1883
topic = "weather"

# Datei zum Speichern
data_file = "weather_data.json"

# Liste zum Speichern der Daten
weather_data = []

def load_existing_data():
    """Lade vorhandene Daten aus der JSON-Datei"""
    global weather_data
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            weather_data = json.load(f)
        print(f"✓ {len(weather_data)} Datensätze geladen")
    except FileNotFoundError:
        print("ℹ Keine vorhandenen Daten gefunden, starte neu")
        weather_data = []

def save_data():
    """Speichere Daten in JSON-Datei"""
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(weather_data, f, indent=2, ensure_ascii=False)

def on_connect(client, userdata, flags, rc):
    """Callback bei erfolgreicher Verbindung"""
    if rc == 0:
        print(f"✓ Verbunden mit MQTT Broker auf {broker}:{port}")
        client.subscribe(topic)
        print(f"✓ Topic '{topic}' abonniert")
    else:
        print(f"✗ Verbindung fehlgeschlagen mit Code {rc}")

def on_message(client, userdata, msg):
    """Callback bei eingehender Nachricht"""
    try:
        # Parse die empfangene Nachricht
        payload = json.loads(msg.payload.decode())
        
        # Speichere die Daten
        weather_data.append(payload)
        
        # Zeige die Nachricht an
        station_id = payload.get('stationId', 'Unknown')
        temp = payload.get('temperature', 'N/A')
        humidity = payload.get('humidity', 'N/A')
        timestamp = payload.get('timestamp', 'N/A')
        
        # Prüfe auf Sensorfehler
        if temp == -999:
            print(f"⚠ [{station_id}] SENSORFEHLER - Temperatur: {temp}°C, Luftfeuchtigkeit: {humidity}%, Zeit: {timestamp}")
        else:
            print(f"📡 [{station_id}] Temperatur: {temp}°C, Luftfeuchtigkeit: {humidity}%, Zeit: {timestamp}")
        
        # Speichere alle 10 Nachrichten
        if len(weather_data) % 10 == 0:
            save_data()
            print(f"💾 {len(weather_data)} Datensätze gespeichert")
            print_statistics()
        
    except json.JSONDecodeError:
        print(f"✗ Fehler beim Parsen der Nachricht: {msg.payload}")
    except Exception as e:
        print(f"✗ Fehler: {e}")

def print_statistics():
    """Zeige einfache Statistiken"""
    if not weather_data:
        return
    
    # Filtere fehlerhafte Messungen
    valid_data = [d for d in weather_data if d.get('temperature', -999) != -999]
    
    if not valid_data:
        print("\n📊 Keine gültigen Daten für Statistiken vorhanden\n")
        return
    
    # Berechne Durchschnittswerte
    avg_temp = sum(d['temperature'] for d in valid_data) / len(valid_data)
    avg_humidity = sum(d['humidity'] for d in valid_data) / len(valid_data)
    
    # Finde Min/Max
    min_temp = min(d['temperature'] for d in valid_data)
    max_temp = max(d['temperature'] for d in valid_data)
    
    # Zähle Stationen
    stations = set(d['stationId'] for d in weather_data)
    
    # Zähle fehlerhafte Messungen
    error_count = len(weather_data) - len(valid_data)
    
    print(f"\n📊 Statistiken:")
    print(f"   Gesamte Messungen: {len(weather_data)}")
    print(f"   Gültige Messungen: {len(valid_data)}")
    print(f"   Fehlerhafte Messungen: {error_count}")
    print(f"   Aktive Stationen: {len(stations)} ({', '.join(sorted(stations))})")
    print(f"   Durchschnittstemperatur: {avg_temp:.1f}°C")
    print(f"   Durchschnittliche Luftfeuchtigkeit: {avg_humidity:.1f}%")
    print(f"   Temperaturbereich: {min_temp:.1f}°C - {max_temp:.1f}°C\n")

def main():
    """Hauptfunktion"""
    print("=" * 60)
    print("🌦  MQTT Wetterstation Subscriber")
    print("=" * 60)
    
    # Lade vorhandene Daten
    load_existing_data()
    
    # Erstelle MQTT Client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        # Verbinde mit dem Broker
        print(f"\n🔄 Verbinde mit MQTT Broker {broker}:{port}...")
        client.connect(broker, port, 60)
        
        # Starte die Loop
        print("🎧 Warte auf Nachrichten... (Strg+C zum Beenden)\n")
        client.loop_forever()
        
    except KeyboardInterrupt:
        print("\n\n⏹  Beende Subscriber...")
        save_data()
        print_statistics()
        print(f"✓ Finale Daten gespeichert in {data_file}")
        
    except Exception as e:
        print(f"\n✗ Fehler: {e}")
        
    finally:
        client.disconnect()
        print("✓ Getrennt vom Broker")

if __name__ == "__main__":
    main()
