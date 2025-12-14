
import os
import argparse
import re
from typing import Set, Tuple, List

def extract_headers(markdown_text: str) -> Set[str]:
    headers = set()
    lines = markdown_text.split('\n')
    for line in lines:
        match = re.match(r'^(#{1,6})\s+(.*)', line)
        if match:
            header_content = match.group(2).strip()
            normalized = re.sub(r'[^\w\s]', '', header_content).lower().replace(' ', '')
            if normalized:
                headers.add(normalized)
    return headers

def calculate_metrics(generated_headers: Set[str], truth_headers: Set[str]) -> Tuple[float, float, float]:
    if not truth_headers:
        return 0.0, 0.0, 0.0

    intersection = generated_headers.intersection(truth_headers)
    union = generated_headers.union(truth_headers)

    recall = len(intersection) / len(truth_headers)
    
    if not generated_headers:
        precision = 0.0
    else:
        precision = len(intersection) / len(generated_headers)
        
    jaccard = len(intersection) / len(union) if union else 0.0

    return recall, precision, jaccard

def main():
    parser = argparse.ArgumentParser(description="Calculate Section Coverage Score for READMEs.")
    parser.add_argument("--generated", "--gen", type=str, required=True, help="Path to the generated README.md")
    parser.add_argument("--ground-truth-dir", type=str, default="data/readmes", help="Directory containing ground truth READMEs")
    parser.add_argument("--reference", "--ref", type=str, help="Explicit path to ground truth file")
    
    args = parser.parse_args()

    repo_name = os.path.basename(os.path.dirname(os.path.abspath(args.generated)))

    ground_truth_path = args.reference
    
    if not ground_truth_path:
        possible_names = [
            f"{repo_name}_README.md",
            f"{repo_name}.md",
            "README.md"
        ]
        
        for name in possible_names:
            path = os.path.join(args.ground_truth_dir, name)
            if os.path.exists(path):
                ground_truth_path = path
                break
            
    if not ground_truth_path:
        print(f"Warning: Could not automatically find ground truth in {args.ground_truth_dir} for {repo_name}")
        print(f"Checked: {possible_names}")
        return

    print(f"Comparing:")
    print(f"  Generated: {args.generated}")
    print(f"  Ground Truth: {ground_truth_path}")

    try:
        with open(args.generated, 'r', encoding='utf-8') as f:
            gen_text = f.read()
        with open(ground_truth_path, 'r', encoding='utf-8') as f:
            truth_text = f.read()
            
        gen_headers = extract_headers(gen_text)
        truth_headers = extract_headers(truth_text)
        
        recall, precision, jaccard = calculate_metrics(gen_headers, truth_headers)
        
        print("-" * 30)
        print(f"Section Coverage Recall:  {recall:.2%}")
        print(f"Section Precision:        {precision:.2%}")
        print(f"Jaccard Similarity:       {jaccard:.2%}")
        print("-" * 30)
        print(f"Generated Sections ({len(gen_headers)}): {sorted(list(gen_headers))}")
        print(f"Ground Truth Sections ({len(truth_headers)}): {sorted(list(truth_headers))}")
        
    except Exception as e:
        print(f"Error processing files: {e}")

if __name__ == "__main__":
    main()
