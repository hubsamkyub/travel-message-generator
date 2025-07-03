import logging
import traceback
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import streamlit as st
import pandas as pd

class ErrorHandler:
    """통합 에러 처리 시스템"""
    
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        self.ensure_log_dir()
        self.setup_logging()
        self.error_messages = {
            'ko': self.get_korean_messages(),
            'en': self.get_english_messages()
        }
    
    def ensure_log_dir(self):
        """로그 디렉토리 생성"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def setup_logging(self):
        """로깅 설정"""
        # 로그 파일명
        log_filename = os.path.join(
            self.log_dir, 
            f"app_{datetime.now().strftime('%Y%m%d')}.log"
        )
        
        # 로거 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('TravelMessageGenerator')
    
    def get_korean_messages(self) -> Dict[str, str]:
        """한국어 에러 메시지"""
        return {
            'file_upload_error': '파일 업로드 중 오류가 발생했습니다.',
            'file_format_error': '지원하지 않는 파일 형식입니다.',
            'file_size_error': '파일 크기가 너무 큽니다.',
            'file_corrupted': '파일이 손상되었거나 열 수 없습니다.',
            'permission_error': '파일에 접근할 권한이 없습니다.',
            'memory_error': '메모리가 부족합니다. 더 작은 파일을 사용해주세요.',
            'template_error': '템플릿 처리 중 오류가 발생했습니다.',
            'variable_error': '템플릿 변수 오류입니다.',
            'mapping_error': '매핑 설정에 오류가 있습니다.',
            'data_processing_error': '데이터 처리 중 오류가 발생했습니다.',
            'network_error': '네트워크 연결에 문제가 있습니다.',
            'session_expired': '세션이 만료되었습니다.',
            'validation_error': '데이터 검증에 실패했습니다.',
            'encoding_error': '파일 인코딩 오류입니다.',
            'unknown_error': '알 수 없는 오류가 발생했습니다.'
        }
    
    def get_english_messages(self) -> Dict[str, str]:
        """영어 에러 메시지"""
        return {
            'file_upload_error': 'An error occurred while uploading the file.',
            'file_format_error': 'Unsupported file format.',
            'file_size_error': 'File size is too large.',
            'file_corrupted': 'File is corrupted or cannot be opened.',
            'permission_error': 'Permission denied to access the file.',
            'memory_error': 'Insufficient memory. Please use a smaller file.',
            'template_error': 'An error occurred while processing the template.',
            'variable_error': 'Template variable error.',
            'mapping_error': 'There is an error in the mapping configuration.',
            'data_processing_error': 'An error occurred during data processing.',
            'network_error': 'Network connection problem.',
            'session_expired': 'Session has expired.',
            'validation_error': 'Data validation failed.',
            'encoding_error': 'File encoding error.',
            'unknown_error': 'An unknown error occurred.'
        }
    
    def classify_error(self, error: Exception) -> str:
        """에러 분류"""
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        # 파일 관련 에러
        if isinstance(error, FileNotFoundError):
            return 'file_upload_error'
        elif isinstance(error, PermissionError):
            return 'permission_error'
        elif isinstance(error, MemoryError):
            return 'memory_error'
        elif 'encoding' in error_message or 'codec' in error_message:
            return 'encoding_error'
        elif 'corrupted' in error_message or 'invalid' in error_message:
            return 'file_corrupted'
        
        # 템플릿 관련 에러
        elif isinstance(error, KeyError) and '{' in str(error):
            return 'variable_error'
        elif 'template' in error_message:
            return 'template_error'
        
        # 데이터 처리 에러
        elif isinstance(error, ValueError) and 'mapping' in error_message:
            return 'mapping_error'
        elif isinstance(error, ValueError):
            return 'validation_error'
        elif 'data' in error_message or 'dataframe' in error_message:
            return 'data_processing_error'
        
        # 네트워크 에러
        elif 'network' in error_message or 'connection' in error_message:
            return 'network_error'
        
        # 기타
        else:
            return 'unknown_error'
    
    def get_error_message(self, error_type: str, language: str = 'ko') -> str:
        """에러 메시지 가져오기"""
        messages = self.error_messages.get(language, self.error_messages['ko'])
        return messages.get(error_type, messages['unknown_error'])
    
    def get_solution_suggestions(self, error_type: str, language: str = 'ko') -> List[str]:
        """해결 방법 제안"""
        if language == 'ko':
            solutions = {
                'file_upload_error': [
                    '파일이 다른 프로그램에서 열려있지 않은지 확인하세요.',
                    '파일 경로에 특수문자가 없는지 확인하세요.',
                    '브라우저를 새로고침한 후 다시 시도하세요.'
                ],
                'file_format_error': [
                    '.xlsx 또는 .xls 형식의 파일만 지원됩니다.',
                    '파일을 Excel에서 다시 저장해보세요.',
                    '파일 확장자가 올바른지 확인하세요.'
                ],
                'file_size_error': [
                    '파일 크기를 50MB 이하로 줄여주세요.',
                    '불필요한 시트나 데이터를 제거해보세요.',
                    '데이터를 여러 파일로 나누어 처리하세요.'
                ],
                'variable_error': [
                    '템플릿의 변수명이 올바른지 확인하세요.',
                    '매핑 설정에서 해당 변수가 연결되었는지 확인하세요.',
                    '변수명에 특수문자가 없는지 확인하세요.'
                ],
                'mapping_error': [
                    '필수 컬럼(팀명, 발송그룹, 이름)이 매핑되었는지 확인하세요.',
                    '엑셀 파일의 컬럼명이 정확한지 확인하세요.',
                    '헤더 행 번호가 올바른지 확인하세요.'
                ],
                'data_processing_error': [
                    '엑셀 데이터에 빈 행이나 잘못된 값이 없는지 확인하세요.',
                    '필수 데이터가 모두 입력되었는지 확인하세요.',
                    '데이터 형식이 일관성 있는지 확인하세요.'
                ],
                'memory_error': [
                    '더 작은 파일로 테스트해보세요.',
                    '브라우저 탭을 정리하고 다시 시도하세요.',
                    '불필요한 프로그램을 종료하고 다시 시도하세요.'
                ],
                'encoding_error': [
                    '파일을 UTF-8 인코딩으로 저장해보세요.',
                    'Excel에서 "CSV UTF-8"로 저장 후 다시 xlsx로 변환해보세요.',
                    '한글이 포함된 파일명을 영문으로 변경해보세요.'
                ]
            }
        else:
            solutions = {
                'file_upload_error': [
                    'Make sure the file is not open in another program.',
                    'Check if there are special characters in the file path.',
                    'Refresh the browser and try again.'
                ],
                'file_format_error': [
                    'Only .xlsx or .xls format files are supported.',
                    'Try saving the file again in Excel.',
                    'Check if the file extension is correct.'
                ],
                'variable_error': [
                    'Check if the variable names in the template are correct.',
                    'Verify that the variable is mapped in the mapping settings.',
                    'Check if there are special characters in variable names.'
                ]
            }
        
        return solutions.get(error_type, [])
    
    def handle_error(self, error: Exception, context: str = "", language: str = 'ko') -> Dict[str, Any]:
        """에러 처리 메인 함수"""
        # 에러 로깅
        self.logger.error(f"Error in {context}: {str(error)}", exc_info=True)
        
        # 에러 분류
        error_type = self.classify_error(error)
        
        # 에러 정보 구성
        error_info = {
            'error_type': error_type,
            'original_error': str(error),
            'error_class': type(error).__name__,
            'context': context,
            'timestamp': datetime.now().isoformat(),
            'message': self.get_error_message(error_type, language),
            'solutions': self.get_solution_suggestions(error_type, language),
            'traceback': traceback.format_exc() if st.session_state.get('debug_mode', False) else None
        }
        
        return error_info
    
    def show_error_in_streamlit(self, error_info: Dict[str, Any]):
        """Streamlit에서 에러 표시"""
        st.error(f"❌ {error_info['message']}")
        
        # 해결 방법 표시
        if error_info['solutions']:
            with st.expander("💡 해결 방법", expanded=True):
                for i, solution in enumerate(error_info['solutions'], 1):
                    st.write(f"{i}. {solution}")
        
        # 디버그 모드에서 상세 정보 표시
        if error_info.get('traceback') and st.session_state.get('debug_mode', False):
            with st.expander("🔧 상세 오류 정보 (개발자용)", expanded=False):
                st.code(error_info['traceback'])
                st.json({
                    'error_type': error_info['error_type'],
                    'error_class': error_info['error_class'],
                    'context': error_info['context'],
                    'timestamp': error_info['timestamp']
                })
    
    def log_user_action(self, action: str, details: Dict[str, Any] = None):
        """사용자 액션 로깅"""
        log_entry = {
            'action': action,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        
        self.logger.info(f"User action: {action} - {details}")
    
    def get_error_statistics(self, days: int = 7) -> Dict[str, Any]:
        """에러 통계 조회"""
        log_file = os.path.join(
            self.log_dir, 
            f"app_{datetime.now().strftime('%Y%m%d')}.log"
        )
        
        if not os.path.exists(log_file):
            return {'total_errors': 0, 'error_types': {}}
        
        stats = {
            'total_errors': 0,
            'error_types': {},
            'recent_errors': []
        }
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
                for line in lines:
                    if 'ERROR' in line:
                        stats['total_errors'] += 1
                        
                        # 최근 에러 기록
                        if len(stats['recent_errors']) < 10:
                            stats['recent_errors'].append(line.strip())
        
        except Exception as e:
            self.logger.error(f"Error reading log file: {e}")
        
        return stats


class StreamlitErrorHandler:
    """Streamlit 전용 에러 처리"""
    
    def __init__(self):
        self.error_handler = ErrorHandler()
        self.setup_global_error_handling()
    
    def setup_global_error_handling(self):
        """전역 에러 처리 설정"""
        # 세션 상태에 에러 핸들러 저장
        if 'error_handler' not in st.session_state:
            st.session_state.error_handler = self.error_handler
    
    def safe_execute(self, func, *args, context="", show_error=True, **kwargs):
        """안전한 함수 실행"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_info = self.error_handler.handle_error(e, context)
            
            if show_error:
                self.error_handler.show_error_in_streamlit(error_info)
            
            return None
    
    def file_upload_wrapper(self, uploaded_file, max_size_mb=50):
        """파일 업로드 안전 래퍼"""
        if uploaded_file is None:
            return None
        
        try:
            # 파일 크기 검사
            file_size_mb = uploaded_file.size / (1024 * 1024)
            if file_size_mb > max_size_mb:
                raise ValueError(f"파일 크기가 {max_size_mb}MB를 초과합니다. (현재: {file_size_mb:.1f}MB)")
            
            # 파일 형식 검사
            if not uploaded_file.name.lower().endswith(('.xlsx', '.xls')):
                raise ValueError("지원하지 않는 파일 형식입니다. Excel 파일(.xlsx, .xls)만 지원됩니다.")
            
            return uploaded_file
            
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "파일 업로드")
            self.error_handler.show_error_in_streamlit(error_info)
            return None
    
    def excel_read_wrapper(self, file_path_or_buffer, **kwargs):
        """Excel 읽기 안전 래퍼"""
        try:
            return pd.read_excel(file_path_or_buffer, **kwargs)
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "Excel 파일 읽기")
            self.error_handler.show_error_in_streamlit(error_info)
            return None
    
    def template_format_wrapper(self, template: str, variables: Dict[str, Any]):
        """템플릿 포맷팅 안전 래퍼"""
        try:
            return template.format(**variables)
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "템플릿 처리")
            self.error_handler.show_error_in_streamlit(error_info)
            return None
    
    def show_error_dashboard(self):
        """에러 대시보드 표시"""
        st.markdown("## 🔍 에러 모니터링")
        
        stats = self.error_handler.get_error_statistics()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("총 에러 수", stats['total_errors'])
        
        with col2:
            st.metric("에러 유형 수", len(stats.get('error_types', {})))
        
        with col3:
            st.metric("최근 에러", len(stats.get('recent_errors', [])))
        
        # 최근 에러 목록
        if stats.get('recent_errors'):
            st.markdown("### 📋 최근 에러 로그")
            for i, error_log in enumerate(stats['recent_errors'][:5]):
                st.code(error_log, language='text')
        
        # 로그 파일 다운로드
        log_file = os.path.join(
            self.error_handler.log_dir,
            f"app_{datetime.now().strftime('%Y%m%d')}.log"
        )
        
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            st.download_button(
                label="📥 로그 파일 다운로드",
                data=log_content,
                file_name=f"error_log_{datetime.now().strftime('%Y%m%d')}.log",
                mime="text/plain"
            )


# 전역 에러 핸들러 인스턴스
_global_error_handler = None

def get_error_handler():
    """전역 에러 핸들러 가져오기"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = StreamlitErrorHandler()
    return _global_error_handler

def safe_execute(func, *args, context="", **kwargs):
    """전역 안전 실행 함수"""
    error_handler = get_error_handler()
    return error_handler.safe_execute(func, *args, context=context, **kwargs)

def handle_file_upload(uploaded_file, max_size_mb=50):
    """전역 파일 업로드 처리"""
    error_handler = get_error_handler()
    return error_handler.file_upload_wrapper(uploaded_file, max_size_mb)

def safe_read_excel(file_path_or_buffer, **kwargs):
    """전역 안전 Excel 읽기"""
    error_handler = get_error_handler()
    return error_handler.excel_read_wrapper(file_path_or_buffer, **kwargs)

def safe_format_template(template: str, variables: Dict[str, Any]):
    """전역 안전 템플릿 포맷팅"""
    error_handler = get_error_handler()
    return error_handler.template_format_wrapper(template, variables)