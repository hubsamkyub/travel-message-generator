import pandas as pd
import re
from datetime import datetime
from collections import defaultdict

class EnhancedDataProcessor:
    """향상된 데이터 처리 클래스"""
    
    def __init__(self):
        self.group_data = {}
        self.fixed_data = {}
        
    def natural_sort_key(self, text):
        """자연 정렬을 위한 키 함수"""
        return [int(part) if part.isdigit() else part.lower() 
                for part in re.split(r'(\d+)', str(text))]
    
    def parse_cell_address(self, cell_address):
        """셀 주소를 행, 열 인덱스로 변환 (A1 -> (0, 0))"""
        if not cell_address or not isinstance(cell_address, str):
            return None, None
            
        try:
            col_str = ''.join(filter(str.isalpha, cell_address.upper()))
            row_str = ''.join(filter(str.isdigit, cell_address))
            
            if not col_str or not row_str:
                return None, None
                
            col_idx = 0
            for i, char in enumerate(reversed(col_str)):
                col_idx += (ord(char) - ord('A') + 1) * (26 ** i)
            col_idx -= 1
            
            row_idx = int(row_str) - 1
            
            return row_idx, col_idx
        except Exception:
            return None, None
    
    def get_cell_value(self, df, cell_address, default=""):
        """DataFrame에서 셀 주소로 값 가져오기"""
        row_idx, col_idx = self.parse_cell_address(cell_address)
        if row_idx is None or col_idx is None:
            return default
            
        try:
            if row_idx < len(df) and col_idx < len(df.columns):
                value = df.iloc[row_idx, col_idx]
                return value if pd.notna(value) else default
            return default
        except Exception:
            return default
    
    def extract_fixed_data(self, df_raw, fixed_mapping):
        """고정 데이터 추출"""
        fixed_data = {}
        for key, cell_addr in fixed_mapping.items():
            value = self.get_cell_value(df_raw, cell_addr)
            if key in ['base_exchange_rate', 'current_exchange_rate', 'exchange_rate_diff', 'company_burden']:
                try:
                    clean_value = str(value).replace(',', '').replace('원', '').replace(' ', '').strip()
                    fixed_data[key] = int(float(clean_value)) if clean_value and clean_value.replace('.', '').replace('-', '').isdigit() else 0
                except (ValueError, TypeError):
                    fixed_data[key] = 0
            else:
                fixed_data[key] = str(value) if value else ""
        self.fixed_data = fixed_data
        return fixed_data
    
    def process_group_data_dynamic(self, customer_df, column_mappings):
        """그룹 데이터 처리 (동적 매핑 및 단순화된 키 저장)"""
        try:
            self.group_data = {}
            reverse_mappings = {v: k for k, v in column_mappings.items()}
            
            team_col = reverse_mappings.get("team_name")
            sender_group_col = reverse_mappings.get("sender_group")
            name_col = reverse_mappings.get("name")

            if not all([team_col, sender_group_col, name_col]):
                raise ValueError("필수 변수(team_name, sender_group, name)가 컬럼과 매핑되지 않았습니다.")

            missing_cols = [col for col in [team_col, sender_group_col, name_col] if col not in customer_df.columns]
            if missing_cols:
                raise ValueError(f"매핑된 필수 컬럼이 엑셀에 없습니다: {', '.join(missing_cols)}")

            groups = customer_df.groupby([team_col, sender_group_col], sort=False)
            
            group_order = {}
            for idx, row in customer_df.iterrows():
                group_key = (row[team_col], row[sender_group_col])
                if pd.notna(group_key[1]) and group_key not in group_order:
                    group_order[group_key] = idx
            
            sorted_group_keys = sorted(group_order.keys(), key=lambda x: group_order[x])
            
            group_id_counter = 1
            for group_key in sorted_group_keys:
                team_name, sender_group = group_key
                group_members = groups.get_group(group_key)
                
                representative = group_members.iloc[0]
                members_list = group_members[name_col].tolist()

                group_info = {
                    'group_id': f"G{group_id_counter:03d}",
                    'team_name': str(team_name),
                    'sender_group': str(sender_group),
                    'sender': str(representative[name_col]),
                    'members': [str(name) for name in members_list],
                    'group_size': len(members_list),
                    'group_members_text': ', '.join([f"{name}님" for name in members_list]),
                    'excel_order': group_order[group_key]
                }

                # [핵심 수정] 모든 컬럼 값을 2가지 방식으로 저장
                for excel_col, var_name in column_mappings.items():
                    if excel_col in representative.index:
                        value = representative[excel_col]
                        
                        # 1. 엑셀 컬럼명 그대로 저장: [컬럼:...] 태그를 위해 사용
                        group_info[excel_col] = str(value) if pd.notna(value) else ""
                        
                        # 2. 변수명으로 저장: {변수} 태그를 위해 사용 (타입 변환 포함)
                        if any(keyword in var_name.lower() for keyword in ['price', 'fee', 'amount', 'balance', 'cost', 'money', '금액', '비용', '요금']):
                            try:
                                clean_value = str(value).replace(',', '').replace('원', '').strip()
                                group_info[var_name] = int(float(clean_value)) if clean_value and clean_value.replace('.', '').replace('-', '').isdigit() else 0
                            except (ValueError, TypeError):
                                group_info[var_name] = 0
                        else:
                            group_info[var_name] = str(value) if pd.notna(value) else ""
                
                self.group_data[group_info['group_id']] = group_info
                group_id_counter += 1

            return self.group_data

        except Exception as e:
            raise Exception(f"동적 그룹 데이터 처리 중 오류: {str(e)}")

