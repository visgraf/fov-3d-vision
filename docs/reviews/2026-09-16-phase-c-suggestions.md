> Third-party review received 2026-09-16 at the start of Phase C ("Suggestions for Phase C"),
> reproduced verbatim below the reading. The reviewer had read the repository at `2c08064`.

## Reading (Chat, 2026-09-16)

Taken: the three Phase C candidates are layers of one experiment (estimator, policy, judge);
the belief in inverse depth with the Fisher information transformed by the exact Jacobian;
the expected-information policy as one candidate; the separation of *where to look* (ω) from
*at what depth to verge* (ẑ), which `fixation_pairs.py` conflates by taking a world point; the
budget as rays with matcher and policy time reported beside it; the baselines, including an
oracle from `truth.npz`; E₂ = 2, e_max = 45 held fixed until the policy exists (D16's overturn
clause). Not taken: the native-lattice matcher as the first step (C1 there) — the loop closes on
the D15 instrument extended over the field (`stereo_field.py`), which is engineering, and the
oracle bracket tells afterwards whether a better estimator is the bottleneck; the plan's
sequence and governance (C0 contract first, six steps) — this project closes phases fast and
carries the measurement discipline in each tool's checks, not in a contract. Two things the
review did not have: the head is fixed and directions are stored in the head frame, so
cross-fixation correspondence is the identity and fusion is inverse-variance averaging per
cell; and the instrument's map was the fovea only (±2°), so the field over the disc, at a
per-level cell size, was the real gap. Decisions taken on it: D17.

## The review, verbatim

I would slightly reframe the choice. I do **not** think the three Phase C candidates are really alternatives. They are three layers of the same experiment:

| Candidate                   | Role I would give it in Phase C                              |
| --------------------------- | ------------------------------------------------------------ |
| Non-uniform-lattice matcher | **Estimator** — what did the two eyes infer from the samples? |
| Gaze policy                 | **Scientific centerpiece** — where should the eyes look next? |
| Reconstruction vs. budget   | **Evaluation criterion** — did active sensing actually buy more 3-D information per ray? |

So I would name Phase C something like **Active Foveated Stereo under a Sampling Budget**, with the central question:

$\boxed{ \text{Can the system choose its own successive binocular fixations so that} \atop \text{3-D uncertainty decreases faster per ray than with a fixed fixation sequence?} }$

