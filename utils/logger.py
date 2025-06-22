"""
디스코드 봇용 로깅 구성.
"""

import logging
import sys
from datetime import datetime
import os

def setup_logger(log_level: str = "INFO", log_file: str = "") -> logging.Logger:
    """
    봇의 로깅 구성을 설정합니다.
    
    Args:
        log_level: 로깅 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 선택적 로그 파일 경로
    
    Returns:
        구성된 로거 인스턴스
    """
    
    # 환경에서 로그 레벨 가져오거나 기본값 사용
    level = os.getenv('LOG_LEVEL', log_level).upper()
    
    # 포매터 생성
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 루트 로거 생성 및 구성
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level, logging.INFO))
    
    # 기존 핸들러 모두 제거
    logger.handlers.clear()
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러 (선택사항)
    if log_file:
        try:
            # 로그 디렉토리가 없으면 생성
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            logger.info(f"파일에 로깅: {log_file}")
            
        except Exception as e:
            logger.error(f"파일 핸들러 생성 실패: {e}")
    
    # 일부 라이브러리의 노이즈 줄이기
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('discord.http').setLevel(logging.WARNING)
    logging.getLogger('apscheduler').setLevel(logging.WARNING)
    
    logger.info("로깅 시스템 초기화됨")
    return logger

class BotLogger:
    """구조화된 로깅을 위한 컨텍스트 매니저."""
    
    def __init__(self, logger_name: str):
        self.logger = logging.getLogger(logger_name)
    
    def info(self, message: str, **kwargs):
        """선택적 컨텍스트와 함께 정보 메시지를 로깅합니다."""
        context = self._format_context(kwargs)
        self.logger.info(f"{message}{context}")
    
    def error(self, message: str, **kwargs):
        """선택적 컨텍스트와 함께 오류 메시지를 로깅합니다."""
        context = self._format_context(kwargs)
        self.logger.error(f"{message}{context}")
    
    def warning(self, message: str, **kwargs):
        """선택적 컨텍스트와 함께 경고 메시지를 로깅합니다."""
        context = self._format_context(kwargs)
        self.logger.warning(f"{message}{context}")
    
    def debug(self, message: str, **kwargs):
        """선택적 컨텍스트와 함께 디버그 메시지를 로깅합니다."""
        context = self._format_context(kwargs)
        self.logger.debug(f"{message}{context}")
    
    def _format_context(self, context: dict) -> str:
        """로깅을 위해 컨텍스트 딕셔너리를 포맷합니다."""
        if not context:
            return ""
        
        context_str = " | ".join([f"{k}={v}" for k, v in context.items()])
        return f" | {context_str}"

def log_command_usage(func):
    """명령어 사용을 로깅하는 데코레이터."""
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(__name__)
        
        # 컨텍스트 정보 추출 시도
        ctx = None
        for arg in args:
            if hasattr(arg, 'author') and hasattr(arg, 'command'):
                ctx = arg
                break
        
        if ctx:
            logger.info(
                f"명령어 사용됨: {ctx.command.name} | "
                f"사용자: {ctx.author} | "
                f"길드: {ctx.guild.name if ctx.guild else 'DM'} | "
                f"채널: #{ctx.channel.name if hasattr(ctx.channel, 'name') else 'DM'}"
            )
        
        return func(*args, **kwargs)
    
    return wrapper
