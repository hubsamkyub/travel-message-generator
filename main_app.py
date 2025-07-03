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

def show_mapping_step():
    st.header("2️⃣ 매핑 설정")

    if 'uploaded_file' not in st.session_state:
        create_info_card(
            "파일이 필요합니다", "먼저 엑셀 파일을 업로드해주세요.", "⚠️", "warning"
        )
        if st.button("⬅️ 이전 단계로"):
            st.session_state.current_step = 1
            st.rerun()
        return

    create_info_card(
        "매핑 설정 안내",
        """
        • **기본 설정**: 고정 정보의 셀 주소와 데이터 테이블의 헤더 행 번호를 입력합니다.
        • **동적 컬럼 매핑**: 엑셀의 각 컬럼에 사용할 **변수명을 지정**합니다. 이 변수명은 템플릿에서 `{변수명}` 형태로 사용됩니다.
        • **필수 매핑**: `team_name`, `sender_group`, `name` 변수는 반드시 하나 이상의 컬럼과 매핑되어야 합니다.
        """,
        "🔧"
    )

    # 탭 구조를 2개로 재구성
    tab1, tab2 = st.tabs(["⚙️ 기본 설정 (고정 정보, 테이블)", "🔗 동적 컬럼 매핑"])
    
    # 탭1: 고정 정보 및 테이블 설정
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
            "📋 헤더 행 번호 (컬럼명이 있는 행)", min_value=1, max_value=50, value=st.session_state.get("header_row", 9),
            help="1부터 시작하는 행 번호를 입력하세요."
        )

        # UI 상태 유지를 위해 세션에 값 저장
        st.session_state.product_name_cell = product_name_cell
        st.session_state.payment_due_cell = payment_due_cell
        st.session_state.base_exchange_cell = base_exchange_cell
        st.session_state.current_exchange_cell = current_exchange_cell
        st.session_state.header_row = header_row

    # 탭2: 동적 컬럼 매핑
    with tab2:
        st.markdown("### 🔗 동적 컬럼 매핑")
        st.markdown("엑셀의 각 컬럼에 사용할 변수명을 지정하거나 수정하세요.")

        try:
            # 헤더 행 번호를 기준으로 데이터프레임 다시 읽기
            df_table = pd.read_excel(
                st.session_state.uploaded_file,
                sheet_name=st.session_state.selected_sheet,
                header=header_row - 1
            ).dropna(how='all', axis=1) # 값이 모두 비어있는 컬럼은 무시

            available_columns = df_table.columns.tolist()

            # 동적 매핑 초기화 또는 자동 재생성
            if 'dynamic_mappings' not in st.session_state or st.button("🔄 변수명 자동 생성"):
                st.session_state.dynamic_mappings = {col: generate_variable_name(str(col)) for col in available_columns}
                st.success("✅ 변수명이 자동으로 생성되었습니다.")

            # UI 컬럼 헤더
            col_h1, col_h2, col_h3 = st.columns([2, 2, 1])
            col_h1.markdown("**엑셀 컬럼**")
            col_h2.markdown("**프로그램 변수명**")
            col_h3.markdown("**필수 지정**")
            
            # 동적 매핑 UI 생성
            final_column_mappings = {}
            for col_header in available_columns:
                c1, c2, c3 = st.columns([2, 2, 1])
                c1.markdown(f"`{col_header}`")
                
                # 사용자가 변수명 입력
                var_name = c2.text_input(
                    f"var_for_{col_header}",
                    value=st.session_state.dynamic_mappings.get(col_header, ""),
                    label_visibility="collapsed"
                )
                
                # 필수 변수 지정
                with c3:
                    is_team = st.checkbox("팀", key=f"team_{col_header}", help="이 컬럼을 'team_name'으로 지정합니다.")
                    is_group = st.checkbox("그룹", key=f"group_{col_header}", help="이 컬럼을 'sender_group'으로 지정합니다.")
                    is_name = st.checkbox("이름", key=f"name_{col_header}", help="이 컬럼을 'name'으로 지정합니다.")

                # 체크박스에 따라 변수명 강제 지정
                if is_team: var_name = "team_name"
                if is_group: var_name = "sender_group"
                if is_name: var_name = "name"
                
                if var_name:
                    final_column_mappings[col_header] = var_name

            # 필수 변수 매핑 확인
            mapped_vars = final_column_mappings.values()
            missing_required = [v for v in ['team_name', 'sender_group', 'name'] if v not in mapped_vars]
            if missing_required:
                st.error(f"**필수 변수 미지정:** `{', '.join(missing_required)}`을(를) 컬럼과 매핑해주세요.")

            # 최종 매핑 정보 구성
            st.session_state.mapping_data = {
                "fixed_data_mapping": {
                    "product_name": product_name_cell,
                    "payment_due_date": payment_due_cell,
                    "base_exchange_rate": base_exchange_cell,
                    "current_exchange_rate": current_exchange_cell,
                },
                "table_settings": {"header_row": header_row},
                "column_mappings": final_column_mappings
            }
            
            with st.expander("📋 현재 매핑 요약 보기"):
                st.json(st.session_state.mapping_data)

        except Exception as e:
            show_error_details(e, "테이블 데이터를 읽는 중")
            st.markdown("**💡 해결 방법:**\n- 헤더 행 번호가 올바른지 확인하세요.\n- 선택한 시트에 데이터가 있는지 확인하세요.")
            missing_required = ['team_name'] # 다음 단계 버튼 비활성화를 위해 임의값 설정

    # 네비게이션 버튼
    st.markdown("---")
    col_nav1, col_nav2 = st.columns([1, 1])
    with col_nav1:
        if st.button("⬅️ 이전 단계", use_container_width=True):
            st.session_state.current_step = 1
            st.rerun()
    with col_nav2:
        # 필수 변수가 모두 매핑되었을 때만 다음 단계 버튼 활성화
        is_disabled = 'missing_required' in locals() and bool(missing_required)
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
    
    if 'mapping_data' not in st.session_state:
        create_info_card(
            "매핑 설정이 필요합니다",
            "먼저 매핑 설정을 완료해주세요.",
            "⚠️",
            "warning"
        )
        if st.button("⬅️ 이전 단계로"):
            st.session_state.current_step = 2
            st.rerun()
        return
    
    # 템플릿 안내 정보
    create_info_card(
        "템플릿 작성 가이드",
        """
        • **변수 사용**: `{변수명}` 형태로 사용 (예: {product_name})
        • **숫자 포맷**: `{금액:,}` 형태로 콤마 표시 (예: {total_balance:,}원)
        • **미리보기**: 실시간으로 결과를 확인할 수 있습니다
        • **자동 완성**: 사용 가능한 변수를 참조하세요
        """,
        "📝"
    )
    
    # 기본 템플릿
    default_template = """[여행처럼]
잔금 입금 안내

안녕하세요, 여행처럼입니다.
{product_name} 예약 건 관련하여
잔금 결제를 요청드리고자 연락드립니다.

※상품가는 현금가 기준으로 현금 이체해주셔야 하며 카드 결제 시
2.5%의 카드수수료가 발생하는 점 참고 부탁드리겠습니다.

더불어 현재 환율이 저희 여행사에서 계획했던 예산에서
약 {exchange_rate_diff}원 상승하여 아래와 같이 추가요금이 발생되었습니다.

ㆍ상품 판매 기준환율 {base_exchange_rate:,}원
ㆍ현재 매매 기준환율 {current_exchange_rate:,}원
ㆍ환율 {exchange_rate_diff}원 인상으로 인한 1인당 추가요금 {additional_fee_per_person:,}원

[결제내역]
{group_members_text}
상품가 + 환차금 - 예약금 - 항공료 = {total_balance:,}원

ㆍ잔금 : {total_balance:,}원
ㆍ잔금 완납일 : {payment_due_date}

아래 계좌로 송금 부탁드립니다.
*{bank_account}*

감사합니다. ^^"""

    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("### 📝 메시지 템플릿 편집")
        
        # 템플릿 편집기
        template = st.text_area(
            "템플릿 내용",
            value=st.session_state.get('template', default_template),
            height=500,
            help="변수는 {변수명} 형태로 사용하세요. 예: {product_name}, {total_balance:,}",
            key="template_editor"
        )
        
        # 템플릿 저장
        st.session_state.template = template
        
        # 템플릿 액션 버튼
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            if st.button("🔄 기본 템플릿으로 리셋", help="기본 템플릿으로 초기화"):
                st.session_state.template = default_template
                st.rerun()
        
        with col_b:
            if st.button("💾 템플릿 저장", help="현재 템플릿을 파일로 저장"):
                st.download_button(
                    label="📄 템플릿 다운로드",
                    data=template,
                    file_name=f"template_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
        
        with col_c:
            uploaded_template = st.file_uploader(
                "📁 템플릿 불러오기",
                type=['txt'],
                help="저장된 템플릿 파일을 업로드"
            )
            if uploaded_template:
                template_content = uploaded_template.read().decode('utf-8')
                st.session_state.template = template_content
                st.success("✅ 템플릿이 불러와졌습니다!")
                st.rerun()
    
    with col2:
        st.markdown("### 💡 사용 가능한 변수")
        
        # 탭으로 변수 분류
        var_tab1, var_tab2, var_tab3 = st.tabs(["기본 정보", "그룹 정보", "계산 변수"])
        
        with var_tab1:
            st.markdown("""
            **🏷️ 상품 정보:**
            - `{product_name}` - 상품명
            - `{payment_due_date}` - 잔금완납일
            
            **💱 환율 정보:**
            - `{base_exchange_rate:,}` - 기준환율
            - `{current_exchange_rate:,}` - 현재환율
            - `{exchange_rate_diff}` - 환율차액
            - `{company_burden:,}` - 당사부담금
            """)
        
        with var_tab2:
            st.markdown("""
            **👥 그룹 정보:**
            - `{team_name}` - 팀명
            - `{sender_group}` - 발송그룹
            - `{group_members_text}` - 멤버 목록
            - `{group_size}` - 그룹 인원수
            
            **💰 금액 정보:**
            - `{total_balance:,}` - 총 잔금
            - `{bank_account}` - 계좌정보
            - `{contact}` - 연락처
            """)
        
        with var_tab3:
            st.markdown("""
            **🧮 자동 계산:**
            - `{additional_fee_per_person:,}` - 1인당 추가요금
            - `{product_price:,}` - 상품가
            - `{exchange_fee:,}` - 환차금
            - `{deposit:,}` - 예약금
            
            **📝 형식 예시:**
            - 콤마 표시: `{금액:,}원`
            - 일반 텍스트: `{변수명}`
            """)
        
        # 매핑된 컬럼 기반 추천 변수
        if 'mapping_data' in st.session_state:
            optional_cols = st.session_state.mapping_data.get('optional_columns', {})
            if optional_cols:
                st.markdown("### 🎯 매핑된 변수")
                for excel_col, var_name in optional_cols.items():
                    st.code(f"{{{var_name}}}")
        
        # 변수 삽입 도구
        st.markdown("### ⚡ 빠른 삽입")
        quick_vars = {
            "상품명": "{product_name}",
            "총 잔금": "{total_balance:,}원",
            "멤버 목록": "{group_members_text}",
            "완납일": "{payment_due_date}",
            "계좌": "{bank_account}"
        }
        
        for label, var_code in quick_vars.items():
            if st.button(f"➕ {label}", key=f"insert_{label}", help=f"{var_code} 삽입"):
                st.info(f"복사: `{var_code}`")
    
    # 템플릿 미리보기
    st.markdown("---")
    st.markdown("### 🔍 템플릿 미리보기")
    
    with st.container():
        # 미리보기 샘플 데이터 생성
        sample_data = {
            'product_name': '하와이 힐링 7일',
            'payment_due_date': '2024-12-20',
            'base_exchange_rate': 1300,
            'current_exchange_rate': 1350,
            'exchange_rate_diff': 50,
            'company_burden': 20,
            'team_name': '1팀',
            'sender_group': 'A그룹',
            'group_members_text': '김철수님, 이영희님',
            'group_size': 2,
            'total_balance': 3480000,
            'bank_account': '국민은행 123-456-789 (주)여행사',
            'additional_fee_per_person': 70,
            'contact': '010-1234-5678',
            'product_price': 2800000,
            'exchange_fee': 40000,
            'deposit': 500000
        }
        
        try:
            show_template_preview(template, sample_data)
            
            # 사용된 변수 분석
            template_vars = set(re.findall(r'\{(\w+)(?::[^}]+)?\}', template))
            
            col_info1, col_info2, col_info3 = st.columns(3)
            with col_info1:
                st.metric("사용된 변수 수", len(template_vars))
            with col_info2:
                missing_vars = [var for var in template_vars if var not in sample_data]
                st.metric("누락된 변수", len(missing_vars))
            with col_info3:
                st.metric("템플릿 길이", f"{len(template)} 자")
            
            if missing_vars:
                st.warning(f"⚠️ 누락된 변수: {', '.join(missing_vars)}")
                st.markdown("매핑 설정에서 해당 변수를 추가하거나 템플릿에서 제거하세요.")
            
        except Exception as e:
            show_error_details(e, "템플릿 미리보기 생성 중")
    
    # 네비게이션 버튼
    st.markdown("---")
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("⬅️ 이전 단계", use_container_width=True):
            st.session_state.current_step = 2
            st.rerun()
    with col2:
        if st.button("➡️ 다음 단계: 메시지 생성", type="primary", use_container_width=True):
            # 템플릿 유효성 검사
            try:
                template_vars = set(re.findall(r'\{(\w+)(?::[^}]+)?\}', template))
                basic_vars = {'product_name', 'team_name', 'group_members_text'}
                
                if not any(var in template_vars for var in basic_vars):
                    st.warning("⚠️ 기본 변수(상품명, 팀명, 멤버 등) 중 하나는 포함되어야 합니다.")
                else:
                    st.session_state.current_step = 4
                    st.success("✅ 메시지 생성 단계로 이동합니다!")
                    st.rerun()
                    
            except Exception as e:
                st.error(f"템플릿 검증 중 오류: {str(e)}")

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

def show_results_step():
    st.header("5️⃣ 결과 확인")
    
    if not st.session_state.generated_messages:
        st.warning("⚠️ 생성된 메시지가 없습니다.")
        if st.button("⬅️ 이전 단계로"):
            st.session_state.current_step = 4
            st.rerun()
        return
    
    st.success(f"✅ 총 {len(st.session_state.generated_messages)}개의 메시지가 생성되었습니다!")
    
    # 그룹 선택
    group_options = []
    for group_id, data in st.session_state.generated_messages.items():
        group_info = data['group_info']
        group_options.append(f"{group_id} - {group_info['team_name']} ({group_info['sender_group']})")
    
    selected_group = st.selectbox("📋 확인할 그룹을 선택하세요:", group_options)
    
    if selected_group:
        group_id = selected_group.split(' ')[0]
        message_data = st.session_state.generated_messages[group_id]
        group_info = message_data['group_info']
        message = message_data['message']
        
        # 그룹 정보 표시
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("팀명", group_info['team_name'])
        with col2:
            st.metric("발송그룹", group_info['sender_group'])
        with col3:
            st.metric("인원수", f"{group_info['group_size']}명")
        
        st.markdown("**👥 그룹 멤버:**")
        st.write(", ".join(group_info['members']))
        
        # 메시지 표시
        st.markdown("**📱 생성된 메시지:**")
        st.markdown(f'<div class="message-preview">{message}</div>', unsafe_allow_html=True)
        
        # 메시지 복사 버튼
        if st.button("📋 클립보드에 복사", key=f"copy_{group_id}"):
            st.success("✅ 메시지가 클립보드에 복사되었습니다!")
    
    st.markdown("---")
    
    # 전체 다운로드 섹션
    st.markdown("**📥 전체 결과 다운로드**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 텍스트 파일 다운로드
        if st.button("📄 텍스트 파일 다운로드", type="primary"):
            txt_content = create_text_download()
            st.download_button(
                label="💾 messages.txt 다운로드",
                data=txt_content,
                file_name=f"travel_messages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
    
    with col2:
        # 엑셀 파일 다운로드
        if st.button("📊 엑셀 파일 다운로드", type="secondary"):
            excel_content = create_excel_download()
            st.download_button(
                label="💾 messages.xlsx 다운로드",
                data=excel_content,
                file_name=f"travel_messages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    # 네비게이션
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("⬅️ 이전 단계"):
            st.session_state.current_step = 4
            st.rerun()
    with col2:
        if st.button("🔄 새로 시작", type="secondary"):
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