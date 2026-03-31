#!/usr/bin/env python3
"""
格式检查脚本 - 在 md_to_html 和 upload_draft 之间执行
检查 Markdown/HTML 是否符合微信公众号推荐规则

用法:
  python3 format_check.py article.md [--strict]

退出码:
  0 = 全部通过（或有仅警告）
  1 = 存在必须拦截的问题
"""

import argparse
import json
import re
import sys
from pathlib import Path


class CheckResult:
    def __init__(self):
        self.errors = []   # 必须拦截
        self.warnings = [] # 建议但放行
        self.info = []     # 纯信息

    def add_error(self, rule, msg):
        self.errors.append({"rule": rule, "msg": msg})

    def add_warning(self, rule, msg):
        self.warnings.append({"rule": rule, "msg": msg})

    def add_info(self, rule, msg):
        self.info.append({"rule": rule, "msg": msg})

    @property
    def passed(self):
        return len(self.errors) == 0


def check_markdown(md_text: str, result: CheckResult):
    """检查 Markdown 原文"""
    lines = md_text.strip().split("\n")

    # 提取标题（第一个 # 开头的行）
    title = ""
    for line in lines:
        m = re.match(r'^#\s+(.+)', line.strip())
        if m:
            title = m.group(1).strip()
            break

    # 1. 标题检查
    if not title:
        result.add_error("title", "缺少文章标题（# 开头的第一行）")
    elif len(title) < 10:
        result.add_warning("title", f"标题过短（{len(title)}字），建议15-30字")
    elif len(title) > 35:
        result.add_warning("title", f"标题过长（{len(title)}字），建议15-30字")
    else:
        result.add_info("title", f"标题长度OK：{len(title)}字")

    # 标题是否含数字+场景
    has_number = bool(re.search(r'\d', title))
    if has_number:
        result.add_info("title", "标题包含数字")
    else:
        result.add_warning("title", "标题不含数字，建议加入数字增加吸引力")

    # 2. 字数检查（去除空白和标记符号后的纯文本）
    plain_text = re.sub(r'[#*`>\-\[\]\(\)!|]', '', md_text)
    plain_text = re.sub(r'https?://\S+', '', plain_text)
    char_count = len(plain_text.strip())
    if char_count < 1000:
        result.add_warning("wordcount", f"字数偏少（约{char_count}字），日报建议1500-2500字")
    elif char_count > 5000:
        result.add_warning("wordcount", f"字数偏多（约{char_count}字），建议控制在4000字以内")
    else:
        result.add_info("wordcount", f"字数OK：约{char_count}字")

    # 3. 段落长度检查
    long_paragraphs = 0
    current_para_lines = 0
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and not stripped.startswith('-') and not stripped.startswith('*') and not stripped.startswith('>'):
            current_para_lines += 1
        else:
            if current_para_lines > 5:
                long_paragraphs += 1
            current_para_lines = 0
    if current_para_lines > 5:
        long_paragraphs += 1

    if long_paragraphs > 0:
        result.add_warning("paragraph", f"有{long_paragraphs}个段落超过5行，手机阅读体验可能不佳")

    # 4. H2 嵌套深度
    h2_count = 0
    h3_count = 0
    for line in lines:
        if re.match(r'^##\s', line.strip()):
            h2_count += 1
            h3_count = 0
        elif re.match(r'^###\s', line.strip()):
            h3_count += 1
            if h3_count > 3:
                result.add_warning("nesting", "H2 下超过3个H3，嵌套过深")

    # 5. 禁用词检查
    forbidden_terms = ['SEO', 'GEO', 'SEM', 'DAU', 'MAU', 'ROI优化', '转化率优化']
    for term in forbidden_terms:
        if term.lower() in md_text.lower():
            result.add_error("forbidden", f"文中包含禁用术语「{term}」，微信公众号推荐机制会降权")

    # 6. 钩子开头检查（前100字是否有价值导向）
    first_100 = md_text[:300].replace('#', '').strip()
    filler_patterns = [
        r'今天我们来聊', r'大家好', r'欢迎来到', r'很高兴',
        r'今天来分享', r'下面我来', r'接下来让我们'
    ]
    for pattern in filler_patterns:
        if re.search(pattern, first_100):
            result.add_warning("hook", f"开头可能包含废话铺垫（匹配到：{pattern}），建议直接给价值")
            break

    # 7. 互动引导检查
    interaction_keywords = ['评论区', '留言', '你怎么看', '关注不迷路', '下一篇', '预告']
    has_interaction = any(kw in md_text for kw in interaction_keywords)
    if not has_interaction:
        result.add_warning("interaction", "文章缺少互动引导（评论区/留言/关注等）")

    # 8. 分隔线数量
    hr_count = md_text.count('\n---\n') + md_text.count('\n***\n')
    if hr_count > 3:
        result.add_warning("hr", f"使用了{hr_count}个分隔线，过多影响阅读流畅度")

    return title


