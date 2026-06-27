#!/usr/bin/env python3
"""
PillScan — Pill Image Dataset Collector
========================================

Utility script to download and organize pill images from public sources
for training the PillScan AI models.

Sources:
  1. NIH C3PI (Computational Photography Project for Pill Identification)
  2. Web search (Google Images via direct URLs)
  3. Saudi SFDA product image catalog

Usage:
    python collect_dataset.py --output ./dataset --per-class 100

This script creates the directory structure expected by
colab_training_pipeline.py.
"""

import os
import sys
import json
import hashlib
import argparse
import urllib.request
from pathlib import Path
from typing import Dict, List

# The 10 SFDA-registered medications matching our system
PILL_CLASSES: Dict[str, Dict] = {
    'panadol_extra': {
        'search_terms': ['panadol extra tablet', 'panadol extra pill white oval'],
        'shape': 'oval',
        'color': 'white',
        'description_en': 'Paracetamol 500mg + Caffeine 65mg',
        'description_ar': 'باراسيتامول ٥٠٠ + كافيين ٦٥',
    },
    'amoxil_500mg': {
        'search_terms': ['amoxil 500mg capsule', 'amoxicillin capsule red yellow'],
        'shape': 'capsule',
        'color': 'red-yellow',
        'description_en': 'Amoxicillin 500mg',
        'description_ar': 'أموكسيسيلين ٥٠٠',
    },
    'glucophage_500mg': {
        'search_terms': ['glucophage 500mg tablet', 'metformin tablet white round'],
        'shape': 'round',
        'color': 'white',
        'description_en': 'Metformin 500mg',
        'description_ar': 'ميتفورمين ٥٠٠',
    },
    'lipitor_10mg': {
        'search_terms': ['lipitor 10mg tablet', 'atorvastatin tablet white oval'],
        'shape': 'oval',
        'color': 'white',
        'description_en': 'Atorvastatin 10mg',
        'description_ar': 'أتورفاستاتين ١٠',
    },
    'zestril_10mg': {
        'search_terms': ['zestril 10mg tablet', 'lisinopril tablet pink round'],
        'shape': 'round',
        'color': 'pink',
        'description_en': 'Lisinopril 10mg',
        'description_ar': 'ليزينوبريل ١٠',
    },
    'augmentin_625mg': {
        'search_terms': ['augmentin 625mg tablet', 'augmentin tablet white oval'],
        'shape': 'oval',
        'color': 'white',
        'description_en': 'Amoxicillin/Clavulanate 625mg',
        'description_ar': 'أموكسيسيلين/كلافولانيت ٦٢٥',
    },
    'ventolin_2mg': {
        'search_terms': ['ventolin 2mg tablet', 'salbutamol tablet white round'],
        'shape': 'round',
        'color': 'white',
        'description_en': 'Salbutamol 2mg',
        'description_ar': 'سالبوتامول ٢',
    },
    'nexium_20mg': {
        'search_terms': ['nexium 20mg capsule', 'esomeprazole capsule purple'],
        'shape': 'capsule',
        'color': 'purple',
        'description_en': 'Esomeprazole 20mg',
        'description_ar': 'إيزوميبرازول ٢٠',
    },
    'concor_5mg': {
        'search_terms': ['concor 5mg tablet', 'bisoprolol tablet yellow heart'],
        'shape': 'heart',
        'color': 'yellow',
        'description_en': 'Bisoprolol 5mg',
        'description_ar': 'بيزوبرولول ٥',
    },
    'brufen_400mg': {
        'search_terms': ['brufen 400mg tablet', 'ibuprofen tablet pink round'],
        'shape': 'round',
        'color': 'pink',
        'description_en': 'Ibuprofen 400mg',
        'description_ar': 'إيبوبروفين ٤٠٠',
    },
}


def create_directory_structure(output_dir: str) -> None:
    """Create the expected dataset directory structure."""
    for split in ['train', 'val', 'test']:
        for class_name in PILL_CLASSES:
            class_dir = os.path.join(output_dir, split, class_name)
            os.makedirs(class_dir, exist_ok=True)
    print(f"✅ Directory structure created at: {output_dir}")


