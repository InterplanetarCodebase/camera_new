import cv2
import os
import numpy as np
import glob
import imutils
import asyncio
import sys
import base64
import websockets
import config

# Argument parsing
if len(sys.argv) < 2:
    print("Usage: python3 modified_client.py <ws_port>")
    sys.exit(1)

PORT = sys.argv[1]
URI = f"ws://{config.IP}:{PORT}"

# Client communication function from Code-1
async def get_frames_from_server(uri, num_frames=3):
    frames = []
    async with websockets.connect(uri) as websocket:
        print(f"[+] Connected to {uri}")
        try:
            while len(frames) < num_frames:
                data = await websocket.recv()
                img_data = base64.b64decode(data)
                nparr = np.frombuffer(img_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                if frame is not None:
                    frames.append(frame)
                    print(f"[{len(frames)}/{num_frames}] Frame received from server")
        except websockets.exceptions.ConnectionClosed:
            print("[-] Connection closed by server.")

    return frames

# Replaces capture_three_images
async def fetch_and_save_images():
    folder_name = 'unstitched'
    os.makedirs(folder_name, exist_ok=True)
    frames = await get_frames_from_server(URI)

    for i, frame in enumerate(frames, 1):
        filename = os.path.join(folder_name, f'image_{i}.jpg')
        cv2.imwrite(filename, frame)
        print(f"Saved {filename}")

def image_stitcher():
    asyncio.run(fetch_and_save_images())
    
    image_paths = glob.glob('unstitched/*.jpg')
    images = []

    for image in image_paths:
        img = cv2.imread(image)
        if img is not None:
            images.append(img)
    
    if len(images) < 2:
        print("Need at least two images to stitch.")
        return

    images_stitched = cv2.Stitcher_create()
    error, stitched_image = images_stitched.stitch(images)

    if not error:
        stitched_image = cv2.copyMakeBorder(stitched_image, 10, 10, 10, 10, cv2.BORDER_CONSTANT, (0,0,0))

        gray = cv2.cvtColor(stitched_image, cv2.COLOR_BGR2GRAY)
        thresh_img = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY)[1]

        contours = cv2.findContours(thresh_img.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(contours)
        areaOI = max(contours, key=cv2.contourArea)

        mask = np.zeros(thresh_img.shape, dtype="uint8")
        x, y, w, h = cv2.boundingRect(areaOI)
        cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)

        minRectangle = mask.copy()
        sub = mask.copy()

        while cv2.countNonZero(sub) > 0:
            minRectangle = cv2.erode(minRectangle, None)
            sub = cv2.subtract(minRectangle, thresh_img)
        
        contours = cv2.findContours(minRectangle.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(contours)
        areaOI = max(contours, key=cv2.contourArea)

        x, y, w, h = cv2.boundingRect(areaOI)
        stitched_image = stitched_image[y:y + h, x:x + w]
        cv2.imshow("Final Cropped Image", stitched_image)
        cv2.imwrite('stitched_image.jpg', stitched_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print("Image stitching failed.")

if __name__ == "__main__":
    image_stitcher()
    print("Image stitching complete.")
