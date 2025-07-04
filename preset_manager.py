# preset_manager.py

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class PresetManager:
    """매핑 프리셋 관리 시스템"""

    def __init__(self, preset_dir="presets"):
        self.preset_dir = preset_dir
        self.ensure_preset_dir()

    def ensure_preset_dir(self):
        """프리셋 저장을 위한 디렉토리 생성"""
        if not os.path.exists(self.preset_dir):
            os.makedirs(self.preset_dir)

    def get_preset_list(self) -> List[Dict]:
        """저장된 프리셋 목록을 반환"""
        presets = []
        for filename in os.listdir(self.preset_dir):
            if filename.endswith('.json'):
                try:
                    preset_id = filename.replace('.json', '')
                    preset_data = self.load_preset(preset_id)
                    if preset_data:
                        presets.append({
                            'id': preset_id,
                            'name': preset_data.get('name', preset_id),
                            'description': preset_data.get('description', ''),
                            'created_at': preset_data.get('created_at', '')
                        })
                except Exception as e:
                    print(f"프리셋 {filename} 로드 중 오류: {e}")
                    continue
        # 생성일 기준으로 최신순 정렬
        presets.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return presets

    def load_preset(self, preset_id: str) -> Optional[Dict]:
        """특정 프리셋을 로드"""
        preset_file = os.path.join(self.preset_dir, f"{preset_id}.json")
        if not os.path.exists(preset_file):
            return None
        try:
            with open(preset_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"프리셋 로드 오류: {e}")
            return None

    def save_preset(self, preset_id: str, preset_data: Dict) -> bool:
        """프리셋을 저장"""
        preset_file = os.path.join(self.preset_dir, f"{preset_id}.json")
        try:
            preset_data['created_at'] = datetime.now().isoformat()
            with open(preset_file, 'w', encoding='utf-8') as f:
                json.dump(preset_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"프리셋 저장 오류: {e}")
            return False

    def delete_preset(self, preset_id: str) -> bool:
        """프리셋을 삭제"""
        preset_file = os.path.join(self.preset_dir, f"{preset_id}.json")
        if not os.path.exists(preset_file):
            return False
        try:
            os.remove(preset_file)
            return True
        except Exception as e:
            print(f"프리셋 삭제 오류: {e}")
            return False