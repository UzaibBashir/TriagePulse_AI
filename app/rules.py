RULE_VERSION='demo-rules-v1'
def assess(v):
    rules=[]
    # Demonstration thresholds are configurable engineering examples, not clinical guidance.
    for field, limit, comparison, rule_id, label in [
        ('heart_rate',130,'high','DEMO-HR-HIGH','heart rate above the demonstration threshold'),
        ('heart_rate',45,'low','DEMO-HR-LOW','heart rate below the demonstration threshold'),
        ('respiratory_rate',30,'high','DEMO-RR-HIGH','respiratory rate above the demonstration threshold'),
        ('oxygen_saturation',90,'low','DEMO-SPO2-LOW','oxygen saturation below the demonstration threshold'),
        ('systolic_bp',85,'low','DEMO-SBP-LOW','systolic blood pressure below the demonstration threshold'),
        ('temperature',39,'high','DEMO-TEMP-HIGH','temperature above the demonstration threshold')]:
        x=v.get(field)
        if x is not None and ((comparison=='high' and x>=limit) or (comparison=='low' and x<=limit)):
            rules.append({'id':rule_id,'measurement':field,'value':x,'explanation':label})
    if any(r['id'] in ('DEMO-SPO2-LOW','DEMO-SBP-LOW') for r in rules): category='Critical rule triggered'
    elif rules: category='Elevated concern'
    else: category='Routine monitoring'
    return {'category':category,'rules':rules,'explanation':'; '.join(r['explanation'] for r in rules) if rules else 'No configured demonstration rule was triggered. Continue routine monitoring and review data quality.'}
