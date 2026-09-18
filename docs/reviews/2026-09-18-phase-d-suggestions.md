> Third-party review received 2026-09-18 of Phase C and of the Phase D plan as first written,
> reproduced verbatim below the reading.

## Reading (Chat, 2026-09-18)

Taken, into the revised `docs/phase-d-plan.md`: the diagnosis before the matcher change (as
D1's first hour, not a step — the records and truth exist, no rendering; with the truth
sidecar's occlusion flag it separates the unfixable from the window's from the search's); the
safety valve in coarse-to-fine (parent as proposal, full search on a boundary hit, a weak
peak or an LR failure); P(child gross | parent gross) beside the per-level gross; the window
as D2 in two forms only (3 × 3 at the fine levels, photometrically weighted 5 × 5) ahead of
the outlier term, because the observation should be fixed before its failure is modelled;
the inlier probability π as D3, still conditional, and the coverage-vs-information re-run
after it; checkpoints read off one long run. Not taken: the five-step framing (D0 folds into
D1; the plan stays three conditional steps and the long run), the probability table, and a
rule for the saved-pairs → field → loop order, which is how every step here has run. The
prediction the review invites is written into the plan: the window's errors at the fine
levels, the search's at the coarse ones.

## The review, verbatim

If you had to make a plan for Phase D, what would it be?
How do you see the challenges, achievements and chances of success?

----

Yes. I would make Phase D a **depth-estimator reliability phase**, not another expansion of the active-vision architecture.

That is also close to the direction already written into the repository. Phase D is currently open but, as of today, its planned experiments have not yet been run. The repo proposes coarse-to-fine stereo first, a gross-error term in fusion only if needed, and finally a long run toward saturation.

I would keep that overall direction, but sharpen it into a five-step program.

# 1. What I think Phase D should answer

Phase C established that the loop works. I would not make Phase D ask again whether active foveated stereo works.

Instead:

$\boxed{ \text{Can the existing foveated stereo sensor produce a reliable multiscale depth belief?} }$

More specifically:

$\boxed{ \text{coarse peripheral estimate} \rightarrow \text{better fine search} \rightarrow \text{fewer gross matches} \rightarrow \text{better belief} \rightarrow \text{better active reconstruction} }$

The current problem is very clear. On the Classroom at `full`, about one third of measured cells have gross errors greater than 25%; at `small` it is roughly half. These errors are concentrated around depth discontinuities, while the fine-band estimates themselves are much better.

That is almost an ideal starting point for a new phase: there is a specific failure, a measurable number, and plausible mechanisms.

------

# 2. My Phase D plan

I would divide it into **D0–D4**:

| Step   | Question                                               | Main deliverable            |
| ------ | ------------------------------------------------------ | --------------------------- |
| **D0** | Why are the gross errors occurring?                    | error taxonomy / diagnostic |
| **D1** | Does coarse-to-fine correspondence fix them?           | hierarchical stereo field   |
| **D2** | If not, can edge-aware matching fix the remainder?     | robust matcher              |
| **D3** | Can the belief explicitly represent residual outliers? | robust probabilistic fusion |
| **D4** | What happens as the gaze budget approaches saturation? | 50→500 fixation curves      |

The important difference from the current plan is **D0** and an explicit branch between matching errors and fusion errors.

------

## D0 — Diagnose the gross errors before changing the matcher

I would spend a surprisingly serious amount of effort here, perhaps only half a day in coding but enough analysis to know what D1 is actually supposed to repair.

You already have ground truth for the saved Phase-C records. Therefore no rendering is necessary.

For every gross cell, record:

$(\text{level}, e, \text{true depth}, \text{estimated depth}, \text{LR residual}, \text{NCC peaks}, \text{gradient}, \text{parent estimate}, \text{distance to depth edge}).$

The crucial distinction is between two hypotheses.

### Hypothesis A — search ambiguity

The correct NCC peak exists, but the wide ±3–6° independent search finds another plausible peak.

Then coarse-to-fine should work extremely well.

### Hypothesis B — support-window contamination

The current $5\times5$ window straddles foreground and background, so there is **no single correct disparity represented by the window**.

Then narrowing the search may do little—or even make things worse.

The repository itself already suspects both phenomena: the Phase-D document describes a $5\times5$ window crossing two surfaces, while D20 proposes coarse-to-fine as the first test.

This distinction matters enormously.

I would produce one diagnostic figure:

$\boxed{ P(\mathrm{gross}) \quad\text{vs.}\quad \text{distance from true depth discontinuity} }$

separated by level.

If gross error shoots up within one correlation-window radius of a depth edge, we already know where Phase D needs to concentrate.

------

# 3. D1 — Coarse-to-fine stereo, but with a safety valve

I agree strongly with the current proposal to match

$L_4\rightarrow L_3\rightarrow L_2\rightarrow L_1\rightarrow L_0.$

Currently each level independently searches a comparatively wide disparity interval. The proposed D1 instead upsamples the parent-level parallax and searches roughly ±2 cells around it.

Conceptually,

$\hat p_{\ell}^{\,0} = U(\hat p_{\ell+1})$

and

$p_\ell\in [ \hat p_{\ell}^{\,0}-2c_\ell,\, \hat p_{\ell}^{\,0}+2c_\ell ].$

I would make one modification to the current plan:

**do not trust the parent unconditionally.**

Use three modes.

A trustworthy LR-consistent parent gets the narrow search. An ambiguous parent gets an intermediate search. A missing or dubious parent keeps the original full search.

And there should be an escape clause: if the best NCC result lies against the boundary of the narrow interval, has a weak peak ratio, or fails LR consistency, retry the full search.

That prevents classic coarse-to-fine error propagation.

This is especially important near depth boundaries, because the coarse cell may describe the background while the finer child lies on the foreground.

So coarse-to-fine should be treated as a **proposal mechanism**, not as a hard prior.

------

# 4. What I would measure in D1

The current decision rule is good: on the Classroom `full` coverage run, coarse-to-fine counts as a win if gross fraction falls by roughly one third or median inverse-depth error improves by more than the approximately 10% run-to-run spread. The baseline is currently gross $=0.344$ and median error $=0.0427\,\mathrm{m}^{-1}$.

I would retain those, but add two diagnostics:

$G_\ell = P\left( \frac{|\hat\rho-\rho^*|}{\rho^*}>0.25 \right)$

for every level, and

$P(\text{child gross}\mid\text{parent gross}).$

That second number is particularly informative.

If coarse-to-fine works, we should see

$P(\text{child gross}\mid\text{parent good}) \ll P(\text{gross today}).$

If instead bad parent matches simply cascade downward, the failure mechanism will be immediately visible.

I would also track runtime. The proposed narrower search should reduce NCC work, so success should ideally mean **more accurate and faster**, not more accurate and slower. The existing plan predicts inference time should decrease.

------

# 5. D2 — If the problem is really the window, fix the window

This is where I would differ most from simply following the current D1→D2 plan mechanically.

Suppose coarse-to-fine reduces

$G:0.344\rightarrow0.28$

but most residual failures remain exactly on object silhouettes.

I would **not** immediately make the belief model more sophisticated.

The observation itself is still wrong.

I would first try an edge-aware matcher.

The simplest experiment would compare the existing $5\times5$ window against a $3\times3$ window. Smaller support should reduce foreground/background mixing but increase noise.

A better version is an adaptive support window:

$w_{ij} = w_s(i,j)\, w_I(I_{ij}-I_0),$

so samples that are spatially distant or photometrically unlike the centre contribute less to NCC.

Then the effective window follows image structure rather than blindly crossing an edge.

I would test only two or three variants:

$5\times5, \qquad 3\times3, \qquad \text{edge-weighted }5\times5.$

Nothing more complicated yet.

The question is simply:

> Is the remaining error caused by correspondence search, or by the assumption that every fixed window represents one surface?

That is an interesting research result in its own right.

------

# 6. D3 — Only then add an explicit outlier probability

The current Phase-D plan proposes doing this if gross errors remain above 20%, which I think is a sensible threshold.

Phase C already discovered that one Gaussian variance is not sufficient. It now correctly distinguishes reducible measurement noise from a non-reducible model floor.

Phase D could add a third concept:

$\boxed{ \text{probability that the correspondence is simply wrong} }$

so a measurement becomes

$(\hat\rho,\sigma_{\rm noise},\sigma_{\rm floor},\pi_{\rm inlier}).$

Conceptually, the likelihood becomes

$p(z\mid\rho) = \pi\, \mathcal N(z;\rho,\sigma^2) + (1-\pi)\, p_{\rm outlier}(z).$

I would estimate $\pi$ initially from quantities you already have:

$\pi = f( \text{LR residual}, \text{NCC peak ratio}, \text{parent-child agreement} ).$

No neural network.

No learned stereo.

Just calibrate those observable confidence cues against the existing truth.

That would give the active loop something Phase C lacked: not only

> "this measurement has large variance"

but

> "there is a 30% probability this correspondence belongs to the wrong mode entirely."

That is much closer to what actually happens at a depth discontinuity.

------

# 7. This would also rehabilitate the information policy

Phase C's information policy is currently handicapped because it assumes that the uncertainty model describes the important errors.

But it does not: the repo explicitly notes that gross errors are outside the model, which is one reason coverage-first remains the default.

Once an inlier probability exists, the expected gain can become something like

$E[\Delta H] \approx \pi_{\rm inlier}\, \Delta H_{\rm good}.$

Then I would rerun only:

$\text{coverage} \quad\text{vs.}\quad \text{information}.$

Not five policies again.

And I would regard either outcome as useful.

If information now wins materially, Phase C's failure was primarily a bad uncertainty model.

If it still does not, then the stronger conclusion is:

> even with a much better uncertainty model, inhibition of return / coverage remains most of what gaze control buys.

That would actually strengthen the scientific result of the project.

------

# 8. D4 — Run the system to saturation

Only after stabilizing the matcher would I run the proposed 500-fixation experiment.

The repository estimates that roughly 500 fixations would cover the 60° cap at foveal quality, costing about 13 minutes and 13 G rays at `full`—still about 16× fewer rays than the full reference panorama. That is currently a prediction, not yet a measurement.

I would save checkpoints from **one run** at

$K=10,\;25,\;50,\;100,\;200,\;300,\;500.$

Then plot versus cumulative rays:

$\text{any coverage}, \quad \text{fine coverage}, \quad \operatorname{median}|\Delta\rho|, \quad P_{90}(|\Delta\rho|), \quad G, \quad \text{vergence error}.$

This experiment is more important than it may appear.

There are two very different possible curves.

If

$\text{error}\rightarrow 0.015\!-\!0.019\ {\rm m}^{-1},$

the current fine-band level reported by Phase C, then the story is very clean:

> coarse peripheral depth guides the observer until foveation progressively replaces it with accurate measurements.

Phase C's current fine-band error is indeed about $0.015\!-\!0.019\ {\rm m}^{-1}$ on the Classroom at `full`.

But if the curve saturates much earlier, say near $0.030$, then simply putting the fovea everywhere is insufficient. There is still a structural stereo-estimation floor.

Both outcomes would be scientifically interesting.

------

# 9. The hardest technical challenge

I think the largest risk is **not implementing coarse-to-fine stereo**. That part is straightforward.

The difficult issue is that depth discontinuities violate the model of the block matcher.

Imagine:

```text
          foreground
             │
             │
─────────────┼──────────── depth edge
             │ background
```

A $5\times5$ support region centred close to that edge contains two disparities.

There is no unique "correct disparity of the window."

Now make the window coarser.

The problem becomes worse.

So there is a dangerous possibility:

$\boxed{ \text{coarse-to-fine can propagate the coarse edge error rather than cure it.} }$

That is why I would add D0 and the narrow-search fallback.

If that failure occurs, it is not bad news for the project. It identifies precisely what the next scientific step is: **support adaptation**, rather than a deeper disparity pyramid.

------

# 10. The second challenge: noise versus spatial support

The Classroom is substantially noisier than the calibration room at the rendering settings used in Phase C. At `small`, it is effectively at the sensor's texture/noise limit; the repo reports relative noise around 0.18 and gross matches around one half. `full` improves that situation substantially.

This creates a fundamental tradeoff:

$\text{larger window} \Rightarrow \text{better statistical matching}$

but

$\text{larger window} \Rightarrow \text{more likely to cross a depth discontinuity}.$

That is exactly the kind of tradeoff that makes an adaptive support mechanism potentially more interesting than simply selecting one new window size.

------

# 11. The third challenge: feedback

The matcher does not live in isolation.

A wrong peripheral estimate causes

$\text{wrong depth} \rightarrow \text{wrong vergence} \rightarrow \text{different stereo pair} \rightarrow \text{different subsequent estimate}.$

Phase C already demonstrated that the periphery is good enough to place vergence within roughly $0.4$ m at the median on the Classroom.

Improving the field could therefore have a nonlinear benefit: better coarse correspondence gives better vergence, which makes the next foveal match easier.

But the reverse is possible too.

For that reason I would always proceed in this order:

$\boxed{ \text{saved-pair test} \rightarrow \text{offline field test} \rightarrow \text{closed-loop test}. }$

Never debug the matcher and the active loop simultaneously.

------

# 12. What I would count as Phase-D achievements

A **minimum successful Phase D** would give us:

$G_{\rm full} : 0.34 \rightarrow \lesssim0.23$

without worsening fine depth estimates or coverage.

That corresponds roughly to the current plan's "reduce gross by one third" criterion.

A **strong Phase D** would achieve approximately

$G_{\rm full}<0.20$

and

$\operatorname{median}|\Delta\rho| \approx0.035\ {\rm m}^{-1}$

or better at 50 fixations, while reducing or maintaining inference time. The $0.035$ target is also close to the current repository's prediction for coarse-to-fine.

A **very strong Phase D** would additionally show the long-run curve approaching the current fine-band error as foveal coverage approaches saturation.

That would establish a beautiful hierarchy:

$\boxed{ \begin{array}{rcl} \text{periphery} &\Rightarrow& \text{coarse range}\\ &\Rightarrow& \text{vergence}\\ &\Rightarrow& \text{coarse-to-fine correspondence}\\ &\Rightarrow& \text{foveal depth}\\ &\Rightarrow& \text{progressively accurate 3-D belief}. \end{array}}$

That is considerably stronger than simply saying "we have a stereo matcher."

------

# 13. My estimate of the chances

I would separate several notions of success.

| Outcome                                                      | My estimate |
| ------------------------------------------------------------ | ----------- |
| Coarse-to-fine implementation works technically              | **~95%**    |
| It makes matching faster                                     | **~85–90%** |
| It produces a measurable reduction in gross errors           | **~75%**    |
| It achieves the planned ~⅓ reduction in gross errors by itself | **~60–70%** |
| Coarse-to-fine + edge-aware support gets gross below ~20%    | **~75–85%** |
| Robust confidence/fusion improves the belief materially      | **~75%**    |
| 500-fixation run yields a clean saturation curve             | **>90%**    |
| Long-run error approaches the present fine-band floor        | **~60–70%** |
| A repaired information policy clearly beats coverage-first   | **~25–35%** |

The last number is deliberately low.

I do **not** think Phase D should be judged by whether expected-information finally beats coverage.

Phase C may have uncovered a deeper fact: once revisiting is suppressed, geometric coverage may simply be a very strong policy for this sensing problem.

Even a perfect uncertainty model cannot create much policy advantage if most useful actions are approximately equivalent.

------

# 14. Overall chance that Phase D succeeds

If "success" means:

> identify the origin of gross errors, substantially reduce them, preserve the active loop, and establish the error-versus-budget saturation behavior,

I would put the overall probability around

$\boxed{80\%}$

because the project is now in a favorable situation: the sensor works, geometry works, truth exists, the loop works, the problematic cells are identifiable, the experiment is fast, and there is already a plausible engineering remedy.

The main uncertainty is **which remedy** wins—search restriction, adaptive support, or robust probabilistic fusion—not whether the failure can be studied.

That is a very different situation from Phase C, where the whole active loop still had to be shown to work.

------

# 15. What I would deliberately *not* put into Phase D

I agree strongly with the repository's current exclusion of head motion, lookahead policies, and changing $E_2/e_{\max}$ as actions.

I would also avoid a learned stereo matcher.

Those are good later research questions, but right now they would obscure a rare opportunity: **the current failure mode is simple enough to understand mechanistically**.

I would want Phase D to close with an answer like:

> Independent multiscale matching caused X% gross correspondence error. Coarse-to-fine prediction removed Y%; adaptive support removed another Z%; the remaining failure probability is explicitly represented in the belief. As fixation budget increases, coarse peripheral estimates are progressively replaced by foveal ones and reconstruction approaches a measured asymptote.

If Phase D can say that, I think it becomes one of the strongest phases of the project—not because it introduces a flashy new component, but because it turns the Phase-C prototype into a **credible multiscale 3-D perception mechanism**.

---

