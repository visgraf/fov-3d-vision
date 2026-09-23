# FullScene-REAL-1S — one-round visible-seed recovery

Question: when a benchmark object's oracle centre direction is occluded, can one bounded prediction-side survey on the established 5-degree lattice recover a usable seed without evaluator geometry?

This experiment consumes the completed REAL-1 baseline only. It dynamically selects baseline rows with `NOT_VISIBLE_OR_NO_TARGET_SUPPORT`. For each such row it renders exactly the eight neighbors of the failed centre on a 5-degree Moore ring. All eight are rendered before selection. The winner is chosen by target valid-depth count, then target-visible pixels, then fixed ring order. If observer-side valid target depth exists, the same winning observation is reused with the established selected-object seed extraction/purity semantics.

There is no second ring, radius expansion, extra seed render, growth, audit, handoff, revisit, scheduler, or truth access. A failure after the ring is a valid experimental outcome.

The experiment does not test discovery: object identity and the original centre direction remain the same explicit REAL-1 oracle scaffold.
