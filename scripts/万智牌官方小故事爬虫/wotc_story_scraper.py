"""wotc_story_scraper.py
====================================

本模块以教学示范的方式实现万智牌官网《斯翠海文》故事的定向抓取。
需求核心：
1. 固定抓取 10 篇英文故事，并在页面存在简体中文版时同步抓取；
2. 利用 `trafilatura` 提取 Markdown 正文，确保文本结构清晰；
3. 下载正文中引用的所有图片到本地 `assets` 目录，Markdown 中改写为相对路径；
4. 将抓取过程拆分为可复用的函数与类，边界处理独立封装，配合详尽中文注释帮助初学者理解。

运行示例：
    python wotc_story_scraper.py --sleep 1.2

输出目录结构：
    scripts/万智牌官方小故事爬虫/output/<slug>/<语言代码>.md
    scripts/万智牌官方小故事爬虫/assets/<slug>/<编号_图片描述>.jpg

注意事项：
    - 默认以英文站点为基础，当检测到 zh-Hans 页面可用时才会额外抓取；
    - 如遇请求失败或限速，脚本会记录错误并继续后续任务；
    - 可通过 CLI 参数调整请求间隔与输出路径。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import httpx
from lxml import html as lxml_html

# ---- 第三方正文提取：优先使用 trafilatura，若缺失则降级为 markdownify ----
try:  # pragma: no cover - 依赖是否安装取决于运行环境
    import trafilatura  # type: ignore

    HAVE_TRAF = True
except Exception:  # pragma: no cover - 降级分支主要用于教学演示
    HAVE_TRAF = False
    from markdownify import markdownify as md  # type: ignore


# ===============================
# 常量与基础数据
# ===============================

# 官方提供的十篇斯翠海文故事（英文原文链接）
TARGET_ARTICLES: Tuple[str, ...] = (
    "https://magic.wizards.com/en/news/magic-story/episode-1-class-session-2021-03-25",
    "https://magic.wizards.com/en/news/magic-story/cry-magic-2021-03-26",
    "https://magic.wizards.com/en/news/magic-story/episode-2-lessons-2021-03-31",
    "https://magic.wizards.com/en/news/magic-story/episode-3-extracurriculars-2021-04-07",
    "https://magic.wizards.com/en/news/magic-story/chains-bind-2021-04-09",
    "https://magic.wizards.com/en/news/magic-story/episode-4-put-test-2021-04-14",
    "https://magic.wizards.com/en/news/magic-story/mentor-2021-04-16",
    "https://magic.wizards.com/en/news/magic-story/episode-5-final-exam-2021-04-21",
    "https://magic.wizards.com/en/news/magic-story/blue-green-ribbons-2021-04-23",
    "https://magic.wizards.com/en/news/magic-story/silent-voice-calls-2021-04-30",
)

# 站点通用请求头：通过语言分支调整 Accept-Language
BASE_HEADERS: Dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}

# 用于识别图片 Markdown 的正则表达式
MD_IMAGE_PATTERN = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<src>[^)]+)\)")


# ===============================
# 数据结构定义
# ===============================


@dataclass
class ArticleMeta:
    """封装单篇文章的元信息，便于后续写入 Front Matter。"""

    title: str
    author: str
    published: str
    source_url: str
    language: str


@dataclass
class DownloadResult:
    """记录单次语言抓取的落盘信息，用于返回执行结果。"""

    meta: ArticleMeta
    markdown_path: Path
    assets: List[Path]
    warnings: List[str]


# ===============================
# 基础工具函数
# ===============================


def sanitize_filename(name: str, fallback: str = "untitled") -> str:
    """将标题/描述转换为安全的文件名片段，避免跨平台非法字符。"""

    cleaned = re.sub(r"[\\/:*?\"<>|]+", "_", name).strip()
    return cleaned or fallback


def derive_slug(source_url: str) -> str:
    """从故事 URL 中提取末段 slug，用作目录名。"""

    parsed = urlparse(source_url)
    slug = Path(parsed.path).name
    return sanitize_filename(slug)


def build_headers(language_code: str) -> Dict[str, str]:
    """根据语言代码生成请求头，帮助服务器返回期望语言版本。"""

    headers = dict(BASE_HEADERS)
    # Accept-Language 需要兼顾首选语言与英文备选，避免 406
    if language_code.lower().startswith("zh"):
        headers["Accept-Language"] = "zh-CN,zh;q=0.9,en;q=0.6"
    else:
        headers["Accept-Language"] = "en-US,en;q=0.8"
    return headers


def fetch_html(
    client: httpx.Client,
    url: str,
    language_code: str,
    max_retries: int = 3,
    sleep_seconds: float = 1.0,
) -> Tuple[Optional[str], List[str]]:
    """带简单重试的 HTML 抓取，返回页面文本与告警列表。"""

    warnings: List[str] = []
    headers = build_headers(language_code)
    for attempt in range(1, max_retries + 1):
        try:
            response = client.get(url, headers=headers, follow_redirects=True, timeout=30)
            if response.status_code == 200 and response.text:
                return response.text, warnings
            warnings.append(
                f"HTTP {response.status_code}：{url} (尝试 {attempt}/{max_retries})"
            )
        except httpx.HTTPError as exc:  # 网络或超时异常
            warnings.append(
                f"请求异常：{exc} (尝试 {attempt}/{max_retries})"
            )
        time.sleep(sleep_seconds)
    return None, warnings


def parse_html_tree(html_text: str) -> lxml_html.HtmlElement:
    """将 HTML 字符串解析为 lxml DOM，以便后续 XPath 操作。"""

    return lxml_html.fromstring(html_text)


def extract_article_meta(tree: lxml_html.HtmlElement, language_code: str, source_url: str) -> ArticleMeta:
    """从 JSON-LD 脚本中提取标题、作者与发布时间。"""

    title = ""
    author = ""
    published = ""
    for node in tree.xpath('//script[@type="application/ld+json"]/text()'):
        try:
            data = json.loads(node)
        except json.JSONDecodeError:
            continue
        if isinstance(data, list):
            candidates: Iterable[dict] = [item for item in data if isinstance(item, dict)]
        elif isinstance(data, dict):
            candidates = [data]
        else:
            continue
        for item in candidates:
            if item.get("@type") not in {"Article", "NewsArticle"}:
                continue
            title = item.get("headline") or title
            published = item.get("datePublished") or published
            author_data = item.get("author")
            if isinstance(author_data, list):
                names = [a.get("name") for a in author_data if isinstance(a, dict)]
                author = ", ".join(filter(None, names)) or author
            elif isinstance(author_data, dict):
                author = author_data.get("name", author)
    # 兜底：若 JSON-LD 缺失，回退到 <h1> 与页面辅助信息
    if not title:
        title = (tree.xpath("string(//h1)") or "").strip()
    if not author:
        author = (tree.xpath('string(//*[@data-testid="byline-name"])') or "").strip()
    if not published:
        published = (
            tree.xpath('string(//*[@data-testid="publish-date"])') or ""
        ).strip()
    return ArticleMeta(
        title=title or "未命名文章",
        author=author or "未知作者",
        published=published,
        source_url=source_url,
        language=language_code,
    )


def extract_language_variants(
    tree: lxml_html.HtmlElement,
    base_url: str,
) -> Dict[str, str]:
    """解析 <link rel="alternate"> 列表，构建语言代码到 URL 的映射。"""

    variants: Dict[str, str] = {}
    for link in tree.xpath('//link[@rel="alternate"][@hreflang]'):
        lang = link.get("hreflang", "").strip()
        href = link.get("href", "").strip()
        if not lang or not href:
            continue
        variants[lang.lower()] = urljoin(base_url, href)
    return variants


def html_to_markdown(html_text: str, source_url: str) -> str:
    """将整页 HTML 转换为 Markdown，用于写入最终文件。"""

    if HAVE_TRAF:
        result = trafilatura.extract(  # type: ignore[arg-type]
            html_text,
            include_links=True,
            include_formatting=True,
            output_format="markdown",
            url=source_url,
        )
        if result:
            return result

    # 降级：使用 lxml 选出主体标签，再走 markdownify
    tree = parse_html_tree(html_text)
    node = tree.xpath('//article | //main | //*[@data-component="Article"]')
    html_fragment = "".join(
        lxml_html.tostring(item, encoding="unicode") for item in (node or [tree])
    )
    return md(html_fragment)


def collect_images(
    tree: lxml_html.HtmlElement,
    base_url: str,
) -> List[Tuple[str, str]]:
    """提取文章主体中的图片 URL 与 alt 文本。"""

    results: List[Tuple[str, str]] = []
    for img in tree.xpath('//article//img | //main//img'):
        src = img.get("src") or img.get("data-src") or ""
        if not src:
            continue
        full_url = urljoin(base_url, src)
        alt_text = (img.get("alt") or "").strip()
        results.append((full_url, alt_text))
    return results


def rewrite_markdown_images(
    markdown_text: str,
    replacement_map: Dict[str, str],
) -> str:
    """将 Markdown 中的远程图片 URL 替换为本地相对路径。"""

    def _replace(match: re.Match[str]) -> str:
        src = match.group("src")
        alt = match.group("alt")
        new_src = replacement_map.get(src, src)
        return f"![{alt}]({new_src})"

    return MD_IMAGE_PATTERN.sub(_replace, markdown_text)


# ===============================
# 资源下载与管理
# ===============================


class AssetManager:
    """统一管理图片落盘，避免重复下载并生成相对路径。"""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.cache: Dict[str, Dict[str, Path]] = {}

    def ensure_download(
        self,
        client: httpx.Client,
        slug: str,
        remote_url: str,
        alt_text: str,
        index: int,
    ) -> Tuple[Optional[Path], Optional[str]]:
        """下载图片并返回文件路径；若已缓存则直接复用。"""

        slug_cache = self.cache.setdefault(slug, {})
        if remote_url in slug_cache:
            return slug_cache[remote_url], None

        slug_dir = self.base_dir / slug
        slug_dir.mkdir(parents=True, exist_ok=True)

        parsed = urlparse(remote_url)
        ext = Path(parsed.path).suffix or ".jpg"
        safe_alt = sanitize_filename(alt_text, fallback=f"image-{index:02d}")
        candidate = slug_dir / f"{index:02d}_{safe_alt}{ext}"
        suffix_counter = 1
        while candidate.exists():
            candidate = slug_dir / f"{index:02d}_{safe_alt}_{suffix_counter}{ext}"
            suffix_counter += 1

        try:
            with client.stream("GET", remote_url, headers=BASE_HEADERS, timeout=30) as resp:
                resp.raise_for_status()
                with candidate.open("wb") as fh:
                    for chunk in resp.iter_bytes():
                        fh.write(chunk)
        except httpx.HTTPError as exc:
            return None, f"图片下载失败：{remote_url} -> {exc}"

        slug_cache[remote_url] = candidate
        return candidate, None


# ===============================
# 主要抓取流程封装
# ===============================


class StoryScraper:
    """面向初学者的抓取流程封装类，负责组织任务与输出结果。"""

    def __init__(
        self,
        output_root: Path,
        asset_root: Path,
        sleep_seconds: float,
    ) -> None:
        self.output_root = output_root
        self.asset_root = asset_root
        self.sleep_seconds = sleep_seconds
        self.asset_manager = AssetManager(asset_root)

    def scrape_article(self, client: httpx.Client, url: str) -> List[DownloadResult]:
        """抓取单篇英文页面，并尝试下载可用的多语言版本。"""

        slug = derive_slug(url)
        results: List[DownloadResult] = []

        # 先抓英文原文
        en_html, en_warnings = fetch_html(client, url, "en", sleep_seconds=self.sleep_seconds)
        if not en_html:
            print(f"[x] 无法获取英文原文：{url}")
            return []

        # 解析 HTML 一次即可复用节点树
        en_tree = parse_html_tree(en_html)
        variants = extract_language_variants(en_tree, url)

        # 组织需要抓取的语言：英文永远保留，中文若可用则追加
        language_plan: List[Tuple[str, str, Optional[lxml_html.HtmlElement], Optional[str], List[str]]]
        language_plan = [("en", url, en_tree, en_html, en_warnings)]

        zh_url = variants.get("zh") or variants.get("zh-cn") or variants.get("zh-hans")
        if zh_url:
            language_plan.append(("zh-Hans", zh_url, None, None, []))

        for lang_code, lang_url, cached_tree, cached_html, warnings in language_plan:
            if cached_html is None:
                html_text, new_warnings = fetch_html(
                    client, lang_url, lang_code, sleep_seconds=self.sleep_seconds
                )
                warnings.extend(new_warnings)
                if not html_text:
                    warnings.append(f"多语言页面不可用：{lang_code} -> {lang_url}")
                    markdown_dir = self.output_root / slug
                    markdown_dir.mkdir(parents=True, exist_ok=True)
                    expected_path = markdown_dir / f"{lang_code}.md"
                    results.append(
                        DownloadResult(
                            meta=ArticleMeta(
                                title="抓取失败",
                                author="",
                                published="",
                                source_url=lang_url,
                                language=lang_code,
                            ),
                            markdown_path=expected_path,
                            assets=[],
                            warnings=warnings,
                        )
                    )
                    continue
                cached_html = html_text
                cached_tree = parse_html_tree(html_text)

            assert cached_tree is not None
            assert cached_html is not None

            meta = extract_article_meta(cached_tree, lang_code, lang_url)
            markdown = html_to_markdown(cached_html, lang_url)

            # 图片收集与下载
            images = collect_images(cached_tree, lang_url)
            replacement_map: Dict[str, str] = {}
            assets: List[Path] = []
            markdown_dir = self.output_root / slug
            markdown_dir.mkdir(parents=True, exist_ok=True)

            for idx, (img_url, alt) in enumerate(images, start=1):
                local_path, warn = self.asset_manager.ensure_download(
                    client,
                    slug,
                    img_url,
                    alt,
                    index=idx,
                )
                if warn:
                    warnings.append(warn)
                    continue
                if local_path is None:
                    continue
                assets.append(local_path)
                relative_path = Path(os.path.relpath(local_path, markdown_dir))
                replacement_map[img_url] = relative_path.as_posix()

            markdown = rewrite_markdown_images(markdown, replacement_map)

            # 写入 Markdown 文件，包含 Front Matter 与提示语
            markdown_path = markdown_dir / f"{lang_code}.md"
            front_matter = [
                "---",
                f'title: "{meta.title}"',
                f"author: {meta.author}",
                f"published: {meta.published}",
                f"source: {meta.source_url}",
                f"language: {meta.language}",
                "tags: [Strixhaven, Magic Story]",
                "---",
                "",
                "_注：非盈利同人整理，遵循威世智粉丝内容政策，仅供教学与跑团使用。_",
                "",
            ]
            markdown_path.write_text("\n".join(front_matter) + markdown, encoding="utf-8")

            result = DownloadResult(
                meta=meta,
                markdown_path=markdown_path,
                assets=assets,
                warnings=warnings,
            )
            results.append(result)

        return results

    def run(self, limit: Optional[int] = None) -> List[DownloadResult]:
        """遍历目标文章列表并收集所有抓取结果。"""

        all_results: List[DownloadResult] = []
        self.output_root.mkdir(parents=True, exist_ok=True)
        self.asset_root.mkdir(parents=True, exist_ok=True)

        with httpx.Client(follow_redirects=True) as client:
            for idx, url in enumerate(TARGET_ARTICLES, start=1):
                if limit is not None and idx > limit:
                    break
                print(f"[>] ({idx}/{len(TARGET_ARTICLES)}) 处理 {url}")
                results = self.scrape_article(client, url)
                all_results.extend(results)
                time.sleep(self.sleep_seconds)
        return all_results


# ===============================
# CLI 入口：解析参数并执行
# ===============================


def parse_args() -> argparse.Namespace:
    """命令行参数解析，允许自定义输出路径与请求间隔。"""

    parser = argparse.ArgumentParser(
        description="抓取万智牌斯翠海文官方故事（英文必抓，中文可选）。",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "output",
        help="Markdown 输出目录根路径。",
    )
    parser.add_argument(
        "--assets",
        type=Path,
        default=Path(__file__).resolve().parent / "assets",
        help="图片资源保存根目录。",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=1.0,
        help="每次请求后的等待秒数，帮助避开限速。",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="可选：仅抓取前 N 篇，便于调试。",
    )
    return parser.parse_args()


def main() -> None:
    """程序主入口：初始化抓取器并输出执行摘要。"""

    args = parse_args()
    scraper = StoryScraper(args.output, args.assets, args.sleep)
    results = scraper.run(limit=args.limit)

    print("\n[summary] 抓取完成，结果概览：")
    for item in results:
        status = "OK" if item.markdown_path.is_file() else "FAIL"
        markdown_display = (
            item.markdown_path if item.markdown_path.is_file() else "N/A"
        )
        print(
            f"  - {item.meta.language} | {item.meta.title} | {status} | "
            f"Markdown: {markdown_display}"
        )
        for warning in item.warnings:
            print(f"      ! {warning}")


if __name__ == "__main__":
    main()
