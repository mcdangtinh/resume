#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để resize và chuyển đổi tất cả ảnh trong assets/img/ 
sang format WebP với kích thước tối ưu cho web (nhẹ nhất).
"""

import os
from pathlib import Path
from PIL import Image
import sys

# Fix encoding cho Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Cấu hình
SOURCE_DIR = Path("assets/img")
OUTPUT_DIR = Path("assets/img-2")

# Kích thước tối đa cho các loại ảnh
MAX_WIDTH_LARGE = 1920  # Cho ảnh hero, background
MAX_WIDTH_MEDIUM = 1200  # Cho ảnh portfolio, gallery
MAX_WIDTH_SMALL = 800  # Cho ảnh nhỏ, icon
MAX_WIDTH_ICON = 256  # Cho icon nhỏ

# Quality cho WebP (80-85 là tốt, cân bằng giữa chất lượng và kích thước)
# WebP thường nhẹ hơn JPEG 25-35% với cùng chất lượng
WEBP_QUALITY = 82

def get_max_size(file_path):
    """
    Xác định kích thước tối đa dựa trên tên file và thư mục
    """
    path_str = str(file_path).lower()
    
    # Icon và favicon
    if any(keyword in path_str for keyword in ['icon', 'favicon', 'logo', 'ft/']):
        return MAX_WIDTH_ICON
    
    # Ảnh hero/background
    if any(keyword in path_str for keyword in ['hero', 'bg', 'background']):
        return MAX_WIDTH_LARGE
    
    # Ảnh profile
    if 'profile' in path_str:
        return MAX_WIDTH_MEDIUM
    
    # Ảnh portfolio, gallery
    if any(keyword in path_str for keyword in ['portfolio', 'masonry', 'canhan', 'sukien', 'lehoi', 'teambuilding', 'thuonghieu', 'linhvuc']):
        return MAX_WIDTH_MEDIUM
    
    # Mặc định
    return MAX_WIDTH_MEDIUM

def resize_image(input_path, output_path, max_size):
    """
    Resize ảnh giữ tỉ lệ và chuyển sang WebP (hỗ trợ transparency)
    """
    try:
        # Mở ảnh
        with Image.open(input_path) as img:
            # Giữ RGBA nếu có transparency (WebP hỗ trợ alpha channel)
            # Chỉ convert sang RGB nếu không có transparency
            has_transparency = img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info)
            
            if img.mode == 'P':
                # Convert palette mode sang RGBA để giữ transparency
                img = img.convert('RGBA')
            elif img.mode not in ('RGB', 'RGBA'):
                # Convert các mode khác
                if has_transparency:
                    img = img.convert('RGBA')
                else:
                    img = img.convert('RGB')
            
            # Lấy kích thước hiện tại
            width, height = img.size
            
            # Tính toán kích thước mới giữ tỉ lệ
            if width > max_size or height > max_size:
                if width > height:
                    new_width = max_size
                    new_height = int(height * (max_size / width))
                else:
                    new_height = max_size
                    new_width = int(width * (max_size / height))
                
                # Resize với LANCZOS (chất lượng tốt)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Tạo thư mục output nếu chưa có
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Lưu ảnh với WebP (method=6 là chất lượng nén tốt nhất nhưng chậm hơn)
            # method=4 là cân bằng tốt giữa tốc độ và kích thước
            img.save(output_path, 'WEBP', quality=WEBP_QUALITY, method=4)
            
            # Thông tin
            original_size = os.path.getsize(input_path) / 1024  # KB
            new_size = os.path.getsize(output_path) / 1024  # KB
            reduction = ((original_size - new_size) / original_size * 100) if original_size > 0 else 0
            
            return {
                'success': True,
                'original_size': original_size,
                'new_size': new_size,
                'reduction': reduction,
                'original_dim': (width, height),
                'new_dim': img.size
            }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def process_images():
    """
    Xử lý tất cả ảnh trong thư mục nguồn
    """
    if not SOURCE_DIR.exists():
        print(f"❌ Thư mục nguồn không tồn tại: {SOURCE_DIR}")
        return
    
    # Tạo thư mục output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Định dạng ảnh được hỗ trợ
    image_extensions = {'.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG', '.heic', '.HEIC', '.webp', '.WEBP'}
    
    # Đếm
    total_files = 0
    processed_files = 0
    failed_files = 0
    total_original_size = 0
    total_new_size = 0
    
    print(f"🖼️  Bắt đầu xử lý ảnh từ: {SOURCE_DIR}")
    print(f"📁 Lưu vào: {OUTPUT_DIR}\n")
    
    # Duyệt tất cả file
    for root, dirs, files in os.walk(SOURCE_DIR):
        for file in files:
            file_path = Path(root) / file
            
            # Kiểm tra extension
            if file_path.suffix not in image_extensions:
                continue
            
            total_files += 1
            
            # Tính đường dẫn tương đối
            relative_path = file_path.relative_to(SOURCE_DIR)
            output_path = OUTPUT_DIR / relative_path.with_suffix('.webp')
            
            # Xác định max size
            max_size = get_max_size(file_path)
            
            # Xử lý ảnh
            print(f"📸 Đang xử lý: {relative_path}")
            result = resize_image(file_path, output_path, max_size)
            
            if result['success']:
                processed_files += 1
                total_original_size += result['original_size']
                total_new_size += result['new_size']
                print(f"   ✅ Hoàn thành: {result['original_dim']} → {result['new_dim']}")
                print(f"   📊 Kích thước: {result['original_size']:.1f} KB → {result['new_size']:.1f} KB ({result['reduction']:.1f}% giảm)")
            else:
                failed_files += 1
                print(f"   ❌ Lỗi: {result['error']}")
            print()
    
    # Tổng kết
    print("=" * 60)
    print("📊 TỔNG KẾT")
    print("=" * 60)
    print(f"Tổng số file: {total_files}")
    print(f"Xử lý thành công: {processed_files}")
    print(f"Thất bại: {failed_files}")
    print(f"Kích thước ban đầu: {total_original_size:.1f} KB ({total_original_size/1024:.2f} MB)")
    print(f"Kích thước sau xử lý: {total_new_size:.1f} KB ({total_new_size/1024:.2f} MB)")
    if total_original_size > 0:
        total_reduction = ((total_original_size - total_new_size) / total_original_size * 100)
        print(f"Giảm: {total_reduction:.1f}%")
    print("=" * 60)

if __name__ == "__main__":
    try:
        process_images()
        print("\n✅ Hoàn thành!")
    except KeyboardInterrupt:
        print("\n\n⚠️  Đã dừng bởi người dùng")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

