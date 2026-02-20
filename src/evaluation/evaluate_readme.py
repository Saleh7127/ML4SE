import argparse
import os
import csv
from rouge import Rouge


# python src/evaluation/evaluate_readme.py --repo <repo-name> --gen generated_readmes/<repo-name>.md --ref data/readmes/<repo-name>.md

def load_text(path):
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def append_to_csv(csv_path, data):
    file_exists = os.path.exists(csv_path)
    fieldnames = [
        "repo_name", 
        "rouge-1-p", "rouge-1-r", "rouge-1-f",
        "rouge-2-p", "rouge-2-r", "rouge-2-f",
        "rouge-l-p", "rouge-l-r", "rouge-l-f",
        "bert_precision", "bert_recall", "bert_f1"
    ]
    
    try:
        with open(csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(data)
        print(f"Results appended to {csv_path}")
    except Exception as e:
        print(f"Error appending to CSV: {e}")

def evaluate(repo_name, generated_path=None, reference_path=None, csv_path=None):
    # Default paths
    if not generated_path:
        generated_path = os.path.join("readmes", repo_name, "README.md")
    
    if not reference_path:
        # Try to find it in the repo data dir
        reference_path = os.path.join("data", "repositories", repo_name, "README.md")

    print(f"Evaluating {repo_name}...")
    print(f"Generated: {generated_path}")
    print(f"Reference: {reference_path}")

    gen_text = load_text(generated_path)
    ref_text = load_text(reference_path)

    if not gen_text:
        print(f"Error: Generated README not found at {generated_path}")
        return
    
    if not ref_text:
        print(f"Error: Reference README not found at {reference_path}")
        return

    # Initialize Rouge
    rouge = Rouge()
    
    # Calculate scores
    scores = {}
    csv_data = {"repo_name": repo_name}
    
    try:
        scores = rouge.get_scores(gen_text, ref_text)[0]
    except Exception as e:
        print(f"Error calculating ROUGE: {e}")
        return

    # Print results
    print("\n--- ROUGE Scores ---")
    for metric, results in scores.items():
        print(f"{metric.upper()}:")
        print(f"  Precision: {results['p']:.4f}")
        print(f"  Recall:    {results['r']:.4f}")
        print(f"  F1-Score:  {results['f']:.4f}")
        
        # Flatten for CSV
        csv_data[f"{metric}-p"] = results['p']
        csv_data[f"{metric}-r"] = results['r']
        csv_data[f"{metric}-f"] = results['f']

    # Calculate BERT Score
    try:
        from bert_score import score
        print("\nCalculating BERT Score (this may take a moment)...")
        P, R, F1 = score([gen_text], [ref_text], lang='en', verbose=True)
        print("\n--- BERT Scores ---")
        print(f"Precision: {P.mean():.4f}")
        print(f"Recall:    {R.mean():.4f}")
        print(f"F1-Score:  {F1.mean():.4f}")
        
        csv_data["bert_precision"] = P.mean().item()
        csv_data["bert_recall"] = R.mean().item()
        csv_data["bert_f1"] = F1.mean().item()
        
    except Exception as e:
        print(f"\nError calculating BERT Score: {e}")
       
    if csv_path:
        append_to_csv(csv_path, csv_data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate generated README against reference.")
    parser.add_argument("--repo", default=None, type=str, required=True, help="Repository name")
    parser.add_argument("--gen", type=str, help="Path to generated README")
    parser.add_argument("--ref", type=str, help="Path to reference README")
    parser.add_argument("--csv", type=str, default="evaluation_results.csv", help="Path to CSV output file")

    args = parser.parse_args()
    
    evaluate(args.repo, args.gen, args.ref, args.csv)
