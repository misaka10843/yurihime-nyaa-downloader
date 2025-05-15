import re
import logging
from pathlib import Path
from natsort import natsorted
import shutil
from cbz.comic import ComicInfo
from cbz.constants import PageType, YesNo, Manga, AgeRating, Format
from cbz.page import PageInfo

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def parse_folder_name(folder_name):
    """解析文件夹名称返回元数据"""
    # 匹配 "YYYY年MM月号" 或 "YYYY年M月号" 格式
    match = re.match(
        r"^コミック百合姫\s+(\d{4})年(\d{1,2})月号$",
        folder_name.strip()
    )

    if not match:
        log.error(f"无效的文件夹格式: {folder_name}")
        raise ValueError(f"无效的文件夹格式: {folder_name}")

    year, month = match.groups()

    # 格式化月份补零
    formatted_month = f"{int(month):02d}"
    chapter_number = f"{year}{formatted_month}"
    title = f"コミック百合姫 {year}年{formatted_month}月号"
    series_name = "コミック百合姫"

    return {
        "chapter_number": chapter_number,
        "title": title,
        "series_name": series_name
    }


def process_directory(source_dir: Path, specials=False):
    """处理单个目录"""
    try:
        # 验证目录有效性
        if not source_dir.is_dir():
            log.error(f"无效目录: {source_dir}")
            raise ValueError(f"无效目录: {source_dir}")

        # 获取并排序文件列表（自然排序）
        paths = natsorted(source_dir.iterdir(), key=lambda x: x.name)
        if not paths:
            log.error(f"没有在 {source_dir} 中找到图片")
            raise RuntimeError(f"没有在 {source_dir} 中找到图片")

        # 构建页面信息
        pages = [
            PageInfo.load(
                path=path,
                type=PageType.FRONT_COVER if i == 0 else
                PageType.BACK_COVER if i == len(paths) - 1 else
                PageType.STORY
            )
            for i, path in enumerate(paths)
        ]

        # 解析元数据
        meta = parse_folder_name(source_dir.name)

        # 构建漫画元数据
        comic = ComicInfo.from_pages(
            pages=pages,
            title=meta["title"],
            series=meta["series_name"],
            number=meta["chapter_number"],
            language_iso='zh',
            format=Format.WEB_COMIC,
            black_white=YesNo.NO,
            manga=Manga.YES,
            age_rating=AgeRating.PENDING
        )

        # 构建输出路径
        base_dir = Path("./cbz") / meta["series_name"]
        if specials:
            base_dir /= "Specials"

        # 确保目录存在
        base_dir.mkdir(parents=True, exist_ok=True)
        cbz_path = base_dir / f"{meta['chapter_number']}.cbz"

        # 打包并清理
        cbz_path.write_bytes(comic.pack())
        log.info(f"CBZ打包成功: {cbz_path}")
        # shutil.rmtree(source_dir, ignore_errors=True)
        log.info(f"图片删除成功: {source_dir}")

    except Exception as e:
        log.error(f"处理目录失败: {source_dir} - {str(e)}")
        raise


def process_all_directories(root_dir: str):
    """处理根目录下的所有子目录"""
    root_path = Path(root_dir)

    if not root_path.exists():
        log.error(f"根目录不存在: {root_dir}")
        return

    for child in root_path.iterdir():
        if child.is_dir():
            log.info(f"开始处理目录: {child.name}")
            try:
                process_directory(child)
                log.info(f"完成处理: {child.name}")
            except:
                log.error(f"跳过处理失败目录: {child.name}")
                continue


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("使用方法: python package.py <根目录>")
        sys.exit(1)

    process_all_directories(sys.argv[1])