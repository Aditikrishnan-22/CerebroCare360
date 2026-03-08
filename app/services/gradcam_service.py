import os
import numpy as np
import tensorflow as tf
from PIL import Image
import cv2

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HEATMAP_DIR = os.path.join(BASE_DIR, 'app', 'static', 'heatmaps')

GRADCAM_MODEL = 'vgg16'
GRADCAM_LAYER = 'block5_conv3'


def generate_gradcam(image_path, model, class_idx, layer_name='block5_conv3'):
    os.makedirs(HEATMAP_DIR, exist_ok=True)

    grad_model = tf.keras.models.Model(
        inputs=model.inputs,
        outputs=[model.get_layer(layer_name).output, model.output]
    )

    img = Image.open(image_path).convert('RGB').resize((224, 224))
    img_array  = np.array(img, dtype=np.float32) / 255.0
    img_tensor = tf.constant(np.expand_dims(img_array, axis=0))

    with tf.GradientTape() as tape:
    tape.watch(img_tensor)
    outputs      = grad_model(img_tensor)
    conv_outputs = tf.convert_to_tensor(outputs[0])
    predictions  = tf.convert_to_tensor(outputs[1])
    loss         = tf.reduce_mean(predictions[:, class_idx])

    grads = tape.gradient(loss, conv_outputs)

    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2)).numpy()
    conv_outputs = conv_outputs[0].numpy()

    for i in range(pooled_grads.shape[0]):
        conv_outputs[:, :, i] *= pooled_grads[i]

    heatmap = np.mean(conv_outputs, axis=-1)
    heatmap = np.maximum(heatmap, 0)
    heatmap = heatmap / (np.max(heatmap) + 1e-8)

    heatmap_resized = cv2.resize(heatmap, (224, 224))
    heatmap_uint8   = np.uint8(255 * heatmap_resized)
    heatmap_colored = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
    heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)

    original      = np.array(img)
    superimposed  = heatmap_colored * 0.4 + original * 0.6
    superimposed  = np.clip(superimposed, 0, 255).astype(np.uint8)

    base_name        = os.path.splitext(os.path.basename(image_path))[0]
    overlay_filename = f"{base_name}_gradcam.png"
    overlay_path     = os.path.join(HEATMAP_DIR, overlay_filename)
    Image.fromarray(superimposed).save(overlay_path)

    print(f"GradCAM saved: {overlay_path}")
    return overlay_filename


def generate_gradcam_for_scan(image_path, models, class_idx):
    try:
        if GRADCAM_MODEL in models:
            return generate_gradcam(image_path, models[GRADCAM_MODEL], class_idx, GRADCAM_LAYER)
        else:
            name = list(models.keys())[0]
            return generate_gradcam(image_path, models[name], class_idx, GRADCAM_LAYER)
    except Exception as e:
        import traceback
        print(f"GradCAM generation failed: {e}")
        traceback.print_exc()
        return None