# Workout progression model correction

## Root cause

The previous training pipeline subtracted historical values from target-day statistics. A Random Forest could use the resulting change values to reconstruct the target directly. The prior name-based leakage check missed this because the input columns had derived names. Date-ordered splitting could isolate later rows while still allowing the answer inside each row. The original audit found that the one-session weight change reproduced the target difference in 100% of rows and the two-session change did so in 96.43%.

Production used prior sessions for similarly named columns. It also grouped records by date instead of workout timestamp and computed the time gap and trend from different sessions. The previous offline recommendation evaluator ran a different policy from FastAPI.

## Feature definitions

The target is the maximum recorded working weight on exercise date $t$. Inputs use records strictly before $t$. The model still takes 30 ordered inputs, including the exercise name. The CSV holds the target date and weight separately from those inputs.

| Input | Before | After |
| --- | --- | --- |
| `weight_change` | Weight at $t$ minus weight at $t-1$ | Weight at $t-1$ minus weight at $t-2$ |
| `volume_change` | Volume at $t$ minus volume at $t-1$ | Volume at $t-1$ minus volume at $t-2$ |
| `reps_change` | Reps at $t$ minus reps at $t-1$ | Reps at $t-1$ minus reps at $t-2$ |
| `one_rm_change` | Estimated 1RM at $t$ minus estimated 1RM at $t-1$ | Estimated 1RM at $t-1$ minus estimated 1RM at $t-2$ |
| `weight_change_2` | Weight at $t$ minus weight at $t-2$ when available | Weight at $t-1$ minus weight at $t-3$ |
| `volume_change_2` | Volume at $t$ minus volume at $t-2$ when available | Volume at $t-1$ minus volume at $t-3$ |
| `one_rm_change_2` | Estimated 1RM at $t$ minus estimated 1RM at $t-2$ when available | Estimated 1RM at $t-1$ minus estimated 1RM at $t-3$ |
| Previous and lagged statistics | Historical shifts with zero-filled gaps during training | Explicit $t-1$, $t-2$, and $t-3$ values after the three-session gate |
| Gap and count | Training gap ended at target timestamp. Session count used timestamp-level rows. | Calendar days between $t-2$ and $t-1$. Count of all valid historical exercise dates. |
| Rolling means and recent bests | Shifted training features could use fewer than three sessions. | Means for weight, volume, reps, and 1RM, plus maximum weight and 1RM, using exactly the latest three sessions. |
| Weight, volume, and 1RM trends | Training compared $t-1$ with $t-3$. Serving used a fourth historical session where available. | Compare $t-1$ with $t-4$, falling back to $t-3$ when only three sessions exist. |

The shared aggregator groups per athlete and exercise wherever athlete IDs are available. FastAPI queries one user and exercise. Both paths normalize names and use one exercise session per UTC calendar date. For each day, the aggregator sums set counts, reps and weight × reps, and takes the maximum working weight and maximum Epley estimated 1RM across its records. For API records with repeated sets, the set count multiplies per-set reps and volume. It converts logged kilograms to pounds using 0.45359237 kg/lb. The dataset retains the prior alias normalization, exact duplicate removal, the Chin Up and Weighted dips exclusions, and the Squat (Barbell) outlier rule above 1,000 lb. Workout history dated after today is omitted from prediction. Invalid dates and invalid required statistics fail explicitly.

## Dataset and partitions

The repository's input is `data/weightlifting_721_workouts.csv`. It has no athlete identifier or documented upstream source in the checkout and appears to represent one athlete. Preprocessing retained 8,401 of 9,932 set records after exact duplicate removal. Aggregation and filtering produced 1,725 eligible exercise sessions. Feature generation produced **1,535 supervised observations**, down from 1,653 under the previous pipeline. The minimum history rose from one session to three, and same-day exercise records now merge.

| Partition | Observations | Inclusive target dates |
| --- | ---: | --- |
| Training | 1,075 | 2015-11-08 to 2018-02-21 |
| Validation | 229 | 2018-02-22 to 2018-06-03 |
| Test | 231 | 2018-06-05 to 2018-09-29 |

Shared split logic assigns whole dates by observation count near the 70% and 85% cutoffs. The exercise encoder and both estimators fit on training only. Random Forest retains 300 trees, depth 12, minimum leaf size 2, and random seed 42. Its validation MAE was 21.9738 lb. No model hyperparameters were chosen from the held-out results.

## Held-out performance

MAE, RMSE, and median absolute error are in pounds. Positive relative MAE improvement means lower error than persistence.

