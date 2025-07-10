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
        
    def natural_sort_key(self, text):
        """자연 정렬을 위한 키 함수"""
        return [int(part) if part.isdigit() else part.lower() 
                for part in re.split(r'(\d+)', str(text))]

    def generate_messages(self, template, group_data, fixed_data, group_exchange_rates=None):
        """스마트 템플릿을 지원하는 메시지 생성 함수 (완전 수정 버전)"""
        if not group_data:
            raise ValueError("그룹 데이터가 없습니다.")
        
        if group_exchange_rates is None:
            group_exchange_rates = {}
        
        try:
            self.generated_messages = {}
            self.final_messages = {}
            
            # 템플릿에서 사용된 컬럼 참조들 미리 추출
            import re
            column_refs = re.findall(r'\[컬럼:([^\]:]+)\]', template)  # 일반 컬럼 참조: [컬럼:컬럼명]
            column_format_refs = re.findall(r'\[컬럼:([^\]:]+):([^\]]+)\]', template)  # 포맷 포함 컬럼 참조: [컬럼:컬럼명:,]
            
            for group_id, group_info in group_data.items():
                # 1. 스마트 템플릿 전처리: [컬럼:컬럼명] 및 [컬럼:컬럼명:포맷] 처리
                processed_template = template
                
                # 일반 컬럼 참조 처리: [컬럼:컬럼명]
                for col_name in column_refs:
                    col_value = self._find_column_value(col_name, group_info)
                    
                    # 기본 텍스트 포맷팅
                    if isinstance(col_value, (int, float)):
                        formatted_value = str(col_value)
                    elif isinstance(col_value, str) and col_value.replace(',', '').replace('.', '').replace('-', '').isdigit():
                        formatted_value = col_value
                    else:
                        formatted_value = str(col_value) if col_value is not None else ""
                    
                    # 찾지 못한 경우 오류 표시
                    if col_value is None:
                        formatted_value = f"❌[{col_name}]"
                    
                    # [컬럼:컬럼명]을 실제 값으로 치환
                    processed_template = processed_template.replace(f"[컬럼:{col_name}]", formatted_value)
                
                # 포맷 포함 컬럼 참조 처리: [컬럼:컬럼명:포맷]
                for col_name, format_type in column_format_refs:
                    col_value = self._find_column_value(col_name, group_info)
                    
                    # 숫자 포맷팅 적용
                    if format_type == ',' and col_value is not None:
                        try:
                            if isinstance(col_value, (int, float)):
                                formatted_value = f"{col_value:,}"
                            elif isinstance(col_value, str):
                                clean_value = col_value.replace(',', '').replace('원', '').strip()
                                if clean_value and clean_value.replace('.', '').replace('-', '').isdigit():
                                    num_value = int(float(clean_value))
                                    formatted_value = f"{num_value:,}"
                                else:
                                    formatted_value = str(col_value)
                            else:
                                formatted_value = str(col_value)
                        except (ValueError, TypeError):
                            formatted_value = str(col_value) if col_value is not None else ""
                    else:
                        formatted_value = str(col_value) if col_value is not None else ""
                    
                    # 찾지 못한 경우 오류 표시
                    if col_value is None:
                        formatted_value = f"❌[{col_name}]"
                    
                    # [컬럼:컬럼명:포맷]을 실제 값으로 치환
                    processed_template = processed_template.replace(f"[컬럼:{col_name}:{format_type}]", formatted_value)
                
                # 2. 시스템 변수 준비 (기존 로직과 동일)
                variables = {}
                
                # 고정 정보 추가
                for key, value in fixed_data.items():
                    if isinstance(value, (int, float)):
                        variables[key] = value
                    else:
                        try:
                            str_val = str(value).replace(',', '').replace('원', '').strip()
                            if str_val and str_val.replace('.', '').replace('-', '').isdigit():
                                variables[key] = int(float(str_val))
                            else:
                                variables[key] = str(value) if value else ""
                        except:
                            variables[key] = str(value) if value else ""
                
                # 그룹별 환율 정보 추가
                exchange_info = group_exchange_rates.get(group_id, {})
                for key, value in exchange_info.items():
                    variables[key] = value
                
                # 그룹 정보를 변수로 추가 (타입 변환 포함)
                for key, value in group_info.items():
                    if isinstance(value, (int, float)):
                        variables[key] = value
                    elif isinstance(value, list):
                        if key == 'members':
                            variables['group_members_text'] = ', '.join([f"{name}님" for name in value])
                        else:
                            variables[key] = ', '.join(str(item) for item in value)
                    else:
                        str_value = str(value) if value is not None else ""
                        
                        # 숫자 필드 스마트 감지
                        is_numeric_field = any(keyword in key.lower() for keyword in 
                                            ['price', 'fee', 'amount', 'balance', 'cost', 'money', 
                                            '금액', '비용', '요금', '원', 'rate', 'size', 'count'])
                        
                        is_numeric_value = False
                        try:
                            clean_value = str_value.replace(',', '').replace('원', '').replace(' ', '').strip()
                            if clean_value and (clean_value.isdigit() or 
                                            (clean_value.replace('.', '').replace('-', '').isdigit())):
                                is_numeric_value = True
                        except:
                            pass
                        
                        if is_numeric_field or is_numeric_value:
                            try:
                                clean_value = str_value.replace(',', '').replace('원', '').replace(' ', '').strip()
                                variables[key] = int(float(clean_value)) if clean_value else 0
                            except (ValueError, TypeError):
                                variables[key] = 0
                        else:
                            variables[key] = str_value
                
                # 3. 특별 계산 변수들
                variables['group_size'] = len(group_info.get('members', []))
                
                current_exchange_fee = variables.get('exchange_fee', 0)
                current_company_burden = exchange_info.get('company_burden', variables.get('company_burden', 0))
                variables['additional_fee_per_person'] = current_exchange_fee + current_company_burden
                
                # 추가 금액 텍스트
                additional_amount = variables.get('additional_amount', 0)
                try:
                    additional_amount = int(additional_amount) if additional_amount else 0
                except:
                    additional_amount = 0
                
                if additional_amount != 0:
                    variables['additional_amount_text'] = f" - 추가금액 {additional_amount:,}원"
                else:
                    variables['additional_amount_text'] = ""
                
                # 기본값 설정
                default_vars = {
                    'product_price': 0,
                    'deposit': 0,
                    'flight_fee': 0,
                    'individual_balance': 0,
                    'total_balance': 0,
                    'bank_account': '계좌정보 없음',
                    'contact': ''
                }
                
                for var_name, default_value in default_vars.items():
                    if var_name not in variables:
                        variables[var_name] = default_value
                
                # 4. 템플릿 변수 검증 및 메시지 생성
                try:
                    # 현재 템플릿에서 사용된 변수들 추출 (이미 컬럼 참조는 처리됨)
                    template_vars = set(re.findall(r'\{(\w+)(?::[^}]+)?\}', processed_template))
                    
                    # 없는 변수들에 기본값 제공
                    for var in template_vars:
                        if var not in variables:
                            if any(keyword in var.lower() for keyword in 
                                ['price', 'fee', 'amount', 'balance', 'cost', 'money', 'size', 'rate', 'count',
                                '금액', '비용', '요금', '원', '개수', '인원']):
                                variables[var] = 0
                            else:
                                variables[var] = ""
                    
                    # 숫자 포맷팅 변수들 타입 강제 변환
                    number_format_vars = set(re.findall(r'\{(\w+):[^}]*[,d][^}]*\}', processed_template))
                    for var_name in number_format_vars:
                        if var_name in variables:
                            try:
                                current_value = variables[var_name]
                                if isinstance(current_value, str):
                                    clean_value = current_value.replace(',', '').replace('원', '').replace(' ', '').strip()
                                    variables[var_name] = int(float(clean_value)) if clean_value else 0
                                elif not isinstance(current_value, (int, float)):
                                    variables[var_name] = 0
                            except (ValueError, TypeError):
                                variables[var_name] = 0
                    
                    # 최종 메시지 생성
                    message = processed_template.format(**variables)
                    
                except KeyError as e:
                    missing_var = str(e).strip("'")
                    raise ValueError(f"템플릿에 정의되지 않은 변수: {{{missing_var}}}")
                    
                except ValueError as e:
                    error_msg = str(e)
                    if "Cannot specify" in error_msg or "format" in error_msg.lower():
                        problematic_vars = []
                        for var_name, var_value in variables.items():
                            if f"{{{var_name}:" in processed_template and not isinstance(var_value, (int, float)):
                                problematic_vars.append(f"{var_name} = '{var_value}' (타입: {type(var_value).__name__})")
                        
                        raise ValueError(f"숫자 포맷팅을 문자값에 적용하려 했습니다.\n문제가 있는 변수들: {', '.join(problematic_vars[:3])}")
                    else:
                        raise ValueError(f"변수 값 처리 중 오류: {error_msg}")
                        
                except Exception as e:
                    raise Exception(f"스마트 템플릿 처리 중 예상치 못한 오류: {str(e)}")
                
                # 메시지 저장
                self.generated_messages[group_id] = {
                    'message': message,
                    'group_info': group_info,
                    'variables_used': variables,
                    'column_refs_used': column_refs,  # 디버깅용
                    'column_format_refs_used': column_format_refs  # 디버깅용
                }
                
                self.final_messages[group_id] = message
            
            if not self.generated_messages:
                raise Exception("성공적으로 생성된 메시지가 없습니다. 템플릿과 데이터를 확인해주세요.")
            
            return {
                'messages': self.generated_messages,
                'total_count': len(self.generated_messages),
                'column_refs_found': list(set(column_refs + [col for col, fmt in column_format_refs]))
            }
            
        except Exception as e:
            raise Exception(f"스마트 메시지 생성 중 오류: {str(e)}")

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