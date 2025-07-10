import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Optional

class TemplateManager:
    """템플릿 관리 시스템 (사용자 템플릿 중심)"""
    
    def __init__(self, template_dir="templates", file_template_dir="file_templates"):
        self.template_dir = template_dir
        self.file_template_dir = file_template_dir
        self.ensure_directories()
    
    def ensure_directories(self):
        """템플릿 디렉토리들 생성"""
        for directory in [self.template_dir, self.file_template_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
    
    def get_user_template_list(self) -> List[Dict]:
        """사용자가 저장한 템플릿 목록만 반환"""
        templates = []
        
        for filename in os.listdir(self.template_dir):
            if filename.endswith('.json') and not filename.startswith('default_'):
                try:
                    template_id = filename.replace('.json', '')
                    template_data = self.load_template(template_id)
                    if template_data:
                        templates.append({
                            'id': template_id,
                            'name': template_data.get('name', template_id),
                            'description': template_data.get('description', ''),
                            'created_at': template_data.get('created_at', ''),
                            'updated_at': template_data.get('updated_at', ''),
                            'variables_count': len(template_data.get('variables', []))
                        })
                except Exception as e:
                    print(f"템플릿 {filename} 로드 중 오류: {e}")
                    continue
        
        # 업데이트 순으로 정렬
        templates.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        return templates
    
    def get_template_list(self) -> List[Dict]:
        """하위 호환성을 위한 기존 메서드"""
        return self.get_user_template_list()
    
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
    
    def create_user_template(self, name: str, content: str, description: str = "") -> str:
        """사용자 템플릿 생성"""
        import re
        
        # 변수 추출
        column_refs = re.findall(r'\[컬럼:([^\]]+)\]', content)
        system_vars = re.findall(r'\{(\w+)(?::[^}]+)?\}', content)
        all_variables = list(set(column_refs + system_vars))
        
        # 고유 ID 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        template_id = f"user_{timestamp}"
        
        template_data = {
            "name": name,
            "description": description,
            "content": content,
            "variables": all_variables,
            "column_refs": column_refs,
            "system_vars": system_vars,
            "category": "user",
            "created_at": datetime.now().isoformat()
        }
        
        if self.save_template(template_id, template_data):
            return template_id
        else:
            raise Exception("템플릿 저장에 실패했습니다.")
    
    def create_template_from_content(self, name: str, content: str, description: str = "", 
                                   category: str = "user") -> str:
        """하위 호환성을 위한 기존 메서드"""
        return self.create_user_template(name, content, description)
    
    # --- 파일별 템플릿 저장/로드 기능 ---
    
    def _get_file_hash(self, file_key: str) -> str:
        """파일 키를 해시로 변환"""
        return hashlib.md5(file_key.encode('utf-8')).hexdigest()[:12]
    
    def save_file_template(self, file_key: str, template_content: str) -> bool:
        """특정 파일에 연결된 템플릿 저장"""
        try:
            file_hash = self._get_file_hash(file_key)
            template_file = os.path.join(self.file_template_dir, f"{file_hash}.json")
            
            template_data = {
                "file_key": file_key,
                "content": template_content,
                "saved_at": datetime.now().isoformat()
            }
            
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"파일 템플릿 저장 오류: {e}")
            return False
    
    def load_file_template(self, file_key: str) -> Optional[str]:
        """특정 파일에 연결된 템플릿 로드"""
        try:
            file_hash = self._get_file_hash(file_key)
            template_file = os.path.join(self.file_template_dir, f"{file_hash}.json")
            
            if not os.path.exists(template_file):
                return None
            
            with open(template_file, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
                return template_data.get('content')
                
        except Exception as e:
            print(f"파일 템플릿 로드 오류: {e}")
            return None
    
    def delete_file_template(self, file_key: str) -> bool:
        """특정 파일에 연결된 템플릿 삭제"""
        try:
            file_hash = self._get_file_hash(file_key)
            template_file = os.path.join(self.file_template_dir, f"{file_hash}.json")
            
            if os.path.exists(template_file):
                os.remove(template_file)
                return True
            return False
        except Exception as e:
            print(f"파일 템플릿 삭제 오류: {e}")
            return False
    
    def get_file_template_info(self, file_key: str) -> Optional[Dict]:
        """파일 템플릿 정보 조회"""
        try:
            file_hash = self._get_file_hash(file_key)
            template_file = os.path.join(self.file_template_dir, f"{file_hash}.json")
            
            if not os.path.exists(template_file):
                return None
            
            with open(template_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            print(f"파일 템플릿 정보 조회 오류: {e}")
            return None
    
    # --- 기존 메서드들 (호환성 유지) ---
    
    def duplicate_template(self, source_id: str, new_name: str) -> str:
        """템플릿 복제"""
        source_template = self.load_template(source_id)
        if not source_template:
            raise Exception(f"원본 템플릿 {source_id}를 찾을 수 없습니다.")
        
        new_template = source_template.copy()
        new_template['name'] = new_name
        new_template['description'] = f"{source_template.get('description', '')} (복제본)"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_id = f"copy_{timestamp}"
        
        if self.save_template(new_id, new_template):
            return new_id
        else:
            raise Exception("템플릿 복제에 실패했습니다.")
    
    def export_template(self, template_id: str) -> Optional[str]:
        """템플릿 내보내기"""
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
            
            if 'content' not in template_data:
                raise Exception("유효하지 않은 템플릿 파일입니다.")
            
            if new_name:
                template_data['name'] = new_name
            elif 'name' not in template_data:
                template_data['name'] = f"가져온 템플릿 {datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 변수 재추출
            import re
            content = template_data['content']
            column_refs = re.findall(r'\[컬럼:([^\]]+)\]', content)
            system_vars = re.findall(r'\{(\w+)(?::[^}]+)?\}', content)
            template_data['variables'] = list(set(column_refs + system_vars))
            template_data['column_refs'] = column_refs
            template_data['system_vars'] = system_vars
            
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
    
    def search_templates(self, query: str) -> List[Dict]:
        """템플릿 검색"""
        all_templates = self.get_user_template_list()
        query_lower = query.lower()
        
        results = []
        for template in all_templates:
            if (query_lower in template.get('name', '').lower() or
                query_lower in template.get('description', '').lower()):
                results.append(template)
        
        return results
    
    def validate_template(self, content: str, excel_columns: List[str] = None) -> Dict:
        """스마트 템플릿 유효성 검사"""
        import re
        
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'column_refs': [],
            'system_vars': [],
            'stats': {}
        }
        
        try:
            # 컬럼 참조 및 시스템 변수 추출
            result['column_refs'] = re.findall(r'\[컬럼:([^\]]+)\]', content)
            result['system_vars'] = re.findall(r'\{(\w+)(?::[^}]+)?\}', content)
            
            # 기본 통계
            result['stats'] = {
                'character_count': len(content),
                'line_count': len(content.split('\n')),
                'column_refs_count': len(result['column_refs']),
                'system_vars_count': len(result['system_vars'])
            }
            
            # 기본 검증
            if not content.strip():
                result['errors'].append("템플릿 내용이 비어있습니다.")
                result['is_valid'] = False
            
            if len(content) > 10000:
                result['warnings'].append("템플릿이 너무 깁니다. (10,000자 초과)")
            
            # 엑셀 컬럼 검증 (컬럼 정보가 제공된 경우)
            if excel_columns:
                for col_ref in result['column_refs']:
                    if col_ref not in excel_columns:
                        result['errors'].append(f"존재하지 않는 컬럼: '{col_ref}'")
                        result['is_valid'] = False
            
            # 괄호 매칭 확인
            open_braces = content.count('{')
            close_braces = content.count('}')
            open_brackets = content.count('[')
            close_brackets = content.count(']')
            
            if open_braces != close_braces:
                result['errors'].append(f"중괄호 매칭 오류: {{ {open_braces}개, }} {close_braces}개")
                result['is_valid'] = False
            
            if open_brackets != close_brackets:
                result['errors'].append(f"대괄호 매칭 오류: [ {open_brackets}개, ] {close_brackets}개")
                result['is_valid'] = False
            
        except Exception as e:
            result['errors'].append(f"검증 중 오류 발생: {str(e)}")
            result['is_valid'] = False
        
        return result