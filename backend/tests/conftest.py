import sys
from pathlib import Path

# 获取backend目录的绝对路径
backend_dir = str(Path(__file__).parent.parent.absolute())

# 将backend目录添加到Python路径
sys.path.insert(0, backend_dir)
