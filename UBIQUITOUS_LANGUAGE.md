# Ubiquitous Language

## Building and plant

| Term | Definition | Aliases to avoid |
| --- | --- | --- |
| **Plant** | The simulated physical building whose room temperatures evolve under heat inputs and weather disturbances. | Building, simulator, environment |
| **BRCM Plant** | The first-principles building resistance-capacitance model used as the ground-truth plant in closed-loop simulations. | BRCM building, BRCM simulator, MATLAB plant |
| **Room** | One of the five controlled thermal zones with measured temperature and radiator heat input. | Zone, actuator index |
| **Room Temperature** | The measured output temperature of each controlled room in degrees Celsius. | Output, y, state |
| **Radiator Heat Input** | The controllable heating power applied to each room. | Control input, action, u, radiator input |
| **Ambient Temperature** | The outside air temperature disturbance used by the plant and forecasts. | Tamb, outside temperature |
| **Solar Radiation** | The solar heat disturbance used by the plant and forecasts. | SolRad, solar rad |
| **Ground Temperature** | A fixed plant disturbance representing heat exchange with the ground. | T_ground, ground disturbance |

## Models and signals

| Term | Definition | Aliases to avoid |
| --- | --- | --- |
| **State-Space Model** | A linear dynamical model with A, B, C, and D matrices used by MPC and observers. | LTI model, system, learned model |
| **Learned Model** | A trained state-space model loaded from a Hydra/WandB run for controller design. | Case 3 model, checkpoint model |
| **N4SID Model** | A system-identification model loaded from MATLAB matrices and used as an MPC model alternative. | MATLAB model, identified model |
| **State** | The model-internal thermal state vector used by observers and MPC. | Room temperature, output |
| **Output** | The measured room-temperature vector exposed by the plant. | State, measurement, y |
| **Disturbance** | An exogenous input that affects temperatures but is not controlled, usually ambient temperature and solar radiation. | Weather, d, input disturbance |
| **Disturbance Forecast** | A horizon-length sequence of future disturbances supplied to MPC. | Forecast, weather forecast, d_forecast |
| **Reference** | A target room-temperature vector used by the rule-based controller. | Setpoint, target |
| **Temperature Bounds** | Time-varying lower and upper room-temperature constraints used by MPC. | Comfort bounds, constraints, Tmin/Tmax |
| **Safety Margin** | A buffer that tightens temperature bounds before MPC optimization. | Tmargin, margin, buffer |
| **Scaler** | A transformation between physical units and normalized model space. | Normalizer, base scaler |

## Control policies

| Term | Definition | Aliases to avoid |
| --- | --- | --- |
| **Controller** | A policy that maps current information to a radiator heat input. | Agent, policy |
| **RBC** | A rule-based hysteresis controller that switches heat between minimum and maximum values around a reference. | Reference controller, baseline, rule controller |
| **Economic MPC** | A model predictive controller that minimizes energy, comfort violation, and input movement over a prediction horizon. | MPC, EMPC, optimizer |
| **Control Action** | The first radiator heat-input vector applied to the plant at the current step. | Action, input, u |
| **Action Trajectory** | The full horizon of optimized future heat inputs computed by MPC. | Control trajectory, u trajectory |
| **Prediction Horizon** | The number of future controller steps optimized by MPC. | Horizon, lookahead |
| **Deadband** | The RBC hysteresis width around the temperature reference. | Hysteresis band |
| **Slack Weight** | The MPC penalty weight for violating temperature bounds. | Comfort weight, violation weight |
| **Energy Weight** | The MPC penalty weight for heat input energy use. | R weight, R_weight |
| **Input-Movement Weight** | The MPC penalty on changes between consecutive heat inputs. | lambda_du, smoothness penalty |

## State estimation

| Term | Definition | Aliases to avoid |
| --- | --- | --- |
| **Observer** | A state estimator that reconstructs model state from prior inputs and current room-temperature measurements. | State estimator, Luenberger observer |
| **Filtering Luenberger Observer** | An observer that predicts from the previous input and corrects with the current measurement. | Standard observer |
| **Augmented Observer** | An observer whose state includes persistent disturbance estimates for offset-free MPC. | Augmented Luenberger observer |
| **Output Disturbance** | An additive estimated bias at the model output used to correct plant-model mismatch. | d_hat, disturbance estimate |
| **Input Disturbance** | An estimated disturbance injected through model dynamics. | Ground disturbance, dynamic disturbance |
| **Innovation** | The prior output error used to correct the observer estimate. | Prior error, residual |
| **Prior Estimate** | The predicted state before measurement correction. | Prediction, prior |
| **Posterior Estimate** | The corrected state after measurement correction. | x_hat, corrected estimate |

## Simulation and evaluation

| Term | Definition | Aliases to avoid |
| --- | --- | --- |
| **Simulation** | A closed-loop run of plant, controller, observer, disturbances, and comfort bounds. | Rollout, experiment |
| **Warmup Phase** | The initial simulation phase run with RBC to initialize plant and observer state before evaluation. | Warm-up, burn-in |
| **Evaluation Phase** | The simulation phase used to compute controller performance metrics. | Eval, test phase |
| **Plant Step** | The fast physical integration timestep of the plant, currently 30 seconds. | Fast step, plant dt |
| **Controller Step** | The slower decision timestep of the controller and observer, currently 15 minutes. | Slow step, control dt |
| **Multi-Rate Agent** | The coordinator that updates slow controllers and observers while the plant advances at a faster timestep. | Control agent, agent |
| **Zero-Order Hold** | Reuse of the latest controller action between controller-step boundaries. | ZOH, cached action |
| **Controller Input Data** | The timestamped data frame containing disturbances and comfort bounds for simulation. | Input dataframe, controller inputs |
| **Simulation Result** | The timestamped data frame containing temperatures, heat inputs, observer errors, phases, and controller diagnostics. | Result dataframe, rollout dataframe |

