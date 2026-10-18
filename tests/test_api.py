import json
from app import create_app
def client(tmp_path):
    app=create_app({'TESTING':True,'DATABASE':str(tmp_path/'test.sqlite3')}); return app.test_client()
def sample(**kwargs):
    d={'event_id':'event-1','patient_id':'SIM-001','heart_rate':145,'respiratory_rate':32,'oxygen_saturation':88,'systolic_bp':100,'temperature':37.2,'is_simulated':True}; d.update(kwargs); return d
def test_health_and_dashboard(tmp_path):
    c=client(tmp_path); assert c.get('/health').json['status']=='ok'; assert c.get('/api/v1/dashboard/summary').json['patient_count']==0
def test_ingestion_alert_ack_and_dedupe(tmp_path):
    c=client(tmp_path); r=c.post('/api/v1/observations',json=sample()); assert r.status_code==201; assert r.json['alert_id']; assert r.json['assessment']['rules']; assert c.post('/api/v1/observations',json=sample()).json['status']=='duplicate'; aid=r.json['alert_id']; assert c.post(f'/api/v1/alerts/{aid}/acknowledge').json['status']=='acknowledged'; assert c.get(f'/api/v1/alerts/{aid}').json['status']=='acknowledged'; assert c.get('/api/v1/dashboard/summary').json['observation_count']==1
def test_invalid_and_normal(tmp_path):
    c=client(tmp_path); r=c.post('/api/v1/observations',json=sample(heart_rate='bad')); assert r.status_code==422; n=c.post('/api/v1/observations',json=sample(event_id='normal',patient_id='SIM-002',heart_rate=78,respiratory_rate=16,oxygen_saturation=98,systolic_bp=120,temperature=36.8)); assert n.status_code==201 and not n.json['alert_id']; assert c.get('/api/v1/alerts').json['items']==[]
def test_simulator_lifecycle(tmp_path):
    c=client(tmp_path); assert c.get('/api/v1/simulator/status').json['status']=='stopped'; assert c.post('/api/v1/simulator/start',json={'scenario':'normal'}).json['status']=='running'; assert c.post('/api/v1/simulator/pause').json['status']=='paused'; assert c.post('/api/v1/simulator/resume').json['status']=='running'; assert c.post('/api/v1/simulator/reset').json['status']=='stopped'
