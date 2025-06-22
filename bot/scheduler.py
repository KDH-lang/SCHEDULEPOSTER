"""
디스코드 봇용 메시지 스케줄링 시스템.
"""

import logging
from datetime import datetime, time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
import discord

class MessageScheduler:
    """예약 메시지 게시를 처리합니다."""
    
    def __init__(self, bot, settings):
        """스케줄러를 초기화합니다."""
        self.bot = bot
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # 시간대로 스케줄러 생성
        timezone = pytz.timezone(settings.timezone)
        self.scheduler = AsyncIOScheduler(timezone=timezone)
        
        # 예약된 작업 설정
        self._setup_scheduled_jobs()
    
    def _setup_scheduled_jobs(self):
        """월간 예약 메시지 작업을 설정합니다."""
        for channel_config in self.settings.scheduled_channels:
            channel_id = channel_config['channel_id']
            message_template = channel_config.get('message', self.settings.default_message)
            
            # 매월 20일 오전 9시에 메시지 예약
            job_id = f"monthly_message_{channel_id}"
            
            self.scheduler.add_job(
                func=self._send_scheduled_message_with_retry,
                trigger=CronTrigger(
                    day=20, hour=9, minute=0, second=0
                ),
                args=[channel_id, message_template],
                id=job_id,
                name=f"채널 {channel_id}용 월간 메시지",
                replace_existing=True
            )
            # 발송 하루 전 관리자 알림 (2번)
            for admin_id in getattr(self.settings, 'admin_ids', []):
                self.scheduler.add_job(
                    func=self._notify_admin_before_send,
                    trigger=CronTrigger(
                        day=19, hour=9, minute=0, second=0
                    ),
                    args=[admin_id, channel_id],
                    id=f"notify_admin_{admin_id}_{channel_id}",
                    name=f"{admin_id}에게 발송 전 알림",
                    replace_existing=True
                )
            
            self.logger.info(f"채널 {channel_id}용 월간 작업 예약됨")
    
    async def _send_scheduled_message(self, channel_id: int, message_template: str):
        """지정된 채널에 예약 메시지를 전송합니다."""
        try:
            channel = self.bot.get_channel(channel_id)
            
            if channel is None:
                self.logger.error(f"채널 ID {channel_id}를 찾을 수 없습니다")
                return
            
            # 현재 날짜로 메시지 포맷
            current_date = datetime.now(pytz.timezone(self.settings.timezone))
            formatted_message = message_template.format(
                date=current_date.strftime("%Y-%m-%d"),
                month=current_date.strftime("%B"),
                year=current_date.year,
                day=current_date.day
            )
            
            # 메시지 전송
            sent_message = await channel.send(formatted_message)
            
            # 스케줄 메시지 ID를 봇에 저장 (댓글 응답용)
            self.bot.schedule_message_ids.add(sent_message.id)
            
            # 채널 타입 확인 후 로그
            if hasattr(channel, 'name') and hasattr(channel, 'guild'):
                self.logger.info(f"예약 메시지 전송 성공: #{channel.name} in {channel.guild.name}")
            else:
                self.logger.info(f"예약 메시지 전송 성공: 채널 ID {channel_id}")
            
        except discord.Forbidden:
            self.logger.error(f"채널 {channel_id}에 메시지를 보낼 권한이 없습니다")
        except discord.HTTPException as e:
            self.logger.error(f"채널 {channel_id}에 메시지 전송 실패: {e}")
        except Exception as e:
            self.logger.error(f"예약 메시지 전송 중 예상치 못한 오류: {e}")
    
    async def _send_scheduled_message_with_retry(self, channel_id: int, message_template: str, max_retry: int = 3):
        """발송 실패시 재시도 및 내역 기록, 실패시 관리자 DM 알림"""
        for attempt in range(1, max_retry+1):
            try:
                await self._send_scheduled_message(channel_id, message_template)
                # 발송 성공시 내역 기록
                self.settings.add_send_log({
                    "channel_id": channel_id,
                    "message": message_template,
                    "status": "success",
                    "datetime": datetime.now().isoformat(),
                    "attempt": attempt
                })
                return
            except Exception as e:
                self.logger.error(f"메시지 발송 실패(시도 {attempt}): {e}")
                if attempt == max_retry:
                    # 실패 내역 기록
                    self.settings.add_send_log({
                        "channel_id": channel_id,
                        "message": message_template,
                        "status": "fail",
                        "datetime": datetime.now().isoformat(),
                        "error": str(e),
                        "attempt": attempt
                    })
                    # 관리자에게 DM 알림
                    await self._notify_admin_send_fail(channel_id, str(e))

    async def _notify_admin_before_send(self, admin_id: int, channel_id: int):
        """발송 하루 전 관리자에게 DM 알림"""
        user = self.bot.get_user(admin_id)
        if user:
            try:
                await user.send(f"[알림] 내일 채널 {channel_id}에 예약 메시지가 발송될 예정입니다. 수정할 내용이 있으면 오늘 중 변경해주세요.")
            except Exception as e:
                self.logger.error(f"관리자 DM 발송 실패: {e}")

    async def _notify_admin_send_fail(self, channel_id: int, error_msg: str):
        """발송 실패시 관리자에게 DM 알림"""
        for admin_id in getattr(self.settings, 'admin_ids', []):
            user = self.bot.get_user(admin_id)
            if user:
                try:
                    await user.send(f"[경고] 채널 {channel_id} 예약 메시지 발송 실패: {error_msg}")
                except Exception as e:
                    self.logger.error(f"관리자 DM 발송 실패: {e}")
    
    def start(self):
        """스케줄러를 시작합니다."""
        self.scheduler.start()
        self.logger.info("메시지 스케줄러 시작됨")
        
        # 다음 예약된 실행 시간 로그
        for job in self.scheduler.get_jobs():
            next_run = job.next_run_time
            self.logger.info(f"{job.name}의 다음 실행: {next_run}")
    
    def shutdown(self):
        """스케줄러를 종료합니다."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            self.logger.info("메시지 스케줄러 종료됨")
    
    def get_next_runs(self):
        """예정된 메시지에 대한 정보를 가져옵니다."""
        jobs_info = []
        for job in self.scheduler.get_jobs():
            channel_id = int(job.args[0])
            channel = self.bot.get_channel(channel_id)
            
            # 채널 타입 확인
            if channel and hasattr(channel, 'name'):
                channel_name = f"#{channel.name}"
            else:
                channel_name = f"채널 ID: {channel_id}"
            
            jobs_info.append({
                'channel_name': channel_name,
                'channel_id': channel_id,
                'next_run': job.next_run_time,
                'job_name': job.name
            })
        
        return jobs_info
    
    async def send_test_message(self, channel_id: int):
        """예약 메시지 시스템을 확인하기 위해 테스트 메시지를 전송합니다."""
        # 설정된 채널의 메시지를 찾거나 기본 메시지 사용
        message_template = self.settings.default_message
        for channel_config in self.settings.scheduled_channels:
            if channel_config['channel_id'] == channel_id:
                message_template = channel_config.get('message', self.settings.default_message)
                break
        
        test_message = f"🧪 **테스트 메시지**\n\n{message_template}\n\n*이것은 예약 메시지 시스템의 테스트였습니다.*"
        
        # 현재 날짜로 포맷
        current_date = datetime.now(pytz.timezone(self.settings.timezone))
        formatted_message = test_message.format(
            date=current_date.strftime("%Y-%m-%d"),
            month=current_date.strftime("%B"),
            year=current_date.year,
            day=current_date.day
        )
        
        # 테스트 메시지 직접 전송
        try:
            channel = self.bot.get_channel(channel_id)
            if channel is None:
                self.logger.error(f"채널 ID {channel_id}를 찾을 수 없습니다")
                return False
            
            # 테스트 메시지 전송
            sent_message = await channel.send(formatted_message)
            
            # 스케줄 메시지 ID를 봇에 저장 (댓글 응답용)
            self.bot.schedule_message_ids.add(sent_message.id)
            
            # 로그
            if hasattr(channel, 'name') and hasattr(channel, 'guild'):
                self.logger.info(f"테스트 메시지 전송 성공: #{channel.name} in {channel.guild.name}")
            else:
                self.logger.info(f"테스트 메시지 전송 성공: 채널 ID {channel_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"테스트 메시지 전송 중 오류: {e}")
            return False
