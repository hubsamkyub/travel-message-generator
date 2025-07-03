import streamlit as st
import pandas as pd
import re
from datetime import datetime

def show_success_metric(title, value, delta=None):
    """성공 메트릭 표시"""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.metric(
            label=title,
            value=value,
            delta=delta
        )

def show_processing_steps(steps, current_step=0):
    """처리 단계 시각화"""
    cols = st.columns(len(steps))
    
    for i, (col, step) in enumerate(zip(cols, steps)):
        with col:
            if i < current_step:
                st.success(f"✅ {step}")
            elif i == current_step:
                st.info(f"🔄 {step}")
            else:
                st.write(f"⏳ {step}")

def create_info_card(title, content, icon="ℹ️", type="info"):
    """정보 카드 생성"""
    if type == "success":
        st.success(f"{icon} **{title}**\n\n{content}")
    elif type == "warning":
        st.warning(f"{icon} **{title}**\n\n{content}")
    elif type == "error":
        st.error(f"{icon} **{title}**\n\n{content}")
    else:
        st.info(f"{icon} **{title}**\n\n{content}")

def show_data_summary(df, title="데이터 요약"):
    """데이터 요약 정보 표시"""
    with st.expander(f"📊 {title}", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("총 행 수", len(df))
        with col2:
            st.metric("총 열 수", len(df.columns))
        with col3:
            null_count = df.isnull().sum().sum()
            st.metric("빈 셀 수", null_count)
        
        st.markdown("**컬럼 정보:**")
        for i, col in enumerate(df.columns):
            non_null = df[col].notna().sum()
            st.write(f"• {col}: {non_null}/{len(df)} 값")

def highlight_template_variables(template_text):
    """템플릿 변수 하이라이팅 HTML 생성"""
    # 변수 패턴 찾기 {변수명} 또는 {변수명:포맷}
    pattern = r'\{([^}]+)\}'
    
    def replace_var(match):
        var_content = match.group(1)
        var_name = var_content.split(':')[0]  # 포맷 부분 제거
        return f'<span style="background-color: #fff3cd; padding: 2px 4px; border-radius: 3px; font-family: monospace; color: #856404;">{{{var_content}}}</span>'
    
    highlighted = re.sub(pattern, replace_var, template_text)
    return highlighted

def show_template_preview(template, sample_variables=None):
    """템플릿 미리보기"""
    if sample_variables is None:
        sample_variables = {
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
            'additional_fee_per_person': 70
        }
    
    st.markdown("**🔍 템플릿 미리보기:**")
    
    try:
        # 누락된 변수들에 대해 기본값 제공
        template_vars = set(re.findall(r'\{(\w+)(?::[^}]+)?\}', template))
        
        for var in template_vars:
            if var not in sample_variables:
                if any(keyword in var.lower() for keyword in ['price', 'fee', 'amount', 'balance', 'cost', 'money', 'rate', 'size', 'count']):
                    sample_variables[var] = 0
                else:
                    sample_variables[var] = f"[{var}]"
        
        preview_message = template.format(**sample_variables)
        
        st.markdown(
            f'<div style="background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; padding: 15px; font-family: \'Noto Sans KR\', sans-serif; line-height: 1.6; white-space: pre-wrap;">{preview_message}</div>',
            unsafe_allow_html=True
        )
        
    except KeyError as e:
        missing_var = str(e).strip("'")
        st.error(f"❌ 누락된 변수: {{{missing_var}}}")
    except Exception as e:
        st.error(f"❌ 미리보기 생성 오류: {str(e)}")

def show_variable_suggestions(df_columns):
    """변수 제안 표시"""
    st.markdown("**💡 사용 가능한 변수 제안:**")
    
    # 기본 변수들
    basic_vars = [
        "product_name", "payment_due_date", "base_exchange_rate", 
        "current_exchange_rate", "exchange_rate_diff", "company_burden"
    ]
    
    # 그룹 변수들
    group_vars = [
        "team_name", "sender_group", "group_members_text", 
        "group_size", "total_balance", "bank_account"
    ]
    
    # 컬럼에서 추정되는 변수들
    suggested_vars = []
    for col in df_columns:
        col_lower = str(col).lower()
        if any(keyword in col_lower for keyword in ['금액', '요금', '비용', 'price', 'fee', 'amount']):
            var_name = col.replace(' ', '_').replace('-', '_').lower()
            suggested_vars.append(f"{var_name} (from '{col}')")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**기본 정보:**")
        for var in basic_vars:
            st.code(f"{{{var}}}")
    
    with col2:
        st.markdown("**그룹 정보:**")
        for var in group_vars:
            st.code(f"{{{var}}}")
    
    with col3:
        st.markdown("**엑셀 컬럼 기반:**")
        for var in suggested_vars[:5]:  # 최대 5개만 표시
            st.code(f"{{{var.split(' ')[0]}}}")

def show_group_statistics(group_data):
    """그룹 통계 표시"""
    if not group_data:
        return
    
    st.markdown("**📈 그룹 통계**")
    
    # 기본 통계
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 그룹 수", len(group_data))
    
    with col2:
        total_members = sum(group['group_size'] for group in group_data.values())
        st.metric("총 인원 수", total_members)
    
    with col3:
        teams = set(group['team_name'] for group in group_data.values())
        st.metric("팀 수", len(teams))
    
    with col4:
        avg_size = total_members / len(group_data) if group_data else 0
        st.metric("평균 그룹 크기", f"{avg_size:.1f}명")
    
    # 팀별 분포
    team_distribution = {}
    for group in group_data.values():
        team = group['team_name']
        team_distribution[team] = team_distribution.get(team, 0) + 1
    
    if team_distribution:
        st.markdown("**팀별 그룹 분포:**")
        chart_data = pd.DataFrame(
            list(team_distribution.items()),
            columns=['팀', '그룹 수']
        )
        st.bar_chart(chart_data.set_index('팀'))

def create_download_section(generated_messages):
    """다운로드 섹션 생성"""
    st.markdown("---")
    st.markdown("## 📥 결과 다운로드")
    
    if not generated_messages:
        st.warning("생성된 메시지가 없습니다.")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 텍스트 파일 다운로드
        txt_content = create_text_download_content(generated_messages)
        st.download_button(
            label="📄 텍스트 파일 다운로드",
            data=txt_content,
            file_name=f"messages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            help="모든 메시지를 텍스트 파일로 다운로드합니다."
        )
    
    with col2:
        # 엑셀 파일 다운로드
        excel_content = create_excel_download_content(generated_messages)
        st.download_button(
            label="📊 엑셀 파일 다운로드", 
            data=excel_content,
            file_name=f"messages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="그룹 정보와 메시지를 엑셀 파일로 다운로드합니다."
        )
    
    with col3:
        # CSV 파일 다운로드
        csv_content = create_csv_download_content(generated_messages)
        st.download_button(
            label="📋 CSV 파일 다운로드",
            data=csv_content,
            file_name=f"messages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            help="그룹 정보를 CSV 파일로 다운로드합니다."
        )

def create_text_download_content(generated_messages):
    """텍스트 다운로드 컨텐츠 생성"""
    content = []
    content.append(f"여행 잔금 문자 메시지")
    content.append(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    content.append(f"총 {len(generated_messages)}개 그룹")
    content.append("=" * 60)
    content.append("")
    
    for group_id, data in generated_messages.items():
        group_info = data['group_info']
        message = data['message']
        
        content.append(f"[{group_id}] {group_info['team_name']} - {group_info['sender_group']}")
        content.append(f"발송인: {group_info['sender']}")
        content.append(f"대상자: {', '.join(group_info['members'])} ({group_info['group_size']}명)")
        content.append(f"연락처: {group_info.get('contact', '')}")
        content.append("-" * 40)
        content.append(message)
        content.append("")
        content.append("=" * 60)
        content.append("")
    
    return "\n".join(content)

def create_excel_download_content(generated_messages):
    """엑셀 다운로드 컨텐츠 생성"""
    import io
    
    data = []
    for group_id, message_data in generated_messages.items():
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
            '총잔금': group_info.get('total_balance', ''),
            '메시지': message
        })
    
    df = pd.DataFrame(data)
    
    # 메모리에 엑셀 파일 생성
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='메시지목록')
        
        # 워크시트 스타일링
        workbook = writer.book
        worksheet = writer.sheets['메시지목록']
        
        # 헤더 스타일
        from openpyxl.styles import Font, PatternFill
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        
        for col_num, column_title in enumerate(df.columns, 1):
            cell = worksheet.cell(row=1, column=col_num)
            cell.font = header_font
            cell.fill = header_fill
        
        # 열 너비 조정
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    return output.getvalue()

