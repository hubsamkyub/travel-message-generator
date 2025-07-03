import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class TemplateManager:
    """템플릿 관리 시스템"""
    
    def __init__(self, template_dir="templates"):
        self.template_dir = template_dir
        self.ensure_template_dir()
        self.load_default_templates()
    
    def ensure_template_dir(self):
        """템플릿 디렉토리 생성"""
        if not os.path.exists(self.template_dir):
            os.makedirs(self.template_dir)
    
    def load_default_templates(self):
        """기본 템플릿들 로드/생성"""
        default_templates = {
            "standard": {
                "name": "표준 잔금 안내",
                "description": "일반적인 여행 잔금 안내 템플릿",
                "content": """[여행처럼]
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

감사합니다. ^^""",
                "variables": ["product_name", "exchange_rate_diff", "base_exchange_rate", "current_exchange_rate", 
                            "additional_fee_per_person", "group_members_text", "total_balance", "payment_due_date", "bank_account"],
                "category": "travel",
                "created_at": datetime.now().isoformat()
            },
            
            "simple": {
                "name": "간단한 잔금 안내",
                "description": "핵심 정보만 포함한 간단한 템플릿",
                "content": """[{product_name}] 잔금 안내

안녕하세요!
{product_name} 여행 잔금 안내입니다.

👥 대상: {group_members_text}
💰 잔금: {total_balance:,}원
📅 완납일: {payment_due_date}
🏦 계좌: {bank_account}

감사합니다.""",
                "variables": ["product_name", "group_members_text", "total_balance", "payment_due_date", "bank_account"],
                "category": "travel",
                "created_at": datetime.now().isoformat()
            },
            
            "detailed": {
                "name": "상세 정보 포함",
                "description": "모든 상세 정보를 포함한 완전한 템플릿",
                "content": """=== {product_name} 잔금 결제 안내 ===

📋 예약 정보
• 상품명: {product_name}
• 팀: {team_name} / 그룹: {sender_group}
• 참가자: {group_members_text} ({group_size}명)

💰 결제 정보
• 상품가: {product_price:,}원
• 환차금: {exchange_fee:,}원 (기준환율 {base_exchange_rate:,}원 → 현재환율 {current_exchange_rate:,}원)
• 예약금: {deposit:,}원 (기납부)
• 항공료: {flight_fee:,}원 (별도)
• 추가금액: {additional_amount:,}원
• 1인당 잔금: {individual_balance:,}원
• 총 잔금: {total_balance:,}원

📅 결제 정보
• 완납일: {payment_due_date}
• 입금계좌: {bank_account}
• 입금자명: {sender} (대표)

📞 문의: {contact}

※ 결제 후 현금영수증 번호를 알려주세요.
감사합니다.""",
                "variables": ["product_name", "team_name", "sender_group", "group_members_text", "group_size",
                            "product_price", "exchange_fee", "base_exchange_rate", "current_exchange_rate",
                            "deposit", "flight_fee", "additional_amount", "individual_balance", "total_balance",
                            "payment_due_date", "bank_account", "sender", "contact"],
                "category": "travel",
                "created_at": datetime.now().isoformat()
            }
        }
        
        # 기본 템플릿 파일들 생성
        for template_id, template_data in default_templates.items():
            template_file = os.path.join(self.template_dir, f"{template_id}.json")
            if not os.path.exists(template_file):
                self.save_template(template_id, template_data)
    
    def get_template_list(self) -> List[Dict]:
        """저장된 템플릿 목록 반환"""
        templates = []
        
        for filename in os.listdir(self.template_dir):
            if filename.endswith('.json'):
                try:
                    template_id = filename.replace('.json', '')
                    template_data = self.load_template(template_id)
                    if template_data:
                        templates.append({
                            'id': template_id,
                            'name': template_data.get('name', template_id),
                            'description': template_data.get('description', ''),
                            'category': template_data.get('category', 'general'),
                            'created_at': template_data.get('created_at', ''),
                            'variables_count': len(template_data.get('variables', []))
                        })
                except Exception as e:
                    print(f"템플릿 {filename} 로드 중 오류: {e}")
                    continue
        
        # 생성일순으로 정렬
        templates.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return templates
    
    def load_template(self, template_id: str) -> Optional[Dict]:
        """특정 템플릿 로드"""
        template_file = os.path.join(self.template_dir, f"{template_id}.json")
        
        if not os.path.exists(template_file):
            return None
        
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"템플릿 로드 오류: {e}")
            return None
    
    def save_template(self, template_id: str, template_data: Dict) -> bool:
        """템플릿 저장"""
        template_file = os.path.join(self.template_dir, f"{template_id}.json")
        
        try:
            # 저장 시간 추가
            template_data['updated_at'] = datetime.now().isoformat()
            
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"템플릿 저장 오류: {e}")
            return False
    
    def delete_template(self, template_id: str) -> bool:
        """템플릿 삭제"""
        template_file = os.path.join(self.template_dir, f"{template_id}.json")
        
        if not os.path.exists(template_file):
            return False
        
        try:
            os.remove(template_file)
            return True
        except Exception as e:
            print(f"템플릿 삭제 오류: {e}")
            return False
    
    def create_template_from_content(self, name: str, content: str, description: str = "", 
                                   category: str = "custom") -> str:
        """내용으로부터 새 템플릿 생성"""
        import re
        
        # 변수 추출
        variables = list(set(re.findall(r'\{(\w+)(?::[^}]+)?\}', content)))
        
        # 고유 ID 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        template_id = f"custom_{timestamp}"
        
        template_data = {
            "name": name,
            "description": description,
            "content": content,
            "variables": variables,
            "category": category,
            "created_at": datetime.now().isoformat()
        }
        
        if self.save_template(template_id, template_data):
            return template_id
        else:
            raise Exception("템플릿 저장에 실패했습니다.")
    
    def duplicate_template(self, source_id: str, new_name: str) -> str:
        """템플릿 복제"""
        source_template = self.load_template(source_id)
        if not source_template:
            raise Exception(f"원본 템플릿 {source_id}를 찾을 수 없습니다.")
        
        # 새 템플릿 데이터 생성
        new_template = source_template.copy()
        new_template['name'] = new_name
        new_template['description'] = f"{source_template.get('description', '')} (복제본)"
        
        # 새 ID 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_id = f"copy_{timestamp}"
        
        if self.save_template(new_id, new_template):
            return new_id
        else:
            raise Exception("템플릿 복제에 실패했습니다.")
    
    def export_template(self, template_id: str) -> Optional[str]:
        """템플릿 내보내기 (JSON 문자열 반환)"""
        template_data = self.load_template(template_id)
        if not template_data:
            return None
        
        try:
            return json.dumps(template_data, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"템플릿 내보내기 오류: {e}")
            return None
    
    def import_template(self, json_content: str, new_name: str = None) -> str:
        """템플릿 가져오기"""
        try:
            template_data = json.loads(json_content)
            
            # 필수 필드 확인
            if 'content' not in template_data:
                raise Exception("유효하지 않은 템플릿 파일입니다. 'content' 필드가 없습니다.")
            
            # 이름 설정
            if new_name:
                template_data['name'] = new_name
            elif 'name' not in template_data:
                template_data['name'] = f"가져온 템플릿 {datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 변수 재추출 (안전성을 위해)
            import re
            template_data['variables'] = list(set(re.findall(r'\{(\w+)(?::[^}]+)?\}', template_data['content'])))
            
            # ID 생성 및 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            template_id = f"imported_{timestamp}"
            
            if self.save_template(template_id, template_data):
                return template_id
            else:
                raise Exception("템플릿 저장에 실패했습니다.")
                
        except json.JSONDecodeError:
            raise Exception("유효하지 않은 JSON 파일입니다.")
        except Exception as e:
            raise Exception(f"템플릿 가져오기 중 오류: {str(e)}")
    
    def get_template_by_category(self, category: str) -> List[Dict]:
        """카테고리별 템플릿 필터링"""
        all_templates = self.get_template_list()
        return [t for t in all_templates if t.get('category') == category]
    
    def search_templates(self, query: str) -> List[Dict]:
        """템플릿 검색"""
        all_templates = self.get_template_list()
        query_lower = query.lower()
        
        results = []
        for template in all_templates:
            # 이름, 설명, 변수에서 검색
            if (query_lower in template.get('name', '').lower() or
                query_lower in template.get('description', '').lower()):
                results.append(template)
        
        return results
    
    def validate_template(self, content: str) -> Dict:
        """템플릿 유효성 검사"""
        import re
        
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'variables': [],
            'stats': {}
        }
        
        try:
            # 변수 추출
            variables = re.findall(r'\{(\w+)(?::[^}]+)?\}', content)
            result['variables'] = list(set(variables))
            
            # 기본 통계
            result['stats'] = {
                'character_count': len(content),
                'line_count': len(content.split('\n')),
                'variable_count': len(result['variables']),
                'unique_variables': len(set(variables))
            }
            
            # 기본 검증
            if not content.strip():
                result['errors'].append("템플릿 내용이 비어있습니다.")
                result['is_valid'] = False
            
            if len(content) > 10000:
                result['warnings'].append("템플릿이 너무 깁니다. (10,000자 초과)")
            
            # 필수 변수 확인
            recommended_vars = ['product_name', 'payment_due_date', 'total_balance']
            missing_recommended = [var for var in recommended_vars if var not in result['variables']]
            if missing_recommended:
                result['warnings'].append(f"권장 변수가 누락되었습니다: {', '.join(missing_recommended)}")
            
            # 괄호 매칭 확인
            open_braces = content.count('{')
            close_braces = content.count('}')
            if open_braces != close_braces:
                result['errors'].append(f"중괄호 매칭 오류: {{ {open_braces}개, }} {close_braces}개")
                result['is_valid'] = False
            
            # 잘못된 변수 형식 검사
            invalid_vars = re.findall(r'\{[^}]*[^a-zA-Z0-9_:,\s][^}]*\}', content)
            if invalid_vars:
                result['warnings'].append(f"잘못된 변수 형식이 발견되었습니다: {', '.join(invalid_vars[:3])}")
            
        except Exception as e:
            result['errors'].append(f"검증 중 오류 발생: {str(e)}")
            result['is_valid'] = False
        
        return result


