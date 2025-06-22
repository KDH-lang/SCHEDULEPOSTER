"""
예약 메시지 기능이 있는 디스코드 봇 구현.
"""

import discord
from discord.ext import commands
import logging
import asyncio
from datetime import datetime
import pytz

from bot.scheduler import MessageScheduler
from bot.commands import BotCommands
from config.settings import Settings
from utils.application_manager import ApplicationManager
from utils.notification_system import NotificationSystem
from utils.analytics import Analytics

class ScheduledBot(commands.Bot):
    """예약 메시지 기능이 있는 디스코드 봇."""
    
    def __init__(self, settings: Settings):
        """설정으로 봇을 초기화합니다."""
        # 인텐트 설정 (메시지 내용 읽기 권한 포함)
        intents = discord.Intents.default()
        intents.message_content = True
        
        # 봇 초기화
        super().__init__(
            command_prefix=settings.command_prefix,
            intents=intents,
            help_command=None
        )
        
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.scheduler = None
        self.schedule_message_ids = set()  # 스케줄 메시지 ID 저장
        self.application_manager = None
        self.notification_system = None
        self.analytics = None
        
    async def setup_hook(self):
        """봇이 시작될 때 호출되는 설정 훅."""
        self.logger.info("봇 설정 중...")
        
        # 스케줄러 초기화
        self.scheduler = MessageScheduler(self, self.settings)
        
        # 신청 현황/통계/알림 시스템 초기화
        self.application_manager = ApplicationManager(self.settings)
        self.analytics = Analytics(self.settings)
        self.notification_system = NotificationSystem(self, self.settings, self.application_manager)
        
        # 명령어 cog 추가
        await self.add_cog(BotCommands(self, self.settings, self.scheduler, self.application_manager, self.analytics))
        
        # 슬래시 명령어 동기화
        try:
            synced = await self.tree.sync()
            self.logger.info(f"슬래시 명령어 {len(synced)}개 동기화 완료")
        except Exception as e:
            self.logger.error(f"슬래시 명령어 동기화 실패: {e}")
        
        # 스케줄러 시작
        self.scheduler.start()
        
        # 알림 시스템 시작
        await self.notification_system.setup_notifications()
        
        self.logger.info("봇 설정 완료")
    
    async def on_ready(self):
        """봇이 성공적으로 디스코드에 연결되었을 때 호출됩니다."""
        self.logger.info(f"봇 준비 완료! {self.user}로 로그인됨")
        self.logger.info(f"봇이 {len(self.guilds)}개 서버에 있습니다")
        self.logger.info(f"명령어 접두사: '{self.settings.command_prefix}'")
        
        # 서버 정보 로그
        for guild in self.guilds:
            self.logger.info(f"서버: {guild.name} (ID: {guild.id})")
        
        # 봇 상태 설정
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="예약 메시지 대기 중"
        )
        await self.change_presence(activity=activity)
        
        # 설정된 채널들 검증
        await self._validate_channels()
    
    async def on_message(self, message):
        """메시지가 전송될 때 호출됩니다."""
        # 봇 자신의 메시지는 무시
        if message.author == self.user:
            return
        
        # 스케줄 메시지에 대한 답글인지 확인
        if hasattr(message, 'reference') and message.reference:
            if message.reference.message_id in self.schedule_message_ids:
                try:
                    # 신청 현황 기록
                    if self.application_manager:
                        # 예시: 날짜 추출은 간단히 본문 전체를 리스트로 저장
                        requested_dates = [message.content.strip()]
                        self.application_manager.add_application(
                            message_id=str(message.reference.message_id),
                            user_id=message.author.id,
                            user_name=str(message.author),
                            requested_dates=requested_dates,
                            additional_info=""
                        )
                    # 통계 기록
                    if self.analytics:
                        self.analytics.record_application({
                            'user_id': message.author.id,
                            'user_name': str(message.author),
                            'requested_dates': [message.content.strip()],
                            'applied_at': datetime.now(pytz.timezone(self.settings.timezone)).isoformat(),
                            'channel_id': message.channel.id
                        })
                    # 스케줄 신청 완료 메시지 전송
                    await message.reply("✅ **스케줄 신청이 완료되었습니다!**\n\n신청해 주셔서 감사합니다. ")
                    # 확인 이모지 반응 추가
                    await message.add_reaction("✅")
                    await message.add_reaction("📅")
                    self.logger.info(f"스케줄 신청 응답 전송됨: 사용자 {message.author}")
                except Exception as e:
                    self.logger.error(f"스케줄 신청 응답 전송 실패: {e}")
        
        # 명령어 디버깅
        if message.content.startswith(self.settings.command_prefix):
            self.logger.info(f"명령어 감지됨: '{message.content}' (작성자: {message.author}, 채널: {message.channel})")
            
        # 명령어 처리
        try:
            await self.process_commands(message)
        except Exception as e:
            self.logger.error(f"명령어 처리 중 오류: {e}")
            if message.content.startswith(self.settings.command_prefix):
                await message.reply(f"명령어 처리 중 오류가 발생했습니다: {e}")
    
    async def _validate_channels(self):
        """설정된 모든 채널에 접근 가능한지 검증합니다."""
        for channel_config in self.settings.scheduled_channels:
            channel_id = channel_config['channel_id']
            channel = self.get_channel(channel_id)
            
            if channel is None:
                self.logger.warning(f"채널 ID {channel_id}에 접근할 수 없습니다")
            else:
                # 채널 타입 확인 (텍스트 채널인지)
                if hasattr(channel, 'name') and hasattr(channel, 'guild'):
                    self.logger.info(f"채널 접근 검증 완료: #{channel.name} in {channel.guild.name}")
                else:
                    self.logger.info(f"채널 접근 검증 완료: 채널 ID {channel_id}")
    
    async def on_command_error(self, ctx, error):
        """명령어 오류를 처리합니다."""
        if isinstance(error, commands.CommandNotFound):
            return  # 알 수 없는 명령어는 무시
        
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ 이 명령어를 사용할 권한이 없습니다.")
            return
        
        if isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ 이 명령어를 실행하는 데 필요한 권한이 없습니다.")
            return
        
        self.logger.error(f"명령어 오류 {ctx.command}: {error}")
        await ctx.send("❌ 명령어 실행 중 오류가 발생했습니다.")
    
    async def close(self):
        """봇이 종료될 때 리소스를 정리합니다."""
        self.logger.info("봇 종료 중...")
        
        if self.scheduler:
            self.scheduler.shutdown()
        
        await super().close()
        self.logger.info("봇 종료 완료")
