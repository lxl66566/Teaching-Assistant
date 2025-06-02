import math


def format_size(size_in_bytes: int) -> str:
    """将字节数转换为人类可读的格式"""
    if size_in_bytes == 0:
        return "0 B"

    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_in_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_in_bytes / p, 2)
    return f"{s} {size_name[i]}"
