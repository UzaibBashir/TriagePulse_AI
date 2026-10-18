import threading, time
from collections import deque
class Metrics:
    def __init__(self): self.lock=threading.Lock(); self.samples=deque(maxlen=2000); self.requests=0; self.success=0; self.errors=0; self.processed=0; self.duplicates=0; self.invalid=0; self.simulated=0
    def record(self, elapsed, status):
        with self.lock:
            self.samples.append(elapsed); self.requests+=1; self.success += status < 400; self.errors += status >= 400
    def snapshot(self):
        with self.lock:
            xs=sorted(self.samples)
            q=lambda p: round(xs[min(len(xs)-1, int((len(xs)-1)*p))*1]*1000,2) if xs else None
            return {'request_count':self.requests,'successful_requests':self.success,'error_count':self.errors,'api_latency_ms':{'p50':q(.50),'p95':q(.95),'p99':q(.99) if len(xs)>=100 else None,'samples':len(xs)},'observations_processed':self.processed,'duplicate_events_rejected':self.duplicates,'invalid_observations_rejected':self.invalid,'simulator_events_generated':self.simulated}
