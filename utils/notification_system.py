"""
고급 알림 시스템.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import pytz
import discord

class NotificationSystem:
    """고급 알림 시스템을 관리합니다."""
    
    def __init__(self, bot, settings, application_manager):
        """알림 시스템을 초기화합니다."""
        self.bot = bot
        self.settings = settings
        self.application_manager = application_manager
        self.logger = logging.getLogger(__name__)
        
        # 알림 설정
        self.notification_settings = {
            'deadline_reminder_hours': [24, 12, 6, 1],  # 마감 전 알림 시간 (시간)
            'low_participation_threshold': 3,  # 낮은 참여 기준 (명)
            'high_conflict_threshold': 3,  # 높은 충돌 기준 (명)
            'daily_report_time': '18:00',  # 일일 보고 시간
            'weekly_report_day': 'monday',  # 주간 보고 요일
            'weekly_report_time': '09:00'   # 주간 보고 시간
        }
        
        # 알림 작업 저장
        self.notification_tasks = {}
    
    async def setup_notifications(self):
        """알림 시스템을 설정합니다."""
        # 정기적인 알림 작업 설정
        await self._setup_deadline_reminders()
        await self._setup_daily_reports()
        await self._setup_weekly_reports()
        
        self.logger.info("알림 시스템 설정 완료")
    
    async def _setup_deadline_reminders(self):
        """마감일 알림을 설정합니다."""
        for hours in self.notification_settings['deadline_reminder_hours']:
            # 매일 특정 시간에 마감일이 임박한 신청 확인
            task = asyncio.create_task(self._check_deadline_reminders(hours))
            self.notification_tasks[f'deadline_reminder_{hours}h'] = task
    
    async def _setup_daily_reports(self):
        """일일 보고 알림을 설정합니다."""
        task = asyncio.create_task(self._daily_report_scheduler())
        self.notification_tasks['daily_report'] = task
    
    async def _setup_weekly_reports(self):
        """주간 보고 알림을 설정합니다."""
        task = asyncio.create_task(self._weekly_report_scheduler())
        self.notification_tasks['weekly_report'] = task
    
    async def _check_deadline_reminders(self, hours_before: int):
        """마감일이 임박한 신청에 대한 알림을 확인합니다."""
        while True:
            try:
                current_time = datetime.now(pytz.timezone(self.settings.timezone))
                deadline_threshold = current_time + timedelta(hours=hours_before)
                
                active_sessions = self.application_manager.get_active_sessions()
                
                for session in active_sessions:
                    deadline = datetime.fromisoformat(session['deadline'])
                    
                    # 마감일이 임박한 경우 알림
                    if deadline <= deadline_threshold and deadline > current_time:
                        await self._send_deadline_reminder(session, hours_before)
                
                # 1시간마다 확인
                await asyncio.sleep(3600)
                
            except Exception as e:
                self.logger.error(f"마감일 알림 확인 중 오류: {e}")
                await asyncio.sleep(3600)
    
    async def _send_deadline_reminder(self, session: Dict, hours_before: int):
        """마감일 임박 알림을 전송합니다."""
        try:
            channel = self.bot.get_channel(session['channel_id'])
            if not channel:
                return
            
            summary = session['summary']
            total_applications = summary['total_applications']
            
            embed = discord.Embed(
                title=f"⏰ 스케줄 신청 마감 {hours_before}시간 전",
                description=f"현재까지 **{total_applications}명**이 신청했습니다.",
                color=discord.Color.orange()
            )
            
            if summary['popular_dates']:
                embed.add_field(
                    name="🔥 인기 날짜",
                    value="\n".join([f"• {date} ({summary['date_counts'][date]}명 신청)" 
                                    for date in summary['popular_dates'][:5]]),
                    inline=False
                )
            
            embed.add_field(
                name="📅 마감일",
                value=f"<t:{int(datetime.fromisoformat(session['deadline']).timestamp())}:R>",
                inline=False
            )
            
            embed.set_footer(text="아직 신청하지 않으셨다면 서둘러 신청해주세요!")
            
            await channel.send(embed=embed)
            
            # 관리자에게도 알림
            await self._notify_admins_deadline_reminder(session, hours_before)
            
        except Exception as e:
            self.logger.error(f"마감일 알림 전송 실패: {e}")
    
    async def _notify_admins_deadline_reminder(self, session: Dict, hours_before: int):
        """관리자에게 마감일 임박 알림을 전송합니다."""
        for admin_id in self.settings.admin_ids:
            try:
                user = self.bot.get_user(admin_id)
                if user:
                    summary = session['summary']
                    channel = self.bot.get_channel(session['channel_id'])
                    channel_name = channel.name if channel else f"채널 {session['channel_id']}"
                    
                    message = (
                        f"🔔 **마감일 임박 알림**\n\n"
                        f"채널: #{channel_name}\n"
                        f"마감까지: {hours_before}시간\n"
                        f"현재 신청: {summary['total_applications']}명\n"
                        f"고유 신청자: {summary['unique_applicants']}명"
                    )
                    
                    if summary['popular_dates']:
                        message += f"\n\n🔥 인기 날짜:\n"
                        for date in summary['popular_dates'][:3]:
                            count = summary['date_counts'][date]
                            message += f"• {date}: {count}명\n"
                    
                    await user.send(message)
                    
            except Exception as e:
                self.logger.error(f"관리자 마감일 알림 전송 실패 (ID: {admin_id}): {e}")
    
    async def _daily_report_scheduler(self):
        """일일 보고 스케줄러를 실행합니다."""
        while True:
            try:
                current_time = datetime.now(pytz.timezone(self.settings.timezone))
                report_time = datetime.strptime(self.notification_settings['daily_report_time'], '%H:%M').time()
                
                # 다음 보고 시간까지 대기
                next_report = current_time.replace(
                    hour=report_time.hour, 
                    minute=report_time.minute, 
                    second=0, 
                    microsecond=0
                )
                
                if current_time.time() >= report_time:
                    next_report += timedelta(days=1)
                
                wait_seconds = (next_report - current_time).total_seconds()
                await asyncio.sleep(wait_seconds)
                
                # 일일 보고 전송
                await self._send_daily_report()
                
            except Exception as e:
                self.logger.error(f"일일 보고 스케줄러 오류: {e}")
                await asyncio.sleep(3600)
    
    async def _send_daily_report(self):
        """일일 보고를 전송합니다."""
        try:
            active_sessions = self.application_manager.get_active_sessions()
            
            if not active_sessions:
                return
            
            for admin_id in self.settings.admin_ids:
                try:
                    user = self.bot.get_user(admin_id)
                    if not user:
                        continue
                    
                    embed = discord.Embed(
                        title="📊 일일 스케줄 신청 현황 보고",
                        description=f"현재 활성 신청 세션: {len(active_sessions)}개",
                        color=discord.Color.blue()
                    )
                    
                    for session in active_sessions:
                        summary = session['summary']
                        channel = self.bot.get_channel(session['channel_id'])
                        channel_name = channel.name if channel else f"채널 {session['channel_id']}"
                        
                        # 참여도 평가
                        participation_level = "🟢 높음" if summary['total_applications'] >= 5 else \
                                           "🟡 보통" if summary['total_applications'] >= 3 else "🔴 낮음"
                        
                        embed.add_field(
                            name=f"#{channel_name}",
                            value=(
                                f"신청: {summary['total_applications']}명\n"
                                f"참여도: {participation_level}\n"
                                f"마감: <t:{int(datetime.fromisoformat(session['deadline']).timestamp())}:R>"
                            ),
                            inline=True
                        )
                    
                    await user.send(embed=embed)
                    
                except Exception as e:
                    self.logger.error(f"관리자 일일 보고 전송 실패 (ID: {admin_id}): {e}")
                    
        except Exception as e:
            self.logger.error(f"일일 보고 전송 실패: {e}")
    
    async def _weekly_report_scheduler(self):
        """주간 보고 스케줄러를 실행합니다."""
        while True:
            try:
                current_time = datetime.now(pytz.timezone(self.settings.timezone))
                
                # 다음 월요일 오전 9시까지 대기
                days_ahead = 7 - current_time.weekday()  # 월요일 = 0
                if days_ahead == 7:
                    days_ahead = 0
                
                next_monday = current_time + timedelta(days=days_ahead)
                next_report = next_monday.replace(
                    hour=9, minute=0, second=0, microsecond=0
                )
                
                wait_seconds = (next_report - current_time).total_seconds()
                await asyncio.sleep(wait_seconds)
                
                # 주간 보고 전송
                await self._send_weekly_report()
                
            except Exception as e:
                self.logger.error(f"주간 보고 스케줄러 오류: {e}")
                await asyncio.sleep(86400)  # 1일 대기
    
    async def _send_weekly_report(self):
        """주간 보고를 전송합니다."""
        try:
            # 지난 주 데이터 수집
            week_ago = datetime.now(pytz.timezone(self.settings.timezone)) - timedelta(days=7)
            
            # 통계 데이터 수집 (실제 구현에서는 더 상세한 통계 필요)
            total_sessions = len(self.application_manager.applications)
            active_sessions = len(self.application_manager.get_active_sessions())
            
            for admin_id in self.settings.admin_ids:
                try:
                    user = self.bot.get_user(admin_id)
                    if not user:
                        continue
                    
                    embed = discord.Embed(
                        title="📈 주간 스케줄 신청 통계",
                        description=f"지난 주 활동 요약",
                        color=discord.Color.purple()
                    )
                    
                    embed.add_field(
                        name="📊 전체 현황",
                        value=(
                            f"총 신청 세션: {total_sessions}개\n"
                            f"활성 세션: {active_sessions}개\n"
                            f"마감된 세션: {total_sessions - active_sessions}개"
                        ),
                        inline=False
                    )
                    
                    embed.add_field(
                        name="💡 개선 제안",
                        value=(
                            "• 참여도가 낮은 채널에 대한 홍보 강화\n"
                            "• 인기 날짜 충돌 해결 방안 검토\n"
                            "• 신청 기간 조정 고려"
                        ),
                        inline=False
                    )
                    
                    await user.send(embed=embed)
                    
                except Exception as e:
                    self.logger.error(f"관리자 주간 보고 전송 실패 (ID: {admin_id}): {e}")
                    
        except Exception as e:
            self.logger.error(f"주간 보고 전송 실패: {e}")
    
    async def send_low_participation_alert(self, session: Dict):
        """낮은 참여도 알림을 전송합니다."""
        summary = session['summary']
        
        if summary['total_applications'] < self.notification_settings['low_participation_threshold']:
            for admin_id in self.settings.admin_ids:
                try:
                    user = self.bot.get_user(admin_id)
                    if user:
                        channel = self.bot.get_channel(session['channel_id'])
                        channel_name = channel.name if channel else f"채널 {session['channel_id']}"
                        
                        await user.send(
                            f"⚠️ **낮은 참여도 알림**\n\n"
                            f"채널: #{channel_name}\n"
                            f"현재 신청: {summary['total_applications']}명\n"
                            f"기준: {self.notification_settings['low_participation_threshold']}명\n\n"
                            f"홍보나 리마인더 메시지 전송을 고려해보세요."
                        )
                        
                except Exception as e:
                    self.logger.error(f"낮은 참여도 알림 전송 실패 (ID: {admin_id}): {e}")
    
    async def send_high_conflict_alert(self, session: Dict):
        """높은 충돌 알림을 전송합니다."""
        summary = session['summary']
        
        if len(summary['popular_dates']) >= self.notification_settings['high_conflict_threshold']:
            for admin_id in self.settings.admin_ids:
                try:
                    user = self.bot.get_user(admin_id)
                    if user:
                        channel = self.bot.get_channel(session['channel_id'])
                        channel_name = channel.name if channel else f"채널 {session['channel_id']}"
                        
                        conflict_dates = "\n".join([
                            f"• {date} ({summary['date_counts'][date]}명 신청)"
                            for date in summary['popular_dates'][:5]
                        ])
                        
                        await user.send(
                            f"🔥 **높은 충돌 알림**\n\n"
                            f"채널: #{channel_name}\n"
                            f"충돌 날짜 수: {len(summary['popular_dates'])}개\n\n"
                            f"충돌 날짜:\n{conflict_dates}\n\n"
                            f"조정이 필요할 수 있습니다."
                        )
                        
                except Exception as e:
                    self.logger.error(f"높은 충돌 알림 전송 실패 (ID: {admin_id}): {e}")
    
    def shutdown(self):
        """알림 시스템을 종료합니다."""
        for task_name, task in self.notification_tasks.items():
            if not task.done():
                task.cancel()
        self.logger.info("알림 시스템 종료됨") 