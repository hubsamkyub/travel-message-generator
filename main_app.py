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

    # PresetManager 인스턴스 생성
    preset_manager = PresetManager()

    if 'uploaded_file' not in st.session_state:
        create_info_card("파일이 필요합니다", "먼저 엑셀 파일을 업로드해주세요.", "⚠️", "warning")
        if st.button("⬅️ 이전 단계로"):
            st.session_state.current_step = 1
            st.rerun()
        return

    # --- 탭 UI 구성 ---
    tab1, tab2, tab3 = st.tabs(["⚙️ 기본 설정", "🔗 동적 컬럼 매핑", "💾 프리셋 관리"])

    # 탭 1: 고정 정보 및 테이블 설정
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

    # 탭 2: 동적 컬럼 매핑
    with tab2:
        try:
            df_table = pd.read_excel(st.session_state.uploaded_file, sheet_name=st.session_state.selected_sheet, header=header_row - 1).dropna(how='all', axis=1)
            available_columns = ["선택 안 함"] + df_table.columns.tolist()

            # 파일이 바뀌면 매핑을 다시 하도록 상태 초기화
            if 'current_file_id' not in st.session_state or st.session_state.current_file_id != st.session_state.uploaded_file.file_id:
                st.session_state.current_file_id = st.session_state.uploaded_file.file_id
                if 'auto_mapping_done' in st.session_state:
                    del st.session_state.auto_mapping_done

            # 자동 매핑 로직
            if 'auto_mapping_done' not in st.session_state:
                default_preset = preset_manager.load_preset('default')
                preset_mappings = default_preset.get('mapping_data', {}).get('dynamic_mappings', {}) if default_preset else {}
                preset_required = default_preset.get('mapping_data', {}).get('required_selections', {}) if default_preset else {}

                def find_best_match(columns, keywords, preset_val):
                    if preset_val and preset_val in columns: return preset_val
                    for keyword in keywords:
                        for col in columns:
                            if keyword in str(col): return col
                    return "선택 안 함"

                st.session_state.team_col_selection = find_best_match(df_table.columns, ['팀'], preset_required.get('team_col'))
                st.session_state.sender_group_selection = find_best_match(df_table.columns, ['그룹', '발송'], preset_required.get('sender_group_col'))
                st.session_state.name_col_selection = find_best_match(df_table.columns, ['이름', '성명'], preset_required.get('name_col'))

                st.session_state.dynamic_mappings = {}
                for col in df_table.columns:
                    st.session_state.dynamic_mappings[col] = preset_mappings.get(col, generate_variable_name(str(col)))
                
                st.session_state.auto_mapping_done = True
                if default_preset: st.toast("⭐ 기본 프리셋을 적용하여 변수명을 복원했습니다.")

            st.markdown("#### 🔴 필수 변수 지정")
            required_cols = st.columns(3)
            team_col = required_cols[0].selectbox("팀(team_name) 컬럼", available_columns, index=available_columns.index(st.session_state.get("team_col_selection", "선택 안 함")))
            sender_group_col = required_cols[1].selectbox("그룹(sender_group) 컬럼", available_columns, index=available_columns.index(st.session_state.get("sender_group_selection", "선택 안 함")))
            name_col = required_cols[2].selectbox("이름(name) 컬럼", available_columns, index=available_columns.index(st.session_state.get("name_col_selection", "선택 안 함")))

            st.session_state.team_col_selection = team_col
            st.session_state.sender_group_selection = sender_group_col
            st.session_state.name_col_selection = name_col
            
            missing_required = [label for label, col in zip(['팀', '그룹', '이름'], [team_col, sender_group_col, name_col]) if col == "선택 안 함"]
            if missing_required:
                st.error(f"**필수 변수 미지정:** `{', '.join(missing_required)}`에 해당하는 컬럼을 선택해주세요.")

            st.markdown("---")
            st.markdown("#### 🔵 선택 변수 지정 (템플릿에 사용할 추가 정보)")
            
            optional_columns = [col for col in df_table.columns if col not in [team_col, sender_group_col, name_col]]
            
            if st.button("🔄 선택 변수명 자동 생성"):
                st.session_state.dynamic_mappings.update({col: generate_variable_name(str(col)) for col in optional_columns})

            ui_cols = st.columns(2)
            ui_cols[0].markdown("**엑셀 컬럼**")
            ui_cols[1].markdown("**프로그램 변수명**")

            for col_header in optional_columns:
                c1, c2 = st.columns(2)
                c1.markdown(f"`{col_header}`")
                st.session_state.dynamic_mappings[col_header] = c2.text_input(f"var_for_{col_header}", value=st.session_state.dynamic_mappings.get(col_header, ""), label_visibility="collapsed")
            
        except Exception as e:
            st.error(f"테이블 데이터를 읽는 중 오류가 발생했습니다: {e}")
            missing_required = ['팀']

    # 탭3: 프리셋 관리
    with tab3:
        st.markdown("### 💾 매핑 프리셋 관리")
        presets = preset_manager.get_preset_list()
        all_preset_options = {p['name']: p['id'] for p in presets}
        
        st.markdown("#### ⭐ 기본 프리셋 설정")
        default_preset_data = preset_manager.load_preset('default')
        st.info(f"현재 기본 프리셋: **{default_preset_data['name'] if default_preset_data else '없음'}** (파일 업로드 시 자동 적용)")

        set_default_preset_name = st.selectbox("기본으로 사용할 프리셋 선택", list(all_preset_options.keys()))
        if st.button("⭐ 기본으로 설정", disabled=not set_default_preset_name):
            preset_id = all_preset_options[set_default_preset_name]
            preset_data = preset_manager.load_preset(preset_id)
            if preset_data:
                preset_manager.save_preset('default', preset_data)
                st.success(f"'{set_default_preset_name}'을(를) 기본 프리셋으로 설정했습니다.")
                st.rerun()

        st.markdown("---")
        st.markdown("#### 📂 프리셋 목록")
        preset_to_load = st.selectbox("프리셋 불러오기", ["선택 안 함"] + list(all_preset_options.keys()))
        if st.button("🔄 프리셋 적용하기", disabled=(preset_to_load == "선택 안 함")):
            preset_id = all_preset_options[preset_to_load]
            preset_data = preset_manager.load_preset(preset_id)
            if preset_data:
                mapping = preset_data.get('mapping_data', {})
                st.session_state.update(mapping.get('fixed_settings', {}))
                st.session_state.update(mapping.get('required_selections', {}))
                st.session_state.dynamic_mappings = mapping.get('dynamic_mappings', {})
                st.session_state.auto_mapping_done = True
                st.success(f"'{preset_to_load}' 프리셋을 적용했습니다.")
                st.rerun()
        
        st.markdown("---")
        st.markdown("#### 현재 매핑 설정 저장하기")
        new_preset_name = st.text_input("저장할 프리셋 이름")
        if st.button("💾 현재 설정 저장", disabled=not new_preset_name):
            current_mapping_data = {
                "fixed_settings": { "product_name_cell": product_name_cell, "payment_due_cell": payment_due_cell, "base_exchange_cell": base_exchange_cell, "current_exchange_cell": current_exchange_cell, "header_row": header_row },
                "required_selections": { "team_col_selection": team_col, "sender_group_selection": sender_group_col, "name_col_selection": name_col },
                "dynamic_mappings": {k: v for k, v in st.session_state.get('dynamic_mappings', {}).items() if k in df_table.columns}
            }
            preset_manager.save_preset(new_preset_name, {"name": new_preset_name, "mapping_data": current_mapping_data})
            st.success(f"'{new_preset_name}' 프리셋을 저장했습니다.")
            st.rerun()

    # --- 최종 매핑 정보 구성 및 네비게이션 ---
    final_column_mappings = {}
    if 'team_col' in locals() and team_col != "선택 안 함": final_column_mappings[team_col] = 'team_name'
    if 'sender_group_col' in locals() and sender_group_col != "선택 안 함": final_column_mappings[sender_group_col] = 'sender_group'
    if 'name_col' in locals() and name_col != "선택 안 함": final_column_mappings[name_col] = 'name'
    
    if 'optional_columns' in locals():
        for col, var_name in st.session_state.get('dynamic_mappings', {}).items():
            if col in optional_columns and var_name:
                final_column_mappings[col] = var_name
    
    st.session_state.mapping_data = {
        "fixed_data_mapping": { "product_name": product_name_cell, "payment_due_date": payment_due_cell, "base_exchange_rate": base_exchange_cell, "current_exchange_rate": current_exchange_cell },
        "table_settings": { "header_row": header_row },
        "column_mappings": final_column_mappings
    }
    
    st.markdown("---")
    nav_cols = st.columns([1, 1])
    with nav_cols[0]:
        if st.button("⬅️ 이전 단계 (파일 업로드)", use_container_width=True):
            st.session_state.current_step = 1
            del st.session_state.auto_mapping_done
            st.rerun()
    with nav_cols[1]:
        is_disabled = 'missing_required' in locals() and bool(missing_required)
        if st.button("➡️ 다음 단계 (템플릿 설정)", type="primary", use_container_width=True, disabled=is_disabled):
            # 문제 3 해결: 성공적인 매핑 설정을 'default' 프리셋으로 저장
            preset_manager.save_preset('default', {"name": "Last Used Setting", "mapping_data": st.session_state.mapping_data})
            
            st.session_state.current_step = 3
            st.success("✅ 매핑 설정이 완료되었습니다. 다음 단계로 이동합니다.")
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

    # --- 1. 변수 및 데이터 준비 ---
    fixed_data_mapping = st.session_state.mapping_data.get('fixed_data_mapping', {})
    column_mappings = st.session_state.mapping_data.get('column_mappings', {})
    header_row = st.session_state.mapping_data.get('table_settings', {}).get('header_row', 1)
    fixed_vars = list(fixed_data_mapping.keys())
    dynamic_vars = list(column_mappings.values())
    calculated_vars = ['group_members_text', 'group_size', 'additional_fee_per_person']
    all_available_vars = sorted(list(set(fixed_vars + dynamic_vars + calculated_vars)))

    preview_variables = {}
    try:
        df_table = pd.read_excel(st.session_state.uploaded_file, sheet_name=st.session_state.selected_sheet, header=header_row - 1)
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

    # --- 2. 사이드바: 템플릿 라이브러리 ---
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🗂️ 내 템플릿 라이브러리")
        templates = template_manager.get_template_list()
        template_options = {t['name']: t['id'] for t in templates}
        if not templates:
            st.info("저장된 템플릿이 없습니다.")
        
        selected_template_name = st.selectbox("라이브러리에서 불러오기", ["선택 안 함"] + list(template_options.keys()))
        
        btn_cols = st.columns(2)
        if btn_cols[0].button("📂 불러오기", use_container_width=True, disabled=(selected_template_name == "선택 안 함")):
            template_id = template_options[selected_template_name]
            loaded_data = template_manager.load_template(template_id)
            if loaded_data:
                st.session_state.template = loaded_data['content']
                st.success(f"'{selected_template_name}'을(를) 불러왔습니다.")
                st.rerun()
        
        if btn_cols[1].button("🗑️ 삭제", use_container_width=True, disabled=(selected_template_name == "선택 안 함")):
            template_id = template_options[selected_template_name]
            if template_manager.delete_template(template_id):
                st.success(f"'{selected_template_name}'을(를) 삭제했습니다.")
                st.rerun()

        st.markdown("---")
        new_template_name = st.text_input("현재 템플릿 저장 이름")
        if st.button("💾 현재 템플릿 저장", disabled=not new_template_name):
            current_template_content = st.session_state.get('template', '')
            try:
                # 문제 2 해결: create_template_from_content를 사용하여 올바른 데이터 구조로 저장
                template_id = template_manager.create_template_from_content(
                    name=new_template_name,
                    content=current_template_content,
                    description=f"Saved from app at {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                )
                # create_template_from_content가 새 ID를 부여하므로, 원래 이름의 ID를 삭제하고 새 ID로 저장
                # 더 나은 방법은 save_template을 직접 사용하되, dictionary를 만들어주는 것
                # 여기서는 TemplateManager의 기존 메서드를 최대한 활용
                st.success(f"'{new_template_name}' 이름으로 저장했습니다.")
                st.rerun()
            except Exception as e:
                st.error(f"템플릿 저장 실패: {e}")


    # --- 3. 메인 화면: 편집기 및 미리보기 ---
    editor_col, preview_col = st.columns(2, gap="large")
    with editor_col:
        st.markdown("##### 📝 메시지 템플릿 편집")
        # 'template' 키가 없으면 기본값으로 초기화
        if 'template' not in st.session_state:
            # 기본 템플릿 로드 시도
            default_tpl = template_manager.load_template('standard')
            st.session_state.template = default_tpl['content'] if default_tpl else "[여행처럼]\n안녕하세요, {product_name} 안내입니다."
        
        template = st.text_area("Template Editor", value=st.session_state.template, height=500, key="template_editor", label_visibility="collapsed")
        st.session_state.template = template
        
        char_count = len(template)
        sms_type = "LMS" if char_count > 90 else "SMS"
        sms_count_str = f"{sms_type} 1건"
        if char_count > 2000: sms_count_str = f"LMS {((char_count - 1) // 2000) + 1}건"
        st.caption(f"글자 수: {char_count}자 | 예상 메시지: {sms_count_str}")
        
    with preview_col:
        show_template_preview(template, preview_variables)

    # --- 4. 스마트 매핑 및 변수 목록 ---
    st.markdown("---")
    
    # 문제 1 해결: st.session_state.mapping_just_applied 플래그 추가
    if 'mapping_just_applied' in st.session_state and st.session_state.mapping_just_applied:
        st.success("✅ 매핑이 적용되었습니다! 템플릿이 업데이트되었습니다.")
        del st.session_state.mapping_just_applied # 메시지 표시 후 플래그 제거

    with st.expander("📂 내 템플릿 파일 가져오기 (스마트 변수 매핑)", expanded=False):
        uploaded_template_file = st.file_uploader(
            "사용자 정의 템플릿 파일(.txt)을 업로드하세요.", type=['txt'],
            key="template_file_uploader"
        )
        
        if uploaded_template_file is not None:
            # 파일이 업로드 되면, 바로 분석 시작
            uploaded_content = uploaded_template_file.getvalue().decode("utf-8")
            template_vars = set(re.findall(r'\{(\w+)(?::[^}]+)?\}', uploaded_content))
            unmapped_vars = [var for var in template_vars if var not in all_available_vars]

            if not unmapped_vars:
                st.session_state.template = uploaded_content
                st.success("✅ 템플릿이 성공적으로 적용되었습니다. 모든 변수가 현재 시스템과 일치합니다.")
                st.rerun() # 성공 시 바로 rerun하여 uploader 초기화
            else:
                st.warning("⚠️ 템플릿의 변수와 시스템 변수가 다릅니다. 아래에서 매핑을 조정해주세요.")
                st.markdown("**스마트 변수 매핑 도우미**")
                
                # 매핑을 위한 딕셔너리 준비
                mapping_selections = {}
                for var in unmapped_vars:
                    cols = st.columns([2, 1, 2])
                    cols[0].markdown(f"템플릿 변수: `{var}`")
                    cols[1].markdown("→")
                    mapping_selections[var] = cols[2].selectbox(f"map_for_{var}", ["선택 안 함"] + all_available_vars, label_visibility="collapsed")

                if st.button("🚀 매핑 적용하고 템플릿 업데이트", type="primary"):
                    new_template = uploaded_content
                    for template_var, system_var in mapping_selections.items():
                        if system_var != "선택 안 함":
                            pattern = r'\{' + re.escape(template_var) + r'(:[^}]+)?\}'
                            replacement = lambda m: f"{{{system_var}{m.group(1) or ''}}}"
                            new_template = re.sub(pattern, replacement, new_template)
                    
                    st.session_state.template = new_template
                    # 문제 1 해결: 플래그 설정 후 rerun
                    st.session_state.mapping_just_applied = True
                    st.rerun()

    st.markdown("---")
    st.markdown("##### 💡 사용 가능한 변수 목록")
    
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
        st.success("✅ 템플릿 설정이 완료되었습니다. 다음 단계로 이동합니다.")
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
# main_app.py 파일에서 show_results_step 함수 전체를 아래 코드로 교체합니다.

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

# create_text_download와 create_excel_download 함수도 수정이 필요합니다.
# 수정된 내용을 다운로드에 반영할 수 있도록 아래 코드로 교체해주세요.

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