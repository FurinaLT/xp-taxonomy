import os
import re
import pyperclip

DOCS_DIR = "docs"
FILE_NUM = 0

def title_from_name(name: str, is_file: bool, parent_dir: str = None, level: int = 0) -> str:
    """
    生成 nav 中显示的标题：
    - 文件：去掉 .md，原样保留（不修改）
    - 目录：
      - 一级目录（level=1）：原样保留
      - 二、三级目录（level=2,3）：去掉开头的单个数字或字母
      - 四级及以上（level>=4）：原样保留
    - 如果是 index.md，使用父级目录名作为标题
    """
    if is_file:
        # 如果文件是 index.md，使用父目录名称
        if name == "index.md" and parent_dir:
            return title_from_name(parent_dir, is_file=False, level=level-1)
        name = os.path.splitext(name)[0]
        return name.strip()
    
    # 以下是目录的处理
    # 只有二、三级目录需要去掉开头的单个数字或字母
    if level in [2, 3]:
        # 去掉开头的单个数字或字母
        name = re.sub(r'^[0-9A-Za-z]', '', name)
    
    return name.strip()


def sort_key(name: str):
    """
    用于排序，但不影响显示：
    支持：
      01
      1B21
      1B21.3
      1B21.3.2
    """
    m = re.match(r"^(\d+[A-Z]*?(?:\.\d+)*)", name)
    if m:
        return (0, m.group(1))
    return (1, name)


def build_nav(current_path: str, docs_root: str, parent_dir: str = None, level: int = 0):
    """
    level: 当前层级（0=docs根目录，1=一级目录，2=二级目录，3=三级目录...）
    """
    items = []

    entries = sorted(
        os.listdir(current_path),
        key=sort_key
    )

    for entry in entries:
        if entry.startswith("."):
            continue

        full_path = os.path.join(current_path, entry)
        # 下一级的层级是当前层级+1
        next_level = level + 1

        if os.path.isdir(full_path):
            # 递归构建文件夹
            children = build_nav(full_path, docs_root, entry, next_level)
            if children:
                items.append({
                    title_from_name(entry, is_file=False, parent_dir=parent_dir, level=next_level): children
                })

        elif entry.endswith(".md"):
            # 文件处理 - 文件不需要修改标题，但还是要传递 level 给 index.md 判断用
            rel_path = os.path.relpath(full_path, docs_root).replace("\\", "/")
            items.append({
                title_from_name(entry, is_file=True, parent_dir=parent_dir, level=next_level): rel_path
            })

    return items


def dump_yaml(nav_items, indent=2):
    global FILE_NUM

    lines = ["nav:"]

    def walk(items, level):
        global FILE_NUM
        space = " " * level
        for item in items:
            for key, value in item.items():
                if isinstance(value, list):
                    lines.append(f"{space}- {key}:")
                    walk(value, level + indent)
                else:
                    FILE_NUM += 1
                    lines.append(f"{space}- {key}: {value}")

    walk(nav_items, indent)
    return "\n".join(lines)


if __name__ == "__main__":
    nav = build_nav(DOCS_DIR, DOCS_DIR)
    yaml_text = dump_yaml(nav)

    pyperclip.copy(yaml_text)

    print(f"✅ MkDocs nav 已生成（已复制到剪贴板）\n文件数量: {FILE_NUM}\n词条数量: {FILE_NUM - 13}")