def generate_metadata(output_dir: str) -> None:
    """Generate a metadata JSON file describing each drug class."""
    metadata = {
        'project': 'PillScan',
        'university': 'University of Tabuk',
        'num_classes': len(PILL_CLASSES),
        'classes': {}
    }
    
    for idx, (class_name, info) in enumerate(PILL_CLASSES.items()):
        metadata['classes'][class_name] = {
            'index': idx,
            'shape': info['shape'],
            'color': info['color'],
            'description_en': info['description_en'],
            'description_ar': info['description_ar'],
            'search_terms': info['search_terms'],
        }
    
    metadata_path = os.path.join(output_dir, 'metadata.json')
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"✅ Metadata written to: {metadata_path}")


def generate_label_map(output_dir: str) -> None:
    """Generate the label map file for TFLite mobile deployment."""
    labels_path = os.path.join(output_dir, 'pill_labels.txt')
    with open(labels_path, 'w') as f:
        for class_name in PILL_CLASSES:
            f.write(f"{class_name}\n")
    print(f"✅ Label map written to: {labels_path}")


def print_collection_guide() -> None:
    """Print a manual collection guide for when automated download isn't available."""
    print("\n" + "=" * 70)
    print("📸 Manual Image Collection Guide for PillScan")
    print("=" * 70)
    print()
    print("For best model accuracy, collect images with these guidelines:")
    print()
    print("📐 Image Specifications:")
    print("   - Resolution: at least 640×640 pixels")
    print("   - Format: JPEG or PNG")
    print("   - File size: 50KB - 5MB")
    print()
    print("📷 Photography Tips:")
    print("   - Use a white or neutral background")
    print("   - Photograph from directly above (top-down)")
    print("   - Include varied angles (±30°)")
    print("   - Vary lighting (daylight, indoor, flash)")
    print("   - Include partial pill views for robustness")
    print("   - Photograph both single and multiple pills")
    print()
    print("🎯 Minimum Images per Class:")
    print("   - Training: 80+ images")
    print("   - Validation: 20+ images")
    print("   - Test: 10+ images")
    print()
    print("📋 Classes to photograph:")
    print()
    for idx, (name, info) in enumerate(PILL_CLASSES.items()):
        print(f"   {idx+1:2d}. {name}")
        print(f"       {info['description_en']} / {info['description_ar']}")
        print(f"       Shape: {info['shape']}, Color: {info['color']}")
        print()
    
    print("=" * 70)
    print("💡 Place photos in: dataset/<split>/<class_name>/")
    print("   Example: dataset/train/panadol_extra/img_001.jpg")
    print("=" * 70)


def count_dataset(output_dir: str) -> None:
    """Count images in each class directory and print summary."""
    print("\n📊 Dataset Summary:")
    print("-" * 60)
    print(f"{'Class':<25} {'Train':>8} {'Val':>8} {'Test':>8} {'Total':>8}")
    print("-" * 60)
    
    grand_total = 0
    for class_name in PILL_CLASSES:
        counts = {}
        for split in ['train', 'val', 'test']:
            class_dir = Path(output_dir) / split / class_name
            if class_dir.exists():
                count = len([f for f in class_dir.iterdir() 
                           if f.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp')])
            else:
                count = 0
            counts[split] = count
        
        total = sum(counts.values())
        grand_total += total
        
        status = "✅" if counts['train'] >= 80 else ("⚠️" if counts['train'] >= 20 else "❌")
        print(f"  {status} {class_name:<22} {counts['train']:>8} {counts['val']:>8} {counts['test']:>8} {total:>8}")
    
    print("-" * 60)
    print(f"{'TOTAL':<28} {'':<8} {'':<8} {'':<8} {grand_total:>8}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description='PillScan Dataset Collection Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create directory structure
  python collect_dataset.py --output ./dataset --setup
  
  # Print collection guide
  python collect_dataset.py --guide
  
  # Count current images
  python collect_dataset.py --output ./dataset --count
        """
    )
    parser.add_argument('--output', type=str, default='./dataset',
                        help='Output directory for dataset')
    parser.add_argument('--setup', action='store_true',
                        help='Create directory structure and metadata')
    parser.add_argument('--guide', action='store_true',
                        help='Print manual collection guide')
    parser.add_argument('--count', action='store_true',
                        help='Count images in dataset')
    
    args = parser.parse_args()
    
    if args.guide:
        print_collection_guide()
        return
    
    if args.setup:
        create_directory_structure(args.output)
        generate_metadata(args.output)
        generate_label_map(args.output)
        print_collection_guide()
        return
    
    if args.count:
        count_dataset(args.output)
        return
    
    # Default: setup + guide
    create_directory_structure(args.output)
    generate_metadata(args.output)
    generate_label_map(args.output)
    print_collection_guide()


if __name__ == '__main__':
    main()