| Predictor | MAE | RMSE | Median absolute error | R² | MAE improvement |
| --- | ---: | ---: | ---: | ---: | ---: |
| Previous weight | 18.7706 | 29.9280 | 10.0000 | 0.9409 | 0.00% |
| Recent-three-session mean | 18.0657 | 27.9576 | 13.3333 | 0.9484 | 3.76% |
| Linear Regression | 19.0994 | 28.8324 | 12.1119 | 0.9451 | −1.75% |
| Random Forest | 19.1626 | 28.9525 | 13.5688 | 0.9447 | −2.09% |

The recent-three-session mean had the lowest held-out MAE and RMSE. Random Forest had 2.09% higher MAE than persistence and remains the configured production estimator as requested. The evaluation script prints the held-out count and MAE for each of the 29 evaluated exercises.

### Per-exercise MAE (lb)

| Exercise | Test n | Persistence | Recent three mean | Linear Regression | Random Forest |
| --- | ---: | ---: | ---: | ---: | ---: |
| Bench Press (Barbell) | 14 | 13.21 | 16.07 | 14.76 | 18.47 |
| Bent Over Row (Dumbbell) | 2 | 15.00 | 6.67 | 8.22 | 11.21 |
| Bicep Curl (Barbell) | 14 | 8.21 | 7.38 | 12.28 | 6.28 |
| Deadlift (Barbell) | 3 | 51.67 | 56.11 | 35.10 | 43.59 |
| Deadlift - Trap Bar | 1 | 90.00 | 90.00 | 148.81 | 111.80 |
| Face pull | 5 | 10.00 | 6.67 | 9.89 | 4.47 |
| Hack Squat | 4 | 26.25 | 32.08 | 8.84 | 19.78 |
| Hammer Curl (Dumbbell ) | 3 | 6.67 | 8.89 | 4.75 | 9.55 |
| Hammer High Row - 1 Arm | 8 | 8.75 | 20.00 | 23.75 | 23.68 |
| Hammer Row - Wide Grip | 15 | 18.67 | 17.33 | 18.31 | 15.00 |
| Hammer lat pulldown | 1 | 45.00 | 58.33 | 37.85 | 55.78 |
| Hammer seated row (CLOSE GRIP) | 16 | 15.00 | 15.00 | 10.18 | 17.68 |
| Incline Bench Press (Barbell) | 15 | 7.33 | 8.22 | 8.57 | 12.16 |
| Incline Press (Dumbbell) | 8 | 20.00 | 14.17 | 13.63 | 14.77 |
| Lat Pulldown | 2 | 32.50 | 15.00 | 16.22 | 22.69 |
| Lateral Raise (Dumbbells) | 14 | 2.86 | 2.86 | 5.96 | 3.96 |
| Leg curl | 1 | 10.00 | 5.00 | 7.77 | 9.10 |
| Leg outward fly | 3 | 3.33 | 4.44 | 8.09 | 4.49 |
| Leg press (hinge ) | 9 | 56.67 | 72.96 | 73.71 | 78.19 |
| Low Incline Dumbbell Bench | 5 | 18.00 | 18.00 | 18.00 | 17.36 |
| Neutral Chin | 16 | 32.25 | 21.71 | 36.56 | 24.33 |
| Overhead Press (Dumbbell) | 1 | 0.00 | 20.00 | 31.02 | 15.46 |
| Romanian Deadlift (Barbell) | 18 | 7.22 | 11.48 | 8.80 | 12.01 |
| Seated Cable Row (close Grip) | 5 | 13.00 | 12.33 | 20.02 | 15.28 |
| Seated Shoulder Press (Barbell) | 12 | 8.33 | 11.11 | 12.28 | 14.87 |
| Seated Shoulder Press (Dumbbell) | 1 | 50.00 | 55.00 | 64.55 | 54.15 |
| Squat (Barbell) | 26 | 39.04 | 26.41 | 27.25 | 25.49 |
| T-bar Row | 8 | 8.75 | 8.44 | 6.66 | 13.70 |
| Tricep pushdown | 1 | 10.00 | 16.67 | 11.45 | 15.02 |

### Walk-forward recommendation results

For each test date, walk-forward evaluation reconstructed the exercise's prefix using only logged sessions before that date. Earlier held-out sessions become available to later predictions. The regressor stays fixed. All 231 reconstructed input vectors and targets matched the held-out CSV. Evaluation executed the same adjustment function as the workout prediction route and scored the final returned kilogram value in pounds.

| Output | MAE (lb) | RMSE (lb) |
| --- | ---: | ---: |
| Previous weight | 18.7706 | 29.9280 |
| Raw Random Forest | 19.1626 | 28.9525 |
| Hybrid recommendation | 18.4845 | 28.7707 |

The hybrid's MAE was 1.52% lower than persistence. Of 232 eligible exercise sessions in the test date range, 231 received recommendations and one fell below the three-session threshold, for 99.57% coverage. There were 129 decreases, 102 increases, and zero unchanged recommendations. Changes ranged from −9.9337 to +9.9507 lb, with a median of −0.3960 lb. There were zero constraint violations.

