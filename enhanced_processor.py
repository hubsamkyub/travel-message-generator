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
            if key in ['base_exchange_rate', 'current_exchange_rate', 'exchange_rate_diff', 'company_burden', 'exchange_burden']:
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
        """그룹 데이터 처리 (동적 매핑 및 group_size 추가)"""
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

                # [해결 코드] 여기에 'group_size'를 추가했습니다.
                group_info = {
                    'group_id': f"G{group_id_counter:03d}",
                    'team_name': str(team_name),
                    'sender_group': str(sender_group),
                    'sender': str(representative[name_col]),
                    'members': [str(name) for name in members_list],
                    'group_size': len(members_list), # 인원수 추가
                    'excel_order': group_order[group_key]
                }

                # 모든 컬럼 값을 엑셀 컬럼명 그대로 저장
                for excel_col in customer_df.columns:
                    if excel_col in representative.index:
                        value = representative[excel_col]
                        group_info[excel_col] = str(value) if pd.notna(value) else ""
                
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
        """단순화되고 안정적인 로직으로 메시지를 생성"""
        if not group_data:
            raise ValueError("그룹 데이터가 없습니다.")
        
        self.generated_messages = {}

        for group_id, group_info in group_data.items():
            # 1. 모든 변수를 하나의 딕셔너리로 통합
            variables = {}
            variables.update(fixed_data)  # 고정 변수
            variables.update(group_info)  # 그룹 변수 (엑셀 컬럼명 키 포함)

            # 2. 특별 계산 변수 추가
            variables['group_size'] = len(group_info.get('members', []))
            variables['group_members_text'] = ', '.join([f"{name}님" for name in group_info.get('members', [])])
            
            # 'additional_fee_per_person'는 이제 사용되지 않는 것으로 보임 (템플릿에 따라 다름)
            # 필요 시 아래 로직 활성화
            # try:
            #     exchange_fee = int(variables.get('exchange_fee', 0))
            #     company_burden = int(variables.get('company_burden', 0))
            #     variables['additional_fee_per_person'] = exchange_fee + company_burden
            # except (ValueError, TypeError):
            #     variables['additional_fee_per_person'] = 0

            # 3. 템플릿 태그를 치환하는 콜백 함수
            def replacer(match):
                # [컬럼:...] 태그 또는 {...} 태그에서 핵심 내용(키)과 포맷팅 정보 추출
                # key는 그룹 2(컬럼) 또는 그룹 5(변수) 중 하나가 됨
                key = match.group(2) or match.group(5)
                formatting = match.group(3) or match.group(6)
                
                # 통합 딕셔너리에서 값 조회
                value = variables.get(key, f"❌[{key}]")
                
                if isinstance(value, str) and value.startswith("❌"):
                    return value

                # 숫자 포맷팅 적용 (요청 시)
                if formatting and ':' in formatting:
                    try:
                        # 문자열 내 쉼표 등 비숫자 문자 제거 후 숫자 변환
                        num_value = float(re.sub(r'[^\d.-]', '', str(value)))
                        return f"{int(num_value):,}"
                    except (ValueError, TypeError):
                        return str(value) # 변환 실패 시 원본 값 반환
                
                return str(value)

            # [컬럼:키] 또는 {키} 형태의 모든 태그를 찾는 정규식
            pattern = r'\[(컬럼):([^\]:]+)(:[^\]]*)?\]|(\{)([^}]+?)(:[^}]+)?\}'
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