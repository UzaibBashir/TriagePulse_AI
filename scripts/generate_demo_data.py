import uuid
from datetime import datetime,timezone
from app import create_app
from app.routes import api
def main():
    app=create_app()
    with app.test_client() as c:
        for i in range(1,9):
            concerning=i in (3,7)
            c.post('/api/v1/observations',json={'event_id':str(uuid.uuid4()),'patient_id':f'SIM-{i:03d}','observed_at':datetime.now(timezone.utc).isoformat(),'heart_rate':145 if concerning else 72+i,'respiratory_rate':32 if concerning else 14+i%4,'oxygen_saturation':88 if concerning else 97,'systolic_bp':84 if concerning else 116,'temperature':37.1,'is_simulated':True})
    print('Generated deterministic fictional demonstration observations.')
if __name__=='__main__':main()
