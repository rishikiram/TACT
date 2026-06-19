##
Into dev, I want to ingest a bunch of related data. 

The data would be start with a medical asset that will define 
a set of patients, diseases, and competitive treatments. 

Our goal is to extract, normalize and structure data of the arms of published studies.
Dev should accept
- list of arms
- associated populations to each arm -- *would we expect seperate studies' arms to share populations?*
- catagorize arms [anchor_comparator / placebo / active_comparator_candidate / historical_context / investigational_benchmark / not_relevant / needs_review]
- *what is an anchor_comparator in this context?*
- associated studies for *?(later development and competitive analysis")* 
- how are inclusion/exclsion criteria determined for clinincal trials, what information is helpful for that?
