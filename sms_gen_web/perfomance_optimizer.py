import streamlit as st
import pandas as pd
import time
import hashlib
import pickle
import os
from functools import wraps
from typing import Any, Callable, Dict, Optional
import logging

class PerformanceOptimizer:
    """성능 최적화 클래스"""
    
    def __init__(self, cache_dir="cache"):
        self.cache_dir = cache_dir
        self.ensure_cache_dir()
        self.setup_logging()
    
    def ensure_cache_dir(self):
        """캐시 디렉토리 생성"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def setup_logging(self):
        """성능 로깅 설정"""
        self.perf_logger = logging.getLogger('performance')
        self.perf_logger.setLevel(logging.INFO)
        
        # 성능 로그 파일
        perf_handler = logging.FileHandler(
            os.path.join(self.cache_dir, 'performance.log'),
            encoding='utf-8'
        )
        perf_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        self.perf_logger.addHandler(perf_handler)
    
    def measure_time(self, func_name: str = None):
        """실행 시간 측정 데코레이터"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()
                
                execution_time = end_time - start_time
                name = func_name or func.__name__
                
                # 로깅
                self.perf_logger.info(f"{name} executed in {execution_time:.4f} seconds")
                
                # 느린 함수 경고 (2초 이상)
                if execution_time > 2.0:
                    self.perf_logger.warning(f"Slow function detected: {name} took {execution_time:.4f}s")
                
                return result
            return wrapper
        return decorator
    
    def cache_dataframe(self, cache_key: str, ttl_hours: int = 1):
        """DataFrame 캐싱 데코레이터"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 캐시 파일 경로
                cache_file = os.path.join(self.cache_dir, f"{cache_key}.pickle")
                
                # 캐시 확인
                if os.path.exists(cache_file):
                    # 파일 수정 시간 확인
                    file_age = time.time() - os.path.getmtime(cache_file)
                    if file_age < ttl_hours * 3600:  # TTL 체크
                        try:
                            with open(cache_file, 'rb') as f:
                                cached_data = pickle.load(f)
                            self.perf_logger.info(f"Cache hit for {cache_key}")
                            return cached_data
                        except Exception as e:
                            self.perf_logger.error(f"Cache read error for {cache_key}: {e}")
                
                # 캐시 미스 - 함수 실행
                result = func(*args, **kwargs)
                
                # 결과 캐싱
                try:
                    with open(cache_file, 'wb') as f:
                        pickle.dump(result, f)
                    self.perf_logger.info(f"Cache stored for {cache_key}")
                except Exception as e:
                    self.perf_logger.error(f"Cache write error for {cache_key}: {e}")
                
                return result
            return wrapper
        return decorator
    
    def optimize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """DataFrame 메모리 최적화"""
        if df is None or df.empty:
            return df
        
        original_memory = df.memory_usage(deep=True).sum()
        optimized_df = df.copy()
        
        # 숫자 컬럼 최적화
        for col in optimized_df.select_dtypes(include=['int64']).columns:
            col_min = optimized_df[col].min()
            col_max = optimized_df[col].max()
            
            if col_min >= 0:  # 양수만
                if col_max < 255:
                    optimized_df[col] = optimized_df[col].astype('uint8')
                elif col_max < 65535:
                    optimized_df[col] = optimized_df[col].astype('uint16')
                elif col_max < 4294967295:
                    optimized_df[col] = optimized_df[col].astype('uint32')
            else:  # 음수 포함
                if col_min > -128 and col_max < 127:
                    optimized_df[col] = optimized_df[col].astype('int8')
                elif col_min > -32768 and col_max < 32767:
                    optimized_df[col] = optimized_df[col].astype('int16')
                elif col_min > -2147483648 and col_max < 2147483647:
                    optimized_df[col] = optimized_df[col].astype('int32')
        
        # Float 컬럼 최적화
        for col in optimized_df.select_dtypes(include=['float64']).columns:
            optimized_df[col] = pd.to_numeric(optimized_df[col], downcast='float')
        
        # 문자열 컬럼 최적화
        for col in optimized_df.select_dtypes(include=['object']).columns:
            num_unique_values = len(optimized_df[col].unique())
            num_total_values = len(optimized_df[col])
            
            # 카테고리로 변환할지 결정 (유니크 값이 50% 미만인 경우)
            if num_unique_values / num_total_values < 0.5:
                optimized_df[col] = optimized_df[col].astype('category')
        
        optimized_memory = optimized_df.memory_usage(deep=True).sum()
        memory_reduction = (original_memory - optimized_memory) / original_memory * 100
        
        self.perf_logger.info(f"DataFrame optimized: {memory_reduction:.1f}% memory reduction")
        
        return optimized_df
    
    def batch_process_groups(self, group_data: Dict, batch_size: int = 100):
        """그룹 데이터 배치 처리"""
        groups = list(group_data.items())
        batches = [groups[i:i + batch_size] for i in range(0, len(groups), batch_size)]
        
        self.perf_logger.info(f"Processing {len(groups)} groups in {len(batches)} batches")
        
        return batches
    
    def lazy_load_template_variables(self, template: str):
        """템플릿 변수 지연 로딩"""
        if not hasattr(self, '_template_cache'):
            self._template_cache = {}
        
        template_hash = hashlib.md5(template.encode()).hexdigest()
        
        if template_hash not in self._template_cache:
            import re
            variables = set(re.findall(r'\{(\w+)(?::[^}]+)?\}', template))
            self._template_cache[template_hash] = variables
        
        return self._template_cache[template_hash]
    
    def preload_common_data(self):
        """공통 데이터 사전 로딩"""
        if 'preloaded_data' not in st.session_state:
            st.session_state.preloaded_data = {
                'korean_names': self._load_korean_names(),
                'bank_accounts': self._load_bank_accounts(),
                'common_templates': self._load_common_templates()
            }
    
    def _load_korean_names(self):
        """한국 이름 데이터 로딩"""
        return [
            "김민준", "이서현", "박도윤", "최서준", "정하윤", "강지우", "윤서연", "임준혁",
            "오시우", "한예준", "송지아", "안도현", "장서현", "조건우", "신지민", "홍예은"
        ]
    
    def _load_bank_accounts(self):
        """은행 계좌 데이터 로딩"""
        return [
            "국민은행 123-456-789012 (주)여행처럼",
            "신한은행 234-567-890123 (주)여행처럼",
            "우리은행 345-678-901234 (주)여행처럼"
        ]
    
    def _load_common_templates(self):
        """공통 템플릿 로딩"""
        return {
            'simple': '간단한 잔금 안내 템플릿',
            'detailed': '상세한 잔금 안내 템플릿'
        }
    
    def clear_cache(self, pattern: str = None):
        """캐시 정리"""
        cleared_files = 0
        
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.pickle'):
                if pattern is None or pattern in filename:
                    try:
                        os.remove(os.path.join(self.cache_dir, filename))
                        cleared_files += 1
                    except Exception as e:
                        self.perf_logger.error(f"Cache clear error for {filename}: {e}")
        
        self.perf_logger.info(f"Cleared {cleared_files} cache files")
        return cleared_files
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        cache_files = []
        total_size = 0
        
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.pickle'):
                filepath = os.path.join(self.cache_dir, filename)
                file_size = os.path.getsize(filepath)
                file_age = time.time() - os.path.getmtime(filepath)
                
                cache_files.append({
                    'filename': filename,
                    'size_mb': file_size / 1024 / 1024,
                    'age_hours': file_age / 3600
                })
                total_size += file_size
        
        return {
            'total_files': len(cache_files),
            'total_size_mb': total_size / 1024 / 1024,
            'files': cache_files
        }


class StreamlitPerformanceMonitor:
    """Streamlit 성능 모니터링"""
    
    def __init__(self):
        self.optimizer = PerformanceOptimizer()
        self.metrics = {}
    
    def start_monitoring(self):
        """모니터링 시작"""
        if 'performance_metrics' not in st.session_state:
            st.session_state.performance_metrics = {
                'page_loads': 0,
                'file_uploads': 0,
                'message_generations': 0,
                'errors': 0,
                'start_time': time.time()
            }
    
    def track_event(self, event_type: str, details: Dict[str, Any] = None):
        """이벤트 추적"""
        if 'performance_metrics' not in st.session_state:
            self.start_monitoring()
        
        st.session_state.performance_metrics[event_type] = \
            st.session_state.performance_metrics.get(event_type, 0) + 1
        
        self.optimizer.perf_logger.info(f"Event: {event_type}, Details: {details}")
    
    def show_performance_dashboard(self):
        """성능 대시보드 표시"""
        st.markdown("## 📊 성능 모니터링")
        
        if 'performance_metrics' not in st.session_state:
            st.info("성능 데이터가 없습니다. 애플리케이션을 사용해보세요.")
            return
        
        metrics = st.session_state.performance_metrics
        uptime = time.time() - metrics.get('start_time', time.time())
        
        # 기본 메트릭
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("업타임", f"{uptime/3600:.1f}시간")
        with col2:
            st.metric("페이지 로드", metrics.get('page_loads', 0))
        with col3:
            st.metric("파일 업로드", metrics.get('file_uploads', 0))
        with col4:
            st.metric("메시지 생성", metrics.get('message_generations', 0))
        
        # 캐시 통계
        st.markdown("### 💾 캐시 통계")
        cache_stats = self.optimizer.get_cache_stats()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("캐시 파일 수", cache_stats['total_files'])
        with col2:
            st.metric("캐시 크기", f"{cache_stats['total_size_mb']:.1f}MB")
        
        # 캐시 관리
        if st.button("🗑️ 캐시 정리"):
            cleared = self.optimizer.clear_cache()
            st.success(f"✅ {cleared}개 캐시 파일이 정리되었습니다.")
            st.rerun()
        
        # 세부 캐시 정보
        if cache_stats['files']:
            with st.expander("📋 캐시 파일 상세"):
                for file_info in cache_stats['files']:
                    st.write(f"📄 {file_info['filename']}: {file_info['size_mb']:.2f}MB, {file_info['age_hours']:.1f}시간 전")
    
    def optimize_session_state(self):
        """세션 상태 최적화"""
        # 불필요한 큰 데이터 제거
        large_keys = []
        for key, value in st.session_state.items():
            if hasattr(value, '__sizeof__'):
                size = value.__sizeof__()
                if size > 1024 * 1024:  # 1MB 이상
                    large_keys.append((key, size))
        
        if large_keys:
            self.optimizer.perf_logger.warning(f"Large session state objects: {large_keys}")
    
    def memory_usage_alert(self):
        """메모리 사용량 경고"""
        import psutil
        
        try:
            memory_percent = psutil.virtual_memory().percent
            if memory_percent > 80:
                st.warning(f"⚠️ 높은 메모리 사용량: {memory_percent:.1f}%")
                
                if st.button("🔄 메모리 최적화"):
                    self.optimize_session_state()
                    self.optimizer.clear_cache("temp_")
                    st.success("✅ 메모리 최적화가 완료되었습니다.")
                    
        except ImportError:
            # psutil이 없는 경우 무시
            pass


# 전역 성능 최적화 인스턴스
_global_optimizer = None

def get_optimizer():
    """전역 성능 최적화 인스턴스 가져오기"""
    global _global_optimizer
    if _global_optimizer is None:
        _global_optimizer = PerformanceOptimizer()
    return _global_optimizer

def optimize_large_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """대용량 DataFrame 최적화"""
    optimizer = get_optimizer()
    return optimizer.optimize_dataframe(df)

@st.cache_data(ttl=3600)  # 1시간 캐시
def cached_excel_read(file_path: str, **kwargs):
    """캐시된 Excel 읽기"""
    return pd.read_excel(file_path, **kwargs)

@st.cache_data(ttl=1800)  # 30분 캐시
def cached_template_processing(template: str, sample_data: dict):
    """캐시된 템플릿 처리"""
    try:
        return template.format(**sample_data)
    except Exception as e:
        return f"템플릿 오류: {str(e)}"

def performance_monitor(func_name: str = None):
    """성능 모니터링 데코레이터"""
    optimizer = get_optimizer()
    return optimizer.measure_time(func_name)

def setup_performance_optimization():
    """성능 최적화 초기 설정"""
    # Streamlit 설정 최적화
    st.set_page_config(
        page_title="여행 잔금 문자 생성기",
        page_icon="✈️",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': "여행 잔금 문자 생성기 v1.0"
        }
    )
    
    # 성능 CSS 추가
    st.markdown("""
    <style>
        /* 빠른 렌더링을 위한 CSS 최적화 */
        .main .block-container {
            max-width: 1200px;
            padding-top: 1rem;
        }
        
        /* 애니메이션 최적화 */
        * {
            transition: none !important;
            animation-duration: 0s !important;
        }
        
        /* 스크롤 최적화 */
        .main {
            overflow-anchor: none;
        }
        
        /* 폰트 최적화 */
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Noto Sans KR', sans-serif;
            font-display: swap;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # 모니터링 시작
    monitor = StreamlitPerformanceMonitor()
    monitor.start_monitoring()
    monitor.track_event('page_load')
    
    return monitor