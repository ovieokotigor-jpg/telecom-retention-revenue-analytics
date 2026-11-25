"""Seven explanatory analyses; run after the pipeline prepares SQL reports."""
from pathlib import Path
import json,sqlite3,sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
INK='#25334c';BLUE='#466cae';TEAL='#178b88';CORAL='#d36b61';PALE='#e9eff6'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False})
def main():
 read=lambda n:pd.read_csv(ROOT/'reports'/f'{n}.csv')
 m=read('monthly');co=read('cohort_retention');risk=read('tenure_risk');out=read('outage_bands');ch=read('channels');pl=read('plan_performance')
 with sqlite3.connect(ROOT/'telecom.sqlite') as c:d=pd.read_sql('SELECT * FROM subscription_mart',c)
 charts=[]
 def save(fig,name,title,note):
  fig.suptitle(title,x=.06,ha='left',fontsize=16,weight='bold',color=INK);fig.text(.06,.02,note,fontsize=8,color='#657185');fig.tight_layout(rect=[.02,.075,.98,.90]);fig.savefig(ROOT/'charts'/name,dpi=160);plt.close(fig);charts.append((name,title,note))
 v=co.pivot(index='activation_month',columns='age',values='retention');fig,ax=plt.subplots(figsize=(13,8));cmap=plt.get_cmap('YlGnBu').copy();cmap.set_bad('#eeeeee');im=ax.imshow(np.ma.masked_invalid(v),vmin=0,vmax=1,cmap=cmap,aspect='auto')
 for i in range(len(v)):
  for j in range(len(v.columns)):
   if pd.notna(v.iloc[i,j]):ax.text(j,i,f'{v.iloc[i,j]:.0%}',ha='center',va='center',fontsize=6,color='white' if v.iloc[i,j]>.65 else INK)
 ax.set_yticks(range(len(v)),v.index.str[:7],fontsize=7);ax.set_xticks(range(24));ax.set_xlabel('Months since activation (0 = first month-end)');fig.colorbar(im,ax=ax,label='End-of-month retained share')
 save(fig,'01_cohort_retention.png','Compare retention at the same customer age','Grey cells have not yet been observed. Month 0 can be below 100% because first-month exits are included.')
 fig,ax=plt.subplots(figsize=(11,5));x=np.arange(24);ax.bar(x,m.acquired_customers,color=TEAL,label='New subscriptions');ax.bar(x,-m.churned_customers,color=CORAL,label='Churned subscriptions');ax.plot(x,m.acquired_customers-m.churned_customers,'o-',color=INK,label='Net additions',lw=1.4);ax.axhline(0,color='#b4bdca',lw=.8);ax.set_xticks(x[::2],m.month.str[:7].iloc[::2],rotation=30);ax.set_ylabel('Customers');ax.legend(frameon=False,ncol=3,fontsize=9)
 save(fig,'02_customer_flow.png','Acquisition can conceal an underlying retention problem','Opening + new − exits = closing customers. This is a newly launched fictional provider; opening base starts at zero.')
 fig,ax=plt.subplots(figsize=(10,5));ax.plot(risk.tenure_month,risk.exposure_churn_rate*100,'o-',color=CORAL);ax.set_xlabel('Months since activation');ax.set_ylabel('Monthly exposed-customer churn (%)');ax.set_ylim(0,max(risk.exposure_churn_rate)*120)
 for _,r in risk.iloc[::3].iterrows():ax.annotate(f'n={int(r.exposed):,}',(r.tenure_month,r.exposure_churn_rate*100),xytext=(0,10),textcoords='offset points',fontsize=7,ha='center')
 save(fig,'03_tenure_risk.png','Early-life churn differs from later customer experience','Exposure includes new and opening customers. Older tenure groups contain survivors and fewer acquisition cohorts.')
 fig,axes=plt.subplots(1,2,figsize=(11,5));labels=out.outage_band.str.split(': ').str[-1];axes[0].bar(labels,out.exposure_churn_rate*100,color=CORAL);axes[0].set_ylabel('Monthly churn (%)');axes[1].bar(labels,out.tickets_per_100_months,color=TEAL);axes[1].set_ylabel('Tickets / 100 customer-months')
 for a in axes:a.set_xlabel('Area outage hours in the same month')
 save(fig,'04_outage_relationship.png','Service disruption and customer friction move together','Descriptive association with shared area-month exposures. Same-month outages are not a prospective churn prediction.')
 fig,ax=plt.subplots(figsize=(11,5));gross=m.gross_ngn.sum();vals=[gross,-m.promo_ngn.sum(),-m.credit_ngn.sum()];running=0
 for i,value in enumerate(vals):
  ax.bar(i,value/1e6,bottom=running/1e6,color=BLUE if i==0 else CORAL);running+=value;ax.text(i,(running if value>0 else running-value)/1e6+5,f'{value/1e6:+,.1f}',ha='center')
 ax.bar(3,running/1e6,color=TEAL);ax.text(3,running/1e6+5,f'{running/1e6:,.1f}',ha='center');ax.set_xticks(range(4),['Gross fees','Promotion discounts','Service credits','Net subscription']);ax.set_ylabel('NGN millions');assert abs(running-m.net_ngn.sum())<.01
 save(fig,'05_revenue_bridge.png','Reconcile headline fees to net subscription revenue','Full-month service assumed, including final month. Taxes, collections, bad debt and operating costs are outside scope.')
 fig,ax=plt.subplots(figsize=(10,5));ax.scatter(pl.arpu_ngn,pl.exposure_churn_rate*100,s=pl.customer_months/25,color=[BLUE,TEAL,CORAL],alpha=.8,edgecolor='white')
 for _,r in pl.iterrows():ax.annotate(r.plan_name,(r.arpu_ngn,r.exposure_churn_rate*100),xytext=(8,10),textcoords='offset points')
 ax.set_xlabel('Net subscription revenue / customer-month (NGN)');ax.set_ylabel('Monthly exposed-customer churn (%)');ax.margins(.3)
 save(fig,'06_plan_positioning.png','Read revenue and retention together','Bubble area represents customer-months. Customer mix and plan switching prevent a causal ranking of plan quality.')
 fig,ax=plt.subplots(figsize=(10,5))
 for name,g in d.groupby('acquisition_channel'):
  grouped=g.groupby('tenure_month').churned.mean();ax.plot(grouped.index,grouped.values*100,'o-',ms=3,label=name)
 ax.set_xlim(0,12);ax.set_xlabel('Months since activation (ages 0–12 shown)');ax.set_ylabel('Monthly exposed-customer churn (%)');ax.legend(frameon=False)
 save(fig,'07_channel_tenure.png','Compare acquisition channels within customer tenure','Digital promotion expires after the first three billed months in the simulation. Other customer differences remain uncontrolled.')
 latest=m.iloc[-1];top=ch.loc[ch.exposure_churn_rate.idxmax()];rate=d.churned.mean();mature=co[co.age==11];ret12=mature.retained.sum()/mature.cohort_size.sum()
 findings=f'''- December 2025 closing subscribers: **{int(latest.closing_customers):,}**.
- Net subscription revenue across the observed period: **NGN {m.net_ngn.sum()/1e6:,.2f} million**.
- Monthly exposure-based churn across all customer-months: **{rate:.2%}**. This is not a two-year customer churn probability.
- End-of-month-12 retention: **{ret12:.1%}**, pooled only across cohorts with 12 observed months (age 11).
- Highest observed acquisition-channel monthly churn: **{top.acquisition_channel}**, **{top.exposure_churn_rate:.2%}**. This is descriptive, not a causal channel effect.
- December 2025 net ARPU: **NGN {latest.arpu_ngn:,.0f}** per exposed customer-month.
'''
 (ROOT/'analysis/findings.md').write_text('# Calculated findings\n\n'+findings)
 gen=json.loads((ROOT/'reports/generation.json').read_text());audit=json.loads((ROOT/'reports/validation.json').read_text());counts='\n'.join(f'| {k}.csv | {v:,} |' for k,v in gen['raw_rows'].items())
 template=(ROOT/'README_TEMPLATE.md').read_text().replace('{{FINDINGS}}',findings).replace('{{COUNTS}}',counts).replace('{{CLEAN}}',f"{audit['counts']['subscription_months']:,}").replace('{{QUARANTINE}}',f"{audit['counts']['quarantine']:,}")
 template=template.replace('{{CHARTS}}','\n\n'.join(f'### {title}\n![{title}](charts/{name})\n{note}' for name,title,note in charts));(ROOT/'README.md').write_text(template)
 (ROOT/'reports/environment.json').write_text(json.dumps({'python':sys.version,'numpy':np.__version__,'pandas':pd.__version__,'matplotlib':matplotlib.__version__},indent=2));print(findings)
if __name__=='__main__':main()
