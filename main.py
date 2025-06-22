#!/usr/bin/env python3
"""
디스코드 예약 메시지 봇
봇 애플리케이션의 메인 진입점입니다.
"""

import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

from bot.discord_bot import ScheduledBot
from utils.logger import setup_logger
from config.settings import Settings

def main():
    """디스코드 봇을 시작하는 메인 함수입니다."""
    # 환경 변수 로드
    load_dotenv()
    
    # 로깅 설정
    logger = setup_logger()
    
    # 환경 변수에서 디스코드 봇 토큰 가져오기
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        logger.error("DISCORD_BOT_TOKEN 환경 변수가 필요합니다!")
        logger.error(".env 파일에 디스코드 봇 토큰을 설정해주세요")
        sys.exit(1)
    
    # 설정 로드
    try:
        settings = Settings()
        logger.info("설정이 성공적으로 로드되었습니다")
    except Exception as e:
        logger.error(f"설정 로드 실패: {e}")
        sys.exit(1)
    
    # 봇 생성 및 실행
    try:
        bot = ScheduledBot(settings)
        logger.info("디스코드 봇 시작 중...")
        bot.run(token)
    except KeyboardInterrupt:
        logger.info("사용자에 의해 봇이 중지되었습니다")
    except Exception as e:
        logger.error(f"봇 실행 중 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
