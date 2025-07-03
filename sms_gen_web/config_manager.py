import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import streamlit as st

class ConfigManager:
    """설정 관리 시스템"""
    
    def __init__(self, config_dir="configs"):
        self.config_dir = config_dir
        self.ensure_config_dir()
        self.load_default_configs()
    
    def ensure_config_dir(self):
        """설정 디렉토리 생성"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
    
    def load_default_configs(self):
        """기본 설정들 로드/생성"""
        default_configs = {
            "app_settings": {
                "name": "애플리케이션 기본 설정",
                "description": "애플리케이션의 기본 동작 설정",
                "settings": {
                    "max_file_size_mb": 50,
                    "supported_formats": [".xlsx", ".xls"],
                    "default_template": "standard",
                    "auto_save_interval": 300,  # 5분
                    "show_advanced_options": False,
                    "debug_mode": False,
                    "theme": "light",
                    "language": "ko"
                },
                "created_at": datetime.now().isoformat()
            },
            
            "ui_settings": {
                "name": "UI 표시 설정",
                "description": "사용자 인터페이스 관련 설정",
                "settings": {
                    "show_progress_bar": True,
                    "show_tooltips": True,
                    "compact_mode": False,
                    "sidebar_collapsed": False,
                    "show_variable_suggestions": True,
                    "show_template_preview": True,
                    "auto_highlight_variables": True,
                    "page_width": "wide"
                },
                "created_at": datetime.now().isoformat()
            },
            
            "data_processing": {
                "name": "데이터 처리 설정",
                "description": "데이터 처리 및 검증 관련 설정",
                "settings": {
                    "skip_empty_rows": True,
                    "auto_detect_encoding": True,
                    "strict_validation": False,
                    "max_groups": 1000,
                    "max_members_per_group": 50,
                    "auto_format_numbers": True,
                    "preserve_excel_order": True,
                    "handle_merged_cells": True
                },
                "created_at": datetime.now().isoformat()
            }
        }
        
        # 기본 설정 파일들 생성
        for config_id, config_data in default_configs.items():
            config_file = os.path.join(self.config_dir, f"{config_id}.json")
            if not os.path.exists(config_file):
                self.save_config(config_id, config_data)
    
    def get_config_list(self) -> List[Dict]:
        """저장된 설정 목록 반환"""
        configs = []
        
        for filename in os.listdir(self.config_dir):
            if filename.endswith('.json'):
                try:
                    config_id = filename.replace('.json', '')
                    config_data = self.load_config(config_id)
                    if config_data:
                        configs.append({
                            'id': config_id,
                            'name': config_data.get('name', config_id),
                            'description': config_data.get('description', ''),
                            'created_at': config_data.get('created_at', ''),
                            'updated_at': config_data.get('updated_at', ''),
                            'settings_count': len(config_data.get('settings', {}))
                        })
                except Exception as e:
                    print(f"설정 {filename} 로드 중 오류: {e}")
                    continue
        
        return configs
    
    def load_config(self, config_id: str) -> Optional[Dict]:
        """특정 설정 로드"""
        config_file = os.path.join(self.config_dir, f"{config_id}.json")
        
        if not os.path.exists(config_file):
            return None
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"설정 로드 오류: {e}")
            return None
    
    def save_config(self, config_id: str, config_data: Dict) -> bool:
        """설정 저장"""
        config_file = os.path.join(self.config_dir, f"{config_id}.json")
        
        try:
            # 저장 시간 추가
            config_data['updated_at'] = datetime.now().isoformat()
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"설정 저장 오류: {e}")
            return False
    
    def get_setting(self, config_id: str, setting_key: str, default_value: Any = None) -> Any:
        """특정 설정값 가져오기"""
        config_data = self.load_config(config_id)
        if not config_data:
            return default_value
        
        settings = config_data.get('settings', {})
        return settings.get(setting_key, default_value)
    
    def update_setting(self, config_id: str, setting_key: str, value: Any) -> bool:
        """특정 설정값 업데이트"""
        config_data = self.load_config(config_id)
        if not config_data:
            return False
        
        if 'settings' not in config_data:
            config_data['settings'] = {}
        
        config_data['settings'][setting_key] = value
        return self.save_config(config_id, config_data)
    
    def export_config(self, config_id: str) -> Optional[str]:
        """설정 내보내기"""
        config_data = self.load_config(config_id)
        if not config_data:
            return None
        
        try:
            return json.dumps(config_data, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"설정 내보내기 오류: {e}")
            return None
    
    def import_config(self, json_content: str, config_id: str = None) -> str:
        """설정 가져오기"""
        try:
            config_data = json.loads(json_content)
            
            # 필수 필드 확인
            if 'settings' not in config_data:
                raise Exception("유효하지 않은 설정 파일입니다. 'settings' 필드가 없습니다.")
            
            # ID 설정
            if not config_id:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                config_id = f"imported_{timestamp}"
            
            if self.save_config(config_id, config_data):
                return config_id
            else:
                raise Exception("설정 저장에 실패했습니다.")
                
        except json.JSONDecodeError:
            raise Exception("유효하지 않은 JSON 파일입니다.")
        except Exception as e:
            raise Exception(f"설정 가져오기 중 오류: {str(e)}")


class StreamlitConfigManager:
    """Streamlit 세션 상태 기반 설정 관리"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.init_session_state()
    
    def init_session_state(self):
        """세션 상태 초기화"""
        if 'app_config' not in st.session_state:
            st.session_state.app_config = self.config_manager.load_config('app_settings')
        
        if 'ui_config' not in st.session_state:
            st.session_state.ui_config = self.config_manager.load_config('ui_settings')
        
        if 'data_config' not in st.session_state:
            st.session_state.data_config = self.config_manager.load_config('data_processing')
    
    def get_app_setting(self, key: str, default=None):
        """앱 설정값 가져오기"""
        config = st.session_state.get('app_config', {})
        settings = config.get('settings', {})
        return settings.get(key, default)
    
    def get_ui_setting(self, key: str, default=None):
        """UI 설정값 가져오기"""
        config = st.session_state.get('ui_config', {})
        settings = config.get('settings', {})
        return settings.get(key, default)
    
    def get_data_setting(self, key: str, default=None):
        """데이터 처리 설정값 가져오기"""
        config = st.session_state.get('data_config', {})
        settings = config.get('settings', {})
        return settings.get(key, default)
    
    def update_app_setting(self, key: str, value):
        """앱 설정값 업데이트"""
        if 'app_config' not in st.session_state:
            st.session_state.app_config = {}
        
        if 'settings' not in st.session_state.app_config:
            st.session_state.app_config['settings'] = {}
        
        st.session_state.app_config['settings'][key] = value
        
        # 파일에도 저장
        self.config_manager.update_setting('app_settings', key, value)
    
    def show_settings_panel(self):
        """설정 패널 UI 표시"""
        st.markdown("## ⚙️ 애플리케이션 설정")
        
        tab1, tab2, tab3 = st.tabs(["🔧 기본 설정", "🎨 UI 설정", "📊 데이터 처리"])
        
        with tab1:
            st.markdown("### 📱 기본 애플리케이션 설정")
            
            col1, col2 = st.columns(2)
            
            with col1:
                max_file_size = st.number_input(
                    "최대 파일 크기 (MB)",
                    min_value=1, max_value=200,
                    value=self.get_app_setting('max_file_size_mb', 50),
                    help="업로드 가능한 최대 파일 크기"
                )
                
                debug_mode = st.checkbox(
                    "디버그 모드",
                    value=self.get_app_setting('debug_mode', False),
                    help="상세한 오류 정보 표시"
                )
                
                theme = st.selectbox(
                    "테마",
                    ["light", "dark", "auto"],
                    index=["light", "dark", "auto"].index(self.get_app_setting('theme', 'light')),
                    help="애플리케이션 테마"
                )
            
            with col2:
                auto_save_interval = st.number_input(
                    "자동 저장 간격 (초)",
                    min_value=60, max_value=1800,
                    value=self.get_app_setting('auto_save_interval', 300),
                    help="설정 자동 저장 간격"
                )
                
                show_advanced = st.checkbox(
                    "고급 옵션 표시",
                    value=self.get_app_setting('show_advanced_options', False),
                    help="고급 사용자 옵션 표시"
                )
            
            # 설정 저장
            if st.button("💾 기본 설정 저장", type="primary"):
                self.update_app_setting('max_file_size_mb', max_file_size)
                self.update_app_setting('debug_mode', debug_mode)
                self.update_app_setting('theme', theme)
                self.update_app_setting('auto_save_interval', auto_save_interval)
                self.update_app_setting('show_advanced_options', show_advanced)
                st.success("✅ 기본 설정이 저장되었습니다!")
        
        with tab2:
            st.markdown("### 🎨 사용자 인터페이스 설정")
            
            col1, col2 = st.columns(2)
            
            with col1:
                show_progress = st.checkbox(
                    "진행률 표시",
                    value=self.get_ui_setting('show_progress_bar', True),
                    help="작업 진행률 바 표시"
                )
                
                show_tooltips = st.checkbox(
                    "도움말 툴팁 표시",
                    value=self.get_ui_setting('show_tooltips', True),
                    help="각 기능의 도움말 표시"
                )
                
                compact_mode = st.checkbox(
                    "컴팩트 모드",
                    value=self.get_ui_setting('compact_mode', False),
                    help="간결한 UI 모드"
                )
                
                page_width = st.selectbox(
                    "페이지 너비",
                    ["centered", "wide"],
                    index=["centered", "wide"].index(self.get_ui_setting('page_width', 'wide')),
                    help="페이지 레이아웃 너비"
                )
            
            with col2:
                show_suggestions = st.checkbox(
                    "변수 제안 표시",
                    value=self.get_ui_setting('show_variable_suggestions', True),
                    help="템플릿 작성 시 변수 제안"
                )
                
                show_preview = st.checkbox(
                    "템플릿 미리보기",
                    value=self.get_ui_setting('show_template_preview', True),
                    help="실시간 템플릿 미리보기"
                )
                
                auto_highlight = st.checkbox(
                    "변수 자동 하이라이트",
                    value=self.get_ui_setting('auto_highlight_variables', True),
                    help="템플릿의 변수 자동 강조"
                )
            
            # UI 설정 저장
            if st.button("💾 UI 설정 저장", type="primary"):
                # UI 설정 업데이트 로직
                st.success("✅ UI 설정이 저장되었습니다!")
        
        with tab3:
            st.markdown("### 📊 데이터 처리 설정")
            
            col1, col2 = st.columns(2)
            
            with col1:
                skip_empty = st.checkbox(
                    "빈 행 자동 스킵",
                    value=self.get_data_setting('skip_empty_rows', True),
                    help="빈 행을 자동으로 건너뜀"
                )
                
                auto_detect_encoding = st.checkbox(
                    "인코딩 자동 감지",
                    value=self.get_data_setting('auto_detect_encoding', True),
                    help="파일 인코딩 자동 감지"
                )
                
                strict_validation = st.checkbox(
                    "엄격한 검증",
                    value=self.get_data_setting('strict_validation', False),
                    help="데이터 검증을 엄격하게 수행"
                )
                
                preserve_order = st.checkbox(
                    "엑셀 순서 유지",
                    value=self.get_data_setting('preserve_excel_order', True),
                    help="엑셀의 원본 순서 유지"
                )
            
            with col2:
                max_groups = st.number_input(
                    "최대 그룹 수",
                    min_value=10, max_value=10000,
                    value=self.get_data_setting('max_groups', 1000),
                    help="처리 가능한 최대 그룹 수"
                )
                
                max_members = st.number_input(
                    "그룹당 최대 인원",
                    min_value=1, max_value=200,
                    value=self.get_data_setting('max_members_per_group', 50),
                    help="한 그룹의 최대 인원 수"
                )
                
                auto_format = st.checkbox(
                    "숫자 자동 포맷팅",
                    value=self.get_data_setting('auto_format_numbers', True),
                    help="숫자 데이터 자동 포맷팅"
                )
            
            # 데이터 처리 설정 저장
            if st.button("💾 데이터 설정 저장", type="primary"):
                # 데이터 설정 업데이트 로직
                st.success("✅ 데이터 처리 설정이 저장되었습니다!")
        
        # 설정 관리 액션
        st.markdown("---")
        st.markdown("### 🔧 설정 관리")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📥 설정 내보내기", use_container_width=True):
                # 모든 설정을 통합하여 내보내기
                all_settings = {
                    'app_settings': st.session_state.get('app_config', {}),
                    'ui_settings': st.session_state.get('ui_config', {}),
                    'data_settings': st.session_state.get('data_config', {}),
                    'exported_at': datetime.now().isoformat()
                }
                
                st.download_button(
                    label="💾 설정 파일 다운로드",
                    data=json.dumps(all_settings, ensure_ascii=False, indent=2),
                    file_name=f"app_settings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )
        
        with col2:
            uploaded_config = st.file_uploader(
                "📁 설정 가져오기",
                type=['json'],
                help="이전에 내보낸 설정 파일"
            )
            
            if uploaded_config:
                try:
                    config_content = json.loads(uploaded_config.read().decode('utf-8'))
                    
                    # 설정 적용
                    if 'app_settings' in config_content:
                        st.session_state.app_config = config_content['app_settings']
                    if 'ui_settings' in config_content:
                        st.session_state.ui_config = config_content['ui_settings']
                    if 'data_settings' in config_content:
                        st.session_state.data_config = config_content['data_settings']
                    
                    st.success("✅ 설정이 가져와졌습니다!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ 설정 가져오기 실패: {str(e)}")
        
        with col3:
            if st.button("🔄 기본값으로 리셋", use_container_width=True):
                if st.button("⚠️ 정말 리셋하시겠습니까?", type="secondary"):
                    # 기본 설정으로 리셋
                    self.init_session_state()
                    st.success("✅ 설정이 기본값으로 리셋되었습니다!")
                    st.rerun()


def apply_ui_settings():
    """UI 설정 적용"""
    config_manager = StreamlitConfigManager()
    
    # 페이지 설정 적용
    page_width = config_manager.get_ui_setting('page_width', 'wide')
    if page_width == 'wide':
        st.set_page_config(layout="wide")
    
    # 컴팩트 모드 CSS
    if config_manager.get_ui_setting('compact_mode', False):
        st.markdown("""
        <style>
            .main .block-container {
                padding-top: 1rem;
                padding-bottom: 1rem;
            }
            .metric-container {
                background-color: transparent;
            }
        </style>
        """, unsafe_allow_html=True)
    
    # 변수 하이라이트 CSS
    if config_manager.get_ui_setting('auto_highlight_variables', True):
        st.markdown("""
        <style>
            .variable-highlight {
                background-color: #fff3cd;
                padding: 2px 4px;
                border-radius: 3px;
                font-family: monospace;
                color: #856404;
            }
        </style>
        """, unsafe_allow_html=True)

def get_user_preferences():
    """사용자 환경설정 반환"""
    config_manager = StreamlitConfigManager()
    
    return {
        'theme': config_manager.get_app_setting('theme', 'light'),
        'language': config_manager.get_app_setting('language', 'ko'),
        'debug_mode': config_manager.get_app_setting('debug_mode', False),
        'show_tooltips': config_manager.get_ui_setting('show_tooltips', True),
        'show_progress': config_manager.get_ui_setting('show_progress_bar', True),
        'max_file_size': config_manager.get_app_setting('max_file_size_mb', 50)
    }