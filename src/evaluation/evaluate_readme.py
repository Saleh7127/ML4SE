import argparse
import os
from rouge import Rouge


# python src/evaluation/evaluate_readme.py --repo ThatGuyJacobee__Elite-Music --gen readmes/ThatGuyJacobee__Elite-Music/README.md --ref data/readmes/ThatGuyJacobee__Elite-Music.md

def load_text(path):
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def evaluate(repo_name, generated_path=None, reference_path=None):
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

    # Calculate BERT Score
    try:
        from bert_score import score
        print("\nCalculating BERT Score (this may take a moment)...")
        P, R, F1 = score([gen_text], [ref_text], lang='en', verbose=True)
        print("\n--- BERT Scores ---")
        print(f"Precision: {P.mean():.4f}")
        print(f"Recall:    {R.mean():.4f}")
        print(f"F1-Score:  {F1.mean():.4f}")
    except Exception as e:
        print(f"\nError calculating BERT Score: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate generated README against reference.")
    parser.add_argument("--repo", default=None, type=str, help="Repository name")
    parser.add_argument("--gen", type=str, help="Path to generated README")
    parser.add_argument("--ref", type=str, help="Path to reference README")

    args = parser.parse_args()
    
    evaluate(args.repo, args.gen, args.ref)
