import logging

# import sys

# from loguru import logger

# # 步骤 1: 创建一个自定义的 InterceptHandler 类
# class InterceptHandler(logging.Handler):
#     def emit(self, record):
#         # 获取 Loguru 对应的级别名称，如果不存在则使用原始级别号
#         try:
#             level = logger.level(record.levelname).name
#         except ValueError:
#             level = record.levelno

#         # 查找原始日志消息的调用者帧，以确保 Loguru 显示正确的源文件和行号
#         frame, depth = logging.currentframe(), 0
#         while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
#             frame = frame.f_back
#             depth += 1

#         logger.opt(depth=depth, exception=record.exc_info).log(
#             level, record.getMessage()
#         )


root_logger = logging.getLogger()
# 清除可能存在的其他 handler，防止重复打印
root_logger.handlers = []
# 添加我们的自定义 InterceptHandler
# root_logger.addHandler(InterceptHandler())
# 设置根记录器的级别，确保能够捕获到 DEBUG 级别的日志
root_logger.setLevel(logging.INFO)

# agenticwrapper_logger = logging.getLogger("AgenticWrapper")
# agenticwrapper_logger.handlers = []
# agenticwrapper_logger.addHandler(InterceptHandler())
# agenticwrapper_logger.setLevel(logging.INFO)
