from PyQt6.QtCore import QThread, pyqtSignal

class AIThread(QThread):
    log_signal = pyqtSignal(str)
    
    def __init__(self, agent, steps, delay):
        super().__init__()
        self.agent = agent
        self.steps = steps
        self.delay = delay
    
    def run(self):
        try:
            self.log_signal.emit("AI线程启动")
            self.agent.run(steps=self.steps, delay=self.delay)
        except Exception as e:
            self.log_signal.emit(f"AI运行错误: {e}")
        finally:
            self.log_signal.emit("AI线程结束") 