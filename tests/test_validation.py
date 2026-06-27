import numpy as np
import pytest
from systemictau.validation import evaluate_early_warning

def test_evaluate_early_warning():
    try:
        import sklearn
    except ImportError:
        pytest.skip("scikit-learn not installed")
        
    predictions = np.array([0.1, 0.2, 0.8, 0.9, 0.2])
    truth = np.array([0, 0, 1, 1, 0])
    
    metrics = evaluate_early_warning(predictions, truth, threshold=0.5)
    assert metrics['precision'] == 1.0
    assert metrics['recall'] == 1.0
    assert metrics['false_alarm_rate'] == 0.0
    assert metrics['auc'] == 1.0
