"""
PillScan — Model Export Script
Exports trained PyTorch model to ONNX and TFLite formats for deployment.

Usage:
    python export.py --model_path ../models/classification/best_model.pth --format onnx
    python export.py --model_path ../models/classification/best_model.pth --format tflite
    python export.py --model_path ../models/classification/best_model.pth --format all
"""

import os
import argparse
import json


def get_args():
    parser = argparse.ArgumentParser(description="Export PillScan Model")
    parser.add_argument("--model_path", type=str, required=True, help="Path to trained .pth model")
    parser.add_argument("--output_dir", type=str, default="../models/classification", help="Output directory")
    parser.add_argument("--format", type=str, default="all", choices=["onnx", "tflite", "all"])
    parser.add_argument("--img_size", type=int, default=224)
    parser.add_argument("--quantize", action="store_true", help="Apply INT8 quantization for TFLite")
    return parser.parse_args()


def export_onnx(model, output_path, img_size):
    """Export model to ONNX format for server deployment."""
    import torch

    dummy_input = torch.randn(1, 3, img_size, img_size)
    model.eval()

    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        export_params=True,
        opset_version=17,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={
            "input": {0: "batch_size"},
            "output": {0: "batch_size"},
        },
    )

    # Verify
    import onnx
    onnx_model = onnx.load(output_path)
    onnx.checker.check_model(onnx_model)

    file_size = os.path.getsize(output_path) / (1024 * 1024)
    print(f"   ✅ ONNX exported: {output_path} ({file_size:.1f} MB)")


def export_tflite(model, output_path, img_size, quantize=False):
    """Export model to TFLite format for mobile deployment."""
    import torch
    import numpy as np

    # First export to ONNX, then convert to TFLite
    # Alternative: Use torch → TF SavedModel → TFLite pipeline

    onnx_temp = output_path.replace(".tflite", "_temp.onnx")
    export_onnx(model, onnx_temp, img_size)

    try:
        import onnx
        from onnx_tf.backend import prepare
        import tensorflow as tf

        # ONNX → TF
        onnx_model = onnx.load(onnx_temp)
        tf_rep = prepare(onnx_model)

        saved_model_dir = output_path.replace(".tflite", "_saved_model")
        tf_rep.export_graph(saved_model_dir)

        # TF → TFLite
        converter = tf.lite.TFLiteConverter.from_saved_model(saved_model_dir)

        if quantize:
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            converter.target_spec.supported_types = [tf.int8]

            # Representative dataset for quantization calibration
            def representative_dataset():
                for _ in range(100):
                    data = np.random.rand(1, img_size, img_size, 3).astype(np.float32)
                    yield [data]

            converter.representative_dataset = representative_dataset
            print("   🔧 INT8 quantization enabled")

        tflite_model = converter.convert()

        with open(output_path, "wb") as f:
            f.write(tflite_model)

        file_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"   ✅ TFLite exported: {output_path} ({file_size:.1f} MB)")

    except ImportError:
        print("   ⚠️  TFLite export requires: pip install onnx-tf tensorflow")
        print("   Using ONNX model for server deployment instead.")
    finally:
        if os.path.exists(onnx_temp):
            os.remove(onnx_temp)


def main():
    args = get_args()

    try:
        import torch
        import timm
    except ImportError:
        print("❌ Missing: pip install torch timm")
        return

    print("=" * 60)
    print("PillScan Model Export")
    print("=" * 60)

    # Load trained model
    checkpoint = torch.load(args.model_path, map_location="cpu")
    num_classes = checkpoint.get("num_classes", 10)
    class_names = checkpoint.get("class_names", [])

    print(f"   Model: EfficientNet-V2-S")
    print(f"   Classes: {num_classes}")
    print(f"   Val Accuracy: {checkpoint.get('val_acc', 'N/A')}%")

    model = timm.create_model(
        "tf_efficientnetv2_s",
        pretrained=False,
        num_classes=num_classes,
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    os.makedirs(args.output_dir, exist_ok=True)

    if args.format in ("onnx", "all"):
        onnx_path = os.path.join(args.output_dir, "pillscan_classifier.onnx")
        export_onnx(model, onnx_path, args.img_size)

    if args.format in ("tflite", "all"):
        tflite_path = os.path.join(args.output_dir, "pillscan_classifier.tflite")
        export_tflite(model, tflite_path, args.img_size, quantize=args.quantize)

    # Save metadata
    metadata = {
        "model_name": "EfficientNet-V2-S",
        "num_classes": num_classes,
        "class_names": class_names,
        "input_size": args.img_size,
        "normalization": {
            "mean": [0.485, 0.456, 0.406],
            "std": [0.229, 0.224, 0.225],
        },
    }
    metadata_path = os.path.join(args.output_dir, "model_metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n   📋 Metadata saved: {metadata_path}")
    print(f"\n{'=' * 60}")
    print("Export complete!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