## Optimization and comparison

| Term | Definition | Aliases to avoid |
| --- | --- | --- |
| **Hyperparameter Optimization** | An Optuna search over controller parameters using energy and comfort objectives. | hopt, tuning, sweep |
| **Trial** | One Optuna evaluation of a controller parameter set. | Experiment, run |
| **Study** | A named Optuna collection of trials for one controller and model source. | Tuning run, database |
| **Paired Studies** | Matching MPC and RBC studies associated with the same model run identifier. | Paired databases, matched hopt output |
| **Model Bundle** | A local artifact directory containing a model checkpoint and Hydra config plus provenance metadata. | Run directory, artifact bundle |
| **Model Provider** | A source adapter that supplies a model bundle from local storage or WandB. | Provider, model source |
| **Pareto Front** | The non-dominated trade-off curve between energy consumption and comfort violation. | Pareto plot, frontier |
| **Comfort Cap** | A maximum acceptable comfort violation used to select the lowest-energy feasible trial. | Constraint cap, target max comfort violation |

## Performance metrics

| Term | Definition | Aliases to avoid |
| --- | --- | --- |
| **Energy Consumption** | Total radiator energy consumed over the evaluation phase in watt-hours. | Total energy, energy Wh |
| **Comfort Violation** | Total temperature-bound violation accumulated across rooms and time in kelvin-hours. | Kelvin-hour sum, violation |
| **Peak Power** | Maximum instantaneous total radiator power across all rooms in watts. | Max power |
| **Improvement** | Relative metric reduction of MPC compared with RBC. | Delta, gain |

## Relationships

- A **Simulation** contains exactly one **Plant**, one active **Controller**, one **Observer**, and one **Controller Input Data** stream.
- A **Warmup Phase** uses **RBC** before the **Evaluation Phase** may hotswap to **Economic MPC**.
- An **Economic MPC** uses a **State-Space Model**, **Disturbance Forecast**, **Temperature Bounds**, and optional **Output Disturbance** to compute an **Action Trajectory**.
- Only the first **Control Action** from an **Action Trajectory** is applied to the **Plant**; remaining actions are replanned at the next **Controller Step**.
- A **Multi-Rate Agent** updates the **Plant** every **Plant Step** and updates the **Controller** on **Controller Step** boundaries.
- An **Observer** consumes previous **Radiator Heat Input**, previous **Disturbance**, and current **Room Temperature** to produce a **Posterior Estimate**.
- A **Trial** belongs to one **Study**; **Paired Studies** compare **RBC** and **Economic MPC** on the same model source and data.
- **Pareto Front** points are computed from **Energy Consumption** and **Comfort Violation** metrics over the **Evaluation Phase**.

## Example dialogue

> **Dev:** "When the **Evaluation Phase** starts, do we keep using the **RBC**?"
>
> **Domain expert:** "Only if RBC is the evaluated **Controller**. Otherwise the **Multi-Rate Agent** hotswaps from warmup **RBC** to **Economic MPC** on a **Controller Step** boundary."
>
> **Dev:** "So MPC receives **Room Temperature** directly from the **Plant**?"
>
> **Domain expert:** "No. MPC receives the observer's **Posterior Estimate** and optional **Output Disturbance**; **Room Temperature** is the measured **Output** used to correct the **Observer**."
>
> **Dev:** "And the optimized **Action Trajectory** is all applied to the plant?"
>
> **Domain expert:** "No. Only the first **Control Action** is applied, held by **Zero-Order Hold** between controller updates, then MPC replans over the **Prediction Horizon**."
>
> **Dev:** "When comparing controllers, which numbers define the **Pareto Front**?"
>
> **Domain expert:** "Each **Trial** contributes **Energy Consumption** and **Comfort Violation** from the **Evaluation Phase**; non-dominated trials form the **Pareto Front**."

## Flagged ambiguities

- "input" is overloaded for **Radiator Heat Input**, **Disturbance**, **Controller Input Data**, and model input matrices; prefer the specific term in prose.
- "output" can mean **Room Temperature**, model output vector, or saved output files; use **Room Temperature** for the controlled physical quantity and "artifact" for files.
- "state" is ambiguous between **State** and **Room Temperature** because the BRCM plant returns first states as room temperatures; reserve **State** for model-internal vectors and **Room Temperature** for measured outputs.
- "disturbance" covers weather, ground effects, input disturbances, and output bias; use **Ambient Temperature**, **Solar Radiation**, **Input Disturbance**, or **Output Disturbance** when known.
- Heat units alternate between W/m² at controller/plant interfaces and W in metrics/storage after room-area scaling; always state **Radiator Heat Input** units explicitly.
- "MPC" and "Economic MPC" are used interchangeably; use **Economic MPC** when referring to the implemented objective and **MPC** only as a short label in plots.
- "Case 3", "learned model", and "WandB model" refer to the same current learned-controller model family in scripts; pick **Learned Model** unless the thesis taxonomy specifically requires **Case 3**.
- "hopt", "sweep", "tuning", and "optimization" refer to Optuna controller search; use **Hyperparameter Optimization** in documentation.