This is also how I would resolve a small tension in the current documentation. The README still lists the non-uniform matcher first among the open candidates, but the Phase B summary is more definite: “Phase C is the gaze policy,” and says Phase B has deliberately handed Phase C a rig, an information-per-ray quantity, a measured cost per pair, and a falsifiable test against fixed target order. ([GitHub](https://github.com/visgraf/fov-3d-vision)) ([GitHub](https://github.com/visgraf/fov-3d-vision/blob/main/docs/phase-b-summary.md))

That direction also fits the conceptual motivation of the project particularly well: the original context says active vision should be treated as a controlled sampling problem and that the target claim is essentially “the same posterior for less computation.” The eye report makes the same point in perceptual terms: peripheral evidence selects a target, the gaze moves, foveal analysis updates the state, and the next observation should be chosen to reduce uncertainty or disambiguate depth.

## 1. The non-uniform matcher is important — but I would make it an enabling component

There is a real scientific hole here. Phase B's `stereo_instrument.py` intentionally avoids it: it first integrates foveal samples onto a uniform $(\theta,\phi)$ grid and then performs ordinary NCC/Lucas–Kanade matching. D15 explicitly says it “never sees the non-uniform lattice.” ([GitHub](https://github.com/visgraf/fov-3d-vision/blob/main/DECISIONS.md))

So the project has not yet demonstrated:

$\text{D1 samples} \quad\longrightarrow\quad \text{stereo inference}$

without first going through

$\text{D1 samples} \rightarrow \text{uniform reconstruction} \rightarrow \text{matcher}.$

That deserves investigation.

But I would **not** make “build the best non-uniform stereo matcher” the whole of Phase C. That could become a research project of indefinite length, and it would postpone the active-vision experiment that Phases A and B were preparing.

There is also a repository-architecture reason. D5 deliberately says that `fov-3d-vision` produces samples while the research matcher belongs on the `active-stereo` side, unless that decision is explicitly overturned. ([GitHub](https://github.com/visgraf/fov-3d-vision/blob/main/DECISIONS.md)) And `active-stereo` already has exactly the right conceptual slots: L3 is disparity inference, L5 is vergence control, and L6 is the next-fixation policy. Its estimators are also explicitly designed to carry uncertainty as `Estimate(value, variance)`. ([GitHub](https://github.com/visgraf/active-stereo))

### What I would build

Not merely a matcher returning

$\hat\delta.$

I would make the native matcher return a **local disparity posterior**

$p(\delta\mid{\cal S}_L,{\cal S}_R),$

or at least

$(\hat\delta,\sigma_\delta^2).$

That uncertainty is what Phase C actually needs.

The matching should operate directly on

$(\mathbf d_i,v_i,A_i),$

where $\mathbf d_i$ is direction, $v_i$ is measured radiance/value, and $A_i$ is footprint.

After conversion to Phase B's epipolar coordinates, a candidate disparity simply changes

$(\theta,\phi) \rightarrow (\theta+\delta,\phi).$

Instead of interpolating both eyes to a rectangular lattice, one could evaluate a footprint-weighted matching likelihood directly from neighboring irregular samples. Conceptually,

$C(\delta) = \sum_{ij} w_{ij}(\delta) \, \|v_i^L-v_j^R\|^2,$

where $w_{ij}$ depends on angular proximity and overlap of the two samples' footprints.

Then

$p(\delta)\propto \exp\!\left[-\frac{C(\delta)}{2\sigma^2}\right].$

The important output is the **shape** of this function, not just its argmin.

That would turn the non-uniform matcher into exactly what the gaze policy needs: a measurement model.

------

# 2. I would make the gaze policy the actual Phase C contribution

This is where the previous two phases become one system.

Phase A established:

$\text{where the samples are} + \text{what they cost}.$

Phase B established:

$\text{what binocular information those samples contain}.$

Phase C can now close the loop:

$\boxed{ \text{observe} \rightarrow \text{infer depth + uncertainty} \rightarrow \text{choose next fixation} \rightarrow \text{observe again} }$

This also matches the architecture already defined in `active-stereo`, where the outer loop is explicitly what turns perception into active inference: L6 selects the next fixation, changing vergence/geometry and therefore the next sensory evidence. ([GitHub](https://github.com/visgraf/active-stereo/blob/main/docs/architecture.md))

## The state should be a belief, not just a depth map

I would maintain something like

${\cal B}_t(\omega) = p(\rho(\omega)\mid D_{1:t}),$

where

$\rho=\frac{1}{z}$

is inverse range and $\omega$ is spherical direction.

I prefer inverse depth here because disparity is much closer to linear in inverse depth than in metric range. Phase B already gives you exact spherical triangulation, so the transformation need not use a pinhole approximation.

A cell might therefore carry

$(\hat\rho,\sigma_\rho^2,\text{validity},\text{visibility},N_{\rm obs}).$

This makes “what have I learned so far?” explicit.

------

# 3. I would change Phase B's information criterion slightly for the policy

Phase B measures Fisher information in **disparity**:

$I_\delta.$

That was exactly right for deciding whether $E_2$ helped stereo matching.

But Phase C is ultimately about recovering **3-D structure**.

The policy should therefore care about information in depth—or preferably inverse depth—not disparity itself.

From the exact stereo geometry,

$\delta=f(\rho),$

so Fisher information transforms approximately as

$\boxed{ I_\rho = I_\delta \left( \frac{\partial\delta}{\partial\rho} \right)^2 . }$

`rig.py` already gives you the geometry needed to obtain this Jacobian, analytically or numerically.

That matters because two scene locations with identical disparity precision need not have identical metric depth precision.

So I would make the Phase-C quantity something like

$\frac{\text{expected reduction in 3-D uncertainty}} {\text{rays}}.$

That is closer to the original “same posterior for less computation” formulation than simply maximizing texture gradients.

------

# 4. A very natural first gaze policy falls out of that formulation

Suppose the current inverse-depth variance at spherical cell $q$ is

$\sigma_{\rho,q}^2.$

A candidate fixation $a$ is predicted to supply information $I_{\rho,q}(a)$.

For a Gaussian approximation, the expected entropy reduction has the form

$\Delta H_q(a) \approx \frac12 \log \left[ 1+\sigma_{\rho,q}^2 I_{\rho,q}(a) \right].$

Then choose

$\boxed{ a^* = \arg\max_a \frac{ \displaystyle\sum_q w_q\Delta H_q(a) + \lambda\,\Delta\Omega_{\rm new}(a) }{ N_{\rm rays}(a) } }$

where

- $w_q$ is an optional task importance;
- $\Delta\Omega_{\rm new}$ rewards previously uncovered regions;
- $N_{\rm rays}(a)$ is the known cost of that foveated pair.

This gives you **exploration and exploitation without RL**.

A location that is uncertain but promising attracts a fixation. Once it has been measured well, its variance falls and the expected information gain from revisiting it falls automatically.

That is a very clean computational analogue of

$\text{peripheral evidence} \rightarrow \text{target selection} \rightarrow \text{saccade} \rightarrow \text{foveal analysis}.$

I would avoid learned gaze policies at first. A one-step greedy information policy is interpretable, measurable, and gives a baseline that any learned policy would later have to beat.

------

# 5. There is an important Phase-C issue hidden in `fixation_pairs.py`

Currently a fixation pair is specified using a **known world-space point**

$P.$

That is completely appropriate for Phases A and B because you are validating geometry.

But an active observer does not know $P$ beforehand.

Phase C therefore needs to distinguish:

$\text{where to look}$

from

$\text{at what depth to verge}.$

A useful decomposition is

$\boxed{ \text{gaze direction }\omega + \text{estimated fixation depth }\hat z. }$

The gaze policy chooses $\omega$. The current stereo belief supplies $\hat z$, and the vergence controller turns those into the two eye orientations.

Interestingly, this separation is already present in `active-stereo`: L5 is control/vergence and L6 is “where next.” ([GitHub](https://github.com/visgraf/active-stereo/blob/main/docs/architecture.md))

If the chosen region has no reliable depth estimate, the controller can keep the previous vergence, use a prior distance, or eventually perform a small vergence search. I would treat that as a later experiment rather than putting it into the first Phase-C test.

------

# 6. “Reconstruction quality versus budget” should be the judge, not the Phase-C topic

This third candidate is essential, but I would not make it the research question.

Phase A already established the pattern:

$\text{quality}(B)$

versus a declared ray budget $B$.

Phase C should extend exactly that methodology from **radiance reconstruction** to **3-D reconstruction**.

After every accumulated fixation pair, record something like

$B_t=\sum_{k=1}^{t}N_{\rm rays}(a_k)$

and measure

$E_\rho(B_t), \qquad \mathrm{coverage}(B_t), \qquad \mathrm{calibration}(B_t).$

I would use inverse-depth error or the existing depth-quantum formulation as the main geometric measure, accompanied by solid-angle coverage. Posterior calibration is especially important: if the system says $\sigma_z=2\,\mathrm{cm}$, the observed errors should behave accordingly.

A point-cloud or surface metric such as completeness/accuracy could be added later, but I would not let Chamfer distance become the primary metric prematurely. The native object here is still a spherical binocular depth belief.

And I would retain **ray count as the primary sensor budget**, because that maintains comparability with Phases A and B. Matcher/policy wall time should be reported separately rather than silently folded into the ray count. Otherwise an extremely expensive matcher could appear to achieve “less computation” simply because it used fewer rendered rays.

------

# 7. The baselines make the experiment quite strong

I would compare the adaptive policy against the already available fixed target order, a random order, and a simple coverage-greedy policy that always looks toward the least-covered region. Then add an **oracle policy** allowed to use `truth.npz` only to estimate the best possible next fixation.

That gives an informative bracket:

$\text{random/fixed} < \text{sample-driven active policy} < \text{oracle}$

if things work.

The oracle is particularly useful. Suppose the active policy performs poorly. If the oracle also performs poorly, the problem is probably the sensor/foveation geometry. If the oracle is excellent but the real policy is poor, the bottleneck is the matcher, uncertainty estimate, or selection criterion.

That decomposition is much more informative than one final reconstruction error.

------

# 8. I would implement Phase C in this order

| Step                                      | Purpose                                                      |
| ----------------------------------------- | ------------------------------------------------------------ |
| **C0 — Evaluation contract**              | Freeze the budget and 3-D error/coverage metrics *before* building the policy |
| **C1 — Native-lattice stereo likelihood** | Direct D1-v2 samples → disparity estimate + uncertainty      |
| **C2 — Cross-fixation belief fusion**     | Accumulate disparity/inverse-depth evidence from successive pairs |
| **C3 — Expected-information gaze policy** | Select the next angular fixation from the current belief     |
| **C4 — Active reconstruction vs. budget** | Fixed/random/coverage-greedy/active/oracle curves            |
| **C5 — Adaptive sensor profile**          | Only then allow $E_2$, $e_{\max}$, etc. to become policy variables |

This ordering means the matcher is indeed the **first new technical component**, which agrees with the current README ordering, but the **scientific purpose of Phase C remains the gaze policy**.

That distinction resolves the apparent conflict in the documentation rather neatly.

------

# 9. I would initially keep $E_2=2^\circ,e_{\max}=45^\circ$ fixed

This is important experimentally.

Phase B has just closed D16 using those values, and its explicit overturn condition says Phase C may reopen the question once a policy prices coverage into the objective. ([GitHub](https://github.com/visgraf/fov-3d-vision/blob/main/DECISIONS.md))

If Phase C simultaneously changes:

$\text{gaze location},\quad E_2,\quad e_{\max},\quad \text{vergence policy}$

you won't know what caused an improvement.

So first hold the sensor fixed and solve

$\text{where next?}$

Then there is a particularly interesting second experiment:

> Under the same cumulative ray budget, is it better to make fewer wide $45^\circ$ fixations, or more cheaper/narrower $30^\circ$ fixations?

Phase B already hints that this could be nontrivial: $e_{\max}=30^\circ$ used fewer rays and had greater disparity information per ray than $45^\circ$, while $45^\circ$ had better single-pair disparity error and wider instantaneous coverage. ([GitHub](https://github.com/visgraf/fov-3d-vision/blob/main/docs/phase-b-summary.md))

That trade-off only really becomes meaningful once **number and placement of fixations are controlled by a policy**.

Eventually the action could become

$a_t= (\omega_t,E_{2,t},e_{\max,t}),$

which would turn Phase C from active gaze into genuinely **active sensing**.

But I would make that C5 rather than C1.

------

## My resulting Phase C

I would therefore change the README's single sentence from “three candidates, not yet chosen” to something conceptually closer to:

> **Phase C — active binocular sampling.**
> Develop a native-lattice stereo estimator that preserves uncertainty, accumulate its evidence across fixations, and use the resulting 3-D belief to select the next fixation by expected information gain per ray. Evaluate the closed loop by reconstruction quality and coverage versus cumulative ray budget, against fixed, random, coverage-based, and oracle policies.

That produces a very natural progression:

$\boxed{ \begin{array}{ccc} \text{Phase A} &:& \text{How should an eye sample?}\\[2mm] \downarrow &&\\[-2mm] \text{Phase B} &:& \text{What depth information do two such eyes obtain?}\\[2mm] \downarrow &&\\[-2mm] \text{Phase C} &:& \textbf{Given what they currently know, where should the eyes look next?} \end{array}}$

To me, that third question is the one that makes the project fully **active vision**, rather than merely an unusual stereo camera.