import argparse
import pickle
import git
import pandas as pd
from nltk.sentiment import SentimentIntensityAnalyzer
from git.exc import InvalidGitRepositoryError

def main():
    parser = argparse.ArgumentParser(
        prog="Git stats for fun",
        description="Collects fun stuff about git repos, into a csv for playing around"
    )
    parser.add_argument(
        '--repos',
        nargs='+',
        help="Full path to repos to check, separated by space",
        required=True
    )
    parser.add_argument(
        '--smash-users',
        help="Combine users with different names into one, separate names by , and users by :"
    )
    parser.add_argument(
        '--list-users',
        help='Display list of users and commits, useful for smashing users together',
        action='store_true'
    )
    parser.add_argument(
        '--add-sentiment-analyze',
        help="Uses sentiment anlysis from pre-trained NLTK model",
        action='store_true'
    )
    parser.add_argument(
        '--save-debug-pickle',
        help='Saving a debug pickle'
    )
    parser.add_argument(
        '--load-debug-pickle',
        help='Loading debug pickle'
    )
    parser.add_argument(
        '--save-as',
        help='Filename for saving the parsed data to'
    )
    args = parser.parse_args()
    raw_commits = None
    total_commit_count = 0
    if args.load_debug_pickle:
        print(f"Loading data from {args.load_debug_pickle}")
        with open(args.load_debug_pickle, 'rb') as f:
            raw_commits = pickle.load(f)
        total_commit_count = raw_commits.shape[0]
    else:
        for repo in args.repos:
            print(f"Parsing {repo}...")
            try:
                repo_commits, commit_count = parse_repo_to_dataframe(repo)
                if raw_commits is None:
                    raw_commits = repo_commits
                else:
                    raw_commits = pd.concat([raw_commits, repo_commits])
                total_commit_count += commit_count
            except InvalidGitRepositoryError:
                print(f"Warning - Could not parse {repo}, skipping!")
    if args.save_debug_pickle:
        print(f"Saving as debug pickle: {args.save_debug_pickle}")
        with open(args.save_debug_pickle, 'wb') as f:
            pickle.dump(raw_commits, f)
    print(f"Parsed {total_commit_count} commits, done")
    if args.smash_users:
        print("Smashing users...")
        mapping = get_smash_users_mapping(args.smash_users)
        for replacement, replacing in mapping.items():
            raw_commits = raw_commits.replace(to_replace=replacing, value=replacement)
    if args.list_users:
        print(raw_commits.groupby('author')['message'].count())
    if args.add_sentiment_analyze:
        sia = SentimentIntensityAnalyzer()
        raw_commits['sentiment'] = raw_commits.apply(
            lambda row: sia.polarity_scores(row['message']),
            axis=1
        )
        raw_commits = raw_commits \
            .join(pd.json_normalize(raw_commits['sentiment'])) \
            .drop('sentiment', axis='columns')
    print(f'Saving as {args.save_as}... ')
    raw_commits.to_csv(args.save_as)
    print("Done!")

def get_smash_users_mapping(smash_string):
    different_users = {}
    for users in smash_string.split(':'):
        users_to_replace = users.split(',')
        replacement = users_to_replace[0]
        different_users[replacement] = users_to_replace
    return different_users


def parse_repo_to_dataframe(path_to_repo):
    g = git.Repo(path_to_repo)
    main_branch = "master"
    if main_branch not in g.branches:
        main_branch = "main"
    count = 0
    raw_commits = pd.DataFrame()
    for commit in g.iter_commits(main_branch):
        new_row = pd.DataFrame({
            'author':commit.author.name,
            'date':commit.authored_datetime,
            'message':commit.message.replace('\n', ' ') ,
            'stats_insertions':commit.stats.total['insertions'],
            'stats_deletions':commit.stats.total['deletions'],
            'stats_lines':commit.stats.total['lines']
            },
            index=[count]
        )
        raw_commits = pd.concat([raw_commits, new_row])
        count += 1

    raw_commits['date'] = pd.to_datetime(raw_commits['date'], utc=True)
    raw_commits['hour'] = raw_commits['date'].dt.hour
    raw_commits['minute'] = raw_commits['date'].dt.minute
    raw_commits['day'] = raw_commits['date'].dt.weekday
    raw_commits['message_length'] = raw_commits['message'].apply(len)
    raw_commits.sort_values('day', ascending=False).head(5).to_string()
    return raw_commits, count


if __name__ == "__main__":
    main()