def create_csv_download_content(generated_messages):
    """CSV 다운로드 컨텐츠 생성"""
    data = []
    for group_id, message_data in generated_messages.items():
        group_info = message_data['group_info']
        
        data.append({
            '그룹ID': group_id,
            '팀명': group_info['team_name'],
            '발송그룹': group_info['sender_group'],
            '발송인': group_info['sender'],
            '연락처': group_info.get('contact', ''),
            '그룹멤버': ', '.join(group_info['members']),
            '인원수': group_info['group_size'],
            '총잔금': group_info.get('total_balance', '')
        })
    
    df = pd.DataFrame(data)
    return df.to_csv(index=False, encoding='utf-8-sig')

def show_error_details(error, context=""):
    """상세 오류 정보 표시"""
    st.error(f"❌ **오류 발생** {context}")
    
    with st.expander("🔧 상세 오류 정보", expanded=False):
        st.code(f"""
오류 타입: {type(error).__name__}
오류 메시지: {str(error)}
        """)
        
        # 일반적인 해결 방법 제시
        if "KeyError" in str(type(error)):
            st.markdown("""
            **💡 해결 방법:**
            - 템플릿의 변수명이 매핑된 변수와 일치하는지 확인
            - 매핑 설정에서 누락된 컬럼이 있는지 확인
            """)
        elif "ValueError" in str(type(error)):
            st.markdown("""
            **💡 해결 방법:**
            - 숫자 포맷팅({변수:,})을 문자 변수에 사용했는지 확인
            - 엑셀 데이터의 형식이 올바른지 확인
            """)
        elif "FileNotFoundError" in str(type(error)):
            st.markdown("""
            **💡 해결 방법:**
            - 파일이 제대로 업로드되었는지 확인
            - 파일 형식이 .xlsx 또는 .xls인지 확인
            """)