class EnhancedMessageGenerator:
    """향상된 메시지 생성 클래스"""
    
    def __init__(self):
        self.generated_messages = {}
        self.column_mappings = {}

    def generate_messages(self, template, group_data, fixed_data):
        """단순화된 로직으로 메시지를 생성"""
        if not group_data:
            raise ValueError("그룹 데이터가 없습니다.")
        
        self.generated_messages = {}

        for group_id, group_info in group_data.items():
            
            # [핵심 수정] 단순하고 직접적인 조회 함수
            def replace_template_tags(match):
                # 태그 타입과 내용 추출
                tag_type = match.group(1) # '컬럼' 또는 '{'
                content = match.group(2).strip() # '고객 부담금' 또는 'product_name'
                formatting = match.group(3) # ':,}
                
                value = None
                
                if tag_type == '컬럼':
                    # 컬럼 태그는 group_info에서 컬럼명으로 직접 찾음
                    value = group_info.get(content)
                else: # '{'
                    # 시스템 변수 태그는 group_info와 fixed_data에서 찾음
                    value = group_info.get(content, fixed_data.get(content))

                if value is None:
                    return f"❌[{content}]"

                # 숫자 포맷팅 적용
                if formatting and ':' in formatting:
                    try:
                        num_value = int(float(str(value).replace(',', '')))
                        return f"{num_value:,}"
                    except (ValueError, TypeError):
                        return str(value)
                
                return str(value)
            
            # 정규식을 통해 모든 태그 ([컬럼:...] 및 {...})를 한 번에 처리
            # 그룹 1: 태그 타입 ('컬럼' 또는 '{')
            # 그룹 2: 태그 내용 (컬럼명 또는 변수명)
            # 그룹 3: 포맷팅 문자열 (예: ':,}')
            pattern = r'\[(컬럼):([^\]:]+)(:[^\]]*)?\]|\{([^}]+?)(:[^},]+)?\}'
            
            # 정규식 치환을 위한 콜백 함수
            def replacer(match):
                # [컬럼:...] 태그가 매칭된 경우
                if match.group(1) == '컬럼':
                    col_name = match.group(2).strip()
                    format_str = match.group(3)
                    value_str = group_info.get(col_name, f"❌[{col_name}]")
                    
                    if format_str and ':' in format_str:
                        try:
                            num_value = int(float(str(value_str).replace(',', '')))
                            return f"{num_value:,}"
                        except (ValueError, TypeError):
                            return value_str
                    return value_str
                # {...} 태그가 매칭된 경우
                else:
                    var_name = match.group(4).strip()
                    format_str = match.group(5)
                    
                    # group_info, fixed_data, 특별 계산 변수 순으로 값 찾기
                    if var_name in group_info:
                        value = group_info[var_name]
                    elif var_name in fixed_data:
                        value = fixed_data[var_name]
                    elif var_name == 'additional_fee_per_person':
                        exchange_fee = group_info.get('exchange_fee', 0)
                        company_burden = fixed_data.get('company_burden', 0)
                        value = exchange_fee + company_burden
                    else:
                        value = f"❌[{var_name}]"
                    
                    if format_str and ':' in format_str:
                        try:
                            num_value = int(float(str(value).replace(',', '')))
                            return f"{num_value:,}"
                        except (ValueError, TypeError):
                            return str(value)
                    return str(value)

            final_message = re.sub(pattern, replacer, template)
            
            self.generated_messages[group_id] = {
                'message': final_message,
                'group_info': group_info
            }

        return {'messages': self.generated_messages, 'total_count': len(self.generated_messages)}

    def get_sorted_messages(self):
        """정렬된 메시지 반환"""
        if not self.generated_messages: return []
        return sorted(self.generated_messages.items(), key=lambda item: item[1]['group_info'].get('excel_order', 0))