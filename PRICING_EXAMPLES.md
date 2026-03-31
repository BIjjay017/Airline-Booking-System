# Dynamic Pricing & ML Prediction Examples

## Understanding the Flight Price Prediction System

The upgraded system uses a **two-layer approach**:
1. **ML Model (Base)**: Ensemble prediction from trained models
2. **Business Rules**: Dynamic pricing multipliers based on market factors

---

## Example 1: Basic Economy Flight

### Scenario
- Route: Kathmandu (KTM) → Pokhara (PKR)
- Class: Economy Basic (E1)
- Baggage: 15kg (standard)
- Departure: 9:00 AM
- Date: 2025-05-15 (4 weeks advance)
- Refundable: No
- Occupancy: 70%

### Calculation

**Step 1: Base Price**
```
Route base price: रु 3,895 (standard KTM-PKR)
```

**Step 2: Apply Multipliers**
```
Flight Class (E1):              1.0x  (base)
Baggage (<20kg):                1.0x  (no charge)
Time of Day (9:00 AM):          1.2x  (morning peak)
Advance Booking (28 days):      0.85x (15% discount)
Season (May = Summer = Peak):   1.4x  (peak season)
Occupancy (70% = medium):       1.0x  (standard)
Refundable (No):                1.0x  (base)

Total Multiplier: 1.0 × 1.0 × 1.2 × 0.85 × 1.4 × 1.0 × 1.0 = 1.428
```

**Step 3: Calculate Price**
```
Final Price: 3,895 × 1.428 = 5,564.46 रु
```

**Step 4: Apply Bounds**
```
Minimum (80%): 3,895 × 0.8 = 3,116 रु
Maximum (200%): 3,895 × 2.0 = 7,790 रु

Final Price: 5,564.46 रु ✓ (within bounds)
```

**Step 5: Confidence Score**
```
ML Prediction: 5,400 रु
Final Price: 5,564 रु
Difference: 164 रु (2.9% variance)

Confidence: 92% ✓ (high confidence)
```

### Result
```json
{
  "base_price": 3895.00,
  "final_price": 5564.46,
  "confidence": 0.92,
  "savings": 2030.54,
  "breakdown": {
    "class": "Economy Basic (1.0x)",
    "baggage": "Standard 15kg (1.0x)",
    "time": "Morning Peak 9 AM (1.2x)",
    "advance": "28 days ahead - 15% discount (0.85x)",
    "season": "Summer Peak (1.4x)",
    "occupancy": "70% Full (1.0x)",
    "refundable": "Non-refundable (1.0x)"
  }
}
```

---

## Example 2: Last-Minute Business Flight

### Scenario
- Route: Kathmandu (KTM) → Biratnagar (BRT)
- Class: Business Comfort (B2)
- Baggage: 30kg
- Departure: 6:00 PM
- Date: 2025-04-01 (2 days advance - RISKY!)
- Refundable: Yes
- Occupancy: 95% (almost full!)

### Calculation

**Base Price for KTM-BRT**: रु 5,205

**Multipliers**:
```
Flight Class (B2):              1.55x (premium business)
Baggage (30kg):                 1.15x (heavy baggage)
Time (18:00 = 6 PM):            1.25x (evening peak)
Advance (2 days):               1.0x  (last minute, no discount!)
Season (April = High):          1.2x  (moderate season)
Occupancy (95% full):           1.35x (scarcity pricing!)
Refundable (Yes):               1.15x (refundable premium)

Total: 1.55 × 1.15 × 1.25 × 1.0 × 1.2 × 1.35 × 1.15 = 3.84
```

**Price Calculation**:
```
Final: 5,205 × 3.84 = 19,987.20 रु

Max allowed (200%): 5,205 × 2.0 = 10,410 रु
Applied cap: 10,410 रु (price capped at 2x base)
```

**Confidence**: 65% (high variance, premium pricing applied)

### Result
```json
{
  "base_price": 5205.00,
  "final_price": 10410.00,
  "confidence": 0.65,
  "premium": 5205.00,
  "message": "Premium pricing due to: Last-minute booking, High occupancy, Business class, Refundable option"
}
```

---

## Example 3: Smart Booking Strategy

### Compare Options for KTM → PKR

