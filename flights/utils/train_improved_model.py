"""
Improved ML Model Training Script
Creates an ensemble model with better feature engineering for flight price prediction
"""

import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import warnings
warnings.filterwarnings('ignore')


class ImprovedFlightPriceModel:
    """
    Ensemble model for flight price prediction with advanced feature engineering
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.encoder = OneHotEncoder(sparse=False, handle_unknown='ignore')
        self.models = {
            'rf': RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42),
            'gb': GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, random_state=42),
            'lr': LinearRegression()
        }
        self.feature_names = None
        self.categorical_features = ['airline_name', 'aircraft_type', 'departure_airport', 
                                    'arrival_airport', 'flight_class', 'refundable_status']
        self.numerical_features = ['dep_hour', 'arr_hour', 'baggage_kg', 'flight_duration', 
                                  'days_to_departure', 'is_weekend', 'season', 'occupancy_rate']

    def create_synthetic_training_data(self, n_samples=5000):
        """
        Create synthetic training data for Nepal domestic flights
        """
        airlines = ['YETI AIRLINES', 'NEPAL AIRLINES', 'BUDDHA AIR', 'SHREE AIRLINES']
        aircraft = ['ATR72', 'DHRUV', 'DHC6', 'CRJ200']
        airports = ['KTM', 'PKR', 'BRT', 'DHM', 'NGJ', 'JMM']
        classes = ['E1', 'E2', 'B', 'B2']
        refund = ['Refundable', 'NonRefundable']
        seasons = [0, 1, 2, 3]  # Winter, Spring, Summer, Fall

        data = {
            'airline_name': np.random.choice(airlines, n_samples),
            'aircraft_type': np.random.choice(aircraft, n_samples),
            'departure_airport': np.random.choice(airports, n_samples),
            'arrival_airport': np.random.choice(airports, n_samples),
            'flight_class': np.random.choice(classes, n_samples),
            'refundable_status': np.random.choice(refund, n_samples),
            'dep_hour': np.random.randint(6, 22, n_samples),
            'arr_hour': np.random.randint(6, 22, n_samples),
            'baggage_kg': np.random.randint(10, 40, n_samples),
            'flight_duration': np.random.randint(30, 240, n_samples),
            'days_to_departure': np.random.randint(0, 60, n_samples),
            'is_weekend': np.random.randint(0, 2, n_samples),
            'season': np.random.choice(seasons, n_samples),
            'occupancy_rate': np.random.uniform(0.3, 0.95, n_samples),
        }

        df = pd.DataFrame(data)

        # Create realistic prices based on route
        route_base_prices = {
            ('KTM', 'PKR'): 3895,
            ('PKR', 'KTM'): 3895,
            ('KTM', 'BRT'): 5205,
            ('BRT', 'KTM'): 5205,
            ('KTM', 'DHM'): 5715,
            ('DHM', 'KTM'): 5715,
            ('KTM', 'NGJ'): 6105,
            ('NGJ', 'KTM'): 6105,
        }

        prices = []
        for idx, row in df.iterrows():
            route = (row['departure_airport'], row['arrival_airport'])
            base = route_base_prices.get(route, 4500)

            # Class adjustment
            class_mult = {'E1': 1.0, 'E2': 1.15, 'B': 1.35, 'B2': 1.55}.get(row['flight_class'], 1.0)
            base *= class_mult

            # Baggage adjustment
            if row['baggage_kg'] < 20:
                baggage_mult = 1.0
            elif row['baggage_kg'] < 30:
                baggage_mult = 1.05
            else:
                baggage_mult = 1.15
            base *= baggage_mult

            # Time adjustment (peak hours)
            if row['dep_hour'] in [7, 8, 9, 17, 18, 19]:
                base *= 1.15

            # Advance booking discount
            if row['days_to_departure'] >= 30:
                base *= 0.80
            elif row['days_to_departure'] >= 14:
                base *= 0.90
            elif row['days_to_departure'] >= 7:
                base *= 0.95

            # Season adjustment
            season_mult = [1.0, 1.2, 1.3, 1.1][row['season']]
            base *= season_mult

            # Weekend premium
            if row['is_weekend']:
                base *= 1.05

            # Occupancy-based pricing (scarcity)
            if row['occupancy_rate'] >= 0.9:
                base *= 1.25
            elif row['occupancy_rate'] >= 0.75:
                base *= 1.15

            # Refundable premium
            if row['refundable_status'] == 'Refundable':
                base *= 1.15

            # Add small noise
            base += np.random.normal(0, base * 0.05)
            prices.append(max(base * 0.8, base))  # Ensure minimum discount

        df['price'] = prices
        
        # Validate no same route
        df = df[df['departure_airport'] != df['arrival_airport']]
        
        return df

    def prepare_features(self, df, fit=False):
        """
        Prepare and transform features
        """
        X_cat = df[self.categorical_features].copy()
        X_num = df[self.numerical_features].copy()

        if fit:
            X_cat_encoded = self.encoder.fit_transform(X_cat)
            X_num_scaled = self.scaler.fit_transform(X_num)
        else:
            X_cat_encoded = self.encoder.transform(X_cat)
            X_num_scaled = self.scaler.transform(X_num)

        X = np.hstack([X_cat_encoded, X_num_scaled])

        if fit:
            # Create feature names
            cat_features = self.encoder.get_feature_names_out(self.categorical_features)
            self.feature_names = np.concatenate([cat_features, self.numerical_features])

        return X

    def train(self, df=None):
        """
        Train the ensemble model
        """
        if df is None:
            print("Generating synthetic training data...")
            df = self.create_synthetic_training_data(5000)
        
        print(f"Training data shape: {df.shape}")
        print(f"Price range: रु{df['price'].min():.2f} - रु{df['price'].max():.2f}")

        # Prepare features
        X = self.prepare_features(df, fit=True)
        y = df['price'].values

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        print("\nTraining ensemble models...")

        # Train individual models
        for name, model in self.models.items():
            print(f"  Training {name.upper()}...", end=" ")
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            print(f"MAE: रु{mae:.2f}, R²: {r2:.3f}")

        print("\nModel training complete!")
        return self.models, self.scaler, self.encoder, self.feature_names

    def predict(self, features_dict):
        """
        Make prediction on new data
        """
        # Convert dict to DataFrame with proper structure
        data = {
            'airline_name': [features_dict.get('airline_name', 'YETI AIRLINES')],
            'aircraft_type': [features_dict.get('aircraft_type', 'ATR72')],
            'departure_airport': [features_dict.get('departure_airport', 'KTM')],
            'arrival_airport': [features_dict.get('arrival_airport', 'PKR')],
            'flight_class': [features_dict.get('flight_class', 'E1')],
            'refundable_status': [features_dict.get('refundable_status', 'NonRefundable')],
            'dep_hour': [features_dict.get('dep_hour', 9)],
            'arr_hour': [features_dict.get('arr_hour', 10)],
            'baggage_kg': [features_dict.get('baggage_kg', 15)],
            'flight_duration': [features_dict.get('flight_duration', 60)],
            'days_to_departure': [features_dict.get('days_to_departure', 7)],
            'is_weekend': [features_dict.get('is_weekend', 0)],
            'season': [features_dict.get('season', 1)],
            'occupancy_rate': [features_dict.get('occupancy_rate', 0.7)],
        }
        
        df = pd.DataFrame(data)
        X = self.prepare_features(df, fit=False)

        # Ensemble prediction (weighted average of models)
        predictions = []
        weights = {'rf': 0.4, 'gb': 0.4, 'lr': 0.2}
        
        for name, weight in weights.items():
            pred = self.models[name].predict(X)[0]
            predictions.append(pred * weight)

        ensemble_pred = sum(predictions)
        
        # Add confidence score based on model agreement
        individual_preds = [self.models[name].predict(X)[0] for name in self.models]
        pred_range = max(individual_preds) - min(individual_preds)
        confidence = max(0, 1 - (pred_range / ensemble_pred * 0.2))  # Lower range = higher confidence

        return ensemble_pred, confidence

    def save_model(self, filepath):
        """
        Save the trained model
        """
        model_data = {
            'models': self.models,
            'scaler': self.scaler,
            'encoder': self.encoder,
            'feature_names': self.feature_names,
            'categorical_features': self.categorical_features,
            'numerical_features': self.numerical_features
        }
        joblib.dump(model_data, filepath)
        print(f"Model saved to {filepath}")


if __name__ == "__main__":
    print("=" * 60)
    print("IMPROVED FLIGHT PRICE PREDICTION MODEL")
    print("=" * 60)

    # Create and train model
    trainer = ImprovedFlightPriceModel()
    models, scaler, encoder, features = trainer.train()

    # Test the model
    print("\n" + "=" * 60)
    print("MODEL TESTING")
    print("=" * 60)

    test_cases = [
        {
            'airline_name': 'YETI AIRLINES',
            'aircraft_type': 'ATR72',
            'departure_airport': 'KTM',
            'arrival_airport': 'PKR',
            'flight_class': 'E1',
            'refundable_status': 'NonRefundable',
            'dep_hour': 9,
            'arr_hour': 10,
            'baggage_kg': 15,
            'flight_duration': 45,
            'days_to_departure': 14,
            'is_weekend': 0,
            'season': 1,
            'occupancy_rate': 0.7
        },
        {
            'airline_name': 'NEPAL AIRLINES',
            'aircraft_type': 'DHC6',
            'departure_airport': 'KTM',
            'arrival_airport': 'BRT',
            'flight_class': 'B',
            'refundable_status': 'Refundable',
            'dep_hour': 18,
            'arr_hour': 19,
            'baggage_kg': 25,
            'flight_duration': 120,
            'days_to_departure': 30,
            'is_weekend': 1,
            'season': 2,
            'occupancy_rate': 0.85
        }
    ]

    for i, test in enumerate(test_cases, 1):
        price, confidence = trainer.predict(test)
        print(f"\nTest Case {i}:")
        print(f"  Route: {test['departure_airport']} -> {test['arrival_airport']}")
        print(f"  Class: {test['flight_class']}")
        print(f"  Predicted Price: रु{price:.2f}")
        print(f"  Confidence: {confidence:.1%}")

    # Save the model
    print("\n" + "=" * 60)
    model_path = "flights/models/improved_flight_price_model.pkl"
    trainer.save_model(model_path)
    print(f"\n✅ Improved model saved to: {model_path}")
