import yaml
from pathlib import Path
from typing import Dict, Any


class Config:
    """YAML設定管理クラス"""
    
    def __init__(self, config_file: str = "config/config.yaml"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """YAML設定ファイルを読み込み"""
        if not self.config_file.exists():
            print(f"エラー: 設定ファイルが見つかりません: {self.config_file}")
            print("config/config.yaml.example を参考に設定ファイルを作成してください。")
            raise FileNotFoundError(f"設定ファイルが必要です: {self.config_file}")
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if config is None:
                    raise ValueError("設定ファイルが空です")
                return config
        except (yaml.YAMLError, IOError) as e:
            print(f"設定ファイル読み込みエラー: {e}")
            raise
    
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """設定をYAMLファイルに保存（管理用）"""
        try:
            # ディレクトリが存在しない場合は作成
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)
            print(f"設定ファイルを作成しました: {self.config_file}")
        except IOError as e:
            print(f"設定ファイル保存エラー: {e}")
    
    def get_itunes_media_path(self) -> str:
        """iTunes Media Pathを取得"""
        return self.config["itunes"]["media_path"]
    
    def get_artwork_output_dir(self) -> str:
        """アートワーク出力ディレクトリを取得"""
        return self.config["artwork"]["output_dir"]
    
    def get_itunes_api_country(self) -> str:
        """iTunes API国コードを取得"""
        return self.config["itunes"]["api_country"]
    
    def get_artwork_quality(self) -> str:
        """アートワーク品質を取得"""
        return self.config["artwork"]["quality"]
    
    def show_config(self) -> None:
        """現在の設定を表示"""
        print("現在の設定:")
        print("-" * 40)
        print(yaml.dump(self.config, default_flow_style=False, allow_unicode=True, indent=2))
    
    def validate_itunes_path(self) -> bool:
        """iTunes Media Pathの存在確認"""
        try:
            path = Path(self.get_itunes_media_path())
            if path.exists() and path.is_dir():
                return True
            else:
                print(f"警告: iTunes Media Pathが見つかりません: {path}")
                return False
        except KeyError as e:
            print(f"エラー: 設定ファイルに必要な項目がありません: {e}")
            return False


# グローバル設定インスタンス
config = Config()


if __name__ == "__main__":
    # 設定テスト
    config.show_config()
    print(f"iTunes Media Path: {config.get_itunes_media_path()}")
    print(f"Path exists: {config.validate_itunes_path()}")