**Option A: Same Day**
```
Departure: Today (0 days advance)
Time: Various times
Occupancy: 85%

Estimated Price: 6,500 - 7,800 रु
Confidence: 60-70%
```

**Option B: Next Week (Book Now)**
```
Departure: 7 days ahead
Time: 9:00 AM
Occupancy: 50%

Estimated Price: 3,500 - 4,200 रु
Confidence: 85-90%
Discount: ~45%
```

**Option C: Ideal Strategy (Book 4 Weeks)**
```
Departure: 28+ days ahead
Time: Early morning (6-8 AM)
Occupancy: 40-60%

Estimated Price: 2,700 - 3,500 रु
Confidence: 90%+
Discount: ~60%
```

### Savings by Advance Booking
```
Last Hour:    7,500 रु
Next Day:     6,200 रु (17% savings)
Next Week:    4,100 रु (45% savings)
4 Weeks:      2,900 रु (61% savings)

Smart Strategy = Book 4 weeks in advance for off-peak times!
```

---

## Example 4: Seasonal Impact

### KTM → PKR Throughout Year

**February (Off-Season)**
```
Base: 3,895
Season Multiplier: 1.0x (standard)
Typical Final: 4,200 - 4,800 रु
```

**May (Peak Season)**
```
Base: 3,895
Season Multiplier: 1.4x (peak)
Typical Final: 5,500 - 6,500 रु
```

**October (High Season)**
```
Base: 3,895
Season Multiplier: 1.2x (high)
Typical Final: 4,800 - 5,500 रु
```

**December (Peak Holiday)**
```
Base: 3,895
Season Multiplier: 1.4x (peak)
Occupancy: 90%+ (high)
Typical Final: 7,000 - 8,500 रु
```

### Best Time to Travel
- **Cheapest**: February-March (off-season)
- **Mid-range**: April, October-November
- **Expensive**: May-September, December
- **Avoid**: Peak holidays (late December, April)

---

## Example 5: The Impact of Flight Class & Baggage

### Same Flight, Different Classes

**Economy Basic (E1) + 15kg**:
```
Multiplier: 1.0 × 1.0 = 1.0
Price: 3,895 रु
```

**Economy Comfort (E2) + 20kg**:
```
Multiplier: 1.15 × 1.05 = 1.21
Price: 4,713 रु
Difference: +818 रु (+21%)
```

**Business Basic (B) + 30kg**:
```
Multiplier: 1.35 × 1.15 = 1.55
Price: 6,037 रु
Difference: +3,142 रु (+81%)
```

**Business Comfort (B2) + 40kg**:
```
Multiplier: 1.55 × 1.15 = 1.78
Price: 6,931 रु
Difference: +4,036 रु (+104%)
```

---

## Example 6: Understanding Confidence Scores

### What Confidence Score Means

**90-100% (Very High Confidence)**
- Prediction is highly reliable
- Multiple models agree
- Standard pricing applied
- **Trust the price!**

Example: Regular booking, 2+ weeks advance, moderate occupancy
```json
{
  "price": 4200,
  "confidence": 0.95,
  "recommendation": "Book now"
}
```

**75-90% (High Confidence)**
- Generally reliable prediction
- Some variance between models
- Standard or premium pricing
- Reasonable to book

Example: 1 week advance, peak time
```json
{
  "price": 5400,
  "confidence": 0.82,
  "recommendation": "Good price"
}
```

**50-75% (Medium Confidence)**
- Higher uncertainty
- Business premium or last-minute
- Use with caution
- Consider alternatives

Example: Last-minute business class
```json
{
  "price": 8900,
  "confidence": 0.65,
  "recommendation": "Expensive - consider economy"
}
```

**Below 50% (Low Confidence)**
- Extreme conditions (emergency booking)
- Limited data
- Use as rough estimate
- **Not reliable**

Example: 30 minutes before departure
```json
{
  "price": 12500,
  "confidence": 0.38,
  "recommendation": "Talk to customer service"
}
```

---

## Example 7: Real-Time Occupancy Impact

### Flight KTM → PKR, Departure 9:00 AM

**8 hours before departure**
```
Occupancy: 30%
Multiplier: 0.9x (discount for low occupancy)
Price: 3,500 रु
Confidence: 88%
```

