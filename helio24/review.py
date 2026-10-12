"""Review frozen predictions without modifying model selection or thresholds."""
import numpy as np


def classify_windows(predictions, threshold):
    review = predictions.copy()
    alarm = review.probability >= threshold
    positive = review.target.eq(1)
    review['outcome'] = np.select(
        [alarm & positive, alarm & ~positive, ~alarm & positive],
        ['Hits', 'False alarms', 'Misses'], default='Correct quiet forecasts',
    )
    return review


def review_export(review):
    """Exclude local paths and model inputs from the downloadable review."""
    columns = ['harp', 'forecast_time', 'prediction_end', 'label', 'probability', 'outcome']
    return review[columns].sort_values(['forecast_time', 'harp']).to_csv(index=False)
