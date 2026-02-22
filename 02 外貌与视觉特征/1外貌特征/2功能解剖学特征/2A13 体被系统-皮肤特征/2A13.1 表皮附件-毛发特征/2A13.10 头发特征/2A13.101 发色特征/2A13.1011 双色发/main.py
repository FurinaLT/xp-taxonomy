#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
目录下md文件和文件夹批量重命名工具
功能：替换直接子级文件/文件夹名称中的指定文本，排除index.md
"""

import os
import re
import sys
from pathlib import Path


def batch_rename(directory, old_text, new_text, dry_run=True):
    """
    批量重命名目录下的md文件和文件夹
    
    Args:
        directory: 目标目录路径
        old_text: 要替换的文本
        new_text: 替换后的文本
        dry_run: True为预览模式，False为实际执行
    
    Returns:
        (成功列表, 跳过列表, 失败列表)
    """
    target_dir = Path(directory).resolve()
    
    if not target_dir.exists():
        print(f"❌ 错误：目录不存在 {target_dir}")
        return [], [], []
    
    if not target_dir.is_dir():
        print(f"❌ 错误：{target_dir} 不是目录")
        return [], [], []
    
    success_list = []
    skip_list = []
    fail_list = []
    
    # 获取直接子级（不递归）
    items = list(target_dir.iterdir())
    
    print(f"\n{'='*60}")
    print(f"📁 目标目录: {target_dir}")
    print(f"🔍 替换规则: '{old_text}' → '{new_text}'")
    print(f"⚡ 执行模式: {'【预览模式】' if dry_run else '【实际执行】'}")
    print(f"{'='*60}\n")
    
    for item in items:
        original_name = item.name
        
        # 排除index.md文件（不区分大小写）
        if original_name.lower() == "index.md":
            skip_list.append((original_name, "保留文件"))
            print(f"⏭️  跳过: {original_name} (保留文件)")
            continue
        
        # 检查是否需要替换
        if old_text not in original_name:
            skip_list.append((original_name, "无需替换"))
            continue
        
        # 生成新名称
        new_name = original_name.replace(old_text, new_text)
        new_path = item.parent / new_name
        
        # 检查目标是否已存在
        if new_path.exists():
            fail_list.append((original_name, new_name, "目标已存在"))
            print(f"❌ 失败: {original_name} → {new_name} (目标已存在)")
            continue
        
        try:
            if dry_run:
                # 预览模式
                print(f"👁️  预览: {original_name}")
                print(f"       → {new_name}")
                success_list.append((original_name, new_name))
            else:
                # 实际执行
                item.rename(new_path)
                print(f"✅ 成功: {original_name}")
                print(f"       → {new_name}")
                success_list.append((original_name, new_name))
                
        except Exception as e:
            fail_list.append((original_name, new_name, str(e)))
            print(f"❌ 失败: {original_name} → {new_name} ({e})")
    
    # 打印统计
    print(f"\n{'='*60}")
    print(f"📊 统计结果:")
    print(f"   ✅ 成功/预览: {len(success_list)}")
    print(f"   ⏭️  跳过: {len(skip_list)}")
    print(f"   ❌ 失败: {len(fail_list)}")
    print(f"{'='*60}")
    
    return success_list, skip_list, fail_list


def interactive_mode():
    """交互式模式"""
    print("🛠️  批量重命名工具")
    print("-" * 40)
    
    # 获取目录
    directory = input("请输入目标目录路径 (默认当前目录): ").strip()
    if not directory:
        directory = "."
    
    # 获取替换规则
    old_text = input("请输入要替换的文本: ").strip()
    if not old_text:
        print("❌ 错误：要替换的文本不能为空")
        return
    
    new_text = input("请输入替换后的文本: ").strip()
    
    # 先执行预览
    print("\n" + "="*60)
    print("🔍 先执行预览模式...")
    success, skip, fail = batch_rename(directory, old_text, new_text, dry_run=True)
    
    if not success:
        print("\n⚠️  没有需要重命名的项目")
        return
    
    # 确认执行
    confirm = input("\n是否确认执行实际重命名? (yes/no): ").strip().lower()
    if confirm in ['yes', 'y']:
        batch_rename(directory, old_text, new_text, dry_run=False)
    else:
        print("❎ 已取消操作")


def main():
    """主函数 - 支持命令行参数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='批量重命名目录下的md文件和文件夹（排除index.md）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 交互式模式
  python rename_tool.py
  
  # 预览模式（默认）
  python rename_tool.py -d ./docs -o "旧文本" -n "新文本"
  
  # 实际执行
  python rename_tool.py -d ./docs -o "旧文本" -n "新文本" --execute
        """
    )
    
    parser.add_argument('-d', '--directory', default='.', 
                       help='目标目录路径 (默认: 当前目录)')
    parser.add_argument('-o', '--old', 
                       help='要替换的文本')
    parser.add_argument('-n', '--new', default='',
                       help='替换后的文本 (默认: 空字符串)')
    parser.add_argument('-e', '--execute', action='store_true',
                       help='实际执行重命名（否则为预览模式）')
    
    args = parser.parse_args()
    
    # 如果没有提供必要参数，进入交互模式
    if not args.old:
        interactive_mode()
        return
    
    # 命令行模式
    batch_rename(args.directory, args.old, args.new, dry_run=not args.execute)


if __name__ == "__main__":
    main()