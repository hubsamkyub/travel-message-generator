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
        • **필수 컬럼**: 팀명, 발송그룹, 이름
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
                        # 엑셀 파일 읽기
                        excel_file = pd.ExcelFile(uploaded_file)
                        sheet_names = excel_file.sheet_names
                        
                        # 성공 메시지
                        st.success(f"✅ 파일 업로드 성공!")
                        
                        # 파일 정보 표시
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("📄 파일명", uploaded_file.name.split('.')[0][:15] + "...")
                        with col_b:
                            st.metric("📊 시트 수", len(sheet_names))
                        with col_c:
                            file_size = uploaded_file.size / 1024 / 1024  # MB
                            st.metric("💾 파일 크기", f"{file_size:.1f}MB")
                        
                        # 시트 선택
                        st.markdown("**📋 처리할 시트를 선택하세요:**")
                        selected_sheet = st.selectbox(
                            "시트 선택",
                            sheet_names,
                            index=0,
                            help="데이터가 포함된 시트를 선택하세요"
                        )
                        
                        if selected_sheet:
                            # 시트 데이터 미리보기
                            df_preview = pd.read_excel(uploaded_file, sheet_name=selected_sheet, header=None)
                            
                            st.markdown("**🔍 데이터 미리보기:**")
                            st.dataframe(
                                df_preview.head(15), 
                                use_container_width=True,
                                height=400
                            )
                            
                            # 데이터 요약
                            show_data_summary(df_preview, "시트 데이터 분석")
                            
                            # 세션에 저장
                            st.session_state.uploaded_file = uploaded_file
                            st.session_state.selected_sheet = selected_sheet
                            st.session_state.sheet_data = df_preview
                            
                            # 다음 단계 버튼
                            st.markdown("---")
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
│ A3: [빈칸]  D3: 완납일    │
│ ...                 │
│ A9: 팀     B9: 그룹     │
│ A10: 1팀   B10: A그룹   │
│ A11: 1팀   B11: A그룹   │
└─────────────────────┘
            """)
            
            # 샘플 파일 다운로드 링크
            st.markdown("**📥 샘플 파일 다운로드**")
            st.markdown("""
            테스트용 샘플 파일이 필요하시면  
            `create_sample_data.py`를 실행하여  
            샘플 엑셀 파일을 생성할 수 있습니다.
            """)
            
            if st.button("📝 샘플 데이터 정보", help="샘플 데이터 구조를 확인하세요"):
                with st.expander("샘플 데이터 구조", expanded=True):
                    st.markdown("""
                    **고정 정보 위치:**
                    - D2: 상품명
                    - D3: 잔금완납일
                    - F2: 기준환율
                    - F3: 현재환율
                    - F4: 환율차액
                    - F5: 당사부담금
                    
                    **테이블 구조:**
                    - 9행: 헤더 (팀, 발송그룹, 이름...)
                    - 10행부터: 고객 데이터
                    """)

# main_app.py 파일에서 show_mapping_step 함수를 아래 코드로 교체하세요.
# main_app.py 파일에서 show_mapping_step 함수를 아래 코드로 교체하세요.

def show_mapping_step():
    st.header("2️⃣ 매핑 설정")

    if 'uploaded_file' not in st.session_state:
        create_info_card("파일이 필요합니다", "먼저 엑셀 파일을 업로드해주세요.", "⚠️", "warning")
        if st.button("⬅️ 이전 단계로"):
            st.session_state.current_step = 1
            st.rerun()
        return

    # --- 탭 UI 구성 ---
    tab1, tab2 = st.tabs(["⚙️ 기본 설정 (고정 정보, 테이블)", "🔗 동적 컬럼 매핑"])

    # 탭1: 고정 정보 및 테이블 설정 (이전과 동일)
    with tab1:
        st.markdown("### 📍 고정 정보 셀 주소 설정")
        col1, col2 = st.columns(2)
        with col1:
            product_name_cell = st.text_input("🏷️ 상품명", value=st.session_state.get("product_name_cell", "D2"))
            payment_due_cell = st.text_input("📅 잔금완납일", value=st.session_state.get("payment_due_cell", "D3"))
        with col2:
            base_exchange_cell = st.text_input("💱 기준환율", value=st.session_state.get("base_exchange_cell", "F2"))
            current_exchange_cell = st.text_input("📈 현재환율", value=st.session_state.get("current_exchange_cell", "F3"))

        st.markdown("### 📊 테이블 구조 설정")
        header_row = st.number_input(
            "📋 헤더 행 번호 (컬럼명이 있는 행)", min_value=1, max_value=50, value=st.session_state.get("header_row", 9)
        )
        # UI 상태 유지를 위해 세션에 값 저장
        st.session_state.product_name_cell = product_name_cell
        st.session_state.payment_due_cell = payment_due_cell
        st.session_state.base_exchange_cell = base_exchange_cell
        st.session_state.current_exchange_cell = current_exchange_cell
        st.session_state.header_row = header_row

    # 탭2: 동적 컬럼 매핑 (개선된 UI)
    with tab2:
        try:
            df_table = pd.read_excel(
                st.session_state.uploaded_file,
                sheet_name=st.session_state.selected_sheet,
                header=header_row - 1
            ).dropna(how='all', axis=1)
            available_columns = ["선택 안 함"] + df_table.columns.tolist()

            # ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼ [핵심 수정 부분] ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
            # 1. 필수 변수 매핑 (더 직관적인 Selectbox 사용)
            st.markdown("#### 🔴 필수 변수 지정")
            st.markdown("아래 3개 항목은 반드시 엑셀의 해당 컬럼과 연결해야 합니다.")
            
            required_cols = st.columns(3)
            # st.selectbox를 사용하여 각 필수 변수에 해당하는 엑셀 컬럼을 명시적으로 선택
            team_col = required_cols[0].selectbox(
                "팀(team_name) 컬럼", available_columns,
                index=available_columns.index(st.session_state.get("team_col_selection", "선택 안 함"))
            )
            sender_group_col = required_cols[1].selectbox(
                "그룹(sender_group) 컬럼", available_columns,
                index=available_columns.index(st.session_state.get("sender_group_selection", "선택 안 함"))
            )
            name_col = required_cols[2].selectbox(
                "이름(name) 컬럼", available_columns,
                index=available_columns.index(st.session_state.get("name_col_selection", "선택 안 함"))
            )

            # 사용자의 선택을 세션에 저장하여 상태 유지
            st.session_state.team_col_selection = team_col
            st.session_state.sender_group_selection = sender_group_col
            st.session_state.name_col_selection = name_col

            # 필수 항목 선택 여부 확인
            missing_required = []
            if team_col == "선택 안 함": missing_required.append("팀")
            if sender_group_col == "선택 안 함": missing_required.append("그룹")
            if name_col == "선택 안 함": missing_required.append("이름")

            if missing_required:
                st.error(f"**필수 변수 미지정:** `{', '.join(missing_required)}`에 해당하는 컬럼을 선택해주세요.")

            st.markdown("---")

            # 2. 선택(옵션) 변수 매핑
            st.markdown("#### 🔵 선택 변수 지정 (템플릿에 사용할 추가 정보)")
            st.markdown("엑셀의 각 컬럼에 사용할 변수명을 자유롭게 지정하세요.")

            # 필수 항목으로 선택된 컬럼은 제외하고 나머지 컬럼만 표시
            optional_columns = [col for col in df_table.columns if col not in [team_col, sender_group_col, name_col]]
            
            # 변수명 자동 생성
            if 'dynamic_mappings' not in st.session_state or st.button("🔄 선택 변수명 자동 생성"):
                st.session_state.dynamic_mappings = {col: generate_variable_name(str(col)) for col in optional_columns}

            ui_cols = st.columns(2)
            ui_cols[0].markdown("**엑셀 컬럼**")
            ui_cols[1].markdown("**프로그램 변수명 (템플릿에 사용)**")

            for col_header in optional_columns:
                c1, c2 = st.columns(2)
                c1.markdown(f"`{col_header}`")
                st.session_state.dynamic_mappings[col_header] = c2.text_input(
                    f"var_for_{col_header}",
                    value=st.session_state.dynamic_mappings.get(col_header, ""),
                    label_visibility="collapsed"
                )
            # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

            # 최종 매핑 정보 구성
            final_column_mappings = {}
            if team_col != "선택 안 함": final_column_mappings[team_col] = 'team_name'
            if sender_group_col != "선택 안 함": final_column_mappings[sender_group_col] = 'sender_group'
            if name_col != "선택 안 함": final_column_mappings[name_col] = 'name'
            
            # 선택 변수들을 최종 매핑에 추가
            for col, var_name in st.session_state.dynamic_mappings.items():
                if col in optional_columns and var_name:
                    final_column_mappings[col] = var_name

            st.session_state.mapping_data = {
                "fixed_data_mapping": { "product_name": product_name_cell, "payment_due_date": payment_due_cell, "base_exchange_rate": base_exchange_cell, "current_exchange_rate": current_exchange_cell },
                "table_settings": { "header_row": header_row },
                "column_mappings": final_column_mappings
            }
            with st.expander("📋 현재 매핑 요약 보기"):
                st.json(st.session_state.mapping_data)

        except Exception as e:
            show_error_details(e, "테이블 데이터를 읽는 중")
            missing_required = ['팀'] # 오류 발생 시 다음 단계 버튼 비활성화

    # 네비게이션 버튼
    st.markdown("---")
    col_nav1, col_nav2 = st.columns([1, 1])
    with col_nav1:
        if st.button("⬅️ 이전 단계", use_container_width=True):
            st.session_state.current_step = 1
            st.rerun()
    with col_nav2:
        is_disabled = bool(missing_required) # 필수 항목이 선택되지 않으면 비활성화
        if st.button("➡️ 다음 단계: 템플릿 설정", type="primary", use_container_width=True, disabled=is_disabled):
            st.session_state.current_step = 3
            st.success("✅ 템플릿 설정 단계로 이동합니다!")
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

    # 매핑 데이터 유효성 검사
    if 'mapping_data' not in st.session_state or not st.session_state.mapping_data.get('column_mappings'):
        create_info_card(
            "매핑 설정이 필요합니다",
            "이전 단계에서 엑셀 컬럼과 변수 매핑을 먼저 완료해주세요.", "⚠️", "warning"
        )
        if st.button("⬅️ 이전 단계로"):
            st.session_state.current_step = 2
            st.rerun()
        return

    # --- 1. 변수 목록 및 미리보기 데이터 준비 ---
    fixed_data_mapping = st.session_state.mapping_data.get('fixed_data_mapping', {})
    column_mappings = st.session_state.mapping_data.get('column_mappings', {})
    header_row = st.session_state.mapping_data.get('table_settings', {}).get('header_row', 1)

    fixed_vars = list(fixed_data_mapping.keys())
    dynamic_vars = list(column_mappings.values())
    calculated_vars = ['group_members_text', 'group_size', 'additional_fee_per_person']
    all_available_vars = sorted(list(set(fixed_vars + dynamic_vars + calculated_vars)))

    # 미리보기에 사용할 실제 데이터 생성
    preview_variables = {}
    try:
        df_table = pd.read_excel(
            st.session_state.uploaded_file,
            sheet_name=st.session_state.selected_sheet,
            header=header_row - 1
        )
        if not df_table.empty:
            first_row = df_table.iloc[0]
            for excel_col, var_name in column_mappings.items():
                if excel_col in first_row:
                    preview_variables[var_name] = first_row[excel_col]

        for var_name, cell in fixed_data_mapping.items():
            preview_variables[var_name] = get_cell_value(st.session_state.sheet_data, cell)

        preview_variables['group_members_text'] = f"{preview_variables.get('name', '아무개')}님 외 1명"
        preview_variables['group_size'] = 2
        preview_variables['additional_fee_per_person'] = 70000

    except Exception as e:
        st.warning(f"미리보기 데이터 생성 중 오류 발생: {e}")


    # --- 2. 상단 레이아웃: [좌] 편집기 | [우] 미리보기 ---
    editor_col, preview_col = st.columns(2, gap="large")

    with editor_col:
        st.markdown("##### 📝 메시지 템플릿 편집")
        default_template = st.session_state.get('template', "[여행처럼]\n안녕하세요, {product_name} 안내입니다.")
        template = st.text_area("Template Editor", value=default_template, height=500, key="template_editor", label_visibility="collapsed")
        st.session_state.template = template

    with preview_col:
        show_template_preview(template, preview_variables)


    # --- 3. 하단 레이아웃: 템플릿 관리 및 변수 목록 ---
    st.markdown("---")

    with st.expander("📂 내 템플릿 관리 (가져오기 및 변수 스마트 매핑)", expanded=True):
        uploaded_template_file = st.file_uploader("사용자 정의 템플릿 파일(.txt)을 업로드하세요.", type=['txt'], key="template_uploader")

        # '매핑 적용' 버튼을 누른 후에는 이 조건이 False가 되어 매핑 UI가 더 이상 보이지 않음
        if uploaded_template_file and 'template_to_system_map' in st.session_state:
            st.warning(f"⚠️ 템플릿의 변수와 시스템 변수가 다릅니다. 아래에서 매핑을 조정해주세요.")
            st.markdown("**스마트 변수 매핑 도우미**")
            
            unmapped_template_vars = list(st.session_state.template_to_system_map.keys())
            for var in unmapped_template_vars:
                cols = st.columns([2, 1, 2])
                cols[0].markdown(f"템플릿 변수: `{var}`")
                cols[1].markdown("→")
                st.session_state.template_to_system_map[var] = cols[2].selectbox(
                    f"map_for_{var}", ["선택 안 함"] + all_available_vars,
                    index=(["선택 안 함"] + all_available_vars).index(st.session_state.template_to_system_map.get(var, "선택 안 함")),
                    label_visibility="collapsed"
                )

            if st.button("🚀 매핑 적용하고 템플릿 업데이트", type="primary"):
                uploaded_content = st.session_state.uploaded_template_content
                new_template = uploaded_content
                for template_var, system_var in st.session_state.template_to_system_map.items():
                    if system_var != "선택 안 함":
                        pattern = r'\{' + re.escape(template_var) + r'(:[^}]+)?\}'
                        replacement = lambda m: f"{{{system_var}{m.group(1) or ''}}}"
                        new_template = re.sub(pattern, replacement, new_template)
                
                st.session_state.template = new_template

                # ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼ [핵심 수정 부분] ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
                # 작업 완료 후, 매핑 UI를 다시 띄우는 데 사용된 모든 세션 상태를 깨끗하게 삭제
                st.session_state.pop('template_to_system_map', None)
                st.session_state.pop('uploaded_template_content', None)
                st.session_state.pop('uploader_key', None)
                # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

                st.success("✅ 매핑이 적용되었습니다! 템플릿이 업데이트되었습니다.")
                st.rerun()

        elif uploaded_template_file:
            # 파일이 업로드되었지만 아직 매핑 UI가 생성되지 않은 초기 상태
            if 'uploader_key' not in st.session_state or st.session_state.uploader_key != uploaded_template_file.file_id:
                st.session_state.uploaded_template_content = uploaded_template_file.read().decode('utf-8')
                st.session_state.uploader_key = uploaded_template_file.file_id
                
                uploaded_content = st.session_state.uploaded_template_content
                template_vars = set(re.findall(r'\{(\w+)(?::[^}]+)?\}', uploaded_content))
                unmapped_template_vars = [var for var in template_vars if var not in all_available_vars]

                if not unmapped_template_vars:
                    st.session_state.template = uploaded_content
                    st.success("✅ 템플릿이 성공적으로 적용되었습니다. 모든 변수가 현재 시스템과 일치합니다.")
                    st.session_state.pop('uploader_key', None) # 작업 완료 후 정리
                    st.rerun()
                else:
                    # 매핑이 필요한 경우, 매핑 UI를 생성하기 위한 세션 상태 설정 후 재실행
                    st.session_state.template_to_system_map = {var: "선택 안 함" for var in unmapped_template_vars}
                    st.rerun()

    st.markdown("---")
    st.markdown("##### 💡 사용 가능한 변수 목록")
    # (이하 변수 목록 표시 UI는 이전과 동일)
    var_tabs = st.tabs(["**엑셀 컬럼**", "**고정 정보**", "**자동 계산**"])
    with var_tabs[0]:
        st.markdown("2단계에서 매핑한 `엑셀 컬럼 → {변수명}` 목록입니다.")
        for excel_col, var_name in sorted(column_mappings.items(), key=lambda item: item[1]):
            st.text(f"'{excel_col}' → {{{var_name}}}")
    with var_tabs[1]:
        st.markdown("2단계 기본 설정에서 매핑된 변수입니다.")
        for var in sorted(fixed_vars):
            st.code(f"{{{var}}}", language="text")
    with var_tabs[2]:
        st.markdown("시스템에서 자동으로 계산되는 변수입니다.")
        for var in sorted(calculated_vars):
            st.code(f"{{{var}}}", language="text")
    with st.expander("⚡ 빠른 변수 삽입 (클릭하여 복사)"):
        quick_cols = st.columns(5)
        for i, var_name in enumerate(all_available_vars):
            if quick_cols[i % 5].button(f"`{{{var_name}}}`", use_container_width=True, help=f"{{{var_name}}} 복사"):
                st.info(f"아래 텍스트를 복사하여 사용하세요:")
                st.code(f"{{{var_name}}}", language="text")

    # --- 4. 네비게이션 버튼 ---
    st.markdown("---")
    nav_cols = st.columns([1, 1])
    if nav_cols[0].button("⬅️ 이전 단계 (매핑 설정)", use_container_width=True):
        st.session_state.current_step = 2
        st.rerun()
    if nav_cols[1].button("➡️ 다음 단계 (메시지 생성)", type="primary", use_container_width=True):
        st.session_state.current_step = 4
        st.success("✅ 메시지 생성 단계로 이동합니다!")
        st.rerun()

        
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
    """데이터 처리 및 메시지 생성 (향상된 버전)"""
    
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
        
        status_text.text("📊 테이블 데이터 로드 완료...")
        progress_bar.progress(40)
        
        # 3. 그룹 데이터 생성
        group_data = data_processor.process_group_data_dynamic(
            customer_df,
            st.session_state.mapping_data["column_mappings"]
        )
        st.session_state.group_data = group_data

        status_text.text(f"👥 {len(group_data)}개 그룹 생성 완료...")
        progress_bar.progress(60)
        
        # 4. 메시지 생성
        template = st.session_state.template
        
        result = message_generator.generate_messages(
            template, 
            group_data, 
            fixed_data
        )
        
        st.session_state.generated_messages = result['messages']
        
        status_text.text("✨ 메시지 생성 완료!")
        progress_bar.progress(100)
        
        # 완료 메시지
        success_info = f"""
        🎉 **메시지 생성 완료!**
        
        📊 **처리 결과:**
        - 📁 처리된 그룹 수: **{len(group_data)}개**
        - 📝 생성된 메시지 수: **{result['total_count']}개**
        """
        
        st.success(success_info)
        
        progress_bar.empty()
        status_text.empty()

    except Exception as e:
        show_error_details(e, "데이터 처리 및 메시지 생성 중")
        raise

# main_app.py 파일에서 show_results_step 함수를 아래 코드로 교체하세요.

def show_results_step():
    st.header("5️⃣ 결과 확인")

    if not st.session_state.get('generated_messages'):
        st.warning("⚠️ 생성된 메시지가 없습니다. 이전 단계에서 메시지를 생성해주세요.")
        if st.button("⬅️ 이전 단계로"):
            st.session_state.current_step = 4
            st.rerun()
        return

    total_messages = len(st.session_state.generated_messages)
    st.success(f"✅ 총 {total_messages}개의 메시지가 생성되었습니다!")

    # 그룹 선택 UI
    group_options = []
    # 생성된 메시지를 엑셀 순서대로 정렬하여 보여주기
    sorted_messages = sorted(st.session_state.generated_messages.items(), key=lambda item: item[1]['group_info'].get('excel_order', 0))
    
    for group_id, data in sorted_messages:
        group_info = data['group_info']
        group_options.append(f"{group_id} - {group_info['team_name']} ({group_info.get('sender', '')}님 그룹)")
    
    selected_group_label = st.selectbox("📋 확인할 그룹을 선택하세요:", group_options)

    if selected_group_label:
        # 선택된 레이블에서 group_id 추출
        selected_group_id = selected_group_label.split(' ')[0]
        message_data = st.session_state.generated_messages[selected_group_id]
        group_info = message_data['group_info']
        message = message_data['message']

        # 그룹 정보 표시
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("팀명", group_info.get('team_name', 'N/A'))
        with col2:
            st.metric("대표자", group_info.get('sender', 'N/A'))
        with col3:
            st.metric("인원수", f"{group_info.get('group_size', 0)}명")

        # ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼ [핵심 수정 부분] ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
        # st.markdown 대신 st.text_area를 사용하여 안정적으로 메시지 표시
        st.markdown("**📱 생성된 메시지 (아래 박스를 클릭하여 쉽게 복사하세요)**")
        st.text_area(
            label="Generated Message",
            value=message,
            height=300,
            disabled=True,  # 사용자가 수정은 못하게 막음
            label_visibility="collapsed",
            help="이 박스 안의 텍스트는 마우스로 쉽게 선택하고 복사(Ctrl+C)할 수 있습니다."
        )
        # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

    st.markdown("---")

    # 전체 다운로드 섹션
    st.markdown("**📥 전체 결과 다운로드**")
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        txt_content = create_text_download()
        st.download_button(
            label="📄 모든 메시지 텍스트로 다운로드",
            data=txt_content,
            file_name=f"travel_messages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    with col_dl2:
        excel_content = create_excel_download()
        st.download_button(
            label="📊 모든 메시지 엑셀로 다운로드",
            data=excel_content,
            file_name=f"travel_messages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    # 네비게이션
    st.markdown("---")
    col_nav1, col_nav2 = st.columns([1, 1])
    with col_nav1:
        if col_nav1.button("⬅️ 이전 단계 (템플릿 설정)", use_container_width=True):
            st.session_state.current_step = 3
            st.rerun()
    with col_nav2:
        if col_nav2.button("🔄 처음부터 새로 시작", use_container_width=True):
            # 세션 상태 초기화
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state.current_step = 1
            st.rerun()
            
def create_text_download():
    """텍스트 파일 다운로드 컨텐츠 생성"""
    content = []
    
    for group_id, data in st.session_state.generated_messages.items():
        group_info = data['group_info']
        message = data['message']
        
        content.append(f"=== {group_id} ({group_info['team_name']}-{group_info['sender_group']}) ===")
        content.append(f"발송인: {group_info['sender']}")
        content.append(f"대상자: {', '.join(group_info['members'])}")
        content.append(f"연락처: {group_info.get('contact', '')}")
        content.append("-" * 60)
        content.append(message)
        content.append("\n" + "="*60 + "\n")
    
    return "\n".join(content)

def create_excel_download():
    """엑셀 파일 다운로드 컨텐츠 생성"""
    data = []
    
    for group_id, message_data in st.session_state.generated_messages.items():
        group_info = message_data['group_info']
        message = message_data['message']
        
        data.append({
            '그룹ID': group_id,
            '팀명': group_info['team_name'],
            '발송그룹': group_info['sender_group'],
            '발송인': group_info['sender'],
            '연락처': group_info.get('contact', ''),
            '그룹멤버': ', '.join(group_info['members']),
            '인원수': group_info['group_size'],
            '메시지': message
        })
    
    df = pd.DataFrame(data)
    
    # 엑셀 파일을 메모리에 생성
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='메시지')
    
    return output.getvalue()

if __name__ == "__main__":
    main()