import pandas as pd
import re
from datetime import datetime

class EnhancedDataProcessor:
    """향상된 데이터 처리 클래스"""
    
    def __init__(self):
        self.group_data = {}
        self.fixed_data = {}
        self.group_exchange_rates = {}
        
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
                
            # 열 문자를 숫자로 변환 (A=0, B=1, ..., Z=25, AA=26, ...)
            col_idx = 0
            for i, char in enumerate(reversed(col_str)):
                col_idx += (ord(char) - ord('A') + 1) * (26 ** i)
            col_idx -= 1  # 0-based로 변환
            
            row_idx = int(row_str) - 1  # 0-based로 변환
            
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
            
            # 숫자 필드 처리
            if key in ['base_exchange_rate', 'current_exchange_rate', 'exchange_rate_diff', 'company_burden']:
                try:
                    # 문자열에서 숫자만 추출
                    clean_value = str(value).replace(',', '').replace('원', '').replace(' ', '').strip()
                    fixed_data[key] = int(float(clean_value)) if clean_value and clean_value.replace('.', '').replace('-', '').isdigit() else 0
                except (ValueError, TypeError):
                    fixed_data[key] = 0
            else:
                fixed_data[key] = str(value) if value else ""
        
        self.fixed_data = fixed_data
        return fixed_data
    
    def process_group_data(self, customer_df, required_columns, optional_columns):
        """그룹 데이터 처리 (향상된 버전)"""
        try:
            self.group_data = {}
            
            # 필수 컬럼 매핑 확인
            team_col = None
            sender_group_col = None
            name_col = None
            
            for excel_col, var_name in required_columns.items():
                if var_name == "team_name":
                    team_col = excel_col
                elif var_name == "sender_group":
                    sender_group_col = excel_col  
                elif var_name == "name":
                    name_col = excel_col
            
            if not all([team_col, sender_group_col, name_col]):
                raise ValueError("필수 컬럼(팀명, 발송그룹, 이름) 매핑이 없습니다.")
            
            # 컬럼 존재 확인
            missing_cols = []
            for col_name, col_var in [(team_col, "팀명"), (sender_group_col, "발송그룹"), (name_col, "이름")]:
                if col_name not in customer_df.columns:
                    missing_cols.append(f"{col_var}({col_name})")
            
            if missing_cols:
                raise ValueError(f"다음 컬럼들이 엑셀에 없습니다: {', '.join(missing_cols)}")
            
            # 팀과 문자 발송 그룹으로 그룹화
            groups = customer_df.groupby([team_col, sender_group_col])
            
            # 엑셀 원본 순서를 유지하기 위해 첫 번째 행의 인덱스 저장
            group_order = {}
            for idx, row in customer_df.iterrows():
                team = row[team_col]
                sender_group = row[sender_group_col]
                if pd.notna(sender_group):
                    group_key = (team, sender_group)
                    if group_key not in group_order:
                        group_order[group_key] = idx
            
            # 그룹을 엑셀 순서대로 정렬
            sorted_group_keys = sorted(group_order.keys(), key=lambda x: group_order[x])
            
            group_id = 1
            for group_key in sorted_group_keys:
                team_name, sender_group = group_key
                
                try:
                    group_members = groups.get_group(group_key)
                except KeyError:
                    continue  # 그룹이 없으면 스킵
                
                # 그룹의 대표자 찾기 (연락처가 있는 사람 우선)
                contact_col = None
                for excel_col, var_name in optional_columns.items():
                    if var_name == "contact" and excel_col in customer_df.columns:
                        contact_col = excel_col
                        break
                
                if contact_col and contact_col in group_members.columns:
                    representatives = group_members[group_members[contact_col].notna()]
                    representative = representatives.iloc[0] if len(representatives) > 0 else group_members.iloc[0]
                else:
                    representative = group_members.iloc[0]
                
                # 그룹 멤버 이름 리스트
                members_list = group_members[name_col].tolist()
                
                # 그룹 정보 생성
                group_info = {
                    'group_id': f"G{group_id:03d}",
                    'team_name': str(team_name),
                    'sender_group': str(sender_group),
                    'sender': str(representative[name_col]),
                    'members': [str(name) for name in members_list],
                    'group_size': len(members_list),
                    'group_members_text': ', '.join([f"{name}님" for name in members_list]),
                    'excel_order': group_order[group_key]
                }
                
                # 모든 매핑된 컬럼들을 동적으로 처리
                all_mappings = {}
                all_mappings.update(required_columns)
                all_mappings.update(optional_columns)
                
                for excel_col, var_name in all_mappings.items():
                    if excel_col in customer_df.columns and excel_col in representative.index:
                        value = representative[excel_col]
                        
                        # 숫자로 추정되는 필드들은 정수로 변환
                        if any(keyword in var_name.lower() for keyword in 
                              ['price', 'fee', 'amount', 'balance', 'cost', 'money', '금액', '비용', '요금']):
                            try:
                                clean_value = str(value).replace(',', '').replace('원', '').replace(' ', '').strip()
                                group_info[var_name] = int(float(clean_value)) if clean_value and clean_value.replace('.', '').replace('-', '').isdigit() else 0
                            except (ValueError, TypeError):
                                group_info[var_name] = 0
                        else:
                            group_info[var_name] = str(value) if pd.notna(value) else ""
                
                self.group_data[group_info['group_id']] = group_info
                group_id += 1
            
            return self.group_data
            
        except Exception as e:
            raise Exception(f"그룹 데이터 처리 중 오류: {str(e)}")

    def process_group_data_dynamic(self, customer_df, column_mappings):
        """그룹 데이터 처리 (동적 매핑 버전)"""
        try:
            self.group_data = {}

            # 역방향 매핑 (var_name -> excel_col)
            reverse_mappings = {v: k for k, v in column_mappings.items()}
            
            # 필수 변수에 해당하는 엑셀 컬럼명 찾기
            team_col = reverse_mappings.get("team_name")
            sender_group_col = reverse_mappings.get("sender_group")
            name_col = reverse_mappings.get("name")

            if not all([team_col, sender_group_col, name_col]):
                raise ValueError("필수 변수(team_name, sender_group, name)가 컬럼과 매핑되지 않았습니다.")

            # 컬럼 존재 확인
            missing_cols = [col for col in [team_col, sender_group_col, name_col] if col not in customer_df.columns]
            if missing_cols:
                raise ValueError(f"매핑된 필수 컬럼이 엑셀에 없습니다: {', '.join(missing_cols)}")

            # 팀과 문자 발송 그룹으로 그룹화
            groups = customer_df.groupby([team_col, sender_group_col])
            
            # ... (이하 로직은 기존 process_group_data와 매우 유사하게 진행) ...
            # 엑셀 원본 순서를 유지하기 위해 첫 번째 행의 인덱스 저장
            group_order = {}
            for idx, row in customer_df.iterrows():
                team = row[team_col]
                sender_group = row[sender_group_col]
                if pd.notna(sender_group):
                    group_key = (team, sender_group)
                    if group_key not in group_order:
                        group_order[group_key] = idx
            
            # 그룹을 엑셀 순서대로 정렬
            sorted_group_keys = sorted(group_order.keys(), key=lambda x: group_order[x])
            
            group_id_counter = 1
            for group_key in sorted_group_keys:
                team_name, sender_group = group_key
                
                try:
                    group_members = groups.get_group(group_key)
                except KeyError:
                    continue
                
                # 대표자 찾기 (연락처가 있는 사람 우선)
                contact_col = reverse_mappings.get('contact')
                if contact_col and contact_col in group_members.columns:
                    representatives = group_members[group_members[contact_col].notna()]
                    representative = representatives.iloc[0] if len(representatives) > 0 else group_members.iloc[0]
                else:
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
                }

                # 모든 매핑된 컬럼 값을 group_info에 추가
                for excel_col, var_name in column_mappings.items():
                    if excel_col in customer_df.columns and excel_col in representative.index:
                        value = representative[excel_col]
                        # 숫자/문자 자동 변환 로직 (기존과 유사)
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
        self.final_messages = {}
        self.column_mappings = {}
        self.excel_columns = []
        
    def natural_sort_key(self, text):
        """자연 정렬을 위한 키 함수"""
        return [int(part) if part.isdigit() else part.lower() 
                for part in re.split(r'(\d+)', str(text))]

    def generate_messages(self, template, group_data, fixed_data):
        """스마트 템플릿을 지원하는 메시지 생성 함수 (오류 수정 버전)"""
        if not group_data:
            raise ValueError("그룹 데이터가 없습니다.")
        
        try:
            self.generated_messages = {}
            self.final_messages = {}
            
            # 컬럼명과 변수명을 매핑하는 딕셔너리 (정확한 조회를 위해 사용)
            excel_col_to_var_name = self.column_mappings

            for group_id, group_info in group_data.items():
                
                # --- 1. [컬럼:...] 태그를 실제 값으로 치환하는 함수 ---
                def replace_column_tag(match):
                    col_name = match.group(1)  # Excel 컬럼명 (예: "고객 부담금")
                    format_str = match.group(2) # 포맷 문자열 (예: ":,")
                    
                    # 매핑 정보에서 정확한 변수명 찾기
                    var_name = excel_col_to_var_name.get(col_name)
                    
                    if var_name and var_name in group_info:
                        value = group_info[var_name]
                        
                        # 숫자 포맷팅 적용 (format_str이 있는 경우)
                        if format_str and (format_str.strip() == ':' or format_str.strip() == ':,') :
                            try:
                                num_value = int(float(str(value).replace(',', '')))
                                return f"{num_value:,}"
                            except (ValueError, TypeError):
                                return str(value) # 숫자 변환 실패 시 원본 값 반환
                        
                        return str(value) # 포맷팅이 없으면 문자열로 반환
                    else:
                        # 매핑 정보에 없으면 오류 표시
                        return f"❌[{col_name}]"

                # 정규식을 사용해 [컬럼:컬럼명] 또는 [컬럼:컬럼명:,] 형태의 모든 태그를 한 번에 치환
                processed_template = re.sub(r'\[컬럼:([^\]:]+)(:[^\]]*)?\]', replace_column_tag, template)

                # --- 2. {변수명} 시스템 변수 처리 ---
                variables = {}
                variables.update(fixed_data)
                variables.update(group_info)

                # 특별 계산 변수
                variables['group_size'] = len(group_info.get('members', []))
                variables['group_members_text'] = ', '.join([f"{name}님" for name in group_info.get('members', [])])
                
                current_exchange_fee = variables.get('exchange_fee', 0)
                # [수정된 부분] exchange_info 대신 variables에서 직접 값을 가져옵니다.
                current_company_burden = variables.get('company_burden', 0)
                variables['additional_fee_per_person'] = current_exchange_fee + current_company_burden
                
                # 숫자 포맷팅을 위한 타입 변환
                number_format_vars = set(re.findall(r'\{(\w+):[^}]*,[^}]*\}', processed_template))
                for var in number_format_vars:
                    if var in variables:
                        try:
                            variables[var] = int(float(str(variables[var]).replace(',', '')))
                        except (ValueError, TypeError):
                            variables[var] = 0 # 숫자 변환 실패 시 0으로 처리

                # --- 3. 최종 메시지 생성 ---
                try:
                    # format_map을 사용하여 없는 키에 대한 오류 방지
                    final_message = processed_template.format_map(defaultdict(str, variables))
                except Exception as e:
                    final_message = f"오류: 메시지를 생성하는 중 문제가 발생했습니다. ({str(e)})"
                
                # 결과 저장
                self.generated_messages[group_id] = {
                    'message': final_message,
                    'group_info': group_info,
                    'variables_used': variables
                }
                self.final_messages[group_id] = final_message

            return {
                'messages': self.generated_messages,
                'total_count': len(self.generated_messages)
            }
            
        except Exception as e:
            # traceback을 추가하여 더 상세한 오류 로깅
            import traceback
            error_details = traceback.format_exc()
            raise Exception(f"메시지 생성 중 오류 발생: {str(e)}\n{error_details}")

    def get_sorted_messages(self):
        """자연 정렬된 메시지 반환"""
        if not self.generated_messages:
            return []
        
        # 엑셀 순서를 기준으로 정렬
        sorted_items = sorted(self.generated_messages.items(), 
                            key=lambda item: item[1]['group_info'].get('excel_order', 0))
        return sorted_items

    def _find_column_value(self, col_name, group_info):
        """그룹 정보에서 컬럼값 찾기 (개선된 매칭)"""
        # 1차: 직접 매칭
        if col_name in group_info:
            return group_info[col_name]
        
        # 2차: 매핑 테이블 활용
        if hasattr(self, 'column_mappings'):
            for excel_col, var_name in self.column_mappings.items():
                if excel_col == col_name and var_name in group_info:
                    return group_info[var_name]
        
        # 3차: 유사한 이름으로 찾기
        for key, value in group_info.items():
            if col_name.lower() in key.lower() or key.lower() in col_name.lower():
                return value
        
        # 찾지 못한 경우
        return None

    def get_sorted_messages(self):
        """자연 정렬된 메시지 반환"""
        if not self.generated_messages:
            return []
        
        sorted_items = sorted(self.generated_messages.items(), 
                            key=lambda x: self.natural_sort_key(x[1]['group_info']['team_name']))
        return sorted_items