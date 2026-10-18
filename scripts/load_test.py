import argparse, json, statistics, time, urllib.request, uuid
def main():
    p=argparse.ArgumentParser(); p.add_argument('--url',default='http://127.0.0.1:8000'); p.add_argument('--events',type=int,default=100); args=p.parse_args(); xs=[]
    for i in range(args.events):
        body=json.dumps({'event_id':str(uuid.uuid4()),'patient_id':f'LOAD-{i%10:03d}','heart_rate':80,'respiratory_rate':16,'oxygen_saturation':98,'systolic_bp':120,'temperature':36.8,'is_simulated':True}).encode(); req=urllib.request.Request(args.url+'/api/v1/observations',body,{'Content-Type':'application/json'}); t=time.perf_counter()
        with urllib.request.urlopen(req) as r:r.read()
        xs.append((time.perf_counter()-t)*1000)
    xs.sort(); q=lambda x:round(xs[min(len(xs)-1,int((len(xs)-1)*x))],2); print(json.dumps({'events':len(xs),'duration_seconds':round(sum(xs)/1000,2),'p50_ms':q(.5),'p95_ms':q(.95),'p99_ms':q(.99) if len(xs)>=100 else None,'concurrency':1},indent=2))
if __name__=='__main__':main()
