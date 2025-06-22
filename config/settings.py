"""
디스코드 봇을 위한 설정 및 구성 관리.
"""

import json
import logging
import os
from typing import List, Dict, Any

class Settings:
    """봇 구성과 설정을 관리합니다."""
    
    def __init__(self, config_file: str = "config/config.json"):
        """구성 파일에서 설정을 로드합니다."""
        self.config_file = config_file
        self.logger = logging.getLogger(__name__)
        
        # 기본 설정
        self.command_prefix = "!"
        self.timezone = "UTC"
        self.default_message = "📅 **[이번 달 스케쥴 신청 안내]**\n\n안녕하세요! 이번 달 스케쥴 신청을 **오늘부터 5일간 (20일~25일)** 받습니다.\n\n👉 **아래 댓글로 신청해 주세요:**\n원하는 날짜와 시간을 댓글에 작성해 주시면 됩니다.\n\n✅ **신청 시 유의사항**\n- 다른 직원이 선택한 날짜를 먼저 확인해 주세요.\n- 가능한 한 **중복 없이** 날짜를 배정해 주세요.\n- 신청 마감 후에는 조정이 어려우니, **기간 내 제출** 꼭 부탁드립니다!\n\n감사합니다 🙏"
        self.scheduled_channels = []
        self.admin_ids = []  # 관리자 디스코드 사용자 ID 목록
        self.log_file = "config/send_log.json"  # 발송 내역 저장 파일
        self.send_logs = []  # 발송 내역 메모리 캐시
        
        # 구성 로드
        self._load_config()
    
    def _load_config(self):
        """JSON 파일에서 구성을 로드합니다."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 로드된 구성으로 설정 업데이트
                self.command_prefix = config.get('command_prefix', self.command_prefix)
                self.timezone = config.get('timezone', self.timezone)
                self.default_message = config.get('default_message', self.default_message)
                self.scheduled_channels = config.get('scheduled_channels', self.scheduled_channels)
                self.admin_ids = config.get('admin_ids', self.admin_ids)
                self.log_file = config.get('log_file', self.log_file)
                # 발송 내역 파일 로드
                self._load_send_logs()
                
                self.logger.info(f"{self.config_file}에서 구성 로드됨")
                self._validate_config()
            else:
                self.logger.warning(f"구성 파일 {self.config_file}을 찾을 수 없습니다. 기본값 사용")
                self._create_default_config()
                
        except json.JSONDecodeError as e:
            self.logger.error(f"구성 파일의 JSON이 잘못됨: {e}")
            raise
        except Exception as e:
            self.logger.error(f"구성 로드 오류: {e}")
            raise
    
    def _validate_config(self):
        """로드된 구성을 검증합니다."""
        # 예약된 채널 검증
        for i, channel_config in enumerate(self.scheduled_channels):
            if not isinstance(channel_config, dict):
                raise ValueError(f"인덱스 {i}의 채널 구성이 잘못됨")
            
            if 'channel_id' not in channel_config:
                raise ValueError(f"인덱스 {i}의 채널 구성에 'channel_id'가 누락됨")
            
            if not isinstance(channel_config['channel_id'], int):
                raise ValueError(f"인덱스 {i}에서 'channel_id'는 정수여야 함")
        
        self.logger.info("구성 검증 통과")
    
    def _create_default_config(self):
        """기본 구성 파일을 생성합니다."""
        default_config = {
            "command_prefix": self.command_prefix,
            "timezone": self.timezone,
            "default_message": self.default_message,
            "scheduled_channels": [
                {
                    "channel_id": 0,
                    "message": "📅 월간 알림: {month} {year}의 예약 메시지입니다!",
                    "description": "0을 실제 채널 ID로 교체하세요"
                }
            ]
        }
        
        # 구성 디렉토리가 없으면 생성
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            
            self.logger.info(f"기본 구성 파일 생성됨: {self.config_file}")
            self.logger.info("구성 파일을 편집하고 봇을 다시 시작해주세요")
            
        except Exception as e:
            self.logger.error(f"기본 구성 파일 생성 실패: {e}")
    
    def save_config(self):
        """현재 설정을 구성 파일에 저장합니다."""
        config = {
            "command_prefix": self.command_prefix,
            "timezone": self.timezone,
            "default_message": self.default_message,
            "scheduled_channels": self.scheduled_channels,
            "admin_ids": self.admin_ids,
            "log_file": self.log_file,
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            self.logger.info("구성 저장 성공")
            
        except Exception as e:
            self.logger.error(f"구성 저장 실패: {e}")
            raise
    
    def _load_send_logs(self):
        """발송 내역 파일을 로드합니다."""
        import json
        import os
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    self.send_logs = json.load(f)
            except Exception:
                self.send_logs = []
        else:
            self.send_logs = []

    def add_send_log(self, log_entry: dict):
        """발송 내역을 추가하고 파일에 저장합니다."""
        self.send_logs.append(log_entry)
        import json
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(self.send_logs, f, ensure_ascii=False, indent=2)

    def get_send_logs(self, limit=10):
        """최근 발송 내역을 반환합니다."""
        return self.send_logs[-limit:]
    
    def add_scheduled_channel(self, channel_id: int, message: str = ""):
        """새로운 예약 채널을 추가합니다."""
        # 채널이 이미 존재하는지 확인
        for channel_config in self.scheduled_channels:
            if channel_config['channel_id'] == channel_id:
                self.logger.warning(f"채널 {channel_id}은 이미 구성됨")
                return False
        
        # 새 채널 추가
        new_channel = {
            "channel_id": channel_id,
            "message": message if message else self.default_message
        }
        
        self.scheduled_channels.append(new_channel)
        self.save_config()
        
        self.logger.info(f"예약 채널 추가됨: {channel_id}")
        return True
    
    def remove_scheduled_channel(self, channel_id: int):
        """예약 채널을 제거합니다."""
        for i, channel_config in enumerate(self.scheduled_channels):
            if channel_config['channel_id'] == channel_id:
                del self.scheduled_channels[i]
                self.save_config()
                self.logger.info(f"예약 채널 제거됨: {channel_id}")
                return True
        
        self.logger.warning(f"채널 {channel_id}을 구성에서 찾을 수 없음")
        return False
