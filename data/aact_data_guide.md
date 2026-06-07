# AACT Table Guide

## Design Groups vs Result Groups
When a study is registered in ClinicalTrials.gov, information is entered about how the study defines participant groups. In AACT, this information is stored in the Design_Groups table stores how the study defines participant groups when reporting the design of the trial. Result_Groups table contains the actual info that is reported after the study has completed. ***AACT has not attempted to link data between these 2 tables.***

## result_rroups Table
All result tables (Outcomes, Outcome_Counts, Baseline_Measures, Reported_Events, etc.) relate to Result_Groups via the foreign key result_group_id.

For example, Outcomes.result_group_id = Result_Groups.id.


## the problem
design groups spcify the experimental arm, vs control vs other arms, but the results section reports things in groups, but it does not necessarily use the same groups/arms and it doesn't specify which ones are the experimental/control/etc arms. for now, I think I should just pick one... Overall, results are not commonly too commonly reported to ctgov it appears. I think something like 13%

I want to try joining by group title, across design group, and result_groups