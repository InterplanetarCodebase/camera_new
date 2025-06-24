import asyncio
import websockets
import base64
import cv2
import numpy as np
import os
import imutils
import time

# Config
PORT = 8765
SAVE_FOLDER = 'unstitched'
STITCHED_OUTPUT = 'stitched_image.jpg'
NUM_IMAGES_TO_CAPTURE = 3
CAPTURE_DELAY = 5  # seconds

connected_clients = set()

def capture_and_save_images(cap):
    print("[Camera] Warming up...")
    time.sleep(2)
    image_paths = []

    os.makedirs(SAVE_FOLDER, exist_ok=True)

    for i in range(NUM_IMAGES_TO_CAPTURE):
        print(f"[Capture] Waiting {CAPTURE_DELAY}s before capturing image {i + 1}...")
        time.sleep(CAPTURE_DELAY)
        for _ in range(5):
            cap.grab()

        ret, frame = cap.read()
        if not ret:
            print(f"[Error] Failed to capture image {i + 1}")
            continue
        path = os.path.join(SAVE_FOLDER, f'image_{i+1}.jpg')
        cv2.imwrite(path, frame)
        print(f"[Saved] {path}")
        image_paths.append(path)

    return image_paths

def stitch_images(image_paths):
    print("[Stitching] Starting stitching process...")
    images = [cv2.imread(p) for p in image_paths if cv2.imread(p) is not None]
    if len(images) < 2:
        print("[Error] Need at least 2 images to stitch.")
        return

    stitcher = cv2.Stitcher_create(cv2.Stitcher_PANORAMA)
    status, stitched = stitcher.stitch(images)

    if status == cv2.Stitcher_OK:
        stitched = cv2.copyMakeBorder(stitched, 10, 10, 10, 10, cv2.BORDER_CONSTANT, (0,0,0))
        gray = cv2.cvtColor(stitched, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY)[1]

        contours = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(contours)
        areaOI = max(contours, key=cv2.contourArea)

        mask = np.zeros(thresh.shape, dtype="uint8")
        x, y, w, h = cv2.boundingRect(areaOI)
        cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)

        minRectangle = mask.copy()
        sub = mask.copy()

        while cv2.countNonZero(sub) > 0:
            minRectangle = cv2.erode(minRectangle, None)
            sub = cv2.subtract(minRectangle, thresh)

        contours = cv2.findContours(minRectangle.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(contours)
        areaOI = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(areaOI)
        stitched = stitched[y:y+h, x:x+w]

        cv2.imshow("Stitched Image", stitched)
        cv2.imwrite(STITCHED_OUTPUT, stitched)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        print(f"[Done] Saved stitched image as {STITCHED_OUTPUT}")
    else:
        print(f"[Error] Stitching failed with code: {status}")

async def handler(websocket):
    print(f"[+] Client connected: {websocket.remote_address}")
    connected_clients.add(websocket)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[Error] Could not open webcam.")
        return

    try:
        image_paths = capture_and_save_images(cap)
        stitch_images(image_paths)

        # Optionally, send stitched image to client
        if os.path.exists(STITCHED_OUTPUT):
            with open(STITCHED_OUTPUT, 'rb') as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')
                await websocket.send(encoded)
                print("[Sent] Stitched image to client.")
        else:
            await websocket.send("STITCHING_FAILED")
            print("[Send] Stitching failed message sent.")

        await websocket.wait_closed()
    finally:
        cap.release()
        connected_clients.remove(websocket)
        print(f"[-] Client disconnected: {websocket.remote_address}")

async def main():
    server = await websockets.serve(handler, "0.0.0.0", PORT)
    print(f"[WebSocket] Stitcher server started on ws://localhost:{PORT}")
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[Exit] Server shut down.")