def check_html(html: str, result: CheckResult):
    """检查生成的 HTML"""
    # 1. 不支持的标签
    unsupported_tags = ['<video', '<iframe', '<object', '<embed', '<form', '<input']
    for tag in unsupported_tags:
        if tag in html.lower():
            result.add_error("html_tag", f"HTML 包含微信不支持的标签 {tag}")

    # 2. 图片 URL 检查（非微信CDN的图片）
    img_srcs = re.findall(r'src="(https?://[^"]+)"', html)
    non_wx_images = [src for src in img_srcs if 'mmbiz.qpic.cn' not in src and 'mmbiz.qlogo.cn' not in src]
    if non_wx_images:
        result.add_error("image_url", f"有{len(non_wx_images)}张图片使用非微信CDN URL，发布后可能无法显示")

    # 3. 外部链接检查
    external_links = re.findall(r'href="(https?://[^"]+)"', html)
    if external_links:
        result.add_warning("external_link", f"有{len(external_links)}个外部链接，建议转为底部引用")

    # 4. style 标签检查
    if '<style' in html.lower():
        result.add_error("style_tag", "HTML 包含 <style> 标签，微信不支持，必须使用内联样式")

    # 5. script 标签检查
    if '<script' in html.lower():
        result.add_error("script_tag", "HTML 包含 <script> 标签，微信不支持")

    return img_srcs, external_links


def main():
    parser = argparse.ArgumentParser(description="微信公众号文章格式检查")
    parser.add_argument("article", help="Markdown 文章路径")
    parser.add_argument("--html", help="预生成的 HTML（如不提供则自动转换）")
    parser.add_argument("--strict", action="store_true", help="严格模式：警告也视为错误")
    args = parser.parse_args()

    article_path = Path(args.article)
    if not article_path.exists():
        print(json.dumps({"passed": False, "error": f"文件不存在: {article_path}"}))
        sys.exit(1)

    md_text = article_path.read_text(encoding="utf-8")

    # 移除 frontmatter
    md_text = re.sub(r'^---\n.*?\n---\n', '', md_text, flags=re.DOTALL)

    result = CheckResult()

    # 检查 Markdown
    title = check_markdown(md_text, result)

    # 检查 HTML
    if args.html:
        html = Path(args.html).read_text(encoding="utf-8")
    else:
        # 尝试调用 md_to_html.py
        script_dir = Path(__file__).parent
        md_to_html = script_dir / "md_to_html.py"
        if md_to_html.exists():
            import subprocess
            proc = subprocess.run(
                [sys.executable, str(md_to_html), str(article_path)],
                capture_output=True, text=True
            )
            html = proc.stdout
        else:
            html = ""

    img_srcs, external_links = check_html(html, result)

    # 输出结果
    output = {
        "passed": result.passed and (not args.strict or len(result.warnings) == 0),
        "title": title,
        "summary": {
            "errors": len(result.errors),
            "warnings": len(result.warnings),
            "info": len(result.info)
        },
        "errors": result.errors,
        "warnings": result.warnings,
        "info": result.info,
        "stats": {
            "images": len(img_srcs),
            "external_links": len(external_links)
        }
    }

    # 打印可读报告
    print("=" * 50)
    print("📋 格式检查报告")
    print("=" * 50)
    print(f"标题：{title or '(无)'}")
    print(f"结果：{'✅ 通过' if output['passed'] else '❌ 未通过'}")
    print(f"错误：{len(result.errors)} | 警告：{len(result.warnings)} | 信息：{len(result.info)}")
    print()

    if result.errors:
        print("🚫 必须修复：")
        for e in result.errors:
            print(f"  [{e['rule']}] {e['msg']}")
        print()

    if result.warnings:
        print("⚠️  建议优化：")
        for w in result.warnings:
            print(f"  [{w['rule']}] {w['msg']}")
        print()

    if result.info:
        print("ℹ️  检查项：")
        for i in result.info:
            print(f"  [{i['rule']}] {i['msg']}")
        print()

    print("=" * 50)

    # 也输出 JSON 方便程序读取
    if '--json' in sys.argv:
        print("\n--- JSON OUTPUT ---")
        print(json.dumps(output, ensure_ascii=False, indent=2))

    sys.exit(0 if output["passed"] else 1)


if __name__ == "__main__":
    main()
