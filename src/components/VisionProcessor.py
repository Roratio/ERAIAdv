import json
import time
import cv2
import numpy as np
import pytesseract
import mss
import os
from PIL import Image

class VisionProcessor:
    def __init__(self, config_path="config/vision_map.json"):
        # Adjust path relative to project root if needed
        self.config_path = config_path
        self.regions = {}
        self.sct = mss.mss()
        self.load_config()

        # NOTE: User might need to set Tesseract path if it's not in PATH
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    def load_config(self):
        """Loads region definitions from JSON."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.regions = json.load(f)
                print(f"[VisionProcessor] Loaded config: {len(self.regions)} regions defined.")
            except Exception as e:
                print(f"[VisionProcessor] Error loading config: {e}")
                self.regions = {}
        else:
            print(f"[VisionProcessor] Warning: Config file not found at {self.config_path}.")
            print("Please run the Calibration Tool to generate vision_map.json.")
            self.regions = {}

    def capture_screen(self):
        """Captures the primary monitor."""
        # monitor[1] is usually the primary
        monitor = self.sct.monitors[1]
        screenshot = self.sct.grab(monitor)
        
        # Convert to numpy array (BGRA) -> BGR for OpenCV
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img

    def scan_frame(self):
        """Captures screen and returns text for all defined regions."""
        if not self.regions:
            return {"error": "No regions configured"}

        img = self.capture_screen()
        results = {}

        for label, rect in self.regions.items():
            # rect format: {x, y, w, h}
            x, y, w, h = rect.get('x'), rect.get('y'), rect.get('w'), rect.get('h')

            if x is None: continue # Skip invalid

            # Safe cropping (handle boundaries)
            h_img, w_img = img.shape[:2]
            x = max(0, min(x, w_img))
            y = max(0, min(y, h_img))
            w = max(1, min(w, w_img - x))
            h = max(1, min(h, h_img - y))

            roi = img[y:y+h, x:x+w]

            # Preprocessing for better OCR
            # 1. Grayscale
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            # 2. Rescaling (upscaling helps small text)
            gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

            # 3. Thresholding (Assume white text on dark background for games)
            #    Adjust threshold as needed. 150-200 is often good for white text.
            _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
            
            # 4. Invert if needed? Tesseract likes black text on white bg usually.
            #    Let's invert to make it black text on white.
            thresh = cv2.bitwise_not(thresh)

            # Run OCR
            # psm 7: Treat the image as a single text line.
            # lang='jpn+eng': Support Japanese and English
            try:
                text = pytesseract.image_to_string(thresh, lang='eng+jpn', config='--psm 7').strip()
            except pytesseract.TesseractNotFoundError:
                print("[Error] Tesseract executable not found. Please install Tesseract and add to PATH.")
                return {"error": "Tesseract not found"}
            except Exception as e:
                text = "" # Fail silently for partial errors
            
            results[label] = text

        return results

    def debug_show_regions(self):
        """Show a window with rectangles drawn for debugging."""
        if not self.regions:
            print("No regions to debug.")
            return

        while True:
            img = self.capture_screen()
            for label, rect in self.regions.items():
                x, y, w, h = rect['x'], rect['y'], rect['w'], rect['h']
                cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(img, label, (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            cv2.imshow("Vision Debug (Press 'q' to quit)", img)
            if cv2.waitKey(100) & 0xFF == ord('q'):
                break
        
        cv2.destroyAllWindows()

if __name__ == "__main__":
    # Simple test
    # Ensure config/vision_map.json exists or pass a dummy path
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(root_dir, "config", "vision_map.json")
    
    processor = VisionProcessor(config_path)
    
    if not processor.regions:
        print("Config not loaded. Creating dummy regions for test...")
        # Dictionary format matching the JSON
        processor.regions = {
            "test_region": {"x": 100, "y": 100, "w": 200, "h": 50}
        }
    
    print("Running OCR scan (Press Ctrl+C to stop)...")
    # Make sure to handle Tesseract error gracefully in loop
    res = processor.scan_frame()
    print("Result:", res)
    
    # processor.debug_show_regions()