def create_help_sidebar():
    """도움말 사이드바 생성"""
    with st.sidebar:
        st.markdown("---")
        st.markdown("## 💡 도움말")
        
        with st.expander("📁 파일 업로드", expanded=False):
            st.markdown("""
            - 지원 형식: .xlsx, .xls
            - 최대 크기: 50MB
            - 고정 정보와 테이블이 같은 시트에 있어야 함
            """)
        
        with st.expander("🔧 매핑 설정", expanded=False):
            st.markdown("""
            - 셀 주소: A1, B2, C3 형태로 입력
            - 필수 컬럼: 팀명, 발송그룹, 이름
            - 헤더 행 번호는 1부터 시작
            """)
        
        with st.expander("📝 템플릿 작성", expanded=False):
            st.markdown("""
            - 변수 사용: {변수명}
            - 숫자 포맷: {금액:,}원
            - 미리보기로 확인 가능
            """)
        
        with st.expander("🚨 문제 해결", expanded=False):
            st.markdown("""
            - 변수 오류: 매핑 설정 확인
            - 포맷 오류: 숫자/문자 변수 구분
            - 파일 오류: 엑셀 파일 형식 확인
            """)

def show_progress_indicator(current_step, total_steps, step_names):
    """진행 상황 표시기"""
    progress = current_step / total_steps
    st.progress(progress)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if current_step <= len(step_names):
            st.write(f"**현재 단계:** {step_names[current_step-1]}")
    with col2:
        st.write(f"{current_step}/{total_steps}")

def format_currency(amount):
    """통화 포맷팅"""
    try:
        return f"{int(amount):,}원"
    except (ValueError, TypeError):
        return "0원"