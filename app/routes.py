import json, time, uuid
from datetime import datetime, timezone
from flask import Blueprint, current_app, jsonify, request, g
from .db import get_db
from .rules import assess, RULE_VERSION
api=Blueprint('api',__name__)
VITALS={'heart_rate':(20,250),'respiratory_rate':(3,80),'oxygen_saturation':(0,100),'systolic_bp':(30,300),'temperature':(25,45)}
def now(): return datetime.now(timezone.utc).isoformat()
def rowdict(r): return dict(r) if r else None
@api.before_app_request
def begin_timer(): g.started=time.perf_counter()
@api.after_app_request
def end_timer(response):
    m=current_app.extensions.get('metrics')
    if m: m.record(time.perf_counter()-getattr(g,'started',time.perf_counter()), response.status_code)
    response.headers['X-Prototype-Notice']='Synthetic decision-support prototype; human review required.'
    return response
def err(msg, code=400, errors=None): return jsonify(error='invalid_request' if code==400 else 'request_failed',message=msg,details=errors or {}),code
@api.get('/api/v1/metrics')
def metrics():
    db=get_db(); out=current_app.extensions['metrics'].snapshot(); out['active_alerts']=db.execute("select count(*) from alerts where status='active'").fetchone()[0]; return jsonify(out)
@api.get('/api/v1/dashboard/summary')
def summary():
    db=get_db(); return jsonify(patient_count=db.execute('select count(*) from patients').fetchone()[0], active_alerts=db.execute("select count(*) from alerts where status='active'").fetchone()[0], acknowledged_alerts=db.execute("select count(*) from alerts where status='acknowledged'").fetchone()[0], observation_count=db.execute('select count(*) from observations').fetchone()[0], latest_observation=rowdict(db.execute('select * from observations order by observed_at desc limit 1').fetchone()), health='ok', prototype=True)
@api.get('/api/v1/dashboard/activity')
def activity():
    db=get_db(); return jsonify(observations=[dict(r) for r in db.execute('select * from observations order by id desc limit 20')], alerts=[dict(r) for r in db.execute('select * from alerts order by id desc limit 20')])
@api.get('/api/v1/patients')
def patients():
    db=get_db(); q=request.args.get('q','').strip(); rows=db.execute('select p.id,p.created_at, (select count(*) from alerts a where a.patient_id=p.id and a.status="active") active_alerts, (select observed_at from observations o where o.patient_id=p.id order by observed_at desc limit 1) last_seen from patients p where p.id like ? order by p.id limit 200', (f'%{q}%',)).fetchall(); return jsonify(items=[dict(r) for r in rows],count=len(rows))
@api.get('/api/v1/patients/<patient_id>')
def patient(patient_id):
    db=get_db(); p=db.execute('select * from patients where id=?',(patient_id,)).fetchone()
    if not p:return err('Patient not found.',404)
    latest=db.execute('select * from observations where patient_id=? order by observed_at desc limit 1',(patient_id,)).fetchone(); return jsonify(patient=dict(p),latest=rowdict(latest),active_alerts=db.execute("select count(*) from alerts where patient_id=? and status='active'",(patient_id,)).fetchone()[0])
@api.get('/api/v1/patients/<patient_id>/timeline')
def timeline(patient_id):
    db=get_db(); rows=db.execute('select o.*,a.category,a.explanation,a.triggered_rules from observations o left join assessments a on a.observation_id=o.id where o.patient_id=? order by o.observed_at desc limit 200',(patient_id,)).fetchall(); return jsonify(items=[dict(r) for r in rows])
