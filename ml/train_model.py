import joblib

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from ml.model_data import MODEL_FILE, chronological_split, load_features, print_partitions
from ml.progression_features import EXERCISE, FEATURE_COLUMNS, FEATURE_SCHEMA_VERSION, TARGET_COLUMN


def fit_model(train, estimator):
    preprocessor = ColumnTransformer([
        ("exercise", OneHotEncoder(handle_unknown="ignore"), [EXERCISE]),
        ("numeric", "passthrough", FEATURE_COLUMNS[1:]),
    ])
    model = Pipeline([("preprocessor", preprocessor), ("model", estimator)])
    model.fit(train[FEATURE_COLUMNS], train[TARGET_COLUMN])
    model.progression_schema_version = FEATURE_SCHEMA_VERSION
    return model


def main():
    partitions = chronological_split(load_features())
    print_partitions(partitions)
    forest = RandomForestRegressor(
        n_estimators=300, max_depth=12, min_samples_leaf=2, random_state=42, n_jobs=1
    )
    model = fit_model(partitions[0], forest)
    MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary_model = MODEL_FILE.with_suffix(".tmp")
    joblib.dump(model, temporary_model)
    temporary_model.replace(MODEL_FILE)
    print(f"Saved {MODEL_FILE}")


if __name__ == "__main__":
    main()