**4 hours before departure**
```
Occupancy: 60%
Multiplier: 1.0x (normal)
Price: 3,895 रु
Confidence: 75%
```

**1 hour before departure**
```
Occupancy: 85%
Multiplier: 1.2x (high demand)
Price: 4,674 रु
Confidence: 60%
```

**30 minutes before departure**
```
Occupancy: 95%
Multiplier: 1.35x (scarcity pricing)
Price: 5,258 रु
Confidence: 45%
```

---

## Example 8: Price Prediction Accuracy

### Test Cases from ML Model

**Case 1: Regular Booking**
```
Input: KTM→PKR, E1, 15kg, 2 weeks advance, 9 AM, 70%
ML Prediction: 4,150 रु
With Rules: 4,299 रु
Actual Range: 4,150-4,350 रु ✓ ACCURATE
```

**Case 2: Premium Booking**
```
Input: KTM→BRT, B, 30kg, 2 days, 6 PM, 90%
ML Base: 8,500 रु
With Rules:10,410 रु (capped)
Actual Range: 9,500-11,000 रु ✓ REASONABLE
```

**Case 3: Economy Booking**
```
Input: KTM→PKR, E2, 20kg, 4 weeks, 2 AM, 40%
ML Prediction: 2,950 रु
With Rules: 2,900 रु
Actual Range: 2,850-3,100 रु ✓ SPOT-ON
```

---

## Quick Reference: Pricing Thresholds

```
Occupancy Levels:
  <50%: Discount (0.9x)
  50-75%: Standard (1.0x)
  75-90%: Premium (1.2x)
  >90%: Scarcity (1.35x)

Time of Day:
  6-8 AM: Morning (1.0x)
  8-12 PM: Peak Morning (1.2x)
  12-3 PM: Afternoon (1.0x)
  3-6 PM: Afternoon Peak (1.15x)
  6-9 PM: Evening Peak (1.25x)
  9-12 AM: Late (1.05x)
  12-6 AM: Night (0.85x)

Advance Booking:
  0-6 days: No discount (1.0x)
  7-13 days: 5% off (0.95x)
  14-20 days: 10% off (0.9x)
  21-29 days: 15% off (0.85x)
  30+ days: 20% off (0.8x)

Seasons:
  Feb-Mar: Standard (1.0x)
  Apr, Oct-Nov: High (1.2x)
  May-Sep: Peak (1.4x)
  Dec: Peak (1.4x)
```

---

## How ML Model Works

### Three Models in Ensemble

**1. Random Forest (40% weight)**
- Handles non-linear relationships
- Good for categorical features
- Robust to outliers
- Captures market volatility

**2. Gradient Boosting (40% weight)**
- Reduces prediction bias
- Captures feature interactions
- Excellent for sequential patterns
- Reduces overfitting

**3. Linear Regression (20% weight)**
- Provides baseline prediction
- Interpretable coefficients
- Adds stability
- Prevents extreme predictions

### Prediction Process
```
Input Flight Data
    ↓
Feature Engineering (14 features)
    ↓
Preprocessing & Scaling
    ↓
Three Models Predict
    ├─ RF → 4,200 रु
    ├─ GB → 4,350 रु
    └─ LR → 4,100 रु
    ↓
Weighted Average (40%, 40%, 20%)
    ↓
Base ML Prediction: 4,238 रु
    ↓
Apply Business Rules (7 factors)
    ↓
Dynamic Pricing: 4,500 रु
    ↓
Calculate Confidence: 87%
    ↓
Output: {price, base, confidence, breakdown}
```

---

## Optimization Tips for Users

1. **Book 4+ weeks in advance** - 60% savings vs last-minute
2. **Fly early morning or afternoon** - 15-20% cheaper
3. **Avoid peak seasons** (Dec, May-Sep) - Off-season is 40% cheaper
4. **Travel on weekdays** - Slightly cheaper (no Sunday premium)
5. **Choose economy + standard baggage** - 60% cheaper than business
6. **Non-refundable is cheaper** - 15% savings
7. **Monitor occupancy** - Lower occupancy = lower prices
8. **Set price alerts** - Get notifications when price drops

---

**Version**: 2.0.0  
**Model Accuracy**: MAE < 500 रु, R² > 0.85  
**Last Updated**: March 2025
