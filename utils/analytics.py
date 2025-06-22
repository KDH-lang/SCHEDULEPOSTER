"""
통계 및 분석 시스템.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter
import pytz

class Analytics:
    """스케줄 신청 통계 및 분석을 관리합니다."""
    
    def __init__(self, settings, data_file: str = "config/analytics.json"):
        """분석 시스템을 초기화합니다."""
        self.settings = settings
        self.data_file = data_file
        self.logger = logging.getLogger(__name__)
        
        # 통계 데이터 구조
        self.analytics_data = {
            'monthly_stats': {},  # 월별 통계
            'user_participation': {},  # 사용자 참여도
            'popular_times': {},  # 인기 시간대
            'channel_performance': {},  # 채널별 성과
            'trends': {}  # 트렌드 데이터
        }
        
        # 데이터 로드
        self._load_data()
    
    def _load_data(self):
        """분석 데이터를 파일에서 로드합니다."""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.analytics_data = json.load(f)
            self.logger.info("분석 데이터 로드 완료")
        except FileNotFoundError:
            self.logger.info("분석 데이터 파일이 없습니다. 새로 생성합니다.")
            self._save_data()
        except Exception as e:
            self.logger.error(f"분석 데이터 로드 실패: {e}")
            self.analytics_data = {
                'monthly_stats': {},
                'user_participation': {},
                'popular_times': {},
                'channel_performance': {},
                'trends': {}
            }
    
    def _save_data(self):
        """분석 데이터를 파일에 저장합니다."""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.analytics_data, f, ensure_ascii=False, indent=2)
            self.logger.debug("분석 데이터 저장 완료")
        except Exception as e:
            self.logger.error(f"분석 데이터 저장 실패: {e}")
    
    def record_application(self, application_data: Dict):
        """신청 데이터를 기록하고 통계를 업데이트합니다."""
        try:
            current_time = datetime.now(pytz.timezone(self.settings.timezone))
            month_key = current_time.strftime("%Y-%m")
            
            # 월별 통계 업데이트
            self._update_monthly_stats(month_key, application_data)
            
            # 사용자 참여도 업데이트
            self._update_user_participation(application_data)
            
            # 인기 시간대 업데이트
            self._update_popular_times(current_time, application_data)
            
            # 채널 성과 업데이트
            self._update_channel_performance(application_data)
            
            # 트렌드 데이터 업데이트
            self._update_trends(current_time, application_data)
            
            self._save_data()
            
        except Exception as e:
            self.logger.error(f"신청 데이터 기록 실패: {e}")
    
    def _update_monthly_stats(self, month_key: str, application_data: Dict):
        """월별 통계를 업데이트합니다."""
        if month_key not in self.analytics_data['monthly_stats']:
            self.analytics_data['monthly_stats'][month_key] = {
                'total_applications': 0,
                'unique_users': set(),
                'popular_dates': Counter(),
                'application_times': [],
                'channels': Counter()
            }
        
        stats = self.analytics_data['monthly_stats'][month_key]
        stats['total_applications'] += 1
        stats['unique_users'].add(application_data['user_id'])
        
        # 날짜별 신청 현황
        for date in application_data['requested_dates']:
            stats['popular_dates'][date] += 1
        
        # 신청 시간 기록
        stats['application_times'].append(application_data['applied_at'])
        
        # 채널별 신청 현황
        if 'channel_id' in application_data:
            stats['channels'][application_data['channel_id']] += 1
    
    def _update_user_participation(self, application_data: Dict):
        """사용자 참여도를 업데이트합니다."""
        user_id = str(application_data['user_id'])
        
        if user_id not in self.analytics_data['user_participation']:
            self.analytics_data['user_participation'][user_id] = {
                'total_applications': 0,
                'first_application': application_data['applied_at'],
                'last_application': application_data['applied_at'],
                'preferred_dates': Counter(),
                'application_months': set()
            }
        
        user_data = self.analytics_data['user_participation'][user_id]
        user_data['total_applications'] += 1
        user_data['last_application'] = application_data['applied_at']
        
        # 선호 날짜 기록
        for date in application_data['requested_dates']:
            user_data['preferred_dates'][date] += 1
        
        # 신청 월 기록
        current_month = datetime.fromisoformat(application_data['applied_at']).strftime("%Y-%m")
        user_data['application_months'].add(current_month)
    
    def _update_popular_times(self, current_time: datetime, application_data: Dict):
        """인기 시간대를 업데이트합니다."""
        hour_key = current_time.strftime("%H")
        day_key = current_time.strftime("%A")  # 요일
        
        if 'hourly' not in self.analytics_data['popular_times']:
            self.analytics_data['popular_times']['hourly'] = Counter()
        if 'daily' not in self.analytics_data['popular_times']:
            self.analytics_data['popular_times']['daily'] = Counter()
        
        self.analytics_data['popular_times']['hourly'][hour_key] += 1
        self.analytics_data['popular_times']['daily'][day_key] += 1
    
    def _update_channel_performance(self, application_data: Dict):
        """채널별 성과를 업데이트합니다."""
        if 'channel_id' not in application_data:
            return
        
        channel_id = str(application_data['channel_id'])
        
        if channel_id not in self.analytics_data['channel_performance']:
            self.analytics_data['channel_performance'][channel_id] = {
                'total_applications': 0,
                'unique_users': set(),
                'average_participation': 0,
                'last_activity': application_data['applied_at']
            }
        
        channel_data = self.analytics_data['channel_performance'][channel_id]
        channel_data['total_applications'] += 1
        channel_data['unique_users'].add(application_data['user_id'])
        channel_data['last_activity'] = application_data['applied_at']
        
        # 평균 참여도 계산
        channel_data['average_participation'] = len(channel_data['unique_users'])
    
    def _update_trends(self, current_time: datetime, application_data: Dict):
        """트렌드 데이터를 업데이트합니다."""
        week_key = current_time.strftime("%Y-W%W")
        
        if week_key not in self.analytics_data['trends']:
            self.analytics_data['trends'][week_key] = {
                'applications': 0,
                'unique_users': set(),
                'growth_rate': 0
            }
        
        trend_data = self.analytics_data['trends'][week_key]
        trend_data['applications'] += 1
        trend_data['unique_users'].add(application_data['user_id'])
    
    def get_monthly_statistics(self, month: str = None) -> Dict:
        """월별 통계를 반환합니다."""
        if month is None:
            month = datetime.now(pytz.timezone(self.settings.timezone)).strftime("%Y-%m")
        
        if month not in self.analytics_data['monthly_stats']:
            return {'error': '해당 월의 데이터가 없습니다.'}
        
        stats = self.analytics_data['monthly_stats'][month]
        
        # set을 list로 변환 (JSON 직렬화를 위해)
        return {
            'month': month,
            'total_applications': stats['total_applications'],
            'unique_users': len(stats['unique_users']),
            'popular_dates': dict(stats['popular_dates'].most_common(10)),
            'top_channels': dict(stats['channels'].most_common(5)),
            'application_times': len(stats['application_times'])
        }
    
    def get_user_participation_stats(self, user_id: int = None) -> Dict:
        """사용자 참여도 통계를 반환합니다."""
        if user_id is None:
            # 전체 사용자 통계
            total_users = len(self.analytics_data['user_participation'])
            if total_users == 0:
                return {'error': '사용자 데이터가 없습니다.'}
            
            all_applications = [user_data['total_applications'] 
                              for user_data in self.analytics_data['user_participation'].values()]
            
            return {
                'total_users': total_users,
                'average_applications': sum(all_applications) / len(all_applications),
                'most_active_users': self._get_most_active_users(5),
                'participation_distribution': self._get_participation_distribution()
            }
        else:
            # 특정 사용자 통계
            user_id_str = str(user_id)
            if user_id_str not in self.analytics_data['user_participation']:
                return {'error': '해당 사용자의 데이터가 없습니다.'}
            
            user_data = self.analytics_data['user_participation'][user_id_str]
            
            return {
                'user_id': user_id,
                'total_applications': user_data['total_applications'],
                'first_application': user_data['first_application'],
                'last_application': user_data['last_application'],
                'preferred_dates': dict(user_data['preferred_dates'].most_common(5)),
                'application_months': len(user_data['application_months'])
            }
    
    def get_popular_times_analysis(self) -> Dict:
        """인기 시간대 분석을 반환합니다."""
        hourly_data = self.analytics_data['popular_times'].get('hourly', Counter())
        daily_data = self.analytics_data['popular_times'].get('daily', Counter())
        
        return {
            'peak_hours': dict(hourly_data.most_common(5)),
            'peak_days': dict(daily_data.most_common(7)),
            'hourly_distribution': dict(hourly_data),
            'daily_distribution': dict(daily_data)
        }
    
    def get_channel_performance_analysis(self) -> Dict:
        """채널별 성과 분석을 반환합니다."""
        channel_data = self.analytics_data['channel_performance']
        
        if not channel_data:
            return {'error': '채널 데이터가 없습니다.'}
        
        # 채널별 성과 정렬
        sorted_channels = sorted(
            channel_data.items(),
            key=lambda x: x[1]['total_applications'],
            reverse=True
        )
        
        return {
            'top_channels': [
                {
                    'channel_id': channel_id,
                    'total_applications': data['total_applications'],
                    'unique_users': len(data['unique_users']),
                    'average_participation': data['average_participation'],
                    'last_activity': data['last_activity']
                }
                for channel_id, data in sorted_channels[:10]
            ],
            'total_channels': len(channel_data),
            'average_applications_per_channel': sum(
                data['total_applications'] for data in channel_data.values()
            ) / len(channel_data)
        }
    
    def get_trend_analysis(self, weeks: int = 8) -> Dict:
        """트렌드 분석을 반환합니다."""
        current_time = datetime.now(pytz.timezone(self.settings.timezone))
        trends = []
        
        for i in range(weeks):
            week_date = current_time - timedelta(weeks=i)
            week_key = week_date.strftime("%Y-W%W")
            
            if week_key in self.analytics_data['trends']:
                trend_data = self.analytics_data['trends'][week_key]
                trends.append({
                    'week': week_key,
                    'applications': trend_data['applications'],
                    'unique_users': len(trend_data['unique_users'])
                })
        
        if not trends:
            return {'error': '트렌드 데이터가 없습니다.'}
        
        # 성장률 계산
        if len(trends) > 1:
            current_week = trends[0]['applications']
            previous_week = trends[1]['applications']
            growth_rate = ((current_week - previous_week) / previous_week * 100) if previous_week > 0 else 0
        else:
            growth_rate = 0
        
        return {
            'recent_trends': trends,
            'growth_rate': round(growth_rate, 2),
            'average_applications_per_week': sum(t['applications'] for t in trends) / len(trends)
        }
    
    def _get_most_active_users(self, limit: int = 5) -> List[Dict]:
        """가장 활발한 사용자 목록을 반환합니다."""
        sorted_users = sorted(
            self.analytics_data['user_participation'].items(),
            key=lambda x: x[1]['total_applications'],
            reverse=True
        )
        
        return [
            {
                'user_id': user_id,
                'total_applications': user_data['total_applications'],
                'last_application': user_data['last_application']
            }
            for user_id, user_data in sorted_users[:limit]
        ]
    
    def _get_participation_distribution(self) -> Dict:
        """참여도 분포를 반환합니다."""
        applications_count = [user_data['total_applications'] 
                            for user_data in self.analytics_data['user_participation'].values()]
        
        if not applications_count:
            return {}
        
        return {
            'low_participation': len([c for c in applications_count if c <= 1]),
            'medium_participation': len([c for c in applications_count if 2 <= c <= 5]),
            'high_participation': len([c for c in applications_count if c > 5])
        }
    
    def generate_comprehensive_report(self) -> Dict:
        """종합 분석 보고서를 생성합니다."""
        current_month = datetime.now(pytz.timezone(self.settings.timezone)).strftime("%Y-%m")
        
        return {
            'report_generated_at': datetime.now(pytz.timezone(self.settings.timezone)).isoformat(),
            'monthly_stats': self.get_monthly_statistics(current_month),
            'user_participation': self.get_user_participation_stats(),
            'popular_times': self.get_popular_times_analysis(),
            'channel_performance': self.get_channel_performance_analysis(),
            'trends': self.get_trend_analysis(),
            'insights': self._generate_insights()
        }
    
    def _generate_insights(self) -> List[str]:
        """데이터 기반 인사이트를 생성합니다."""
        insights = []
        
        # 인기 시간대 분석
        popular_times = self.get_popular_times_analysis()
        peak_hours = popular_times.get('peak_hours', {})
        if peak_hours:
            most_popular_hour = max(peak_hours.items(), key=lambda x: x[1])
            insights.append(f"가장 인기 있는 신청 시간: {most_popular_hour[0]}시 ({most_popular_hour[1]}건)")
        
        # 참여도 분석
        user_stats = self.get_user_participation_stats()
        if 'average_applications' in user_stats:
            avg_apps = user_stats['average_applications']
            insights.append(f"평균 사용자 신청 횟수: {avg_apps:.1f}회")
        
        # 트렌드 분석
        trends = self.get_trend_analysis()
        if 'growth_rate' in trends:
            growth = trends['growth_rate']
            if growth > 0:
                insights.append(f"신청 증가율: +{growth}% (전주 대비)")
            elif growth < 0:
                insights.append(f"신청 감소율: {growth}% (전주 대비)")
            else:
                insights.append("신청 건수 안정적 (전주 대비 변화 없음)")
        
        return insights
    
    def cleanup_old_data(self, months_to_keep: int = 12):
        """오래된 데이터를 정리합니다."""
        current_time = datetime.now(pytz.timezone(self.settings.timezone))
        cutoff_date = current_time - timedelta(days=months_to_keep * 30)
        
        # 월별 통계 정리
        months_to_remove = []
        for month_key in self.analytics_data['monthly_stats']:
            try:
                month_date = datetime.strptime(month_key, "%Y-%m")
                if month_date < cutoff_date:
                    months_to_remove.append(month_key)
            except ValueError:
                continue
        
        for month in months_to_remove:
            del self.analytics_data['monthly_stats'][month]
        
        # 트렌드 데이터 정리
        weeks_to_remove = []
        for week_key in self.analytics_data['trends']:
            try:
                year, week = week_key.split('-W')
                week_date = datetime.strptime(f"{year}-W{week}-1", "%Y-W%W-%w")
                if week_date < cutoff_date:
                    weeks_to_remove.append(week_key)
            except ValueError:
                continue
        
        for week in weeks_to_remove:
            del self.analytics_data['trends'][week]
        
        if months_to_remove or weeks_to_remove:
            self._save_data()
            self.logger.info(f"오래된 분석 데이터 정리 완료: {len(months_to_remove)}개월, {len(weeks_to_remove)}주") 