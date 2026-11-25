"""Synthetic ISP panel, deterministic seed. No real personal information."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parent
SEED=271828

def generate():
 r=np.random.default_rng(SEED);months=pd.date_range('2024-01-01','2025-12-01',freq='MS');out=ROOT/'data/raw';out.mkdir(parents=True,exist_ok=True)
 plans=pd.DataFrame([(1,'Essential',50,8000),(2,'Plus',120,14000),(3,'Premium',250,22000)],columns=['plan_id','plan_name','allowance_gb','base_fee_ngn'])
 areas=pd.DataFrame([(1,'Metro Central','Urban'),(2,'Metro East','Urban'),(3,'Metro West','Urban'),(4,'Outer North','Peri-urban'),(5,'Outer South','Peri-urban')],columns=['area_id','area_name','area_type'])
 service=[]
 for mi,m in enumerate(months):
  for area in range(1,6):
   degraded=area==4 and 14<=mi<=17
   outage=round(float(np.clip(r.gamma(1.8,1.2)+(3 if area>=4 else 0)+(12 if degraded else 0),0,60)),2)
   service.append(dict(service_id=len(service)+1,area_id=area,month=m.strftime('%Y-%m-%d'),outage_hours=outage,network_incidents=int(r.poisson(1+outage/4))))
 service=pd.DataFrame(service);customers=[];records=[]
 weights=np.linspace(1,1.65,24);weights[[2,8,14,20]]*=1.7;weights/=weights.sum()
 acquired=r.choice(24,4000,p=weights)
 for cid,mi0 in enumerate(acquired,1):
  area=int(r.choice([1,2,3,4,5],p=[.28,.22,.20,.17,.13]));channel=str(r.choice(['Digital','Referral','Retail'],p=[.48,.27,.25]));auto=int(r.random()<.57);segment=str(r.choice(['Home','Remote worker','Microbusiness'],p=[.65,.25,.10]))
  customers.append(dict(customer_id=cid,area_id=area,activation_month=months[mi0].strftime('%Y-%m-%d'),acquisition_channel=channel,segment=segment,autopay=auto))
  pid=int(r.choice([1,2,3],p=[.50,.35,.15]));propensity=float(r.beta(2,8))
  for mi in range(mi0,24):
   tenure=mi-mi0
   if tenure>0 and r.random()<.025:pid=int(r.choice([1,2,3],p=[.30,.45,.25]))
   plan=plans.iloc[pid-1];network=service.iloc[mi*5+area-1];allow=float(plan.allowance_gb)
   used=round(float(np.clip(r.lognormal(np.log(allow*(.65 if segment=='Home' else .85)),.3)*(1-network.outage_hours/720),0,allow)),2)
   tickets=int(r.poisson(.15+network.outage_hours*.06+.2*(used>=allow*.95)))
   fee=int(plan.base_fee_ngn*(1.08 if mi>=12 else 1));discount=round(fee*.15,2) if tenure<3 and channel=='Digital' else 0
   credit=round((fee-discount)*.10,2) if network.outage_hours>8 else 0
   hazard=.012+.018*(tenure<=2)+.035*(tenure==3 and channel=='Digital')+.0018*network.outage_hours+.006*tickets+.025*propensity-.008*auto
   churn=int(r.random()<np.clip(hazard,.003,.30));status='Churned' if churn else 'Retained'
   survey=None
   if r.random()<(.22 if churn else .34):survey=int(np.clip(round(r.normal(4.4-network.outage_hours*.08-.2*tickets,.65)),1,5))
   records.append(dict(snapshot_id=len(records)+1,customer_id=cid,plan_id=pid,month=months[mi].strftime('%Y-%m-%d'),tenure_month=tenure,usage_gb=used,support_tickets=tickets,gross_fee_ngn=fee,promo_discount_ngn=discount,service_credit_ngn=credit,end_status=status,satisfaction_score=survey))
   if churn:break
 customers=pd.DataFrame(customers);snap=pd.DataFrame(records)
 # One corrupted row per selected customer; cleaner excludes the entire history.
 bad_ids=r.choice(customers.customer_id,35,replace=False);answer=[]
 for k,cid in enumerate(bad_ids):
  idx=int(r.choice(snap.index[snap.customer_id==cid]));field='plan_id' if k<20 else 'gross_fee_ngn';snap.loc[idx,field]=999 if k<20 else -500
  answer.append(dict(snapshot_id=int(snap.loc[idx,'snapshot_id']),customer_id=int(cid),issue='unknown_plan' if k<20 else 'negative_fee'))
 for idx in r.choice(snap.index,120,replace=False):snap.loc[idx,'month']=pd.Timestamp(snap.loc[idx,'month']).strftime('%d/%m/%Y')
 for idx in r.choice(snap.index,180,replace=False):snap.loc[idx,'end_status']=' '+snap.loc[idx,'end_status'].upper()+' '
 # Optional survey missingness is realistic nonresponse, not an error.
 snap=pd.concat([snap,snap.iloc[r.choice(len(snap),100,replace=False)]],ignore_index=True)
 tables={'plans':plans,'areas':areas,'customers':customers,'area_service_months':service,'subscription_months':snap}
 for name,df in tables.items():df.to_csv(out/f'{name}.csv',index=False)
 pd.DataFrame(answer).to_csv(ROOT/'reports/injected_issues.csv',index=False)
 (ROOT/'reports/generation.json').write_text(json.dumps({'seed':SEED,'raw_rows':{k:len(v) for k,v in tables.items()},'duplicate_copies':100,'invalid_customers':35},indent=2))
 print({k:len(v) for k,v in tables.items()})
if __name__=='__main__':generate()
