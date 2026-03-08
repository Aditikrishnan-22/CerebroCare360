import os
import numpy as np
from PIL import Image
import tensorflow as tf
from tensorflow.keras.applications.efficientnet import preprocess_input as eff_preprocess

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_DIR = os.path.join(BASE_DIR, 'models')

_models           = {}
_ensemble_weights = None

CLASS_NAMES = ['glioma', 'meningioma', 'notumor', 'pituitary']
IMG_SIZE    = (224, 224)


def _load_models():
    global _models
    if _models:
        return _models
    model_files = {
        'vgg16':        'vgg16_best.h5',
        'resnet50':     'resnet50_best.h5',
        'efficientnet': 'efficientnet_best.h5'
    }
    for name, filename in model_files.items():
        path = os.path.join(MODEL_DIR, filename)
        if os.path.exists(path):
            print(f'Loading {name}...')
            _models[name] = tf.keras.models.load_model(path)
            print(f'{name} loaded ✅')
        else:
            print(f'WARNING: {name} not found at {path}')
    return _models


def _get_weights():
    global _ensemble_weights
    if _ensemble_weights:
        return _ensemble_weights
    _ensemble_weights = {
        'vgg16':        0.3665,
        'resnet50':     0.2787,
        'efficientnet': 0.3548
    }
    return _ensemble_weights


def _preprocess(image_path, model_name):
    img = Image.open(image_path).convert('RGB')
    img = img.resize(IMG_SIZE)
    arr = np.array(img, dtype=np.float32)
    if model_name == 'efficientnet':
        arr = eff_preprocess(arr)
    else:
        arr = arr / 255.0
    return np.expand_dims(arr, axis=0)


def predict(image_path):
    models  = _load_models()
    weights = _get_weights()

    if not models:
        raise ValueError('No models loaded. Check models/ folder.')

    weighted_sum = np.zeros(4)
    total_weight = 0.0

    for name, model in models.items():
        w    = weights.get(name, 1.0)
        arr  = _preprocess(image_path, name)
        pred = model.predict(arr, verbose=0)[0]
        weighted_sum += pred * w
        total_weight += w

    final_probs = weighted_sum / total_weight
    class_idx   = int(np.argmax(final_probs))
    confidence  = float(final_probs[class_idx])
    tumor_type  = CLASS_NAMES[class_idx]
    has_tumor   = tumor_type != 'notumor'

    # GradCAM
    heatmap_filename = None
    try:
        from app.services.gradcam_service import generate_gradcam_for_scan
        heatmap_filename = generate_gradcam_for_scan(image_path, models, class_idx)
        print(f'GradCAM result: {heatmap_filename}')
    except Exception as e:
        import traceback
        print('GradCAM FULL ERROR:')
        traceback.print_exc()

    return {
        'has_tumor':         has_tumor,
        'tumor_type':        tumor_type,
        'confidence':        confidence,
        'low_confidence':    confidence < 0.50,
        'prob_glioma':       float(final_probs[0]),
        'prob_meningioma':   float(final_probs[1]),
        'prob_notumor':      float(final_probs[2]),
        'prob_pituitary':    float(final_probs[3]),
        'model_version':     'ensemble-v1 (3 models)',
        'heatmap_filename':  heatmap_filename,
    }