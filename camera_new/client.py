import asyncio
import websockets
import cv2
import base64
import numpy as np
import sys
import config

if len(sys.argv) < 2:
    print("Usage: python3 client.py <ws://ip:port>")
    sys.exit(1)

PORT = sys.argv[1]
URI =  f"ws://{config.IP}:{PORT}"

async def receive_video():
    async with websockets.connect(URI) as websocket:
        print(f"[+] Connected to {URI}")
        try:
            while True:
                data = await websocket.recv()
                img_data = base64.b64decode(data)
                nparr = np.frombuffer(img_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                if frame is not None:
                    cv2.imshow(f"Video Stream - {config.IP}:{PORT}", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
        except websockets.exceptions.ConnectionClosed:
            print("[-] Connection closed by server.")
        finally:
            cv2.destroyAllWindows()

if __name__ == "__main__":
    asyncio.run(receive_video())
