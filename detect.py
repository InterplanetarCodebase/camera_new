import cv2
import time
import torch
import sys
import asyncio
import websockets
import base64
import numpy as np
from ultralytics import YOLO
import config

# Check for camera index argument
if len(sys.argv) < 2:
    print("Usage: python3 detect.py <camera_index>")
    sys.exit(1)

try:
    cam_index = int(sys.argv[1])
except ValueError:
    print("Camera index must be an integer.")
    sys.exit(1)

# YOLO setup
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Using device: {device}")
model = YOLO("yolov5nu.pt").to(device)

# Video stream
cap = cv2.VideoCapture(cam_index)
if not cap.isOpened():
    print(f"[Error] Failed to open camera {cam_index}")
    sys.exit(1)

# Target FPS
target_fps = 3
frame_interval = 1 / target_fps

# Retry settings
MAX_RETRIES = 5
retry_count = 0

# Global set of connected clients
connected_clients = set()

async def send_frames():
    global retry_count

    while True:
        # Wait until at least one client is connected
        while not connected_clients:
            await asyncio.sleep(0.1)  # check every 100ms

        try:
            start = time.time()
            ret, frame = cap.read()
            if not ret or frame is None:
                raise ValueError("Frame read failed")

            retry_count = 0  # Reset retry count

            # Resize for faster inference
            small_frame = cv2.resize(frame, (640, 480))

            # Inference
            results = model(small_frame, device=0 if device == "cuda" else "cpu")
            annotated = results[0].plot()

            # Encode frame to JPEG
            _, buffer = cv2.imencode('.jpg', annotated)
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')

            # Send to all connected clients
            if connected_clients:
                await asyncio.gather(*[
                    client.send(jpg_as_text) for client in connected_clients
                ])

            # Sleep to maintain target FPS
            elapsed = time.time() - start
            sleep_time = max(0, frame_interval - elapsed)
            await asyncio.sleep(sleep_time)

        except Exception as e:
            print(f"[Warning] Error reading or sending frame: {e}")
            retry_count += 1
            if retry_count >= MAX_RETRIES:
                print("[Error] Max retries reached. Exiting.")
                break
            await asyncio.sleep(0.5)

    cap.release()

async def handler(websocket):
    connected_clients.add(websocket)
    print(f"[+] Client connected: {websocket.remote_address}")
    try:
        await websocket.wait_closed()
    finally:
        connected_clients.remove(websocket)
        print(f"[-] Client disconnected: {websocket.remote_address}")

async def detector():
    server = await websockets.serve(handler, config.IP, sys.argv[2])
    print(f"WebSocket server started on ws://{config.IP}:{sys.argv[2]}")
    await send_frames()

# Run the asyncio event loop immediately at the global scope
try:
    asyncio.run(detector())
except KeyboardInterrupt:
    print("\n[Exit] Server interrupted by user.")
