import yaml
import pandas as pd
from collections import defaultdict

with open("./data/claims_saved.yaml") as f:
    claims_raw = yaml.safe_load(f)

with open("./data/req_saved.yaml") as f:
    reqs_raw = yaml.safe_load(f)

claims_df = pd.DataFrame([
    {"uid": uid, **data}
    for uid, data in claims_raw.items()
])

# Build requirement -> [claim_uids] mapping from claims
req_to_claims = defaultdict(list)
for uid, data in claims_raw.items():
    for req_uid in data.get("requirements", []):
        req_to_claims[req_uid].append(uid)

reqs_df = pd.DataFrame([
    {"uid": uid, **data, "claim_uids": req_to_claims.get(uid, [])}
    for uid, data in reqs_raw.items()
])

# Drop requirements list from claims since it's now on requirements
claims_df = claims_df.drop(columns=["requirements"])

print(claims_df)
print()
print(reqs_df[["uid", "claim_uids"]])

# Rewrite requirements.yaml with claim_uids added
updated_reqs = {}
for uid, data in reqs_raw.items():
    updated_reqs[uid] = {**data, "claim_uids": req_to_claims.get(uid, [])}

with open("./data/requirements.yaml", "w") as f:
    yaml.dump(updated_reqs, f, default_flow_style=False, sort_keys=False, allow_unicode=True, width=10000)

# Rewrite claims.yaml with requirements field removed
updated_claims = {}
for uid, data in claims_raw.items():
    updated_claims[uid] = {k: v for k, v in data.items() if k != "requirements"}

with open("./data/claims.yaml", "w") as f:
    yaml.dump(updated_claims, f, default_flow_style=False, sort_keys=False, allow_unicode=True, width=10000)
