import serial
import csv
import time
from datetime import datetime

# CONFIG: Update 'COM3' or '/dev/ttyACM0' to match your Pico
SERIAL_PORT = '/dev/ttyACM0' 
BAUD_RATE = 115200

def log_data():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Listening on {SERIAL_PORT}...")
        
        # Create CSV with headers if it doesn't exist
        with open('focus_metrics.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Event", "Duration_Secs", "Total_Away_Time"])

        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                if line.startswith("Monitor Active"): continue
                
                # Timestamp the event
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{now}] Pico says: {line}")
                
                # Save to CSV
                with open('focus_metrics.csv', 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([now, "Raw_Log", line])
                    
    except KeyboardInterrupt:
        print("\nLogging stopped.")

if __name__ == "__main__":
    log_data()