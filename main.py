import os
import re
import pyperclip

DOCS_DIR = "docs"


def title_from_name(name: str, is_file: bool, parent_dir: str = None) -> str:
    """
    生成 nav 中显示的标题：
    - 文件：去掉 .md
    - 目录：原样保留（允许包含 .）
    - 如果是 index.md，使用父级目录名作为标题
    """
    if is_file:
        # 如果文件是 index.md，使用父目录名称
        if name == "index.md" and parent_dir:
            return title_from_name(parent_dir, is_file=False)  # 使用父目录名称
        name = os.path.splitext(name)[0]
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


def build_nav(current_path: str, docs_root: str, parent_dir: str = None):
    items = []

    entries = sorted(
        os.listdir(current_path),
        key=sort_key
    )

    for entry in entries:
        if entry.startswith("."):
            continue

        full_path = os.path.join(current_path, entry)

        if os.path.isdir(full_path):
            # 递归构建文件夹
            children = build_nav(full_path, docs_root, entry)
            if children:
                items.append({
                    title_from_name(entry, is_file=False): children
                })

        elif entry.endswith(".md"):
            # 文件处理
            rel_path = os.path.relpath(full_path, docs_root).replace("\\", "/")
            items.append({
                title_from_name(entry, is_file=True, parent_dir=parent_dir): rel_path
            })

    return items


def dump_yaml(nav_items, indent=2):
    lines = ["nav:"]

    def walk(items, level):
        space = " " * level
        for item in items:
            for key, value in item.items():
                if isinstance(value, list):
                    lines.append(f"{space}- {key}:")
                    walk(value, level + indent)
                else:
                    lines.append(f"{space}- {key}: {value}")

    walk(nav_items, indent)
    return "\n".join(lines)


if __name__ == "__main__":
    nav = build_nav(DOCS_DIR, DOCS_DIR)
    yaml_text = dump_yaml(nav)

    pyperclip.copy(yaml_text)

    print("✅ MkDocs nav 已生成（已复制到剪贴板）\n")
    print(yaml_text)
