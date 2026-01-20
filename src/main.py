from machine import Pin, time_pulse_us, RTC
import time
# Matches your filename 'oled.py'
from oled import OLED_1inch3 

class SmartMonitor:
    def __init__(self):
        # --- DISPLAY & SENSORS ---
        self.oled = OLED_1inch3()
        
        # Ultrasonic Sensor (HC-SR04) on GP6/GP7
        self.trig = Pin(6, Pin.OUT)
        self.echo = Pin(7, Pin.IN)
        
        # --- BUTTONS (Built-in on Waveshare HAT) ---
        self.key0 = Pin(15, Pin.IN, Pin.PULL_UP) # Action / Reset
        self.key1 = Pin(17, Pin.IN, Pin.PULL_UP) # View Toggle
        
        # --- CONFIGURATION ---
        self.SIT_THRESHOLD = 80  # cm (Adjust based on your desk setup)
        self.TARGET_TIME = 10    # Seconds for demo (Set to 3000 for 50 mins)
        
        # --- DATA STORAGE ---
        self.history = [500] * 5 # Moving average buffer
        
        # --- METRICS ---
        self.total_away_time = 0 # Tracking "Healthy" movement time
        self.session_count = 0
        self.current_session_start = 0
        self.is_sitting = False
        
        # --- STATE ---
        self.show_dashboard = False
        self.last_key1_press = 0
        self.last_key0_press = 0

    def get_distance(self):
        """Reads distance from HC-SR04 with signal smoothing."""
        self.trig.low(); time.sleep_us(2)
        self.trig.high(); time.sleep_us(10)
        self.trig.low()
        try:
            d = time_pulse_us(self.echo, 1, 30000)
            dist = (d * 0.0343) / 2 if d > 0 else 500
        except OSError: dist = 500
        
        # Simple Moving Average Filter
        self.history.pop(0)
        self.history.append(dist)
        return sum(self.history) / len(self.history)

    def format_time(self, seconds):
        """Formats seconds into readable h/m/s strings."""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        if h > 0: return f"{h}h {m}m"
        return f"{m}m {s}s"

    def handle_inputs(self):
        """Manages button presses with debouncing."""
        now = time.ticks_ms()
        
        # KEY1: Toggle Dashboard View
        if self.key1.value() == 0: 
            if time.ticks_diff(now, self.last_key1_press) > 300:
                self.show_dashboard = not self.show_dashboard
                self.last_key1_press = now

        # KEY0: Reset Timer manually
        if self.key0.value() == 0:
            if time.ticks_diff(now, self.last_key0_press) > 300:
                self.current_session_start = time.time()
                self.last_key0_press = now

    def draw_coffee_cup(self, x, y, color):
        """Draws a pixel-art coffee cup icon."""
        self.oled.fill_rect(x, y, 20, 14, color) # Body
        self.oled.rect(x + 20, y + 2, 4, 8, color) # Handle
        # Steam
        self.oled.line(x + 4, y - 3, x + 4, y - 6, color)
        self.oled.line(x + 10, y - 4, x + 10, y - 8, color)
        self.oled.line(x + 16, y - 3, x + 16, y - 6, color)

    def draw_dashboard(self):
        """Renders the Analytics Dashboard."""
        self.oled.text("DASHBOARD", 30, 2, 0xFFFF)
        self.oled.line(0, 12, 128, 12, 0xFFFF)
        
        # Metric 1: Away Time
        self.oled.text("Away Time:", 5, 25, 0xFFFF)
        self.oled.text(self.format_time(self.total_away_time), 5, 38, 0xFFFF)
        
        # Metric 2: Session Count (Simplified)
        self.oled.text(f"Sits: {self.session_count}", 5, 53, 0xFFFF)

    def draw_countdown_view(self, remaining):
        """Renders the main Countdown Timer."""
        self.oled.text("FOCUS TIME", 25, 2, 0xFFFF)

        # Big Countdown Timer
        mins = int(remaining // 60)
        secs = int(remaining % 60)
        timer_str = "{:02d}:{:02d}".format(mins, secs)
        self.oled.text(timer_str, 40, 25, 0xFFFF)
        
        # Countdown Bar
        pct = max(0, remaining / self.TARGET_TIME)
        self.oled.rect(14, 45, 100, 8, 0xFFFF)
        self.oled.fill_rect(14, 45, int(100 * pct), 8, 0xFFFF)

    def run(self):
        print("Monitor Active. Listening for Sits...")
        
        while True:
            self.oled.fill(0)
            self.handle_inputs()
            
            dist = self.get_distance()
            current_time = time.time()
            
            # --- MAIN LOGIC ENGINE ---
            if dist < self.SIT_THRESHOLD:
                # STATE: SITTING
                if not self.is_sitting:
                    self.is_sitting = True
                    self.current_session_start = current_time
                    self.session_count += 1
                
                # Calculate Countdown
                elapsed = current_time - self.current_session_start
                remaining = self.TARGET_TIME - elapsed
                
                if remaining <= 0:
                    # ALARM STATE (Flash with Coffee Cup)
                    # Text moved up to Y=15 to avoid overlap
                    if int(current_time * 2) % 2 == 0:
                        self.oled.fill(0xFFFF)
                        self.oled.text("STAND UP", 30, 15, 0x0000) 
                        self.draw_coffee_cup(52, 40, 0x0000)
                    else:
                        self.oled.fill(0)
                        self.oled.text("STAND UP", 30, 15, 0xFFFF)
                        self.draw_coffee_cup(52, 40, 0xFFFF)
                
                elif self.show_dashboard:
                    self.draw_dashboard()
                else:
                    self.draw_countdown_view(remaining)
            
            else:
                # STATE: AWAY / STANDING
                if self.is_sitting:
                    self.is_sitting = False 
                
                # Accumulate Away Time
                self.total_away_time += 0.1
                
                if self.show_dashboard:
                    self.draw_dashboard()
                else:
                    # Simplified Away Screen
                    self.oled.text("AWAY", 48, 20, 0xFFFF)
                    self.oled.text(f"Total: {self.format_time(self.total_away_time)}", 20, 40, 0xFFFF)

            self.oled.show()
            time.sleep(0.1)

# --- EXECUTION ---
app = SmartMonitor()
app.run()