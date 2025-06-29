import asyncio
import websockets
import cv2
import base64
import numpy as np
import sys
import os
import config

if len(sys.argv) < 2:
    print("Usage: python3 client.py <port>")
    sys.exit(1)

PORT = sys.argv[1]
URI = f"ws://{config.IP}:{PORT}"

def get_unique_filename(folder, base_name="stitched_image", ext=".jpg"):
    """
    Returns a unique filename in the given folder by checking for existing files.
    """
    i = 1
    while True:
        filename = f"{base_name}{'' if i == 1 else f'_{i}'}{ext}"
        path = os.path.join(folder, filename)
        if not os.path.exists(path):
            return path
        i += 1

async def receive_stitched_image():
    async with websockets.connect(URI) as websocket:
        print(f"[+] Connected to {URI}")
        try:
            data = await websocket.recv()

            if data == "STITCHING_FAILED":
                print("[-] Server reported stitching failure.")
                return

            # Decode Base64 image
            img_data = base64.b64decode(data)
            nparr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is not None:
                # Prepare save folder and unique file path
                save_folder = "stitched_image"
                os.makedirs(save_folder, exist_ok=True)
                save_path = get_unique_filename(save_folder)

                # Save the image
                cv2.imwrite(save_path, frame)
                print(f"[Saved] Image saved as {save_path}")

                # Show the image
                cv2.imshow(f"Stitched Image - {config.IP}:{PORT}", frame)
                print("[Display] Showing stitched image. Press any key to close.")
                cv2.waitKey(0)
        except websockets.exceptions.ConnectionClosed:
            print("[-] Connection closed by server.")
        finally:
            cv2.destroyAllWindows()

if __name__ == "__main__":
    asyncio.run(receive_stitched_image())
