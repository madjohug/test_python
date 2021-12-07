import threading

def loop():
  threading.Timer(1.0, loop).start()
  
  

loop()
