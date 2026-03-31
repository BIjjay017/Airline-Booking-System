"""
Advanced Dynamic Pricing Engine
Combines ML predictions with business rules for realistic pricing
"""
import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from .ml_model import predict_from_form, get_fallback_prediction
from flights.config import get_db_connection


class DynamicPricingEngine:
    """
    Advanced pricing engine that combines ML predictions with dynamic pricing rules
    """
    
    # Base pricing tier for different routes (in NRS)
    ROUTE_BASE_PRICES = {
        ('KATHMANDU', 'POKHARA'): 3895,
        ('POKHARA', 'KATHMANDU'): 3895,
        ('KATHMANDU', 'BIRATNAGAR'): 5205,
        ('BIRATNAGAR', 'KATHMANDU'): 5205,
        ('KATHMANDU', 'DHANGADI'): 5715,
        ('DHANGADI', 'KATHMANDU'): 5715,
        ('KATHMANDU', 'NEPALGUNJ'): 6105,
        ('NEPALGUNJ', 'KATHMANDU'): 6105,
        ('POKHARA', 'BIRATNAGAR'): 6555,
        ('BIRATNAGAR', 'POKHARA'): 6555,
    }

    # Multipliers for different seasons
    SEASON_MULTIPLIERS = {
        'peak': 1.4,      # May-Sep, Dec
        'high': 1.2,      # Jan, Apr, Oct-Nov
        'standard': 1.0   # Feb, Mar
    }

    # Class upgrades
    CLASS_MULTIPLIERS = {
        'E1': 1.0,      # Economy basic
        'E2': 1.15,     # Economy comfort
        'B': 1.35,      # Business basic
        'B2': 1.55      # Business comfort
    }

    # Baggage tier pricing
    BAGGAGE_MULTIPLIERS = {
        'light': 1.0,      # < 20kg
        'standard': 1.05,  # 20-30kg
        'heavy': 1.15      # > 30kg
    }

    # Time of day multipliers
    HOUR_MULTIPLIERS = {
        (6, 8): 1.0,       # Early morning
        (8, 12): 1.2,      # Morning peak
        (12, 15): 1.0,     # Afternoon
        (15, 18): 1.15,    # Afternoon peak
        (18, 21): 1.25,    # Evening peak
        (21, 24): 1.05,    # Late evening
        (0, 6): 0.85       # Night
    }

    # Advance booking discounts
    ADVANCE_BOOKING_DISCOUNTS = {
        30: 0.80,      # 30+ days: 20% discount
        21: 0.85,      # 21-29 days: 15% discount
        14: 0.90,      # 14-20 days: 10% discount
        7: 0.95,       # 7-13 days: 5% discount
        0: 1.0         # 0-6 days: no discount
    }

    def __init__(self):
        self.cache = {}

    def get_dynamic_price(self, form_data):
        """
        Calculate dynamic price using ML model + business rules
        
        Args:
            form_data: dict with flight details
            
        Returns:
            dict: {
                'base_price': float,
                'final_price': float,
                'confidence': float,
                'breakdown': dict
            }
        """
        try:
            # Get ML prediction as base
            ml_price = predict_from_form(form_data)
            
            # Get base route price if available
            departure = str(form_data.get('departure_airport', 'KATHMANDU')).upper()
            arrival = str(form_data.get('arrival_airport', 'POKHARA')).upper()
            
            route_base = self.ROUTE_BASE_PRICES.get((departure, arrival), ml_price)
            base_price = max(ml_price, route_base)  # Use the higher of two
            
            # Calculate all multipliers
            multiplier = 1.0
            breakdown = {
                'base_price': base_price,
                'adjustments': {}
            }
            
            # 1. Flight class adjustment
            flight_class = str(form_data.get('flight_class', 'E1')).upper()
            class_mult = self.CLASS_MULTIPLIERS.get(flight_class, 1.0)
            multiplier *= class_mult
            breakdown['adjustments']['class'] = {
                'class': flight_class,
                'multiplier': class_mult
            }
            
            # 2. Baggage adjustment
            baggage = str(form_data.get('baggage_allowance', '15KG')).upper()
            baggage_kg = self._extract_baggage_weight(baggage)
            if baggage_kg < 20:
                baggage_mult = self.BAGGAGE_MULTIPLIERS['light']
            elif baggage_kg < 30:
                baggage_mult = self.BAGGAGE_MULTIPLIERS['standard']
            else:
                baggage_mult = self.BAGGAGE_MULTIPLIERS['heavy']
            multiplier *= baggage_mult
            breakdown['adjustments']['baggage'] = {
                'weight_kg': baggage_kg,
                'multiplier': baggage_mult
            }
            
            # 3. Time of day adjustment
            dep_time_str = str(form_data.get('departure_time', '09:00'))
            hour = self._extract_hour(dep_time_str)
            time_mult = self._get_time_multiplier(hour)
            multiplier *= time_mult
            breakdown['adjustments']['time'] = {
                'hour': hour,
                'multiplier': time_mult
            }
            
            # 4. Advance booking adjustment
            date_str = str(form_data.get('date', ''))
            advance_days = self._calculate_advance_days(date_str)
            advance_mult = self._get_advance_booking_discount(advance_days)
            multiplier *= advance_mult
            breakdown['adjustments']['advance_booking'] = {
                'days_ahead': advance_days,
                'multiplier': advance_mult
            }
            
            # 5. Seasonal adjustment
            date_obj = self._parse_date(date_str)
            if date_obj:
                season_type = self._get_season_type(date_obj.month)
                season_mult = self.SEASON_MULTIPLIERS.get(season_type, 1.0)
                multiplier *= season_mult
                breakdown['adjustments']['season'] = {
                    'season_type': season_type,
                    'multiplier': season_mult
                }
            
            # 6. Dynamic availability adjustment (from DB)
            try:
                availability_mult = self._get_availability_multiplier(departure, arrival, date_str)
                multiplier *= availability_mult
                breakdown['adjustments']['availability'] = {
                    'multiplier': availability_mult
                }
            except:
                pass
            
            # 7. Refundable status adjustment
            refundable = str(form_data.get('refundable_status', 'NonRefundable'))
            if 'Refundable' in refundable and 'Non' not in refundable:
                refund_mult = 1.15
            else:
                refund_mult = 1.0
            multiplier *= refund_mult
            breakdown['adjustments']['refundable'] = {
                'status': refundable,
                'multiplier': refund_mult
            }
            
            final_price = base_price * multiplier
            
            # Cap price - don't let it go below base or above 2x base
            final_price = max(base_price * 0.8, min(final_price, base_price * 2.0))
            
            breakdown['final_price'] = final_price
            breakdown['total_multiplier'] = multiplier
            
            # Confidence score (0-1) based on prediction quality
            confidence = self._calculate_confidence(ml_price, final_price, form_data)
            
            return {
                'base_price': round(base_price, 2),
                'final_price': round(final_price, 2),
                'confidence': confidence,
                'breakdown': breakdown,
                'currency': 'NRS'
            }
            
        except Exception as e:
            print(f"Pricing error: {e}")
            # Return simple fallback
            fallback = get_fallback_prediction(form_data)
            return {
                'base_price': round(fallback, 2),
                'final_price': round(fallback, 2),
                'confidence': 0.3,
                'breakdown': {'note': 'Fallback pricing used'},
                'currency': 'NRS'
            }

    def _extract_baggage_weight(self, baggage_str):
        """Extract weight in kg from baggage string"""
        import re
        matches = re.findall(r'(\d+\.?\d*)\s*KG', str(baggage_str).upper())
        if matches:
            return int(sum(float(value) for value in matches))
        return 15

    def _extract_hour(self, time_str):
        """Extract hour from time string (HH:MM)"""
        try:
            hour = int(time_str.split(':')[0])
            return hour
        except:
            return 12

    def _get_time_multiplier(self, hour):
        """Get price multiplier based on departure hour"""
        for (start, end), mult in self.HOUR_MULTIPLIERS.items():
            if start < end:
                if start <= hour < end:
                    return mult
            else:  # Night (21-24 and 0-6)
                if hour >= start or hour < end:
                    return mult
        return 1.0

    def _calculate_advance_days(self, date_str):
        """Calculate days between today and booking date"""
        try:
            date_obj = self._parse_date(date_str)
            if date_obj:
                today = datetime.now().date()
                normalized_date = date_obj.date() if hasattr(date_obj, 'date') else date_obj
                return (normalized_date - today).days
        except:
            pass
        return 7

    def _get_advance_booking_discount(self, days):
        """Get discount multiplier based on advance booking days"""
        if days >= 30:
            return self.ADVANCE_BOOKING_DISCOUNTS[30]
        elif days >= 21:
            return self.ADVANCE_BOOKING_DISCOUNTS[21]
        elif days >= 14:
            return self.ADVANCE_BOOKING_DISCOUNTS[14]
        elif days >= 7:
            return self.ADVANCE_BOOKING_DISCOUNTS[7]
        return self.ADVANCE_BOOKING_DISCOUNTS[0]

    def _parse_date(self, date_str):
        """Parse date string in multiple formats"""
        import re as regex
        patterns = [
            '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%d-%b-%Y', '%Y/%m/%d',
            '%d-%b', '%d-%B-%Y'
        ]
        for pattern in patterns:
            try:
                return datetime.strptime(str(date_str).strip(), pattern)
            except:
                continue
        try:
            return pd.to_datetime(date_str)
        except:
            return None

    def _get_season_type(self, month):
        """Determine season pricing tier"""
        if month in [5, 6, 7, 8, 9, 12]:
            return 'peak'
        elif month in [1, 4, 10, 11]:
            return 'high'
        else:
            return 'standard'

    def _get_availability_multiplier(self, departure, arrival, date_str):
        """Get price multiplier based on available seats"""
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            query = """
                SELECT f.available_seats, f.total_seats 
                FROM flights f
                JOIN airports ao ON f.origin_id = ao.airport_id
                JOIN airports ad ON f.destination_id = ad.airport_id
                WHERE ao.code = %s 
                  AND ad.code = %s 
                  AND DATE(f.departure_time) = %s
                ORDER BY f.departure_time
                LIMIT 1
            """
            cur.execute(query, (departure, arrival, date_str))
            result = cur.fetchone()
            cur.close()
            conn.close()
            
            if result:
                available, total = result
                occupancy_rate = (total - available) / total if total > 0 else 0
                
                # Higher occupancy = higher price
                if occupancy_rate >= 0.9:
                    return 1.35  # Nearly full - premium pricing
                elif occupancy_rate >= 0.75:
                    return 1.2   # High occupancy
                elif occupancy_rate >= 0.5:
                    return 1.0   # Medium occupancy
                else:
                    return 0.9   # Low occupancy - discount
            return 1.0
        except:
            return 1.0

    def _calculate_confidence(self, ml_price, final_price, form_data):
        """Calculate confidence score (0-1)"""
        # If prices are reasonable (within expected range), high confidence
        if 2000 < final_price < 30000:
            delta_ratio = min(abs(ml_price - final_price) / max(final_price, 1), 1.0)
            return round(max(0.45, min(0.95, 0.9 - (delta_ratio * 0.4))), 2)
        return 0.5


def get_pricing_engine():
    """Singleton getter for pricing engine"""
    if not hasattr(get_pricing_engine, 'instance'):
        get_pricing_engine.instance = DynamicPricingEngine()
    return get_pricing_engine.instance
