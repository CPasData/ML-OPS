import joblib
import pandas as pd
import numpy as np

model = joblib.load("./models/random_forest_churn.pkl")

print(model.feature_names_in)


# Reproducibilidad
np.random.seed(42)
n_samples = 50
countries = ['France', 'Spain', 'Germany']
genders = ['Male', 'Female']

data = pd.DataFrame({

    'credit_score': np.random.normal(
        loc=650,
        scale=95,
        size=n_samples
    ).clip(350, 850).astype(int),

    'country': np.random.choice(
        countries,
        size=n_samples,
        p=[0.5, 0.25, 0.25]
    ),

    'gender': np.random.choice(
        genders,
        size=n_samples,
        p=[0.55, 0.45]
    ),

    'age': np.random.normal(
        loc=39,
        scale=10,
        size=n_samples
    ).clip(18, 92).astype(int),

    # Antigüedad cliente
    'tenure': np.random.randint(
        0,
        11,
        size=n_samples
    ),

    # Balance
    'balance': np.random.normal(
        loc=76000,
        scale=62000,
        size=n_samples
    ).clip(0, 251000),

    # Número de productos
    'products_number': np.random.choice(
        [1, 2, 3, 4],
        size=n_samples,
        p=[0.5, 0.4, 0.08, 0.02]
    ),

    'credit_card': np.random.choice(
        [0, 1],
        size=n_samples,
        p=[0.3, 0.7]
    ),

    # Miembro activo
    'active_member': np.random.choice(
        [0, 1],
        size=n_samples,
        p=[0.48, 0.52]
    ),

    # Salario estimado
    'estimated_salary': np.random.uniform(
        11,
        200000,
        size=n_samples
    )
})

print(data.head())

sample = pd.DataFrame([{
    "credit_score": 721.43,
    "country": "Spain",
    "gender": "Male",
    "age": 29,
    "tenure": 7.01,
    "balance": 64000,
    "products_number": 1,
    "credit_card": 1,
    "active_member": 1,
    "estimated_salary": 42500
}])


print(model.predict(data))
print(model.predict_proba(data))

print(model.predict(sample))
print(model.predict_proba(sample))