@api.post('/api/v1/observations')
def ingest():
    data=request.get_json(silent=True)
    if not isinstance(data,dict):return err('A JSON object is required.')
    errors={}; event_id=data.get('event_id') or str(uuid.uuid4()); patient_id=data.get('patient_id')
    if not isinstance(patient_id,str) or not patient_id.strip() or len(patient_id)>80: errors['patient_id']='A non-empty synthetic identifier is required.'
    vals={}
    for k,(lo,hi) in VITALS.items():
        x=data.get(k)
        if x is None: vals[k]=None; continue
        if isinstance(x,bool) or not isinstance(x,(int,float)): errors[k]='Must be numeric.'
        elif not lo<=float(x)<=hi: errors[k]=f'Must be within configured input bounds {lo}–{hi}.'
        else: vals[k]=float(x)
    if not any(v is not None for v in vals.values()): errors['measurements']='At least one measurement is required.'
    observed=data.get('observed_at') or now()
    try: observed=datetime.fromisoformat(observed.replace('Z','+00:00')).astimezone(timezone.utc).isoformat()
    except Exception: errors['observed_at']='Must be an ISO-8601 timestamp.'
    if errors: current_app.extensions['metrics'].invalid+=1; return err('Observation validation failed.',422,errors)
    if len(str(event_id))>120:return err('event_id is too long.',422)
    db=get_db()
    try:
        old=db.execute('select id from observations where event_id=?',(str(event_id),)).fetchone()
        if old: current_app.extensions['metrics'].duplicates+=1; return jsonify(status='duplicate',observation_id=old['id']),200
        db.execute('begin immediate')
        db.execute('insert or ignore into patients(id,created_at,is_simulated) values(?,?,?)',(patient_id.strip(),now(),int(bool(data.get('is_simulated',True)))))
        cur=db.execute('insert into observations(event_id,patient_id,observed_at,heart_rate,respiratory_rate,oxygen_saturation,systolic_bp,temperature,is_simulated,quality) values(?,?,?,?,?,?,?,?,?,?)',(str(event_id),patient_id.strip(),observed,*[vals[k] for k in VITALS],int(bool(data.get('is_simulated',True))),'valid'))
        obs_id=cur.lastrowid; result=assess(vals); assessment=db.execute('insert into assessments(observation_id,category,explanation,triggered_rules,model_score,model_version,created_at) values(?,?,?,?,?,?,?)',(obs_id,result['category'],result['explanation'],json.dumps(result['rules']),None,None,RULE_VERSION)); aid=assessment.lastrowid
        alert_id=None
        if result['rules']:
            ac=db.execute('insert into alerts(assessment_id,patient_id,category,explanation,created_at) values(?,?,?,?,?)',(aid,patient_id.strip(),result['category'],result['explanation'],now())); alert_id=ac.lastrowid; db.execute('insert into audit_events(alert_id,event_type,detail,created_at) values(?,?,?,?)',(alert_id,'created',json.dumps(result['rules']),now()))
        db.commit(); m=current_app.extensions['metrics']; m.processed+=1; m.simulated+=int(bool(data.get('is_simulated',True)))
        return jsonify(status='accepted',observation_id=obs_id,assessment={'category':result['category'],'explanation':result['explanation'],'rules':result['rules'],'rule_version':RULE_VERSION},alert_id=alert_id),201
    except Exception as e: db.rollback(); current_app.logger.exception('Observation processing failed'); return err('Observation could not be processed.',500)
@api.get('/api/v1/observations')
def observations():
    page=max(1,request.args.get('page',1,type=int)); limit=min(100,max(1,request.args.get('limit',25,type=int))); db=get_db(); rs=db.execute('select * from observations order by observed_at desc limit ? offset ?',(limit,(page-1)*limit)).fetchall(); return jsonify(items=[dict(r) for r in rs],page=page,limit=limit)
@api.get('/api/v1/alerts')
def alerts():
    status=request.args.get('status'); db=get_db(); sql='select * from alerts'; args=()
    if status in ('active','acknowledged'):sql+=' where status=?';args=(status,)
    sql+=' order by id desc limit 200'; return jsonify(items=[dict(r) for r in db.execute(sql,args)])
@api.get('/api/v1/alerts/<int:alert_id>')
def alert(alert_id):
    r=get_db().execute('select a.*,asmt.triggered_rules,asmt.observation_id from alerts a join assessments asmt on asmt.id=a.assessment_id where a.id=?',(alert_id,)).fetchone(); return (jsonify(dict(r)),200) if r else err('Alert not found.',404)
@api.post('/api/v1/alerts/<int:alert_id>/acknowledge')
def acknowledge(alert_id):
    db=get_db(); r=db.execute('select * from alerts where id=?',(alert_id,)).fetchone()
    if not r:return err('Alert not found.',404)
    if r['status']=='active':
        db.execute("update alerts set status='acknowledged',acknowledged_at=?,acknowledged_by=? where id=?",(now(),'reviewer',alert_id)); db.execute('insert into audit_events(alert_id,event_type,detail,created_at) values(?,?,?,?)',(alert_id,'acknowledged','Acknowledgement recorded; source observation unchanged.',now())); db.commit()
    return jsonify(status='acknowledged',alert_id=alert_id)
@api.get('/api/v1/simulator/status')
def sim_status(): return jsonify(status=current_app.config.get('SIM_STATUS','stopped'),scenario=current_app.config.get('SIM_SCENARIO'),generated=current_app.extensions['metrics'].simulated)
@api.post('/api/v1/simulator/<action>')
def simulator(action):
    if action not in ('start','pause','resume','reset'):return err('Unsupported simulator action.',404)
    data=request.get_json(silent=True) or {}; status=current_app.config.get('SIM_STATUS','stopped')
    if action=='start': current_app.config['SIM_STATUS']='running'; current_app.config['SIM_SCENARIO']=data.get('scenario','normal')
    elif action=='pause' and status=='running': current_app.config['SIM_STATUS']='paused'
    elif action=='resume' and status=='paused': current_app.config['SIM_STATUS']='running'
    elif action=='reset':current_app.config['SIM_STATUS']='stopped'; current_app.config['SIM_SCENARIO']=None
    return jsonify(status=current_app.config.get('SIM_STATUS','stopped'),scenario=current_app.config.get('SIM_SCENARIO'),message='Simulator controls track state; submit events to /api/v1/observations to generate records.')
