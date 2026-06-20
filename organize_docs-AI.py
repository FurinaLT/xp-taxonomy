import os
import re
import json
import shutil
from pathlib import Path

# ========== 配置 ==========
WORKS_DIR = Path("./works")
DOCS_DIR = Path("./docs")
LIST_JSON_PATH = Path("./list.json")
BATCH_SIZE = 500

# 正则匹配两种格式：
# <i class="id">[编号]</i>  或  <i class="id">编号</i>
# [\[\]]* 表示方括号出现 0 次或多次
ID_PATTERN = re.compile(r'<i\s+class="id">\[*(\d+)\]*</i>')


def extract_id_from_md(file_path: Path) -> int | None:
    """从 md 文件开头提取编号，扫描前 30 行"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i > 30:
                    break
                match = ID_PATTERN.search(line)
                if match:
                    return int(match.group(1))
    except Exception as e:
        print(f"⚠️ 读取 {file_path} 失败: {e}")
    return None


def get_batch_folder(id_num: int) -> str:
    """根据编号计算所属批次文件夹名"""
    batch_start = (id_num // BATCH_SIZE) * BATCH_SIZE
    return str(batch_start)


def scan_works() -> dict:
    """扫描 works 目录"""
    file_map = {}
    md_files = list(WORKS_DIR.rglob("*.md"))
    
    if not md_files:
        print(f"⚠️ 警告：在 {WORKS_DIR.absolute()} 下没有找到任何 .md 文件！")
        return {}
    
    print(f"📁 找到 {len(md_files)} 个 md 文件，开始扫描编号...")
    
    for md_file in md_files:
        rel_path = md_file.relative_to(WORKS_DIR)
        file_id = extract_id_from_md(md_file)
        
        if file_id is None:
            print(f"   ❌ 跳过（未找到编号）: {rel_path}")
            # 调试：打印文件前3行看看
            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    preview = "".join([f.readline() for _ in range(3)])
                    print(f"      文件开头预览:\n{preview}")
            except:
                pass
            continue
        
        batch_folder = get_batch_folder(file_id)
        new_name = f"{file_id}.md"
        new_path = f"{batch_folder}/{new_name}"
        
        file_map[str(rel_path)] = {
            "id": file_id,
            "batch_folder": batch_folder,
            "new_name": new_name,
            "new_path": new_path,
            "abs_source": str(md_file)
        }
        print(f"   ✅ {rel_path} → 编号 {file_id} → docs/{new_path}")
    
    return file_map


def copy_files_to_docs(file_map: dict):
    """复制文件到 docs"""
    if not file_map:
        print("⚠️ 没有文件需要复制。")
        return
    
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    copied_count = 0
    
    print(f"\n📂 开始复制文件到 {DOCS_DIR.absolute()}...")
    
    for rel_path, info in file_map.items():
        source = Path(info["abs_source"])
        target_dir = DOCS_DIR / info["batch_folder"]
        target_file = target_dir / info["new_name"]
        
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target_file)
        copied_count += 1
    
    print(f"\n📦 共复制 {copied_count} 个文件到 docs（works 原文件保留）")


def build_nav_tree(file_map: dict) -> list:
    """构建 nav 树"""
    tree = {}
    
    for rel_path, info in file_map.items():
        parts = Path(rel_path).parts
        
        current = tree
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        filename = parts[-1]
        if filename.lower() == "index.md":
            nav_title = parts[-2] if len(parts) > 1 else "首页"
        else:
            nav_title = Path(filename).stem
        
        current[nav_title] = info["new_path"]
    
    return dict_to_nav_list(tree)


def dict_to_nav_list(d: dict) -> list:
    """字典转 nav 列表"""
    result = []
    for key, value in d.items():
        if isinstance(value, dict):
            result.append({key: dict_to_nav_list(value)})
        else:
            result.append({key: value})
    return result


def generate_nav_yaml(nav_list: list) -> str:
    """生成 nav YAML"""
    def write_nav(items, indent=0):
        lines = []
        prefix = "  " * indent
        for item in items:
            for key, value in item.items():
                if isinstance(value, list):
                    lines.append(f"{prefix}- {key}:")
                    lines.extend(write_nav(value, indent + 1))
                else:
                    lines.append(f"{prefix}- {key}: {value}")
        return lines
    
    return "\n".join(write_nav(nav_list))


def copy_to_clipboard(text: str):
    """复制到剪贴板"""
    try:
        import pyperclip
        pyperclip.copy(text)
        print("\n📋 nav 部分已复制到剪贴板！")
        return True
    except ImportError:
        print("\n⚠️ 未安装 pyperclip，请手动复制：")
        return False


def main():
    print("=" * 50)
    print("🚀 开始整理 works → docs")
    print("=" * 50)
    
    print(f"\n🔍 扫描目录: {WORKS_DIR.absolute()}")
    file_map = scan_works()
    
    if not file_map:
        print("\n❌ 没有找到可处理的文件，程序结束。")
        return
    
    with open(LIST_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(file_map, f, ensure_ascii=False, indent=2)
    print(f"\n📋 目录映射已保存到 {LIST_JSON_PATH}")
    
    copy_files_to_docs(file_map)
    
    print("\n🌲 正在构建导航树...")
    nav_list = build_nav_tree(file_map)
    nav_yaml = generate_nav_yaml(nav_list)
    
    success = copy_to_clipboard(nav_yaml)
    
    print("\n" + "=" * 50)
    print("nav:")
    print(nav_yaml)
    print("=" * 50)
    
    print("\n🎉 全部完成！把上面的 nav 粘贴到 mkdocs.yml 里就行啦")


if __name__ == "__main__":
    main()
