#!/usr/bin/env python3
"""Analyze aligned persistent control and matched existing conflict results.

Primary post-hoc contrast:
  interaction = (conflict persistent - conflict fresh)
              - (aligned persistent - aligned fresh)
within the exact same frozen 40 cases.
Negative interaction => persistent-vs-fresh gap is more negative under conflict.
"""
import argparse, json, random, statistics
from collections import defaultdict
from pathlib import Path

BOOT_SEED=2026092301
BOOT_N=10000


def load(path):
    return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]


def ci_boot(vals, seed=BOOT_SEED, n=BOOT_N):
    rng=random.Random(seed)
    m=len(vals)
    means=[]
    for _ in range(n):
        s=[vals[rng.randrange(m)] for __ in range(m)]
        means.append(sum(s)/m)
    means.sort()
    return means[int(0.025*n)], means[min(n-1,int(0.975*n))]


def exact_prop_zero_upper_95(n):
    return 1 - 0.025**(1/n)

ap=argparse.ArgumentParser()
ap.add_argument('--cases',required=True)
ap.add_argument('--aligned-results',required=True)
ap.add_argument('--conflict-results',required=True)
ap.add_argument('--output-json',default='results/aligned_control_analysis.json')
args=ap.parse_args()
case_rows=load(args.cases)
case_ids=[c['case_id'] for c in case_rows]
case_set=set(case_ids)
aligned=[r for r in load(args.aligned_results) if r.get('status')=='ok' and r.get('case_id') in case_set]
conflict=[r for r in load(args.conflict_results) if r.get('status')=='ok' and r.get('case_id') in case_set]

aidx={(r['case_id'],r['arm'],r['condition']):r for r in aligned}
cidx={(r['case_id'],r['arm'],r['condition']):r for r in conflict}

records=[]
for cid in case_ids:
    needa=[
      (cid,'aligned_sequential','H_L1_ALIGNED'),(cid,'aligned_sequential','H_L2_ALIGNED'),
      (cid,'aligned_sequential','H_L3_ALIGNED'),(cid,'aligned_sequential','H_L4_ALIGNED'),
      (cid,'fresh_aligned','H_L4_ALIGNED')]
    needc=[(cid,'sequential','H'),(cid,'sequential','H_L1'),(cid,'sequential','H_L2'),(cid,'sequential','H_L3'),(cid,'sequential','H_L4'),(cid,'fresh','H_L4')]
    missing=[k for k in needa if k not in aidx]+[k for k in needc if k not in cidx]
    if missing: raise SystemExit(f'Missing rows for {cid}: {missing}')
    ah1=aidx[(cid,'aligned_sequential','H_L1_ALIGNED')]
    ah2=aidx[(cid,'aligned_sequential','H_L2_ALIGNED')]
    ah3=aidx[(cid,'aligned_sequential','H_L3_ALIGNED')]
    ah4=aidx[(cid,'aligned_sequential','H_L4_ALIGNED')]
    af=aidx[(cid,'fresh_aligned','H_L4_ALIGNED')]
    ch=cidx[(cid,'sequential','H')]
    ch1=cidx[(cid,'sequential','H_L1')]
    ch2=cidx[(cid,'sequential','H_L2')]
    ch3=cidx[(cid,'sequential','H_L3')]
    ch4=cidx[(cid,'sequential','H_L4')]
    cf=cidx[(cid,'fresh','H_L4')]
    records.append({
      'case_id':cid,
      'aligned_seq_terminal':ah4['confidence'],'aligned_fresh':af['confidence'],
      'aligned_gap':ah4['confidence']-af['confidence'],
      'conflict_seq_terminal':ch4['confidence'],'conflict_fresh':cf['confidence'],
      'conflict_gap':ch4['confidence']-cf['confidence'],
      'interaction':(ch4['confidence']-cf['confidence'])-(ah4['confidence']-af['confidence']),
      'aligned_terminal_agree':ah4['decision']==af['decision'],
      'aligned_e0_both':('E0' in ah4.get('dominant_evidence_ids',[])) and ('E0' in af.get('dominant_evidence_ids',[])),
      'aligned_traj':[ch['confidence'],ah1['confidence'],ah2['confidence'],ah3['confidence'],ah4['confidence']],
      'conflict_traj':[ch['confidence'],ch1['confidence'],ch2['confidence'],ch3['confidence'],ch4['confidence']],
    })

