from src.models.repo_profile import RepoProfile
from src.ingestion.utils.file_scanner import generate_file_tree
from src.agents.profilers.structure_analyzer import StructureAnalyzer
from src.agents.profilers.usage_extractor import UsageExtractor
from src.agents.profilers.config_extractor import ConfigExtractor

class ProfileBuilder:
    def __init__(self):
        self.structure_analyzer = StructureAnalyzer()
        self.usage_extractor = UsageExtractor()
        self.config_extractor = ConfigExtractor()

    def build(self, repo_name: str, repo_path: str) -> RepoProfile:
        print(f"[{repo_name}] 1.4 Profile Builder starting...")
        
        # 0. Context Gathering (File Tree)
        file_tree = generate_file_tree(repo_path, max_depth=2)
        
        # 1. Structure Analysis
        structure = self.structure_analyzer.analyze(repo_name, file_tree)
        
        # 2. Usage Extraction
        usage = self.usage_extractor.extract(repo_name, file_tree)
        
        # 3. Config Extraction
        config = self.config_extractor.extract(repo_name, file_tree)
        
        # 4. Aggregation
        profile = RepoProfile(
            name=repo_name,
            type=structure.type,
            main_language=structure.main_language,
            audience=structure.audience,
            key_features=structure.key_features,
            
            # Usage
            install_methods=usage.install_commands,
            commands=usage.commands,
            has_examples=usage.has_examples,
            usage_snippets=usage.usage_snippets,
            
            # Config
            config_options=config.config_options
        )
        
        print(f"[{repo_name}] Profile built successfully.")
        return profile