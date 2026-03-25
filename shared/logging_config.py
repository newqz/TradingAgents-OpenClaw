# -*- coding: utf-8 -*-
"""
日志配置模块
统一的日志系统
"""

import logging
import sys
from datetime import datetime
from typing import Optional


# 日志格式
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 日志级别环境变量
LOG_LEVEL = "INFO"


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(
    name: str = "tradingagents",
    level: str = "INFO",
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    设置日志系统
    
    Args:
        name: 日志记录器名称
        level: 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
        log_file: 可选的文件处理器
        
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 控制台处理器 (彩色)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = ColoredFormatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器 (如果指定)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称 (通常用 __name__)
        
    Returns:
        日志记录器
    """
    return logging.getLogger(f"tradingagents.{name}")


# 便捷函数
def debug(message: str, name: str = "root"):
    get_logger(name).debug(message)

def info(message: str, name: str = "root"):
    get_logger(name).info(message)

def warning(message: str, name: str = "root"):
    get_logger(name).warning(message)

def error(message: str, name: str = "root"):
    get_logger(name).error(message)

def critical(message: str, name: str = "root"):
    get_logger(name).critical(message)
