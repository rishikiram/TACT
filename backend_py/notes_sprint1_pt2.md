Trial export
- [ ] stable record UID
- [X] NCT ID
- [X] title
- [X] sponsor
- [X] phase and status
- [X] study design and randomization
- [👎] population - no explicit data
- [👎] histology - TODO -> use trial condition
- [👎] line of therapy - TODO -> unclear 
- [👎] biomarker - TODO -> read eligibility?
- [X] interventions
- [ ] anchor-comparator match - TODO
- [X] primary and secondary endpoints
- [X] results availability
- [X] source URL and source update date
- [X] query UID
- [ ] import-run UID - TODO
# ---
Arm Export
- [ ] stable arm UID - TODO
- [~] linked study UID and NCT ID
- [X] arm title and type 
- [X] regimen
- [ ] provisional role - TODO role for us or for the study?
- [ ] population summary - TODO
- [ ] endpoint summary - TODO
- [X] source field and source text 
- [ ] extraction method
- [ ] confidence
- [ ] review status.
# ---
Arm Catagories
- [ ] anchor_comparator
- [ ] active_comparator_candidate
- [ ] historical_context
- [ ] investigational_benchmark
- [ ] placebo
- [ ] not_relevant
- [ ] needs_review
# ---
Shortlist
- [ ] provisional classification
- [ ] inclusion rationale
- [ ] principal caveat
- [ ] candidate status
- [ ] expert-review status.
# ---
Shortlist Facts??
- [ ] population
- [ ] histology
- [ ] line of therapy
- [ ] biomarker strategy
- [ ] background therapy
- [ ] combination strategy
- [ ] comparator
- [ ] primary endpoint
- [ ] PFS endpoint
- [ ] OS endpoint
- [ ] QoL/PRO endpoint
- [ ] sample size
- [ ] randomization
- [ ] phase
- [ ] results availability and maturity
- [ ] trial status
# ---
Dev import contract
- [ ] field name
- [ ] data type
- [ ] whether it is required
- [ ] allowed values
- [ ] example
- [ ] source
- [ ] transformation
- [ ] validation rule
- [ ] proposed target DEV object, where known