The production adjustment blends the raw prediction, recent average, and signed change. It permits reductions and uses configurable defaults of up to 10 lb in either direction with a zero floor. It rounds once, to a feasible 2.5 kg increment. If no increment fits, it returns the bounded unrounded value. The FastAPI response supplies `history_sufficiency` and the equivalent legacy `confidence` field. The score is based on recorded session count. Calorie estimation remains formula-based.

## Verification and limitations

- The leakage audit reconstructed every exported row. Changing selected target and subsequent sessions left 755 earlier observations and the inputs of 50 selected target observations unchanged.
- Eleven automated tests cover target and future independence, feature calculations, low-history behavior, athlete and exercise isolation, disjoint partitions, input validation, aggregation, unit conversion, bounded rounding, and backend parity.
- The backend test exercised the workout recommendation route with mocked MongoDB results and the actual serialized model. Every numeric serving input matched the offline training input to ten decimal places. The exercise name, model input order, and delivered recommendation matched exactly. The production model loader checks its cached model's schema version and feature order.
- The model learns and is evaluated on one apparent athlete's history. Some exercises have only one held-out example. The measured errors describe agreement with observed working weights and cannot establish optimal loading, training outcomes, safety, or a prediction interval. The history-sufficiency value is a heuristic.
- The Angular production build passed with Node.js 24.22.3. The ML scripts and tests passed in the existing `ai-fitness` environment using Python 3.12.13, pandas 3.0.5, and scikit-learn 1.9.0. Joblib emitted a NumPy deprecation warning while loading the artifact.
- The live MongoDB and Render deployment were outside this verification. The existing checkout on `B:` was read-only from this session. The changes were built and verified in a writable copy; the repository overlay contains the files to apply together.

## File inventory

| Status | File | Purpose |
| --- | --- | --- |
| Added | `ml/progression_features.py` | Ordered feature contract, daily aggregation, history validation, and historical prefixes |
| Added | `ml/model_data.py` | Artifact paths, feature CSV contract check, and whole-date partitions |
| Added | `tests/test_progression_features.py` | Feature, aggregation, temporal isolation, and recommendation tests |
| Added | `tests/test_workout_prediction.py` | Route-level parity, serialized schema, and cold-start tests |
| Added | `docs/ml-progression-report.md` | Implementation, evaluation, and reproduction report |
| Updated | `ml/data_processing/preprocess.py` | Reuse the shared exercise normalizer |
| Updated | `ml/data_processing/create_features.py` | Aggregate cleaned sets and export strictly historical observations |
| Updated | `ml/train_model.py` | Train on the shared split and mark the corrected artifact schema |
| Updated | `ml/evaluate_model.py` | Compare four predictors, including per-exercise test counts and errors |
| Updated | `ml/audit_leakage.py` | Rebuild the export and perturb targets and future sessions |
| Updated | `ml/recommendation.py` | Shared pure recommendation policy and bounds |
| Updated | `ml/evaluate_recommendations.py` | Walk-forward evaluation using the production policy |
| Updated | `backend/app/services/workout_prediction.py` | Shared aggregation and feature generation, cached model, and compatible responses |
| Updated | `frontend/src/app/features/predictions/predictions/predictions.html` | Label the history-sufficiency indicator |
| Updated | `frontend/src/app/features/workouts/workouts/workouts.html` | Label the history-sufficiency indicator |
| Updated | `README.md` | Corrected ML scope, metrics, and test instructions |
| Regenerated | `models/workout_weight_model.joblib` | Corrected Random Forest artifact |
| Regenerated | `data/processed/workout_progression_features.csv` | Corrected supervised dataset |
| Regenerated locally | `data/processed/weightlifting_clean.csv` | Intermediate preprocessing output |
| Regenerated locally | `data/processed/recommendation_evaluation.csv` | Session-by-session walk-forward results |

Original copies of the model and feature CSV were saved to the writable working copy's `backups/` folder before regeneration. The original checkout also retains both files.

## Reproduce

Run from the repository root after applying the overlay. To retain the original artifacts in a separate copy, save `models/workout_weight_model.joblib` and `data/processed/workout_progression_features.csv` before applying the overlay or regenerating artifacts.

```powershell
conda activate ai-fitness
python -m ml.data_processing.preprocess
python -m ml.data_processing.create_features
python -m ml.audit_leakage
python -m ml.train_model
python -m ml.evaluate_model
python -m ml.evaluate_recommendations
python -m unittest discover -s tests -v
```

Run `npm run build` from `frontend` with its existing Node dependencies installed. The backend should start from the repository root with `uvicorn backend.app.main:app` so the shared `ml` imports and model artifact resolve.
