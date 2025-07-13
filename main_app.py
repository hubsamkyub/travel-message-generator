import streamlit as st
import pandas as pd
import os
import json
import re
from datetime import datetime
import zipfile
import io
from enhanced_processor import EnhancedDataProcessor, EnhancedMessageGenerator
from ui_helpers import *
from preset_manager import PresetManager
from template_manager import TemplateManager

# 페이지 설정
st.set_page_config(
    page_title="여행 잔금 문자 생성기",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if 'mapping_data' not in st.session_state:
    st.session_state.mapping_data = None
if 'group_data' not in st.session_state:
    st.session_state.group_data = {}
if 'fixed_data' not in st.session_state:
    st.session_state.fixed_data = {}
if 'generated_messages' not in st.session_state:
    st.session_state.generated_messages = {}
if 'current_step' not in st.session_state:
    st.session_state.current_step = 1

# CSS 스타일
st.markdown("""
<style>
    .stApp {
        max-width: 1200px;
    }
    .step-container {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    .variable-highlight {
        background-color: #fff3cd;
        padding: 2px 4px;
        border-radius: 3px;
        font-family: monospace;
    }
    .message-preview {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 5px;
        padding: 15px;
        font-family: 'Noto Sans KR', sans-serif;
        line-height: 1.6;
        white-space: pre-wrap;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("✈️ 여행 잔금 문자 생성기")
    st.markdown("---")
    
    # 사이드바 - 진행 단계
    with st.sidebar:
        st.header("📋 진행 단계")
        
        steps = [
            "📁 엑셀 파일 업로드",
            "🔧 매핑 설정", 
            "📝 템플릿 설정",
            "🚀 메시지 생성",
            "📥 결과 확인"
        ]
        
        # 진행 상황 표시
        show_progress_indicator(st.session_state.current_step, len(steps), [
            "엑셀 파일 업로드", "매핑 설정", "템플릿 설정", "메시지 생성", "결과 확인"
        ])
        
        st.markdown("---")
        
        for i, step in enumerate(steps, 1):
            if st.session_state.current_step == i:
                st.markdown(f"**🔄 {step}**")
            elif st.session_state.current_step > i:
                st.markdown(f"✅ {step}")
            else:
                st.markdown(f"⏳ {step}")
        
        # 도움말 섹션
        create_help_sidebar()
        
        st.markdown("---")
        
        # 리셋 버튼
        if st.button("🔄 처음부터 다시", type="secondary"):
            for key in list(st.session_state.keys()):
                if key not in ['current_step']:
                    del st.session_state[key]
            st.session_state.current_step = 1
            st.rerun()
    
    # 메인 컨텐츠
    if st.session_state.current_step == 1:
        show_file_upload_step()
    elif st.session_state.current_step == 2:
        show_mapping_step()
    elif st.session_state.current_step == 3:
        show_template_step()
    elif st.session_state.current_step == 4:
        show_message_generation_step()
    elif st.session_state.current_step == 5:
        show_results_step()

def show_file_upload_step():
    st.header("1️⃣ 엑셀 파일 업로드")

    # 안내 정보 카드
    create_info_card(
        "📋 업로드 안내",
        """
        • **지원 형식**: .xlsx, .xls
        • **최대 크기**: 50MB
        • **필수 구조**: 고정 정보 + 테이블 데이터
        • **필수 컬럼**: 팀명, 발송그룹, 이름 등 매핑에 필요한 정보
        """,
        "📁"
    )

    with st.container():
        col1, col2 = st.columns([2, 1])

        with col1:
            uploaded_file = st.file_uploader(
                "📂 엑셀 파일을 선택하세요",
                type=['xlsx', 'xls'],
                help="드래그 앤 드롭 또는 클릭하여 파일을 선택하세요"
            )

            if uploaded_file is not None:
                with st.spinner("📊 파일을 분석하고 있습니다..."):
                    try:
                        excel_file = pd.ExcelFile(uploaded_file)
                        sheet_names = excel_file.sheet_names

                        st.success(f"✅ 파일 업로드 성공!")
                        
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("📄 파일명", uploaded_file.name.split('.')[0][:15] + "...")
                        with col_b:
                            st.metric("📊 시트 수", len(sheet_names))
                        with col_c:
                            file_size = uploaded_file.size / 1024 / 1024  # MB
                            st.metric("💾 파일 크기", f"{file_size:.1f}MB")

                        selected_sheet = st.selectbox(
                            "처리할 시트를 선택하세요:",
                            sheet_names,
                            index=0
                        )

                        if selected_sheet:
                            # ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼ [핵심 수정 부분] ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
                            # dtype=str 옵션을 추가하여 모든 데이터를 문자로 읽어오도록 강제
                            df_preview = pd.read_excel(uploaded_file, sheet_name=selected_sheet, header=None, dtype=str).fillna('')
                            # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

                            st.markdown("**🔍 데이터 미리보기:**")
                            st.dataframe(
                                df_preview.head(15),
                                use_container_width=True,
                                height=400
                            )

                            show_data_summary(df_preview, "시트 데이터 분석")

                            st.session_state.uploaded_file = uploaded_file
                            st.session_state.selected_sheet = selected_sheet
                            st.session_state.sheet_data = df_preview
                            
                            # 파일이 바뀌었음을 알리기 위해 매핑 상태 초기화
                            if 'current_file_id' not in st.session_state or st.session_state.current_file_id != uploaded_file.file_id:
                                if 'auto_mapping_done' in st.session_state:
                                    del st.session_state.auto_mapping_done

                            col_next1, col_next2 = st.columns([3, 1])
                            with col_next2:
                                if st.button("➡️ 다음 단계", type="primary", use_container_width=True):
                                    st.session_state.current_step = 2
                                    st.success("✅ 매핑 설정 단계로 이동합니다!")
                                    st.rerun()

                    except Exception as e:
                        show_error_details(e, "파일 읽기 중")
                        st.markdown("""
                        **💡 해결 방법:**
                        - 파일이 다른 프로그램에서 열려있지 않은지 확인
                        - 파일 형식이 .xlsx 또는 .xls인지 확인
                        - 파일이 손상되지 않았는지 확인
                        """)

        with col2:
            st.markdown("### 💡 파일 구조 예시")
            st.code("""
엑셀 파일 구조:
┌─────────────────────┐
│ A1: [빈칸]  D1: 상품명    │
│ A2: [빈칸]  D2: 하와이7일  │
│ ...                 │
│ A9: 팀     B9: 그룹     │
│ A10: 1팀   B10: A그룹   │
└─────────────────────┘
            """)
            st.markdown("**📥 샘플 파일 다운로드**")
            st.markdown("`create_sample_data.py`를 실행하여 샘플 엑셀 파일을 생성할 수 있습니다.")


def show_mapping_step():
    st.header("2️⃣ 매핑 설정")

    if 'uploaded_file' not in st.session_state:
        create_info_card("파일이 필요합니다", "먼저 엑셀 파일을 업로드해주세요.", "⚠️", "warning")
        if st.button("⬅️ 이전 단계로"):
            st.session_state.current_step = 1
            st.rerun()
        return

    # 고정 정보 기본값 설정
    if 'product_name_cell' not in st.session_state:
        st.session_state.product_name_cell = "B2"
        st.session_state.payment_due_cell = "B3"
        st.session_state.base_exchange_cell = "D2"
        st.session_state.current_exchange_cell = "D3"
        st.session_state.exchange_diff_cell = "D4"  # 추가
        st.session_state.exchange_burden_cell = "D5"  # 추가
        st.session_state.company_burden_cell = "D6"  # 추가
        st.session_state.bank_account_cell = "G2"    # 추가
        st.session_state.header_row = 9

    # 간단한 2단계 구성
    tab1, tab2 = st.tabs(["📍 기본 설정", "👥 필수 컬럼 매핑"])

    # 탭 1: 고정 정보 설정 (간소화)
    with tab1:
        st.markdown("### 📋 고정 정보 셀 주소")
        st.info("💡 엑셀에서 상품명, 날짜, 환율 등이 저장된 셀 주소를 입력하세요.")
        
        # 3개 컬럼으로 구성
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.session_state.product_name_cell = st.text_input("🏷️ 상품명 셀", value=st.session_state.product_name_cell, help="예: B2")
            st.session_state.payment_due_cell = st.text_input("📅 잔금완납일 셀", value=st.session_state.payment_due_cell, help="예: B3")
            st.session_state.bank_account_cell = st.text_input("🏦 입금계좌 셀", value=st.session_state.bank_account_cell, help="예: G2")
            
        with col2:
            st.session_state.base_exchange_cell = st.text_input("💱 기준환율 셀", value=st.session_state.base_exchange_cell, help="예: D2")
            st.session_state.current_exchange_cell = st.text_input("📈 현재환율 셀", value=st.session_state.current_exchange_cell, help="예: D3")
            
        with col3:
            st.session_state.exchange_diff_cell = st.text_input("💹 환율차액 셀", value=st.session_state.exchange_diff_cell, help="예: D4")
            st.session_state.company_burden_cell = st.text_input("💰 당사부담금 셀", value=st.session_state.company_burden_cell, help="예: D6")
            st.session_state.exchange_burden_cell = st.text_input("💰 환차추가금 셀", value=st.session_state.exchange_burden_cell, help="예: D5")

        st.markdown("### 📊 테이블 시작점")
        st.session_state.header_row = st.number_input(
            "헤더 행 번호 (컬럼명이 있는 행)", 
            min_value=1, max_value=50, 
            value=st.session_state.header_row,
            help="엑셀에서 '팀', '그룹', '이름' 등의 컬럼명이 있는 행 번호"
        )

    # 탭 2: 필수 컬럼 매핑 (대폭 간소화)
    with tab2:
        st.markdown("### 👥 필수 컬럼 선택")
        st.info("💡 메시지 그룹 생성을 위해 필요한 3개 컬럼을 선택해주세요.")
        
        try:
            header_row = st.session_state.header_row
            # 빈 열이 삭제되지 않도록 .dropna(how='all', axis=1) 제거
            df_table = pd.read_excel(st.session_state.uploaded_file, sheet_name=st.session_state.selected_sheet, header=header_row - 1)
            # 컬럼명의 앞뒤 공백 제거
            df_table.columns = df_table.columns.str.strip()
            
            available_columns = ["👆 선택하세요"] + df_table.columns.tolist()

            # 자동 매핑 시도 (처음 한 번만)
            if 'auto_mapping_simple_done' not in st.session_state:
                def find_column(keywords):
                    for keyword in keywords:
                        for col in df_table.columns:
                            if keyword in str(col):
                                return col
                    return "👆 선택하세요"

                st.session_state.team_col_simple = find_column(['팀'])
                st.session_state.group_col_simple = find_column(['그룹', '발송'])
                st.session_state.name_col_simple = find_column(['이름', '성명'])
                st.session_state.auto_mapping_simple_done = True

            # 3개 필수 컬럼 선택
            st.markdown("#### 🔴 필수 선택")
            col1, col2, col3 = st.columns(3)
            
            team_col = col1.selectbox(
                "팀 컬럼", available_columns, 
                index=available_columns.index(st.session_state.get("team_col_simple", "👆 선택하세요")) if st.session_state.get("team_col_simple", "👆 선택하세요") in available_columns else 0
            )
            group_col = col2.selectbox(
                "발송그룹 컬럼", available_columns,
                index=available_columns.index(st.session_state.get("group_col_simple", "👆 선택하세요")) if st.session_state.get("group_col_simple", "👆 선택하세요") in available_columns else 0
            )
            name_col = col3.selectbox(
                "이름 컬럼", available_columns,
                index=available_columns.index(st.session_state.get("name_col_simple", "👆 선택하세요")) if st.session_state.get("name_col_simple", "👆 선택하세요") in available_columns else 0
            )

            # 세션에 저장
            st.session_state.team_col_simple = team_col
            st.session_state.group_col_simple = group_col
            st.session_state.name_col_simple = name_col
            
            # 필수 컬럼 검증
            selected_columns = [team_col, group_col, name_col]
            missing_selections = [label for label, col in zip(['팀', '발송그룹', '이름'], selected_columns) if col == "👆 선택하세요"]
            
            if missing_selections:
                st.error(f"⚠️ 다음 항목을 선택해주세요: {', '.join(missing_selections)}")
                mapping_ready = False
            else:
                st.success("✅ 필수 컬럼 매핑이 완료되었습니다!")
                mapping_ready = True

            # 데이터 미리보기
            if mapping_ready:
                st.markdown("#### 📋 매핑 결과 미리보기")
                preview_df = df_table[[team_col, group_col, name_col]].head(5)
                preview_df.columns = ['팀', '발송그룹', '이름']
                st.dataframe(preview_df, use_container_width=True)
                
                # 그룹 통계
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                total_rows = len(df_table)
                unique_teams = df_table[team_col].nunique()
                unique_groups = df_table.groupby([team_col, group_col]).ngroups
                
                col_stat1.metric("전체 인원", f"{total_rows}명")
                col_stat2.metric("팀 수", f"{unique_teams}개")
                col_stat3.metric("예상 그룹", f"{unique_groups}개")

        except Exception as e:
            st.error(f"❌ 테이블 데이터 읽기 오류: {e}")
            mapping_ready = False

    # 최종 매핑 데이터 생성
    if 'mapping_ready' in locals() and mapping_ready:
        # 필수 매핑만 포함
        column_mappings = {
            team_col: 'team_name',
            group_col: 'sender_group', 
            name_col: 'name'
        }
        
        # 나머지 컬럼들도 자동으로 포함 (스마트 템플릿에서 사용 가능하도록)
        for col in df_table.columns:
            if col not in column_mappings:
                # 간단한 변수명 생성
                var_name = generate_variable_name(str(col))
                column_mappings[col] = var_name

        st.session_state.mapping_data = {
            "fixed_data_mapping": {
                "product_name": st.session_state.product_name_cell,
                "payment_due_date": st.session_state.payment_due_cell,
                "base_exchange_rate": st.session_state.base_exchange_cell,
                "current_exchange_rate": st.session_state.current_exchange_cell,
                "exchange_rate_diff": st.session_state.exchange_diff_cell,  # 추가
                "company_burden": st.session_state.company_burden_cell,     # 추가
                "exchange_burden": st.session_state.exchange_burden_cell,     # 추가
                "bank_account": st.session_state.bank_account_cell          # 추가
            },
            "table_settings": {
                "header_row": st.session_state.header_row
            },
            "column_mappings": column_mappings
        }
    else:
        mapping_ready = False

    # 네비게이션
    st.markdown("---")
    nav_cols = st.columns([1, 1])
    
    if nav_cols[0].button("⬅️ 이전 단계 (파일 업로드)", use_container_width=True):
        st.session_state.current_step = 1
        if 'auto_mapping_simple_done' in st.session_state:
            del st.session_state.auto_mapping_simple_done
        st.rerun()
    
    if nav_cols[1].button("➡️ 다음 단계 (템플릿 설정)", type="primary", use_container_width=True, disabled=not mapping_ready):
        st.session_state.current_step = 3
        st.success("✅ 간단 매핑이 완료되었습니다! 이제 스마트 템플릿을 설정해보세요.")
        st.rerun()
                  
def preview_fixed_data(fixed_mapping):
    """고정 정보 미리보기"""
    try:
        df_raw = st.session_state.sheet_data
        
        st.markdown("**🔍 고정 정보 미리보기:**")
        
        for key, cell_addr in fixed_mapping.items():
            value = get_cell_value(df_raw, cell_addr)
            st.write(f"**{key}**: {value} (셀: {cell_addr})")
            
    except Exception as e:
        st.error(f"미리보기 오류: {str(e)}")

def get_cell_value(df, cell_address, default=""):
    """DataFrame에서 셀 주소로 값 가져오기"""
    try:
        # 셀 주소 파싱 (예: A1 -> (0, 0))
        col_str = ''.join(filter(str.isalpha, cell_address.upper()))
        row_str = ''.join(filter(str.isdigit, cell_address))
        
        if not col_str or not row_str:
            return default
        
        # 열 문자를 숫자로 변환
        col_idx = 0
        for i, char in enumerate(reversed(col_str)):
            col_idx += (ord(char) - ord('A') + 1) * (26 ** i)
        col_idx -= 1  # 0-based로 변환
        
        row_idx = int(row_str) - 1  # 0-based로 변환
        
        if row_idx < len(df) and col_idx < len(df.columns):
            value = df.iloc[row_idx, col_idx]
            return value if pd.notna(value) else default
        return default
        
    except Exception:
        return default

def get_column_index(columns, search_term):
    """컬럼 리스트에서 검색어가 포함된 인덱스 찾기"""
    for i, col in enumerate(columns):
        if search_term in str(col):
            return i
    return 0

def show_template_step():
    st.header("3️⃣ 템플릿 설정")

    # Manager 인스턴스 생성
    template_manager = TemplateManager()

    # 매핑 데이터 유효성 검사
    if 'mapping_data' not in st.session_state or not st.session_state.mapping_data.get('column_mappings'):
        create_info_card("매핑 설정이 필요합니다", "이전 단계에서 매핑 설정을 완료해주세요.", "⚠️", "warning")
        if st.button("⬅️ 이전 단계로"):
            st.session_state.current_step = 2
            st.rerun()
        return

    # --- 1. 엑셀 데이터 및 컬럼 정보 준비 ---
    try:
        header_row = st.session_state.mapping_data.get('table_settings', {}).get('header_row', 1)
        df_table = pd.read_excel(st.session_state.uploaded_file, sheet_name=st.session_state.selected_sheet, header=header_row - 1, dtype=str).fillna('')
        excel_columns = df_table.columns.tolist()
        
        # 미리보기용 첫 번째 행 데이터
        preview_data = {}
        if not df_table.empty:
            first_row = df_table.iloc[0]
            for col in excel_columns:
                preview_data[col] = first_row[col] if pd.notna(first_row[col]) else ""
        
        # 고정 데이터 추가
        fixed_data_mapping = st.session_state.mapping_data.get('fixed_data_mapping', {})
        for var_name, cell in fixed_data_mapping.items():
            preview_data[var_name] = get_cell_value(st.session_state.sheet_data, cell)
            
    except Exception as e:
        st.error(f"엑셀 데이터 로드 실패: {e}")
        return

    # --- 2. 파일별 템플릿 자동 로드 ---
    file_template_key = f"template_{st.session_state.uploaded_file.name}_{st.session_state.selected_sheet}"
    
    # 템플릿 초기화 (한 번만)
    if 'smart_template' not in st.session_state:
        saved_template = template_manager.load_file_template(file_template_key)
        if saved_template:
            st.session_state.smart_template = saved_template
            st.success("✅ 이전에 저장한 템플릿을 자동으로 불러왔습니다!")
        else:
            # 기본 템플릿 제거하고 빈 문자열로 초기화
            st.session_state.smart_template = ""

    # 편집 중인 템플릿을 위한 임시 변수 초기화
    if 'temp_template_editing' not in st.session_state:
        st.session_state.temp_template_editing = st.session_state.smart_template

    # --- 3. 메인 편집기 및 미리보기 ---
    col_editor, col_preview = st.columns([1, 1], gap="large")
    
    with col_editor:
        st.markdown("##### ✍️ 스마트 템플릿 편집기")
        
        # 텍스트 에디터 - key를 고정하여 값이 유지되도록 함
        template_input = st.text_area(
            "Smart Template Editor", 
            value=st.session_state.temp_template_editing,
            height=350, 
            key="template_editor_area",
            label_visibility="collapsed",
            help="템플릿을 편집한 후 '적용하기' 버튼을 클릭하세요.",
            placeholder="여기에 템플릿을 입력하거나 '빠른 삽입 패널'을 사용하여 변수를 추가하세요."
        )
        
        # 편집된 내용을 임시로 저장
        st.session_state.temp_template_editing = template_input
        
        # 버튼 영역
        col_apply, col_save, col_stats = st.columns([1, 1, 2])
        
        # 적용하기 버튼
        apply_clicked = col_apply.button(
            "✅ 적용하기", 
            type="primary", 
            help="편집한 내용을 적용하여 미리보기를 갱신합니다",
            use_container_width=True
        )
        
        if apply_clicked:
            # 편집된 내용을 실제 템플릿으로 적용
            st.session_state.smart_template = st.session_state.temp_template_editing
            st.success("✅ 템플릿이 적용되었습니다!")
        
        # 파일 저장 버튼
        save_clicked = col_save.button(
            "💾 파일저장", 
            help="현재 적용된 템플릿을 파일에 저장합니다",
            use_container_width=True
        )
        
        if save_clicked:
            template_manager.save_file_template(file_template_key, st.session_state.smart_template)
            st.success("✅ 템플릿이 파일에 저장되었습니다!")
        
        # 템플릿 통계
        current_char_count = len(st.session_state.temp_template_editing)
        current_sms_type = "LMS" if current_char_count > 90 else "SMS"
        col_stats.metric("📊 편집 중", f"{current_char_count}자 | {current_sms_type}")
        
        # 변경사항 알림
        if st.session_state.temp_template_editing != st.session_state.smart_template:
            st.info("💡 편집한 내용이 있습니다. '적용하기' 버튼을 눌러 미리보기를 갱신하세요.")
    
    with col_preview:
        # 현재 적용된 템플릿으로 미리보기 표시
        show_smart_template_preview(st.session_state.smart_template, preview_data, excel_columns)

    # --- 4. 빠른 삽입 패널 ---
    st.markdown("---")
    st.markdown("### 🚀 빠른 삽입 패널")
    
    # 삽입 대기 텍스트 초기화
    if 'insert_ready_text' not in st.session_state:
        st.session_state.insert_ready_text = ""
    
    # 삽입 대기 영역
    if st.session_state.insert_ready_text:
        st.success("📋 아래 코드를 복사하여 템플릿의 원하는 위치에 붙여넣으세요:")
        
        col_code, col_clear = st.columns([5, 1])
        with col_code:
            # 복사하기 쉽도록 code 블록으로 표시
            st.code(st.session_state.insert_ready_text, language="text")
        with col_clear:
            if st.button("❌ 닫기", use_container_width=True):
                st.session_state.insert_ready_text = ""
                st.rerun()
    
    # 빠른 삽입 탭
    tab_columns, tab_fixed, tab_auto = st.tabs(["📊 엑셀 컬럼", "🏷️ 고정 정보", "⚡ 자동 계산"])
    
    with tab_columns:
        st.markdown("##### 📋 엑셀 컬럼 목록")
        
        # 검색 기능
        search_term = st.text_input("🔍 컬럼 검색", placeholder="컬럼명 입력...", key="col_search")
        filtered_columns = [col for col in excel_columns if search_term.lower() in str(col).lower()] if search_term else excel_columns
        
        if not filtered_columns:
            st.info("검색 결과가 없습니다.")
        else:
            # 3열로 표시
            for i in range(0, len(filtered_columns), 3):
                cols = st.columns(3)
                for j, col in enumerate(filtered_columns[i:i+3]):
                    if j < len(cols):
                        with cols[j]:
                            # 샘플 값 표시
                            sample_val = str(preview_data.get(col, ""))[:15]
                            if len(str(preview_data.get(col, ""))) > 15:
                                sample_val += "..."
                            
                            # 숫자 타입 추정
                            is_numeric = False
                            sample_value = preview_data.get(col, "")
                            try:
                                if isinstance(sample_value, (int, float)):
                                    is_numeric = True
                                elif isinstance(sample_value, str):
                                    clean_val = sample_value.replace(',', '').replace('.', '').replace('-', '').strip()
                                    if clean_val and clean_val.isdigit():
                                        is_numeric = True
                            except:
                                pass
                            
                            st.markdown(f"**{col}**")
                            st.caption(f"예: {sample_val}")
                            
                            # 텍스트 삽입 버튼
                            if st.button(f"📄 텍스트", key=f"txt_{col}_{i}_{j}", use_container_width=True):
                                st.session_state.insert_ready_text = f"[컬럼:{col}]"
                                st.rerun()
                            
                            # 숫자 삽입 버튼 (숫자형일 때만)
                            if is_numeric:
                                if st.button(f"🔢 숫자", key=f"num_{col}_{i}_{j}", use_container_width=True):
                                    st.session_state.insert_ready_text = f"[컬럼:{col}:,]"
                                    st.rerun()
    
    with tab_fixed:
        st.markdown("##### 🏷️ 고정 정보 변수")
        fixed_vars = [
            ("product_name", "상품명", "여행 상품 이름"),
            ("payment_due_date", "잔금완납일", "잔금 납부 마감일"),
            ("base_exchange_rate", "기준환율", "계약 당시 환율"),
            ("current_exchange_rate", "현재환율", "현재 환율"),
            ("exchange_rate_diff", "환율차액", "환율 변동 차액"),      # 추가
            ("company_burden", "당사부담금", "회사가 부담하는 금액"),    # 추가
            ("exchange_burden", "환차추가금", "환율 차액 추가금"),    # 추가
            ("bank_account", "입금계좌", "계좌 정보")                   # 추가
        ]
        
        cols = st.columns(2)
        for i, (var_code, var_name, desc) in enumerate(fixed_vars):
            with cols[i % 2]:
                if st.button(f"🏷️ {var_name}", key=f"fixed_{var_code}", help=desc, use_container_width=True):
                    st.session_state.insert_ready_text = f"{{{var_code}}}"
                    st.rerun()
    
    with tab_auto:
        st.markdown("##### ⚡ 자동 계산 변수")
        auto_vars = [
            ("group_members_text", "그룹 멤버", "홍길동님, 김철수님 형태"),
            ("group_size", "인원 수", "그룹의 총 인원"),
            ("additional_fee_per_person", "1인 추가요금", "환율 변동 추가 요금")
        ]
        
        cols = st.columns(2)
        for i, (var_code, var_name, desc) in enumerate(auto_vars):
            with cols[i % 2]:
                is_numeric = var_code in ["group_size", "additional_fee_per_person"]
                icon = "🔢" if is_numeric else "📝"
                if st.button(f"{icon} {var_name}", key=f"auto_{var_code}", help=desc, use_container_width=True):
                    if is_numeric:
                        st.session_state.insert_ready_text = f"{{{var_code}:,}}"
                    else:
                        st.session_state.insert_ready_text = f"{{{var_code}}}"
                    st.rerun()

    # --- 5. 템플릿 파일 관리 ---
    with st.expander("📁 템플릿 파일 관리", expanded=False):
        tab_upload, tab_library = st.tabs(["📤 파일 업로드", "🗂️ 내 라이브러리"])
        
        with tab_upload:
            st.markdown("##### 템플릿 파일 업로드")
            uploaded_file = st.file_uploader(
                "텍스트 파일(.txt) 선택", 
                type=['txt'],
                help="저장된 템플릿 파일을 불러옵니다"
            )
            
            if uploaded_file is not None:
                try:
                    content = uploaded_file.getvalue().decode("utf-8")
                    st.text_area("파일 내용", content, height=200, disabled=True)
                    
                    if st.button("📥 이 템플릿 적용", type="primary"):
                        st.session_state.smart_template = content
                        st.session_state.temp_template_editing = content
                        st.success("✅ 파일의 템플릿을 적용했습니다!")
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"파일 읽기 오류: {e}")
        
        with tab_library:
            st.markdown("##### 저장된 템플릿")
            templates = template_manager.get_user_template_list()
            
            if templates:
                template_dict = {t['name']: t['id'] for t in templates}
                selected = st.selectbox("템플릿 선택", ["선택 안 함"] + list(template_dict.keys()))
                
                col1, col2 = st.columns(2)
                if col1.button("📂 불러오기", disabled=(selected == "선택 안 함")):
                    tid = template_dict[selected]
                    tdata = template_manager.load_template(tid)
                    if tdata:
                        st.session_state.smart_template = tdata['content']
                        st.session_state.temp_template_editing = tdata['content']
                        st.success(f"✅ '{selected}' 템플릿을 불러왔습니다!")
                        st.rerun()
                
                if col2.button("🗑️ 삭제", disabled=(selected == "선택 안 함")):
                    tid = template_dict[selected]
                    if template_manager.delete_template(tid):
                        st.success(f"✅ '{selected}' 템플릿을 삭제했습니다!")
                        st.rerun()
            else:
                st.info("저장된 템플릿이 없습니다.")
            
            st.markdown("---")
            new_name = st.text_input("새 템플릿 이름")
            if st.button("💾 현재 템플릿을 라이브러리에 저장", disabled=not new_name):
                try:
                    tid = template_manager.create_user_template(
                        name=new_name,
                        content=st.session_state.smart_template
                    )
                    st.success(f"✅ '{new_name}' 템플릿을 저장했습니다!")
                    st.rerun()
                except Exception as e:
                    st.error(f"저장 실패: {e}")

    # --- 6. 네비게이션 ---
    st.markdown("---")
    
    # 템플릿 검증
    validation = validate_smart_template(
            st.session_state.smart_template, 
            excel_columns,
            ["product_name", "payment_due_date", "base_exchange_rate", 
            "current_exchange_rate", "exchange_rate_diff", "company_burden",  # 추가
            "exchange_burden",
            "bank_account", "group_members_text", "group_size",               # 추가
            "additional_fee_per_person"]
        )
    
    nav_cols = st.columns([1, 1])
    
    if nav_cols[0].button("⬅️ 이전 단계", use_container_width=True):
        st.session_state.current_step = 2
        st.rerun()
    
    # 진행 가능 여부 체크
    can_proceed = not validation.get('errors', [])
    
    # 편집 중인 내용이 있는데 적용하지 않은 경우
    if st.session_state.temp_template_editing != st.session_state.smart_template:
        st.warning("⚠️ 편집한 내용을 적용하지 않았습니다. '적용하기' 버튼을 먼저 클릭하세요.")
        can_proceed = False
    
    if nav_cols[1].button(
        "➡️ 다음 단계", 
        type="primary", 
        use_container_width=True, 
        disabled=not can_proceed
    ):
        # 템플릿을 파일에 자동 저장
        template_manager.save_file_template(file_template_key, st.session_state.smart_template)
        st.session_state.template = st.session_state.smart_template
        st.session_state.current_step = 4
        st.success("✅ 템플릿이 저장되고 다음 단계로 이동합니다!")
        st.rerun()
    
    # 검증 오류 표시
    if validation.get('errors'):
        st.error("**⚠️ 템플릿 오류:**")
        for error in validation['errors']:
            st.write(f"• {error}")

    # --- 7. 사이드바 도움말 ---
    with st.sidebar:
        st.markdown("### 💡 템플릿 편집 도움말")
        st.markdown("""
        **✏️ 편집 방법:**
        1. 편집기에서 내용 수정
        2. **'적용하기'** 버튼 클릭
        3. 미리보기에서 결과 확인
        
        **📌 중요:**
        - 편집 후 반드시 '적용하기' 클릭
        - 미리보기는 적용된 내용만 표시
        - 다음 단계 전 자동 저장됨
        
        **🔤 템플릿 문법:**
        - `[컬럼:컬럼명]` - 텍스트 값
        - `[컬럼:컬럼명:,]` - 숫자 (천단위)
        - `{변수명}` - 시스템 변수
        """)
        
        with st.expander("🚨 문제 해결"):
            st.markdown("""
            **편집 내용이 사라짐:**
            → '적용하기' 버튼을 클릭하세요
            
            **미리보기가 갱신 안됨:**
            → '적용하기' 후 확인하세요
            
            **다음 단계 진행 불가:**
            → 편집 내용을 먼저 적용하세요
            """)
                                 
def validate_smart_template(template, excel_columns, system_variables):
    """스마트 템플릿 검증 (숫자 포맷 지원)"""
    errors = []
    
    # 컬럼 참조 검증
    import re
    column_refs = re.findall(r'\[컬럼:([^\]:]+)\]', template)  # 일반 참조
    column_format_refs = re.findall(r'\[컬럼:([^\]:]+):[^\]]+\]', template)  # 포맷 참조
    
    all_column_refs = set(column_refs + column_format_refs)
    
    for col_ref in all_column_refs:
        if col_ref not in excel_columns:
            errors.append(f"존재하지 않는 컬럼: '{col_ref}'")
    
    return {'errors': errors}

def show_message_generation_step():
    st.header("4️⃣ 메시지 생성")
    
    if 'template' not in st.session_state:
        st.warning("⚠️ 먼저 템플릿을 설정해주세요.")
        if st.button("⬅️ 이전 단계로"):
            st.session_state.current_step = 3
            st.rerun()
        return
    
    st.markdown("**🚀 데이터 처리 및 메시지 생성**")
    
    if st.button("📊 데이터 처리 및 메시지 생성", type="primary"):
        with st.spinner("데이터를 처리하고 메시지를 생성하고 있습니다..."):
            try:
                # 데이터 처리
                process_data_and_generate_messages()
                st.success("✅ 메시지 생성이 완료되었습니다!")
                st.session_state.current_step = 5
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ 메시지 생성 중 오류 발생: {str(e)}")
    
    # 네비게이션
    if st.button("⬅️ 이전 단계"):
        st.session_state.current_step = 3
        st.rerun()

def process_data_and_generate_messages():
    """데이터 처리 및 스마트 메시지 생성 (개선된 버전)"""
    
    try:
        # 향상된 프로세서 초기화
        data_processor = EnhancedDataProcessor()
        message_generator = EnhancedMessageGenerator()
        
        # 1. 고정 데이터 추출
        df_raw = st.session_state.sheet_data
        fixed_data = data_processor.extract_fixed_data(
            df_raw, 
            st.session_state.mapping_data["fixed_data_mapping"]
        )
        st.session_state.fixed_data = fixed_data
        
        # 진행 상황 표시
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("🔍 고정 정보 추출 완료...")
        progress_bar.progress(20)
        
        # 2. 테이블 데이터 읽기
        header_row = st.session_state.mapping_data["table_settings"]["header_row"] - 1
        customer_df = pd.read_excel(st.session_state.uploaded_file, 
                                   sheet_name=st.session_state.selected_sheet, 
                                   header=header_row)
        
        # [해결 코드] 여기서도 컬럼명 공백을 제거합니다.
        customer_df.columns = customer_df.columns.str.strip()
        
        status_text.text("📊 테이블 데이터 로드 완료...")
        progress_bar.progress(40)
        
        # 3. 그룹 데이터 생성 (컬럼 매핑 정보 전달)
        column_mappings = st.session_state.mapping_data["column_mappings"]
        group_data = data_processor.process_group_data_dynamic(
            customer_df,
            column_mappings
        )
        st.session_state.group_data = group_data

        status_text.text(f"👥 {len(group_data)}개 그룹 생성 완료...")
        progress_bar.progress(60)
        
        # 4. 스마트 메시지 생성 (컬럼 매핑 정보 전달)
        template = st.session_state.get('smart_template', st.session_state.get('template', ''))
        
        # message_generator에 컬럼 매핑 정보 설정
        message_generator.column_mappings = column_mappings
        message_generator.excel_columns = customer_df.columns.tolist()
        
        result = message_generator.generate_messages(
            template, 
            group_data, 
            fixed_data
        )
        
        st.session_state.generated_messages = result['messages']
        
        status_text.text("✨ 스마트 메시지 생성 완료!")
        progress_bar.progress(100)
        
        # 완료 메시지
        success_info = f"""
        🎉 **스마트 메시지 생성 완료!**
        
        📊 **처리 결과:**
        - 📁 처리된 그룹 수: **{len(group_data)}개**
        - 📝 생성된 메시지 수: **{result['total_count']}개**
        - 🔗 사용된 컬럼 참조: **{len(result.get('column_refs_found', []))}개**
        """
        
        st.success(success_info)
        
        progress_bar.empty()
        status_text.empty()

    except Exception as e:
        show_error_details(e, "스마트 데이터 처리 및 메시지 생성 중")
        raise
    
def show_results_step():
    st.header("5️⃣ 결과 확인 및 활용")

    if not st.session_state.get('generated_messages'):
        st.warning("⚠️ 생성된 메시지가 없습니다. 이전 단계에서 메시지를 생성해주세요.")
        if st.button("⬅️ 이전 단계로"):
            st.session_state.current_step = 4
            st.rerun()
        return

    # 수정된 메시지를 저장하기 위한 세션 상태 초기화
    if 'edited_messages' not in st.session_state:
        st.session_state.edited_messages = {}

    total_messages = len(st.session_state.generated_messages)
    st.success(f"✅ 총 {total_messages}개의 메시지 그룹이 생성되었습니다!")

    # --- 1. 결과 필터링 및 검색 UI ---
    st.markdown("#### 🔍 결과 검색 및 필터링")
    search_query = st.text_input("팀명 또는 대표자 이름으로 검색하세요:", placeholder="예: 1팀 또는 홍길동")

    sorted_messages = sorted(st.session_state.generated_messages.items(), key=lambda item: item[1]['group_info'].get('excel_order', 0))

    # 검색 쿼리에 따라 결과 필터링
    filtered_messages = []
    if search_query:
        for group_id, data in sorted_messages:
            group_info = data['group_info']
            # 팀명 또는 대표자 이름에 검색어가 포함되어 있으면 추가
            if search_query.lower() in group_info.get('team_name', '').lower() or search_query.lower() in group_info.get('sender', '').lower():
                filtered_messages.append((group_id, data))
    else:
        filtered_messages = sorted_messages

    if not filtered_messages:
        st.warning(f"'{search_query}'에 해당하는 그룹이 없습니다.")
        return

    # --- 2. 그룹 선택 및 메시지 수정 UI ---
    group_options = [f"{gid} - {d['group_info']['team_name']} ({d['group_info'].get('sender', '')}님 그룹)" for gid, d in filtered_messages]
    selected_group_label = st.selectbox("📋 확인할 그룹을 선택하세요:", group_options)

    if selected_group_label:
        selected_group_id = selected_group_label.split(' ')[0]
        original_message_data = st.session_state.generated_messages[selected_group_id]
        group_info = original_message_data['group_info']

        # 수정된 메시지가 있으면 가져오고, 없으면 원본 메시지 사용
        message_to_display = st.session_state.edited_messages.get(selected_group_id, original_message_data['message'])

        st.markdown("#### ✍️ 개별 메시지 확인 및 수정")
        edited_message = st.text_area(
            "수정 후, 다른 그룹을 선택하면 자동으로 저장됩니다.",
            value=message_to_display,
            height=300,
            key=f"editor_{selected_group_id}"
        )
        # 수정된 내용을 세션에 저장
        st.session_state.edited_messages[selected_group_id] = edited_message

    st.markdown("---")

    # --- 3. 전체 다운로드 및 활용 기능 ---
    st.markdown("#### 📥 전체 다운로드 및 활용")
    
    # '전체 복사' 기능을 위한 확장 박스
    with st.expander("📋 원클릭 전체 복사 (모든 메시지 이어붙이기)"):
        all_messages_content = []
        # 필터링된 결과가 아닌, 전체 메시지를 대상으로 함
        for group_id, data in sorted_messages:
            # 수정된 내용이 있으면 수정본을, 없으면 원본을 사용
            content = st.session_state.edited_messages.get(group_id, data['message'])
            all_messages_content.append(f"--- 📣 {data['group_info']['team_name']} {data['group_info'].get('sender', '')}님 그룹 ---")
            all_messages_content.append(content)
            all_messages_content.append("\n")
        
        full_text = "\n".join(all_messages_content)
        st.text_area("All Messages", value=full_text, height=400, help="이 박스의 전체 내용을 복사하여 사용하세요.")

    # 파일 다운로드 버튼
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        txt_content = create_text_download(include_edited=True) # 수정된 내용을 포함하여 다운로드
        st.download_button("📄 텍스트로 다운로드", data=txt_content, file_name=f"messages_{datetime.now().strftime('%Y%m%d')}.txt", mime="text/plain", use_container_width=True)
    with col_dl2:
        excel_content = create_excel_download(include_edited=True) # 수정된 내용을 포함하여 다운로드
        st.download_button("📊 엑셀로 다운로드", data=excel_content, file_name=f"messages_{datetime.now().strftime('%Y%m%d')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)


    # --- 4. 네비게이션 ---
    st.markdown("---")
    nav_cols = st.columns([1, 1])
    if nav_cols[0].button("⬅️ 이전 단계 (템플릿 설정)", use_container_width=True):
        st.session_state.current_step = 3
        st.rerun()
    if nav_cols[1].button("🔄 처음부터 새로 시작", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

def create_text_download(include_edited=False):
    """텍스트 파일 다운로드 컨텐츠 생성 (수정본 포함 기능 추가)"""
    content = []
    
    sorted_messages = sorted(st.session_state.generated_messages.items(), key=lambda item: item[1]['group_info'].get('excel_order', 0))

    for group_id, data in sorted_messages:
        group_info = data['group_info']
        # 수정된 내용이 있고, 포함 옵션이 켜져 있으면 수정본 사용
        if include_edited and group_id in st.session_state.get('edited_messages', {}):
            message = st.session_state.edited_messages[group_id]
        else:
            message = data['message']
        
        content.append(f"=== {group_id} ({group_info['team_name']}-{group_info['sender_group']}) ===")
        content.append(f"발송인: {group_info['sender']}")
        content.append(f"대상자: {', '.join(group_info['members'])}")
        content.append(f"연락처: {group_info.get('contact', '')}")
        content.append("-" * 60)
        content.append(message)
        content.append("\n" + "="*60 + "\n")
    
    return "\n".join(content)

def create_excel_download(include_edited=False):
    """엑셀 파일 다운로드 컨텐츠 생성 (수정본 포함 기능 추가)"""
    data_to_export = []
    
    sorted_messages = sorted(st.session_state.generated_messages.items(), key=lambda item: item[1]['group_info'].get('excel_order', 0))

    for group_id, message_data in sorted_messages:
        group_info = message_data['group_info']
        
        if include_edited and group_id in st.session_state.get('edited_messages', {}):
            message = st.session_state.edited_messages[group_id]
        else:
            message = message_data['message']
        
        data_to_export.append({
            '그룹ID': group_id,
            '팀명': group_info['team_name'],
            '발송그룹': group_info['sender_group'],
            '발송인': group_info['sender'],
            '연락처': group_info.get('contact', ''),
            '그룹멤버': ', '.join(group_info['members']),
            '인원수': group_info['group_size'],
            '메시지': message
        })
    
    df = pd.DataFrame(data_to_export)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='메시지')
    
    return output.getvalue()
            
if __name__ == "__main__":
    main()