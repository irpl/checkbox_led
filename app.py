from typing import List
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

app = FastAPI()

# app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")
state = 0

class ConnectionManager:
  def __init__(self):
    self.connections: List[WebSocket] = []

  async def connect(self, websocket: WebSocket):
    await websocket.accept()
    self.connections.append(websocket)

  # todo remove websocket from connections list on close
  async def disconnect(self, websocket: WebSocket):
    self.connections.remove(websocket)

  async def broadcast(self, data):
    for connection in self.connections:
      await connection.send_bytes(data)
  
  # async def whisper(self, data, recipient: int):
  #   for connection in self.connections:
  #     if connection[0] == recipient:
  #       await connection.send_text(data)

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
def read_item(request: Request):
  return templates.TemplateResponse("index.html", {"request": request})

@app.get("/state")
def get_state():
  return state

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
  await manager.connect(websocket)
  try:
    while True:
      data = await websocket.receive_text()
      # print(data)
      global state 
      state = int(data)
      # data = state.to_bytes((state.bit_length() + 7) // 8, byteorder='big')
      data = state.to_bytes(4, 'big')
      print(data)
      # hex_data = bytes.fromhex(data["color"])
      await manager.broadcast(data)
      # manager.whisper(bytes.fromhex(data))
      # client.send(data.encode())
      
  except WebSocketDisconnect:
    await manager.disconnect(websocket)
    # client.close()
  finally:
    await manager.disconnect(websocket)