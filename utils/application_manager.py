"""
스케줄 신청 현황 관리 시스템.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import pytz

class ApplicationManager:
    """스케줄 신청 현황을 관리합니다."""
    
    def __init__(self, settings, data_file: str = "config/applications.json"):
        """신청 관리자를 초기화합니다."""
        self.settings = settings
        self.data_file = data_file
        self.logger = logging.getLogger(__name__)
        
        # 신청 데이터 구조
        self.applications = {}  # {message_id: {applications: [], deadline: str, channel_id: int}}
        self.user_applications = {}  # {user_id: {message_id: str, applied_date: str}}
        
        # 데이터 로드
        self._load_data()
    
    def _load_data(self):
        """신청 데이터를 파일에서 로드합니다."""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.applications = data.get('applications', {})
                self.user_applications = data.get('user_applications', {})
            self.logger.info("신청 데이터 로드 완료")
        except FileNotFoundError:
            self.logger.info("신청 데이터 파일이 없습니다. 새로 생성합니다.")
            self._save_data()
        except Exception as e:
            self.logger.error(f"신청 데이터 로드 실패: {e}")
            self.applications = {}
            self.user_applications = {}
    
    def _save_data(self):
        """신청 데이터를 파일에 저장합니다."""
        try:
            data = {
                'applications': self.applications,
                'user_applications': self.user_applications
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.debug("신청 데이터 저장 완료")
        except Exception as e:
            self.logger.error(f"신청 데이터 저장 실패: {e}")
    
    def create_application_session(self, message_id: str, channel_id: int, deadline_days: int = 5):
        """새로운 신청 세션을 생성합니다."""
        deadline = datetime.now(pytz.timezone(self.settings.timezone)) + timedelta(days=deadline_days)
        
        self.applications[message_id] = {
            'applications': [],
            'deadline': deadline.isoformat(),
            'channel_id': channel_id,
            'created_at': datetime.now(pytz.timezone(self.settings.timezone)).isoformat(),
            'status': 'active'
        }
        
        self._save_data()
        self.logger.info(f"신청 세션 생성: 메시지 ID {message_id}, 마감일 {deadline.strftime('%Y-%m-%d %H:%M')}")
    
    def add_application(self, message_id: str, user_id: int, user_name: str, 
                       requested_dates: List[str], additional_info: str = "") -> Dict:
        """신청을 추가합니다."""
        if message_id not in self.applications:
            return {'success': False, 'error': '유효하지 않은 신청 세션입니다.'}
        
        # 마감일 확인
        deadline = datetime.fromisoformat(self.applications[message_id]['deadline'])
        if datetime.now(pytz.timezone(self.settings.timezone)) > deadline:
            return {'success': False, 'error': '신청 기간이 마감되었습니다.'}
        
        # 중복 신청 확인
        if str(user_id) in self.user_applications:
            existing = self.user_applications[str(user_id)]
            if existing.get('message_id') == message_id:
                return {'success': False, 'error': '이미 신청하셨습니다.'}
        
        # 신청 추가
        application = {
            'user_id': user_id,
            'user_name': user_name,
            'requested_dates': requested_dates,
            'additional_info': additional_info,
            'applied_at': datetime.now(pytz.timezone(self.settings.timezone)).isoformat()
        }
        
        self.applications[message_id]['applications'].append(application)
        
        # 사용자 신청 기록
        self.user_applications[str(user_id)] = {
            'message_id': message_id,
            'applied_date': application['applied_at']
        }
        
        self._save_data()
        
        self.logger.info(f"신청 추가: 사용자 {user_name} ({user_id}), 메시지 {message_id}")
        
        return {
            'success': True,
            'application': application,
            'total_applications': len(self.applications[message_id]['applications'])
        }
    
    def get_applications_summary(self, message_id: str) -> Dict:
        """신청 현황 요약을 반환합니다."""
        if message_id not in self.applications:
            return {'error': '유효하지 않은 신청 세션입니다.'}
        
        session = self.applications[message_id]
        applications = session['applications']
        
        # 날짜별 신청 현황
        date_counts = {}
        for app in applications:
            for date in app['requested_dates']:
                date_counts[date] = date_counts.get(date, 0) + 1
        
        # 중복 신청이 많은 날짜
        popular_dates = [date for date, count in date_counts.items() if count > 1]
        
        return {
            'total_applications': len(applications),
            'unique_applicants': len(set(app['user_id'] for app in applications)),
            'date_counts': date_counts,
            'popular_dates': popular_dates,
            'deadline': session['deadline'],
            'applications': applications
        }
    
    def close_application_session(self, message_id: str) -> Dict:
        """신청 세션을 마감합니다."""
        if message_id not in self.applications:
            return {'success': False, 'error': '유효하지 않은 신청 세션입니다.'}
        
        self.applications[message_id]['status'] = 'closed'
        self.applications[message_id]['closed_at'] = datetime.now(pytz.timezone(self.settings.timezone)).isoformat()
        
        self._save_data()
        
        summary = self.get_applications_summary(message_id)
        self.logger.info(f"신청 세션 마감: 메시지 ID {message_id}, 총 신청 {summary['total_applications']}건")
        
        return {'success': True, 'summary': summary}
    
    def get_user_application(self, user_id: int) -> Optional[Dict]:
        """사용자의 신청 정보를 반환합니다."""
        user_id_str = str(user_id)
        if user_id_str not in self.user_applications:
            return None
        
        user_app = self.user_applications[user_id_str]
        message_id = user_app['message_id']
        
        if message_id not in self.applications:
            return None
        
        # 사용자의 신청 찾기
        for app in self.applications[message_id]['applications']:
            if app['user_id'] == user_id:
                return {
                    'application': app,
                    'session_info': self.applications[message_id]
                }
        
        return None
    
    def cleanup_old_sessions(self, days: int = 30):
        """오래된 신청 세션을 정리합니다."""
        cutoff_date = datetime.now(pytz.timezone(self.settings.timezone)) - timedelta(days=days)
        
        to_remove = []
        for message_id, session in self.applications.items():
            created_at = datetime.fromisoformat(session['created_at'])
            if created_at < cutoff_date:
                to_remove.append(message_id)
        
        for message_id in to_remove:
            del self.applications[message_id]
        
        # 사용자 신청 기록도 정리
        to_remove_users = []
        for user_id, user_app in self.user_applications.items():
            if user_app['message_id'] in to_remove:
                to_remove_users.append(user_id)
        
        for user_id in to_remove_users:
            del self.user_applications[user_id]
        
        if to_remove:
            self._save_data()
            self.logger.info(f"오래된 신청 세션 {len(to_remove)}개 정리 완료")
    
    def get_active_sessions(self) -> List[Dict]:
        """활성 신청 세션 목록을 반환합니다."""
        active_sessions = []
        for message_id, session in self.applications.items():
            if session.get('status') == 'active':
                summary = self.get_applications_summary(message_id)
                active_sessions.append({
                    'message_id': message_id,
                    'channel_id': session['channel_id'],
                    'created_at': session['created_at'],
                    'deadline': session['deadline'],
                    'summary': summary
                })
        
        return active_sessions 