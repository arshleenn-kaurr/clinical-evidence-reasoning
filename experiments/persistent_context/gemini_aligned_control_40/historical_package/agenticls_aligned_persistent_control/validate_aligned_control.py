#!/usr/bin/env python3
import argparse, json
from collections import Counter, defaultdict
from pathlib import Path


def load(path):
    p=Path(path)
    if not p.exists(): return []
    return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]

ap=argparse.ArgumentParser()
ap.add_argument('results')
ap.add_argument('--attempt-log')
ap.add_argument('--expected-cases',type=int,default=40)
args=ap.parse_args()
rows=load(args.results)
ok=[r for r in rows if r.get('status')=='ok']
ids=[r.get('run_id') for r in ok]
by=defaultdict(set)
for r in ok:
    by[r['case_id']].add((r['arm'],r['condition']))
required={
 ('aligned_sequential','H_L1_ALIGNED'),
 ('aligned_sequential','H_L2_ALIGNED'),
 ('aligned_sequential','H_L3_ALIGNED'),
 ('aligned_sequential','H_L4_ALIGNED'),
 ('fresh_aligned','H_L4_ALIGNED'),
}
complete=sum(v==required for v in by.values())
source_meta_ok=sum(
  1 for r in ok if r.get('arm')=='aligned_sequential'
  and r.get('source_h_run_id') and r.get('source_h_raw_text_sha256')
)
expected=args.expected_cases*5
print('ALIGNED CONTROL OPERATIONAL VALIDATION')
print('successful_rows:',len(ok))
print('expected_successful_rows:',expected)
print('unique_successful_run_ids:',len(set(ids)))
print('duplicate_successful_run_ids:',len(ids)-len(set(ids)))
print('cases_touched:',len(by))
print('fully_complete_5-new-call_cases:',complete)
print('sequential_rows_with_source_H_provenance:',source_meta_ok)
if args.attempt_log:
    att=load(args.attempt_log)
    print('attempt_rows:',len(att))
    print('attempt_statuses:',dict(Counter(r.get('status') for r in att)))
    shas=defaultdict(set)
    for r in att:
        if r.get('run_id') and r.get('request_sha256'):
            shas[r['run_id']].add(r['request_sha256'])
    changed=[rid for rid,s in shas.items() if len(s)>1]
    print('run_ids_with_changed_request_sha_across_retries:',len(changed))
passed=(len(ok)==expected and len(set(ids))==expected and complete==args.expected_cases and source_meta_ok==args.expected_cases*4)
print('operational_status:', 'PASS' if passed else 'INCOMPLETE_OR_FAIL')
raise SystemExit(0 if passed else 1)
