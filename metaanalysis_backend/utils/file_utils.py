import os
from datetime import datetime


def get_upload_dir(user_id: int) -> str:
    """获取用户专属上传目录"""
    dir_path = os.path.join("uploads", str(user_id))
    os.makedirs(dir_path, exist_ok=True)
    return dir_path


def generate_filepath(user_id: int, filename: str) -> str:
    """生成唯一文件路径，避免重名"""
    upload_dir = get_upload_dir(user_id)
    name, ext = os.path.splitext(filename)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    new_filename = f"{name}_{timestamp}{ext}"
    return os.path.join(upload_dir, new_filename)


def get_file_size(file_path: str) -> int:
    """获取文件大小（字节）"""
    if os.path.exists(file_path):
        return os.path.getsize(file_path)
    return 0