class TemplateHistory:
    """템플릿 편집 히스토리 관리"""
    
    def __init__(self, history_dir="template_history"):
        self.history_dir = history_dir
        self.ensure_history_dir()
    
    def ensure_history_dir(self):
        """히스토리 디렉토리 생성"""
        if not os.path.exists(self.history_dir):
            os.makedirs(self.history_dir)
    
    def save_history(self, template_id: str, content: str, action: str = "edit") -> str:
        """편집 히스토리 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        history_id = f"{template_id}_{timestamp}"
        history_file = os.path.join(self.history_dir, f"{history_id}.json")
        
        history_data = {
            "template_id": template_id,
            "content": content,
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "character_count": len(content)
        }
        
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
            return history_id
        except Exception as e:
            print(f"히스토리 저장 오류: {e}")
            return ""
    
    def get_history(self, template_id: str, limit: int = 10) -> List[Dict]:
        """특정 템플릿의 히스토리 조회"""
        history_files = []
        
        for filename in os.listdir(self.history_dir):
            if filename.startswith(f"{template_id}_") and filename.endswith('.json'):
                history_files.append(filename)
        
        # 최신순 정렬
        history_files.sort(reverse=True)
        
        histories = []
        for filename in history_files[:limit]:
            try:
                with open(os.path.join(self.history_dir, filename), 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                    history_data['history_id'] = filename.replace('.json', '')
                    histories.append(history_data)
            except Exception as e:
                print(f"히스토리 로드 오류: {e}")
                continue
        
        return histories
    
    def restore_from_history(self, history_id: str) -> Optional[str]:
        """히스토리에서 복원"""
        history_file = os.path.join(self.history_dir, f"{history_id}.json")
        
        if not os.path.exists(history_file):
            return None
        
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
                return history_data.get('content')
        except Exception as e:
            print(f"히스토리 복원 오류: {e}")
            return None