def mean(k): return sum(r[k] for r in records)/len(records)
def dir_counts(k):
    vals=[r[k] for r in records]
    return {'lower':sum(v<0 for v in vals),'equal':sum(v==0 for v in vals),'higher':sum(v>0 for v in vals)}

aligned_gaps=[r['aligned_gap'] for r in records]
conflict_gaps=[r['conflict_gap'] for r in records]
inter=[r['interaction'] for r in records]
aci=ci_boot(aligned_gaps,BOOT_SEED)
cci=ci_boot(conflict_gaps,BOOT_SEED+1)
ici=ci_boot(inter,BOOT_SEED+2)
atr=[sum(r['aligned_traj'][j] for r in records)/len(records) for j in range(5)]
ctr=[sum(r['conflict_traj'][j] for r in records)/len(records) for j in range(5)]
summary={
 'n':len(records),
 'bootstrap_n':BOOT_N,'bootstrap_seed':BOOT_SEED,
 'aligned_terminal':{
   'sequential_mean':mean('aligned_seq_terminal'),'fresh_mean':mean('aligned_fresh'),
   'seq_minus_fresh_mean':sum(aligned_gaps)/len(records),'median':statistics.median(aligned_gaps),
   'bootstrap_95_ci':aci,'direction_counts':dir_counts('aligned_gap'),
   'categorical_agreement_n':sum(r['aligned_terminal_agree'] for r in records),
   'e0_in_both_n':sum(r['aligned_e0_both'] for r in records),
 },
 'same_40_existing_conflict_terminal':{
   'sequential_mean':mean('conflict_seq_terminal'),'fresh_mean':mean('conflict_fresh'),
   'seq_minus_fresh_mean':sum(conflict_gaps)/len(records),'median':statistics.median(conflict_gaps),
   'bootstrap_95_ci':cci,'direction_counts':dir_counts('conflict_gap'),
 },
 'polarity_by_persistence_interaction':{
   'definition':'(conflict persistent-fresh) - (aligned persistent-fresh)',
   'mean':sum(inter)/len(records),'median':statistics.median(inter),'bootstrap_95_ci':ici,
   'negative_n':sum(v<0 for v in inter),'zero_n':sum(v==0 for v in inter),'positive_n':sum(v>0 for v in inter),
 },
 'trajectory_means':{
   'states':['H','H+L1','H+L2','H+L3','H+L4'],
   'aligned':atr,'conflict':ctr,
 },
}
Path(args.output_json).parent.mkdir(parents=True,exist_ok=True)
Path(args.output_json).write_text(json.dumps(summary,indent=2),encoding='utf-8')
print('ALIGNED PERSISTENT CONTROL — POST-HOC ANALYSIS')
print('n:',summary['n'])
print('aligned persistent vs fresh:',round(summary['aligned_terminal']['seq_minus_fresh_mean'],2),'CI',tuple(round(x,2) for x in aci),dir_counts('aligned_gap'))
print('same-40 conflict persistent vs fresh:',round(summary['same_40_existing_conflict_terminal']['seq_minus_fresh_mean'],2),'CI',tuple(round(x,2) for x in cci),dir_counts('conflict_gap'))
print('difference-in-differences [conflict gap - aligned gap]:',round(summary['polarity_by_persistence_interaction']['mean'],2),'CI',tuple(round(x,2) for x in ici))
print('aligned terminal categorical agreement:',summary['aligned_terminal']['categorical_agreement_n'],'/ 40')
print('aligned E0 in both terminal outputs:',summary['aligned_terminal']['e0_in_both_n'],'/ 40')
print('aligned trajectory means:',[round(x,2) for x in atr])
print('conflict trajectory means:',[round(x,2) for x in ctr])
print('analysis_json:',args.output_json)
