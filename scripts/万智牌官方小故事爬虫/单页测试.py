"""单页测试脚本
=================

用途：
    - 作为最小可运行示例，仅抓取列表中第一篇故事；
    - 演示 `StoryScraper` 的基础调用方式；
    - 方便在教学过程中快速验证环境依赖是否就绪。

运行：
    python 单页测试.py --output ./debug_output --assets ./debug_assets

提示：
    若要抓取全部故事，请使用主脚本 `wotc_story_scraper.py`。
"""

from __future__ import annotations

import argparse
from pathlib import Path

from wotc_story_scraper import StoryScraper, TARGET_ARTICLES


def parse_args() -> argparse.Namespace:
    """解析最小示例所需的输出目录参数。"""

    parser = argparse.ArgumentParser(description="单篇抓取调试入口")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "debug_output",
        help="Markdown 输出目录，默认写入 scripts/…/debug_output",
    )
    parser.add_argument(
        "--assets",
        type=Path,
        default=Path(__file__).resolve().parent / "debug_assets",
        help="图片资源目录，默认写入 scripts/…/debug_assets",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.5,
        help="请求后的等待秒数，默认 0.5s 便于快速体验",
    )
    return parser.parse_args()


def main() -> None:
    """抓取目标列表首篇文章，输出执行结果摘要。"""

    args = parse_args()
    scraper = StoryScraper(args.output, args.assets, args.sleep)
    # 仅抓取第一条，演示返回结构
    first_url = TARGET_ARTICLES[0]
    print(f"[demo] 抓取示例地址：{first_url}")
    results = scraper.run(limit=1)
    for item in results:
        status = "OK" if item.markdown_path.exists() else "FAIL"
        print(
            f"  - {item.meta.language} | {item.meta.title} | {status} | "
            f"Markdown: {item.markdown_path if item.markdown_path else 'N/A'}"
        )
        for warning in item.warnings:
            print(f"      ! {warning}")


if __name__ == "__main__":
    main()
