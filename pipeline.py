from pathlib import Path
import sqlite3,re,json,subprocess,sys
import pandas as pd
ROOT=Path(__file__).resolve().parent

def queries(file):
 parts=re.split(r'-- name: (\w+)\n',file.read_text());return zip(parts[1::2],parts[2::2])

def main():
 if not (ROOT/'data/raw/subscription_months.csv').exists():
  from generate_data import generate
  generate()
 con=sqlite3.connect(ROOT/'telecom.sqlite');textcols={'plan_name','area_name','area_type','activation_month','acquisition_channel','segment','month','end_status'}
 for f in (ROOT/'data/raw').glob('*.csv'):
  df=pd.read_csv(f,dtype=str,keep_default_na=False)
  for col in df.columns:
   if col not in textcols:assert df[col].map(lambda v:v=='' or bool(re.fullmatch(r'-?\d+(\.\d+)?',v))).all(),col
  df.to_sql('raw_'+f.stem,con,index=False,if_exists='replace')
 con.executescript((ROOT/'sql/01_clean.sql').read_text());checks={n:con.execute(q).fetchone()[0] for n,q in queries(ROOT/'sql/03_validation.sql')};assert not any(checks.values()),checks
 counts={n:con.execute('SELECT COUNT(*) FROM '+n).fetchone()[0] for n in ['raw_subscription_months','subscription_months','invalid_rows','quarantine','eligible_customers','subscription_mart']}
 assert counts['raw_subscription_months']==counts['subscription_months']+counts['quarantine']+100
 assert counts['subscription_mart']==counts['subscription_months'];assert counts['eligible_customers']==3965;assert counts['invalid_rows']==35
 assert con.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
 for n in ['plans','areas','customers','eligible_customers','area_service_months','subscription_months','subscription_mart','invalid_rows','quarantine']:
  pd.read_sql('SELECT * FROM '+n,con).to_csv(ROOT/'data/clean'/f'{n}.csv',index=False)
 for name,q in queries(ROOT/'sql/02_analysis.sql'):pd.read_sql(q,con).to_csv(ROOT/'reports'/f'{name}.csv',index=False)
 m=pd.read_csv(ROOT/'reports/monthly.csv');assert (m.opening_customers.iloc[1:].to_numpy()==m.closing_customers.iloc[:-1].to_numpy()).all();assert (m.opening_customers+m.acquired_customers-m.churned_customers==m.closing_customers).all()
 co=pd.read_csv(ROOT/'reports/cohort_retention.csv')
 assert co.retention.between(0,1).all()
 for _,group in co.groupby('activation_month'):
  assert (group.sort_values('age').retained.diff().dropna()<=0).all()
 assert len(co)==300  # 24+23+...+1 observed cohort-age cells.
 assert co[co.age==0].cohort_size.sum()==counts['eligible_customers']
 assert abs(m.gross_ngn.sum()-m.promo_ngn.sum()-m.credit_ngn.sum()-m.net_ngn.sum())<.01
 audit={'counts':counts,'duplicates_removed':100,'failed_checks':checks,'customer_flow_reconciles':True};(ROOT/'reports/validation.json').write_text(json.dumps(audit,indent=2));con.close()
 for script in ['analysis/eda.py','dashboard/dashboard.py']:subprocess.run([sys.executable,str(ROOT/script)],check=True)
 print(json.dumps(audit,indent=2))
if __name__=='__main__':main()
