"""
예약 메시지 관리를 위한 디스코드 봇 명령어.
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging
from datetime import datetime
import pytz

class AnnouncementModal(discord.ui.Modal, title="📢 공지사항 작성"):
    """공지사항 작성을 위한 모달."""
    
    def __init__(self):
        super().__init__()
    
    title_input = discord.ui.TextInput(
        label="제목",
        placeholder="공지사항 제목을 입력하세요.",
        style=discord.TextStyle.short,
        required=True
    )
    
    content_input = discord.ui.TextInput(
        label="내용",
        placeholder="공지 내용을 입력하세요. Markdown을 지원합니다.",
        style=discord.TextStyle.long,
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """모달 제출 시 호출됩니다."""
        try:
            # "주요공지" 채널 찾기
            announcement_channel = None
            for guild in interaction.client.guilds:
                for channel in guild.text_channels:
                    if channel.name == "💾ㅣ자료실":
                        announcement_channel = channel
                        break
                if announcement_channel:
                    break
            
            if not announcement_channel:
                await interaction.response.send_message(
                    "❌ '주요공지' 채널을 찾을 수 없습니다. 채널명을 확인해주세요.",
                    ephemeral=True
                )
                return
            
            # 공지사항 임베드 생성
            embed = discord.Embed(
                title=f"{self.title_input.value}",
                description=self.content_input.value,
                color=discord.Color.gold(),
                timestamp=datetime.now()
            )
            embed.set_author(
                name=f"{interaction.user.display_name}님의 공지",
                icon_url=interaction.user.avatar.url if interaction.user.avatar else None
            )
            if interaction.guild:
                embed.set_footer(text=f"From {interaction.guild.name}")
            else:
                embed.set_footer(text="개인 메시지로부터의 공지")
            
            # 공지사항 전송
            await announcement_channel.send(embed=embed)
            
            # 성공 메시지
            await interaction.response.send_message("✅ 공지가 성공적으로 전송되었습니다.", ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ 공지사항 업로드 중 오류가 발생했습니다: {str(e)}",
                ephemeral=True
            )

class BotCommands(commands.Cog):
    """예약 메시지 봇 관리를 위한 명령어."""
    
    def __init__(self, bot, settings, scheduler, application_manager, analytics):
        """명령어 cog를 초기화합니다."""
        self.bot = bot
        self.settings = settings
        self.scheduler = scheduler
        self.application_manager = application_manager
        self.analytics = analytics
        self.logger = logging.getLogger(__name__)
    
    @commands.command(name='데모', aliases=['demo'])
    async def demo_command(self, ctx):
        """봇의 기능을 데모로 보여줍니다."""
        embed = discord.Embed(
            title="🤖 스케줄 신청 봇 데모",
            description="실제 작동하는 기능들을 확인해보세요!",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="1️⃣ 현재 상태 확인",
            value="`!status` - 봇 상태와 다음 예약 메시지 확인",
            inline=False
        )
        
        embed.add_field(
            name="2️⃣ 테스트 메시지",
            value="`!test` - 스케줄 신청 메시지 미리보기",
            inline=False
        )
        
        embed.add_field(
            name="3️⃣ 설정된 채널",
            value="`!channels` - 예약 메시지가 전송될 채널 목록",
            inline=False
        )
        
        embed.add_field(
            name="4️⃣ 자동 응답 테스트",
            value="테스트 메시지에 답글을 달면 자동으로 '신청 완료' 응답을 받을 수 있습니다",
            inline=False
        )
        
        embed.set_footer(text="매월 20일 오전 9시에 자동으로 스케줄 신청 안내가 게시됩니다")
        
        await ctx.send(embed=embed)

    # 슬래시 명령어 버전
    @app_commands.command(name="데모", description="봇의 기능을 데모로 보여줍니다")
    async def demo_slash(self, interaction: discord.Interaction):
        """슬래시 명령어로 봇 데모를 보여줍니다."""
        embed = discord.Embed(
            title="🤖 스케줄 신청 봇 데모",
            description="실제 작동하는 기능들을 확인해보세요!",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="1️⃣ 현재 상태 확인",
            value="`/상태` 또는 `!status` - 봇 상태와 다음 예약 메시지 확인",
            inline=False
        )
        
        embed.add_field(
            name="2️⃣ 테스트 메시지",
            value="`/테스트` 또는 `!test` - 스케줄 신청 메시지 미리보기",
            inline=False
        )
        
        embed.add_field(
            name="3️⃣ 설정된 채널",
            value="`/채널목록` 또는 `!channels` - 예약 메시지가 전송될 채널 목록",
            inline=False
        )
        
        embed.add_field(
            name="4️⃣ 자동 응답 테스트",
            value="테스트 메시지에 답글을 달면 자동으로 '신청 완료' 응답을 받을 수 있습니다",
            inline=False
        )
        
        embed.set_footer(text="매월 20일 오전 9시에 자동으로 스케줄 신청 안내가 게시됩니다")
        
        await interaction.response.send_message(embed=embed)

    @commands.command(name='help', aliases=['도움말', 'h'])
    async def help_command(self, ctx):
        """봇 명령어에 대한 도움말 정보를 표시합니다."""
        embed = discord.Embed(
            title="📅 예약 메시지 봇 도움말",
            description="매월 20일 오전 9시에 자동으로 메시지를 게시하는 봇",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="🔧 기본 명령어",
            value=(
                f"`{self.settings.command_prefix}help` - 이 도움말 메시지 표시\n"
                f"`{self.settings.command_prefix}status` - 봇 상태 및 다음 예약 메시지 표시\n"
                f"`{self.settings.command_prefix}channels` - 설정된 채널 목록 표시\n"
                f"`{self.settings.command_prefix}test [채널ID]` - 설정 확인을 위한 테스트 메시지 전송\n"
                f"`{self.settings.command_prefix}demo` - 봇 기능 데모"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚡ 슬래시 명령어",
            value=(
                "`/데모` - 봇 기능 데모\n"
                "`/상태` - 봇 상태 확인\n"
                "`/채널목록` - 설정된 채널 목록\n"
                "`/테스트 [채널ID]` - 테스트 메시지 전송\n"
                "`/명령어` - 이 도움말 표시\n"
                "`/공지` - 공지사항 작성 (모달 입력)\n"
                "`/신청현황` - 신청 현황 요약 (DM 전송)\n"
                "`/통계` - 신청 통계 리포트 (DM 전송)"
            ),
            inline=False
        )
        
        embed.add_field(
            name="👑 관리자 명령어",
            value=(
                f"`{self.settings.command_prefix}add_channel <채널ID> [메시지]` - 예약 채널 추가\n"
                f"`{self.settings.command_prefix}remove_channel <채널ID>` - 예약 채널 삭제\n"
                f"`{self.settings.command_prefix}set_message <채널ID> <메시지>` - 채널별 메시지 수정\n"
                f"`{self.settings.command_prefix}sendlog [개수]` - 최근 발송 내역 조회\n"
                f"`{self.settings.command_prefix}신청현황` - 신청 현황 요약 (DM 전송)\n"
                f"`{self.settings.command_prefix}통계` - 신청 통계 리포트 (DM 전송)"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📋 특별 기능",
            value=(
                "**스케줄 업로드**: DM으로 이미지 + `!스케쥴업로드` → 자동 공지\n"
                "**자동 응답**: 스케줄 메시지 댓글 → 자동 '신청 완료' 응답\n"
                "**현황/통계**: 관리자 DM으로만 전송 (보안 강화)"
            ),
            inline=False
        )
        
        embed.add_field(
            name="일정",
            value="메시지는 **매월 20일 오전 9:00**에 자동으로 게시됩니다",
            inline=False
        )
        
        embed.set_footer(text=f"시간대: {self.settings.timezone}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='status')
    async def status_command(self, ctx):
        """봇 상태와 예정된 메시지를 표시합니다."""
        embed = discord.Embed(
            title="📊 봇 상태",
            color=discord.Color.green()
        )
        
        # 봇 정보
        embed.add_field(
            name="봇 정보",
            value=(
                f"**서버 수:** {len(self.bot.guilds)}\n"
                f"**시간대:** {self.settings.timezone}\n"
                f"**예약된 채널:** {len(self.settings.scheduled_channels)}"
            ),
            inline=True
        )
        
        # 현재 시간
        current_time = datetime.now(pytz.timezone(self.settings.timezone))
        embed.add_field(
            name="현재 시간",
            value=current_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
            inline=True
        )
        
        # 다음 예약된 실행
        next_runs = self.scheduler.get_next_runs()
        if next_runs:
            runs_text = ""
            for run_info in next_runs[:5]:  # 최대 5개의 예정된 실행 표시
                next_run = run_info['next_run']
                channel_name = run_info['channel_name']
                runs_text += f"**{channel_name}**\n{next_run.strftime('%Y-%m-%d %H:%M:%S %Z')}\n\n"
            
            embed.add_field(
                name="다음 예약 메시지",
                value=runs_text.strip(),
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='channels')
    async def channels_command(self, ctx):
        """예약 메시지용으로 설정된 모든 채널을 나열합니다."""
        embed = discord.Embed(
            title="📋 설정된 채널",
            color=discord.Color.orange()
        )
        
        if not self.settings.scheduled_channels:
            embed.description = "현재 예약 메시지용으로 설정된 채널이 없습니다."
        else:
            channels_text = ""
            for i, channel_config in enumerate(self.settings.scheduled_channels, 1):
                channel_id = channel_config['channel_id']
                channel = self.bot.get_channel(channel_id)
                
                if channel and hasattr(channel, 'name') and hasattr(channel, 'guild'):
                    channel_info = f"#{channel.name} in {channel.guild.name}"
                    status = "✅ 접근 가능"
                elif channel:
                    channel_info = f"채널 ID: {channel_id}"
                    status = "✅ 접근 가능"
                else:
                    channel_info = f"채널 ID: {channel_id}"
                    status = "❌ 접근 불가"
                
                channels_text += f"**{i}.** {channel_info}\n"
                channels_text += f"   ID: `{channel_id}`\n"
                channels_text += f"   상태: {status}\n\n"
            
            embed.description = channels_text
        
        embed.set_footer(text="메시지는 매월 20일 오전 9:00에 게시됩니다")
        
        await ctx.send(embed=embed)
    
    @app_commands.command(name="채널목록", description="예약 메시지용으로 설정된 모든 채널을 나열합니다")
    async def channels_slash(self, interaction: discord.Interaction):
        """슬래시 명령어로 설정된 채널 목록을 확인합니다."""
        embed = discord.Embed(
            title="📋 설정된 채널",
            color=discord.Color.orange()
        )
        
        if not self.settings.scheduled_channels:
            embed.description = "현재 예약 메시지용으로 설정된 채널이 없습니다."
        else:
            channels_text = ""
            for i, channel_config in enumerate(self.settings.scheduled_channels, 1):
                channel_id = channel_config['channel_id']
                channel = self.bot.get_channel(channel_id)
                
                if channel and hasattr(channel, 'name') and hasattr(channel, 'guild'):
                    channel_info = f"#{channel.name} in {channel.guild.name}"
                    status = "✅ 접근 가능"
                elif channel:
                    channel_info = f"채널 ID: {channel_id}"
                    status = "✅ 접근 가능"
                else:
                    channel_info = f"채널 ID: {channel_id}"
                    status = "❌ 접근 불가"
                
                channels_text += f"**{i}.** {channel_info}\n"
                channels_text += f"   ID: `{channel_id}`\n"
                channels_text += f"   상태: {status}\n\n"
            
            embed.description = channels_text
        
        embed.set_footer(text="메시지는 매월 20일 오전 9:00에 게시됩니다")
        
        await interaction.response.send_message(embed=embed)
    
    @commands.command(name='test')
    @commands.has_permissions(manage_messages=True)
    async def test_command(self, ctx, channel_id: int = 0):
        """예약 메시지 시스템을 확인하기 위해 테스트 메시지를 전송합니다."""
        if channel_id == 0:
            # 현재 채널을 기본값으로 사용
            channel_id = ctx.channel.id
            await ctx.send(f"현재 채널 ({channel_id})에 테스트 메시지를 전송합니다.")
        
        # 테스트는 어떤 채널에서든 허용 (관리자 권한 확인됨)
        
        # 채널이 존재하고 접근 가능한지 확인
        target_channel = self.bot.get_channel(channel_id)
        if target_channel is None:
            await ctx.send(f"❌ 채널 ID `{channel_id}`에 접근할 수 없습니다.")
            return
        
        try:
            # 테스트 메시지 전송
            success = await self.scheduler.send_test_message(channel_id)
            
            if success:
                # 성공 메시지와 테스트 안내를 하나의 메시지로 통합
                success_msg = f"✅ **테스트 완료!** 스케줄 신청 메시지가 {target_channel.mention}에 전송되었습니다.\n\n"
                success_msg += "💡 **자동 응답 테스트:** 전송된 메시지에 답글을 달면 '스케줄 신청이 완료되었습니다' 자동 응답을 받을 수 있습니다."
                
                await ctx.send(success_msg)
                
                if hasattr(target_channel, 'name'):
                    self.logger.info(f"테스트 메시지가 #{target_channel.name}에 {ctx.author}에 의해 전송됨")
                else:
                    self.logger.info(f"테스트 메시지가 채널 ID {channel_id}에 {ctx.author}에 의해 전송됨")
            else:
                await ctx.send("❌ 테스트 메시지 전송에 실패했습니다.")
            
        except Exception as e:
            await ctx.send(f"❌ 테스트 메시지 전송 중 오류가 발생했습니다: {str(e)}")
            self.logger.error(f"테스트 명령어 오류: {e}")
    
    @app_commands.command(name="테스트", description="예약 메시지 시스템을 확인하기 위해 테스트 메시지를 전송합니다")
    @app_commands.describe(channel_id="테스트 메시지를 전송할 채널 ID (비워두면 현재 채널)")
    async def test_slash(self, interaction: discord.Interaction, channel_id: int = 0):
        """슬래시 명령어로 테스트 메시지를 전송합니다."""
        # 권한 확인
        if hasattr(interaction.user, 'guild_permissions') and not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ 이 명령어를 사용하려면 '메시지 관리' 권한이 필요합니다.", ephemeral=True)
            return
        
        if channel_id == 0:
            channel_id = interaction.channel.id
            await interaction.response.send_message(f"현재 채널 ({channel_id})에 테스트 메시지를 전송합니다.")
        else:
            await interaction.response.defer()
        
        # 채널이 존재하고 접근 가능한지 확인
        target_channel = self.bot.get_channel(channel_id)
        if target_channel is None:
            if channel_id == interaction.channel.id:
                await interaction.edit_original_response(content=f"❌ 채널 ID `{channel_id}`에 접근할 수 없습니다.")
            else:
                await interaction.followup.send(f"❌ 채널 ID `{channel_id}`에 접근할 수 없습니다.")
            return
        
        try:
            # 테스트 메시지 전송
            success = await self.scheduler.send_test_message(channel_id)
            
            if success:
                # 성공 메시지와 테스트 안내를 하나의 메시지로 통합
                success_msg = f"✅ **테스트 완료!** 스케줄 신청 메시지가 {target_channel.mention}에 전송되었습니다.\n\n"
                success_msg += "💡 **자동 응답 테스트:** 전송된 메시지에 답글을 달면 '스케줄 신청이 완료되었습니다' 자동 응답을 받을 수 있습니다."
                
                if channel_id == interaction.channel.id:
                    await interaction.edit_original_response(content=success_msg)
                else:
                    await interaction.followup.send(success_msg)
                
                if hasattr(target_channel, 'name'):
                    self.logger.info(f"테스트 메시지가 #{target_channel.name}에 {interaction.user}에 의해 전송됨 (슬래시 명령어)")
                else:
                    self.logger.info(f"테스트 메시지가 채널 ID {channel_id}에 {interaction.user}에 의해 전송됨 (슬래시 명령어)")
            else:
                error_msg = "❌ 테스트 메시지 전송에 실패했습니다."
                if channel_id == interaction.channel.id:
                    await interaction.edit_original_response(content=error_msg)
                else:
                    await interaction.followup.send(error_msg)
            
        except Exception as e:
            error_msg = f"❌ 테스트 메시지 전송 중 오류가 발생했습니다: {str(e)}"
            if channel_id == interaction.channel.id:
                await interaction.edit_original_response(content=error_msg)
            else:
                await interaction.followup.send(error_msg)
            self.logger.error(f"테스트 슬래시 명령어 오류: {e}")
    
    @test_command.error
    async def test_command_error(self, ctx, error):
        """테스트 명령어의 오류를 처리합니다."""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ 이 명령어를 사용하려면 '메시지 관리' 권한이 필요합니다.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ 잘못된 채널 ID입니다. 유효한 숫자를 제공해주세요.")
    
    @app_commands.command(name="명령어", description="사용 가능한 모든 슬래시 명령어를 표시합니다")
    async def commands_slash(self, interaction: discord.Interaction):
        """사용 가능한 슬래시 명령어 목록을 표시합니다."""
        embed = discord.Embed(
            title="📋 사용 가능한 명령어 총정리",
            description="디스코드에서 `/`를 입력하여 명령어를 사용할 수 있습니다.",
            color=discord.Color.purple()
        )
        
        embed.add_field(
            name="🔧 기본 명령어 (!)",
            value=(
                "`!help` / `!도움말` - 도움말 표시\n"
                "`!status` - 봇 상태 및 다음 예약 메시지 확인\n"
                "`!channels` - 설정된 채널 목록 표시\n"
                "`!test [채널ID]` - 테스트 메시지 전송\n"
                "`!demo` - 봇 기능 데모"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚡ 슬래시 명령어 (/)",
            value=(
                "`/데모` - 봇 기능 데모\n"
                "`/상태` - 봇 상태 확인\n"
                "`/채널목록` - 설정된 채널 목록\n"
                "`/테스트 [채널ID]` - 테스트 메시지 전송\n"
                "`/명령어` - 이 도움말 표시\n"
                "`/공지` - 공지사항 작성 (모달 입력)\n"
                "`/신청현황` - 신청 현황 요약 (DM 전송)\n"
                "`/통계` - 신청 통계 리포트 (DM 전송)"
            ),
            inline=False
        )
        
        embed.add_field(
            name="👑 관리자 전용 명령어",
            value=(
                "`!add_channel <채널ID> [메시지]` - 예약 채널 추가\n"
                "`!remove_channel <채널ID>` - 예약 채널 삭제\n"
                "`!set_message <채널ID> <메시지>` - 채널별 메시지 수정\n"
                "`!sendlog [개수]` - 최근 발송 내역 조회\n"
                "`!신청현황` - 신청 현황 요약 (DM 전송)\n"
                "`!통계` - 신청 통계 리포트 (DM 전송)"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📋 특별 기능",
            value=(
                "**스케줄 업로드**: DM으로 이미지 + `!스케쥴업로드` → 자동 공지\n"
                "**자동 응답**: 스케줄 메시지 댓글 → 자동 '신청 완료' 응답\n"
                "**현황/통계**: 관리자 DM으로만 전송 (보안 강화)\n"
                "**공지사항**: 모달 입력으로 깔끔한 공지 작성"
            ),
            inline=False
        )
        
        embed.add_field(
            name="💡 팁",
            value=(
                "• 슬래시 명령어(`/`)가 더 현대적이고 안정적입니다\n"
                "• 관리자 명령어는 서버 관리 권한이 필요합니다\n"
                "• 신청 현황/통계는 DM으로만 전송되어 보안이 강화됩니다"
            ),
            inline=False
        )
        
        embed.set_footer(text="매월 20일 오전 9시에 자동으로 스케줄 신청 안내가 게시됩니다")
        
        await interaction.response.send_message(embed=embed)
    
    @commands.command(name='add_channel')
    @commands.has_permissions(administrator=True)
    async def add_channel(self, ctx, channel_id: int, *, message: str = ""):
        """예약 메시지 채널 추가: !add_channel <채널ID> [메시지]"""
        if self.settings.add_scheduled_channel(channel_id, message):
            await ctx.send(f"✅ 채널 {channel_id}가 예약 채널로 추가되었습니다.")
        else:
            await ctx.send(f"❌ 채널 {channel_id}는 이미 예약 채널로 등록되어 있습니다.")

    @commands.command(name='remove_channel')
    @commands.has_permissions(administrator=True)
    async def remove_channel(self, ctx, channel_id: int):
        """예약 메시지 채널 삭제: !remove_channel <채널ID>"""
        if self.settings.remove_scheduled_channel(channel_id):
            await ctx.send(f"✅ 채널 {channel_id}가 예약 채널에서 삭제되었습니다.")
        else:
            await ctx.send(f"❌ 채널 {channel_id}는 예약 채널로 등록되어 있지 않습니다.")

    @commands.command(name='set_message')
    @commands.has_permissions(administrator=True)
    async def set_message(self, ctx, channel_id: int, *, message: str):
        """예약 메시지 내용 수정: !set_message <채널ID> <메시지>"""
        found = False
        for ch in self.settings.scheduled_channels:
            if ch['channel_id'] == channel_id:
                ch['message'] = message
                self.settings.save_config()
                found = True
                break
        if found:
            await ctx.send(f"✅ 채널 {channel_id}의 예약 메시지가 수정되었습니다.")
        else:
            await ctx.send(f"❌ 채널 {channel_id}는 예약 채널로 등록되어 있지 않습니다.")

    @commands.command(name='sendlog')
    @commands.has_permissions(administrator=True)
    async def sendlog(self, ctx, limit: int = 10):
        """최근 예약 메시지 발송 내역 조회: !sendlog [개수]"""
        logs = self.settings.get_send_logs(limit)
        if not logs:
            await ctx.send("최근 발송 내역이 없습니다.")
            return
        desc = ""
        for log in logs:
            desc += f"채널: {log.get('channel_id')} | 상태: {log.get('status')} | 시도: {log.get('attempt', 1)}\n시간: {log.get('datetime')}\n"
            if log.get('status') == 'fail':
                desc += f"오류: {log.get('error')}\n"
            desc += "---\n"
        embed = discord.Embed(title="최근 예약 메시지 발송 내역", description=desc, color=discord.Color.dark_gold())
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        # 봇 자신의 메시지, 서버 메시지 무시
        if message.author.bot or message.guild is not None:
            return
        # 관리자만 허용 (admin_ids는 config에 있어야 함)
        admin_ids = getattr(self.settings, 'admin_ids', [])
        if message.author.id not in admin_ids:
            return
        # 첨부파일이 있고, 텍스트 명령이 '!스케쥴업로드'로 시작
        if message.attachments and message.content.strip().startswith('!스케쥴업로드'):
            await message.channel.send('몇 월 스케쥴 공지인지 숫자(예: 7)를 입력해 주세요.')
            def check(m):
                return m.author == message.author and m.channel == message.channel and m.content.isdigit()
            try:
                reply = await self.bot.wait_for('message', check=check, timeout=60)
                month = int(reply.content)
                # 스케쥴 채널 찾기 (이름이 '스케쥴'인 텍스트 채널)
                schedule_channel = None
                for guild in self.bot.guilds:
                    for channel in guild.text_channels:
                        if channel.name == '스케쥴':
                            schedule_channel = channel
                            break
                    if schedule_channel:
                        break
                if not schedule_channel:
                    await message.channel.send('서버에 "스케쥴" 채널을 찾을 수 없습니다.')
                    return
                # 양식 메시지 생성
                title = f"[ 📅 {month}월 스케쥴 공지 ]"
                content = (
                    f"{month}월 스케쥴을 아래 이미지와 같이 공지드립니다.\n"
                    "각 개인은 해당 스케쥴 참고해주세요.\n"
                    "요청한 휴무 반영 여부 확인 부탁드립니다."
                )
                # 파일 첨부
                file = await message.attachments[0].to_file()
                await schedule_channel.send(content=f"{title}\n\n{content}", file=file)
                await message.channel.send(f"{month}월 스케쥴 공지가 서버에 업로드되었습니다.")
            except Exception as e:
                await message.channel.send(f"오류 또는 시간 초과: {e}")

    @commands.command(name='신청현황')
    @commands.has_permissions(administrator=True)
    async def application_status(self, ctx):
        """현재 활성화된 모든 신청 세션의 현황을 요약해서 DM으로 보여줍니다 (관리자 전용)."""
        sessions = self.application_manager.get_active_sessions()
        if not sessions:
            await ctx.author.send("현재 활성화된 신청 세션이 없습니다.")
            return
        embed = discord.Embed(title="📋 신청 현황 요약", color=discord.Color.teal())
        for session in sessions:
            summary = session['summary']
            channel = self.bot.get_channel(session['channel_id'])
            channel_name = channel.name if channel else f"채널 {session['channel_id']}"
            embed.add_field(
                name=f"#{channel_name}",
                value=(
                    f"신청자: {summary['unique_applicants']}명\n"
                    f"총 신청: {summary['total_applications']}건\n"
                    f"마감: <t:{int(datetime.fromisoformat(session['deadline']).timestamp())}:R>"
                ),
                inline=False
            )
        try:
            await ctx.author.send(embed=embed)
            if ctx.guild:
                await ctx.send("✅ 현황 요약을 DM으로 전송했습니다.", delete_after=10)
        except Exception:
            await ctx.send("❌ DM 전송에 실패했습니다. DM 허용 여부를 확인해주세요.")

    @app_commands.command(name="신청현황", description="현재 활성화된 모든 신청 세션의 현황을 요약해서 DM으로 보여줍니다 (관리자 전용)")
    async def application_status_slash(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ 관리자만 사용할 수 있습니다.", ephemeral=True)
            return
        sessions = self.application_manager.get_active_sessions()
        if not sessions:
            await interaction.user.send("현재 활성화된 신청 세션이 없습니다.")
            await interaction.response.send_message("DM으로 현황을 전송했습니다.", ephemeral=True)
            return
        embed = discord.Embed(title="📋 신청 현황 요약", color=discord.Color.teal())
        for session in sessions:
            summary = session['summary']
            channel = self.bot.get_channel(session['channel_id'])
            channel_name = channel.name if channel else f"채널 {session['channel_id']}"
            embed.add_field(
                name=f"#{channel_name}",
                value=(
                    f"신청자: {summary['unique_applicants']}명\n"
                    f"총 신청: {summary['total_applications']}건\n"
                    f"마감: <t:{int(datetime.fromisoformat(session['deadline']).timestamp())}:R>"
                ),
                inline=False
            )
        try:
            await interaction.user.send(embed=embed)
            await interaction.response.send_message("✅ 현황 요약을 DM으로 전송했습니다.", ephemeral=True)
        except Exception:
            await interaction.response.send_message("❌ DM 전송에 실패했습니다. DM 허용 여부를 확인해주세요.", ephemeral=True)

    @commands.command(name='통계')
    @commands.has_permissions(administrator=True)
    async def analytics_report(self, ctx):
        """스케줄 신청 통계 및 분석 리포트를 DM으로 보여줍니다 (관리자 전용)."""
        report = self.analytics.generate_comprehensive_report()
        embed = discord.Embed(title="📊 스케줄 신청 통계 리포트", color=discord.Color.dark_blue())
        # 월별 통계
        monthly = report.get('monthly_stats', {})
        embed.add_field(name="이번 달 신청 수", value=str(monthly.get('total_applications', 0)), inline=True)
        embed.add_field(name="고유 신청자 수", value=str(monthly.get('unique_users', 0)), inline=True)
        # 인기 날짜
        popular_dates = monthly.get('popular_dates', {})
        if popular_dates:
            embed.add_field(name="인기 날짜 Top 3", value="\n".join([f"{k}: {v}명" for k, v in list(popular_dates.items())[:3]]), inline=False)
        # 인사이트
        insights = report.get('insights', [])
        if insights:
            embed.add_field(name="데이터 인사이트", value="\n".join(insights), inline=False)
        try:
            await ctx.author.send(embed=embed)
            if ctx.guild:
                await ctx.send("✅ 통계 리포트를 DM으로 전송했습니다.", delete_after=10)
        except Exception:
            await ctx.send("❌ DM 전송에 실패했습니다. DM 허용 여부를 확인해주세요.")

    @app_commands.command(name="통계", description="스케줄 신청 통계 및 분석 리포트를 DM으로 보여줍니다 (관리자 전용)")
    async def analytics_report_slash(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ 관리자만 사용할 수 있습니다.", ephemeral=True)
            return
        report = self.analytics.generate_comprehensive_report()
        embed = discord.Embed(title="📊 스케줄 신청 통계 리포트", color=discord.Color.dark_blue())
        # 월별 통계
        monthly = report.get('monthly_stats', {})
        embed.add_field(name="이번 달 신청 수", value=str(monthly.get('total_applications', 0)), inline=True)
        embed.add_field(name="고유 신청자 수", value=str(monthly.get('unique_users', 0)), inline=True)
        # 인기 날짜
        popular_dates = monthly.get('popular_dates', {})
        if popular_dates:
            embed.add_field(name="인기 날짜 Top 3", value="\n".join([f"{k}: {v}명" for k, v in list(popular_dates.items())[:3]]), inline=False)
        # 인사이트
        insights = report.get('insights', [])
        if insights:
            embed.add_field(name="데이터 인사이트", value="\n".join(insights), inline=False)
        try:
            await interaction.user.send(embed=embed)
            await interaction.response.send_message("✅ 통계 리포트를 DM으로 전송했습니다.", ephemeral=True)
        except Exception:
            await interaction.response.send_message("❌ DM 전송에 실패했습니다. DM 허용 여부를 확인해주세요.", ephemeral=True)

    @app_commands.command(name="공지", description="공지사항을 작성하여 자료실 채널에 업로드합니다")
    async def announcement_slash(self, interaction: discord.Interaction):
        """슬래시 명령어로 공지사항을 작성합니다."""
        # 권한 확인
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message(
                "❌ 이 명령어를 사용하려면 '메시지 관리' 권한이 필요합니다.",
                ephemeral=True
            )
            return
        
        modal = AnnouncementModal()
        await interaction.response.send_modal(modal)
