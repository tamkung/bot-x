from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import os
import importlib
import main_script  # แทนที่ด้วยชื่อไฟล์ของสคริปต์หลักคุณ (ไม่ต้องมี .py)

class CodeChangeHandler(FileSystemEventHandler):
    def __init__(self, module_name):
        self.module_name = module_name

    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            print(f"{event.src_path} has been modified, reloading...")
            self.reload_module()

    def reload_module(self):
        try:
            module = importlib.import_module(self.module_name)
            importlib.reload(module)
            print("Module reloaded successfully.")
            module.main()
        except Exception as e:
            print(f"Error reloading module: {e}")

if __name__ == "__main__":
    module_name = "main_script"  # เปลี่ยนเป็นชื่อไฟล์ของสคริปต์หลัก
    path = os.path.dirname(os.path.abspath(__file__))

    event_handler = CodeChangeHandler(module_name)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
